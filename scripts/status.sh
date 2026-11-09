#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/ui.sh"
scenario=$(cat .scenario 2>/dev/null || echo 'not recorded')
ui_banner 'AI5049 Lab Status · BOB1' "Scenario: $scenario"
ui_subsection 'Runtime containers'
docker ps --format 'table {{.Names}}\t{{.Status}}' --filter name=clab-ai5049- --filter name=ai5049-netbox || true
ui_subsection 'Lab nodes'
printf '  %-42s %s\n' 'operations01.bob1.reefnet.test' 'operator workstation'
printf '  %-42s %s\n' 'edge01.bob1.reefnet.test' 'ReefNet edge / Lagoon side'
printf '  %-42s %s\n' 'edge02.bob1.reefnet.test' 'ReefNet edge / Pacific side'
printf '  %-42s %s\n' 'edge01.bob1.oceanresearch.test' 'customer router'
printf '  %-42s %s\n' 'edge01.bob1.lagoontransit.test' 'Lagoon Transit router'
printf '  %-42s %s\n' 'edge01.bob1.pacifictransit.test' 'Pacific Transit router'
printf '  %-42s %s\n' 'probe01.bob1.lagoontransit.test' 'external probe via Lagoon'
printf '  %-42s %s\n' 'probe01.bob1.pacifictransit.test' 'external probe via Pacific'
printf '  %-42s %s\n' 'service01.bob1.oceanresearch.test' 'customer service'
ui_subsection 'Reachability'
bash scripts/test.sh
ui_subsection 'Capacity and generated load'
printf '  %-34s %s\n' 'Customer handoff' '100 Mbit/s'
printf '  %-34s %s\n' 'Lagoon Transit handoff' '50 Mbit/s'
printf '  %-34s %s\n' 'Pacific Transit handoff' '50 Mbit/s'
bash scripts/traffic.sh status || true
ui_subsection 'Web interfaces'
ui_url 'NetBox' 'http://localhost:8000'
ui_url 'Grafana' 'http://localhost:3000'
ui_url 'Prometheus' 'http://localhost:9090'
ui_url 'Alloy' 'http://localhost:12345'
ui_url 'Loki' 'http://localhost:3100'
echo
