#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/ui.sh"
heading() { printf '\n%s%s%s\n' "$UI_CYAN$UI_BOLD" "$1" "$UI_RESET"; }
device() { printf '  %s%-36s%s %s%-10s%s %s\n' "$UI_MAGENTA" "$1" "$UI_RESET" "$UI_DIM" "$2" "$UI_RESET" "$3"; }
login() { printf '  %s%-12s%s %s%s%s  %s%s%s\n' "$UI_BOLD" "$1" "$UI_RESET" "$UI_MAGENTA" "$2" "$UI_RESET" "$UI_YELLOW$UI_BOLD" "$3" "$UI_RESET"; }
dashboard() { printf '  %s%-22s%s %s\n' "$UI_BOLD" "$1" "$UI_RESET" "$2"; }

ui_banner 'ReefNet BOB1 · lab info' 'Device names, logins and places to look.' compact

heading 'Devices · make enter NODE=<name or short name>'
device 'operations01.bob1.reefnet.test' 'ops01' 'operator workstation: ssh, gnmic, curl, jq'
device 'edge01.bob1.reefnet.test' 'edge01' 'ReefNet edge router, Lagoon side'
device 'edge02.bob1.reefnet.test' 'edge02' 'ReefNet edge router, Pacific side'
device 'edge01.bob1.oceanresearch.test' 'cust01' 'customer router, Ocean Research'
device 'edge01.bob1.lagoontransit.test' 'transit01' 'Lagoon Transit router'
device 'edge01.bob1.pacifictransit.test' 'transit02' 'Pacific Transit router'
device 'probe01.bob1.lagoontransit.test' 'host01' 'probe behind Lagoon: 203.0.113.10, 2001:db8:a::10'
device 'probe01.bob1.pacifictransit.test' 'host02' 'probe behind Pacific: 203.0.113.138, 2001:db8:b::10'
device 'service01.bob1.oceanresearch.test' 'svc01' 'data.oceanresearch.test: 198.51.100.10, 2001:db8:100::10'

heading 'Logins'
login 'Router CLI' 'make enter NODE=edge01.bob1.reefnet.test' 'no login, leave with quit'
login 'Router SSH' 'ssh edge01.bob1.reefnet.test' 'admin / NokiaSrl1!  (from operations01)'
login 'Router gNMI' 'edge01.bob1.reefnet.test:57400' 'admin / NokiaSrl1!  (from operations01)'
login 'NetBox' 'http://localhost:8000' 'admin / admin'
login 'NetBox API' 'cat /state/netbox-token' 'token, on operations01'

heading 'Web interfaces'
ui_url 'NetBox' 'http://localhost:8000' 'Devices, IPAM, Circuits'
ui_url 'Grafana' 'http://localhost:3000' 'Dashboards → ReefNet / BOB1, no login'
ui_url 'Prometheus' 'http://localhost:9090' 'raw metrics, try the query up'

heading 'Grafana dashboards'
dashboard 'Network Overview' 'live map, failures at a glance'
dashboard 'Service Health' 'ping, DNS and HTTP from both probes over time'
dashboard 'BGP, OSPF' 'sessions, adjacencies, received and active routes'
dashboard 'Devices & Interfaces' 'interface state, discards, device events'
dashboard 'Traffic & Capacity' 'load per link and direction'
dashboard 'Telemetry Health' 'is the monitoring data itself fresh?'

heading 'Tools on the Linux nodes'
printf '  %s%s%s\n' "$UI_MAGENTA" 'ping, traceroute, tracepath, mtr, dig, curl, tcpdump, iperf3, ip' "$UI_RESET"
printf '  %s\n' 'Loss on a middle hop in mtr or traceroute can be ICMP rate limiting.'
printf '  %s\n' 'Only loss that continues to the last hop affects the service.'
echo
