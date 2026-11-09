#!/usr/bin/env bash
set -euo pipefail
scenario=networking
if [[ -s .scenario ]]; then
  scenario=$(cat .scenario)
fi
exec bash scripts/start-scenario.sh "$scenario"
