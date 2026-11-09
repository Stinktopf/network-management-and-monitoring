"""Deterministic timing model used in the research slides (no network I/O)."""
import csv, statistics
from pathlib import Path

rows=[]
for name,probes in [('every_5s',list(range(0,60,5))),
                    ('alternating_4_6',[x+d for x in range(0,60,10) for d in (0,4)])]:
    for i in range(120):
        onset=i*.5+.25  # Midpoints avoid coincidence with probe/fault boundaries.
        delays=[(p-onset)%60 for p in probes if (p-onset)%60<5]
        rows.append(dict(method=name,phase=i,onset=onset,detected=bool(delays),
                         delay=min(delays) if delays else ''))
    subset=[r for r in rows if r['method']==name]
    found=[r['delay'] for r in subset if r['detected']]
    print(name, 'detected',len(found),'missed',120-len(found),'median',statistics.median(found))
out=Path(__file__).resolve().parents[1]/'assets/data/sampling-runs.csv'
with out.open('w') as f:
    w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
print(out)
