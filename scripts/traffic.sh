#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/ui.sh"

SOURCE_CONTAINER='clab-ai5049-host01'
SOURCE_FQDN='probe01.bob1.lagoontransit.test'
TARGET_IP='198.51.100.10'
TARGET_FQDN='service01.bob1.oceanresearch.test'
STATE_DIR='.state'
RATE_FILE="$STATE_DIR/traffic-rate"
REMOTE_PID_FILE='/tmp/ai5049-traffic.pid'
DATAGRAM_BYTES=1200
SIM_PPS_CEILING=10000
RATES=(10M 25M 40M 50M 60M 75M)

mkdir -p "$STATE_DIR"

validate_rate() {
  local rate=${1:-} allowed mbit estimated_pps
  for allowed in "${RATES[@]}"; do
    if [[ $rate == "$allowed" ]]; then
      mbit=${rate%M}
      estimated_pps=$(( mbit * 1000000 / (DATAGRAM_BYTES * 8) ))
      if (( estimated_pps >= SIM_PPS_CEILING )); then
        ui_fail "Traffic rate $rate would exceed the SR Linux container simulation packet-rate ceiling"
        exit 2
      fi
      return 0
    fi
  done
  ui_fail "Unsupported classroom traffic rate '${rate:-}'. Choose: ${RATES[*]}"
  exit 2
}

supervisor_running() {
  docker exec "$SOURCE_CONTAINER" sh -c "test -s '$REMOTE_PID_FILE' && kill -0 \"\$(cat '$REMOTE_PID_FILE')\" 2>/dev/null" >/dev/null 2>&1
}

client_running() {
  docker exec "$SOURCE_CONTAINER" pgrep -x iperf3 >/dev/null 2>&1
}

running() {
  supervisor_running && client_running
}

current_rate() {
  if [[ -s $RATE_FILE ]]; then cat "$RATE_FILE"; else printf '%s\n' 'unknown'; fi
}

stop_remote() {
  docker exec "$SOURCE_CONTAINER" sh -c "if [ -s '$REMOTE_PID_FILE' ]; then kill \"\$(cat '$REMOTE_PID_FILE')\" >/dev/null 2>&1 || true; fi; pkill iperf3 >/dev/null 2>&1 || true; rm -f '$REMOTE_PID_FILE'" 2>/dev/null || true
}

wait_running() {
  local i
  for i in $(seq 1 10); do
    if running; then
      return 0
    fi
    sleep 1
  done
  return 1
}

set_rate() {
  local rate=${1:-}
  validate_rate "$rate"
  stop_remote
  docker exec "$SOURCE_CONTAINER" sh -c "nohup sh -c 'while :; do iperf3 -u -c \"$TARGET_IP\" -b \"$rate\" -l \"$DATAGRAM_BYTES\" -t 3600 --forceflush >/tmp/iperf-client.log 2>&1; sleep 1; done' >/tmp/ai5049-traffic-supervisor.log 2>&1 & echo \$! > '$REMOTE_PID_FILE'"
  printf '%s\n' "$rate" > "$RATE_FILE"
  if ! wait_running; then
    ui_fail "Traffic generator did not start on $SOURCE_FQDN"
    exit 1
  fi
  ui_ok "Traffic running · $SOURCE_FQDN → $TARGET_FQDN · configured UDP load $rate"
}

action=${1:-status}
case "$action" in
  set) set_rate "${2:-}" ;;
  burst)
    rate=${2:-}
    validate_rate "$rate"
    if supervisor_running; then
      ui_fail 'Background traffic is active. Stop it before running a standalone burst.'
      exit 2
    fi
    ui_info "Sending 5 second UDP burst · $rate · $SOURCE_FQDN → $TARGET_FQDN"
    docker exec "$SOURCE_CONTAINER" sh -c "iperf3 -u -c '$TARGET_IP' -b '$rate' -l '$DATAGRAM_BYTES' -t 5 >/tmp/iperf-burst.log 2>&1"
    ui_ok 'Traffic burst complete'
    ;;
  status)
    if running; then
      ui_ok "Traffic running · $SOURCE_FQDN → $TARGET_FQDN · configured UDP load $(current_rate)"
    elif supervisor_running; then
      ui_info "Traffic reconnecting · $SOURCE_FQDN → $TARGET_FQDN · configured UDP load $(current_rate)"
    else
      ui_info "Traffic stopped · $SOURCE_FQDN → $TARGET_FQDN"
    fi
    ;;
  stop)
    stop_remote
    rm -f "$RATE_FILE"
    ui_ok 'Traffic generator stopped'
    ;;
  *) ui_fail "Unknown traffic action: $action"; exit 2 ;;
esac
