#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/ui.sh"
scenario=${1:-networking}
ui_success_banner "LAB READY · BOB1 · ${scenario^^}"
ui_url 'NetBox' 'http://localhost:8000' 'admin / admin'
ui_url 'Grafana' 'http://localhost:3000' 'anonymous access'
ui_url 'Prometheus' 'http://localhost:9090'
echo
ui_info 'Use FQDNs for lab nodes. Containerlab IDs stay an implementation detail.'
case "$scenario" in
  networking)
    ui_subsection 'Start here'
    printf '  %s\n' 'make enter NODE=probe01.bob1.lagoontransit.test'
    printf '  %s\n' 'make enter NODE=operations01.bob1.reefnet.test'
    printf '  %-18s %s\n' 'make test' 'end-to-end reachability'
    echo
    ui_subsection 'On probe01.bob1.lagoontransit.test'
    printf '  %sip -br addr%s\n  %sip route%s\n  %sdig data.oceanresearch.test%s\n  %sping -4 -c 2 198.51.100.10%s\n  %straceroute -n -4 198.51.100.10%s\n' "$UI_CYAN" "$UI_RESET" "$UI_CYAN" "$UI_RESET" "$UI_CYAN" "$UI_RESET" "$UI_CYAN" "$UI_RESET" "$UI_CYAN" "$UI_RESET"
    echo
    ui_subsection 'On operations01.bob1.reefnet.test'
    printf '  %sssh edge01.bob1.reefnet.test%s  %sadmin / NokiaSrl1!%s\n' "$UI_CYAN" "$UI_RESET" "$UI_DIM" "$UI_RESET"
    ;;
  operations)
    ui_subsection 'Start here'
    printf '  %s\n' 'make enter NODE=probe01.bob1.lagoontransit.test'
    printf '  %s\n' 'make enter NODE=probe01.bob1.pacifictransit.test'
    printf '  %s\n' 'make enter NODE=operations01.bob1.reefnet.test'
    printf '  %-18s %s\n' 'make test' 'expected: Lagoon IPv4 fails. The three control checks pass'
    ;;
  automation)
    ui_subsection 'Start here'
    printf '  %s\n' 'make enter NODE=operations01.bob1.reefnet.test'
    printf '  %-18s %s\n' 'make test' 'confirm the known IPv4 incident'
    echo
    ui_hint 'NetBox API and gNMI commands are on the current course slide.'
    ;;
  monitoring)
    ui_subsection 'Start here'
    printf '  %-18s %s\n' 'Grafana overview' 'ReefNet / BOB1 → BOB1 · Network Overview'
    printf '  %-18s %s\n' 'Per device' 'BOB1 · Device Detail → device, interface, quality and BGP view'
    printf '  %-18s %s\n' 'make fault-routing' 'policy / control-plane failure'
    printf '  %-18s %s\n' 'make fault-link' 'topology change'
    printf '  %-18s %s\n' 'make healthy' 'restore routing/link state and stop generated traffic'
    echo
    ui_subsection 'Traffic load'
    printf '  %-22s %s\n' 'make traffic-10mbit' 'light baseline'
    printf '  %-22s %s\n' 'make traffic-25mbit' 'visible load change, unconstrained'
    printf '  %-22s %s\n' 'make traffic-40mbit' 'still below the transit limit'
    printf '  %-22s %s\n' 'make traffic-50mbit' 'transit capacity boundary'
    printf '  %-22s %s\n' 'make traffic-60mbit' 'cross the transit limit'
    printf '  %-22s %s\n' 'make traffic-75mbit' 'stronger congestion, customer handoff still has headroom'
    ui_info 'Capacity model: each transit handoff 50 Mbit/s. Customer handoff 100 Mbit/s.'
    ui_info 'Traffic levels stay below the SR Linux container simulation packet-rate ceiling.'
    ;;
esac
echo
ui_subsection 'Control'
printf '  %-18s %s\n' 'make status' 'inspect the running lab'
printf '  %-18s %s\n' 'make test' 'check end-to-end IPv4/IPv6 reachability'
printf '  %-18s %s\n' 'make reset' 'rebuild this course-day state'
printf '  %-18s %s\n' 'make down' 'stop the lab, keep prepared NetBox data'
printf '  %-18s %s\n' 'make clean' 'remove lab state + NetBox data, keep base images'
printf '  %-18s %s\n' 'make next' 'show this course-day guide again'
printf '  %-18s %s\n' 'make help' 'show the complete command overview'
ui_hint 'After make clean, run make setup before starting a course day again.'
echo
