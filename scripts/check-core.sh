#!/usr/bin/env bash
# Integration test on a healthy lab. Restore every interface changed by this test.
set -euo pipefail
source "$(dirname "$0")/lib.sh"
mkdir -p .state/core-check
changed=''
restore() {
  if [[ -n "$changed" ]]; then
    srl_apply edge01 <<CFG
enter candidate
set / interface $changed admin-state enable
commit now
CFG
  fi
}
trap restore EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

json() { docker exec -i clab-ai5049-ops01 jq "$@"; }
snapshot() {
  local node=$1
  srl_show "$node" 'info from state network-instance default protocols | as json' |
    json -c '{
      ospf: [.ospf.instance[] | {
        version, full: ([.area[].interface[].neighbor[]? |
          select(."adjacency-state" == "full")] | length)
      }] | sort_by(.version),
      bgp: [.bgp.neighbor[] | select(."peer-group" | startswith("ibgp-")) | {
        peer: ."peer-address", state: ."session-state",
        transitions: ."established-transitions", local: .transport."local-address",
        families: [."afi-safi"[] | select(."oper-state" == "up") | ."afi-safi-name"]
      }] | sort_by(.peer)
    }'
}

wait_core() {
  local expected=$1 deadline=$((SECONDS + 120)) node state ready
  while (( SECONDS < deadline )); do
    ready=1
    for node in edge01 edge02; do
      state=$(snapshot "$node")
      printf '%s\n' "$state" > ".state/core-check/$node.json"
      if ! printf '%s\n' "$state" | json -e --argjson n "$expected" '
        (.ospf | map(.version) == ["ospf-v2", "ospf-v3"]) and
        (.ospf | all(.full == $n)) and
        (.bgp | length == 2) and (.bgp | all(.state == "established")) and
        (.bgp | map(.families[]) | sort == ["ipv4-unicast", "ipv6-unicast"])
      ' >/dev/null; then ready=0; fi
    done
    (( ready )) && return 0
    sleep 2
  done
  ui_fail 'Core did not converge. See .state/core-check/*.json'
  return 1
}

services() {
  bash scripts/verify-scenario.sh networking
  local node
  for node in host01 host02; do
    docker exec "clab-ai5049-$node" sh -ec '
      dig -4 @198.51.100.10 +short data.oceanresearch.test A +time=2 +tries=1 | grep -qx 198.51.100.10
      dig -6 @2001:db8:100::10 +short data.oceanresearch.test AAAA +time=2 +tries=1 | grep -qx 2001:db8:100::10
      curl -fsS --max-time 5 -4 http://data.oceanresearch.test/ >/dev/null
      curl -fsS --max-time 5 -6 http://data.oceanresearch.test/ >/dev/null
    '
  done
}

ui_section 'Dual-stack core failover'
wait_core 2
services
for node in edge01 edge02; do
  json -c '.bgp' < ".state/core-check/$node.json" > ".state/core-check/$node-baseline.json"
done
for port in ethernet-1/2 ethernet-1/4; do
  # A healthy baseline is required. Do not enable interfaces left down by a user.
  srl_show edge01 "info from running interface $port | as json" |
    json -e '."admin-state" == "enable"' >/dev/null
  changed=$port
  ui_info "Disabling edge01 $port"
  srl_apply edge01 <<CFG
enter candidate
set / interface $port admin-state disable
commit now
CFG
  wait_core 1
  services
  for node in edge01 edge02; do
    json -c '.bgp' < ".state/core-check/$node.json" > ".state/core-check/$node-current.json"
    cmp ".state/core-check/$node-baseline.json" ".state/core-check/$node-current.json"
  done
  ui_ok "$port down: IPv4/IPv6 ping, DNS and HTTP pass, iBGP sessions unchanged"
  restore
  changed=''
  wait_core 2
  services
  for node in edge01 edge02; do
    json -c '.bgp' < ".state/core-check/$node.json" > ".state/core-check/$node-current.json"
    cmp ".state/core-check/$node-baseline.json" ".state/core-check/$node-current.json"
  done
done
ui_ok 'Both core links restored, OSPFv2/OSPFv3 adjacencies full'
