#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/ui.sh"
container=clab-ai5049-ops01
api='http://netbox.bob1.reefnet.test:8080/api'

nb_eval() {
  local path=$1 expr=$2
  docker exec "$container" sh -c \
    'TOKEN=$(cat /state/netbox-token); curl -fsS -H "Authorization: Bearer $TOKEN" "$1" | jq -er "$2"' \
    sh "$api/$path" "$expr"
}

assert_count() {
  local label=$1 path=$2 expected=$3
  local n
  n=$(nb_eval "$path" '.count')
  if [[ ! $n =~ ^[0-9]+$ ]]; then
    ui_fail "$label · API returned a non-numeric count: ${n@Q}"
    return 1
  fi
  (( n >= expected )) || { ui_fail "$label · expected >= $expected, found $n"; return 1; }
  printf '  %-24s %s\n' "$label" "$n"
}

ui_subsection 'NetBox source of truth'
assert_count 'Sites' 'dcim/sites/' 1
assert_count 'Locations' 'dcim/locations/' 1
assert_count 'Racks' 'dcim/racks/' 1
assert_count 'Devices' 'dcim/devices/?site=bob1' 14
assert_count 'Interfaces' 'dcim/interfaces/' 35
assert_count 'Physical cables' 'dcim/cables/' 8
assert_count 'Prefixes' 'ipam/prefixes/' 21
assert_count 'IP addresses' 'ipam/ip-addresses/' 51
assert_count 'ASNs' 'ipam/asns/' 4
assert_count 'Tenants' 'tenancy/tenants/' 4
assert_count 'Providers' 'circuits/providers/' 2
assert_count 'Provider networks' 'circuits/provider-networks/' 2
assert_count 'Circuits' 'circuits/circuits/' 2
assert_count 'Circuit terminations' 'circuits/circuit-terminations/' 4
assert_count 'Application services' 'ipam/services/' 19

ui_subsection 'Required relationships'
for dev in \
  edge01.bob1.reefnet.test edge02.bob1.reefnet.test edge01.bob1.oceanresearch.test \
  edge01.bob1.lagoontransit.test edge01.bob1.pacifictransit.test \
  probe01.bob1.lagoontransit.test probe01.bob1.pacifictransit.test \
  service01.bob1.oceanresearch.test operations01.bob1.reefnet.test \
  gnmic.bob1.reefnet.test prometheus.bob1.reefnet.test grafana.bob1.reefnet.test \
  alloy.bob1.reefnet.test loki.bob1.reefnet.test; do
  nb_eval "dcim/devices/?name=$dev" '.count == 1' >/dev/null
  printf '  %-42s %s\n' "$dev" 'present'
done
for cid in BOB1-LAGOON-001 BOB1-PACIFIC-001; do
  nb_eval "circuits/circuits/?cid=$cid" '.count == 1' >/dev/null
  printf '  %-24s %s\n' "$cid" 'active circuit record'
