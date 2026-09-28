"""Course-native SVG visualizations, using the restored Fulda/neutral palette."""
from pathlib import Path
from html import escape
R=Path(__file__).resolve().parents[1]; A=R/'assets/diagrams'; A.mkdir(exist_ok=True)
G='#72bf44'; K='#303030'; M='#777'; L='#dedede'; W=1100
PRIMARY_SERIES={'traceroute-rtt','convergence-steps','counter-gauge','time-series-samples','stale-panel'}

def t(x,y,s,z=25,anchor='middle',weight=400,color=K):
 return f'<text x="{x}" y="{y}" font-size="{z}" text-anchor="{anchor}" font-weight="{weight}" fill="{color}">{escape(str(s))}</text>'
def ln(x,y,xx,yy,arrow=False,dash=False,color=None,width=None):
 if color is None: color=M
 if arrow:
  from math import hypot
  length=hypot(xx-x,yy-y)
  if length>45:
   dx,dy=(xx-x)/length*5,(yy-y)/length*5
   x,y,xx,yy=x+dx,y+dy,xx-dx,yy-dy
 if width is None: width=2
 marker='a' if color==G else 'a-grey'
 return f'<path d="M{x},{y} L{xx},{yy}" fill="none" stroke="{color}" stroke-width="{width}"'+(f' marker-end="url(#{marker})"' if arrow else '')+(' stroke-dasharray="7 6"' if dash else '')+'/>'
def rect(x,y,w,h,fill='#f6f6f6',stroke='#ccc',rx=5):
 return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>'
def circle(x,y,r,fill='white',stroke=M):
 return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
def card(x,y,w,h,label,sub='',accent=False):
 s=rect(x,y,w,h)
 s+=t(x+w/2,y+h/2-(16 if sub else 0),label,25,weight=700).replace('<text ', '<text dominant-baseline="central" ')
 if sub:s+=t(x+w/2,y+h/2+16,sub,22,color=M).replace('<text ', '<text dominant-baseline="central" ')
 return s
def save(name,s,h=300,desc=None):
 s=s.replace(G,K if name in PRIMARY_SERIES else M)
 (A/(name+'.svg')).write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="{h}" viewBox="0 0 1100 {h}" role="img" aria-label="{escape(desc or name,quote=True)}"><title>{escape(desc or name)}</title><defs><marker id="a" viewBox="0 0 10 10" refX="10" refY="5" markerUnits="userSpaceOnUse" markerWidth="10" markerHeight="10" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="{M}"/></marker><marker id="a-grey" viewBox="0 0 10 10" refX="10" refY="5" markerUnits="userSpaceOnUse" markerWidth="10" markerHeight="10" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="{M}"/></marker></defs><g font-family="Arial, Liberation Sans, sans-serif">{s}</g></svg>')
def pathflow(name,labels,subs=None,caption='',h=250):
 n=len(labels);w=(1060-56*(n-1))/n;s=''
 for i,label in enumerate(labels):
  x=20+i*(w+56);s+=card(x,45,w,105,label,subs[i] if subs else '',False)
  if i<n-1:s+=ln(x+w+12,97,x+w+44,97,True)
 if caption:s+=t(550,215,caption,24)
 save(name,s,h)
def device(x,y,label,kind='router',sub=''):
 if kind=='host':
  s=rect(x-48,y-34,96,62,'white',M)+ln(x,y+28,x,y+44)+ln(x-27,y+44,x+27,y+44)
 elif kind=='server':
  s=''
  for dy in [-30,-4,22]:s+=rect(x-44,y+dy,88,21,'#fafafa',M)+circle(x-30,y+dy+10,2,G,G)
 else:
  s=rect(x-47,y-32,94,64,'white',M,12)
  for dx,dy in [(-27,-15),(27,15),(-27,15),(27,-15)]:s+=ln(x,y,x+dx,y+dy,True,color=M)
 s+=t(x,y+83,label,25,weight=700)
 if sub:s+=t(x,y+111,sub,22,color=M)
 return s

# A restrained course map, not a code block.
s=ln(110,75,990,75,color='#ccc')
for i,(a,b) in enumerate(zip(['Understand','Operate','Automate','Observe'],['Healthy request','One incident','Safe repetition','Earlier evidence'])):
 x=120+i*285;s+=circle(x,75,26,'white',G)+t(x,84,i+1,24,weight=700)+t(x,141,a,28,weight=700)+t(x,177,b,23,color=M)
