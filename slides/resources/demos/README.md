# Recorded instructor demos

These are real command outputs from the local rehearsal, not synthetic data. Each transcript records capture time, base Git revision, kernel and router image. The base revision precedes the local teaching-document edits. Results demonstrate one run and do not establish identical timing or throughput on other computers.

| Transcript | Use |
|---|---|
| [Networking](networking.txt) | Host, DNS, HTTP, routes and return path |
| [Operations](operations.txt) | Failed controls, route boundary, effective policy, CLI repair and verification |
| [Automation](automation.txt) | Filtered inventory, gNMI read/write/read-back and independent service checks |
| [Monitoring](monitoring.txt) | Freshness, counter snapshots, receiver loss, link fault and restoration |
| [Physical discard counters](discard-counters.txt) | Physical egress counter and its recorded time series during the monitoring run |

The 10 October 2026 rehearsal passed all four course scenarios. In Monitoring, the physical Lagoon egress counter remained zero below capacity, increased under overload and stopped increasing after load reduction. `show interface ... detail` includes subinterface discards. Use `info from state interface ethernet-1/1 statistics` for the physical `out-discarded-packets` counter. The additional transcript records this distinction, and new captures include the physical counter directly.

Container aliases in these transcripts: host01 = Lagoon probe, host02 = Pacific probe, svc01 = customer service, ops01 = operator workstation, edge01/edge02 = ReefNet, transit01 = Lagoon, transit02 = Pacific, cust01 = Ocean Research. The worksheet and CheatSheet use their full names.

Show only the relevant command and output. Reveal the diagnosis and repair during debrief. If the live demo is unavailable, continue from these files rather than waiting for lab startup. Counter values, route ages and timestamps will differ on a new run.

To refresh, first run `make networking`, then `python3 scripts/capture-teaching.py` from the repository. The capture script changes routing faults, offered traffic and core-b, and restores healthy state after successful completion. This optional instructor recording tool requires Python 3 on the WSL host, Docker access and a prepared lab. Student exercises do not require this recording tool. It overwrites these transcripts. If interrupted, inspect the state and use `make healthy` before another rehearsal. Review outputs for errors and sensitive data before publishing.

To repeat one recording on a healthy prepared lab, use `python3 scripts/capture-teaching.py --only monitoring` (or `networking`, `operations`, `automation`). Other transcripts are kept.
