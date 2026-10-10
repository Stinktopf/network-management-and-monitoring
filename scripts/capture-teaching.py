#!/usr/bin/env python3
"""Rehearse demo commands on a prepared healthy lab and save measured evidence.

Run after make networking. Changes routing faults, traffic and core-b, then restores
healthy state. Does not start/destroy containers. Output is reviewed course material.
"""
import argparse
import datetime
import os
from pathlib import Path
import re
import shlex
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
OUT = ROOT / 'slides/resources/demos'
OUT.mkdir(parents=True, exist_ok=True)
log = None

def run(args, location='WSL repository', display=None, expected=(0,), stdin=None, timeout=120):
    command = display or shlex.join(args)
    result = subprocess.run(args, input=stdin, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=timeout)
    output = re.sub(r'\x1b\[[0-9;]*[A-Za-z]', '', result.stdout)
    if log:
        log.write(f'\n[{location}]\n$ {command}\n{output}\n[exit {result.returncode}]\n')
        log.flush()
    if result.returncode not in expected or re.search(r'^\s*(Error:|Parsing error|Invalid command)', output, re.M):
        raise RuntimeError(f'Command failed: {command}\n{output}')
    return output

def shell(script):
    return run(['bash', script])

def node(name, command, expected=(0,)):
    return run(['docker', 'exec', 'clab-ai5049-'+name, 'sh', '-c', command],
               name+' Linux shell', command, expected)

def cli(name, command):
    return run(['docker', 'exec', 'clab-ai5049-'+name, 'bash', '-lc',
                'su -s /bin/bash admin -c '+shlex.quote('/opt/srlinux/bin/sr_cli -d '+shlex.quote(command))],
               name+' SR Linux CLI', command)

def section(name):
    global log
    if log:
        log.close()
    log = (OUT / (name+'.txt')).open('w')
    log.write(f'ReefNet measured rehearsal: {name}\nCaptured: {datetime.datetime.now().astimezone().isoformat()}\n')
    run(['uname', '-sr'])
    run(['git', 'rev-parse', '--short', 'HEAD'], display='git rev-parse --short HEAD (base revision, local teaching edits present)')
    run(['docker', 'inspect', '--format', '{{.Config.Image}}', 'clab-ai5049-edge01'])
    print('Recording '+name, flush=True)

def matrix(fault=False):
    for n in ('host01', 'host02'):
        for af, addr in ((4,'198.51.100.10'),(6,'2001:db8:100::10')):
            bad = fault and n=='host01' and af==4
            node(n, f'ping -{af} -c 2 -W 1 {addr}', (1,) if bad else (0,))
            url=f'http://{addr}/' if af==4 else f'http://[{addr}]/'
            node(n, f'curl --fail --max-time 5 -g -{af} '+shlex.quote(url), (7,28) if bad else (0,))

def routes():
    for n in ('edge01','edge02','transit01','transit02'):
        cli(n,'show network-instance default protocols bgp routes ipv4 prefix 198.51.100.0/24')
        cli(n,'show network-instance default route-table ipv4-unicast prefix 198.51.100.0/24')
    for n,peer in (('edge01','192.0.2.2'),('edge02','192.0.2.5')):
        cli(n,f'show network-instance default protocols bgp neighbor {peer} advertised-routes ipv4')

BGP='/network-instance[name=default]/protocols/bgp'
GROUP=BGP+'/group[group-name=lagoon-v4]'
def gnmi(operation, path):
    return node('ops01', "gnmic -a edge01.bob1.reefnet.test:57400 -u admin -p 'NokiaSrl1!' --skip-verify --encoding json_ietf --timeout 15s "+operation+' '+shlex.quote(path))

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--only', choices=('networking', 'operations', 'automation', 'monitoring'))
args = parser.parse_args()
shell('scripts/wait-healthy.sh')
if args.only in (None, 'networking'):
    section('networking')
    for n in ('host01','host02'):
        for command in ('hostname','ip -br link','ip -br addr','ip route','ip -6 route',
                        'ip route get 198.51.100.10','ip neigh',
                        'dig @198.51.100.10 data.oceanresearch.test A +time=1 +tries=1',
                        'dig @2001:db8:100::10 data.oceanresearch.test AAAA +time=1 +tries=1',
                        'traceroute -n -4 -w 1 -q 1 -m 8 198.51.100.10',
                        'curl --fail --max-time 5 -4 http://data.oceanresearch.test/',
                        'curl --fail --max-time 5 -6 http://data.oceanresearch.test/'):
            node(n,command)
    matrix()
    node('ops01','getent hosts edge01.bob1.reefnet.test')
    for command in ('show interface brief','show interface ethernet-1/1 detail',
                    'show interface ethernet-1/2 detail','show interface ethernet-1/3 detail',
                    'show network-instance default route-table ipv4-unicast summary',
                    'show network-instance default protocols bgp neighbor',
                    'show network-instance default protocols ospf neighbor',
                    'show network-instance default protocols bgp routes ipv6 prefix 2001:db8:100::/48'):
        cli('edge01',command)
    routes()
    cli('cust01','show network-instance default protocols bgp neighbor 192.0.2.1 advertised-routes ipv4')
    for prefix in ('203.0.113.0/25','203.0.113.128/25'):
        cli('cust01','show network-instance default route-table ipv4-unicast prefix '+prefix)

