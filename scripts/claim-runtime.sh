#!/usr/bin/env bash
# A PC can hold AI5049 containers from an earlier lab, e.g. another checkout or user.
# Remove them and management networks that would collide with ai5049-mgmt.
set -euo pipefail
source "$(dirname "$0")/ui.sh"
root=$(cd "$(dirname "$0")/.." && pwd)
mgmt_net=ai5049-mgmt
mgmt_subnet=172.20.20.0/24

foreign=()
declare -A origins=()
while read -r name; do
  [[ -n "$name" ]] || continue
  origin=$(docker inspect -f '{{index .Config.Labels "clab-topo-file"}}{{index .Config.Labels "com.docker.compose.project.working_dir"}}' "$name" 2>/dev/null || true)
  origin=${origin%/lab.clab.yml}
  [[ "$origin" == "$root" ]] && continue
  foreign+=("$name")
  origins[${origin:-unknown}]=$(( ${origins[${origin:-unknown}]:-0} + 1 ))
done < <(docker ps -a --format '{{.Names}}' | grep -E '^(clab-ai5049-|ai5049-netbox)' || true)

if ((${#foreign[@]})); then
  for origin in "${!origins[@]}"; do
    ui_warn "${origins[$origin]} containers belong to another lab checkout · $origin"
  done
  ui_info 'Only one AI5049 lab can run per PC · removing the other lab containers (NetBox data is kept)'
  docker rm -f "${foreign[@]}" >/dev/null
  ui_ok "Removed ${#foreign[@]} containers from the other checkout"
fi

conflict=0
while read -r net; do
  [[ -n "$net" && "$net" != "$mgmt_net" ]] || continue
  subnets=$(docker network inspect -f '{{range .IPAM.Config}}{{.Subnet}} {{end}}' "$net" 2>/dev/null || true)
  [[ " $subnets " == *" $mgmt_subnet "* ]] || continue
  users=$(docker network inspect -f '{{range .Containers}}{{.Name}} {{end}}' "$net" 2>/dev/null || true)
  if [[ -z "${users// /}" ]]; then
    docker network rm "$net" >/dev/null
    ui_ok "Removed unused Docker network $net that also used $mgmt_subnet"
  else
    ui_fail "Docker network $net also uses $mgmt_subnet and is in use by: $users"
    conflict=1
  fi
done < <(docker network ls --format '{{.Name}}')
if (( conflict )); then
  ui_hint 'Stop that other Containerlab lab first (containerlab destroy -t <its topology>), then start again.'
  exit 1
fi

if docker network inspect "$mgmt_net" >/dev/null 2>&1; then
  subnets=$(docker network inspect -f '{{range .IPAM.Config}}{{.Subnet}} {{end}}' "$mgmt_net")
  if [[ " $subnets " != *" $mgmt_subnet "* ]]; then
    users=$(docker network inspect -f '{{range .Containers}}{{.Name}} {{end}}' "$mgmt_net")
    if [[ -n "${users// /}" ]]; then
      ui_fail "$mgmt_net uses ${subnets% } instead of $mgmt_subnet and is in use by: $users"
      exit 1
    fi
    docker network rm "$mgmt_net" >/dev/null
    ui_ok "Removed $mgmt_net with unexpected subnet ${subnets% }"
  fi
fi
ui_ok 'Docker runtime is free for this lab checkout'
