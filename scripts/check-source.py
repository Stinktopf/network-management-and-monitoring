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
for path in sorted(ROOT.glob("*.md")):
    for target in re.findall(r"\]\(([^)]+)\)", path.read_text()):
        if "://" not in target and not target.startswith("#"):
            resolved = (path.parent / target.split("#")[0]).resolve()
            if not resolved.is_relative_to(ROOT) or not resolved.exists():
                raise SystemExit(f"Broken or external local link: {path.name}: {target}")
subprocess.run(["python3", str(ROOT / "scripts/check-model-consistency.py")], check=True)
subprocess.run(["python3", str(ROOT / "scripts/test-qdisc-exporter.py")], check=True)
subprocess.run(["python3", str(ROOT / "scripts/test-observability.py")], check=True)
print("Source checks passed: shell, Python, JSON, documentation links and BOB1 model")
