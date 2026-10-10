#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/ui.sh"

fqdn=${1:?usage: enter.sh <device-fqdn>}
mode=shell
case "$fqdn" in
  operations01.bob1.reefnet.test)
    container=clab-ai5049-ops01
    title="$fqdn / operator workstation"
    hint='ssh edge01.bob1.reefnet.test  /  gnmic -a edge01.bob1.reefnet.test:57400 --encoding json_ietf ...'
    ;;
  probe01.bob1.lagoontransit.test)
    container=clab-ai5049-host01
    title="$fqdn / Lagoon Transit side"
    hint='ip -br addr  /  ip route  /  dig data.oceanresearch.test  /  ping -4 198.51.100.10'
    ;;
  probe01.bob1.pacifictransit.test)
    container=clab-ai5049-host02
    title="$fqdn / Pacific Transit side"
    hint='ip -br addr  /  ip route  /  ping -4 198.51.100.10  /  traceroute -n -4 198.51.100.10'
    ;;
  service01.bob1.oceanresearch.test)
    container=clab-ai5049-svc01
    title="$fqdn / Bora Bora Ocean Research service"
    hint='tail -f /tmp/iperf-server.log'
    ;;
  edge01.bob1.reefnet.test)
    container=clab-ai5049-edge01; mode=srl; title="$fqdn / SR Linux"; hint='show network-instance default protocols bgp neighbor' ;;
  edge02.bob1.reefnet.test)
    container=clab-ai5049-edge02; mode=srl; title="$fqdn / SR Linux"; hint='show network-instance default protocols ospf neighbor' ;;
  edge01.bob1.oceanresearch.test)
    container=clab-ai5049-cust01; mode=srl; title="$fqdn / SR Linux"; hint='show network-instance default protocols bgp neighbor' ;;
  edge01.bob1.lagoontransit.test)
    container=clab-ai5049-transit01; mode=srl; title="$fqdn / SR Linux"; hint='show network-instance default protocols bgp neighbor' ;;
  edge01.bob1.pacifictransit.test)
    container=clab-ai5049-transit02; mode=srl; title="$fqdn / SR Linux"; hint='show network-instance default protocols bgp neighbor' ;;
  *)
    ui_fail "Unknown lab device: $fqdn"
    ui_hint 'Use a device FQDN from the topology, e.g. operations01.bob1.reefnet.test'
    exit 2
    ;;
esac

if ! docker inspect "$container" >/dev/null 2>&1; then
  ui_fail "$fqdn is not running"
  ui_hint 'Start a scenario first, e.g. make networking'
  exit 1
fi

if [[ "$mode" == srl ]]; then
  ui_banner "$title" 'Opening the SR Linux CLI / use quit to return to your normal terminal'
else
  ui_banner "$title" 'Opening the lab node / use exit to return to your normal terminal'
fi
ui_hint "$hint"
echo
if [[ "$fqdn" == operations01.bob1.reefnet.test ]]; then
  docker exec "$container" sh -lc 'mkdir -p /root/.ssh && cp /opt/ai5049/ssh_config /root/.ssh/config && chown root:root /root/.ssh /root/.ssh/config && chmod 0700 /root/.ssh && chmod 0600 /root/.ssh/config'
fi

if [[ "$mode" == srl ]]; then
  exec docker exec -it "$container" bash -lc \
    "su -s /bin/bash admin -c '/opt/srlinux/bin/sr_cli'"
fi
# Refresh the greeting even when the running lab uses an older tools image.
docker cp "$(dirname "$0")/../tools/welcome.sh" "$container:/etc/profile.d/ai5049.sh" >/dev/null
# A command failure inside the interactive shell is not a failure to enter it.
# Normalize the session's exit status inside Docker so Docker launch errors survive.
exec docker exec -it "$container" bash -c 'bash -l; exit 0'
