#!/usr/bin/env python3
import argparse
import ast
import json
import re
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description="Check the standalone BOB1 lab model.")
parser.add_argument("--slides", type=Path, help="Optionally check a course Markdown file too")
args = parser.parse_args()
MODEL = json.loads((ROOT / "tools" / "bob1_model.json").read_text())


def fail(message: str) -> None:
    raise SystemExit(f"model consistency: {message}")


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def srl_to_clab(interface: str) -> str:
    match = re.fullmatch(r"ethernet-1/(\d+)", interface)
    return f"e1-{match.group(1)}" if match else interface


asns = {key: value["asn"] for key, value in MODEL["autonomous_systems"].items()}
expected_local_as = {
    "edge01.cfg": asns["reefnet"],
    "edge02.cfg": asns["reefnet"],
    "cust01.cfg": asns["oceanresearch"],
    "transit01.cfg": asns["lagoontransit"],
    "transit02.cfg": asns["pacifictransit"],
}
expected_peer_as = {
    "edge01.cfg": {asns["reefnet"], asns["oceanresearch"], asns["lagoontransit"]},
    "edge02.cfg": {asns["reefnet"], asns["pacifictransit"]},
    "cust01.cfg": {asns["reefnet"]},
    "transit01.cfg": {asns["reefnet"]},
    "transit02.cfg": {asns["reefnet"]},
}

for filename, expected_asn in expected_local_as.items():
    text = (ROOT / "configs" / "srl" / filename).read_text()
    local = {int(x) for x in re.findall(r"protocols bgp autonomous-system (\d+)", text)}
    peers = {int(x) for x in re.findall(r"protocols bgp group \S+ peer-as (\d+)", text)}
    require(local == {expected_asn}, f"{filename} local ASN {sorted(local)} != {expected_asn}")
    require(peers == expected_peer_as[filename], f"{filename} peer ASNs {sorted(peers)} != {sorted(expected_peer_as[filename])}")

# Containerlab node identity and physical links must match the canonical model.
topology = (ROOT / "lab.clab.yml").read_text()
for node, data in MODEL["nodes"].items():
    block_match = re.search(rf"^    {re.escape(node)}:\n(?P<body>(?:^      .*\n)*)", topology, re.M)
    require(block_match is not None, f"lab.clab.yml is missing node {node}")
    body = block_match.group("body")
    require(f"hostname: {data['fqdn']}" in body, f"{node} hostname differs from model")
    require(f"mgmt-ipv4: {data['mgmt_ipv4']}" in body, f"{node} management address differs from model")

for link_id, link in MODEL["links"].items():
    a_node, a_if = link["a"]
    z_node, z_if = link["z"]
    a = f"{a_node}:{srl_to_clab(a_if)}"
    z = f"{z_node}:{srl_to_clab(z_if)}"
    forward = f'[{json.dumps(a)}, {json.dumps(z)}]'
    reverse = f'[{json.dumps(z)}, {json.dumps(a)}]'
    require(forward in topology or reverse in topology, f"lab.clab.yml link {link_id} does not match {a} <-> {z}")

# Grafana topology labels must use the same routing domains as the routers and NetBox.
dash_path = ROOT / "configs" / "grafana" / "dashboards" / "05-topology-paths.json"
dash = json.loads(dash_path.read_text())
canvas = next((p for p in dash.get("panels", []) if p.get("type") == "canvas"), None)
require(canvas is not None, "topology dashboard has no Canvas panel")
elements = {e.get("name"): e for e in canvas["options"]["root"]["elements"]}
expected_labels = {
    "ReefNet Edge 01": f"ReefNet Edge 01\nAS{asns['reefnet']}",
    "ReefNet Edge 02": f"ReefNet Edge 02\nAS{asns['reefnet']}",
    "Ocean Research": f"Ocean Research\nAS{asns['oceanresearch']}",
    "Lagoon Transit": f"Lagoon Transit\nAS{asns['lagoontransit']}",
    "Pacific Transit": f"Pacific Transit\nAS{asns['pacifictransit']}",
}
for name, expected in expected_labels.items():
    actual = elements.get(name, {}).get("config", {}).get("text", {}).get("fixed")
    require(actual == expected, f"Grafana label {name!r} is {actual!r}, expected {expected!r}")

# NetBox bootstrap must store capacity in structured fields rather than prose.
bootstrap = (ROOT / "tools" / "netbox_bootstrap.py").read_text()
require('bob1_model.json' in bootstrap, "NetBox bootstrap is not tied to the canonical model")
require('payload["speed"] = speed' in bootstrap, "NetBox interface speed field is not populated")
require("service capacity" not in bootstrap, "NetBox descriptions still duplicate service capacity text")

# NetBox management addresses and cable endpoints must mirror Containerlab.
mgmt_match = re.search(r"    mgmt = \{(.*?)\n    \}\n", bootstrap, re.S)
require(mgmt_match is not None, "NetBox management map not found")
mgmt = ast.literal_eval("{" + mgmt_match.group(1) + "\n}")
for node, data in MODEL["nodes"].items():
    require(node in mgmt, f"NetBox management map is missing {node}")
    require(mgmt[node][1].split("/")[0] == data["mgmt_ipv4"], f"NetBox management IP for {node} differs from model")

