# network-management-and-monitoring

Networking lab for AI5049 at Hochschule Fulda. ReefNet is a small dual-stack ISP with two upstream providers and one customer, Bora Bora Ocean Research.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/topology-dark.svg">
  <img src="assets/topology.svg" alt="ReefNet BOB1 with two routers, two core links, two transit providers and Ocean Research">
</picture>

## Slides

[PDF](slides/exports/nmm.pdf) | [HTML](slides/exports/nmm.html) | [PowerPoint](slides/exports/nmm.pptx) | [Source](slides/nmm.md)

## Exercises

After a short demo, work through the exercises at your own pace. You can finish at home.

[Exercises](EXERCISES.md) | [CheatSheet PDF](slides/exports/cheatsheet.pdf) | [CheatSheet HTML](slides/exports/cheatsheet.html)

`make exercises` shows the overview. `make cheatsheet` prints the command reference without a running lab.

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

`make task` gives the task, `make hint` offers help and `make solution STEP=1` shows a worked step. Choose another step with `STEP=2`. Run these in WSL.

Note your findings and next step before stopping. Starting a scenario again recreates its initial state. See the [exercise instructions](EXERCISES.md#start-and-get-help).

## Access

| Service | Address | Login |
|---|---|---|
| NetBox | http://localhost:8000 | `admin` / `admin` |
| Grafana | http://localhost:3000 | Anonymous administration |
| Prometheus | http://localhost:9090 | No login |
| Router CLI / gNMI | Device FQDN | `admin` / `NokiaSrl1!` |

The passwords above are lab defaults. Grafana allows anonymous administration and ports listen on host interfaces, so keep the lab on a trusted network.

Use the [CheatSheet](slides/resources/CHEATSHEET.md) for node access, traffic controls and fault experiments. Leave Linux with `exit` and router CLIs with `quit`.

Router management names and SSH resolve on `operations01.bob1.reefnet.test`. The probe DNS serves `data.oceanresearch.test`. Device names and links are defined in the [network model](tools/bob1_model.json).

## Traffic

- Customer handoff: **100 Mbit/s**
- Lagoon Transit handoff: **50 Mbit/s**
- Pacific Transit handoff: **50 Mbit/s**

Choose one load at a time with `make traffic-40mbit`, `make traffic-60mbit` or `make traffic-75mbit`. Return to `make traffic-10mbit` after measuring. `make traffic-stop` stops it. More controls: `make help`.

The SR Linux container has a 10,000 packets/s forwarding limit. Traffic uses 1200-byte UDP datagrams and tops out at 75 Mbit/s, so the transit link should hit its limit first.

## Grafana

Open the `ReefNet / BOB1` folder, starting with **Network Overview**. Use **Topology & Paths** to locate links, **Fault Analysis** to investigate, **Service Health** for probes and **Device Detail** for one router. **Telemetry Health** checks collection and logs. Dashboards refresh every five seconds.

Ingress and egress discards are separate. Linux queue drops in Telemetry Health can count the same losses, so do not add them to SR Linux discards.

## Housekeeping

| Command | Action |
|---|---|
| `make down` | Stop runtime, keep NetBox data |
| `make reset` | Rebuild the current scenario |
| `make clean` | **Delete lab state and NetBox data**, keep downloaded images |
| `make status` | Show runtime status |
| `make test` | Probe customer IPv4/IPv6 reachability from both upstreams |
| `make course-check` | Restart and test all four scenarios, then stop |
| `make check` | Check source, documentation and network model without Docker |
| `make healthy` | Clear faults, stop traffic and restore link capacities |
| `make help` | List commands |

After `make clean`, run `make setup` again.

## Troubleshooting

Start with `make doctor` and the failed phase in `.state/setup-*.log`. `make diagnostics` collects more detail.

Common causes:

- Not enough free disk space
- Docker stopped or inaccessible to your Linux user
- Another process using port 8000, 3000, 9090, 3100 or 12345

Fix the cause and rerun `make setup`. Existing NetBox data is kept unless the database schema has changed.

Project submission: [contributions and declaration of independent work](slides/resources/templates/DECLARATION.md).

<details>
<summary>Editing slides and handouts</summary>

Build with Node.js 18+, npm and Chromium:

```bash
cd slides
npm ci
npm run build
```

- Exports: lecture HTML, PDF and PPTX plus CheatSheet HTML/PDF in `slides/exports/`. PowerPoint contains slide images. Edit lecture content in the Marp source.
- Install Liberation fonts. Set `CHROME_PATH` if Chromium is not at `/usr/bin/chromium`.
- For VS Code preview, use the Marp extension and enable `markdown.marp.enableHtml`.
- Lecture theme: `slides/theme/ai5049.css`. A4 reference: `slides/resources/CHEATSHEET.md` and `slides/theme/handout.css`. The CLI uses the same reference source.
- [Diagram sources](slides/assets/README.md) and [teaching data](slides/assets/data/README.md) describe regeneration. Python 3 is needed for the generators.
- `npm run build:handouts` builds only the CheatSheet. `npm run sampling` regenerates the synthetic timing-model data. Run all npm commands from `slides/`.

From the repository root, `make slides` builds all exports and `make handouts` builds only the CheatSheet.

</details>
