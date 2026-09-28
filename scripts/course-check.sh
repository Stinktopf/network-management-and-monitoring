#!/usr/bin/env bash
set -eEuo pipefail
if [[ -t 1 && -z ${NO_COLOR:-} ]]; then export AI5049_COLOR=always; fi
source "$(dirname "$0")/ui.sh"
mkdir -p .state
log=.state/course-check.log
scenario_marker=.state/course-check-scenarios
: > "$log"
: > "$scenario_marker"
exec > >(tee -a "$log") 2>&1
phase='course-check initialization'
on_error() {
  rc=$?; trap - ERR
  ui_error_banner "COURSE CHECK FAILED · $phase"
  bash scripts/diagnostics.sh "$phase" 2>&1 | tee .state/last-startup-diagnostics.log || true
  ui_hint "Full course-check log: $log"
  ui_hint 'Diagnostic snapshot: .state/last-startup-diagnostics.log'
  exit "$rc"
}
trap on_error ERR
ui_banner 'AI5049 Instructor Course Check · BOB1' 'Runs the selected course scenarios and the core actions used in the live slides.'
ui_info 'Run this on the exact WSL machine/image set used in class.'
phase='preflight'; ui_section 'Preflight'; bash scripts/preflight.sh
scenario_spec=${AI5049_COURSE_CHECK_SCENARIOS:-'networking operations automation monitoring'}
read -r -a scenarios <<< "$scenario_spec"
for scenario in "${scenarios[@]}"; do
  case "$scenario" in
    networking|operations|automation|monitoring) ;;
    *) ui_fail "Unknown course-check scenario: $scenario"; exit 2 ;;
  esac
  phase="scenario $scenario startup"
  ui_banner "Scenario · ${scenario^^}" 'Starting and exercising the documented classroom workflow'
  AI5049_NO_GUIDE=1 bash scripts/start-scenario.sh "$scenario"
  case "$scenario" in
    networking)
      phase='networking service probes'; ui_section 'Networking checks'
      bash scripts/test.sh
      docker exec clab-ai5049-ops01 sh -c 'test "$(stat -c %U:%a /root/.ssh/config)" = root:600'
      docker exec clab-ai5049-ops01 sh -c "grep -qx '172.20.20.11 edge01.bob1.reefnet.test' /etc/hosts && ssh -G edge01.bob1.reefnet.test 2>/dev/null | grep -qx 'user admin'"
      docker exec clab-ai5049-host01 sh -c 'dig +short data.oceanresearch.test A | grep -qx 198.51.100.10'
      docker exec clab-ai5049-host01 sh -c 'ip route get 198.51.100.10 >/dev/null'
      ;;
    operations)
      phase='operations documented CLI repair'; ui_section 'Operations repair'
      bash scripts/clear-routing.sh; bash scripts/wait-healthy.sh; bash scripts/verify-scenario.sh networking
      ;;
    automation)
      phase='automation NetBox API read'; ui_section 'Automation · NetBox API'
      docker exec clab-ai5049-ops01 sh -c 'TOKEN=$(cat /state/netbox-token); curl -fsS -H "Authorization: Bearer $TOKEN" "http://netbox.bob1.reefnet.test:8080/api/dcim/devices/?name=edge01.bob1.reefnet.test" | jq -e ".count == 1" >/dev/null'
      phase='automation documented gNMI read'; ui_section 'Automation · gNMI read'
      docker exec clab-ai5049-ops01 gnmic -a edge01.bob1.reefnet.test:57400 -u admin -p 'NokiaSrl1!' --skip-verify --encoding json_ietf --timeout 10s get --path '/network-instance[name=default]/protocols/bgp/group[group-name=lagoon-v4]/export-policy' >/dev/null
      phase='automation documented gNMI repair'; ui_section 'Automation · gNMI repair'
      docker exec clab-ai5049-ops01 gnmic -a edge01.bob1.reefnet.test:57400 -u admin -p 'NokiaSrl1!' --skip-verify --encoding json_ietf --timeout 10s set --delete '/network-instance[name=default]/protocols/bgp/group[group-name=lagoon-v4]/export-policy' >/dev/null
      bash scripts/wait-healthy.sh; bash scripts/verify-scenario.sh networking
      ;;
    monitoring)
      phase='monitoring Prometheus telemetry data'; ui_section 'Monitoring · Prometheus'
      for _ in $(seq 1 20); do
        if docker exec clab-ai5049-ops01 sh -c 'curl -fsSG --data-urlencode '\''query={__name__=~"ai5049_.*"}'\'' http://clab-ai5049-prometheus:9090/api/v1/query | jq -e ".data.result | length > 0" >/dev/null' >/dev/null 2>&1; then break; fi
        sleep 1
      done
      docker exec clab-ai5049-ops01 sh -c 'curl -fsSG --data-urlencode '\''query={__name__=~"ai5049_.*"}'\'' http://clab-ai5049-prometheus:9090/api/v1/query | jq -e ".data.result | length > 0" >/dev/null'
      phase='monitoring Grafana dashboard provisioning'; ui_section 'Monitoring · Grafana'
      curl -fsS 'http://localhost:3000/api/dashboards/uid/reefnet-bob1-overview' >/dev/null && curl -fsS 'http://localhost:3000/api/dashboards/uid/reefnet-bob1-device' >/dev/null
      phase='monitoring traffic controls'; ui_section 'Monitoring · Traffic load'; bash scripts/traffic.sh status; bash scripts/traffic.sh set 10M; bash scripts/traffic.sh set 25M; bash scripts/traffic.sh set 40M; bash scripts/traffic.sh stop; bash scripts/traffic.sh burst 40M; bash scripts/traffic.sh set 50M; bash scripts/traffic.sh set 60M; bash scripts/traffic.sh set 75M; bash scripts/traffic.sh set 10M
      phase='monitoring link fault and Loki event path'; ui_section 'Monitoring · Link fault + Loki'; bash scripts/fault-link.sh; sleep 5
      docker exec clab-ai5049-ops01 sh -c 'curl -fsSG --data-urlencode '\''query={job="srlinux"}'\'' --data-urlencode '\''limit=5'\'' http://clab-ai5049-loki:3100/loki/api/v1/query_range | jq -e ".data.result | length > 0" >/dev/null'
      bash scripts/clear-link.sh; sleep 3; bash scripts/verify-scenario.sh monitoring
      phase='monitoring capacity boundary'; ui_section 'Monitoring · Capacity boundary'; bash scripts/traffic.sh set 75M; bash scripts/traffic.sh set 10M
      ;;
  esac
  ui_ok "$scenario scenario passed"
  printf '%s\n' "$scenario" >> "$scenario_marker"
done
phase='final container check'; ui_section 'Final container check'; bash scripts/check-containers.sh
passed_scenarios=$(paste -sd ' ' "$scenario_marker")
ui_success_banner 'COURSE SCENARIO CHECK PASSED'
ui_info "Passed scenarios: $passed_scenarios"
ui_hint "Full report: $log"
trap - ERR
if [[ ${AI5049_COURSE_CHECK_KEEP_UP:-0} != 1 ]]; then
  bash scripts/down.sh
fi
