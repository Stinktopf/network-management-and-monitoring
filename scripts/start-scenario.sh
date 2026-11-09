#!/usr/bin/env bash
set -eEuo pipefail
source "$(dirname "$0")/check-platform.sh"
if [[ -t 1 && -z ${NO_COLOR:-} ]]; then export AI5049_COLOR=always; fi
source "$(dirname "$0")/ui.sh"

if [[ ${AI5049_SETUP_RUN:-0} != 1 ]]; then
  exec 9>/tmp/ai5049-setup.lock
  if ! flock -n 9; then
    ui_fail 'make setup is still running its validation lab on this PC.'
    ui_hint 'Wait for setup to finish, then start your scenario again.'
    exit 1
  fi
fi

scenario=${1:?usage: start-scenario.sh networking|operations|monitoring}
case "$scenario" in networking|operations|monitoring) ;; *) ui_fail "Unknown scenario: $scenario"; exit 2 ;; esac

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
bash scripts/claim-runtime.sh
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
bash scripts/prepare-scenario.sh "$scenario"

[[ "${AI5049_NO_GUIDE:-0}" == 1 ]] || bash scripts/next-steps.sh "$scenario"
