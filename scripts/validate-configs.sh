#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/ui.sh"
root=$(cd "$(dirname "$0")/.." && pwd)
cd "$root"
run() {
  local label=$1; shift
  ui_section "$label"
  ui_cmd "$@"
  "$@"
  ui_ok "$label"
}
run 'Shell script syntax' bash -c 'set -e; for f in scripts/*.sh tools/welcome.sh; do bash -n "$f"; done'
run 'Operator SSH configuration' docker run --rm --entrypoint /bin/sh ai5049-tools:bob1-v20 -lc "ssh -G -F /opt/ai5049/ssh_config edge01.bob1.reefnet.test 2>/dev/null | grep -qx 'user admin'"
run 'BOB1 model consistency' docker run --rm --entrypoint /bin/sh -v "$root:/lab:ro" ai5049-tools:bob1-v20 -lc 'cd /lab && python3 scripts/check-model-consistency.py'
run 'Grafana dashboards' docker run --rm --entrypoint /bin/sh -v "$root:/lab:ro" ai5049-tools:bob1-v20 -lc 'cd /lab && python3 scripts/check-dashboards.py'
run 'Containerlab topology' containerlab validate -t lab.clab.yml
run 'NetBox Compose model' docker compose -f compose.netbox.yml config -q
run 'Grafana Alloy configuration' docker run --rm -v "$root/configs/alloy/alloy-config.alloy:/etc/alloy/config.alloy:ro" grafana/alloy:v1.16.0 validate /etc/alloy/config.alloy
run 'Grafana Loki configuration' docker run --rm -v "$root/configs/loki/loki-config.yml:/etc/loki/loki-config.yml:ro" grafana/loki:3.7.1 -config.file=/etc/loki/loki-config.yml -verify-config
run 'Prometheus configuration' docker run --rm --entrypoint /bin/promtool -v "$root/configs/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro" -v "$root/configs/prometheus/reefnet.rules.yml:/etc/prometheus/reefnet.rules.yml:ro" quay.io/prometheus/prometheus:v3.11.3 check config /etc/prometheus/prometheus.yml
run 'Prometheus recording rules' docker run --rm --entrypoint /bin/promtool -v "$root/configs/prometheus/reefnet.rules.yml:/etc/prometheus/reefnet.rules.yml:ro" quay.io/prometheus/prometheus:v3.11.3 check rules /etc/prometheus/reefnet.rules.yml
ui_success_banner 'CONFIGURATION VALID'
