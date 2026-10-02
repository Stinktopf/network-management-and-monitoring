"""Native SVG teaching diagrams; no raster screenshots or external assets.

All numerical teaching examples are synthetic; case diagrams are qualitative.
"""
from pathlib import Path
from html import escape
R=Path(__file__).resolve().parents[1]/'assets/diagrams'
R.mkdir(parents=True,exist_ok=True)
G='#72bf44'; K='#303030'; M='#626262'; L='#e9e9e9'
DATA_ACCENTS={'paired-runs.svg'}
PRIMARY_SERIES={'collector-backlog.svg','dns-check-latencies.svg','retention-resolution.svg','sampling-phase.svg'}

def text(x,y,s,size=25,anchor='middle',color=K,weight=400):
 return f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" fill="{color}" font-weight="{weight}">{escape(str(s))}</text>'
def line(x,y,xx,yy,arrow=True,dash=False,color=None):
 if color is None: color='#777' if arrow else '#999'
 if arrow:
  from math import hypot
  length=hypot(xx-x,yy-y)
  if length>45:
   dx,dy=(xx-x)/length*5,(yy-y)/length*5
   x,y,xx,yy=x+dx,y+dy,xx-dx,yy-dy
 marker='arrow' if color==G else 'arrow-grey'
 return f'<path d="M{x},{y} L{xx},{yy}" fill="none" stroke="{color}" stroke-width="2"'+(f' marker-end="url(#{marker})"' if arrow else '')+(' stroke-dasharray="8 6"' if dash else '')+'/>'
def box(x,y,w,h,label,sub=None,green=False):
 a=f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="#f6f6f6" stroke="#c9c9c9" stroke-width="1.5"/>'
 # Center the complete label group, including subtitles, within its box.
 ls=label.split('|'); count=len(ls)+(1 if sub else 0)
 base=y+h/2-(count-1)*16
 for n,l in enumerate(ls):
  a+=text(x+w/2,base+32*n,l,25,weight=700).replace('<text ', '<text dominant-baseline="central" ')
 if sub:
  a+=text(x+w/2,base+32*len(ls),sub,22,color=M).replace('<text ', '<text dominant-baseline="central" ')
 return a
def save(name,body,h=290,desc='Explanatory course diagram'):
 if name in PRIMARY_SERIES: body=body.replace(G,K)
 elif name not in DATA_ACCENTS: body=body.replace(G,'#777')
 svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="{h}" viewBox="0 0 1100 {h}" role="img" aria-label="{escape(desc,quote=True)}"><title>{escape(desc)}</title><defs><marker id="arrow" viewBox="0 0 8 8" markerUnits="userSpaceOnUse" markerWidth="10" markerHeight="10" refX="8" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8" fill="#777"/></marker><marker id="arrow-grey" viewBox="0 0 8 8" markerUnits="userSpaceOnUse" markerWidth="10" markerHeight="10" refX="8" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8" fill="#777"/></marker></defs><g font-family="Arial, Liberation Sans, sans-serif">{body}</g></svg>'
 (R/name).write_text(svg)
def flow(name,labels,subs=None,caption='',height=235):
 n=len(labels); gap=56; w=(1060-gap*(n-1))/n; a=''
 for i,l in enumerate(labels):
  x=20+i*(w+gap); a+=box(x,38,w,104,l,subs[i] if subs else None,green=False)
  if i<n-1:a+=line(x+w+12,90,x+w+gap-12,90)
 if caption:a+=text(550,200,caption,24)
 save(name,a,height,caption or ' → '.join(labels))

