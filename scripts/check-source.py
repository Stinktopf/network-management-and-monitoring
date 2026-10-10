#!/usr/bin/env python3
"""Fast checks for a standalone clone. No Docker or third-party modules needed."""
import ast
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for directory in ("scripts", "tools"):
    for path in (ROOT / directory).glob("*.sh"):
        subprocess.run(["bash", "-n", str(path)], check=True)
    for path in (ROOT / directory).glob("*.py"):
        ast.parse(path.read_text(), filename=str(path))
for directory in ("configs", "tools"):
    for path in (ROOT / directory).rglob("*.json"):
        json.loads(path.read_text())
panel_titles = {
    panel['title']
    for path in (ROOT / 'configs/grafana/dashboards').glob('*.json')
    for panel in json.loads(path.read_text()).get('panels', [])
}
for name in ('validate-configs.sh', 'setup-smoke.sh'):
    source = (ROOT / 'scripts' / name).read_text()
    for title in re.findall(r'(?:any|select)\(\.title == "([^"]+)"\)(?! \| not)', source):
        if title not in panel_titles:
            raise SystemExit(f'Stale Grafana panel assertion in {name}: {title}')
documents = subprocess.check_output(
    ['git', 'ls-files', '--cached', '--others', '--exclude-standard', '--', '*.md'],
    cwd=ROOT, text=True,
).splitlines()
for name in sorted(set(documents)):
    path = ROOT / name
    if not path.exists():
        continue
    for target in re.findall(r"\]\(([^)]+)\)", path.read_text()):
        if "://" not in target and not target.startswith("#"):
            resolved = (path.parent / target.split("#")[0]).resolve()
            if not resolved.is_relative_to(ROOT) or not resolved.exists():
                raise SystemExit(f"Broken or external local link: {path.name}: {target}")
subprocess.run(["python3", str(ROOT / "scripts/check-model-consistency.py")], check=True)
subprocess.run(["python3", str(ROOT / "scripts/test-qdisc-exporter.py")], check=True)
subprocess.run(["python3", str(ROOT / "scripts/test-observability.py")], check=True)
subprocess.run(["python3", str(ROOT / "scripts/test-guides.py")], check=True)
print("Source checks passed: shell, Python, JSON, documentation links and BOB1 model")
