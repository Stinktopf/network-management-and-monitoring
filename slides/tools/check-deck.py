"""Check deck structure, provenance coverage, assets and rendered artifacts."""
from pathlib import Path
from collections import Counter
import json
import re
import xml.etree.ElementTree as ET
import fitz

root = Path(__file__).resolve().parents[1]
text = (root / 'ai5049-reefnet.md').read_text()
slides = re.split(r'^---\s*$', text, flags=re.M)[2:]
manifest = json.loads((root / 'docs/slide-manifest.json').read_text())
assert len(slides) == len(manifest) == 366
assert 'marp: true' in text and 'theme: default' in text and 'style: |' in text
css = (root / 'theme/ai5049.css').read_text()
css = re.sub(r"/\* @theme ai5049 \*/\s*|@import 'default';\s*", '', css).strip()
assert '\n'.join('  ' + line for line in css.splitlines()) in text, 'Embedded theme is stale'
assert 'size: 16:9' in text and 'paginate: true' in text
assert '../Kursreferenzen/Technik/assets/' not in text
for n, (slide, record) in enumerate(zip(slides, manifest), 1):
    assert f'slide-id: S{n:03d};' in slide
    assert re.search(r'^# (.+)', slide, re.M)[1] == record['title']
    assert '<div class="badge">' not in slide
    assert record['kind'] in {'CORE', 'LAB', 'DEEP DIVE', 'RESEARCH'}
    if record['layout'] == 'day':
        assert re.fullmatch(r'\d{1,2} [A-Z][a-z]+ 20\d{2}', record['title']), n
        assert re.search(r'^## .+', slide, re.M), n
    nav = re.search(r'<nav.*?</nav>', slide, re.S)
    if record['layout'] in {'day', 'chapter', 'title'}:
        assert nav is None, n
    elif record['section'] in {'Networking 101', 'Network Operations', 'Network Automation', 'Monitoring / Observability'}:
        assert nav and nav[0].count('class="active"') == 1, n
    else:
        assert nav is None, n
# Keep the course narrative aligned with the published dates.
# Incident stories form one closing block on Automation day, including cable cases.
sections = [r['section'] for r in manifest]
incident_section = 'Network Automation · Incident stories'
incident_indices = [i for i, section in enumerate(sections) if section == incident_section]
assert incident_indices == list(range(min(incident_indices), max(incident_indices) + 1))
assert sections[min(incident_indices) - 1] == 'Network Automation'
assert sections[max(incident_indices) + 1] == 'Monitoring / Observability'
assert all(r['kind'] == 'DEEP DIVE' for r in manifest if r['section'] == incident_section)
active_date = None
for record in manifest:
    if record['layout'] == 'day':
        active_date = record['title']
    if record['section'] == incident_section:
        assert active_date == '13 October 2026', ('Incident on the wrong day', record['slide'])

for source_id in [294, 295, 296, 297]:
    record = next(r for r in manifest if r['old'] == source_id)
    assert record['section'] == incident_section, ('Cable case outside day 2', source_id)
research_indices = [i for i, section in enumerate(sections) if section == 'Research · questions and sources']
research_titles = [manifest[i]['title'] for i in research_indices]
assert research_titles[0] == '30 October 2026'
assert research_titles.index('From a problem to a research question') < research_titles.index('Can public data answer your question?')
assert research_titles[-1] == 'Your question, your next step'
assets = set(re.findall(r'!\[[^\]]*\]\(([^)]+)\)', text))
for asset in assets:
    assert not asset.startswith('/'), asset
    path = root / asset
    assert path.is_file(), path
    if path.suffix == '.svg':
        ET.parse(path)
# The migration audit is retained locally but is not part of the course repository.
rows = []
triage = root / 'docs/slide-triage.md'
if triage.is_file():
    rows = re.findall(r'^\| (\d+) \|.*?\| (KEEP|MERGE|MOVE|CUT|REBUILD) \|',
                      triage.read_text(), re.M)
    assert [int(i) for i, _ in rows] == list(range(1, 454))
pdf = fitz.open(root / 'exports/ai5049-reefnet.pdf')
assert len(pdf) == len(slides)
for name in ['exports/ai5049-reefnet.html', 'build/qa/slides.html']:
    html = (root / name).read_text()
    assert 'src="assets/' not in html, name
    assert html.count('<section ') == len(slides), name
qa = json.loads((root / 'build/qa/layout-report.json').read_text())
assert qa == {'slides': len(slides), 'issues': []}, qa
for name in ['preview-report.json', 'pdf-report.json']:
    report = json.loads((root / 'build/qa' / name).read_text())
    assert report == {'slides': len(slides), 'issues': []}, (name, report)
svg_qa = json.loads((root / 'build/qa/svg-report.json').read_text())
assert svg_qa['assets'] == len(assets) and not svg_qa['issues'], svg_qa
alignment = json.loads((root / 'build/qa/node-alignment-report.json').read_text())
assert alignment['groups'] > 200 and not alignment['issues'], alignment
assert '.py' not in re.sub(r'<!--.*?-->', '', text, flags=re.S)
print(f'{len(slides)} slides; {len(assets)} local SVG assets; HTML/PDF/QA consistent.')
print('Technical core mix:', dict(Counter(r['kind'] for r in manifest if r['section'] in
      {'Networking 101', 'Network Operations', 'Network Automation', 'Monitoring / Observability'})))
if rows:
    print('Local migration audit:', dict(Counter(a for _, a in rows)))
