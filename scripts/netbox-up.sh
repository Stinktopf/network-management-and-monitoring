#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/ui.sh"
mode=${1:-wait}
quiet=0 progress=0
[[ ${2:-} == --quiet || ${1:-} == --quiet ]] && quiet=1
[[ ${2:-} == --progress || ${1:-} == --progress ]] && { progress=1; quiet=0; }
[[ ${1:-} == --quiet || ${1:-} == --progress ]] && mode=wait
root=$(cd "$(dirname "$0")/.." && pwd)
compose=(docker compose -p ai5049 -f "$root/compose.netbox.yml")
mkdir -p "$root/.state"
fail_with_logs() {
  ui_fail 'NetBox stack failed · recent logs follow'
  "${compose[@]}" logs --no-color --tail 100 postgres redis netbox >&2 || true
  exit 1
}
run_bootstrap() {
  ui_info 'Web UI reachable · provisioning BOB1 inventory'
  if docker inspect -f '{{.State.Running}}' clab-ai5049-ops01 2>/dev/null | grep -qx true; then
    ui_cmd docker exec clab-ai5049-ops01 python3 /opt/ai5049/netbox_bootstrap.py
    docker exec clab-ai5049-ops01 python3 /opt/ai5049/netbox_bootstrap.py
    return
  fi
  ui_cmd docker run --rm --network ai5049-mgmt -e NETBOX_URL=http://netbox.bob1.reefnet.test:8080 -v "$root/.state:/state" ai5049-tools:bob1-v20 python3 /opt/ai5049/netbox_bootstrap.py
  docker run --rm --network ai5049-mgmt -e NETBOX_URL=http://netbox.bob1.reefnet.test:8080 -v "$root/.state:/state" ai5049-tools:bob1-v20 python3 /opt/ai5049/netbox_bootstrap.py
}
case "$mode" in
  start)
    first=0; docker volume inspect ai5049-netbox-postgres-data >/dev/null 2>&1 || first=1
    ui_cmd "${compose[@]}" up -d
    if ! "${compose[@]}" up -d 2>&1 | tee "$root/.state/netbox-compose.log"; then fail_with_logs; fi
    if (( first )); then touch "$root/.state/netbox-first-init"; ui_info 'First database · migrations and search index will run once'; else rm -f "$root/.state/netbox-first-init"; ui_ok 'Existing NetBox database reused'; fi
    exit 0 ;;
  wait) ;;
  *) ui_fail 'usage: netbox-up.sh start|wait [--quiet|--progress]'; exit 2 ;;
esac
start_ts=$(date +%s)
first_init=0
if [[ -f "$root/.state/netbox-first-init" ]]; then
  first_init=1
  max_seconds=900
else
  max_seconds=180
fi
last_notice=-15; last_line=''
for _ in $(seq 1 $((max_seconds/2))); do
  if curl -fsS --max-time 2 http://localhost:8000/login/ >/dev/null 2>&1; then
    run_bootstrap || { ui_fail 'NetBox reachable, but inventory bootstrap failed'; fail_with_logs; }
    touch "$root/.state/netbox-ready"; rm -f "$root/.state/netbox-first-init"
    (( quiet )) || ui_ok "NetBox ready · $(( $(date +%s) - start_ts ))s"
    exit 0
  fi
  for service in postgres redis netbox; do
    cid=$("${compose[@]}" ps -q "$service" 2>/dev/null || true); [[ -z "$cid" ]] && continue
    state=$(docker inspect -f '{{.State.Status}}' "$cid" 2>/dev/null || echo unknown)
    health=$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$cid" 2>/dev/null || echo unknown)
    [[ "$state" == exited || "$state" == dead ]] && { ui_fail "NetBox $service exited during startup"; fail_with_logs; }
    if [[ "$health" == unhealthy ]]; then
      # First initialization can outlive Docker's health grace period. Use HTTP readiness here.
      if [[ "$service" == netbox && $first_init -eq 1 ]]; then
        :
      else
        ui_fail "NetBox $service is unhealthy"
        fail_with_logs
      fi
    fi
  done
  elapsed=$(( $(date +%s) - start_ts ))
  if (( progress && elapsed >= last_notice + 15 )); then
    logs=$("${compose[@]}" logs --no-color --tail 160 netbox 2>/dev/null || true)
    latest=$(printf '%s\n' "$logs" | grep -E 'Applying database migrations|Running migrations:|Applying [^ ]+\.[^ ]+\.\.\. OK|Running trace_paths|Removing stale content types|Removing expired user sessions|Building search index|Starting unit:|Listening at:' | tail -n1 | sed -E 's/^[^|]*\| ?//' || true)
    latest=${latest#⚙️ }
    case "$latest" in
      'Applying database migrations') latest='database migrations' ;;
      'Running migrations:') latest='database migrations' ;;
      'Running trace_paths') latest='updating cable paths' ;;
      'Removing stale content types') latest='database cleanup' ;;
      'Removing expired user sessions') latest='session cleanup' ;;
      'Building search index (lazy)'|'Building search index') latest='building search index' ;;
      *'Listening at:'*) latest='web application listening' ;;
    esac
    [[ -n "$latest" ]] || latest='starting NetBox application'
    if [[ "$latest" != "$last_line" || $elapsed -ge $((last_notice + 30)) ]]; then ui_pending_line "NetBox ${elapsed}s · $latest"; last_line=$latest; fi
    last_notice=$elapsed
  elif (( ! quiet && elapsed >= last_notice + 15 )); then ui_pending_line "NetBox ${elapsed}s · waiting for web UI"; last_notice=$elapsed; fi
  sleep 2
done
ui_fail "NetBox did not become ready within ${max_seconds} seconds"
fail_with_logs