save('course-journey',s,220)
s=ln(135,104,348,104,True)+ln(451,104,663,104,True)+ln(769,104,971,104,True)
s+=device(85,105,'Client','host')+device(400,105,'Access')+device(716,105,'Transit')+device(1020,105,'Service','server')
s+=t(550,35,'One request crosses several independently operated links.',25)
save('request-network',s,260)
# Protocol layers and encapsulation encode containment instead of text arrows.
s=''
for i,(a,b) in enumerate([('Application','HTTP, DNS'),('Transport','TCP, UDP'),('Internet','IP, ICMP'),('Link','Ethernet'),('Physical','Copper, fiber, radio')]):
 y=10+i*57;s+=rect(140,y,820,49,'#f7f7f7')+ln(141,y+4,141,y+45,color=G,width=4)+t(165,y+32,a,25,'start',700)+t(925,y+32,b,23,'end')
save('protocol-stack',s,300)
s=card(20,70,270,95,'Resolver','Cached answer?')+card(430,20,245,80,'DNS hierarchy','Delegation')+card(800,70,280,95,'Authoritative DNS','A / AAAA records')
s+=ln(295,98,426,65,True)+ln(680,65,796,99,True)+ln(794,182,295,182,True)+t(550,219,'Reply: address records with a cache lifetime',26)+t(550,265,'An address is an answer about naming, not service health.',23)
save('dns-resolution',s,285)
for name,layers in [('dns-encapsulation',[('IP','Resolver address'),('UDP','Destination port 53'),('DNS','Question: data.oceanresearch.test A?')]),('ip-packet',[('IP','203.0.113.10 → 198.51.100.10'),('Transport','TCP or UDP header'),('Application','Request data')]),('ethernet-frame',[('Ethernet frame','Source and next-hop MAC'),('IP packet','Source and destination IP'),('Payload','Transport + application data')])]:
 s=''
 for i,(a,b) in enumerate(layers):
  x=30+i*50;y=20+i*80;w=1040-i*100;h=270-i*100
  cy=y+(40 if i<2 else h/2)
  s+=rect(x,y,w,h,'white' if i<2 else '#f7f7f7')
  s+=t(x+24,cy,a,25,'start',700).replace('<text ', '<text dominant-baseline="central" ')
  s+=t(x+w-24,cy,b,23,'end').replace('<text ', '<text dominant-baseline="central" ')
 save(name,s,305)
s=rect(5,25,650,200,'#fafafa')+t(325,55,'Local prefix: 203.0.113.0/25',24)
s+=device(100,116,'Host','host')+device(545,116,'Gateway')+device(970,116,'Remote service','server')
s+=ln(160,103,483,103,True)+t(325,94,'198.51.100.10 → gateway',22)+ln(602,103,914,103,True)
s+=circle(310,170,7,G,G)+ln(158,144,298,169,True)+t(313,209,'203.0.113.42: direct',22)
save('local-remote',s,260)
s=device(90,97,'Client','host','203.0.113.10')+device(485,97,'Next hop','router','203.0.113.1')+device(1000,97,'Destination','server','198.51.100.10')
s+=ln(145,94,430,94,True,color=G,width=3)+ln(540,94,944,94,True,dash=True)+t(286,64,'Local link',24)+t(740,64,'Remaining path',24)+t(550,274,'The packet keeps its final IP destination.',25)
save('next-hop',s,295)
s=rect(430,90,240,120,'white',M,10)+t(550,150,'Switch',29,weight=700).replace('<text ', '<text dominant-baseline="central" ')
for x,y,lab in [(80,150,'A'),(1010,75,'B'),(1010,250,'C')]:
 s+=device(x,y,lab,'host')
s+=ln(135,150,425,150,True,color=G,width=3)+ln(675,125,951,75,True,color=G,width=3)+ln(675,180,951,240,dash=True)
s+=t(550,55,'Learn source MAC → ingress port',26)+t(550,253,'Known destination B: forward on its port.',24)+t(550,292,'Unknown destination: flood eligible ports.',23,color=M)
save('switch-forwarding',s,370)
s=t(210,25,'Host',27,weight=700)+t(900,25,'Next hop',27,weight=700)+ln(210,44,210,240)+ln(900,44,900,240)
s+=ln(216,95,894,95,True)+t(555,77,'Who owns this next-hop IP?',25)+ln(894,185,216,185,True)+t(555,167,'This link-layer address',25)
s+=t(550,280,'ARP uses broadcast. ND uses multicast solicitation.',24)
save('neighbor-resolution',s,305)
s=''
for i,(a,b) in enumerate([('Link 1','Host MAC → router MAC'),('Link 2','Router MAC → next-hop MAC')]):
 x=20+i*570;s+=rect(x,30,510,210,'white')+t(x+255,71.5,a,27,weight=700)+t(x+255,116.5,b,22)+rect(x+20,139,470,72,'#f7f7f7')+t(x+255,169,'Same IP endpoints',24,weight=700)+t(x+255,198,'203.0.113.10 → 198.51.100.10',23)
