"""Native SVG teaching diagrams; no raster screenshots or external assets.

All numerical teaching examples are synthetic; case diagrams are qualitative.
"""
from pathlib import Path
from html import escape
R=Path(__file__).resolve().parents[1]/'assets/diagrams'
R.mkdir(parents=True,exist_ok=True)
G='#72bf44'; K='#303030'; M='#626262'; L='#e9e9e9'
DATA_ACCENTS={'paired-runs.svg'}
PRIMARY_SERIES={'dns-check-latencies.svg','sampling-phase.svg'}

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
 # Pad the marker viewport and end the shaft inside the triangle, before its tip.
 svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="{h}" viewBox="0 0 1100 {h}" role="img" aria-label="{escape(desc,quote=True)}"><title>{escape(desc)}</title><defs><marker id="arrow" viewBox="-1 -1 10 10" markerUnits="userSpaceOnUse" markerWidth="10" markerHeight="10" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#777"/></marker><marker id="arrow-grey" viewBox="-1 -1 10 10" markerUnits="userSpaceOnUse" markerWidth="10" markerHeight="10" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#777"/></marker></defs><g font-family="Arial, Liberation Sans, sans-serif">{body}</g></svg>'
 (R/name).write_text(svg)
def flow(name,labels,subs=None,caption='',height=235):
 n=len(labels); gap=56; w=(1060-gap*(n-1))/n; a=''
 for i,l in enumerate(labels):
  x=20+i*(w+gap); a+=box(x,38,w,104,l,subs[i] if subs else None,green=False)
  if i<n-1:a+=line(x+w+12,90,x+w+gap-12,90)
 if caption:a+=text(550,200,caption,24)
 save(name,a,height,caption or ' → '.join(labels))

flow('address-hierarchy.svg',['IANA','RIR','Network'],['Global pool','Regional registry','More-specific prefix'],caption='Administrative delegation, not a forwarding path')
flow('incident-loop.svg',['Reproduce','Bound + explain','Repair','Verify'],caption='Evidence before action. Recovery before closure.')
flow('prometheus-data-path.svg',['Exporter','Prometheus','Query','Grafana'],['Source freshness','Scrape + store','Select series','Interpret'],caption='A successful scrape can still return stale source data.')
flow('alert-path.svg',['Observation','Rule','Routing','Notification'],['Value + age','Pending / firing','Group / inhibit','Delivery result'],height=175)
flow('maintenance-gates.svg',['Precheck','Canary','Service check','Continue'],caption='Stop time + recovery owner apply at every gate.')
flow('evidence-chain.svg',['Question','Method','Evidence','Claim'],caption='The method determines which conclusions the evidence can support.')
flow('literature-argument.svg',['Find','Assess','Connect','Refine'],['Relevant studies','Claims + evidence','Agreement + limits','Research question'],height=175)
flow('experiment-run-cycle.svg',['Reset','Baseline','Inject','Observe','Restore'],caption='Run ID, seed, versions and raw results travel with the experiment.')
flow('research-record.svg',['Figure','Analysis','Run records','Raw evidence'],['Result + units','Versioned code','Setup + run ID','Data + versions'],caption='Follow one reported number all the way back.')

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

a=box(10,20,225,75,'SR Linux|counters')+box(335,20,225,75,'gNMIc')
a+=box(10,125,225,75,'Linux queues|diagnostics')+box(335,125,225,75,'Queue exporter')
a+=box(10,230,225,75,'Probes|Lagoon / Pacific')+box(335,230,225,75,'Probe exporter')
a+=box(660,20,225,285,'Prometheus')
a+=box(10,345,225,75,'SR Linux logs')+box(335,345,225,75,'Alloy')
a+=box(660,345,225,75,'Loki')+box(930,215,160,75,'Grafana',green=True)
for y in (57,162,267,382):
 a+=line(240,y,328,y)+line(565,y,653,y)
