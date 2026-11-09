#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/ui.sh"

CUSTOMER_KBIT=100000
TRANSIT_KBIT=50000

set_rate() {
  local node=$1 interface=$2 rate=$3 label=$4
  ui_cmd containerlab tools netem set -n "$node" -i "$interface" --rate "$rate"
  containerlab tools netem set -n "$node" -i "$interface" --rate "$rate" >/dev/null
  ui_ok "$label"
}

ui_section 'Apply link capacities'
set_rate clab-ai5049-edge01 e1-1 "$CUSTOMER_KBIT" 'edge01.bob1.reefnet.test → edge01.bob1.oceanresearch.test · 100 Mbit/s'
set_rate clab-ai5049-cust01 e1-1 "$CUSTOMER_KBIT" 'edge01.bob1.oceanresearch.test → edge01.bob1.reefnet.test · 100 Mbit/s'
set_rate clab-ai5049-edge01 e1-3 "$TRANSIT_KBIT" 'edge01.bob1.reefnet.test → edge01.bob1.lagoontransit.test · 50 Mbit/s'
set_rate clab-ai5049-transit01 e1-1 "$TRANSIT_KBIT" 'edge01.bob1.lagoontransit.test → edge01.bob1.reefnet.test · 50 Mbit/s'
set_rate clab-ai5049-edge02 e1-2 "$TRANSIT_KBIT" 'edge02.bob1.reefnet.test → edge01.bob1.pacifictransit.test · 50 Mbit/s'
set_rate clab-ai5049-transit02 e1-1 "$TRANSIT_KBIT" 'edge01.bob1.pacifictransit.test → edge02.bob1.reefnet.test · 50 Mbit/s'
ui_info 'Capacity model · customer 100 Mbit/s · transit 50 Mbit/s'