s+=ln(534,140,582,140,True)+t(550,289,'Each router builds a new link-layer frame.',25)
save('hop-encapsulation',s,310)
s=''
for x,y,label,sub in [(160,160,'Customer AS','Own routing policy'),(550,75,'Transit AS','Connects networks'),(930,160,'Peer AS','Own routing policy')]:
 s+=f'<ellipse cx="{x}" cy="{y}" rx="145" ry="64" fill="#fafafa" stroke="#bbb" stroke-width="1.5"/>'+t(x,y-16,label,27,weight=700).replace('<text ', '<text dominant-baseline="central" ')+t(x,y+16,sub,22).replace('<text ', '<text dominant-baseline="central" ')
s+=ln(300,126,417,99,True)+ln(690,102,795,128,True)+ln(310,183,780,183,False,True)+t(550,218,'Policy defines the relationship.',23)+t(550,279,'An AS is an administrative boundary, not one router.',25)
save('as-domains',s,305)
s=''
for x,y,xx,yy,c in [(190,135,550,40,1),(550,40,915,135,1),(190,135,550,240,5),(550,240,915,135,2)]:
 s+=ln(x,y,xx,yy,color=G if c==1 else '#aaa',width=3 if c==1 else 2)+t((x+xx)/2,(y+yy)/2-12,c,24)
for x,y,l in [(190,135,'A'),(550,40,'B'),(915,135,'D'),(550,240,'C')]:s+=circle(x,y,30)+t(x,y+9,l,26,weight=700)
s+=t(550,302,'Example link costs: the shortest internal path costs 2.',24)
save('igp-costs',s,325)
pathflow('destination-demux',['IP address','Transport port','Socket','Application'],['This host','This service','Receive bytes','Produce response'],h=190)
s=t(165,27,'Client sends',25,weight=700)+t(580,27,'Router 1',25,weight=700)+t(955,27,'Router 2',25,weight=700)
for y,l,xx in [(90,'TTL 1',580),(205,'TTL 2',955)]:
 s+=t(25,y+7,l,24,'start')+ln(150,y,xx-12,y,True,color=G,width=3)+circle(xx,y,9,'white',G)+ln(xx-10,y+38,150,y+38,True,dash=True)+t((xx+150)/2,y+68,'ICMP Time Exceeded',23)
save('traceroute-ttl',s,300)
# Operational evidence and scope.
s=''
for y,lab,result in [(65,'Lagoon','IPv4 fails, IPv6 works'),(215,'Pacific','IPv4 and IPv6 work')]:
 s+=device(120,y,lab,'host')+ln(180,y,715,140,True,dash=y==65)+t(470,47 if y==65 else 266,result,24)
s+=device(775,140,'ReefNet')+ln(827,140,1002,140,True)+device(1052,140,'Service','server')
save('partial-reachability',s,345)
s=t(600,32,'IPv4',25,weight=700)+t(920,32,'IPv6',25,weight=700)
for y,lab,states in [(65,'Lagoon',['FAIL','PASS']),(175,'Pacific',['PASS','PASS'])]:
 s+=t(50,y+52,lab,29,'start',700)
 for x,state in zip([450,770],states):
  s+=rect(x,y,300,90,'#fafafa')+t(x+150,y+56,state,27,weight=700)
  s+=ln(x+20,y+76,x+280,y+76,color=G if state=='PASS' else '#777',dash=state=='FAIL',width=3)
save('incident-scope',s,285)
s=''
for i,(a,b) in enumerate([('Control plane','Routes learned and selected'),('Forwarding plane','Entries used to move packets'),('Service behavior','The customer gets a response')]):
 y=12+i*92;s+=rect(20,y,1060,76,'white')+ln(20,y+2,20,y+74,color=G,width=4)+t(48,y+47,a,27,'start',700)+t(1035,y+47,b,25,'end')
save('three-planes',s,290)
pathflow('hypothesis-chain',['Policy override','Export absent','Route absent','IPv4 probe fails'],caption='Predict the missing evidence before changing the router.')
s=ln(95,110,1020,110)
for x,a,b in [(100,'Report','Scope'),(330,'Reproduce','Observation'),(570,'Hypothesis','Prediction'),(790,'Repair','Diff'),(1010,'Verify','Service proof')]:
 s+=circle(x,110,9,'white',G)+t(x,72,a,24,weight=700)+t(x,157,b,22)
