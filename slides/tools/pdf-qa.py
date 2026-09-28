"""Check the delivered PDF itself, independently of the browser DOM."""
from pathlib import Path
import json
import re
from html import unescape
import fitz

root = Path(__file__).resolve().parents[1]
doc = fitz.open(root / 'exports/ai5049-reefnet.pdf')
issues = []
source_slides = re.split(r"^---\s*$", (root / "ai5049-reefnet.md").read_text(), flags=re.M)[2:]
for index, page in enumerate(doc, 1):
    sx, sy = 1280 / page.rect.width, 720 / page.rect.height
    directive = re.search(r'<!-- _footer: (".*") -->', source_slides[index-1])
    if directive:
        footer = json.loads(directive[1])
        expected = [unescape(url) for url in re.findall(r'href="([^"]+)"', footer)]
        actual = {link.get('uri') for link in page.get_links()}
        for url in expected:
            if url not in actual:
                issues.append({'slide': index, 'type': 'missing-footer-link', 'url': url})
    headings = []
    heading_y = None
    for block in page.get_text('dict')['blocks']:
        for line in block.get('lines', []):
            for span in line['spans']:
                x0, y0, x1, y1 = span['bbox']
                size = span['size'] * sx
                # First large text is the title, regardless of vertical position.
                if size >= 40 and heading_y is None:
                    heading_y = y0
                if size >= 40 and abs(y0 - (heading_y if heading_y is not None else -999)) < 2:
                    headings.append(span)
                if size >= 20 and (y0 * sy < 45 or y1 * sy > 612 or x0 * sx < 60 or x1 * sx > 1220):
                    issues.append({'slide': index, 'type': 'content-bounds', 'text': span['text']})
    if not headings:
        issues.append({'slide': index, 'type': 'missing-title'})
    for span in headings:
        rgb = ((span['color'] >> 16) & 255, (span['color'] >> 8) & 255, span['color'] & 255)
        if any(abs(a-b) > 1 for a,b in zip(rgb,(114,191,68))):
            issues.append({'slide': index, 'type': 'heading-color', 'text': span['text'], 'color': rgb})
report = {'slides': len(doc), 'issues': issues}
(root / 'build/qa/pdf-report.json').write_text(json.dumps(report, indent=2))
print(f'PDF QA: {len(doc)} pages, {len(issues)} findings')
raise SystemExit(bool(issues))
