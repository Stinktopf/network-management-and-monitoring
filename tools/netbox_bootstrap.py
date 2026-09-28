#!/usr/bin/env python3
import json, os, sys, time, urllib.error, urllib.parse, urllib.request

BASE = os.environ.get("NETBOX_URL", "http://netbox.bob1.reefnet.test:8080").rstrip("/")
STATE = "/state/netbox-token"
ADMIN = {"username": "admin", "password": "admin"}

MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bob1_model.json")
with open(MODEL_PATH, encoding="utf-8") as model_file:
    MODEL = json.load(model_file)

AS_REEFNET = MODEL["autonomous_systems"]["reefnet"]["asn"]
AS_OCEANRESEARCH = MODEL["autonomous_systems"]["oceanresearch"]["asn"]
AS_LAGOON = MODEL["autonomous_systems"]["lagoontransit"]["asn"]
AS_PACIFIC = MODEL["autonomous_systems"]["pacifictransit"]["asn"]
CUSTOMER_SPEED = MODEL["links"]["customer"]["capacity_kbps"]
LAGOON_SPEED = MODEL["links"]["lagoon"]["capacity_kbps"]
PACIFIC_SPEED = MODEL["links"]["pacific"]["capacity_kbps"]


def req(method, path, data=None, token=None, ok=(200, 201)):
    body = None if data is None else json.dumps(data).encode()
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = urllib.request.Request(BASE + path, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=20) as resp:
            raw = resp.read().decode()
            if resp.status not in ok:
                raise RuntimeError(f"{method} {path}: HTTP {resp.status}: {raw}")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        raise RuntimeError(f"{method} {path}: HTTP {e.code}: {raw}") from e


def wait_netbox():
    for _ in range(450):
        try:
            with urllib.request.urlopen(BASE + "/login/", timeout=3) as resp:
                if resp.status < 500:
                    return
        except Exception:
            pass
        time.sleep(2)
    raise RuntimeError("NetBox did not become ready")


def provision_token():
    result = req("POST", "/api/users/tokens/provision/", ADMIN)
    plaintext = result.get("token") or ""
    key = result.get("key") or ""
    if plaintext.startswith("nbt_"):
        token = plaintext
    elif key and plaintext:
        token = f"nbt_{key}.{plaintext}"
    else:
        raise RuntimeError("NetBox token provisioning did not return key/plaintext")
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    with open(STATE, "w") as f:
        f.write(token + "\n")
    return token


def get_token():
    if os.path.exists(STATE):
        try:
            token = open(STATE).read().strip()
            if token:
                req("GET", "/api/dcim/sites/?limit=1", token=token)
                return token
        except Exception:
            pass
    return provision_token()


def list_first(path, params, token):
    q = urllib.parse.urlencode(params)
    x = req("GET", f"{path}?{q}", token=token)
    return x.get("results", [None])[0] if x.get("count", 0) else None


def ensure(path, lookup, payload, token):
    existing = list_first(path, lookup, token)
    if existing:
        return existing
    return req("POST", path, payload, token=token)


def reconcile(path, lookup, payload, token):
    existing = list_first(path, lookup, token)
    if existing:
        return patch(path, existing, payload, token)
    return req("POST", path, payload, token=token)


def patch(path, obj, payload, token):
    return req("PATCH", f"{path}{obj['id']}/", payload, token=token, ok=(200,))


def get_detail(path, object_id, token):
    return req("GET", f"{path}{object_id}/", token=token)


def count(path, token, params=None):
    q = urllib.parse.urlencode(params or {})
    return int(req("GET", f"{path}?{q}", token=token).get("count", 0))


def ensure_cable(a_iface, b_iface, label, cable_type, token):
    a = get_detail("/api/dcim/interfaces/", a_iface["id"], token)
    b = get_detail("/api/dcim/interfaces/", b_iface["id"], token)
    a_cable = (a.get("cable") or {}).get("id")
    b_cable = (b.get("cable") or {}).get("id")
    if a_cable and b_cable:
        if a_cable != b_cable:
            raise RuntimeError(f"NetBox cable conflict for {label}")
        return get_detail("/api/dcim/cables/", a_cable, token)
    if a_cable or b_cable:
        raise RuntimeError(f"NetBox cable conflict for {label}: one endpoint is already cabled")
    return req("POST", "/api/dcim/cables/", {
        "a_terminations": [{"object_type": "dcim.interface", "object_id": a_iface["id"]}],
        "b_terminations": [{"object_type": "dcim.interface", "object_id": b_iface["id"]}],
        "status": "connected", "type": cable_type, "label": label,
    }, token=token)


