# Teaching the BOB1 labs

Start each lab together. Demonstrate one command, read its output with the class,
then ask students to choose a check that distinguishes two possible explanations.
They should justify the next command before running it. Syntax help is available
without giving away the expected result.

| In the WSL repository | Purpose |
|---|---|
| `make next` | Short task and starting point for step 1 |
| `make next STEP=2` | Move to a chosen task |
| `make hint STEP=2` | Commands and questions for that task |
| `make solution STEP=2` | Full investigation and worked answer |
| `make solution SCENARIO=operations` | All worked steps for instructor preparation |

These commands display text. Repeating one shows the same step. They do not run
commands or remember progress. `STEP=all` shows every step at the selected help level.
Return from Linux nodes with `exit` and from SR Linux with `quit` before running
another make command in WSL. Router management names and SSH belong on operations01.

Keep the full solution in a separate instructor terminal until the discussion.
The investigation commands, output fields, alternative explanations, exact repair
and conditional rollback are maintained together in [the guide sources](scripts/guides).
Show one block at a time. A worked solution is not a script to paste wholesale.
Do not run its conditional rollback after a successful repair.

## Networking: build a baseline together

Start with `make networking`. No repair is expected. The shared demonstration is
`ip -br addr` and `ip route` on the Lagoon probe. Have the class identify the service
interface and gateway before choosing a ping or traceroute. Then let students
repeat their chosen checks from Pacific and explain the differences.

| Step | Shared prompt and independent work | Evidence to discuss |
|---|---|---|
| 1 | Read one probe's addresses together, then compare the other source and IPv6 | Source, gateway, path and four reachability results |
| 2 | Read one `dig` response together, then resolve a router name on operations01 | DNS status, answer, server and management address |
| 3 | Compare one BGP entry with its forwarding entry, then investigate Edge 02 | Peer AS, active route, next hop and the role of OSPF |
| 4 | Ask how the reply gets back, then inspect customer and service | Both probe return prefixes, local DNS and external checks |

Expected baseline: Lagoon uses 203.0.113.10/25 via 203.0.113.1, Pacific uses
203.0.113.138/25 via 203.0.113.129. Customer DNS returns 198.51.100.10 and
2001:db8:100::10. All four external checks pass. Router names resolve through
the operator's management mapping, not through customer DNS.

Deliverable: a path sketch with forward and return routes plus the healthy result
matrix. Discuss why an established BGP session or a silent traceroute hop alone
cannot establish whether the application works.

## Operations: investigate before revealing the cause

Start with `make operations`. Project the incident and the short `make next` task.
Run one reachability check together. Ask students to choose a control before giving
them the source/address-family matrix. Reveal hints only when they need command
syntax or cannot identify the next useful observation.

| Step | Shared prompt and independent work | Evidence required before moving on |
|---|---|---|
| 1 | Reproduce one symptom, then compare sources, families and DNS | Affected combination and working controls |
| 2 | Read interface and neighbor state, then inspect both ends of the path | Cabled ports and relevant sessions, not unused disabled ports |
| 3 | Follow the customer prefix into ReefNet and check the reply path | Receipt, active forwarding entry and customer return route |
| 4 | Compare one sender/receiver pair, then use Pacific as a control | First boundary where the exact prefix differs |
| 5 | Read the attachment chain together, then let students trace the matching rule | Peer, group, effective policy, prefix match and action |
| 6 | Have students propose a change and rollback, then review the candidate diff | Only the justified change before commit |
| 7 | Ask what would falsify a successful repair, then repeat independent checks | Route propagation, four controls and customer DNS |

Instructor result: only Lagoon IPv4 fails. Interfaces and BGP remain up. Edge 01
receives the customer prefix but does not advertise it on its IPv4 session toward
Lagoon. The receiver has no active customer forwarding route, while Pacific works.
Lagoon can still show an unselected BGP path learned from the IPv6 peer. Compare
the route source and active table instead of treating any BGP entry as usable.
The `lagoon-v4`
group overrides the instance export policy with `BLOCK-CUSTOMER-V4`, which rejects
the exact customer prefix. Removing that attachment restores inheritance.

Use `make solution SCENARIO=operations STEP=6` for the precise candidate, diff,
commit and conditional rollback. Require the demonstrated policy chain before
showing the deletion. After convergence, Lagoon's route and DNS must recover and
all four reachability checks must pass. `make reset` recreates the incident.

Deliverable: a short incident record with impact, the first demonstrated routing
boundary, the effective rule, exact change and before/after evidence. If the live
symptoms differ from the reference, investigate them instead of applying its repair.

## Automation: transfer the investigation to APIs

Start with `make automation`. This intentionally repeats the Operations incident.
Read the first NetBox response together. Have students locate the target and prove
agreement between inventory and management resolution before reading device data.