s+=t(550,239,'Record timestamps, actions and evidence at each boundary.',25)
save('recovery-record',s,270)
s=card(20,85,230,110,'Device','ReefNet Edge 01')+card(325,85,200,110,'Interface','ethernet-1/3')+card(605,85,210,110,'Circuit','Lagoon handoff')+card(890,85,190,110,'Provider','Lagoon Transit')
for x,xx in [(255,320),(530,600),(820,885)]:s+=ln(x,140,xx,140,True)
s+=t(550,38,'An inventory is a graph of relationships.',27)+t(550,258,'Join the intended circuit to the actual change target.',25)
save('inventory-relationships',s,290)
pathflow('validation-gates',['Syntax','Semantics','Policy'],['Can it be parsed?','Does it mean something?','Is that behavior allowed?'],caption='A valid configuration can still violate the change contract.')
# Contrast rollout scope here. The later timeout exercise handles per-device outcomes.
s=''
for y,label,active in [(35,'One at a time',[True,False,False,False]),(160,'All at once',[True,True,True,True])]:
 s+=t(25,y+44,label,27,'start',700)
 for i,is_active in enumerate(active):
  x=340+i*190
  s+=card(x,y,155,85,f'r{i+1}','Changing' if is_active else 'Waiting')
  s+=ln(x+14,y+97,x+141,y+97,dash=not is_active,width=3 if is_active else 2)
s+=t(550,310,'How many devices can this change affect before the next check?',25)
save('fleet-progress',s,340,'Serial versus concurrent rollout: one changing router versus four before verification')
for name,states in [('fleet-timeout',['Verified','Verified','Timed out','Waiting','Waiting'])]:
 n=len(states);gap=1080/n;s=''
 for i,state in enumerate(states):
  x=gap*(i+.5);s+=device(x,65,f'r{i+1}')+t(x,218,state,24,weight=700)+ln(x-65,235,x+65,235,color=G if state=='Verified' else M,dash=state!='Verified',width=3)
 s+=t(550,295,'Progress is per device. A timeout is not a rollback.',25)
 save(name,s,320)
s=ln(105,235,1040,235)+ln(105,235,105,30)+t(80,29,'Distance to intent',23,'start')+t(1030,279,'Change cycles',23,'end')
s+='<path d="M110,60 H315 V120 H530 V172 H735 V212 H935 V232 H1030" fill="none" stroke="#72bf44" stroke-width="3"/>'
s+=t(730,79,'Repeated correction',26)+t(730,115,'must approach the target.',25)
save('convergence-steps',s,300,'Qualitative convergence illustration, not measured data')
s=card(30,35,290,90,'Git','Reviewed desired state')+card(405,35,290,90,'Reconciler','Compare and act')+card(805,35,265,90,'Network','Observed state')
s+=ln(325,80,400,80,True)+ln(700,80,800,80,True)+f'<path d="M937,132 V214 H550 V132" fill="none" stroke="{M}" stroke-width="2" marker-end="url(#a-grey)"/>'+t(750,258,'Fresh evidence closes the loop.',25)
save('git-reconcile',s,290)
s=card(390,10,320,68,'interfaces')+card(390,125,320,70,'interface[name]')+ln(550,90,550,115,True)
for x,l,sub in [(20,'name','Key: string'),(390,'enabled','Boolean'),(760,'mtu','Unsigned integer')]:
 s+=card(x,260,320,78,l,sub)+ln(550,208,x+160,250,True)
save('yang-tree',s,365)
# RPC roles do not imply a sequence or four arrows into an anonymous box.
s=t(120,30,'Client',28,weight=700)+t(975,30,'gNMI target',28,weight=700)
s+=ln(120,50,120,320)+ln(975,50,975,320)
for y,label in [(90,'Capabilities: discover supported models'),(160,'Get: request a snapshot'),(230,'Set: submit a transaction')]:
 s+=ln(127,y,968,y,True)+t(550,y-12,label,25)
s+=ln(968,310,127,310,True,color=G,width=3)+t(550,294,'Subscribe: receive updates over time',25)
save('gnmi-operations',s,340,'Three request examples and the server-to-client update direction within a Subscribe RPC; replies omitted')
# Measurements: timelines and distinct geometry rather than mock terminals.
s=device(120,80,'Observer','host')+device(965,80,'Endpoint','server')+ln(180,60,905,60,True,color=G,width=3)+ln(905,110,180,110,True)+t(545,46,'Outbound path',24)+t(545,152,'Return path',24)+t(550,260,'RTT contains both paths and endpoint processing.',25)
save('rtt-paths',s,295)
s=ln(130,225,1030,225)+ln(130,225,130,35)+t(130,24,'Mbit/s',23,'start')+t(1030,282,'Time (s)',23,'end')
for value in [0,25,50]:
 y=225-value*3.5;s+=t(112,y+8,value,22,'end')
vals=[25,30,28,35,32,40,36,38]
for i,value in enumerate(vals):
 x=165+115*i;y=225-value*3.5
 if i:s+=ln(x-115,225-vals[i-1]*3.5,x,y,color=K,width=2)
 s+=circle(x,y,5,K,K)+t(x,252,i,22)
