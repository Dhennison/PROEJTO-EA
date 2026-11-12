"""Price-only scenario engine. No queue/fills; no Work outcomes used as inputs."""
from decimal import Decimal as D,localcontext,ROUND_FLOOR,ROUND_CEILING
from bisect import bisect_left
from datetime import datetime,timezone
NAMES=('S38.2','S50','S61.8','R38.2','R61.8')
DISTANCES=(375,375,650,375,450)
def calendar(ms):return datetime.fromtimestamp(ms//1000,timezone.utc).strftime('%Y.%m.%d %H:%M:%S')+f'.{ms%1000:03d}'
def epoch(s):return int(datetime.strptime(s,'%Y.%m.%d %H:%M:%S').replace(tzinfo=timezone.utc).timestamp())*1000
def round5(x):return (x/5+D('.5')).to_integral_value(rounding=ROUND_FLOOR)*5
def levels(ref):
 with localcontext() as ctx:
  ctx.prec=40
  o,h,l,c,adj=map(D,(ref['open'],ref['high_prev'],ref['low_prev'],ref['close_prev'],ref['adjustment']))
  pp=(h+l+c)/3;r200=o+2*abs(l-pp);s200=o-2*abs(h-pp)
  r={p:adj+(r200-adj)*D(p) for p in ('0.236','0.382','0.5','0.618')}
  s={p:adj+(s200-adj)*D(p) for p in ('0.236','0.382','0.5','0.618')}
  ens=(s['0.382'],s['0.5'],s['0.618'],r['0.382'],r['0.618'])
  tps=((s['0.382']+s['0.236'])/2,s['0.382'],s['0.5'],r['0.236'],(r['0.618']+r['0.5'])/2)
  out=[]
  for i,(en,tp) in enumerate(zip(ens,tps)):
   buy=i<3;sl=en-D(DISTANCES[i]) if buy else en+D(DISTANCES[i]);valid=o>=en if buy else o<=en
   blocked=adj<=s200 if buy else adj>=r200
   out.append(dict(name=NAMES[i],buy=buy,eligible=valid and not blocked,entry=en,sl=sl,tp=tp,entry5=round5(en),sl5=round5(sl),tp5=round5(tp)))
  return out

def boundaries(ls):
 result=[]
 for l in ls:
  for k in ('entry','sl','tp','entry5','sl5','tp5'):
   v=l[k]/5;result.extend((5*v.to_integral_value(rounding=ROUND_FLOOR),5*v.to_integral_value(rounding=ROUND_CEILING)))
 return sorted(result)

def reduce_events(events,ls):
 """Keep first two records of each category plus every minute opener/non-grid trade."""
 bounds=boundaries(ls);last_bucket=None;last_minute=None;run=0
 for t in events:
  price=t['p'];idx=bisect_left(bounds,price);bucket=2*idx+int(idx<len(bounds) and bounds[idx]==price)
  changed=bucket!=last_bucket;minute=t['msc']//60000
  run=1 if changed else min(3,run+1)
  if changed or run<=2 or minute!=last_minute or price%5!=0:yield t
  last_bucket=bucket;last_minute=minute

def replay(events,ls,cut=None,grid=False,strict=False):
 state={l['name']:{'level':l,'status':'SEM_TOQUE' if l['eligible'] else 'INELEGIVEL','entry_event':None,'exit_event':None,'entry_theory':None,'exit_theory':None,'reason':None,'points':None} for l in ls}
 for t in events:
  p=t['p']
  for l in ls:
   s=state[l['name']]
   if not l['eligible'] or s['exit_event'] is not None:continue
   en=l['entry5' if grid else 'entry'];tp=l['tp5' if grid else 'tp'];sl=l['sl5' if grid else 'sl']
   if cut is not None and t['msc']>=cut:
    if s['entry_event'] is not None:
     s.update(exit_event=t,exit_theory=p,reason='CORTE_LAST',status='ENCERRADA')
    continue
   if s['entry_event'] is None:
    hit=(p<en if strict else p<=en) if l['buy'] else (p>en if strict else p>=en)
    if hit:s.update(entry_event=t,entry_theory=en,status='ABERTA')
    continue # Same protocol as manual audits: exit only at a later business record.
   stop=p<=sl if l['buy'] else p>=sl;target=p>=tp if l['buy'] else p<=tp
   if stop or target:s.update(exit_event=t,exit_theory=sl if stop else tp,reason='STOP' if stop else 'ALVO',status='ENCERRADA')
 for l in ls:
  s=state[l['name']]
  if s['exit_event'] is not None:
   s['points']=(s['exit_theory']-s['entry_theory'] if l['buy'] else s['entry_theory']-s['exit_theory']).quantize(D('0.000001'))
 return state

def summary(states):
 return {k:(s['status'],s['entry_event'],s['exit_event'],s['entry_theory'],s['exit_theory'],s['reason'],s['points']) for k,s in states.items()}
