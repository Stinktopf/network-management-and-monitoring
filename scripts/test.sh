#!/usr/bin/env bash
set -u
source "$(dirname "$0")/lib.sh"
printf '  %s%-42s %-7s %-10s%s\n' "$UI_BOLD" SOURCE AF RESULT "$UI_RESET"
printf '  %-42s %-7s %-10s\n' '------------------------------------------' '-------' '----------'
run_test() {
  local node=$1 label=$2 mode=$3 af_label=$4 target=$5 result
  if { [[ "$mode" == "-4" ]] && ping4 "$node" "$target"; } || { [[ "$mode" == "-6" ]] && ping6 "$node" "$target"; }; then
    result="${UI_GREEN}${UI_OK} PASS${UI_RESET}"
  else
    result="${UI_RED}${UI_FAIL} FAIL${UI_RESET}"
  fi
  printf '  %-42s %-7s %b\n' "$label" "$af_label" "$result"
}
run_test host01 probe01.bob1.lagoontransit.test -4 IPv4 198.51.100.10
run_test host01 probe01.bob1.lagoontransit.test -6 IPv6 2001:db8:100::10
run_test host02 probe01.bob1.pacifictransit.test -4 IPv4 198.51.100.10
run_test host02 probe01.bob1.pacifictransit.test -6 IPv6 2001:db8:100::10
