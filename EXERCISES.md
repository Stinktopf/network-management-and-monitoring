# Working with ReefNet

After the demo, work through the exercises at your own pace on the university lab PCs. No submission is required.

Containerlab and the course WSL are preinstalled there. [Clone the repository and run `make setup`](README.md#setup). Wait for `READY FOR CLASS`, then start Networking.

To repeat an exercise on your own Windows PC, install [WSL-Containerlab](https://github.com/srl-labs/WSL-Containerlab), the same environment used in class, then follow the [lab setup](README.md#setup). Use your notes to repeat the investigation from the scenario's initial state.

Keep the [CheatSheet](slides/exports/cheatsheet.pdf) open for node access, investigation commands, traffic and faults. In the terminal: `make cheatsheet`.

## Start and get help

Run `make` commands in the WSL repository. Choose a scenario below, then run `make task`.

| Command | Purpose |
|---|---|
| `make task` | Task and starting point |
| `make hint` | Investigation commands and clues |
| `make solution` | Investigation commands and worked answer |
| `make down` | Remove the running lab and discard router changes |

Use `STEP=2` to select a step, for example `make hint STEP=2`. Solutions show the investigation commands and a concise worked answer. Help does not advance automatically. Each scenario command recreates its starting state. Note your findings and next step before restarting or stopping.

## Exercises

Times exclude the demo. Networking includes 30 minutes for cloning, `make setup` and questions, followed by 30 minutes of exercises.

| Start in WSL | Task | In class |
|---|---|---|
| `make networking` | Follow a request from Lagoon to `data.oceanresearch.test`. Explain name resolution, the outward path and the reply path. | 60 min: 30 setup + 30 exercise |
| `make operations` | Lagoon reports a service failure. Reproduce it, locate the fault, repair it and verify recovery from both probes over IPv4 and IPv6. | 45 min |
| `make automation` | Investigate the same incident using NetBox and gNMI. Inspect the current configuration, apply a justified change and verify recovery. | 60 min |
| `make monitoring` | Compare offered load, received traffic and loss at the 50 Mbit/s cap. Then compare a link failure, a routing failure and a short burst. Restore the baseline after each experiment. | 75 min |

Each scenario works independently. Record the observations that support your explanation. Use `make task` to start, `make hint` for clues, and `make solution` to compare commands and results.
