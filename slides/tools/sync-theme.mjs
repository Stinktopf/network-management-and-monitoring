// Keep the Markdown portable: VS Code can render it without a registered theme.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const css=fs.readFileSync(path.join(root,'theme/ai5049.css'),'utf8')
  .replace(/\/\* @theme ai5049 \*\/\s*/, '')
  .replace(/@import 'default';\s*/, '').trim();
const file=path.join(root,'nmm.md');
let source=fs.readFileSync(file,'utf8');
source=source.replace(/^theme: .*$/m,'theme: default');
source=source.replace(/^style: \|\n(?:[ \t].*\n|\n)*/m,'');
source=source.replace(/^(description: .*\n)/m,`$1style: |\n${css.split('\n').map(l=>'  '+l).join('\n')}\n`);
fs.writeFileSync(file,source);
