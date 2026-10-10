import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
process.chdir(root);
fs.mkdirSync('exports', { recursive: true });
if (!process.argv.includes('--handout-only')) await import('./sync-theme.mjs');

const source = 'nmm.md';
const marp = path.join(root, 'node_modules/@marp-team/marp-cli/marp-cli.js');
const runMarp = (args, options = {}, input = source) => execFileSync(process.execPath,
  [marp, input, '--html', ...args], { stdio: 'inherit', ...options });

if (!process.argv.includes('--handout-only')) {
  runMarp(['-o', 'exports/nmm.html']);

  // Keep the HTML portable: embed local images instead of linking outside exports/.
  const mimeTypes = {
    '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg', '.gif': 'image/gif', '.webp': 'image/webp',
  };
  const html = fs.readFileSync('exports/nmm.html', 'utf8').replace(
    /src="([^"#]+)"/g, (attribute, source) => {
      if (/^(?:[a-z]+:|\/\/)/i.test(source)) return attribute;
      const file = decodeURIComponent(source);
      const mime = mimeTypes[path.extname(file).toLowerCase()];
      if (!mime) return attribute;
      return `src="data:${mime};base64,${fs.readFileSync(file).toString('base64')}"`;
    });
  fs.writeFileSync('exports/nmm.html', html);

  if (!process.argv.includes('--html-only')) {
    for (const format of ['pdf', 'pptx']) {
      runMarp([`--${format}`, '--allow-local-files', '--browser-path',
        process.env.CHROME_PATH || '/usr/bin/chromium', '--browser-timeout', '120',
        '-o', `exports/nmm.${format}`],
      { env: { ...process.env, CHROME_NO_SANDBOX: '1' } });
    }
  }

}

// The command reference is also available as a printable handout.
runMarp(['-o', 'exports/cheatsheet.html'], {}, 'resources/CHEATSHEET.md');
if (!process.argv.includes('--html-only')) {
  runMarp(['--pdf', '--allow-local-files', '--browser-path',
    process.env.CHROME_PATH || '/usr/bin/chromium', '--browser-timeout', '120',
    '-o', 'exports/cheatsheet.pdf'],
  { env: { ...process.env, CHROME_NO_SANDBOX: '1' } }, 'resources/CHEATSHEET.md');
}
