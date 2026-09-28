#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/lib.sh"
ui_info 'Removing the lagoon-v4 export-policy override on edge01.bob1.reefnet.test'
srl_apply edge01 <<'CFG'
enter candidate
delete / network-instance default protocols bgp group lagoon-v4 export-policy
commit now
CFG
ui_ok 'Routing policy restored · Lagoon Transit IPv4 inherits EXPORT-BGP again'
