#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/ui.sh"
scenario=${1:-networking}
step=${2:-1}
level=${3:-task}
legacy_step=''
case "$scenario" in
  networking|operations|automation|monitoring) ;;
  *) ui_fail "Unknown scenario: $scenario"; exit 2 ;;
esac
case "$level" in
  task|hint|solution) ;;
  *) ui_fail "Unknown guide level: $level"; exit 2 ;;
esac
guide="$(dirname "$0")/guides/$scenario.txt"
count=$(grep -c '^@@ [0-9]' "$guide")
if [[ "$step" != all ]]; then
  if [[ ! "$step" =~ ^[1-9][0-9]?$ ]] || (( step > count )); then
    ui_fail "Choose STEP=1 through STEP=$count, or STEP=all"
    exit 2
  fi
fi
ui_banner "BOB1 / ${scenario^^} / ${level^^}" "" compact
if [[ "$level" == solution && "$step" == all ]]; then
  printf '%sInvestigation steps%s\n' "$UI_BOLD" "$UI_RESET"
  sed -n 's/^@@ \([0-9].*\)/  \1/p' "$guide"
  echo
fi
awk -v wanted="$step" -v level="$level" '
  /^@@ [0-9]+ / {
    current=$2; section="task"; selected=(wanted == "all" || current == wanted)
    if (selected) {
      print substr($0, 4)
    }
    next
  }
  /^@@ / {
    section=$2
    if (selected && level == "solution" && section == "investigation")
      print "Investigation commands"
    if (selected && level == "solution" && section == "solution") {
      print "\nWorked answer"
    }
    next
  }
  selected && (section == level || (level == "solution" && section == "investigation")) { print }
' "$guide" | awk -f "$(dirname "$0")/reflow-guide.awk" | ui_document guide
if [[ "$level" == task ]]; then
  ui_action 'Commands and clues:' "make hint SCENARIO=$scenario STEP=$step"
fi
if [[ "$step" != all ]] && (( step < count )); then
  if [[ "$level" == solution ]]; then
    ui_action 'Next worked step:' "make solution SCENARIO=$scenario STEP=$((step + 1))"
  else
    ui_action 'When ready:' "make task SCENARIO=$scenario STEP=$((step + 1))"
  fi
fi
if [[ "$level" == hint ]]; then
  ui_action 'Commands and expected results:' "make solution SCENARIO=$scenario STEP=$step"
fi
