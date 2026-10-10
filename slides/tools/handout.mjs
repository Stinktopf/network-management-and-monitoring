import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';

// Reuse the Markdown parser and browser already installed with Marp.
const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const require = createRequire(path.join(root, 'node_modules/@marp-team/marp-cli/package.json'));
const MarkdownIt = require('markdown-it');
const puppeteer = require('puppeteer-core');

export async function buildHandout({ pdf = true } = {}) {
  const md = new MarkdownIt();
  const renderSection = source => {
    const tokens = md.parse(source, {});
    for (const token of tokens) {
      if (token.type === 'heading_open' || token.type === 'heading_close') {
        token.tag = `h${Number(token.tag.slice(1)) + 1}`;
      }
    }
    return md.renderer.render(tokens, md.options, {});
  };
  const source = fs.readFileSync(path.join(root, 'resources/CHEATSHEET.md'), 'utf8');
  const sections = source.trim().split(/\n---\n/);
  const pages = [
    { title: 'Explore the network', sections: [0, 1, 2] },
    { title: 'Inspect and change configuration', sections: [3, 4] },
    { title: 'Read and change through APIs', sections: [5, 6] },
    { title: 'Measure and experiment', sections: [7, 8, 9] },
  ];
  if (sections.length !== 10) throw new Error('Expected ten command-reference sections');
  const pagesHtml = pages.map(({ title, sections: pageSections }, index) => `<article class="page${index === 1 || index === 2 ? ' compact' : ''}">
    <header><span>AI5049 / ReefNet</span><span>Command reference</span></header>
    <h1>${title}</h1>
    ${pageSections.map(sectionIndex => `<section>${renderSection(sections[sectionIndex])}</section>`).join('\n')}
    <footer><span>WSL = repository terminal. Exit Linux with <code>exit</code>, SR Linux with <code>quit</code>.</span><span>${index + 1} / ${pages.length}</span></footer>
  </article>`).join('\n');
  const css = fs.readFileSync(path.join(root, 'theme/handout.css'), 'utf8');
  const output = path.join(root, 'exports/cheatsheet.html');
  fs.mkdirSync(path.dirname(output), { recursive: true });
  fs.writeFileSync(output, `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>ReefNet command reference</title><style>${css}</style></head><body>${pagesHtml}</body></html>\n`);
  console.log('Command reference: exports/cheatsheet.html');
  if (!pdf) return;
  const browser = await puppeteer.launch({
    executablePath: process.env.CHROME_PATH || '/usr/bin/chromium', args: ['--no-sandbox'],
  });
  try {
    const page = await browser.newPage();
    await page.goto(pathToFileURL(output).href);
    await page.emulateMediaType('print');
    await page.evaluate(() => document.fonts.ready);
    const overflow = await page.evaluate(() => [...document.querySelectorAll('.page')].flatMap((sheet, i) => {
      const bottom = sheet.querySelector('footer').getBoundingClientRect().top - 8;
      return [...sheet.querySelectorAll('section')].filter(s => s.getBoundingClientRect().bottom > bottom)
        .map(() => i + 1);
    }));
    if (overflow.length) throw new Error(`Handout content exceeds page ${overflow.join(', ')}`);
    await page.pdf({ path: path.join(root, 'exports/cheatsheet.pdf'), preferCSSPageSize: true, printBackground: true });
    console.log(`Command reference: exports/cheatsheet.pdf (A4, ${pages.length} pages)`);
  } finally {
    await browser.close();
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  await buildHandout({ pdf: !process.argv.includes('--html-only') });
}
