import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const source=fs.readFileSync(path.join(root,'ai5049-reefnet.md'),'utf8');
const escape=s=>s.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
const md=['# Quellenverzeichnis','','Quellen zum aktiven AI5049-/BOB1-/ReefNet-Foliensatz, nach Foliennummer geordnet. Die Links stehen zusätzlich in den Marp-Präsentationsnotizen. Ausgewählte Hauptquellen sind im Folienfooter verlinkt. Verbindliche Richtlinien bleiben als benannte Links auf den Unterrichtsfolien sichtbar, ebenso Lab-Adressen und ausführbare URLs.',''];
const sections=[];
for(const slide of source.split(/^---\s*$/m).slice(2)) {
 const notes=slide.match(/<!--\s*Source references \(not projected\):([\s\S]*?)-->/)?.[1];
 if(!notes)continue;
 const id=Number(slide.match(/slide-id: S(\d+)/)[1]);
 const title=slide.match(/^# (.+)$/m)[1];
 const refs=[...notes.matchAll(/^- \[([^\]]+)\]\(([^)]+)\)/gm)].map(m=>({label:m[1],url:m[2]}));
 md.push(`## ${String(id).padStart(3,'0')} · ${title}`,'',...refs.map(r=>`- [${r.label}](${r.url})`),'');
 sections.push(`<section id="slide-${id}"><h2>${String(id).padStart(3,'0')} · ${escape(title)}</h2><ul>${refs.map(r=>`<li><a href="${escape(r.url)}">${escape(r.label)}</a></li>`).join('')}</ul></section>`);
}
fs.writeFileSync(path.join(root,'REFERENCES.md'),md.join('\n'));
fs.mkdirSync(path.join(root,'exports'),{recursive:true});
fs.writeFileSync(path.join(root,'exports/references.html'),`<!doctype html><html lang="de"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>AI5049 · Quellen</title><style>body{font:18px/1.5 Arial,sans-serif;max-width:900px;margin:48px auto;padding:0 24px;color:#303030}h1{color:#72bf44}h2{color:#72bf44;font-size:22px;margin-top:36px}a{color:inherit;text-decoration-color:#aaa}li{margin:8px 0}section{border-top:1px solid #eee;margin-top:30px}</style><h1>AI5049 · Quellenverzeichnis</h1><p>Quellen nach Foliennummer. Die Links stehen auch in den Marp-Präsentationsnotizen.</p>${sections.join('')}</html>`);
