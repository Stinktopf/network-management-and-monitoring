import puppeteer from 'puppeteer-core';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));process.chdir(root);
const md=fs.readFileSync('ai5049-reefnet.md','utf8');
const files=[...new Set([...md.matchAll(/!\[[^\]]*\]\((assets\/[^)]+\.svg)\)/g)].map(m=>m[1]))];
const browser=await puppeteer.launch({executablePath:process.env.CHROME_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
const page=await browser.newPage();const issues=[];
const screenshotDir='/tmp/ai5049-svg-review';
if(process.argv.includes('--images'))fs.mkdirSync(screenshotDir,{recursive:true});
for(const file of files){
 await page.setContent(fs.readFileSync(file,'utf8'));await page.evaluate(()=>document.fonts.ready);
 const found=await page.evaluate(()=>{
  const svg=document.querySelector('svg'),v=svg.viewBox.baseVal;
  const texts=[...svg.querySelectorAll('text')].map(e=>{const b=e.getBBox();return {text:e.textContent,x:b.x,y:b.y,w:b.width,h:b.height}}),result=[];
  const palette=new Set(['#303030','#666666','#888888','#cccccc','#dddddd','#f6f6f6','#ffffff','#72bf44']);
  for(const element of svg.querySelectorAll('[fill],[stroke]')) {
   for(const property of ['fill','stroke']) {
    const value=element.getAttribute(property);
    if(value?.startsWith('#')&&!palette.has(value.toLowerCase()))result.push({type:'palette',property,value});
   }
  }
  // Every arrowhead must be neutral, including marker definitions not used yet.
  for(const marker of svg.querySelectorAll('marker *')) {
   for(const property of ['fill','stroke']) {
    const value=getComputedStyle(marker)[property];
    const rgb=value.match(/^rgb\((\d+), (\d+), (\d+)\)$/);
    if(rgb && !(rgb[1]===rgb[2] && rgb[2]===rgb[3]))result.push({type:'colored-arrowhead',property,value});
   }
  }
  const overlap=(a,b)=>Math.max(0,Math.min(a.x+a.w,b.x+b.w)-Math.max(a.x,b.x))*Math.max(0,Math.min(a.y+a.h,b.y+b.h)-Math.max(a.y,b.y));
  for(const t of texts){
   if(t.x<v.x-1||t.y<v.y-1||t.x+t.w>v.x+v.width+1||t.y+t.h>v.y+v.height+1)result.push({type:'canvas',...t});
  }
  for(let i=0;i<texts.length;i++)for(let j=i+1;j<texts.length;j++)if(overlap(texts[i],texts[j])>8)result.push({type:'text-overlap',a:texts[i].text,b:texts[j].text});
  for(const r of svg.querySelectorAll('rect')){
   const q=r.getBBox(),b={x:q.x,y:q.y,w:q.width,h:q.height};
   if(b.w<100||b.h<48)continue;
   for(const t of texts){
    const area=overlap(t,b);if(area<20)continue;
    if(t.x>=b.x-1&&t.y>=b.y-1&&t.x+t.w<=b.x+b.w+1&&t.y+t.h<=b.y+b.h+1)continue;
    result.push({type:'box-edge',text:t.text});
   }
  }
  // Detect strokes through label areas; respect opaque shapes painted later.
  const elements=[...svg.querySelectorAll('*')];
  const masks=elements.filter(e=>!e.closest('defs') && ['rect','circle','ellipse','path','polygon'].includes(e.tagName) && getComputedStyle(e).fill!=='none' && parseFloat(getComputedStyle(e).fillOpacity)>0);
  const reported=new Set();
  for(const path of svg.querySelectorAll('path,line,polyline')) {
   if(path.closest('defs') || getComputedStyle(path).stroke==='none')continue;
   const length=path.getTotalLength();
   for(let d=0;d<=length;d+=3) {
    const point=path.getPointAtLength(d);
    for(const label of texts) {
     if(reported.has(label.text))continue;
     if(point.x<=label.x+3 || point.x>=label.x+label.w-3 || point.y<=label.y+3 || point.y>=label.y+label.h-3)continue;
     if(masks.some(mask=>elements.indexOf(mask)>elements.indexOf(path) && mask.isPointInFill(point)))continue;
     result.push({type:'stroke-through-label',text:label.text});reported.add(label.text);
    }
   }
  }
  return result;
 });
 if(process.argv.includes('--images')) {
  const bounds=await page.evaluate(()=>{const r=document.querySelector('svg').getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height}});
  await page.setViewport({width:Math.ceil(bounds.width+20),height:Math.ceil(bounds.height+20),deviceScaleFactor:1});
  await page.screenshot({path:path.join(screenshotDir,path.basename(file,'.svg')+'.png'),clip:bounds});
 }
 issues.push(...found.map(i=>({file,...i})));
}
await browser.close();fs.writeFileSync('build/qa/svg-report.json',JSON.stringify({assets:files.length,issues},null,2));console.log('SVG QA:',files.length,'assets,',issues.length,'findings');if(issues.length)process.exitCode=1;
