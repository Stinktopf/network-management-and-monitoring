#!/usr/bin/env bash
set -eEuo pipefail
source "$(dirname "$0")/ui.sh"
current='initialization'; mkdir -p .state
fail() { rc=$?; trap - ERR; ui_error_banner "COURSE CHECK FAILED · $current"; exit "$rc"; }
trap fail ERR
step() { current=$1; ui_section "$current"; }
cmd() { ui_cmd "$@"; "$@"; }

prom_expect() {
  local label=$1
  local query=$2
  local ok=0
  for i in $(seq 1 15); do
    if docker exec clab-ai5049-ops01 sh -c "curl -fsSG --data-urlencode 'query=${query}' http://clab-ai5049-prometheus:9090/api/v1/query | jq -e '.data.result | length > 0'" >/dev/null 2>&1; then
      ok=1
      break
    fi
    sleep 1
  done
  [[ $ok == 1 ]]
  ui_ok "${label}"
}
step 'DNS · probe01.bob1.lagoontransit.test'
cmd docker exec clab-ai5049-host01 sh -c 'dig +short data.oceanresearch.test A | tee /tmp/ai5049-dns-check | grep -qx 198.51.100.10'
ui_ok 'data.oceanresearch.test → 198.51.100.10'
cmd docker exec clab-ai5049-host01 sh -c 'dig @2001:db8:100::10 +short data.oceanresearch.test AAAA | grep -qx 2001:db8:100::10'
ui_ok 'DNS is reachable over IPv6 as well'
step 'NetBox · inventory'
cmd bash scripts/netbox-check.sh
ui_ok 'Site, devices, IPAM, ASNs, circuits, cables and services verified'
step 'Operator SSH config · FQDN access'
cmd docker exec clab-ai5049-ops01 sh -c 'test "$(stat -c %U:%a /root/.ssh/config)" = root:600'
cmd docker exec clab-ai5049-ops01 sh -c "grep -qx '172.20.20.11 edge01.bob1.reefnet.test' /etc/hosts && ssh -G edge01.bob1.reefnet.test 2>/dev/null | grep -qx 'user admin'"
ui_ok 'SSH config is root-owned and resolves router FQDNs'
step 'gNMI read · edge01.bob1.reefnet.test'
cmd docker exec clab-ai5049-ops01 gnmic -a edge01.bob1.reefnet.test:57400 -u admin -p 'NokiaSrl1!' --skip-verify --encoding json_ietf --timeout 10s get --path '/interface[name=ethernet-1/1]/admin-state' --path '/interface[name=ethernet-1/1]/oper-state'
ui_ok 'gNMI admin and oper state reads work'
step 'Operations fault · IPv4 export'
cmd bash scripts/fault-routing.sh
cmd bash scripts/verify-scenario.sh operations
ui_ok 'Expected IPv4-only failure externally visible'
step 'Automation repair · gNMI Set'
cmd docker exec clab-ai5049-ops01 gnmic -a edge01.bob1.reefnet.test:57400 -u admin -p 'NokiaSrl1!' --skip-verify --encoding json_ietf --timeout 10s set --delete '/network-instance[name=default]/protocols/bgp/group[group-name=lagoon-v4]/export-policy'
ui_wait 'Waiting for routing after API change'
cmd bash scripts/wait-healthy.sh
cmd bash scripts/verify-scenario.sh networking
ui_ok 'gNMI repair restored healthy state'
step 'Link fault + recovery'
cmd bash scripts/fault-link.sh
prom_expect 'core-b admin state becomes disabled' 'reefnet_cabled_interface_admin_enabled{source="edge01.bob1.reefnet.test",interface_name="ethernet-1/4"} == 0'
prom_expect 'core-b oper state becomes down' 'reefnet_cabled_interface_oper_up{source="edge01.bob1.reefnet.test",interface_name="ethernet-1/4"} == 0'
cmd bash scripts/clear-link.sh
cmd bash scripts/wait-healthy.sh
prom_expect 'core-b admin state recovers to enabled' 'reefnet_cabled_interface_admin_enabled{source="edge01.bob1.reefnet.test",interface_name="ethernet-1/4"} == 1'
prom_expect 'core-b oper state recovers to up' 'reefnet_cabled_interface_oper_up{source="edge01.bob1.reefnet.test",interface_name="ethernet-1/4"} == 1'
ui_ok 'Link fault/recovery and admin/oper telemetry work'
step 'Classroom capacity profile'
cmd bash scripts/apply-capacity-profile.sh
ui_ok '100 Mbit/s customer and 50 Mbit/s transit capacities applied'
step 'Traffic path · iperf3'
cmd bash scripts/traffic.sh burst 40M
ui_ok 'Traffic path works'
step 'Prometheus · gNMI telemetry'
prom_ok=0
for i in $(seq 1 20); do
  if docker exec clab-ai5049-ops01 sh -c 'curl -fsSG --data-urlencode '\''query={__name__=~"ai5049_.*"}'\'' http://clab-ai5049-prometheus:9090/api/v1/query | jq -e ".data.result | length > 0"' >/dev/null 2>&1; then prom_ok=1; break; fi
  (( i % 5 == 0 )) && ui_pending_line "Prometheus telemetry · ${i}s"
  sleep 1
