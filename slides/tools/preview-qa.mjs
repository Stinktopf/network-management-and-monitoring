// Render with Marp Core and its built-in theme, as an unconfigured editor does.
import {Marp} from '@marp-team/marp-core';
import fs from 'node:fs';
import {execFileSync} from 'node:child_process';
const marp=new Marp({html:true});
const {html,css}=marp.render(fs.readFileSync('ai5049-reefnet.md','utf8'));
const embedded=html.replace(/src="assets\/diagrams\/([^"#]+)"/g,(_,name)=>
 `src="data:image/svg+xml;base64,${fs.readFileSync(`assets/diagrams/${name}`).toString('base64')}"`);
fs.writeFileSync('build/qa/editor-preview.html',`<!doctype html><meta charset="utf-8"><style>${css}</style><div class="marpit">${embedded}</div>`);
execFileSync(process.execPath,['tools/visual-qa.mjs','--preview'],{stdio:'inherit'});