flow('environment-create.svg',['Topology file','Containerlab','Devices + links'],caption='Creation is not verification.')
flow('observation-path.svg',['Collect','Store','Query','Grafana'],caption='A panel is the end of an observation pipeline.')
flow('address-hierarchy.svg',['IANA','RIR','Network'],['Global pool','Regional registry','More-specific prefix'],caption='Administrative delegation, not a forwarding path')
flow('incident-loop.svg',['Reproduce','Bound + explain','Repair','Verify'],caption='Evidence before action. Recovery before closure.')
flow('monitor-loop.svg',['Collect','Store','Query','Visualize','Alert','Respond'],height=175)
flow('prometheus-data-path.svg',['Exporter','Prometheus','Query','Grafana'],['Source freshness','Scrape + store','Select series','Interpret'],caption='A successful scrape can still return stale source data.')
flow('alert-path.svg',['Observation','Rule','Routing','Notification'],['Value + age','Pending / firing','Group / inhibit','Delivery result'],height=175)
flow('artifact-promotion-flow.svg',['Code + input','Tested artifact','Review','Deploy'],caption='Deploy the reviewed artifact without regenerating it.')
flow('maintenance-gates.svg',['Precheck','Canary','Service check','Continue'],caption='Stop time + recovery owner apply at every gate.')
flow('test-layers.svg',['Model','Emulate','Integrate','Postcheck'],['Static properties','NOS behavior','API semantics','Live service'],caption='Different tests expose different failure classes.')
flow('evidence-chain.svg',['Question','Method','Evidence','Claim'],caption='The claim cannot be stronger than its weakest evidence boundary.')
flow('experiment-run-cycle.svg',['Reset','Baseline','Inject','Observe','Restore'],caption='Run ID, seed, versions and raw results travel with the experiment.')
flow('research-record.svg',['Figure','Analysis','Run records','Raw evidence'],['Result + units','Versioned code','Setup + run ID','Data + versions'],caption='Follow one reported number all the way back.')
flow('retry-cascade.svg',['Task restarts','Spanner overload','Slower recovery'],caption='Missing randomized exponential backoff amplified the restart load.')
flow('google-policy-failure.svg',['Policy data','Global replication','Service Control'],['Blank fields','Wide blast radius','Crash loop'],caption='A null pointer crashed the API policy-checking process.')
flow('interdomain-service-path.svg',['Client AS','Transit AS','Service AS'],caption='Each observer sees only part of this path.')