a+=line(890,162,1005,208)+line(890,382,1005,297)
a+=text(280,37,'gNMI',19)+text(280,142,'tc',19)+text(280,247,'probes',19)+text(280,362,'syslog',19)
save('reefnet-telemetry.svg',a,440)
flow('prefix-experiment.svg',['Fault injector','Fault','External probe'],['Known start and end','Affects one path','Independent outcome'],caption='Unaffected paths and address families serve as controls.')
flow('temporal-split.svg',['Train','Validate','Test'],['Fit parameters','Select settings','Evaluate once'],caption='Train on past data. Test on later data.')
a=box(10,65,290,85,'Observe old state')+box(405,65,290,85,'Move traffic')+box(800,65,290,85,'Observe old state')
a+=line(305,105,400,105)+line(700,105,795,105)+text(550,225,'Wait for fresh evidence before moving again.',28)
save('control-overcorrection.svg',a,265)
flow('mape-k.svg',['Monitor','Analyze','Plan','Execute'],['Telemetry','Forecast, compare','Controller or agent','Change + verify'],caption='Knowledge: intent, source of truth, documentation.')
flow('react-loop.svg',['Reason','Act','Observe'],['Choose the next step','Call a tool','Read the result'],caption='Repeat until the goal is reached or a limit stops the loop.')
# Reinforcement learning: the policy acts, the environment answers with state and reward.
a=box(60,80,330,110,'Agent','policy')+box(710,80,330,110,'Environment','the network')
a+=line(395,105,703,105)+text(550,90,'action',24)
a+=line(703,165,395,165)+text(550,200,'new state + reward',24)
a+=text(550,265,'Goal: the highest total reward over time.',24)
save('rl-loop.svg',a,285,'Reinforcement learning loop: the agent sends an action to the environment and receives a new state and a reward')
# Decision tree: each split asks one question, each leaf holds a prediction.
a=box(400,15,300,70,'Hour 8 to 18?')
a+=box(150,145,300,70,'Weekday?')+box(700,145,300,70,'Low','40 Mbit/s')
a+=box(20,275,280,70,'High','120 Mbit/s')+box(330,275,280,70,'Medium','80 Mbit/s')
a+=line(500,90,330,140)+line(600,90,820,140)+text(390,118,'yes',22)+text(730,118,'no',22)
a+=line(250,220,170,270)+line(350,220,450,270)+text(190,250,'yes',22)+text(430,250,'no',22)
a+=text(830,300,'Leaves hold the prediction.',23)+text(830,333,'Training chooses the questions.',23)
save('decision-tree.svg',a,360,'Illustrative decision tree predicting link load from hour and weekday')