save('time-series-samples',s,300,'Illustrative inbound rate on edge01 ethernet-1/3, the Lagoon handoff')
s=''
for offset,label,ys in [(0,'Counter',[205,185,170,120,94,52]),(560,'Gauge',[145,70,110,42,180,110])]:
 s+=t(offset+260,28,label,28,weight=700)+ln(offset+45,240,offset+515,240)+ln(offset+45,240,offset+45,50)
 for i,y in enumerate(ys):
  x=offset+75+i*80
  if i:s+=ln(x-80,ys[i-1],x,y,color=G,width=3)
 s+=t(offset+270,281,'Bytes on edge01 / ethernet-1/3' if offset==0 else 'DNS-check duration from Lagoon',24)
save('counter-gauge',s,305,'Synthetic counter and gauge trajectories')
s=t(550,25,'Same event',25,weight=700)+ln(550,85,550,195,dash=True)
for y,label,time in [(85,'Probe clock','10:00:04'),(195,'Router clock','10:00:08')]:
 s+=t(10,y+8,label,25,'start')+ln(225,y,1040,y)+circle(550,y,8,G,G)+t(740,y-20,time,25)
s+=t(550,293,'Unsynchronized clocks distort the apparent event order.',25)
save('clock-offsets',s,320,'Illustrative clock readings for one event; the clocks disagree by four seconds')
# One illustrative response per hop; no unexplained repeated points.
s=t(20,25,'One illustrative reply per hop',24,'start',color=M)
for i,value in enumerate([2,100,14,18]):
 y=80+i*63;x=195+value*6.6
 s+=t(20,y+8,f'Hop {i+1}',26,'start')+ln(195,y,1010,y,color='#ddd')
 s+=circle(x,y,8,G,G)+t(x+22,y-14,f'{value} ms',25,'start',700)
for value in [0,20,40,60,80,100,120]:s+=t(195+value*6.6,319,str(value),21)
s+=t(1030,357,'Reply RTT (ms)',24,'end')
save('traceroute-rtt',s,380,'Illustrative traceroute replies: one reply per hop, RTT 2, 100, 14 and 18 milliseconds')
s=ln(85,80,1015,80)
for i,(a,b,c) in enumerate([('Snapshot','Initial state','Populate cache'),('Sync','Complete','Initial transfer'),('Update','Apply value','Keep timestamp'),('Delete','Remove','No longer exists')]):
 x=145+i*270
 s+=circle(x,80,9,'white',M)+t(x,43,a,25,weight=700)+card(x-115,135,230,95,b,c)
save('stream-state',s,265)
s=''
for i,(a,b,c) in enumerate([('0','Measured zero','Valid observation'),('—','No fresh sample','State unknown'),('Deleted','Object removed','Update the model')]):
 x=20+i*365;s+=rect(x,25,330,245,'white')+t(x+165,109.5,a,49,weight=700,color=K)+t(x+165,173.5,b,25,weight=700)+t(x+165,224.5,c,23,color=M)
save('zero-missing-deleted',s,295)
s=''
for i,(x,label,detail) in enumerate([(180,'sources','Lagoon / Pacific'),(550,'IP families','IPv4 / IPv6'),(920,'probe types','ICMP / DNS')]):
 s+=t(x,55,'2',43,weight=700)+t(x,94,label,25)+t(x,131,detail,23,color=M)
 if i<2:s+=t(x+185,76,'×',34,color=M)
s+=ln(85,159,1015,159,color='#ddd')+t(550,211,'8 series for one metric',36,weight=700)+t(550,259,'One target: data.oceanresearch.test',24)
save('cardinality-product',s,285,'ReefNet probe metric: two sources times two IP families times two probe types equals eight label combinations')
s=rect(20,20,1060,260,'white')+t(45,61,'Illustrative panel',23,'start',700)+t(1048,61,'Last source update: 20 min ago',23,'end')+ln(60,223,1020,223)+ln(60,223,60,88)
s+='<path d="M62,155 L185,151 L310,158 L430,149 L550,154" stroke="#72bf44" stroke-width="3" fill="none"/>'+ln(550,154,1018,154,False,True,color='#aaa')+circle(550,154,6,G,G)
s+=t(793,113,'No new observations',24)+t(800,254,'Now',22)
save('stale-panel',s,310,'Illustrative monitoring panel, not a Grafana screenshot')
# Show a quantitative bottleneck, not unrelated-width grey strips.
s=t(125,40,'Lagoon probe',27,weight=700)+t(550,40,'Lagoon handoff',27,weight=700)+t(975,40,'Ocean Research',27,weight=700)
s+=t(125,88,'60 Mbit/s',25)+t(550,88,'50 Mbit/s limit',25)+t(975,88,'≤ 50 Mbit/s',25)
s+=ln(45,141,405,141,color='#777',width=24)+ln(695,141,1060,141,color=G,width=20)
s+='<path d="M408,109 H695 V173 H408 Z" fill="white" stroke="#777" stroke-width="2"/>'
s+=ln(550,179,550,244,True)+t(550,279,'Excess: queue, drop or sender backpressure',25)
save('capacity-bottleneck',s,310,'Illustrative offered rate 60 Mbit/s across a 50 Mbit/s transit link; delivered rate cannot exceed the limit')
s=ln(125,135,1010,135)
for x,a,b in [(140,'10:14:01','Admin disable'),(420,'10:14:02','Oper down'),(700,'10:14:03','OSPF change'),(980,'10:14:04','System event')]:s+=circle(x,135,8,'white',G)+t(x,87,a,24,weight=700)+t(x,187,b,24)
s+=t(550,270,'One controlled link fault, several observations.',25)
save('correlated-events',s,300,'Illustrative event sequence for the BOB1 core-link fault')
s=''
for y,lab,status in [(35,'VPN / OOB','Connected'),(115,'Console server','Logged in'),(195,'Router console','Prompt visible'),(275,'Remote AAA','Timeout')]:
 s+=circle(70,y+17,11,'white',G if y<270 else M)+t(110,y+25,lab,25,'start',700)+t(1030,y+25,status,25,'end')
 if y<270:s+=ln(70,y+31,70,y+80)
