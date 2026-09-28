#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/ui.sh"
ui_section 'Stopping AI5049 lab'
bash scripts/traffic.sh stop >/dev/null 2>&1 || true
docker compose -p ai5049 -f compose.netbox.yml down >/dev/null 2>&1 || true
containerlab destroy -t lab.clab.yml --cleanup >/dev/null 2>&1 || true
rm -f .scenario
ui_ok 'Lab stopped · NetBox data kept'
ui_hint 'Use make clean only when you want a complete fresh start.'