# Eight stages, with a readable row transition and no crossing connector.
a=''
for i,label in enumerate(['Intent','Observe','Compare','Plan','Validate','Change','Verify','Record']):
 x=30+(i%4)*275; y=20+(i//4)*155
 a+=text(x+10,y+28,f'{i+1:02}',22,'start',G,700)
 a+=text(x+110,y+65,label,29,weight=700)
 a+=line(x+10,y+85,x+210,y+85,False,color='#ccc')
 if i%4<3:a+=line(x+218,y+59,x+263,y+59)
a+=f'<path d="M1080,79 V145 H15 V214 H27" fill="none" stroke="#777" stroke-width="2" marker-end="url(#arrow-grey)"/>'
a+=text(550,319,'Failed verification: record actual state, back out, verify again.',24)
save('change-loop.svg',a,345)

# Progressive topology. core-a/core-b are links, never invented devices.
a=box(20,50,205,78,'Lagoon Transit','AS65100')+box(340,50,180,78,'ReefNet E1','AS65000',True)+box(650,50,180,78,'ReefNet E2','AS65000',True)+box(880,50,205,78,'Pacific Transit','AS65200')
a+=line(230,88,333,88,False)+line(835,88,875,88,False)
a+=line(526,76,644,76,False)+line(526,106,644,106,False)
a+=text(585,35,'core-a / core-b',22)
a+=box(300,210,260,70,'Ocean Research','AS65010')+line(430,131,430,204,False)+box(700,210,380,70,'data.oceanresearch.test')+line(565,245,695,245,False)
save('reefnet-overview.svg',a,310,'BOB1: two ReefNet routers, two core links, two upstreams, one customer')

# Request and response: separate routing decisions.
a=box(20,85,220,80,'Client')+box(440,85,220,80,'Network')+box(860,85,220,80,'Service')
a+=line(245,105,432,105)+line(666,105,854,105)+text(550,55,'REQUEST →',25,weight=700)
a+=line(854,150,666,150)+line(432,150,245,150)+text(550,223,'← RESPONSE: independent route lookup',25)
save('response-path.svg',a,255)

# Sequence diagram, distinct from pipeline diagrams.
def sequence(name,events,caption):
 a=text(240,27,'Client',26,weight=700)+text(860,27,'Target',26,weight=700)
 a+=line(240,45,240,245,False,color='#999')+line(860,45,860,245,False,color='#999')
 for i,(label,direction) in enumerate(events):
  y=75+i*62; x,xx=(248,852) if direction=='>' else (852,248)
  a+=line(x,y,xx,y,dash=direction=='x')+text(550,y-12,label,23)
 a+=text(550,283,caption,23)
 save(name,a,305)
sequence('tcp-handshake.svg',[('SYN','>'),('SYN + ACK','<'),('ACK','>')],'TCP setup precedes the application response.')
a=text(200,25,'Client',26,weight=700)+text(850,25,'Target',26,weight=700)
a+=line(200,40,200,235,False,color='#999')+line(850,40,850,235,False,color='#999')
a+=line(208,75,842,75)+text(500,62,'Write request',24)
a+=box(735,105,260,55,'State changed',green=True)
a+=line(842,190,430,190,dash=True)+text(580,177,'Reply lost',24)+text(260,222,'Timeout',24)
a+=text(550,282,'Unknown outcome ≠ no change. Read before retrying.',24)
save('write-timeout.svg',a,305)
a=text(120,25,'Writer A',24,weight=700)+text(600,25,'State owner',24,weight=700)+text(995,25,'Writer B',24,weight=700)
for x in [120,600,995]:a+=line(x,45,x,245,False,color='#999')
a+=line(592,78,128,78)+text(350,65,'Read: version 7',22)
a+=line(987,135,608,135)+text(810,123,'Update → version 8',22)
a+=line(128,195,592,195)+text(350,180,'Write if version = 7',22)+text(790,210,'Rejected: stale version',22)
a+=text(550,282,'Check and write must be atomic at the state owner.',24)
save('lost-update-sequence.svg',a,305)

# Branches: retained state and independent verification.
def branch(name,root,left,right,caption):
 a=box(380,15,340,70,root,green=True)+box(80,160,380,76,left)+box(640,160,380,76,right)
 a+=line(460,90,270,152)+line(640,90,830,152)+text(550,281,caption,23)
 save(name,a,307)
branch('confirmed-commit-branches.svg','Confirmed commit','Confirm before deadline','No confirmation: revert','Verify service before confirming. Requires target support.')
branch('backout-branch.svg','Service verification','Pass: record + hand over','Fail: backout + verify','Rollback: configuration. Backout: recovery procedure.')
branch('site-recovery.svg','Site unavailable','Both copies unreachable','Off-site recovery: test access','Copies do not remove a shared failure domain.')

a=box(25,75,230,85,'OOB access')+box(420,75,245,85,'Console server')+box(835,75,235,85,'Router console')
a+=line(260,115,413,115)+line(670,115,828,115)+text(335,88,'IP',22)+text(750,88,'serial',22)
a+=text(550,220,'Power, emergency authentication and reachable credentials still matter.',24)
save('oob-console-path.svg',a,250)
a=box(60,60,300,85,'Backbone routing')+box(735,60,300,85,'DNS / tools')
a+=line(365,80,728,80)+text(550,59,'reachability',23)+line(728,125,365,125)+text(550,169,'recovery depends on names',23)
a+=text(550,245,'Break the loop before the outage.',27,weight=700)
save('facebook-dns-dependencies.svg',a,275)

# Timelines and measurement semantics.
flow('telemetry-timestamps.svg',['Device event','Collector','Storage','Rule'],['t_event','t_receive','t_ingest','t_evaluate'],caption='Clock offset and transport delay are different quantities.')
a=''
for y,label,times in [(80,'Schedule A',[0,10,20]),(185,'Schedule B',[8,18,28])]:
 a+=text(20,y+7,label,25,'start')+line(225,y,980,y,False,color='#999')
 a+=f'<rect x="384" y="{y-24}" width="96" height="48" fill="#eeeeee"/>'
 for t in times:a+=f'<circle cx="{240+t*24}" cy="{y}" r="8" fill="{G}"/>'
 a+=text(1060,y+8,'miss' if label.endswith('A') else 'hit',22,'end')
a+=text(520,29,'Lagoon IPv4 outage: 6–10 s',22)
for t in [0,10,20,30]:a+=text(240+t*24,225,f'{t} s',22)
a+=text(550,269,'Same 10 s interval. Different onset phase.',25)
save('sampling-phase.svg',a,285,'Synthetic four-second outage missed or detected depending on sample phase')
a=line(75,125,1030,125,False,color='#777')
for x,l,sub in [(100,'Fault','t0'),(350,'Detected','t1'),(590,'Acknowledged','t2'),(980,'Service restored','t3')]:
 a+=line(x,95,x,150,False)+text(x,73,l,23)+text(x,187,sub,24,weight=700)
a+=text(310,242,'Detection: t1 − t0',24)+text(800,242,'Recovery: t3 − t0',24)
save('incident-intervals.svg',a,275)
a=box(20,45,275,80,'Synchronized state',green=True)+box(410,45,280,80,'Connection gap')+box(805,45,275,80,'Fresh snapshot',green=True)
a+=line(300,85,405,85,dash=True)+line(695,85,800,85,dash=True)+text(550,193,'Events during the gap may be irretrievable.',27)
save('gnmi-reconnect-gap.svg',a,225)
# Queue growth uses a scale instead of three boxes with numbers.
a=line(180,220,1020,220,False)+line(180,220,180,25,False)
a+=text(180,22,'Queued samples',23,'start')
a+=line(180,40,1020,40,False,dash=True,color='#aaa')
a+=text(162,48,'80',22,'end')+text(162,227,'0',22,'end')
a+=line(180,220,990,40,False,color=G)+text(1020,285,'Time (s)',23,'end')
for x,v in [(180,0),(585,5),(990,10)]:a+=text(x,249,v,22)
a+=text(210,83,'Net growth: 8 samples/s',25,'start')
a+=text(1020,202,'24 samples/s in, 16/s out',24,'end')
save('collector-backlog.svg',a,310,'Hypothetical ReefNet archive: empty 80-sample buffer, 24 samples/s in, 16/s out, full after 10 seconds')

# Aggregation is a loss of temporal detail, shown on the same time axis.
a=''
values=[0,0,1,0,0,0,0,0,0,0,0,0]
for row,label in enumerate(['Raw samples','4-s means','12-s mean']):
 y=50+row*95;a+=text(15,y+15,label,24,'start')+line(280,y+45,1050,y+45,False,color='#ccc')
 if row==0:
  for i,v in enumerate(values):
   x=310+i*63;a+=f'<circle cx="{x}" cy="{y+35-v*45}" r="5" fill="{G}"/>'
 elif row==1:
  for i,v in enumerate([.25,0,0]):a+=line(287+i*252,y+35-v*45,529+i*252,y+35-v*45,False,color=G)
 else:a+=line(287,y+35-45/12,1033,y+35-45/12,False,color=G)
a+=text(1030,333,'Same scales. Twelve seconds per row.',23,'end')
save('retention-resolution.svg',a,350,'Synthetic spike averaged over progressively wider windows; all rows share the same vertical and temporal scale')
a=line(100,190,1000,190,False)+line(100,190,100,35,False)
a+=line(100,80,460,80,False,color=G)+line(460,80,1000,80,False,dash=True,color='#999')
for x in [100,220,340,460]:a+=f'<circle cx="{x}" cy="80" r="7" fill="{K}"/>'
a+=text(460,224,'10 s: collector stops',22)+text(800,128,'No new evidence',27)+text(800,161,'Do not draw this as healthy.',22)
save('missing-samples-display.svg',a,255)

# Synthetic quantitative visuals with explicit axes and denominators.
# Individual checks in sequence. The x-axis is check index, not elapsed time.
a=text(115,25,'DNS response time (ms)',23,'start')
for value in [0,250,500]:
 y=260-value*.38
 a+=line(115,y,1040,y,False,color='#ddd')+text(98,y+7,value,21,'end')
a+=line(115,260,1040,260,False)+line(115,260,115,50,False)
for value in [1,25,50,75,100]:
 x=130+(value-1)*9
 a+=line(x,260,x,267,False)+text(x,291,value,21)
mean_y=260-44*.38
a+=line(115,mean_y,1040,mean_y,False,dash=True,color='#777')
for index in range(1,101):
 value=500 if index in {12,37,56,78,94} else 20
 x=130+(index-1)*9;y=260-value*.38
 a+=f'<circle cx="{x}" cy="{y}" r="{5 if value==500 else 3}" fill="{K}"/>'
a+=text(555,111,'5 checks: 500 ms',25)
a+=text(555,145,'95 checks: 20 ms',25)
a+=text(570,215,'Mean: 44 ms',24)
a+=line(570,223,570,mean_y-4,False,color='#777')
a+=text(1040,333,'DNS check number',23,'end')
save('dns-check-latencies.svg',a,350,'Synthetic sequence of 100 DNS checks: 95 at 20 ms and 5 at 500 ms. Check number on the horizontal axis, response time in milliseconds on the vertical axis, mean 44 ms.')
a=text(470,30,'Fault',25,weight=700)+text(785,30,'No fault',25,weight=700)+text(10,102,'Alert',25,'start')+text(10,213,'No alert',25,'start')
for x,y,l,g in [(320,50,'90 true positives',True),(635,50,'99 false positives',False),(320,160,'10 false negatives',False),(635,160,'801 true negatives',True)]:a+=box(x,y,295,85,l,green=g)
save('alert-confusion-matrix.svg',a,270,'Synthetic 1000 cases: precision 90/189, recall 90/100')
# Paired observations: use actual symbols in the legend, not shape names.
a=f'<circle cx="335" cy="24" r="8" fill="{G}"/>'+text(358,32,'Method A',24,'start')
a+=f'<rect x="613" y="16" width="16" height="16" fill="{K}"/>'+text(645,32,'Method B',24,'start')
for v in [0,20,40,60]:
 x=150+v*14;a+=line(x,60,x,260,False,color='#e5e5e5')+text(x,291,v,22)
for i,(aa,bb) in enumerate(zip([11,12,10,13,54],[17,18,16,17,18])):
 y=78+i*41;a+=text(15,y+8,f'Pair {i+1}',24,'start')+line(150+aa*14,y,150+bb*14,y,False,color='#999')
 a+=f'<circle cx="{150+aa*14}" cy="{y}" r="8" fill="{G}"/>'
 a+=f'<rect x="{150+bb*14-7}" y="{y-7}" width="14" height="14" fill="{K}"/>'
a+=text(1020,328,'Detection delay (ms)',24,'end')
save('paired-runs.svg',a,345,'Five synthetic paired runs: A is faster four times; its slow fifth run reverses the mean')
a=box(35,35,470,100,'Method A: 18 of 20 detected','Median among detections: 1.0 s',True)+box(595,35,470,100,'Method B: 4 of 20 detected','Median among detections: 0.5 s')
a+=text(550,180,'Synthetic example',22)
save('detection-coverage-delay.svg',a,205)

# Qualitative Internet evidence: no fabricated data or geographic attribution.
a=box(25,30,300,80,'Before event')+box(775,30,300,80,'After event')
a+=line(330,70,770,70)+text(550,49,'Compare matched paths',23)
a+=box(150,160,800,75,'Traceroute-derived paths ≠ traffic shares',green=True)
save('baltic-path-changes.svg',a,270,'Qualitative reading guide for RIPE Labs Baltic cable-cut analysis; no reproduced counts')
flow('cable-evidence.svg',['Physical reports','Route observations','RTT / reachability'],caption='Triangulate evidence. An IP path cannot identify a damaged cable.')
a=box(15,70,240,80,'1500-byte packet')+box(430,70,240,80,'MTU 1280')+box(840,70,245,80,'Client waits')
a+=line(260,108,423,108)+line(675,108,833,108,dash=True,color="#999")+text(550,41,'IPv6: oversized packet is dropped',24)
a+='<path d="M550,160 V198 H300" fill="none" stroke="#777" stroke-width="2" marker-end="url(#arrow-grey)"/>'
a+=line(261,189,279,207,False,color=K)+line(261,207,279,189,False,color=K)
a+=text(550,243,'ICMPv6 Packet Too Big is blocked. The sender cannot learn the limit.',23)
save('path-mtu.svg',a,275)

a=box(10,20,225,75,'SR Linux|counters')+box(335,20,225,75,'gNMIc')
a+=box(10,130,225,75,'Linux queues')+box(335,130,225,75,'Queue exporter')
a+=box(660,20,225,185,'Prometheus')
a+=box(10,260,225,75,'SR Linux logs')+box(335,260,225,75,'Alloy')
a+=box(660,260,225,75,'Loki')+box(930,155,160,75,'Grafana',green=True)
for y in (57,167,297):
 a+=line(240,y,328,y)+line(565,y,653,y)
a+=line(890,112,1005,148)+line(890,297,1005,237)
a+=text(280,37,'gNMI',19)+text(280,147,'tc',19)+text(280,277,'syslog',19)
save('reefnet-telemetry.svg',a,355)
flow('prefix-experiment.svg',['Controller','IPv4 export fault','External probe'],['Known fault window','Lagoon only','Independent outcome'],caption='Pacific and IPv6 remain control observations.')
flow('temporal-split.svg',['Train','Validate','Test'],['Fit parameters','Select settings','Evaluate once'],caption='Train on past data. Test on later data.')
a=box(10,65,290,85,'Observe old state')+box(405,65,290,85,'Move traffic')+box(800,65,290,85,'Observe old state')
a+=line(305,105,400,105)+line(700,105,795,105)+text(550,225,'Wait for fresh evidence before moving again.',28)
save('control-overcorrection.svg',a,265)
flow('agent-boundary.svg',['Planner','Enforced tool','Network','Verifier'],['Proposes action','Scope + permission','Actual state','Independent probe'],caption='Authorization stays outside the planner.')


flow('fastly-trigger.svg',['May 12 release','June 8 change','Network errors'],['Latent software bug','Valid customer input','85% of the network'],caption='The input was valid. The software was not prepared for it.')

print(f'{len(list(R.glob("*.svg")))} SVG diagrams written.')
