#!/usr/bin/env bash
set -u
phase=${1:-unknown}
mode=${2:-full}
export AI5049_COLOR=never
export NO_COLOR=1
if [[ "$mode" == brief ]]; then source "$(dirname "$0")/ui.sh"; fi

state_line() {
  local name=$1 label=$2 state health
  if ! docker inspect "$name" >/dev/null 2>&1; then
    printf '  %-14s MISSING\n' "$label"
    return
  fi
  state=$(docker inspect -f '{{.State.Status}}' "$name" 2>/dev/null || echo unknown)
  health=$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$name" 2>/dev/null || echo unknown)
  if [[ "$health" != none ]]; then
    printf '  %-14s %s / %s\n' "$label" "$state" "$health"
  else
    printf '  %-14s %s\n' "$label" "$state"
  fi
}

if [[ "$mode" == brief ]]; then
  ui_error_banner 'STARTUP CHECK FAILED'
  ui_kv 'Phase' "$phase"
  if ! command -v docker >/dev/null 2>&1 || ! docker info >/dev/null 2>&1; then
    ui_fail 'Docker daemon is not reachable'
    exit 0
  fi
  case "$phase" in
    *NetBox*|*netbox*)
      state_line ai5049-netbox-postgres PostgreSQL
      state_line ai5049-netbox-redis Valkey
      state_line ai5049-netbox NetBox
      echo
      echo 'Last NetBox messages:'
      docker logs --tail 20 ai5049-netbox 2>&1 | sed 's/^/  /' || true
      ;;
    *telemetry*|*Telemetry*|*observability*|*Observability*)
      state_line clab-ai5049-gnmic gNMIc
      state_line clab-ai5049-prometheus Prometheus
      state_line clab-ai5049-alloy Alloy
      state_line clab-ai5049-loki Loki
      state_line clab-ai5049-grafana Grafana
      echo
      for n in gnmic prometheus alloy loki grafana; do
        name="clab-ai5049-$n"
        state=$(docker inspect -f '{{.State.Status}}' "$name" 2>/dev/null || echo missing)
        if [[ "$state" != running ]]; then
          echo "Last $n messages:"
          docker logs --tail 20 "$name" 2>&1 | sed 's/^/  /' || true
        fi
      done
      ;;
    *routing*|*Routing*)
      ui_fail 'End-to-end IPv4/IPv6 reachability did not converge'
      ui_hint 'Run make status for the current lab state.'
      ;;
    *Deploy*|*deploy*|*topology*|*Topology*)
      echo 'Last Containerlab messages:'
      tail -n 30 .state/deploy.log 2>/dev/null | sed 's/^/  /' || true
      ;;
    *)
      ui_hint 'See .state/last-startup-diagnostics.log for details.'
      ;;
  esac
  exit 0
fi

printf '%s\n' 'AI5049 startup diagnostics' '=========================='
printf 'Phase: %s\n' "$phase"
printf 'Time:  %s\n\n' "$(date -Is 2>/dev/null || date)"

for f in .state/validation.log .state/destroy.log .state/deploy.log .state/netbox-compose.log .state/queue-readiness.log .state/scenario-preparation.log; do
  if [[ -s "$f" ]]; then
    printf '\n--- %s (last 100 lines) ---\n' "$f"
    tail -n 100 "$f" | sed -E $'s/\x1B\[[0-9;]*[mK]//g'
  fi
done

command -v docker >/dev/null 2>&1 || exit 0
docker info >/dev/null 2>&1 || exit 0

echo
echo '--- Docker containers ---'
docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}' || true

echo
echo '--- NetBox compose status ---'
docker compose -p ai5049 -f compose.netbox.yml ps 2>/dev/null || true

echo
echo '--- Containerlab status ---'
NO_COLOR=1 containerlab inspect -t lab.clab.yml 2>/dev/null | sed -E $'s/\x1B\[[0-9;]*[mK]//g' || true

bash "$(dirname "$0")/queue-diagnostics.sh"

expected=(
  clab-ai5049-edge01 clab-ai5049-edge02 clab-ai5049-cust01
  clab-ai5049-transit01 clab-ai5049-transit02
  clab-ai5049-host01 clab-ai5049-host02 clab-ai5049-svc01 clab-ai5049-ops01
  clab-ai5049-gnmic clab-ai5049-prometheus clab-ai5049-alloy clab-ai5049-loki clab-ai5049-grafana
  ai5049-netbox-postgres ai5049-netbox-redis ai5049-netbox
)
for name in "${expected[@]}"; do
  docker inspect "$name" >/dev/null 2>&1 || continue
  state=$(docker inspect -f '{{.State.Status}}' "$name" 2>/dev/null || echo unknown)
  health=$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$name" 2>/dev/null || echo unknown)
  if [[ "$state" != running || "$health" == unhealthy ]]; then
    printf '\n--- %s logs (last 60 lines, state=%s health=%s) ---\n' "$name" "$state" "$health"
    docker logs --tail 60 "$name" 2>&1 || true
  fi
done
