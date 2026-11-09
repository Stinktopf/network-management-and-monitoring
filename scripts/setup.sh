#!/usr/bin/env bash
set -eEuo pipefail
source "$(dirname "$0")/check-platform.sh"
if [[ -t 1 && -z ${NO_COLOR:-} ]]; then export AI5049_COLOR=always; fi
source "$(dirname "$0")/ui.sh"
mkdir -p .state
phase='workstation check'
runtime_started=0

exec 9>/tmp/ai5049-setup.lock
if ! flock -n 9; then
  ui_fail 'Another make setup is already running on this PC.'
  ui_hint 'Wait for it to finish, then rerun make setup.'
  exit 1
fi
rm -f .state/setup-complete .state/course-check-scenarios

on_error() {
  rc=$?
  if (($#)); then rc=$1; fi
  trap - ERR INT TERM
  ui_error_banner "SETUP FAILED · $phase"
  if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
    bash scripts/diagnostics.sh "setup: $phase" full > .state/last-startup-diagnostics.log 2>&1 || true
    ui_hint 'Full diagnostics: .state/last-startup-diagnostics.log'
  fi
  if (( runtime_started )); then
    ui_info 'Removing the temporary validation lab after saving diagnostics.'
    bash scripts/down.sh || true
  fi
  exit "$rc"
}
trap on_error ERR
trap 'on_error 130' INT
trap 'on_error 143' TERM

ui_banner 'AI5049 Classroom Lab · BOB1' 'One-time pre-class setup · live output stays visible and is logged under .state/'

phase='workstation check'
ui_section 'Workstation'
ui_cmd bash scripts/doctor.sh
bash scripts/doctor.sh 2>&1 | tee .state/setup-doctor.log

phase='classroom images'
ui_section 'Classroom images'
ui_info 'First run can download several GB. Native Docker progress is shown live.'
ui_cmd bash scripts/ensure-images.sh --all
bash scripts/ensure-images.sh --all 2>&1 | tee .state/setup-images.log

phase='configuration validation'
ui_section 'Configuration validation'
ui_cmd bash scripts/validate-configs.sh
bash scripts/validate-configs.sh 2>&1 | tee .state/setup-validation.log

SCHEMA='v20-bob1-reefnet-source-of-truth-model-v1'
CURRENT_SCHEMA=$(cat .state/netbox-schema-version 2>/dev/null || true)
phase='NetBox classroom database'
ui_section 'NetBox classroom database'
if [[ "$CURRENT_SCHEMA" != "$SCHEMA" ]]; then
  ui_info "Fresh classroom inventory required · stored=${CURRENT_SCHEMA:-none} · target=$SCHEMA"
  ui_cmd docker compose -p ai5049 -f compose.netbox.yml down -v
  docker compose -p ai5049 -f compose.netbox.yml down -v 2>&1 | tee .state/setup-netbox-reset.log || true
  rm -f .state/netbox-token .state/netbox-ready .state/netbox-first-init
  ui_ok 'Old AI5049 NetBox data removed'
else
  ui_ok "Prepared NetBox database found · $SCHEMA"
fi

phase='validation lab'
ui_section 'Validation lab'
ui_info 'Starting the complete networking scenario exactly as it will run in class.'
ui_cmd bash scripts/start-scenario.sh networking
runtime_started=1
AI5049_NO_GUIDE=1 AI5049_SETUP_RUN=1 AI5049_PREFLIGHT_FAST=1 bash scripts/start-scenario.sh networking

phase='course feature checks'
ui_section 'Course feature checks'
ui_info 'DNS · complete NetBox model · gNMI · faults · telemetry · logs · Grafana'
ui_cmd bash scripts/setup-smoke.sh
bash scripts/setup-smoke.sh 2>&1 | tee .state/setup-smoke.log

phase='remaining course workflows'
ui_section 'Remaining course workflows'
ui_info 'Networking passed above. Operations and Monitoring now run through their documented classroom workflows.'
ui_cmd bash scripts/course-check.sh
AI5049_COURSE_CHECK_SCENARIOS='operations monitoring' \
AI5049_COURSE_CHECK_KEEP_UP=1 \
AI5049_COURSE_CHECK_REUSE_LAB=1 \
AI5049_SETUP_RUN=1 \
AI5049_PREFLIGHT_FAST=1 \
  bash scripts/course-check.sh 2>&1 | tee .state/setup-scenarios.log
passed_scenarios=$(paste -sd ' ' .state/course-check-scenarios)
[[ "$passed_scenarios" == 'operations monitoring' ]]
printf '%s\n' "$SCHEMA" > .state/netbox-schema-version
ui_ok 'Networking, Operations and Monitoring passed'

phase='stop validation lab'
ui_section 'Stop validation lab'
ui_info 'Runtime containers stop. The initialized NetBox database stays prepared for class.'
ui_cmd bash scripts/down.sh
bash scripts/down.sh

touch .state/setup-complete
trap - ERR
ui_success_banner 'READY FOR CLASS'
ui_info 'This workstation passed the complete BOB1 pre-class check, including every course state and core workflow.'
ui_hint 'Start the first session with: make networking'
echo
