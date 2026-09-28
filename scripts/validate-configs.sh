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
run 'Grafana dashboard JSON' docker run --rm --entrypoint /bin/sh -v "$root/configs/grafana/dashboards:/dashboards:ro" ai5049-tools:bob1-v20 -lc 'for f in /dashboards/*.json; do jq empty "$f"; done'
run 'Grafana auto refresh' docker run --rm --entrypoint /bin/sh -v "$root/configs/grafana/dashboards:/dashboards:ro" ai5049-tools:bob1-v20 -lc 'for f in /dashboards/*.json; do jq -e '"'"'.refresh == "5s" and (.timepicker.refresh_intervals | index("5s") != null)'"'"' "$f" >/dev/null; done'
run 'Grafana dashboard filters' docker run --rm --entrypoint /bin/sh -v "$root/configs/grafana/dashboards:/dashboards:ro" ai5049-tools:bob1-v20 -lc 'jq -e '"'"'([.templating.list[].name] | index("device") != null and index("interface") != null and index("probe_source") != null and index("quality") == null)'"'"' /dashboards/01-fault-analysis.json >/dev/null && jq -e '"'"'([.templating.list[].name] | index("probe_source") != null and index("af") != null and index("probe_type") != null)'"'"' /dashboards/02-service-health.json >/dev/null && jq -e '"'"'([.templating.list[].name] | index("job") != null and index("device") != null)'"'"' /dashboards/03-telemetry-health.json >/dev/null && jq -e '"'"'.uid == "reefnet-bob1-topology" and ([.templating.list[].name] | index("link") != null and index("quality") == null)'"'"' /dashboards/05-topology-paths.json >/dev/null'
run 'Grafana interface state views' docker run --rm --entrypoint /bin/sh -v "$root/configs/grafana/dashboards:/dashboards:ro" ai5049-tools:bob1-v20 -lc 'jq -e '"'"'.panels | any(.title == "Selected interfaces · admin state") and any(.title == "Selected interfaces · oper state") and any(.title == "Discards · 5m") and any(.title == "Errors · 5m") and any(.title == "FCS errors · 5m")'"'"' /dashboards/01-fault-analysis.json >/dev/null && jq -e '"'"'.panels | any(.title == "Interface admin state") and any(.title == "Interface oper state") and any(.title == "BGP route totals") and (any(.title == "IPv4 route table") | not) and (any(.title == "IPv6 route table") | not)'"'"' /dashboards/04-device-detail.json >/dev/null && jq -e '"'"'.panels | any(.title == "Selected links · admin state") and any(.title == "Selected links · oper state") and any(.title == "Discards · 5m") and any(.title == "Errors · 5m") and any(.title == "FCS errors · 5m") and (any(.title == "Physical link inventory · endpoints, interfaces and routing role") | not) and (any(.title == "ReefNet IPv4 route tables") | not) and (any(.title == "ReefNet IPv6 route tables") | not)'"'"' /dashboards/05-topology-paths.json >/dev/null'

run 'Grafana topology model' docker run --rm --entrypoint /bin/sh -v "$root/configs/grafana/dashboards:/dashboards:ro" ai5049-tools:bob1-v20 -lc 'jq -e '"'"'.panels[] | select(.type == "canvas") | .options.root.elements as $e | ([ $e[] | select(.name == "ReefNet Edge 01") | .connections[] | select(.targetName == "ReefNet Edge 02") ] | length == 2) and ([ $e[] | .connections[]? | select(.targetName == "Core A" or .targetName == "Core B") ] | length == 0) and ([ $e[] | .connections[]? | select(.direction != "none") ] | length == 0)'"'"' /dashboards/05-topology-paths.json >/dev/null'
run 'Grafana datasource wiring' docker run --rm --entrypoint /bin/sh -v "$root/configs/grafana/dashboards:/dashboards:ro" ai5049-tools:bob1-v20 -lc 'jq -e '"'"'.panels[] | select(.title == "Loki events · last 5m") | .datasource.uid == "loki"'"'"' /dashboards/03-telemetry-health.json >/dev/null'
run 'Containerlab topology' containerlab validate -t lab.clab.yml
run 'NetBox Compose model' docker compose -f compose.netbox.yml config -q
run 'Grafana Alloy configuration' docker run --rm -v "$root/configs/alloy/alloy-config.alloy:/etc/alloy/config.alloy:ro" grafana/alloy:v1.16.0 validate /etc/alloy/config.alloy
run 'Grafana Loki configuration' docker run --rm -v "$root/configs/loki/loki-config.yml:/etc/loki/loki-config.yml:ro" grafana/loki:3.7.1 -config.file=/etc/loki/loki-config.yml -verify-config
run 'Prometheus configuration' docker run --rm --entrypoint /bin/promtool -v "$root/configs/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro" -v "$root/configs/prometheus/reefnet.rules.yml:/etc/prometheus/reefnet.rules.yml:ro" quay.io/prometheus/prometheus:v3.11.3 check config /etc/prometheus/prometheus.yml
run 'Prometheus recording rules' docker run --rm --entrypoint /bin/promtool -v "$root/configs/prometheus/reefnet.rules.yml:/etc/prometheus/reefnet.rules.yml:ro" quay.io/prometheus/prometheus:v3.11.3 check rules /etc/prometheus/reefnet.rules.yml
ui_success_banner 'CONFIGURATION VALID'
