# network-management-and-monitoring

Networking lab for AI5049 at Hochschule Fulda. ReefNet is a small dual-stack ISP with two upstream providers and one customer, Bora Bora Ocean Research.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/topology-dark.svg">
  <img src="assets/topology.svg" alt="ReefNet BOB1 with two routers, two core links, two transit providers and Ocean Research">
</picture>

## Slides

[PDF](slides/exports/nmm.pdf) · [HTML](slides/exports/nmm.html) · [PowerPoint](slides/exports/nmm.pptx) · [Source](slides/nmm.md)

Build with Node.js 18+, npm and Chromium:

```bash
cd slides
npm ci
npm run build
```

<details>
<summary>Editing and build notes</summary>

- Exports: HTML, PDF and PPTX in `slides/exports/`. PowerPoint contains slide images and notes. Edit content in the Marp source.
- Install Liberation fonts. Set `CHROME_PATH` if Chromium is not at `/usr/bin/chromium`.
- For VS Code preview, use the Marp extension and enable `markdown.marp.enableHtml`.
- Edit `slides/theme/ai5049.css` for theme changes, then rebuild.
- Diagrams are editable SVGs. To regenerate them, edit the generators in `slides/tools/` and run `npm run diagrams` followed by `npm run build`. This needs Python 3 and overwrites direct SVG edits.
- `npm run sampling` regenerates the synthetic timing-model data. Run all npm commands from `slides/`.

</details>

## Setup

Use the Containerlab WSL distribution provided for the course.

- Docker must be running. Docker Compose, Containerlab, Git, Make and curl must be installed.
- Leave 15 GiB of disk space for the lab and its images. Setup needs Internet access.
- Recommended: 12 GiB RAM and four CPU threads.

In PowerShell:

```powershell
wsl -d Containerlab
```

Inside WSL, clone into your Linux home directory. Avoid `/mnt/c` and OneDrive.

```bash
cd ~
git clone https://github.com/Stinktopf/network-management-and-monitoring.git
cd network-management-and-monitoring
make setup
```

Wait for `READY FOR CLASS`. Setup checks all four scenarios, then stops the containers. NetBox data is kept for the exercises. Setup logs are in `.state/`.

## Sessions

Run from `~/network-management-and-monitoring`. Start one session at a time.

| Command | Starting point |
|---|---|
| `make networking` | Healthy baseline |
| `make operations` | Service incident for guided diagnosis |
| `make automation` | Same routing fault, ready for the automation exercise |
| `make monitoring` | Healthy network with telemetry and traffic |

`make next` gives a short task and starting point. `make hint` supplies commands and questions to explore. Select a step with `STEP=2`. `make solution` shows the full investigation, expected results, repair and verification. These commands only display instructions in the WSL terminal.

Work through the first checks together, then let students choose their next checks. [Teaching notes](INSTRUCTOR.md) cover all four labs. For offline preparation: `make solution SCENARIO=operations`.

## Access

| Service | Address | Login |
|---|---|---|
| NetBox | http://localhost:8000 | `admin` / `admin` |
| Grafana | http://localhost:3000 | Anonymous administration |
| Prometheus | http://localhost:9090 | No login |
| Router CLI / gNMI | Device FQDN | `admin` / `NokiaSrl1!` |

The passwords above are lab defaults. Grafana allows anonymous administration and ports listen on host interfaces, so keep the lab on a trusted network.

### Node shells

Choose one command. Leave the shell before entering another node.

```bash
make enter NODE=probe01.bob1.lagoontransit.test
make enter NODE=probe01.bob1.pacifictransit.test
make enter NODE=operations01.bob1.reefnet.test
make enter NODE=edge01.bob1.reefnet.test
```

Leave Linux shells with `exit`, router CLIs with `quit`.

Router management names and SSH are available from the operations node. If you are on a probe, run `exit`, then `make enter NODE=operations01.bob1.reefnet.test` in WSL. From that node:

```bash
ssh edge01.bob1.reefnet.test
```

Example gNMI read from the same node:

```bash
gnmic -a edge01.bob1.reefnet.test:57400 \
  -u admin -p 'NokiaSrl1!' --skip-verify --encoding json_ietf \
  get --path '/interface[name=ethernet-1/1]/oper-state'
```

The customer DNS at `198.51.100.10` serves `data.oceanresearch.test`, not router management names. It can time out when the customer path fails. From the operations node, NetBox is reachable at `netbox.bob1.reefnet.test`. Device names, addresses and links are defined in [`tools/bob1_model.json`](tools/bob1_model.json).

## Faults

| Inject | Restore |
|---|---|
| `make fault-routing` | `make clear-routing` |
| `make fault-link` | `make clear-link` |

`make healthy` clears both faults, stops traffic and restores the capacity profile.

## Traffic

- Customer handoff: **100 Mbit/s**
- Lagoon Transit handoff: **50 Mbit/s**
- Pacific Transit handoff: **50 Mbit/s**

Choose one continuous load. Run traffic commands from the repository directory.

| Command | Effect |
|---|---|
| `make traffic-10mbit`, `make traffic-25mbit`, `make traffic-40mbit` | Below transit capacity |
| `make traffic-50mbit` | At transit capacity |
| `make traffic-60mbit`, `make traffic-75mbit` | Transit congestion |
| `make traffic-stop` | Stop traffic |
| `make traffic-burst-40mbit` | Standalone burst, stop background traffic first |
| `make traffic-status` | Show current traffic |
| `make traffic-diagnostics` | Save traffic and drop counters to `.state/` |

Continuous traffic reconnects after short path interruptions.

The SR Linux container has a 10,000 packets/s forwarding limit. Traffic uses 1200-byte UDP datagrams and tops out at 75 Mbit/s, so the transit link should hit its limit first.

## Grafana

Open the `ReefNet / BOB1` folder. Dashboards refresh every 5 seconds.

- **Network Overview** is the starting point for a quick check.
- **Topology & Paths** shows links and routing domains. `core-a` and `core-b` are the two parallel links between the ReefNet routers.
- **Fault Analysis** compares probes, interfaces and BGP routes.
- **Service Health** shows reachability from the probes.
- **Telemetry Health** helps check the collectors and device logs.
- **Device Detail** narrows the view to one router.

Dashboards show SR Linux ingress and egress discards separately. **Telemetry Health** adds Linux queue drops for diagnosis. These can count the same losses, so do not add them together.

After updating the lab, run `make monitoring` to rebuild the scenario.

## Housekeeping

| Command | Action |
|---|---|
| `make down` | Stop runtime, keep NetBox data |
| `make reset` | Rebuild the current scenario |
| `make clean` | **Delete lab state and NetBox data**, keep downloaded images |
| `make status` | Show runtime status |
| `make test` | Probe customer IPv4/IPv6 reachability from both upstreams |
| `make course-check` | Repeat all scenario and workflow checks |
| `make check` | Check source, documentation and network model without Docker |
| `make next`, `make hint`, `make solution` | Scenario tasks, clues and worked answers |
| `make help` | List commands |

After `make clean`, run `make setup` again.

## Troubleshooting

Start with `make doctor` and the failed phase in `.state/setup-*.log`. `make diagnostics` collects more detail.

Common causes:

- Not enough free disk space
- Docker stopped or inaccessible to your Linux user
- Another process using port 8000, 3000, 9090, 3100 or 12345

Fix the cause and rerun `make setup`. Existing NetBox data is kept unless the database schema has changed.

Project submission: [team contributions and AI disclosure](slides/resources/templates/DECLARATION.md).