if args.only in (None, 'operations'):
    section('operations')
    shell('scripts/fault-routing.sh')
    run(['bash','scripts/verify-scenario.sh','operations'])
    matrix(True)
    routes()
    for cmd in ('show network-instance default protocols bgp neighbor',
                'info from running network-instance default protocols bgp',
                'info from running network-instance default protocols bgp group lagoon-v4',
                'info from running network-instance default protocols bgp group lagoon-v6',
                'info from running routing-policy'):
        cli('edge01',cmd)
    commands='enter candidate\ndelete / network-instance default protocols bgp group lagoon-v4 export-policy\ndiff\ncommit now\n'
    run(['docker','exec','-i','clab-ai5049-edge01','bash','-lc',
         "su -s /bin/bash admin -c '/opt/srlinux/bin/sr_cli -ed'"],
        'edge01 SR Linux CLI',commands,stdin=commands)
    shell('scripts/wait-healthy.sh')
    routes()
    matrix()

if args.only in (None, 'automation'):
    section('automation')
    shell('scripts/fault-routing.sh')
    run(['bash','scripts/verify-scenario.sh','automation'])
    node('ops01', '''TOKEN=$(cat /state/netbox-token)
    curl -fsSG -H "Authorization: Bearer $TOKEN" \\
      http://netbox.bob1.reefnet.test:8080/api/dcim/devices/ \\
      --data-urlencode name=edge01.bob1.reefnet.test | jq '{count, results: [.results[] | {name, primary_ip4}]}' ''')
    gnmi('get --type config --path',BGP)
    gnmi('set --delete',GROUP+'/export-policy')
    gnmi('get --type config --path',GROUP)
    shell('scripts/wait-healthy.sh')
    matrix()

if args.only in (None, 'monitoring'):
    section('monitoring')
    run(['bash','scripts/traffic.sh','set','25M'])
    run(['bash','scripts/verify-scenario.sh','monitoring'])
    node('ops01', "curl -fsSG --data-urlencode 'query=time() - reefnet_probe_last_run_timestamp_seconds' http://clab-ai5049-prometheus:9090/api/v1/query | jq '.data.result'")
    sample = node('ops01', "timeout 12s gnmic -a edge01.bob1.reefnet.test:57400 -u admin -p 'NokiaSrl1!' --skip-verify --encoding json_ietf subscribe --path '/interface[name=ethernet-1/3]/statistics' --stream-mode sample --sample-interval 5s", (0, 124))
    if 'statistics' not in sample:
        raise RuntimeError('No interface statistics received in demo subscription')
    for load in ('40M','60M','75M','10M'):
        run(['bash','scripts/traffic.sh','set',load])
        log.write('\nObserve for 35 seconds at this load.\n');log.flush()
        cli('transit01','show interface ethernet-1/1 detail')
        cli('transit01','info from state interface ethernet-1/1 statistics')
        time.sleep(35)
        run(['bash','scripts/traffic.sh','status'])
        cli('transit01','show interface ethernet-1/1 detail')
        cli('transit01','info from state interface ethernet-1/1 statistics')
        node('svc01','tail -n 8 /tmp/iperf-server.log')
    shell('scripts/traffic-diagnostics.sh')
    shell('scripts/fault-link.sh')
    cli('edge01','show interface ethernet-1/4 detail')
    cli('edge01','show network-instance default protocols ospf neighbor')
    matrix()
    shell('scripts/clear-link.sh')
    shell('scripts/wait-healthy.sh')
    cli('edge01','show network-instance default protocols ospf neighbor')
    run(['bash','scripts/traffic.sh','stop'])
    run(['bash','scripts/traffic.sh','burst','40M'])
    shell('scripts/healthy.sh')
    shell('scripts/wait-healthy.sh')
    matrix()

log.close()
print('Selected demo commands completed. Service verified healthy.',flush=True)
