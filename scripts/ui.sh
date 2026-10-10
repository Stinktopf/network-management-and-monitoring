#!/usr/bin/env bash
if [[ ${AI5049_COLOR:-auto} == always ]]; then
  _ui_color=1
elif [[ ${AI5049_COLOR:-auto} == never || -n ${NO_COLOR:-} ]]; then
  _ui_color=0
elif [[ -t 1 || -t 2 ]]; then
  _ui_color=1
else
  _ui_color=0
fi

case ${LC_ALL:-${LC_CTYPE:-${LANG:-}}} in
  *UTF-8*|*utf8*|*UTF8*) _ui_utf8=1 ;;
  *) _ui_utf8=0 ;;
esac
[[ ${AI5049_ICONS:-auto} == never ]] && _ui_utf8=0

if (( _ui_color )); then
  UI_RESET=$'\033[0m'
  UI_BOLD=$'\033[1m'
  UI_DIM=$'\033[2m'
  UI_RED=$'\033[31m'
  UI_GREEN=$'\033[32m'
  UI_YELLOW=$'\033[33m'
  UI_BLUE=$'\033[34m'
  UI_MAGENTA=$'\033[35m'
  UI_CYAN=$'\033[36m'
  UI_WHITE=$'\033[37m'
  UI_GRAY=$'\033[90m'
else
  UI_RESET='' UI_BOLD='' UI_DIM='' UI_RED='' UI_GREEN='' UI_YELLOW=''
  UI_BLUE='' UI_MAGENTA='' UI_CYAN='' UI_WHITE='' UI_GRAY=''
fi

if (( _ui_utf8 )); then
  UI_OK='✓' UI_FAIL='✗' UI_WARN='!' UI_WAIT='…' UI_INFO='i' UI_ARROW='→'
  UI_CMD='$' UI_DOT='·'
  UI_TL='+' UI_TR='+' UI_BL='+' UI_BR='+' UI_H='-' UI_V='|'
else
  UI_OK='OK' UI_FAIL='X' UI_WARN='!' UI_WAIT='...' UI_INFO='i' UI_ARROW='->'
  UI_CMD='$' UI_DOT='-' UI_TL='+' UI_TR='+' UI_BL='+' UI_BR='+' UI_H='-' UI_V='|'
fi

ui_rule() {
  local width=${1:-68}
  printf '%s' "$UI_GRAY"
  printf '%*s' "$width" '' | tr ' ' '-'
  printf '%s\n' "$UI_RESET"
}

ui_banner() {
  local title=${1:?title required}
  local subtitle=${2:-}
  local spacing=${3:-normal}
  local width=68
  printf '\n%s%s%s\n' "$UI_CYAN$UI_BOLD" "$title" "$UI_RESET"
  ui_rule "$width"
  [[ -n $subtitle ]] && printf '%s%s%s\n' "$UI_DIM" "$subtitle" "$UI_RESET"
  [[ $spacing == compact ]] || printf '\n'
}

ui_section() {
  printf '\n%s%s%s %s%s%s\n' "$UI_BLUE$UI_BOLD" "$UI_ARROW" "$UI_RESET" "$UI_BOLD" "$1" "$UI_RESET"
}

ui_subsection() {
  printf '\n%s%s%s\n' "$UI_BOLD" "$1" "$UI_RESET"
}

ui_ok()   { printf '  %s%s%s  %s\n' "$UI_GREEN$UI_BOLD" "$UI_OK" "$UI_RESET" "$*"; }
ui_fail() { printf '  %s%s%s  %s\n' "$UI_RED$UI_BOLD" "$UI_FAIL" "$UI_RESET" "$*" >&2; }
ui_warn() { printf '  %s%s%s  %s\n' "$UI_YELLOW$UI_BOLD" "$UI_WARN" "$UI_RESET" "$*"; }
ui_info() { printf '  %s%s%s  %s\n' "$UI_CYAN" "$UI_INFO" "$UI_RESET" "$*"; }
ui_wait() { printf '  %s%s%s  %s\n' "$UI_YELLOW" "$UI_WAIT" "$UI_RESET" "$*"; }

ui_cmd() {
  printf '  %s%s%s %s' "$UI_MAGENTA$UI_BOLD" "$UI_CMD" "$UI_RESET" "$UI_DIM"
  printf ' %q' "$@"
  printf '%s\n' "$UI_RESET"
}

ui_kv() {
  local key=$1 value=$2
  printf '  %s%-18s%s %s\n' "$UI_DIM" "$key" "$UI_RESET" "$value"
}

ui_success_banner() {
  printf '\n%s%s %s%s\n' "$UI_GREEN$UI_BOLD" "$UI_OK" "$*" "$UI_RESET"
  ui_rule 68
}

ui_error_banner() {
  printf '\n%s%s %s%s\n' "$UI_RED$UI_BOLD" "$UI_FAIL" "$*" "$UI_RESET" >&2
  ui_rule 68 >&2
}

ui_duration() {
  local label=$1 seconds=$2
  printf '  %s%s%s  %-38s %s%ss%s\n' "$UI_GREEN$UI_BOLD" "$UI_OK" "$UI_RESET" "$label" "$UI_DIM" "$seconds" "$UI_RESET"
}

ui_pending_line() {
  printf '  %s%s%s  %s\n' "$UI_YELLOW" "$UI_WAIT" "$UI_RESET" "$*"
}

ui_hint() {
  printf '  %s%s%s %s\n' "$UI_CYAN$UI_BOLD" "$UI_ARROW" "$UI_RESET" "$*"
}

ui_action() {
  local label=$1 command_text=$2
  if [[ -z ${UI_ACTION_STARTED:-} ]]; then
    printf '\n'
    UI_ACTION_STARTED=1
  fi
  printf '%s%s%s %s %s%s%s\n' \
    "$UI_CYAN$UI_BOLD" "$UI_ARROW" "$UI_RESET" "$label" \
    "$UI_YELLOW$UI_BOLD" "$command_text" "$UI_RESET"
}

ui_url() {
  local label=$1 url=$2 extra=${3:-}
  printf '  %s%-11s%s %s%s%s' "$UI_BOLD" "$label" "$UI_RESET" "$UI_CYAN" "$url" "$UI_RESET"
  [[ -n $extra ]] && printf '  %s%s%s' "$UI_DIM" "$extra" "$UI_RESET"
  printf '\n'
}

# Human-readable command rows. No shell quoting or command execution.
ui_command_row() {
  local command=$1 description=$2
  if (( ${#command} > 32 )); then
    printf '  %s%s%s\n    %s\n' "$UI_MAGENTA" "$command" "$UI_RESET" "$description"
  else
    printf '  %s%-32s%s %s\n' "$UI_MAGENTA" "$command" "$UI_RESET" "$description"
  fi
}

# Shared presentation for Markdown handouts and plain-text investigation guides.
ui_document() {
  local mode=${1:-markdown}
  shift
  awk -v mode="$mode" -v bold="$UI_BOLD" -v reset="$UI_RESET" \
    -v command="$UI_MAGENTA" -v blue="$UI_BLUE" -v cyan="$UI_CYAN" \
    -v gray="$UI_GRAY" -v arrow="$UI_ARROW" \
    -f "$(dirname "${BASH_SOURCE[0]}")/render-material.awk" "$@"
}