done
for spec in \
  'probe01.bob1.lagoontransit.test:eth1' 'probe01.bob1.pacifictransit.test:eth1' 'service01.bob1.oceanresearch.test:eth1' \
  'edge01.bob1.reefnet.test:ethernet-1/1' 'edge01.bob1.reefnet.test:ethernet-1/2' 'edge01.bob1.reefnet.test:ethernet-1/3' 'edge01.bob1.reefnet.test:ethernet-1/4' \
  'edge02.bob1.reefnet.test:ethernet-1/1' 'edge02.bob1.reefnet.test:ethernet-1/2' 'edge02.bob1.reefnet.test:ethernet-1/3' \
  'edge01.bob1.oceanresearch.test:ethernet-1/1' 'edge01.bob1.oceanresearch.test:ethernet-1/2' \
  'edge01.bob1.lagoontransit.test:ethernet-1/1' 'edge01.bob1.lagoontransit.test:ethernet-1/2' \
  'edge01.bob1.pacifictransit.test:ethernet-1/1' 'edge01.bob1.pacifictransit.test:ethernet-1/2'; do
  dev=${spec%%:*}; iface=${spec#*:}
  nb_eval "dcim/interfaces/?device=$dev&name=$iface" '.count == 1 and .results[0].cable != null' >/dev/null
 done
ui_ok 'All 8 physical lab links are traceable from both endpoints'
for addr in 10.255.0.1/32 10.255.0.2/32 10.255.10.1/32 10.255.100.1/32 10.255.200.1/32; do
  enc=${addr//\//%2F}
  nb_eval "ipam/ip-addresses/?address=$enc" '.count == 1 and .results[0].role.value == "loopback"' >/dev/null
 done
ui_ok 'All SR Linux loopbacks are documented with loopback role'
nb_eval 'dcim/sites/?slug=bob1' '.count == 1 and (.results[0].asns | length) == 4 and .results[0].status.value == "active"' >/dev/null
ui_ok 'BOB1 site is active and linked to all four autonomous systems'

ui_subsection 'Routing domains and interface capacity'
for spec in \
  '65000|ReefNet' '65010|Bora Bora Ocean Research' '65100|Lagoon Transit' '65200|Pacific Transit'; do
  asn=${spec%%|*}; tenant=${spec#*|}
  nb_eval "ipam/asns/?asn=$asn" ".count == 1 and .results[0].tenant.name == \"$tenant\"" >/dev/null
done
ui_ok 'AS65000, AS65010, AS65100 and AS65200 are linked to the correct organizations'

nb_eval 'circuits/providers/?slug=lagoon-transit' '.count == 1 and ([.results[0].asns[].asn] | index(65100) != null)' >/dev/null
nb_eval 'circuits/providers/?slug=pacific-transit' '.count == 1 and ([.results[0].asns[].asn] | index(65200) != null)' >/dev/null
ui_ok 'Transit providers reference the same ASNs as the live BGP configuration'

for spec in \
  'edge01.bob1.reefnet.test|ethernet-1/1|100000' \
  'edge01.bob1.oceanresearch.test|ethernet-1/1|100000' \
  'edge01.bob1.reefnet.test|ethernet-1/3|50000' \
  'edge01.bob1.lagoontransit.test|ethernet-1/1|50000' \
  'edge02.bob1.reefnet.test|ethernet-1/2|50000' \
  'edge01.bob1.pacifictransit.test|ethernet-1/1|50000'; do
  dev=${spec%%|*}; rest=${spec#*|}; iface=${rest%%|*}; speed=${rest##*|}
  nb_eval "dcim/interfaces/?device=$dev&name=$iface" ".count == 1 and .results[0].speed == $speed and (.results[0].description | contains(\"Mbit/s\") | not)" >/dev/null
done
ui_ok 'Managed handoff speeds are stored in the NetBox interface speed field'

for pair in \
  'edge01.bob1.reefnet.test=172.20.20.11/24' 'edge02.bob1.reefnet.test=172.20.20.12/24' 'edge01.bob1.oceanresearch.test=172.20.20.21/24' \
  'edge01.bob1.lagoontransit.test=172.20.20.22/24' 'edge01.bob1.pacifictransit.test=172.20.20.23/24' 'probe01.bob1.lagoontransit.test=172.20.20.31/24' \
  'probe01.bob1.pacifictransit.test=172.20.20.32/24' 'service01.bob1.oceanresearch.test=172.20.20.33/24' 'operations01.bob1.reefnet.test=172.20.20.40/24' \
  'gnmic.bob1.reefnet.test=172.20.20.41/24' 'prometheus.bob1.reefnet.test=172.20.20.42/24' 'grafana.bob1.reefnet.test=172.20.20.43/24' \
  'alloy.bob1.reefnet.test=172.20.20.45/24' 'loki.bob1.reefnet.test=172.20.20.46/24'; do
  dev=${pair%%=*}; addr=${pair#*=}
  nb_eval "dcim/devices/?name=$dev" ".count == 1 and .results[0].primary_ip4.address == \"$addr\"" >/dev/null
done
ui_ok 'Primary management IPs are documented on all 14 devices'

for cid in BOB1-LAGOON-001 BOB1-PACIFIC-001; do
  nb_eval "circuits/circuits/?cid=$cid" '.count == 1 and .results[0].status.value == "active" and .results[0].commit_rate == 50000' >/dev/null
  nb_eval 'circuits/circuit-terminations/?limit=100' "[.results[] | select(.circuit.cid == \"$cid\" and .port_speed == 50000)] | length == 2" >/dev/null
done
ui_ok 'Both 50 Mbit/s transit circuits are active with A/Z terminations'

for svc in DNS HTTP iperf3; do
  nb_eval "ipam/services/?device=service01.bob1.oceanresearch.test&name=$svc" '.count == 1' >/dev/null || \
    nb_eval 'ipam/services/?limit=100' "[.results[] | select(.name == \"$svc\" and .parent.name == \"service01.bob1.oceanresearch.test\")] | length == 1" >/dev/null
done
ui_ok 'Customer-facing DNS, HTTP and iperf3 services are documented on service01.bob1.oceanresearch.test'
ui_ok 'NetBox model is complete and internally linked'
