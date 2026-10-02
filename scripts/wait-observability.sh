#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/ui.sh"
quiet=0
[[ ${1:-} == --quiet ]] && quiet=1
containers=(clab-ai5049-gnmic clab-ai5049-prometheus clab-ai5049-alloy clab-ai5049-loki clab-ai5049-grafana)
check_container_states() {
  local name state
  for name in "${containers[@]}"; do
    if ! docker inspect "$name" >/dev/null 2>&1; then ui_fail "Missing container · $name"; return 1; fi
    state=$(docker inspect -f '{{.State.Status}}' "$name" 2>/dev/null || echo unknown)
    case "$state" in exited|dead|restarting) ui_fail "$name · $state"; return 1 ;; esac
  done
}
prometheus_ready() { curl -fsS --max-time 2 http://localhost:9090/-/ready >/dev/null 2>&1; }
loki_ready()       { curl -fsS --max-time 2 http://localhost:3100/ready >/dev/null 2>&1; }
alloy_ready()      { curl -fsS --max-time 2 http://localhost:12345/-/ready >/dev/null 2>&1 && curl -fsS --max-time 2 http://localhost:12345/-/healthy >/dev/null 2>&1; }
grafana_ready()    { curl -fsS --max-time 2 http://localhost:3000/api/health >/dev/null 2>&1; }
gnmic_ready()      { docker exec clab-ai5049-ops01 curl -fsS --max-time 2 http://clab-ai5049-gnmic:9804/metrics >/dev/null 2>&1; }
prom_scrape_ready() { local t; t=$(curl -fsS --max-time 2 http://localhost:9090/api/v1/targets 2>/dev/null || true); grep -q 'clab-ai5049-gnmic:9804' <<<"$t" && grep -q '"health":"up"' <<<"$t"; }
queue_collection_ready() {
  curl -fsSG --max-time 2 --data-urlencode 'query=(sum(up{job="reefnet-qdisc"}) == 5) and (sum(reefnet_qdisc_present) == 6)' \
    http://localhost:9090/api/v1/query | python3 -c 'import json,sys; sys.exit(len(json.load(sys.stdin)["data"]["result"]) != 1)' >/dev/null 2>&1
}
names=('Prometheus' 'Loki' 'Alloy' 'Grafana' 'gNMIc metrics' 'Prometheus → gNMIc' 'Capacity queue collection')
checks=(prometheus_ready loki_ready alloy_ready grafana_ready gnmic_ready prom_scrape_ready queue_collection_ready)
declare -a done_state=(0 0 0 0 0 0 0)
start=$(date +%s); last_pending=-10
for _ in $(seq 1 120); do
  check_container_states || exit 1
  all=1; pending=()
  for i in "${!checks[@]}"; do
    [[ ${done_state[$i]} -eq 1 ]] && continue
    if "${checks[$i]}"; then
      done_state[$i]=1
      (( quiet )) || ui_ok "${names[$i]}"
    else
      all=0; pending+=("${names[$i]}")
    fi
  done
  (( all )) && exit 0
  elapsed=$(( $(date +%s) - start ))
  if (( ! quiet && elapsed >= last_pending + 10 )); then
    ui_pending_line "${elapsed}s · waiting for: $(IFS=', '; echo "${pending[*]}")"
    last_pending=$elapsed
  fi
  sleep 1
done
ui_fail 'Observability did not become ready within 120 seconds'
for i in "${!checks[@]}"; do [[ ${done_state[$i]} -eq 1 ]] || ui_fail "Not ready · ${names[$i]}"; done
exit 1