save('console-dependencies',s,330)
s=card(20,110,230,100,'Affected cluster','Redundant paths')+card(850,110,230,100,'Rest of network','Still reachable')
s+=ln(255,128,845,128,width=3)+ln(255,190,845,190,width=3)+t(340,108,'Path 1',23)+t(340,231,'Path 2',23)
s+=rect(390,26,320,52,'white')+t(550,60,'Shared work order',23,weight=700)+ln(550,82,550,122,True)+ln(620,82,620,184,True)
save('shared-maintenance',s,285)
s=''
for x,title,subs in [(15,'Before',['1  permit site-local','2  reject remaining']),(595,'After',['1  reject remaining','2  permit site-local — not reached'])]:
 s+=t(x+240,35,title,29,weight=700)
 for i,sub in enumerate(subs):s+=rect(x+10,70+i*88,470,68,'#f7f7f7')+t(x+32,113+i*88,sub,23 if 'not reached' in sub else 27,'start',color=M if 'not reached' in sub else K)
s+=ln(505,150,573,150,True)+t(550,288,'First matching rule wins. Later permission cannot undo rejection.',24)
save('policy-order',s,315)
s=card(20,60,245,100,'ClickHouse query','Column metadata')
for i in range(4):s+=rect(360+i*9,90-i*10,175,100,'white')
s+=t(485,238,'Bot Management features',24)+ln(270,110,350,110,True)+ln(580,110,720,110,True)+rect(737,52,22,155,'#eee')+t(749,29,'200-feature limit',24)+card(815,60,265,100,'FL2 proxy','Panic → HTTP 5xx')
save('generated-file-limit',s,280)
s=ln(75,125,1025,125)
for x,a,b in [(85,'09:47','Fault'),(200,'09:48','Detected'),(765,'10:27','Trigger found'),(1010,'10:36','Recovery starts')]:s+=circle(x,125,8,'white',G)+t(x,82,a,25,weight=700)+t(x,177,b,23)
s+=t(275,240,'Detection: 1 min',25)+t(800,240,'Recovery begins after 49 min',25)
save('fastly-timeline',s,275,'Selected events from Fastly’s June 2021 report; schematic spacing')
s=device(130,102,'BGP router')+device(960,102,'BGP peer')+ln(185,90,905,90,True)+t(550,67,'BGP session',24)+card(385,220,330,75,'BMP collector','Observes exported BGP state')+ln(180,135,390,235,True,True)+t(325,175,'BMP feed',24)
save('bmp-observer',s,325)
s=f'<ellipse cx="550" cy="135" rx="245" ry="103" fill="#fafafa" stroke="#ccc" stroke-width="1.5"/>'+t(550,119,'Internet paths',29,weight=700).replace('<text ', '<text dominant-baseline="central" ')+t(550,151,'Partial visibility',24,color=M).replace('<text ', '<text dominant-baseline="central" ')
for x,y,l in [(105,65,'Atlas probe'),(980,65,'RIS collector'),(105,250,'Your lab'),(980,250,'Service probe')]:
 s+=circle(x,y,11,'white',G)+t(x,y-25,l,23)+ln(x+12 if x<550 else x-12,y,350 if x<550 else 750,115 if y<150 else 180,True)
save('public-vantage-points',s,295,'Schematic observation points, not a geographic map')
s=card(40,20,230,80,'IP hop A')+card(825,20,230,80,'IP hop B')+ln(275,60,820,60,True)+t(550,41,'Same observed IP adjacency',24)
s+=ln(165,115,165,230,False,True)+ln(940,115,940,230,False,True)+ln(170,160,936,160,color='#aaa',width=3)+f'<path d="M170,160 L320,228 H790 L936,160" fill="none" stroke="{G}" stroke-width="3"/>'+t(550,148,'Physical path before',23)+t(550,265,'Physical path after',23)
save('hidden-underlay',s,290)
s=''
for i,(label,times) in enumerate([('Every 5 s',list(range(0,60,5))),('Alternating 4 / 6 s',[x+d for x in range(0,60,10) for d in [0,4]])]):
 y=65+i*120;s+=t(5,y+7,label,25,'start')+ln(290,y,1070,y)+rect(290+4.5*12,y-23,60,46,'#e9e9e9','#e9e9e9',0)
 for tick in times:s+=circle(290+tick*12,y,5,G,G)
