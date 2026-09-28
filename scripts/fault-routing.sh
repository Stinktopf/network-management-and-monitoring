#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/lib.sh"
ui_info 'Applying planned IPv4 export-policy fault on edge01.bob1.reefnet.test'
srl_apply edge01 <<'CFG'
enter candidate
set / network-instance default protocols bgp group lagoon-v4 export-policy [ BLOCK-CUSTOMER-V4 ]
commit now
CFG
ui_warn 'FAULT ACTIVE · Bora Bora Ocean Research IPv4 filtered toward Lagoon Transit'
ui_wait 'Waiting until the fault is externally visible on probe01.bob1.lagoontransit.test'
for _ in $(seq 1 30); do
  if ! ping4 host01 198.51.100.10 && ping6 host01 2001:db8:100::10; then ui_ok 'Expected symptom visible · Lagoon probe IPv4 fails, IPv6 remains healthy'; exit 0; fi
  sleep 1
done
ui_fail 'Fault did not become externally visible within 30 seconds'
exit 1
