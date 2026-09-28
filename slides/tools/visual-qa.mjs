import puppeteer from 'puppeteer-core';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
process.chdir(root);
const browser=await puppeteer.launch({executablePath:process.env.CHROME_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox','--disable-dev-shm-usage'],userDataDir:'/tmp/ai5049-qa-browser'});
const page=await browser.newPage();
await page.setViewport({width:1280,height:720,deviceScaleFactor:1});
const preview=process.argv.includes('--preview');
await page.goto(pathToFileURL(path.join(root,preview?'build/qa/editor-preview.html':'build/qa/slides.html')).href,{waitUntil:'networkidle0'});
await page.evaluate(()=>document.fonts.ready);
const report=await page.evaluate(()=>{
 const issues=[];let count=0;
 for(const section of document.querySelectorAll('section')){
  count++;const sr=section.getBoundingClientRect(),scale=sr.width/1280;
  const rect=e=>{const r=e.getBoundingClientRect();return {x:(r.left-sr.left)/scale,y:(r.top-sr.top)/scale,w:r.width/scale,h:r.height/scale,bottom:(r.bottom-sr.top)/scale,right:(r.right-sr.left)/scale}};
  const title=section.querySelector('h1')?.textContent;
  const put=(type,detail)=>issues.push({slide:count,title,type,...detail});
  if(section.matches('.day,.chapter,.title')) {
   for(const nav of section.querySelectorAll('.progress')) {
    if(getComputedStyle(nav).display!=='none')put('title-progress',{});
   }
  }
  const footer=section.querySelector('footer');
  if(footer?.querySelector('.footer-refs')) {
   const context=footer.querySelector('.footer-context'),refs=footer.querySelector('.footer-refs');
   const fr=rect(footer),cr=rect(context),rr=rect(refs);
   if(cr.right+12>rr.x || rr.right>fr.right+1 || fr.bottom>704 || fr.y<670)
    put('footer-layout',{context:cr,references:rr,footer:fr});
   for(const a of refs.querySelectorAll('a')) {
    const cs=getComputedStyle(a);
    if(cs.color!=='rgb(119, 119, 119)' || cs.textDecorationColor!=='rgb(114, 191, 68)' || !cs.textDecorationLine.includes('underline'))
     put('footer-link-style',{text:a.textContent,color:cs.color,underline:cs.textDecorationColor});
    if(!/^https?:/.test(a.href))put('footer-link-target',{text:a.textContent,href:a.href});
   }
  }
  // Headings must be Fulda green; a neutral gray is not an acceptable fallback.
  for(const h of section.querySelectorAll('h1,h2,h3,h4')) {
   const color=getComputedStyle(h).color;
   if(color!=='rgb(114, 191, 68)')put('heading-color',{text:h.textContent,color});
  }
  // Verify the rendered palette, including inherited theme styles.
  for (const e of section.querySelectorAll('h1,h2,h3,td,th,pre,code,pre code span')) {
   const cs=getComputedStyle(e);
   for(const key of ['color','backgroundColor']) {
    const v=cs[key], numbers=v.match(/[\d.]+/g)?.map(Number);
    if(!numbers || (numbers.length===4 && numbers[3]===0))continue;
    const [r,g,b]=numbers;
    if(!(r===g&&g===b) && !(r===114&&g===191&&b===68))
     put('palette',{element:e.tagName,property:key,value:v});
   }
  }
  const source=section.querySelector('.sources');
  const limit=source?rect(source).y-12:610;
  for(const e of section.children){
   if(e.matches('.badge,.sources,.progress,footer,header'))continue;
   const r=rect(e);
   if(r.bottom>limit+1)put('vertical',{element:e.tagName,bottom:r.bottom,limit,text:e.textContent.slice(0,110)});
   if(r.x<45||r.right>1235)put('horizontal',{element:e.tagName,...r});
  }
  for(const e of section.querySelectorAll('pre,table,img')){
   const r=rect(e);
   if(e.scrollWidth>e.clientWidth+2)put('overflow',{element:e.tagName,excess:e.scrollWidth-e.clientWidth,text:e.textContent.slice(0,110)});
   if(e.tagName==='IMG'&&(!e.complete||!e.naturalWidth))put('broken-image',{});
   if(r.right>1230)put('right-edge',{element:e.tagName,right:r.right});
  }
  // Check text itself, including table cells and nested code containers.
  // A parent can fit even when one unbreakable child extends beyond it.
  for(const e of section.querySelectorAll('p,li,th,td,pre')){
   if(e.closest('.sources,.progress,footer,header')||e.querySelector('img,li,p'))continue;
   const walker=document.createTreeWalker(e,NodeFilter.SHOW_TEXT);
   const er=rect(e);
   while(walker.nextNode()){
    const node=walker.currentNode;if(!node.textContent.trim())continue;
    if(node.parentElement.closest('.katex,math,mjx-container'))continue;
    const range=document.createRange();range.selectNodeContents(node);
    for(const r of range.getClientRects()){
     const left=(r.left-sr.left)/scale,right=(r.right-sr.left)/scale;
     const bottom=(r.bottom-sr.top)/scale;
     if(bottom>limit+1)put('text-bottom',{element:e.tagName,text:node.textContent.slice(0,90),bottom,limit});
     if(left<65||right>1216||(e.matches('th,td')&&right>er.right+2)){
      put('text-edge',{element:e.tagName,text:node.textContent.slice(0,90),left,right});break;
     }
    }
   }
  }
  if(source&&source.scrollHeight>source.clientHeight+2)put('source-overflow',{});
  const h=section.querySelector('h1');
  if(h&&h.getBoundingClientRect().height/scale>parseFloat(getComputedStyle(h).lineHeight)*1.6)put('title-wrap',{text:h.textContent});
  // Real rendered line boxes, not character-count estimates.
  for(const e of section.querySelectorAll('p,li,h1')){
   if(e.closest('pre,.sources,.progress,footer')||e.querySelector('img,li,p')||e.textContent.length<40)continue;
   const walker=document.createTreeWalker(e,NodeFilter.SHOW_TEXT);const words=[];
   while(walker.nextNode()){
    const n=walker.currentNode;
    for(const m of n.textContent.matchAll(/\S+/g)){
     const r=document.createRange();r.setStart(n,m.index);r.setEnd(n,m.index+m[0].length);
     const b=r.getBoundingClientRect(); if(b.width)words.push({text:m[0],y:Math.round((b.top-sr.top)/scale),x:(b.left-sr.left)/scale,right:(b.right-sr.left)/scale});
    }
   }
   const lines=[];for(const w of words){let l=lines.find(l=>Math.abs(l.y-w.y)<10);if(!l){l={y:w.y,words:[]};lines.push(l)}l.words.push(w)}
   if(lines.length>1){const last=lines.at(-1),prev=lines.at(-2); const width=Math.max(...last.words.map(w=>w.right))-Math.min(...last.words.map(w=>w.x));
    if(last.words.length<=3&&width<210&&prev.words.length>4)put('short-last-line',{element:e.tagName,last:last.words.map(w=>w.text).join(' '),text:e.textContent});
   }
  }
 }
 return {slides:count,issues};
});
fs.writeFileSync(preview?'build/qa/preview-report.json':'build/qa/layout-report.json',JSON.stringify(report,null,2));
const types={};for(const i of report.issues)types[i.type]=(types[i.type]||0)+1;
console.log(JSON.stringify({slides:report.slides,issues:types},null,2));
await browser.close();
if (report.issues.length) process.exitCode=1;
