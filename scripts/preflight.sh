#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/ui.sh"
fail=0
for cmd in docker containerlab curl; do
  if ! command -v "$cmd" >/dev/null 2>&1; then ui_fail "Missing command · $cmd"; fail=1; fi
done
if (( fail )); then ui_hint 'Run make doctor for the full environment check.'; exit 1; fi
if ! docker info >/dev/null 2>&1; then ui_fail 'Docker daemon is not reachable'; ui_hint 'Run make doctor for details.'; exit 1; fi
if ! docker compose version >/dev/null 2>&1; then ui_fail 'Docker Compose is not available'; exit 1; fi

check_port() {
  local port=$1 allowed=$2 owner
  owner=$(docker ps --filter "publish=$port" --format '{{.Names}}' 2>/dev/null | head -n1 || true)
  if [[ -n "$owner" && "$owner" != "$allowed" ]]; then ui_fail "Port $port is already used by Docker container '$owner'"; return 1; fi
  if [[ -z "$owner" ]] && command -v ss >/dev/null 2>&1; then
    if ss -ltnH 2>/dev/null | awk '{print $4}' | grep -Eq "(^|:)$port$"; then ui_fail "Port $port is already used by another local process"; return 1; fi
  fi
}
check_port 8000 ai5049-netbox
check_port 3000 clab-ai5049-grafana
check_port 9090 clab-ai5049-prometheus
check_port 3100 clab-ai5049-loki
check_port 12345 clab-ai5049-alloy
ui_ok 'Required TCP ports are available'
mkdir -p .state
if [[ ${AI5049_PREFLIGHT_FAST:-0} == 1 ]]; then
  ui_ok 'Images/configs already checked by setup · runtime preflight only'
else
  bash scripts/ensure-images.sh missing
  bash scripts/validate-configs.sh
fi
