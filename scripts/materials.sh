#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/ui.sh

case "${1:-exercises}" in
  exercises)
    ui_banner 'ReefNet / Exercises' 'Run make commands in the WSL repository.'
    ui_section 'Choose a scenario'
    ui_command_row 'make networking' 'Follow a service request'
    ui_command_row 'make operations' 'Investigate a service incident'
    ui_command_row 'make automation' 'Repair through an API'
    ui_command_row 'make monitoring' 'Compare load, loss and faults'
    ui_section 'Work through it'
    ui_command_row 'make task' 'Task and starting point'
    ui_command_row 'make cheatsheet' 'Commands and terminal context'
    ui_command_row 'make hint STEP=2' 'Investigation help for step 2'
    ui_command_row 'make solution STEP=2' 'Worked investigation for step 2'
    ui_command_row 'make down' 'Stop after saving your work'
    echo
    ui_kv 'Exercises' 'EXERCISES.md'
    ui_kv 'Printable commands' 'slides/exports/cheatsheet.pdf'
    echo
    ui_info 'Scenario commands recreate the starting state. Help does not advance automatically.'
    ;;
  cheatsheet)
    ui_banner 'ReefNet / CheatSheet' 'Commands grouped by terminal and task.'
    ui_document markdown slides/resources/CHEATSHEET.md
    ;;
  *)
    printf 'usage: bash scripts/materials.sh exercises|cheatsheet\n' >&2
    exit 2
    ;;
esac
