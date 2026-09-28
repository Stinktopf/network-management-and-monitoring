#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/lib.sh"

scenario=${1:?usage: verify-scenario.sh networking|operations|automation|monitoring}
fail=0

ping_once() {
  local node=$1 af=$2 target=$3
  if [[ "$af" == -4 ]]; then
    ping4 "$node" "$target"
  else
    ping6 "$node" "$target"
  fi
}

expect_ping() {
  local expected=$1 node=$2 af=$3 target=$4
  local i ok
  for i in $(seq 1 12); do
    ok=0
    ping_once "$node" "$af" "$target" && ok=1
    if [[ "$expected" == pass && $ok -eq 1 ]]; then
      return 0
    fi
    if [[ "$expected" == fail && $ok -eq 0 ]]; then
      return 0
    fi
    sleep 1
  done
  printf 'Scenario check failed: %s %s -> %s should %s.\n' \
    "$node" "$af" "$target" "${expected^^}" >&2
  fail=1
}

case "$scenario" in
  networking|monitoring)
    expect_ping pass host01 -4 198.51.100.10
    expect_ping pass host01 -6 2001:db8:100::10
    expect_ping pass host02 -4 198.51.100.10
    expect_ping pass host02 -6 2001:db8:100::10
    ;;
  operations|automation)
    expect_ping fail host01 -4 198.51.100.10
    expect_ping pass host01 -6 2001:db8:100::10
    expect_ping pass host02 -4 198.51.100.10
    expect_ping pass host02 -6 2001:db8:100::10
    ;;
  *)
    echo "Unknown scenario: $scenario" >&2
    exit 2
    ;;
esac

if [[ "$scenario" == monitoring ]]; then
  traffic_ok=0
  for _ in $(seq 1 10); do
    if docker exec clab-ai5049-host01 sh -c 'test -s /tmp/ai5049-traffic.pid && kill -0 "$(cat /tmp/ai5049-traffic.pid)" 2>/dev/null && pgrep -x iperf3 >/dev/null' >/dev/null 2>&1; then
      traffic_ok=1
      break
    fi
    sleep 1
  done
  if (( traffic_ok == 0 )); then
    echo 'Scenario check failed: monitoring traffic generator is not running on probe01.bob1.lagoontransit.test.' >&2
    fail=1
  fi
  if ! docker exec clab-ai5049-svc01 pgrep -x iperf3 >/dev/null 2>&1; then
    echo 'Scenario check failed: iperf3 server is not running on service01.bob1.oceanresearch.test.' >&2
    fail=1
  fi
fi

(( fail == 0 )) || exit 1
printf 'Scenario start-state verified: %s.\n' "$scenario"