cable_match = re.search(r"    cable_links = \[(.*?)\n    \]\n", bootstrap, re.S)
require(cable_match is not None, "NetBox cable map not found")
cables = ast.literal_eval("[" + cable_match.group(1) + "\n]")
netbox_pairs = {frozenset((tuple(a), tuple(z))) for a, z, _ in cables}
model_pairs = {frozenset((tuple(link["a"]), tuple(link["z"]))) for link in MODEL["links"].values()}
require(netbox_pairs == model_pairs, "NetBox physical cable map differs from the canonical eight data-plane links")

# Every routed and endpoint address configured in the lab must also exist in NetBox.
addresses_match = re.search(r"    addresses = \[(.*?)\n    \]\n    mgmt = \{", bootstrap, re.S)
require(addresses_match is not None, "NetBox address map not found")
netbox_addresses = ast.literal_eval("[" + addresses_match.group(1) + "\n]")
netbox_address_map = {(dev, iface, addr): True for dev, iface, addr, _ in netbox_addresses}
file_to_node = {
    "edge01.cfg": "edge01",
    "edge02.cfg": "edge02",
    "cust01.cfg": "cust01",
    "transit01.cfg": "transit01",
    "transit02.cfg": "transit02",
}
for filename, node in file_to_node.items():
    text = (ROOT / "configs" / "srl" / filename).read_text()
    for iface, addr in re.findall(r"set / interface (\S+) subinterface 0 ipv[46] address (\S+)", text):
        require((node, iface, addr) in netbox_address_map, f"NetBox is missing {node} {iface} {addr}")

for node in ("host01", "host02", "svc01"):
    block_match = re.search(rf"^    {node}:\n(?P<body>.*?)(?=^    \S+:|^  links:)", topology, re.M | re.S)
    require(block_match is not None, f"Containerlab block missing for {node}")
    for addr, iface in re.findall(r"- ip(?: -6)? address add (\S+) dev (\S+)", block_match.group("body")):
        require((node, iface, addr) in netbox_address_map, f"NetBox is missing {node} {iface} {addr}")

# The service-capacity emulation and Prometheus utilization denominators must agree.
customer = MODEL["links"]["customer"]["capacity_kbps"]
lagoon = MODEL["links"]["lagoon"]["capacity_kbps"]
pacific = MODEL["links"]["pacific"]["capacity_kbps"]
require(lagoon == pacific, "the current scripts assume equal transit capacities")
capacity_script = (ROOT / "scripts" / "apply-capacity-profile.sh").read_text()
require(f"CUSTOMER_KBIT={customer}" in capacity_script, "customer netem capacity differs from model")
require(f"TRANSIT_KBIT={lagoon}" in capacity_script, "transit netem capacity differs from model")
rules = (ROOT / "configs" / "prometheus" / "reefnet.rules.yml").read_text()
require(str(customer * 1000) in rules, "Prometheus customer capacity denominator differs from model")
require(str(lagoon * 1000) in rules, "Prometheus transit capacity denominator differs from model")

# Slides are an explicit integration check, never a standalone dependency.
if args.slides:
    slides = args.slides.read_text()
    # The projected topology carries the mapping, without a duplicate prose caption.
    diagram_path = "assets/diagrams/reefnet-overview.svg"
    require(diagram_path in slides, "slides do not show the ReefNet topology")
    diagram = ElementTree.parse(args.slides.parent / diagram_path)
    labels = ["".join(node.itertext()) for node in diagram.iter()
              if node.tag.endswith("}text")]
    for name, domain in [("ReefNet E1", "reefnet"), ("ReefNet E2", "reefnet"),
                         ("Ocean Research", "oceanresearch"),
                         ("Lagoon Transit", "lagoontransit"),
                         ("Pacific Transit", "pacifictransit")]:
        expected = f"AS{asns[domain]}"
        require(any(a == name and b == expected for a, b in zip(labels, labels[1:])),
                f"slide topology does not label {name} with {expected}")
readme = (ROOT / "README.md").read_text()
for line in [
    f"Customer handoff: **{customer // 1000} Mbit/s**",
    f"Lagoon Transit handoff: **{lagoon // 1000} Mbit/s**",
    f"Pacific Transit handoff: **{pacific // 1000} Mbit/s**",
]:
    require(line in readme, f"README capacity differs from model: {line}")

# These were stale values from an older draft and must never reappear in project surfaces.
stale_asns = [64500, 64510, 64520, 64530]
text_files = [
    dash_path,
    ROOT / "tools" / "netbox_bootstrap.py",
    ROOT / "README.md",
]
if args.slides:
    text_files.append(args.slides)
for path in text_files:
    text = path.read_text()
    for stale in stale_asns:
        require(f"AS{stale}" not in text, f"stale AS{stale} remains in {path.name}")

print("BOB1 model consistent across router configs, Containerlab, NetBox, Grafana and documentation"
      + (" and supplied slides" if args.slides else ""))