for tick in [0,10,20,30,40,50,60]:s+=t(290+tick*12,243,tick,21)
s+=t(550,295,'Twelve probes per minute. A five-second fault can fit between probes.',23)
save('sampling-budget',s,320,'Synthetic schedules; highlighted fault from 4.5 to 9.5 seconds')
pathflow('http-control',['Before','During','After'],['HTTP 200','HTTP 503','HTTP 200'],caption='Same routes and interfaces. Different endpoint behavior.')
s=''
for offset,title in [(0,'One run, many samples'),(560,'Several independent runs')]:
 s+=t(offset+265,30,title,26,weight=700)
 if offset==0:
  s+=rect(35,65,455,175,'white')
  for i in range(30):s+=circle(64+(i%10)*43,95+(i//10)*56,5,G,G)
 else:
  for i in range(4):
   x=600+(i%2)*245;y=65+(i//2)*105;s+=rect(x,y,205,78,'white')
   for j in range(6):s+=circle(x+25+j*30,y+39,5,G,G)
s+=t(550,294,'The unit of replication comes from the experimental design.',25)
save('independent-runs',s,320)
s=card(380,10,340,78,'Common fault')+card(20,185,330,85,'Router CPU rises')+card(750,185,330,85,'HTTP latency rises')
s+=ln(425,92,225,178,True)+ln(675,92,885,178,True)+ln(355,225,744,225,True,True)+t(550,208,'Or a direct effect?',23)+t(550,316,'A shared cause can create correlation without a direct causal link.',24)
save('causal-alternatives',s,340)
s=''
for y,n,l in [(38,20,'Tasks attempted'),(110,16,'Agent says “fixed”'),(182,12,'Service check passes'),(254,2,'Unrelated route changed')]:
 s+=t(5,y+28,l,24,'start')+rect(415,y,30*n,38,G if n==12 else '#ededed',G if n==12 else '#ededed',0)+t(435+30*n,y+28,n,25,'start',700)
save('benchmark-evidence',s,315,'Fictional benchmark; overlap between failures is not specified')
s=''
for i,(title,detail) in enumerate([('Receive','Paper + review sheet'),('Read','During the session'),('Write','By hand (DE / EN)'),('Return','To the instructor')]):
 x=25+i*277;s+=rect(x+52,20,145,158,'white','#aaa',2)
 for j,w in enumerate([100,100,75]):s+=ln(x+74,60+j*28,x+74+w,60+j*28,color='#ccc')
 if i==2:s+=ln(x+150,145,x+208,70,color=G,width=5)
 if i<3:s+=ln(x+220,100,x+264,100,True)
 s+=t(x+128,221,title,28,weight=700)+t(x+128,258,detail,22)
save('paper-review',s,285)
# Supplied forecast source is retained for reproducible regeneration.
source=R/'resources/source-graphics'
# Re-layout three supplied diagrams: uniform nodes, centered labels, clear arrow gaps.
s=''
for i,(label,sub) in enumerate([('Received','from customer'),('Import','check policy'),('Selected','check best path'),('Export','check export'),('Lagoon','check receipt')]):
 x=20+i*222;s+=card(x,20,170,90,label,sub)
 if i<4:s+=ln(x+182,65,x+210,65,True)
s+=card(409,200,280,85,'Forwarding entry','customer next hop')+ln(549,120,549,190,True)
save('bgp-route-stages',s,310,'Adapted supplied diagram: inspect received, imported, selected, exported and remotely received routes')
pathflow('citation-chain',['Source','Sentence','Citation'],['What was demonstrated?','What do you claim?','Where can I check it?'],h=180)
s=t(20,27,'SubscriptionList mode',25,'start')
for x,label,sub in [(20,'ONCE','one initial transfer'),(390,'POLL','client requests updates'),(760,'STREAM','continuing updates')]:
 s+=card(x,50,320,88,label,sub)
s+='<path d="M920,150 V165 H180" fill="none" stroke="#777" stroke-width="2"/>'
for x,label,sub in [(20,'SAMPLE','periodic values'),(390,'ON_CHANGE','value changes'),(760,'TARGET_DEFINED','target selects mode')]:
 s+=ln(x+160,165,x+160,197,True)+card(x,210,320,88,label,sub)
save('gnmi-subscription-modes',s,320,'Adapted supplied gNMI subscription mode tree: SAMPLE, ON_CHANGE and TARGET_DEFINED belong to STREAM')
print('Visual assets:',len(list(A.glob('*.svg'))))

# Router forwarding is a distinct progressive view, not a duplicate link diagram.
s=card(20,30,330,75,'Incoming frame','MAC A → MAC R-in')+rect(40,130,290,90,'white')+t(185,165,'IP packet',26,weight=700)+t(185,199,'TTL 64',25)
s+=device(550,120,'Router')+ln(355,120,491,120,True)+ln(608,120,744,120,True)
s+=card(750,30,330,75,'Outgoing frame','MAC R-out → MAC B')+rect(770,130,290,90,'white')+t(915,165,'Same IP endpoints',26,weight=700)+t(915,199,'TTL 63',25)
s+=t(550,292,'Rebuild the frame. Keep the IP destination. TTL values are illustrative.',24)
save('router-forwarding',s,315)

# The supplied forecast figure now has its data and producer alongside it.
# Preserve its actual plotted paths; enlarge labels and remove a redundant title.
from xml.etree import ElementTree as ET
ET.register_namespace('', 'http://www.w3.org/2000/svg')
plot=ET.parse(source/'forecast.svg').getroot()
for parent in plot.iter():
 for child in list(parent):
  if child.tag.endswith('text'):
   if (child.text or '').startswith(('Synthetic teaching data:', 'Shaded:', 'Mbit/s ·')):parent.remove(child)
   else:child.set('font-size','24')
plot.set('role','img');plot.set('aria-label','Synthetic observed traffic, persistence and ridge forecasts with a workload shift and excluded missing-data windows')
# Use line samples as a legend. Put units on axes, not in a prose key.
ns='{http://www.w3.org/2000/svg}'
group=plot.find(ns+'g')
for x,label,color,dash in [(80,'Observed','#303030',None),(360,'Last-value forecast','#999999','6 4'),(760,'Ridge forecast',G,None)]:
 attr={'d':f'M{x},415 h48','stroke':color,'stroke-width':'3','fill':'none'}
 if dash:attr['stroke-dasharray']=dash
 ET.SubElement(group,ns+'path',attr)
 node=ET.SubElement(group,ns+'text',{'x':str(x+60),'y':'423','font-size':'24'});node.text=label
node=ET.SubElement(group,ns+'text',{'x':'80','y':'52','font-size':'24'});node.text='Traffic (Mbit/s)'
(A/'forecast-comparison.svg').write_text(ET.tostring(plot,encoding='unicode'))
D=R/'assets/data';D.mkdir(exist_ok=True)
# Supplied forecast data are maintained directly in assets/data/.

# Google B4: conceptual control path, not a packet path or measured topology.
pathflow('b4-traffic-engineering', ['Applications', 'SDN controller', 'Network edges'],
         ['Demand + priority', 'Allocate paths', 'Enforce rates'],
         'Capacity is allocated across paths as demand and failures change.', h=240)

# A short burst inside a counter interval can overflow a finite output queue.
s=t(95,28,'Offered traffic (Mbit/s)',23,'start')
x0,x1,y0,y1=95,805,237,57
Y=lambda rate:y0-rate/80*(y0-y1)
for rate in [0,25,50,75]:
 y=Y(rate);s+=ln(x0,y,x1,y,color=L,width=1)+t(77,y+7,rate,22,'end')
s+=ln(x0,y1,x0,y0,color=M)+ln(x0,y0,x1,y0,color=M)
# 45 Mbit/s baseline, a 200 ms burst at 75 Mbit/s, 50 Mbit/s service.
left,right=443,457.2
s+=rect(left,Y(75),right-left,Y(50)-Y(75),'#dedede','none',0)
s+=ln(x0,Y(50),x1,Y(50),dash=True,color=M,width=2)
s+=t(595,Y(50)-13,'Capacity: 50 Mbit/s',22)
s+=f'<path d="M95,{Y(45)} H{left} V{Y(75)} H{right} V{Y(45)} H805" fill="none" stroke="{K}" stroke-width="3"/>'
s+=t(510,61,'200 ms burst: 75 Mbit/s',23,'start',700)
s+=ln(495,65,465,Y(75)+3,color=M)
for x,lab in [(95,'0'),(450,'5'),(805,'10 s')]:s+=t(x,268,lab,22)
s+=t(960,78,'Dashboard',25,weight=700)+t(960,130,'≈90%',42,weight=700)
s+=t(960,170,'mean output',23)+t(960,201,'over 10 s',23)
s+=t(550,307,'Synthetic Lagoon example. The brief peak is lost in the average.',23)
save('capacity-hidden-demand',s,325,'A 200 ms burst of 75 Mbit/s exceeds Lagoon capacity of 50 Mbit/s inside a 10 second counter interval. Mean output stays about 90 percent. With a small finite queue, the burst causes drops.')
