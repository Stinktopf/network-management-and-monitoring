#!/usr/bin/env bash
# Read-only snapshots: leave the current traffic and capacity profile running.
set -euo pipefail
source "$(dirname "$0")/ui.sh"
root=$(cd "$(dirname "$0")/.." && pwd)
cd "$root"

docker info >/dev/null
mkdir -p .state
report=$(mktemp .state/traffic-diagnostics-XXXXXXXX.log)
failures=0

capture() {
  local label=$1
  shift
  printf '\n--- %s · %s ---\n' "$label" "$(date -Is)" >> "$report"
  if ! timeout 20s "$@" >> "$report" 2>&1; then
    printf 'COLLECTION FAILED: %s\n' "$label" >> "$report"
    failures=$((failures + 1))
  fi
}

ui_info "Collecting two snapshots, 15 seconds apart · $report"
traffic_active=0
printf '\n--- Configured traffic and process status · %s ---\n' "$(date -Is)" >> "$report"
if traffic_status=$(bash scripts/traffic.sh status 2>&1); then
  printf '%s\n' "$traffic_status" >> "$report"
  if [[ $traffic_status == *'Traffic running'* || $traffic_status == *'Traffic reconnecting'* ]]; then
    traffic_active=1
  fi
else
  printf '%s\nCOLLECTION FAILED: Configured traffic and process status' "$traffic_status" >> "$report"
  failures=$((failures + 1))
fi
for sample in 1 2; do
  for endpoint in transit01:e1-1 edge01:e1-3 edge01:e1-1 cust01:e1-1 edge02:e1-2 transit02:e1-1; do
    node=${endpoint%:*}
    interface=${endpoint#*:}
    capture "Sample $sample · Linux qdisc · $endpoint" \
      docker exec "clab-ai5049-$node" tc -s -d qdisc show dev "$interface"
  done
  for device in edge01.bob1.lagoontransit.test edge01.bob1.reefnet.test; do
    capture "Sample $sample · SR Linux interface statistics · $device" \
      docker exec clab-ai5049-ops01 gnmic -a "$device:57400" \
        -u admin -p 'NokiaSrl1!' --skip-verify --encoding json_ietf --timeout 10s \
        get --type state --path '/interface[name=ethernet-1/*]/statistics'
  done
  capture "Sample $sample · Prometheus raw and normalized discard counters" \
    curl --fail --silent --show-error --max-time 10 --get \
      --data-urlencode 'query={__name__=~"ai5049_srl_nokia_interfaces_interface_statistics_(in|out)_discarded_packets|reefnet_interface_(in|out)_discards_total|reefnet_qdisc_dropped_packets_total|reefnet_qdisc_present"}' \
      http://localhost:9090/api/v1/query
  capture "Sample $sample · Prometheus link throughput" \
    curl --fail --silent --show-error --max-time 10 --get \
      --data-urlencode 'query={__name__=~"reefnet_link_(in|out)_bps"}' \
      http://localhost:9090/api/v1/query
  if (( traffic_active )); then
    capture "Sample $sample · iperf sender" \
      docker exec clab-ai5049-host01 tail -n 15 /tmp/iperf-client.log
    capture "Sample $sample · iperf receiver" \
      docker exec clab-ai5049-svc01 tail -n 15 /tmp/iperf-server.log
  else
    printf '\n--- Sample %s · iperf sender and receiver · %s ---\nSkipped: traffic generator is stopped.\n' \
      "$sample" "$(date -Is)" >> "$report"
  fi
  if [[ $sample == 1 ]]; then sleep 15; fi
done

ui_info "Report saved · $report"
ui_info 'Compare netem dropped on transit01:e1-1 between samples with SR Linux discards and receiver loss.'
ui_info 'overlimits is not a packet-loss counter. Missing data or collection errors do not mean zero drops.'
if (( ! traffic_active )); then
  ui_warn 'Traffic was stopped · qdisc, SR Linux and Prometheus snapshots are available, iperf loss evidence is not.'
fi
if (( failures > 0 )); then
  ui_fail "$failures collections failed · see report for details"
  exit 1
fi
ui_ok 'Both snapshots collected'
