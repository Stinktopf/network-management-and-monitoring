import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
process.chdir(root);
fs.mkdirSync('exports',{recursive:true});
fs.mkdirSync('build/qa',{recursive:true});
await import('./source-index.mjs');
await import('./sync-theme.mjs');
const source='ai5049-reefnet.md';
const common=[source,'--html'];
for (const [name,extra] of [['exports/ai5049-reefnet.html',[]],['build/qa/slides.html',['--template','bare']]]) {
  execFileSync('node_modules/.bin/marp',[...common,...extra,'-o',name],{stdio:'inherit'});
  let html=fs.readFileSync(name,'utf8');
  html=html.replace(/src="assets\/diagrams\/([^"#]+)"/g,(_,name)=>`src="data:image/svg+xml;base64,${fs.readFileSync(`assets/diagrams/${name}`).toString('base64')}"`);
  fs.writeFileSync(name,html);
}
if (!process.argv.includes('--html-only')) {
 execFileSync('node_modules/.bin/marp',[...common,'--pdf','--allow-local-files','--browser-path',process.env.CHROME_PATH||'/usr/bin/chromium','--browser-timeout','120','-o','exports/ai5049-reefnet.pdf'],{stdio:'inherit',env:{...process.env,CHROME_NO_SANDBOX:'1'}});
}
if (process.argv.includes('--qa')) {
 execFileSync(process.execPath,['tools/visual-qa.mjs'],{stdio:'inherit'});
 execFileSync(process.execPath,['tools/preview-qa.mjs'],{stdio:'inherit'});
 execFileSync(process.execPath,['tools/svg-qa.mjs'],{stdio:'inherit'});
 execFileSync(process.execPath,['tools/node-alignment-qa.mjs'],{stdio:'inherit'});
 execFileSync('python3',['tools/pdf-qa.py'],{stdio:'inherit'});
 execFileSync('python3',['tools/contact-sheets.py'],{stdio:'inherit'});
}
