#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/ui.sh"
ui_section 'Reset NetBox classroom database'
ui_cmd docker compose -p ai5049 -f compose.netbox.yml down -v
docker compose -p ai5049 -f compose.netbox.yml down -v >/dev/null 2>&1 || true
rm -f .state/netbox-token .state/netbox-ready .state/netbox-first-init .state/netbox-schema-version
ui_warn 'NetBox data removed · next start will rebuild inventory and may take a few minutes'
if docker network inspect ai5049-mgmt >/dev/null 2>&1; then bash scripts/netbox-up.sh start; bash scripts/netbox-up.sh wait --progress; fi
