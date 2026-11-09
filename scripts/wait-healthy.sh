#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/lib.sh"
quiet=0
[[ ${1:-} == --quiet ]] && quiet=1
probe4() { ping4 "$1" "$2"; }
probe6() { ping6 "$1" "$2"; }
status_word() { if "$@"; then printf READY; else printf WAIT; fi; }

start=$(date +%s)
last_sig=''
last_print=-10
for _ in $(seq 1 150); do
  h1v4=$(status_word probe4 host01 198.51.100.10)
  h1v6=$(status_word probe6 host01 2001:db8:100::10)
  h2v4=$(status_word probe4 host02 198.51.100.10)
  h2v6=$(status_word probe6 host02 2001:db8:100::10)
  sig="$h1v4/$h1v6/$h2v4/$h2v6"
  elapsed=$(( $(date +%s) - start ))

  if [[ "$sig" == 'READY/READY/READY/READY' ]]; then
    if (( ! quiet )); then
      ui_ok "probe01.bob1.lagoontransit.test · IPv4 + IPv6"
      ui_ok "probe01.bob1.pacifictransit.test · IPv4 + IPv6"
    fi
    exit 0
  fi

  if (( ! quiet )) && { [[ "$sig" != "$last_sig" ]] || (( elapsed >= last_print + 10 )); }; then
    ui_pending_line "routing ${elapsed}s · Lagoon v4=$h1v4 v6=$h1v6 · Pacific v4=$h2v4 v6=$h2v6"
    last_sig=$sig
    last_print=$elapsed
  fi
  sleep 1
done
ui_fail 'IPv4/IPv6 routing did not converge within 150 seconds'
exit 1
