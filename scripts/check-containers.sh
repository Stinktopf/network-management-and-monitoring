#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/ui.sh"
expected_running=(clab-ai5049-edge01 clab-ai5049-edge02 clab-ai5049-cust01 clab-ai5049-transit01 clab-ai5049-transit02 clab-ai5049-host01 clab-ai5049-host02 clab-ai5049-svc01 clab-ai5049-ops01 clab-ai5049-gnmic clab-ai5049-prometheus clab-ai5049-alloy clab-ai5049-loki clab-ai5049-grafana ai5049-netbox-postgres ai5049-netbox-redis ai5049-netbox)
fail=0
for name in "${expected_running[@]}"; do
  if ! docker inspect "$name" >/dev/null 2>&1; then ui_fail "Missing container · $name"; fail=1; continue; fi
  state=$(docker inspect -f '{{.State.Status}}' "$name")
  [[ "$state" == running ]] || { ui_fail "$name · state=$state"; fail=1; }
  health=$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$name")
  [[ "$health" != unhealthy ]] || { ui_fail "$name · health=unhealthy"; fail=1; }
done
(( fail == 0 )) || exit 1
ui_ok 'All 17 classroom containers are running'
