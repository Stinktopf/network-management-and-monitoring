#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/ui.sh"
ui_banner 'AI5049 Full Cleanup · BOB1' 'Removes lab-local runtime and persistent state. Downloaded base images are kept.'
ui_section 'Stop traffic'; bash scripts/traffic.sh stop >/dev/null 2>&1 || true; ui_ok 'Traffic stopped'
ui_section 'Remove NetBox containers and data'; ui_cmd docker compose -p ai5049 -f compose.netbox.yml down -v --remove-orphans; docker compose -p ai5049 -f compose.netbox.yml down -v --remove-orphans >/dev/null 2>&1 || true; ui_ok 'NetBox containers and volumes removed'
ui_section 'Remove Containerlab topology'; ui_cmd containerlab destroy -t lab.clab.yml --cleanup; containerlab destroy -t lab.clab.yml --cleanup 2>&1 || true
leftovers="$(docker ps -aq --filter 'name=clab-ai5049-' 2>/dev/null || true)"; [[ -z "$leftovers" ]] || docker rm -f $leftovers >/dev/null 2>&1 || true
docker rm -f ai5049-netbox ai5049-netbox-postgres ai5049-netbox-redis >/dev/null 2>&1 || true
docker network rm ai5049-mgmt >/dev/null 2>&1 || true
docker volume rm ai5049-netbox-postgres-data ai5049-netbox-redis-data ai5049-netbox-media-data >/dev/null 2>&1 || true
rm -rf .state clab-ai5049; rm -f .scenario
ui_success_banner 'CLEAN COMPLETE'
ui_info 'Downloaded Docker images were kept.'
ui_hint 'Fresh pre-class verification: make setup'
echo
