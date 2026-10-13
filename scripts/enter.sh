#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/ui.sh"

fqdn=${1:?usage: enter.sh <device-fqdn>}
# Accept the short container names that docker ps shows.
case "$fqdn" in
  ops01) fqdn=operations01.bob1.reefnet.test ;;
  edge01) fqdn=edge01.bob1.reefnet.test ;;
  edge02) fqdn=edge02.bob1.reefnet.test ;;
  cust01) fqdn=edge01.bob1.oceanresearch.test ;;
  transit01) fqdn=edge01.bob1.lagoontransit.test ;;
  transit02) fqdn=edge01.bob1.pacifictransit.test ;;
  host01) fqdn=probe01.bob1.lagoontransit.test ;;
  host02) fqdn=probe01.bob1.pacifictransit.test ;;
  svc01) fqdn=service01.bob1.oceanresearch.test ;;
esac
mode=shell
case "$fqdn" in
  operations01.bob1.reefnet.test)
    container=clab-ai5049-ops01
    ;;
  probe01.bob1.lagoontransit.test)
    container=clab-ai5049-host01
    ;;
  probe01.bob1.pacifictransit.test)
    container=clab-ai5049-host02
    ;;
  service01.bob1.oceanresearch.test)
    container=clab-ai5049-svc01
    ;;
  edge01.bob1.reefnet.test)
    container=clab-ai5049-edge01
    mode=srl
    ;;
  edge02.bob1.reefnet.test)
    container=clab-ai5049-edge02
    mode=srl
    ;;
  edge01.bob1.oceanresearch.test)
    container=clab-ai5049-cust01
    mode=srl
    ;;
  edge01.bob1.lagoontransit.test)
    container=clab-ai5049-transit01
    mode=srl
    ;;
  edge01.bob1.pacifictransit.test)
    container=clab-ai5049-transit02
    mode=srl
    ;;
  *)
    ui_fail "Unknown lab device: $fqdn"
    ui_hint 'Device names and short names: make info'
    exit 2
    ;;
esac

if ! docker inspect "$container" >/dev/null 2>&1; then
  ui_fail "$fqdn is not running"
  ui_hint 'Start a scenario first, e.g. make networking'
  exit 1
fi

if [[ "$fqdn" == operations01.bob1.reefnet.test ]]; then
  docker exec "$container" sh -lc 'mkdir -p /root/.ssh && cp /opt/ai5049/ssh_config /root/.ssh/config && chown root:root /root/.ssh /root/.ssh/config && chmod 0700 /root/.ssh && chmod 0600 /root/.ssh/config'
fi

if [[ "$mode" == srl ]]; then
  exec docker exec -it "$container" bash -lc \
    "su -s /bin/bash admin -c '/opt/srlinux/bin/sr_cli'; status=\$?; if [[ \$status -eq 1 ]]; then exit 0; else exit \$status; fi"
fi
# Refresh the greeting even when the running lab uses an older tools image.
docker cp "$(dirname "$0")/../tools/welcome.sh" "$container:/etc/profile.d/ai5049.sh" >/dev/null
# The multitool prompt shows \h (probe01). Show the full name to avoid ambiguity.
docker exec "$container" sed -i 's/\[${cHST}\\h/[${cHST}\\H/' /root/.bashrc 2>/dev/null || true
# A command failure inside the interactive shell is not a failure to enter it.
# Normalize the session's exit status inside Docker so Docker launch errors survive.
exec docker exec -it "$container" bash -c 'bash -l; exit 0'