done
[[ $prom_ok == 1 ]]; ui_ok 'Prometheus contains gNMI telemetry'

step 'Prometheus · dashboard telemetry families'
for metric in reefnet_interface_admin_state reefnet_interface_oper_state reefnet_interface_admin_enabled reefnet_interface_oper_up reefnet_cabled_interface_admin_enabled reefnet_cabled_interface_oper_up reefnet_interface_in_bps reefnet_interface_out_bps reefnet_interface_quality_events_total reefnet_bgp_up_peers reefnet_bgp_total_active_routes reefnet_bgp_route_total reefnet_link_admin_enabled reefnet_link_oper_up reefnet_link_in_bps reefnet_link_out_bps reefnet_link_quality_events_total reefnet_link_capacity_bps reefnet_link_utilization_ratio; do
  metric_ok=0
  for i in $(seq 1 25); do
    if docker exec clab-ai5049-ops01 sh -c "curl -fsSG --data-urlencode 'query=${metric}' http://clab-ai5049-prometheus:9090/api/v1/query | jq -e '.data.result | length > 0'" >/dev/null 2>&1; then metric_ok=1; break; fi
    sleep 1
  done
  if [[ $metric_ok != 1 ]]; then
    ui_warn "${metric} is missing"
    if [[ $metric == reefnet_bgp_* ]]; then
      ui_hint 'Raw BGP metric names currently exposed by gNMIc:'
      docker exec clab-ai5049-ops01 sh -c "curl -fsS http://clab-ai5049-gnmic:9804/metrics | grep '^ai5049_.*bgp' | cut -d'{' -f1 | sort -u | head -40" || true
    fi
    false
  fi
  ui_ok "${metric} available"
done


step 'Prometheus · capacity queue telemetry'
prom_expect 'All five queue exporters are up' 'sum(up{job="reefnet-qdisc"}) == 5'
prom_expect 'All six capacity queues are present' 'sum(reefnet_qdisc_present) == 6'
prom_expect 'Lagoon sending queue is visible' 'reefnet_qdisc_dropped_packets_total{source="edge01.bob1.lagoontransit.test",interface_name="ethernet-1/1",link_id="lagoon"}'
prom_expect 'Topology includes Lagoon output discards' 'reefnet_link_out_discards_total{source="edge01.bob1.lagoontransit.test",link_id="lagoon"}'
cmd bash scripts/traffic.sh burst 75M
prom_expect 'Overload increases actual Lagoon queue drops' 'increase(reefnet_qdisc_dropped_packets_total{source="edge01.bob1.lagoontransit.test",link_id="lagoon"}[30s]) > 0'

