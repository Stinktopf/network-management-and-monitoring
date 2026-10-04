# shellcheck shell=bash
case $- in
  *i*) ;;
  *) return 0 ;;
esac

_lab_node=$(hostname)
printf '\nAI5049 · %s\n' "$_lab_node"
case "$_lab_node" in
  operations01.bob1.reefnet.test)
    cat <<'GUIDE'
Operator workstation · BOB1

Router SSH and gNMI use management names from this workstation.
  ssh edge01.bob1.reefnet.test
  ssh edge02.bob1.reefnet.test
  ssh edge01.bob1.oceanresearch.test
  ssh edge01.bob1.lagoontransit.test
  ssh edge01.bob1.pacifictransit.test
Credentials: admin / NokiaSrl1!
Leave a router with quit to return here.
GUIDE
    ;;
  probe01.bob1.lagoontransit.test|probe01.bob1.pacifictransit.test)
    cat <<'GUIDE'
External service probe · BOB1

Inspect the customer data path from this probe:
  ip -br addr
  ip route
  ping -4 -c 3 -W 1 198.51.100.10
  ping -6 -c 3 -W 1 2001:db8:100::10
  traceroute -n -4 -w 1 -q 1 -m 8 198.51.100.10
  dig @198.51.100.10 data.oceanresearch.test A +time=1 +tries=1

Customer DNS requires a working data path. Test IP reachability separately.
For router SSH, return to WSL with exit, then run:
  make enter NODE=operations01.bob1.reefnet.test
GUIDE
    ;;
  service01.bob1.oceanresearch.test)
    cat <<'GUIDE'
Customer service · BOB1

  ip -br addr
  ip route
  tail -n 10 /tmp/iperf-server.log
  dig @127.0.0.1 data.oceanresearch.test A
GUIDE
    ;;
  *) printf 'Lab shell\n' ;;
esac
printf '\nReturn to the WSL repository with exit. Run make next there for the guided investigation.\n\n'
unset _lab_node
