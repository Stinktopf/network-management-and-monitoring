#!/usr/bin/env bash
# Apply one scenario to a running BOB1 lab and verify its expected start state.
set -euo pipefail
source "$(dirname "$0")/ui.sh"
scenario=${1:?usage: prepare-scenario.sh networking|operations|monitoring}
start=$(date +%s)
ui_section "Scenario · $scenario"
case "$scenario" in
  networking) ui_info 'Healthy baseline · no fault injection' ;;
  operations)
    ui_info 'Preparing the incident exercise. Use make task to investigate.'
    bash scripts/fault-routing.sh > .state/scenario-preparation.log 2>&1
    ;;
  monitoring) ui_info 'Starting background traffic probe01.bob1.lagoontransit.test → service01.bob1.oceanresearch.test'; bash scripts/traffic.sh set 25M ;;
  *) ui_fail "Unknown scenario: $scenario"; exit 2 ;;
esac
ui_info 'Verifying expected scenario state and all classroom containers'
bash scripts/verify-scenario.sh "$scenario"
bash scripts/check-containers.sh
printf '%s\n' "$scenario" > .scenario
ui_subsection 'End-to-end reachability'
bash scripts/test.sh
ui_duration 'Scenario verified' "$(( $(date +%s) - start ))"
