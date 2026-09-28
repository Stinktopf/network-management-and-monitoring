#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/ui.sh"
quiet=0
[[ ${1:-} == --quiet ]] && quiet=1
ok=1
issues=()

for cmd in docker containerlab make curl; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    issues+=("$cmd is missing")
    ok=0
  fi
done

if command -v docker >/dev/null 2>&1; then
  docker info >/dev/null 2>&1 || { issues+=("Docker daemon is not reachable"); ok=0; }
  docker compose version >/dev/null 2>&1 || { issues+=("docker compose is missing"); ok=0; }
fi

case "$PWD/" in
  /mnt/[a-zA-Z]/*) issues+=("project is on a Windows mount; move it into the WSL/Linux filesystem") ;;
esac

mem_kb=$(awk '/MemTotal:/ {print $2}' /proc/meminfo)
mem_gb=$(( mem_kb / 1024 / 1024 ))
cpu_count=$(getconf _NPROCESSORS_ONLN 2>/dev/null || echo 0)
disk_gb=$(df -Pk . | awk 'NR==2 {print int($4/1024/1024)}')
(( mem_gb >= 12 )) || issues+=("only ${mem_gb} GiB RAM. 12 GiB or more is recommended")
(( cpu_count == 0 || cpu_count >= 4 )) || issues+=("only ${cpu_count} CPU threads. 4 or more are recommended")
(( disk_gb >= 15 )) || { issues+=("only ${disk_gb} GiB free disk; keep at least 15 GiB free"); ok=0; }

if (( quiet )); then
  if (( ok == 0 )); then printf '%s\n' "${issues[@]}" >&2; exit 1; fi
  exit 0
fi

ui_banner 'Workstation check' 'Docker, Containerlab and local resources'
if command -v docker >/dev/null 2>&1; then ui_ok 'Docker CLI'; else ui_fail 'Docker CLI missing'; fi
if docker info >/dev/null 2>&1; then ui_ok 'Docker daemon'; else ui_fail 'Docker daemon unavailable'; fi
if docker compose version >/dev/null 2>&1; then ui_ok "Docker Compose · $(docker compose version --short 2>/dev/null || echo installed)"; else ui_fail 'Docker Compose missing'; fi
if command -v containerlab >/dev/null 2>&1; then clab_ver=$(containerlab version 2>/dev/null | grep -Eo '[0-9]+\.[0-9]+\.[0-9]+' | head -n1 || true); ui_ok "Containerlab${clab_ver:+ · $clab_ver}"; else ui_fail 'Containerlab missing'; fi
ui_kv 'Memory' "${mem_gb} GiB"
ui_kv 'CPU' "${cpu_count} threads"
ui_kv 'Free disk' "${disk_gb} GiB"
case "$PWD/" in
  /mnt/[a-zA-Z]/*) ui_warn 'Project is on a Windows mount; use ~/... inside WSL' ;;
  *) ui_ok 'Project location · WSL/Linux filesystem' ;;
esac

if ((${#issues[@]})); then
  ui_subsection 'Notes'
  for issue in "${issues[@]}"; do ui_warn "$issue"; done
fi

if (( ok )); then ui_success_banner 'WORKSTATION READY'; else ui_error_banner 'WORKSTATION CHECK FAILED'; fi
exit $((1-ok))
