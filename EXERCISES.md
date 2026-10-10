# Working with ReefNet

After the demo, work through the exercises at your own pace. Finish at home if needed. No submission is required.

The course WSL is already installed. [Clone the repository and run `make setup`](README.md#setup). Wait for `READY FOR CLASS`, then start Networking.

Keep the [CheatSheet](slides/exports/cheatsheet.pdf) open for node access, investigation commands, traffic and faults. In the terminal: `make cheatsheet`.

## Start and get help

Run `make` commands in the WSL repository. Choose a scenario below, then run `make task`.

| Command | Purpose |
|---|---|
| `make task` | Task and starting point |
| `make hint` | Investigation commands and clues |
| `make solution` | Complete worked investigation |
| `make down` | Stop the lab |

Use `STEP=2` to select a step, for example `make hint STEP=2`. Help does not advance automatically. Each scenario command recreates its starting state. Note your findings and next step before restarting or stopping.

## Exercises

Times exclude the demo. Networking includes 30 minutes for cloning, `make setup` and questions, followed by 30 minutes of exercises.

| Start in WSL | Task | In class |
|---|---|---|
| `make networking` | Follow a request from Lagoon to `data.oceanresearch.test`. Explain name resolution, the outward path and the reply path. | 60 min: 30 setup + 30 exercise |
| `make operations` | Lagoon reports a service failure. Reproduce it, locate the fault, repair it and verify recovery from both probes over IPv4 and IPv6. | 60 min |
| `make automation` | Investigate the same incident using NetBox and gNMI. Inspect the current configuration, apply a justified change and verify recovery. | 60 min |
| `make monitoring` | Compare offered load, received traffic and loss at the 50 Mbit/s cap. Then compare a link failure, a routing failure and a short burst. Restore the baseline after each experiment. | 75 min |

Each scenario works independently. Record the commands and observations that support your explanation. Procedures and expected results are in `make task`, `make hint` and `make solution`.