def ensure_service(parent, name, port_mappings, description, token, ip_addresses=None):
    # NetBox 4.3+ uses a generic parent relation.
    data = req("GET", "/api/ipam/services/?limit=100", token=token)
    for item in data.get("results", []):
        pobj = item.get("parent") or {}
        if item.get("name") == name and int(pobj.get("id", -1)) == int(parent["id"]):
            return item
    return req("POST", "/api/ipam/services/", {
        "parent_object_type": "dcim.device",
        "parent_object_id": parent["id"],
        "name": name,
        "port_mappings": port_mappings,
        "ip_addresses": [x["id"] for x in (ip_addresses or [])],
        "description": description,
    }, token=token)


def main():
    wait_netbox()
    token = get_token()

    # Tenancy
    orgs = ensure("/api/tenancy/tenant-groups/", {"slug": "ai5049-organizations"}, {
        "name": "AI5049 Organizations", "slug": "ai5049-organizations",
        "description": "Organizations represented in the BOB1 classroom network",
    }, token)
    tenants = {}
    for key, name, slug, desc in [
        ("provider", "ReefNet", "reefnet", "Operator of the BOB1 ReefNet edge"),
        ("customer", "Bora Bora Ocean Research", "bora-bora-ocean-research", "Marine research customer at BOB1"),
        ("transit01", "Lagoon Transit", "lagoon-transit", "Fictional upstream provider for BOB1"),
        ("transit02", "Pacific Transit", "pacific-transit", "Fictional upstream provider for BOB1"),
    ]:
        tenants[key] = reconcile("/api/tenancy/tenants/", {"slug": slug}, {
            "name": name, "slug": slug, "group": orgs["id"], "description": desc,
        }, token)

    # Site
    oceania = ensure("/api/dcim/regions/", {"slug": "oceania"}, {
        "name": "Oceania", "slug": "oceania", "description": "Geographic region used by the classroom model",
    }, token)
    fp = ensure("/api/dcim/regions/", {"slug": "french-polynesia"}, {
        "name": "French Polynesia", "slug": "french-polynesia", "parent": oceania["id"],
        "description": "Geographic parent for the fictional BOB1 lab site",
    }, token)
    site_group = ensure("/api/dcim/site-groups/", {"slug": "ai5049-classroom"}, {
        "name": "AI5049 Classroom", "slug": "ai5049-classroom",
        "description": "Sites used for the AI5049 live classroom lab",
    }, token)
    site = ensure("/api/dcim/sites/", {"slug": "bob1"}, {
        "name": "BOB1 - ReefNet Bora Bora", "slug": "bob1", "status": "active",
        "region": fp["id"], "group": site_group["id"], "facility": "BOB1",
        "time_zone": "Pacific/Tahiti",
        "description": "Fictional ReefNet BOB1 site on Bora Bora for the AI5049 classroom lab",
    }, token)
    location = ensure("/api/dcim/locations/", {"site_id": site["id"], "slug": "network-room"}, {
        "site": site["id"], "name": "Network Room", "slug": "network-room", "status": "active",
        "facility": "LAB-NET", "description": "Logical room containing the emulated BOB1 network",
    }, token)
    rack_role = ensure("/api/dcim/rack-roles/", {"slug": "network"}, {
        "name": "Network", "slug": "network", "color": "2196f3",
    }, token)
    rack = ensure("/api/dcim/racks/", {"site_id": site["id"], "name": "BOB1-R01"}, {
        "site": site["id"], "location": location["id"], "name": "BOB1-R01", "status": "active",
        "role": rack_role["id"], "facility_id": "LAB-R01", "u_height": 42,
        "description": "Logical classroom rack for the emulated network devices",
    }, token)

    # Device models
    nokia = ensure("/api/dcim/manufacturers/", {"slug": "nokia"}, {"name": "Nokia", "slug": "nokia"}, token)
    generic = ensure("/api/dcim/manufacturers/", {"slug": "ai5049-lab"}, {"name": "AI5049 Lab", "slug": "ai5049-lab", "description": "Synthetic vendor used only for emulated classroom nodes"}, token)
    srl_platform = ensure("/api/dcim/platforms/", {"slug": "nokia-srlinux-25-10"}, {
        "name": "Nokia SR Linux 25.10", "slug": "nokia-srlinux-25-10", "manufacturer": nokia["id"],
        "description": "Pinned SR Linux classroom release",
    }, token)
    linux_platform = ensure("/api/dcim/platforms/", {"slug": "linux-container"}, {
        "name": "Linux Container", "slug": "linux-container", "description": "Containerized Linux classroom node",
    }, token)
    srltype = ensure("/api/dcim/device-types/", {"slug": "srlinux-ixr-d2l-emulated"}, {
        "manufacturer": nokia["id"], "model": "SR Linux IXR-D2L (emulated)", "slug": "srlinux-ixr-d2l-emulated",
        "u_height": 1, "is_full_depth": False, "default_platform": srl_platform["id"],
    }, token)
    ltype = ensure("/api/dcim/device-types/", {"slug": "linux-classroom-node"}, {
        "manufacturer": generic["id"], "model": "Containerlab Linux Node", "slug": "linux-classroom-node", "u_height": 1,
        "is_full_depth": False, "default_platform": linux_platform["id"],
    }, token)
    stype = ensure("/api/dcim/device-types/", {"slug": "containerized-service"}, {
        "manufacturer": generic["id"], "model": "Containerized Observability Service", "slug": "containerized-service", "u_height": 0,
        "is_full_depth": False, "default_platform": linux_platform["id"],
    }, token)

    roles = {}
    for name, slug, color in [
        ("Provider Edge", "provider-edge", "2f6fdb"), ("Customer Edge", "customer-edge", "f0ad4e"),
        ("Transit Router", "transit-router", "d9534f"), ("Client Host", "client-host", "5bc0de"),
        ("Service Host", "service-host", "9467bd"), ("Management Host", "management-host", "607d8b"),
        ("Telemetry Service", "telemetry-service", "26a69a"),
    ]:
        roles[slug] = ensure("/api/dcim/device-roles/", {"slug": slug}, {"name": name, "slug": slug, "color": color}, token)

    # IPAM and ASNs
    rir = ensure("/api/ipam/rirs/", {"slug": "private-use"}, {
        "name": "RFC 6996 Private Use", "slug": "private-use", "is_private": True,
        "description": "Private-use ASN authority for the AI5049 classroom model",
    }, token)
    asns = {}
    for asn, key, desc in [
        (AS_REEFNET, "provider", "ReefNet autonomous system"), (AS_OCEANRESEARCH, "customer", "Bora Bora Ocean Research autonomous system"),
        (AS_LAGOON, "transit01", "Lagoon Transit autonomous system"), (AS_PACIFIC, "transit02", "Pacific Transit autonomous system"),
    ]:
        asns[asn] = reconcile("/api/ipam/asns/", {"asn": asn}, {
            "asn": asn, "rir": rir["id"], "tenant": tenants[key]["id"], "sites": [site["id"]], "description": desc,
        }, token)
    patch("/api/dcim/sites/", site, {"asns": [obj["id"] for obj in asns.values()]}, token)

    ip_roles = {}
    for name, slug in [
        ("Core point-to-point", "core-p2p"), ("External handoff", "external-handoff"),
        ("Customer service", "customer-service"), ("Management", "management"), ("Loopback", "loopback"),
    ]:
        ip_roles[slug] = ensure("/api/ipam/roles/", {"slug": slug}, {"name": name, "slug": slug}, token)

    # Devices
    specs = {
        "edge01": ("edge01.bob1.reefnet.test", "provider-edge", srltype, srl_platform, "provider", 10),
        "edge02": ("edge02.bob1.reefnet.test", "provider-edge", srltype, srl_platform, "provider", 11),
        "cust01": ("edge01.bob1.oceanresearch.test", "customer-edge", srltype, srl_platform, "customer", 20),
        "transit01": ("edge01.bob1.lagoontransit.test", "transit-router", srltype, srl_platform, "transit01", 30),
        "transit02": ("edge01.bob1.pacifictransit.test", "transit-router", srltype, srl_platform, "transit02", 31),
        "host01": ("probe01.bob1.lagoontransit.test", "client-host", ltype, linux_platform, "transit01", None),
        "host02": ("probe01.bob1.pacifictransit.test", "client-host", ltype, linux_platform, "transit02", None),
        "svc01": ("service01.bob1.oceanresearch.test", "service-host", ltype, linux_platform, "customer", None),
        "ops01": ("operations01.bob1.reefnet.test", "management-host", ltype, linux_platform, "provider", None),
        "gnmic": ("gnmic.bob1.reefnet.test", "telemetry-service", stype, linux_platform, "provider", None),
        "prometheus": ("prometheus.bob1.reefnet.test", "telemetry-service", stype, linux_platform, "provider", None),
        "grafana": ("grafana.bob1.reefnet.test", "telemetry-service", stype, linux_platform, "provider", None),
        "alloy": ("alloy.bob1.reefnet.test", "telemetry-service", stype, linux_platform, "provider", None),
        "loki": ("loki.bob1.reefnet.test", "telemetry-service", stype, linux_platform, "provider", None),
    }
    devices = {}
    for key, (name, role, dtype, platform, tenant, position) in specs.items():
        payload = {
            "name": name, "device_type": dtype["id"], "role": roles[role]["id"], "platform": platform["id"],
            "site": site["id"], "location": location["id"], "tenant": tenants[tenant]["id"], "status": "active",
            "description": f"AI5049 classroom node {name}",
        }
        if position is not None:
            payload.update({"rack": rack["id"], "position": position, "face": "front"})
        devices[key] = ensure("/api/dcim/devices/", {"name": name}, payload, token)

    # Interfaces
    links = {
      "edge01": [("ethernet-1/1", "to edge01.bob1.oceanresearch.test", "1000base-lx", CUSTOMER_SPEED), ("ethernet-1/2", "to edge02.bob1.reefnet.test core-a", "1000base-lx", None), ("ethernet-1/3", "to edge01.bob1.lagoontransit.test", "1000base-lx", LAGOON_SPEED), ("ethernet-1/4", "to edge02.bob1.reefnet.test core-b", "1000base-lx", None), ("system0", "routing loopback", "virtual", None), ("mgmt0", "Containerlab management", "virtual", None)],
      "edge02": [("ethernet-1/1", "to edge01.bob1.reefnet.test core-a", "1000base-lx", None), ("ethernet-1/2", "to edge01.bob1.pacifictransit.test", "1000base-lx", PACIFIC_SPEED), ("ethernet-1/3", "to edge01.bob1.reefnet.test core-b", "1000base-lx", None), ("system0", "routing loopback", "virtual", None), ("mgmt0", "Containerlab management", "virtual", None)],
      "cust01": [("ethernet-1/1", "to edge01.bob1.reefnet.test", "1000base-lx", CUSTOMER_SPEED), ("ethernet-1/2", "to service01.bob1.oceanresearch.test", "1000base-t", None), ("system0", "routing loopback", "virtual", None), ("mgmt0", "Containerlab management", "virtual", None)],
      "transit01": [("ethernet-1/1", "to edge01.bob1.reefnet.test", "1000base-lx", LAGOON_SPEED), ("ethernet-1/2", "to probe01.bob1.lagoontransit.test", "1000base-t", None), ("system0", "routing loopback", "virtual", None), ("mgmt0", "Containerlab management", "virtual", None)],
      "transit02": [("ethernet-1/1", "to edge02.bob1.reefnet.test", "1000base-lx", PACIFIC_SPEED), ("ethernet-1/2", "to probe01.bob1.pacifictransit.test", "1000base-t", None), ("system0", "routing loopback", "virtual", None), ("mgmt0", "Containerlab management", "virtual", None)],
      "host01": [("eth1", "to edge01.bob1.lagoontransit.test", "1000base-t", None), ("eth0", "Containerlab management", "virtual", None)],
      "host02": [("eth1", "to edge01.bob1.pacifictransit.test", "1000base-t", None), ("eth0", "Containerlab management", "virtual", None)],
      "svc01": [("eth1", "to edge01.bob1.oceanresearch.test", "1000base-t", None), ("eth0", "Containerlab management", "virtual", None)],
      "ops01": [("eth0", "Containerlab management", "virtual", None)],
      "gnmic": [("eth0", "Containerlab management", "virtual", None)],
      "prometheus": [("eth0", "Containerlab management", "virtual", None)],
      "grafana": [("eth0", "Containerlab management", "virtual", None)],
      "alloy": [("eth0", "Containerlab management", "virtual", None)],
      "loki": [("eth0", "Containerlab management", "virtual", None)],
    }
    ifaces = {}
    for dev, entries in links.items():
        for name, desc, itype, speed in entries:
            payload = {
                "device": devices[dev]["id"], "name": name, "type": itype, "description": desc, "enabled": True,
            }
            if speed is not None:
                payload["speed"] = speed
            ifaces[(dev, name)] = reconcile(
                "/api/dcim/interfaces/",
                {"device_id": devices[dev]["id"], "name": name},
                payload,
                token,
            )

    # Prefixes
    prefixes = [
      ("10.0.0.0/31", "core-p2p", "provider", "edge01-edge02 core-a IPv4"),
      ("10.0.0.2/31", "core-p2p", "provider", "edge01-edge02 core-b IPv4"),
      ("2001:db8:0:12::/127", "core-p2p", "provider", "edge01-edge02 core-a IPv6"),
      ("2001:db8:0:14::/127", "core-p2p", "provider", "edge01-edge02 core-b IPv6"),
      ("192.0.2.0/31", "external-handoff", "customer", "Bora Bora Ocean Research ↔ ReefNet IPv4"),
      ("2001:db8:0:10::/127", "external-handoff", "customer", "Bora Bora Ocean Research ↔ ReefNet IPv6"),
      ("192.0.2.2/31", "external-handoff", "transit01", "ReefNet ↔ Lagoon Transit IPv4"),
      ("2001:db8:0:a::/127", "external-handoff", "transit01", "ReefNet ↔ Lagoon Transit IPv6"),
      ("192.0.2.4/31", "external-handoff", "transit02", "ReefNet ↔ Pacific Transit IPv4"),
      ("2001:db8:0:b::/127", "external-handoff", "transit02", "ReefNet ↔ Pacific Transit IPv6"),
      ("198.51.100.0/24", "customer-service", "customer", "Bora Bora Ocean Research service IPv4"),
      ("2001:db8:100::/48", "customer-service", "customer", "Bora Bora Ocean Research service IPv6"),
      ("203.0.113.0/25", "external-handoff", "transit01", "Lagoon Transit probe LAN"),
      ("2001:db8:a::/64", "external-handoff", "transit01", "Lagoon Transit probe LAN IPv6"),
      ("203.0.113.128/25", "external-handoff", "transit02", "Pacific Transit probe LAN"),
      ("2001:db8:b::/64", "external-handoff", "transit02", "Pacific Transit probe LAN IPv6"),
      ("172.20.20.0/24", "management", "provider", "Containerlab management network"),
      ("10.255.0.0/24", "loopback", "provider", "ReefNet edge loopbacks"),
      ("10.255.10.0/24", "loopback", "customer", "Bora Bora Ocean Research loopbacks"),
      ("10.255.100.0/24", "loopback", "transit01", "Lagoon Transit loopbacks"),
      ("10.255.200.0/24", "loopback", "transit02", "Pacific Transit loopbacks"),
    ]
    for prefix, role, tenant, desc in prefixes:
        ensure("/api/ipam/prefixes/", {"prefix": prefix}, {
            "prefix": prefix, "scope_type": "dcim.site", "scope_id": site["id"], "tenant": tenants[tenant]["id"],
            "status": "active", "role": ip_roles[role]["id"], "description": desc,
        }, token)

    # IP addresses
    addresses = [
      ("edge01", "ethernet-1/1", "192.0.2.1/31", ""), ("edge01", "ethernet-1/1", "2001:db8:0:10::1/127", ""),
      ("edge01", "ethernet-1/2", "10.0.0.0/31", ""), ("edge01", "ethernet-1/2", "2001:db8:0:12::/127", ""),
      ("edge01", "ethernet-1/3", "192.0.2.3/31", ""), ("edge01", "ethernet-1/3", "2001:db8:0:a::1/127", ""),
      ("edge01", "ethernet-1/4", "10.0.0.2/31", ""), ("edge01", "ethernet-1/4", "2001:db8:0:14::/127", ""),
      ("edge02", "ethernet-1/1", "10.0.0.1/31", ""), ("edge02", "ethernet-1/1", "2001:db8:0:12::1/127", ""),
      ("edge02", "ethernet-1/2", "192.0.2.4/31", ""), ("edge02", "ethernet-1/2", "2001:db8:0:b::/127", ""),
      ("edge02", "ethernet-1/3", "10.0.0.3/31", ""), ("edge02", "ethernet-1/3", "2001:db8:0:14::1/127", ""),
      ("cust01", "ethernet-1/1", "192.0.2.0/31", ""), ("cust01", "ethernet-1/1", "2001:db8:0:10::/127", ""),
      ("cust01", "ethernet-1/2", "198.51.100.1/24", ""), ("cust01", "ethernet-1/2", "2001:db8:100::1/48", ""),
      ("transit01", "ethernet-1/1", "192.0.2.2/31", ""), ("transit01", "ethernet-1/1", "2001:db8:0:a::/127", ""),
      ("transit01", "ethernet-1/2", "203.0.113.1/25", ""), ("transit01", "ethernet-1/2", "2001:db8:a::1/64", ""),
      ("transit02", "ethernet-1/1", "192.0.2.5/31", ""), ("transit02", "ethernet-1/1", "2001:db8:0:b::1/127", ""),
      ("transit02", "ethernet-1/2", "203.0.113.129/25", ""), ("transit02", "ethernet-1/2", "2001:db8:b::1/64", ""),
      ("host01", "eth1", "203.0.113.10/25", "probe01.bob1.lagoontransit.test"), ("host01", "eth1", "2001:db8:a::10/64", "probe01.bob1.lagoontransit.test"),
      ("host02", "eth1", "203.0.113.138/25", "probe01.bob1.pacifictransit.test"), ("host02", "eth1", "2001:db8:b::10/64", "probe01.bob1.pacifictransit.test"),
      ("svc01", "eth1", "198.51.100.10/24", "data.oceanresearch.test"), ("svc01", "eth1", "2001:db8:100::10/48", "data.oceanresearch.test"),
      ("edge01", "system0", "10.255.0.1/32", "edge01.bob1.reefnet.test"), ("edge02", "system0", "10.255.0.2/32", "edge02.bob1.reefnet.test"),
      ("cust01", "system0", "10.255.10.1/32", "edge01.bob1.oceanresearch.test"), ("transit01", "system0", "10.255.100.1/32", "edge01.bob1.lagoontransit.test"),
      ("transit02", "system0", "10.255.200.1/32", "edge01.bob1.pacifictransit.test"),
    ]
    mgmt = {
      "edge01": ("mgmt0", "172.20.20.11/24"), "edge02": ("mgmt0", "172.20.20.12/24"),
      "cust01": ("mgmt0", "172.20.20.21/24"), "transit01": ("mgmt0", "172.20.20.22/24"),
      "transit02": ("mgmt0", "172.20.20.23/24"), "host01": ("eth0", "172.20.20.31/24"),
      "host02": ("eth0", "172.20.20.32/24"), "svc01": ("eth0", "172.20.20.33/24"),
      "ops01": ("eth0", "172.20.20.40/24"), "gnmic": ("eth0", "172.20.20.41/24"),
      "prometheus": ("eth0", "172.20.20.42/24"), "grafana": ("eth0", "172.20.20.43/24"),
      "alloy": ("eth0", "172.20.20.45/24"), "loki": ("eth0", "172.20.20.46/24"),
    }
    for dev, (iface, addr) in mgmt.items():
        addresses.append((dev, iface, addr, specs[dev][0]))

    address_objs = {}
    for dev, iface, addr, dns_name in addresses:
        payload = {
            "address": addr, "status": "active", "tenant": tenants[specs[dev][4]]["id"],
            "assigned_object_type": "dcim.interface", "assigned_object_id": ifaces[(dev, iface)]["id"],
            "description": f"{specs[dev][0]} {iface}",
        }
        if dns_name: payload["dns_name"] = dns_name
        if iface == "system0": payload["role"] = "loopback"
        obj = ensure("/api/ipam/ip-addresses/", {"address": addr}, payload, token)
        address_objs[(dev, iface, addr)] = obj

    for dev, (iface, addr) in mgmt.items():
        patch("/api/dcim/devices/", devices[dev], {"primary_ip4": address_objs[(dev, iface, addr)]["id"]}, token)

    # Physical topology
    cable_links = [
      (("cust01", "ethernet-1/1"), ("edge01", "ethernet-1/1"), "smf-os2"),
      (("edge01", "ethernet-1/2"), ("edge02", "ethernet-1/1"), "smf-os2"),
      (("edge01", "ethernet-1/4"), ("edge02", "ethernet-1/3"), "smf-os2"),
      (("edge01", "ethernet-1/3"), ("transit01", "ethernet-1/1"), "smf-os2"),
      (("edge02", "ethernet-1/2"), ("transit02", "ethernet-1/1"), "smf-os2"),
      (("cust01", "ethernet-1/2"), ("svc01", "eth1"), "cat6a"),
      (("transit01", "ethernet-1/2"), ("host01", "eth1"), "cat6a"),
      (("transit02", "ethernet-1/2"), ("host02", "eth1"), "cat6a"),
    ]
    for a_key, b_key, ctype in cable_links:
        label = f"{specs[a_key[0]][0]}:{a_key[1]} -- {specs[b_key[0]][0]}:{b_key[1]}"
        ensure_cable(ifaces[a_key], ifaces[b_key], label, ctype, token)

    # Transit circuits
    providers = {}
    for key, name, slug, asn in [
        ("transit01", "Lagoon Transit", "lagoon-transit", AS_LAGOON),
        ("transit02", "Pacific Transit", "pacific-transit", AS_PACIFIC),
    ]:
        providers[key] = reconcile("/api/circuits/providers/", {"slug": slug}, {
            "name": name, "slug": slug, "asns": [asns[asn]["id"]],
            "description": f"Fictional classroom transit provider represented by {specs[key][0]}",
        }, token)
    circuit_type = ensure("/api/circuits/circuit-types/", {"slug": "ip-transit"}, {
        "name": "IP Transit", "slug": "ip-transit", "color": "3f51b5", "description": "External IP transit handoff",
    }, token)
    provider_nets = {}
    circuits = {}
    for key, cid, desc in [
        ("transit01", "BOB1-LAGOON-001", "Primary classroom transit via edge01.bob1.lagoontransit.test"),
        ("transit02", "BOB1-PACIFIC-001", "Secondary classroom transit via edge01.bob1.pacifictransit.test"),
    ]:
        provider_nets[key] = reconcile("/api/circuits/provider-networks/", {"provider_id": providers[key]["id"], "name": f"{providers[key]['name']} Backbone"}, {
            "provider": providers[key]["id"], "name": f"{providers[key]['name']} Backbone", "service_id": f"AS{AS_LAGOON if key == 'transit01' else AS_PACIFIC}",
            "description": "Provider-side network represented as a black box in NetBox",
        }, token)
        circuits[key] = reconcile("/api/circuits/circuits/", {"provider_id": providers[key]["id"], "cid": cid}, {
            "cid": cid, "provider": providers[key]["id"], "type": circuit_type["id"], "status": "active",
            "tenant": tenants["provider"]["id"], "commit_rate": LAGOON_SPEED if key == "transit01" else PACIFIC_SPEED, "description": desc,
        }, token)
        a_term = ensure("/api/circuits/circuit-terminations/", {"circuit_id": circuits[key]["id"], "term_side": "A"}, {
            "circuit": circuits[key]["id"], "term_side": "A", "termination_type": "dcim.site", "termination_id": site["id"],
            "port_speed": LAGOON_SPEED if key == "transit01" else PACIFIC_SPEED, "description": f"BOB1 handoff toward {specs[key][0]}",
        }, token)
        patch("/api/circuits/circuit-terminations/", a_term, {
            "port_speed": LAGOON_SPEED if key == "transit01" else PACIFIC_SPEED,
            "description": f"BOB1 handoff toward {specs[key][0]}",
        }, token)
        z_term = ensure("/api/circuits/circuit-terminations/", {"circuit_id": circuits[key]["id"], "term_side": "Z"}, {
            "circuit": circuits[key]["id"], "term_side": "Z", "termination_type": "circuits.providernetwork", "termination_id": provider_nets[key]["id"],
            "port_speed": LAGOON_SPEED if key == "transit01" else PACIFIC_SPEED, "description": "Provider backbone termination",
        }, token)
        patch("/api/circuits/circuit-terminations/", z_term, {
            "port_speed": LAGOON_SPEED if key == "transit01" else PACIFIC_SPEED,
            "description": "Provider backbone termination",
        }, token)

    # Services
    # Management services use management IPs. Customer services use service IPs.
    def mgmt_ip(dev):
        iface, addr = mgmt[dev]
        return [address_objs[(dev, iface, addr)]]

    for dev in ["edge01", "edge02", "cust01", "transit01", "transit02"]:
        ensure_service(devices[dev], "SSH", ["tcp/22"], "SR Linux CLI access", token, mgmt_ip(dev))
        ensure_service(devices[dev], "gNMI", ["tcp/57400"], "SR Linux gNMI management API", token, mgmt_ip(dev))
    svc_ips = [address_objs[("svc01", "eth1", "198.51.100.10/24")], address_objs[("svc01", "eth1", "2001:db8:100::10/48")]]
    ensure_service(devices["svc01"], "DNS", ["udp/53"], "Deterministic data.oceanresearch.test DNS endpoint", token, svc_ips)
    ensure_service(devices["svc01"], "HTTP", ["tcp/80"], "Classroom HTTP service endpoint", token, svc_ips)
    ensure_service(devices["svc01"], "iperf3", ["tcp/5201"], "Traffic measurement endpoint", token, svc_ips)
    ensure_service(devices["gnmic"], "Prometheus metrics", ["tcp/9804"], "gNMIc Prometheus exporter", token, mgmt_ip("gnmic"))
    ensure_service(devices["prometheus"], "Prometheus", ["tcp/9090"], "Metrics database and query API", token, mgmt_ip("prometheus"))
    ensure_service(devices["grafana"], "Grafana", ["tcp/3000"], "BOB1 dashboards", token, mgmt_ip("grafana"))
    ensure_service(devices["alloy"], "Alloy HTTP", ["tcp/12345"], "Grafana Alloy health/API endpoint", token, mgmt_ip("alloy"))
    ensure_service(devices["alloy"], "Syslog ingest", ["udp/1514"], "SR Linux remote syslog receiver", token, mgmt_ip("alloy"))
    ensure_service(devices["loki"], "Loki", ["tcp/3100"], "Log query API", token, mgmt_ip("loki"))

    # Validation
    expected = {
        "sites": ("/api/dcim/sites/", 1), "locations": ("/api/dcim/locations/", 1), "racks": ("/api/dcim/racks/", 1),
        "devices": ("/api/dcim/devices/", 14), "interfaces": ("/api/dcim/interfaces/", 35), "cables": ("/api/dcim/cables/", 8),
        "prefixes": ("/api/ipam/prefixes/", 21), "IP addresses": ("/api/ipam/ip-addresses/", 51), "ASNs": ("/api/ipam/asns/", 4),
        "services": ("/api/ipam/services/", 19), "providers": ("/api/circuits/providers/", 2), "provider networks": ("/api/circuits/provider-networks/", 2), "circuits": ("/api/circuits/circuits/", 2),
        "circuit terminations": ("/api/circuits/circuit-terminations/", 4), "tenants": ("/api/tenancy/tenants/", 4),
    }
    results = {}
    for label, (path, minimum) in expected.items():
        n = count(path, token)
        if n < minimum:
            raise RuntimeError(f"NetBox integrity check: expected at least {minimum} {label}, found {n}")
        results[label] = n

    print("NetBox source of truth ready")
    print(f"  Site                  BOB1 - ReefNet Bora Bora")
    print(f"  Devices / interfaces  {results['devices']} / {results['interfaces']}")
    print(f"  Prefixes / IPs        {results['prefixes']} / {results['IP addresses']}")
    print(f"  ASNs / tenants        {results['ASNs']} / {results['tenants']}")
    print(f"  Providers / circuits  {results['providers']} / {results['circuits']}")
    print(f"  Provider networks      {results['provider networks']}")
    print(f"  Cables / services     {results['cables']} / {results['services']}")
    print("  Physical traces       available on all 8 data-plane links")
    print("Token written to /state/netbox-token")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"NetBox bootstrap failed: {e}", file=sys.stderr)
        sys.exit(1)