step 'Prometheus · overview dashboard queries'
prom_expect 'Edge 01 BGP query returns data' 'reefnet_bgp_up_peers{source="edge01.bob1.reefnet.test"}'
prom_expect 'Edge 02 BGP query returns data' 'reefnet_bgp_up_peers{source="edge02.bob1.reefnet.test"}'
prom_expect 'Customer handoff traffic query returns data' 'reefnet_interface_in_bps{source="edge01.bob1.reefnet.test",interface_name="ethernet-1/1"}'
prom_expect 'Lagoon handoff traffic query returns data' 'reefnet_interface_out_bps{source="edge01.bob1.reefnet.test",interface_name="ethernet-1/3"}'
prom_expect 'ReefNet core traffic query returns data' 'reefnet_interface_in_bps{source="edge01.bob1.reefnet.test",interface_name="ethernet-1/2"}'
prom_expect 'ReefNet BGP route query returns data' 'reefnet_bgp_total_active_routes{source="edge01.bob1.reefnet.test"}'
prom_expect 'Cabled interface admin state is enabled' 'reefnet_cabled_interface_admin_enabled{source="edge01.bob1.reefnet.test",interface_name="ethernet-1/1"} == 1'
prom_expect 'Cabled interface oper state is up' 'reefnet_cabled_interface_oper_up{source="edge01.bob1.reefnet.test",interface_name="ethernet-1/1"} == 1'
prom_expect 'Interface discard query returns data' 'reefnet_interface_in_discards_total{source="edge01.bob1.reefnet.test",interface_name="ethernet-1/1"}'
prom_expect 'Interface error query returns data' 'reefnet_interface_in_errors_total{source="edge01.bob1.reefnet.test",interface_name="ethernet-1/1"}'
prom_expect 'Interface egress discard query returns data' 'reefnet_interface_out_discards_total{source="edge01.bob1.reefnet.test",interface_name="ethernet-1/1"}'
prom_expect 'Device BGP view selector query returns data' 'reefnet_bgp_route_total{source="edge01.bob1.reefnet.test",route_view="active"}'
prom_expect 'Topology link admin state is enabled' 'reefnet_link_admin_enabled{link_id="core-b"} == 1'
prom_expect 'Topology link oper state is up' 'reefnet_link_oper_up{link_id="core-b"} == 1'
prom_expect 'Topology Lagoon → ReefNet direction returns data' 'reefnet_link_in_bps{link_id="lagoon",traffic_direction="Lagoon Transit → ReefNet"}'
prom_expect 'Topology ReefNet → Ocean Research direction returns data' 'reefnet_link_out_bps{link_id="customer",traffic_direction="ReefNet → Ocean Research"}'
prom_expect 'Topology utilization query returns data' 'reefnet_link_utilization_ratio{link_id="lagoon"}'

step 'Loki · SR Linux logs'
loki_ok=0
for i in $(seq 1 20); do
  if docker exec clab-ai5049-ops01 sh -c 'curl -fsSG --data-urlencode '\''query={job="srlinux"}'\'' --data-urlencode '\''limit=5'\'' http://clab-ai5049-loki:3100/loki/api/v1/query_range | jq -e ".data.result | length > 0"' >/dev/null 2>&1; then loki_ok=1; break; fi
  (( i % 5 == 0 )) && ui_pending_line "Loki SR Linux logs · ${i}s"
  sleep 1
done
[[ $loki_ok == 1 ]]; ui_ok 'Loki contains SR Linux logs'

step 'Loki · event counter'
loki_count_query='sum(count_over_time({job="srlinux"} != "Unable to retrieve TLS profile" != "No valid license" != "no default license file nor configured license instances" != "Memory utilization on ram module" != "CPU utilization on cpu module" != "LogSetConfigLevelsToWarning" != "HandleFibMgrNhResolve"[5m])) or on() vector(0)'
docker exec clab-ai5049-ops01 sh -c 'curl -fsSG --data-urlencode "query=$1" http://clab-ai5049-loki:3100/loki/api/v1/query | jq -e ".data.result | length > 0"' sh "$loki_count_query" >/dev/null
ui_ok 'Loki event counter returns a value'
step 'Prometheus · active service probes'
for _ in $(seq 1 20); do
  if docker exec clab-ai5049-ops01 sh -c 'curl -fsS "http://clab-ai5049-prometheus:9090/api/v1/query?query=reefnet_probe_success" | jq -e ".data.result | length == 8"' >/dev/null 2>&1; then break; fi
  sleep 1
done
docker exec clab-ai5049-ops01 sh -c 'curl -fsS "http://clab-ai5049-prometheus:9090/api/v1/query?query=reefnet_probe_success" | jq -e ".data.result | length == 8"' >/dev/null
ui_ok 'Active service probes visible in Prometheus'