| Step | Shared prompt and independent work | Evidence required before moving on |
|---|---|---|
| 1 | Read one inventory response, then establish live impact | Exactly one intended device, matching IP and service matrix |
| 2 | Read the gNMI envelope together, then trace the effective configuration | Saved config plus independent route/advertisement evidence |
| 3 | Review a proposed path and operation, then re-read its preconditions | Scoped change, original value, Set response and rollback |
| 4 | Compare configuration fields, then verify route and application recovery | Read-back, receiving route, all four controls and DNS |

Use `get --type config` for configuration snapshots. Files under `/state/` on
operations01 appear under `.state/` in WSL. Keep authentication tokens out of
screenshots and reports. Compare configuration values, not response timestamps.

The worked Set removes only the group export-policy override. A preceding read
does not make Set an atomic conditional update. Discuss how another operator could
change the value between those requests. A Set acknowledgement also does not prove
route convergence or service recovery. After deleting an optional leaf, read its
parent group to verify the result.

Deliverable: target evidence, before/after configuration, exact operation and
response, rollback plan and independent service checks. The expected service
recovery is the same as Operations. Do not replace the whole BGP subtree.

## Monitoring: predict, measure, explain

Start with `make monitoring`. Read one baseline panel together, including source,
direction, units, time window and freshness. Before each experiment, ask students
to predict which signals will change and which should remain stable. Change one
variable at a time and retain the previous control.

| Step | Shared prompt and independent work | Evidence to discuss |
|---|---|---|
| 1 | Read one panel, then compare service and collection health | Four passing probes, offered load and fresh samples |
| 2 | Predict the 40 Mbit/s control, then measure 60 and 75 Mbit/s separately | Sending rate/discards and receiver throughput/loss |
| 3 | Compare two counter samples, then lower load to 10 Mbit/s | Deltas, collection validity and whether new drops stop |
| 4 | Predict a single core-link outage, then restore it | Interface/OSPF events and external service continuity |
| 5 | Compare a routing fault with congestion, then restore and stop traffic | Source/family pattern, stable sessions and recovered service |

Allow at least 30 seconds at each load before comparing results. The transit cap
is 50 Mbit/s and the customer cap is 100 Mbit/s. Payload throughput need not equal
the configured cap because of overhead and buffering. The congested sending
handoff is Lagoon Transit ethernet-1/1. Match its direction and observation window
to the receiver. A low rate alone is not proof of congestion at that interface.

Linux netem drops and SR Linux egress discards can observe the same loss. Do not
add them. Inspect raw counter deltas and receiver loss when the rolling dashboard
is ambiguous. After reducing load, old loss remains in a five-minute window.
Missing samples and counter resets invalidate a simple numeric comparison.
The collection streams are sampled separately, so their deltas need not match
exactly. Congestion can also reduce probe success while routes and sessions remain up.

The link experiment disables core-b while core-a remains available. Service can
continue after convergence. The routing experiment instead removes Lagoon IPv4
reachability while links and sessions stay established. Restore each injected
fault and verify recovery before proceeding. The final step stops generated load.

Deliverable: an experiment table with time, load/fault, prediction, observation,
control and explanation. Report observed values rather than copying a nominal cap
or treating a graph's shape as the causal explanation.

## Local rehearsal, 4 October 2026

Executed on SR Linux 25.10 and WSL kernel 6.18.33.2. Networking, Operations and
Automation were started separately and their investigation commands exercised.
Both CLI and gNMI repairs restored the route, all four reachability checks and DNS.
The gNMI before/after comparison confirmed only the intended override was removed.

| Offered UDP load | Observed receiver throughput | Observed receiver loss |
|---|---|---|
| 40 Mbit/s | About 40 Mbit/s | 0% |
| 60 Mbit/s | About 48.3 Mbit/s | About 19–20% |
| 75 Mbit/s | About 48.3 Mbit/s | About 36% |
| 10 Mbit/s after reducing load | About 10 Mbit/s | 0% |

These are steady one-second receiver observations after at least 30 seconds per
load. Linux queue and SR Linux egress counters increased above the cap, while the
sampled ingress counter did not. Values vary with host load and sampling time.
At 10 Mbit/s neither drop counter increased during the 35-second comparison.

The rehearsal corrected two teaching details: the general routing-table command
needs `summary`, and a received BGP path on Lagoon can exist without an active
customer forwarding route. Local command outputs are retained in `.state/teaching-*`.

The link outage retained all four service checks while the OSPF neighbor count
changed from two to one and returned to two after restoration. The routing fault
reproduced only Lagoon IPv4 failure. After repair all four checks passed again,
and generated traffic was stopped. The five referenced Grafana views were checked
with rendered panels and no query or JavaScript errors.
