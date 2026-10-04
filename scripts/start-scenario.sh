#!/usr/bin/env bash
set -eEuo pipefail
if [[ -t 1 && -z ${NO_COLOR:-} ]]; then export AI5049_COLOR=always; fi
source "$(dirname "$0")/ui.sh"

scenario=${1:?usage: start-scenario.sh networking|operations|automation|monitoring}
case "$scenario" in networking|operations|automation|monitoring) ;; *) ui_fail "Unknown scenario: $scenario"; exit 2 ;; esac

mkdir -p .state
: > .state/last-startup.log
: > .state/scenario-preparation.log
exec > >(tee -a .state/last-startup.log) 2>&1
phase='initialization'
elapsed() { echo "$(( $(date +%s) - $1 ))"; }

run_logged() {
  local log=$1 label=$2; shift 2
  ui_section "$label"
  ui_cmd "$@"
  "$@" 2>&1 | tee "$log"
}

on_error() {
  rc=$?
  trap - ERR
  ui_error_banner "LAB START FAILED · $phase"
  bash scripts/diagnostics.sh "$phase" full > .state/last-startup-diagnostics.log 2>&1 || true
  bash scripts/diagnostics.sh "$phase" brief >&2 || true
  ui_hint 'Full diagnostics: .state/last-startup-diagnostics.log'
  exit "$rc"
}
trap on_error ERR

ui_banner "BOB1 · ${scenario^^}" 'Live startup log: .state/last-startup.log'
if [[ ! -f .state/setup-complete && "${AI5049_SETUP_RUN:-0}" != 1 ]]; then
  ui_warn 'This workstation has not passed the pre-class setup.'
  ui_hint 'Run: make setup'
  exit 2
fi

phase='Preflight and configuration validation'
t=$(date +%s)
run_logged .state/validation.log 'Preflight & configuration' bash scripts/preflight.sh
ui_duration 'Preflight complete' "$(elapsed "$t")"

phase='Reset previous Containerlab topology'
t=$(date +%s)
ui_section 'Reset previous topology'
ui_cmd containerlab destroy -t lab.clab.yml --cleanup --keep-mgmt-net
containerlab destroy -t lab.clab.yml --cleanup --keep-mgmt-net 2>&1 | tee .state/destroy.log || true
ui_duration 'Previous topology cleared' "$(elapsed "$t")"

phase='Deploy BOB1 topology'
t=$(date +%s)
run_logged .state/deploy.log 'Deploy BOB1 topology' containerlab deploy -t lab.clab.yml
ui_duration 'Topology deployed' "$(elapsed "$t")"

phase='Apply link capacities'
bash scripts/apply-capacity-profile.sh

phase='Start NetBox'
ui_section 'Start NetBox'
bash scripts/netbox-up.sh start

phase='Wait for IPv4/IPv6 routing'
t=$(date +%s)
ui_section 'Routing convergence'
ui_info 'Testing probe01.bob1.lagoontransit.test and probe01.bob1.pacifictransit.test → service01.bob1.oceanresearch.test over IPv4 and IPv6'
bash scripts/wait-healthy.sh
ui_duration 'IPv4/IPv6 routing ready' "$(elapsed "$t")"

phase='Wait for telemetry services'
t=$(date +%s)
ui_section 'Observability services'
bash scripts/wait-observability.sh
ui_duration 'Telemetry stack ready' "$(elapsed "$t")"

phase='Wait for NetBox and provision inventory'
t=$(date +%s)
ui_section 'NetBox & inventory'
bash scripts/netbox-up.sh wait --progress
ui_duration 'NetBox inventory ready' "$(elapsed "$t")"

phase="Apply and verify scenario: $scenario"
t=$(date +%s)
ui_section "Scenario · $scenario"
case "$scenario" in
  networking) ui_info 'Healthy baseline · no fault injection' ;;
  operations|automation)
    ui_info 'Preparing the incident exercise. Use make next to investigate.'
    bash scripts/fault-routing.sh > .state/scenario-preparation.log 2>&1
    ;;
  monitoring) ui_info 'Starting background traffic probe01.bob1.lagoontransit.test → service01.bob1.oceanresearch.test'; bash scripts/traffic.sh set 25M ;;
esac
ui_info 'Verifying expected scenario state and all classroom containers'
bash scripts/verify-scenario.sh "$scenario"
bash scripts/check-containers.sh
printf '%s\n' "$scenario" > .scenario
ui_subsection 'End-to-end reachability'
bash scripts/test.sh
ui_duration 'Scenario verified' "$(elapsed "$t")"

[[ "${AI5049_NO_GUIDE:-0}" == 1 ]] || bash scripts/next-steps.sh "$scenario"