step 'Grafana · ReefNet / BOB1 dashboards'
grafana_ok=0
for i in $(seq 1 20); do
  if curl -fsS 'http://localhost:3000/api/dashboards/uid/reefnet-bob1-overview' >/dev/null 2>&1 \
    && curl -fsS 'http://localhost:3000/api/dashboards/uid/reefnet-bob1-faults' >/dev/null 2>&1 \
    && curl -fsS 'http://localhost:3000/api/dashboards/uid/reefnet-bob1-service' >/dev/null 2>&1 \
    && curl -fsS 'http://localhost:3000/api/dashboards/uid/reefnet-bob1-telemetry' >/dev/null 2>&1 \
    && curl -fsS 'http://localhost:3000/api/dashboards/uid/reefnet-bob1-device' >/dev/null 2>&1 \
    && curl -fsS 'http://localhost:3000/api/dashboards/uid/reefnet-bob1-topology' >/dev/null 2>&1; then
    grafana_ok=1
    break
  fi
  (( i % 5 == 0 )) && ui_pending_line "Grafana dashboards · ${i}s"
  sleep 1
done
[[ $grafana_ok == 1 ]]
ui_ok 'All six ReefNet / BOB1 dashboards provisioned'

step 'Grafana · dashboard auto refresh'
for uid in reefnet-bob1-overview reefnet-bob1-topology reefnet-bob1-faults reefnet-bob1-service reefnet-bob1-telemetry reefnet-bob1-device; do
  curl -fsS "http://localhost:3000/api/dashboards/uid/$uid" | jq -e '.dashboard.refresh == "5s"' >/dev/null
done
ui_ok 'All six dashboards refresh every 5 seconds'

step 'Grafana · drilldown controls'
curl -fsS 'http://localhost:3000/api/dashboards/uid/reefnet-bob1-faults' | jq -e '.dashboard.templating.list | map(.name) | index("device") != null and index("interface") != null and index("probe_source") != null and index("quality") == null and index("bgp_view") != null' >/dev/null
curl -fsS 'http://localhost:3000/api/dashboards/uid/reefnet-bob1-service' | jq -e '.dashboard.templating.list | map(.name) | index("probe_source") != null and index("af") != null and index("probe_type") != null' >/dev/null
curl -fsS 'http://localhost:3000/api/dashboards/uid/reefnet-bob1-telemetry' | jq -e '.dashboard.templating.list | map(.name) | index("job") != null and index("device") != null' >/dev/null
curl -fsS 'http://localhost:3000/api/dashboards/uid/reefnet-bob1-topology' | jq -e '.dashboard.panels | any(.type == "canvas")' >/dev/null
curl -fsS 'http://localhost:3000/api/dashboards/uid/reefnet-bob1-topology' | jq -e '.dashboard.panels[] | select(.type == "canvas") | .options.root.elements as $e | ([ $e[] | select(.name == "ReefNet Edge 01") | .connections[] | select(.targetName == "ReefNet Edge 02") ] | length == 2) and ([ $e[] | .connections[]? | select(.targetName == "Core A" or .targetName == "Core B") ] | length == 0)' >/dev/null
curl -fsS 'http://localhost:3000/api/dashboards/uid/reefnet-bob1-faults' | jq -e '.dashboard.panels | any(.title == "Selected interfaces · admin state") and any(.title == "Selected interfaces · oper state") and any(.title == "Ingress discards · 5m") and any(.title == "Errors · 5m") and any(.title == "Egress discards · 5m")' >/dev/null
curl -fsS 'http://localhost:3000/api/dashboards/uid/reefnet-bob1-device' | jq -e '.dashboard.panels | any(.title == "Interface admin state") and any(.title == "Interface oper state")' >/dev/null
curl -fsS 'http://localhost:3000/api/dashboards/uid/reefnet-bob1-topology' | jq -e '.dashboard.panels | any(.title == "Selected links · admin state") and any(.title == "Selected links · oper state") and any(.title == "Selected links · traffic by direction") and (any(.title == "Selected links · receive traffic") | not) and (any(.title == "Selected links · transmit traffic") | not) and any(.title == "Ingress discards · 5m") and any(.title == "Errors · 5m") and any(.title == "Egress discards · 5m") and (any(.title == "Physical link inventory · endpoints, interfaces and routing role") | not) and (any(.title == "ReefNet IPv4 route tables") | not) and (any(.title == "ReefNet IPv6 route tables") | not)' >/dev/null
ui_ok 'Drilldowns, topology and interface-state views provisioned'
step 'Restore healthy baseline'
bash scripts/healthy.sh >/dev/null 2>&1 || true; bash scripts/traffic.sh stop >/dev/null 2>&1 || true
cmd bash scripts/wait-healthy.sh
ui_success_banner 'COURSE FEATURE CHECKS PASSED'
trap - ERR
