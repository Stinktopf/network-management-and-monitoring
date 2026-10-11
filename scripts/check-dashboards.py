#!/usr/bin/env python3
"""Check dashboard navigation, layout and provisioned query execution."""
import argparse
import hashlib
import xml.etree.ElementTree as ET
import json
from pathlib import Path
import re
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]

def get(url):
    with urllib.request.urlopen(url, timeout=20) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--live', action='store_true')
    args = parser.parse_args()
    dashboards = [json.loads(p.read_text()) for p in sorted((ROOT / 'configs/grafana/dashboards').glob('*.json'))]
    uids = {d['uid'] for d in dashboards}
    assert len(uids) == len(dashboards) == 7
    asset = ROOT / "configs/grafana/assets/reefnet-topology.svg"
    ET.fromstring(asset.read_text())
    if args.live:
        with urllib.request.urlopen("http://localhost:3000/public/img/reefnet/reefnet-topology.svg", timeout=10) as response:
            assert response.read() == asset.read_bytes(), "SVG asset not current"
    count = 0
    for d in dashboards:
        assert d['refresh'] == '5s'
        assert {link['url'].split('/')[-1] for link in d['links']} == uids, d['title']
        variables = {v['name'] for v in d['templating']['list']} | {'__range', '__rate_interval'}
        assert len({p['id'] for p in d['panels']}) == len(d['panels'])
        if args.live:
            live = get('http://localhost:3000/api/dashboards/uid/' + d['uid'])['dashboard']
            assert live['panels'] == d['panels'], 'Provisioning not current: ' + d['title']
        for i, panel in enumerate(d['panels']):
            if panel['type'] == 'canvas':
                # Concatenated instant queries contribute Time/Value pairs. Keep
                # tooltip field indices stable even when telemetry is missing.
                targets = panel['targets']
                assert all(t.get('instant') and 'or on() vector(-1)' in t['expr'] for t in targets)
                for element in panel['options']['root']['elements']:
                    for link in element.get('links', []):
                        uid = link['url'].split('/')[2]
                        assert uid in uids, link['url']
                        for index in re.findall(r'__data.fields\[(\d+)\]', link['title']):
                            assert int(index) % 2 == 1 and int(index) < 2 * len(targets)
                    resource = element.get('background', {}).get('image', {}).get('fixed', '')
                    if 'reefnet-topology.svg' in resource:
                        assert resource.endswith('?v=' + hashlib.sha256(asset.read_bytes()).hexdigest()[:12])
            for target in panel.get('targets', []):
                if 'increase(' in target.get('expr', ''):
                    assert '[$__range]' in target['expr'] and target.get('instant'), panel['title']
                if 'rate(' in target.get('expr', ''):
                    assert '[$__rate_interval]' in target['expr'] and panel['type'] == 'timeseries', panel['title']
            a = panel['gridPos']
            for other in d['panels'][i+1:]:
                b = other['gridPos']
                assert (a['x'] >= b['x']+b['w'] or b['x'] >= a['x']+a['w'] or
                        a['y'] >= b['y']+b['h'] or b['y'] >= a['y']+a['h']), (panel['title'], other['title'])
            for t in panel.get('targets', []):
                expr = t.get('expr', '')
                assert set(re.findall(r'\$([A-Za-z_]\w*)', expr)) <= variables, panel['title']
                if not args.live or not expr:
                    continue
                expr = expr.replace('$__range', '15m').replace('$__rate_interval', '20s')
                expr = re.sub(r'\$[A-Za-z_]\w*', '.*', expr)
                is_loki = panel.get('datasource', {}).get('uid') == 'loki'
                endpoint = 'http://localhost:3100/loki/api/v1/query_range' if is_loki else 'http://localhost:9090/api/v1/query'
                result = get(endpoint + '?' + urllib.parse.urlencode({'query': expr}))
                assert result['status'] == 'success', (panel['title'], result)
                if not is_loki:
                    assert result['data']['result'], 'No series: ' + panel['title']
                count += 1
        print(d['title'] + ': OK')
    if args.live:
        listed = get('http://localhost:3000/api/search?type=dash-db')
        owned = {d['uid'] for d in listed if d['uid'].startswith('reefnet-bob1-')}
        assert owned == uids, ('Obsolete or missing dashboards', owned ^ uids)
        print(f'{count} live panel queries passed')


if __name__ == '__main__':
    main()