# Overfitting: training error keeps falling, test error turns up again.
a=line(110,270,1000,270,False,color='#777')+line(110,270,110,30,False,color='#777')
a+=text(555,302,'Model complexity →',23)+text(120,25,'Error',23,'start')
a+=f'<path d="M130,80 C330,190 600,235 980,252" fill="none" stroke="#999" stroke-width="3" stroke-dasharray="8 6"/>'
a+=f'<path d="M130,60 C330,170 470,190 560,185 C700,175 850,115 980,65" fill="none" stroke="{K}" stroke-width="3"/>'
a+=text(985,232,'Training error',22,'end')+text(985,52,'Test error',22,'end')
a+=line(545,195,545,270,False,dash=True)
a+=text(200,335,'Underfit',22)+text(545,335,'Best on held-out data',22)+text(900,335,'Overfit',22)
save('overfitting.svg',a,350,'Training error falls with model complexity while test error first falls and then rises')
# The empirical cycle: two rows, the second row returns to the first.
a=''
for i,label in enumerate(['Observe','Question','Hypothesis','Prediction','Experiment','Analysis','Claim','Review']):
 x=30+(i%4)*275; y=20+(i//4)*155
 a+=text(x+10,y+28,f'{i+1:02}',22,'start',G,700)
 a+=text(x+110,y+65,label,29,weight=700)
 a+=line(x+10,y+85,x+210,y+85,False,color='#ccc')
 if i%4<3:a+=line(x+218,y+59,x+263,y+59)
a+=f'<path d="M1080,79 V145 H15 V214 H27" fill="none" stroke="#777" stroke-width="2" marker-end="url(#arrow-grey)"/>'
a+=text(550,319,'Review leads to new observations. A failed prediction is a result too.',24)
save('empirical-cycle.svg',a,345,'Empirical cycle: observe, question, hypothesis, prediction, experiment, analysis, claim, review')
flow('flow-prediction-pipeline.svg',['Capture','Anonymize','Enrich','Label','Train + test'],['Data center flows','Protect addresses','Add context','3 classes','On the stream'],caption='In a data-driven paper, the pipeline is part of the contribution.')
flow('agent-boundary.svg',['Planner','Enforced tool','Network','Verifier'],['Proposes action','Scope + permission','Actual state','Independent probe'],caption='Authorization stays outside the planner.')

# Research workshops: each output becomes the input to the next meeting.
a=''
for i,(date,label,output) in enumerate([
 ('30 Oct','Question','Research brief'),('13 Nov','Design','Study protocol'),
 ('27 Nov','Argument','Evidence + limits'),('11 Dec','Evaluate','Predictions + actions'),
 ('22 Jan','Review','Revised argument'),('5 Feb','Reproduce','Traceable result')]):
 x=25+(i%3)*365; y=10+(i//3)*155
 a+=text(x+155,y+25,date,22,color=M)
 a+=box(x,y+42,310,82,label,output)
 if i%3<2:a+=line(x+320,y+83,x+350,y+83)
a+='<path d="M1075,93 V150 H10 V248 H23" fill="none" stroke="#777" stroke-width="2" marker-end="url(#arrow-grey)"/>'
save('research-journey.svg',a,295,'Six workshops develop one project from research question to reproducible result')

# An explicit example of narrowing, with room to read each question.
a=''
for i,(label,content) in enumerate([
 ('Interest','Automated repair'),('Problem','A successful command can leave the service broken'),
 ('Question','Does independent verification reduce unsafe repairs?'),
 ('Scope','Same incidents, fixed tool access, recovery and side effects')]):
 y=20+i*72
 a+=text(25,y+27,label,24,'start',weight=700)
 a+=text(225,y+27,content,24,'start')
 if i<3:a+=line(190,y+39,190,y+69)
save('question-funnel.svg',a,310,'Narrow an interest through a problem and question to an explicit study scope')

flow('review-selection.svg',['Identify','Deduplicate','Screen','Include'],
 ['Search records','Link versions','Apply criteria','Chart or extract'],
 caption='Counts and reasons for exclusion make the selection traceable.')
flow('design-logic.svg',['Question','Construct','Measure','Inference'],
 ['What is unknown?','What does it mean?','What can we observe?','What follows?'],
 caption='State assumptions and alternative explanations at every step.')

# Synthetic factorial means: the treatment effect changes with workload.
a=line(150,250,790,250,False)+line(150,250,150,30,False)
a+=text(150,20,'Completion time (ms), lower is better',23,'start')
for value,y in [(0,250),(50,150),(100,50)]:
 a+=text(125,y+8,value,22,'end')+line(150,y,790,y,False,color='#ddd')
a+=line(230,150,690,50,False,color=K)+line(230,210,690,30,False,dash=True,color=M)
for x,y in [(230,150),(690,50)]:a+=f'<circle cx="{x}" cy="{y}" r="6" fill="{K}"/>'
for x,y in [(230,210),(690,30)]:a+=f'<rect x="{x-5}" y="{y-5}" width="10" height="10" fill="{M}"/>'
a+=text(230,285,'Light workload',24)+text(690,285,'Heavy workload',24)
a+=text(820,68,'Without A: 50 → 100',22,'start')+text(820,108,'With A: 20 → 110',22,'start')
a+=text(820,174,'Effect of A:',24,'start',weight=700)+text(820,211,'−30 ms → +10 ms',24,'start')
save('factor-interaction.svg',a,310,'Synthetic factorial example: component A reduces completion time under light load but increases it under heavy load')


# IPv6 path MTU: the router reports, only the sender adapts.
a=''
for x,l,sub in [(150,'Sender',''),(550,'Router','next link: MTU 1400'),(950,'Receiver','')]:
 a+=text(x,27,l,26,weight=700)+line(x,45,x,250,False,color='#999')
 if sub:a+=text(x,272,sub,21,color=M)
a+=line(158,85,542,85)+text(350,72,'1,500-byte packet',23)+text(575,92,'✕',26,'start',weight=700)
a+=line(542,150,158,150)+text(350,137,'Packet Too Big: MTU 1400',23)
a+=line(158,215,942,215)+text(550,202,'1,400-byte packets',23)
a+=text(550,315,'The router drops and reports. Only the sender makes packets smaller.',23)
save('pmtud-sequence.svg',a,335,'IPv6 path MTU discovery: router drops a 1500-byte packet, returns ICMPv6 Packet Too Big, sender resends with 1400 bytes')
flow('flow-export.svg',['Packets','Flow cache','Exporter','Collector'],['Read headers','One entry per flow key','Template + records','Decode + store'],caption='An entry leaves the cache when the flow ends or a timeout expires.')

# Probe loop and scrape run on separate clocks.
X=lambda t:180+t*170
a=text(20,87,'Probe results',24,'start')+text(20,192,'Scrapes',24,'start')
a+=f'<rect x="{X(3.3)}" y="66" width="{X(4.3)-X(3.3)}" height="28" fill="#eeeeee"/>'
a+=line(180,80,1040,80,False,color='#999')+line(180,185,1040,185,False,color='#999')
for r,s in [(.1,.5),(1.2,1.5),(2.3,2.5),(2.3,3.5),(4.3,4.5)]:
 a+=line(X(s),177,X(r),88,False,dash=True,color='#999')
for r in [.1,1.2,2.3]:a+=f'<circle cx="{X(r)}" cy="80" r="9" fill="{K}"/>'
a+=f'<circle cx="{X(4.3)}" cy="80" r="9" fill="#fff" stroke="{K}" stroke-width="3"/>'+text(X(4.3),55,'timeout',21)
for s in [.5,1.5,2.5,3.5,4.5]:a+=f'<rect x="{X(s)-8}" y="177" width="16" height="16" fill="{K}"/>'
for t in range(6):a+=text(X(t),232,f'{t} s',21)
a+=text(550,280,'Each scrape copies the newest result. Two scrapes can return the same one.',23)
save('scrape-clocks.svg',a,300,'Probe results and Prometheus scrapes on separate clocks; the scrapes at 2.5 s and 3.5 s return the same result')


print(f'{len(list(R.glob("*.svg")))} SVG diagrams written.')
