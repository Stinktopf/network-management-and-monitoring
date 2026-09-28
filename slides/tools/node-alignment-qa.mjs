import puppeteer from 'puppeteer-core';
import fs from 'node:fs';
const browser=await puppeteer.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
const page=await browser.newPage();const findings=[];
for(const name of fs.readdirSync('assets/diagrams').filter(n=>n.endsWith('.svg'))){
 await page.setContent(fs.readFileSync(`assets/diagrams/${name}`,'utf8'));await page.evaluate(()=>document.fonts.ready);
 const report=await page.evaluate(()=>{
  const svg=document.querySelector('svg');
  const rects=[...svg.querySelectorAll('rect,ellipse,circle')].filter(e=>{const b=e.getBBox();return (b.width>=100&&b.height>=48)||(e.tagName==='circle'&&b.width>=50)});
  const texts=[...svg.querySelectorAll('text')];const report=[];
  for(const rect of rects){
   const b=rect.getBBox();const r={x:b.x,y:b.y,width:b.width,height:b.height};
   const children=rects.filter(other=>{if(other===rect)return false;const q=other.getBBox();return q.x>=r.x&&q.y>=r.y&&q.x+q.width<=r.x+r.width&&q.y+q.height<=r.y+r.height});
   if(children.length)r.height=Math.min(...children.map(c=>c.getBBox().y))-r.y;
   if(r.height<40)continue;
   const inside=texts.filter(t=>{const b=t.getBBox();return b.x>=r.x-1&&b.y>=r.y-1&&b.x+b.width<=r.x+r.width+1&&b.y+b.height<=r.y+r.height+1});
   if(!inside.length||inside.length>6)continue;
   const y0=Math.min(...inside.map(t=>t.getBBox().y)),y1=Math.max(...inside.map(t=>{const b=t.getBBox();return b.y+b.height}));
   const delta=(r.y+r.height/2)-(y0+y1)/2;
   report.push({rect:{x:r.x,y:r.y,width:r.width,height:r.height},text:inside.map(t=>t.textContent),delta:Math.round(delta*10)/10,indices:inside.map(t=>texts.indexOf(t))});
  }
  return report;
 });
 findings.push(...report.map(row=>({file:name,...row})));
}
await browser.close();
const issues=findings.filter(r=>Math.abs(r.delta)>2.5);
fs.writeFileSync('build/qa/node-alignment-report.json',JSON.stringify({groups:findings.length,issues},null,2));
console.log(`Node alignment: ${findings.length} label groups, ${issues.length} findings`);
if(issues.length){console.log(JSON.stringify(issues,null,2));process.exitCode=1;}
