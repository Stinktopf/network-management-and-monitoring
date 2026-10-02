#!/usr/bin/env bash
# Read-only evidence for capacity queue startup failures.
set -uo pipefail

capture() {
  local label=$1 rc
  shift
  printf '\n--- %s ---\n' "$label"
  timeout 10s "$@" 2>&1
  rc=$?
  if (( rc != 0 )); then
    printf 'Collection failed with exit code %s\n' "$rc"
  fi
  return 0
}

printf 'Capacity queue diagnostics · %s\n' "$(date -Is)"
capture 'Tools-container Python used by the readiness check' \
  docker exec clab-ai5049-ops01 python3 --version
capture 'Prometheus scrape targets and last errors' \
  docker exec clab-ai5049-ops01 bash -o pipefail -c '
    curl -fsS --max-time 5 http://clab-ai5049-prometheus:9090/api/v1/targets |
      jq -e '\''.data.activeTargets | map(select(.labels.job == "reefnet-qdisc") |
        {scrapeUrl, health, lastError, lastScrape, lastScrapeDuration})'\''
  '
capture 'Prometheus exporter availability and expected queues' \
  curl -fsSG --max-time 5 \
    --data-urlencode 'query={__name__=~"up|reefnet_qdisc_present",job="reefnet-qdisc"}' \
    http://localhost:9090/api/v1/query

for node in edge01 edge02 cust01 transit01 transit02; do
  capture "$node exporter log" \
    docker exec "clab-ai5049-$node" tail -n 40 /tmp/reefnet-qdisc.log
  capture "$node exporter process" \
    docker exec "clab-ai5049-$node" pgrep -af '[q]disc_exporter.py'
  capture "$node hostname and network namespaces" \
    docker exec "clab-ai5049-$node" bash -c 'hostname; ip netns list'
  capture "$node actual root queues" \
    docker exec "clab-ai5049-$node" /usr/sbin/tc -j -s qdisc show
done
