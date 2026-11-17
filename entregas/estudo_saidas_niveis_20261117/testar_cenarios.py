"""Finite exploratory grid; frozen entries; uncertainty envelopes, not best-case fills.
Keep original reference exact. New exits remain conditional on M1/replay sources.
"""
from pathlib import Path
import csv,json,pickle,itertools,collections,math
import numpy as np
P=Path(__file__).parent;CACHE=Path('/workspace/work/estudo_saidas');data=pickle.loads((CACHE/'dados.pickle').read_bytes())
LEVELS=['R38.2','R61.8','S38.2','S50','S61.8'];days=data['days'];ops=data['ops'];nd=len(days);di={d:i for i,d in enumerate(days)};li={l:i for i,l in enumerate(LEVELS)}
months=sorted({d[:7] for d in days});years=['2024','2025','2026'];mi=np.array([months.index(d[:7]) for d in days]);yi=np.array([years.index(d[:4]) for d in days]);train=yi<2
cfg=[dict(id='D_ORIGINAL',mode='ORIGINAL',tp_multiplier=1,stop_parameter=1)]
for mode,ss in [('STOP_MULT_ORIGINAL',[.25,.5,.75,1,1.25,1.5,2]),('STOP_PROPORTIONAL_NEW_TARGET',[.5,.75,1,1.5,2,3]),('STOP_FIXED_POINTS',[100,150,250,375,500,650])]:
 for t in [.5,.75,1,1.25,1.5,2,3]:
  for st in ss:
   if mode=='STOP_MULT_ORIGINAL' and t==1 and st==1:continue
   cfg.append(dict(id=f'V{len(cfg):03d}',mode=mode,tp_multiplier=t,stop_parameter=st))
for t in [100,150,250,375,500,750,1000]:
 for st in [100,150,250,375,500,650]:cfg.append(dict(id=f'V{len(cfg):03d}',mode='FIXED_TARGET_AND_STOP_POINTS',tp_multiplier=t,stop_parameter=st))
assert len(cfg)==175
bars={d:[(int(b[0][:2])*60+int(b[0][3:]),*b[1:5]) for b in data['bars'][d]] for d in days}
replay=data['replay'];known_noquote={'2024-02-06','2024-06-07','2025-06-03','2025-07-30','2025-08-21'}
original_day=np.zeros((nd,5));counts=np.zeros((nd,5),dtype=int)
for o in ops:original_day[di[o['date']],li[o['level']]]+=o['original'];counts[di[o['date']],li[o['level']]]+=1
assert original_day.sum()==3950

def dist(c,o):
 td=max(5,int(math.floor((c['tp_multiplier'] if c['mode']=='FIXED_TARGET_AND_STOP_POINTS' else abs(o['tp']-o['entry'])*c['tp_multiplier'])/5+.5))*5)
 s=c['stop_parameter']
 sd=max(5,int(math.floor((abs(o['sl']-o['entry'])*s if c['mode']=='STOP_MULT_ORIGINAL' else td*s if c['mode']=='STOP_PROPORTIONAL_NEW_TARGET' else s)/5+.5))*5)
 return td,sd

def tick_choices(es,e,tp,sl,sign,entering):
 def run(events):
  active=not entering
  for tm,p,q in events:
   p*=sign
   if not active:
    if p<=e:active=True
    continue
   if p>=tp:return 'TP'
   if p<=sl:return 'SL'
  return 'OPEN'
 a=run(es);alt=sorted(es,key=lambda ev:ev[0]);b=run(alt)
 # Any ms containing opposite barriers can have unknown internal chronology.
 groups=collections.defaultdict(list)
 for tm,p,q in es:groups[tm].append(sign*p)
 if any(min(v)<=sl and max(v)>=tp for v in groups.values()):return None
 return {a} if a==b else None

def evaluate(o,td,sd,use_replay=True):
 sign=1 if o['buy'] else -1;e=sign*o['entry'];tp=e+td;sl=e-sd;start=int(o['entry_minute'][:2])*60+int(o['entry_minute'][3:]);bs=bars[o['date']]
 cut=next((sign*b[1]-e for b in bs if b[0]>=1080),None)
 if cut is None:return -sd,td,[('18:00','CUT_MISSING')]
 # New August exits cannot be certified from missing Cedro raw/minute data.
 if o['date'].startswith('2026-08') and not data['source'][o['date']].startswith('CEDRO_AUDIT'):return min(-sd,cut),max(td,cut),[('ALL','CEDRO_RAW_AND_AUDIT_M1_MISSING')]
 entrybar=next((b for b in bs if b[0]==start),None)
 if entrybar is None or (entrybar[3]>o['entry'] if sign==1 else entrybar[2]<o['entry']):return min(-sd,cut),max(td,cut),[(o['entry_minute'],'ENTRY_SOURCE_MISMATCH')]
 ends=[];active=True;pending=[];last=start
 for minute,bo,bh,bl,bc in bs:
  if minute<start:continue
  if minute>=1080:
   if active:ends.append(sign*bo-e)
   active=False;break
  if not active:break
  if minute-last>1 and o['date'] not in known_noquote:
   ends.extend([-sd,td]);pending.append((f'{last//60:02d}:{last%60:02d}','GAP_AFTER_ENTRY'))
  last=minute
  O,H,L,C=(bo,bh,bl,bc) if sign==1 else (-bo,-bl,-bh,-bc);entering=minute==start
  if entering:
   poss=H>=tp;forced=poss and (O<=e or C>=tp);stop=L<=sl
   choices=({'TP'} if poss else set())|({'SL'} if stop else set())|({'OPEN'} if not forced and not stop else set())
  else:
   choices={'TP'} if O>=tp else {'SL'} if O<=sl else ({'TP'} if H>=tp else set())|({'SL'} if L<=sl else set()) or {'OPEN'}
  tm=f'{minute//60:02d}:{minute%60:02d}'
  if len(choices)>1:
   exact=tick_choices(replay[(o['date'],tm)],e,tp,sl,sign,entering) if use_replay and (o['date'],tm) in replay else None
   if exact:choices=exact
   else:pending.append((tm,'SEQUENCE_M1'))
  if 'TP' in choices:ends.append(td)
  if 'SL' in choices:ends.append(-sd)
  active='OPEN' in choices
 if active:return min(-sd,cut),max(td,cut),pending+[('18:00','UNFINISHED')]
 assert ends,(o,td,sd)
 return min(ends),max(ends),pending if len(set(ends))>1 else []
# Verify source consistency with the frozen original before any changed exit.
bad={};baseline=[]
for i,o in enumerate(ops):
 lo,hi,pend=evaluate(o,abs(o['tp']-o['entry']),abs(o['sl']-o['entry']))
 if not lo<=o['original']<=hi:bad[i]=(lo,hi)
 baseline.append(dict(date=o['date'],level=o['level'],original=o['original'],M1_lower=lo,M1_upper=hi,source_consistent=lo<=o['original']<=hi,bar_source=o['bar_source']))

def write(name,rs):
 with (P/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rs[0]),delimiter=';',lineterminator='\n');w.writeheader();w.writerows(rs)
write('CONFERENCIA_BASELINE_FONTES.csv',baseline)
lo=np.zeros((len(cfg),nd,5));hi=np.zeros_like(lo);uncertain=np.zeros_like(lo,dtype=int);trade_bounds=[];windows=collections.defaultdict(set)
resume=pickle.loads((CACHE/'resultados.pickle').read_bytes()) if (CACHE/'resultados.pickle').exists() else None
if resume and (resume['data']['source']!=data['source'] or resume['data']['bars']!=data['bars'] or resume['data']['replay']!=data['replay']):resume=None
completed=len(resume['cfg']) if resume else 0
if completed:
 assert completed<=len(cfg) and all(a==b for a,b in zip(resume['cfg'],cfg))
 lo[:completed]=resume['lo'];hi[:completed]=resume['hi'];uncertain[:completed]=resume['uncertain']
 with (P/'LIMITES_POR_OPERACAO.csv').open(encoding='utf-8-sig') as f:trade_bounds=list(csv.DictReader(f,delimiter=';'))
 for w in resume['windows']:windows[(w['date'],w['level'],w['minute'],w['reason'])].update(w['variants'].split('|'))
for ci,c in enumerate(cfg):
 if ci<completed:continue
 for oi,o in enumerate(ops):
  d,l=di[o['date']],li[o['level']]
  if ci==0:a=b=o['original'];pp=[];td=abs(o['tp']-o['entry']);sd=abs(o['sl']-o['entry'])
  else:
   td,sd=dist(c,o)
   # Different numeric parameterization that yields exactly original distances
   # can reuse the already closed original trade.
   if td==abs(o['tp']-o['entry']) and sd==abs(o['sl']-o['entry']):a=b=o['original'];pp=[]
   elif oi in bad:a,b,pp=-sd,td,[(o['entry_minute'],'BASELINE_SOURCE_INCOMPATIBLE')]
   else:a,b,pp=evaluate(o,td,sd)
  lo[ci,d,l]+=a;hi[ci,d,l]+=b;uncertain[ci,d,l]+=a!=b
  trade_bounds.append(dict(variant=c['id'],date=o['date'],level=o['level'],target_points=td,stop_points=sd,lower=a,upper=b,uncertain=a!=b))
  if a!=b:
   for tm,why in pp:windows[(o['date'],o['level'],tm,why)].add(c['id'])
 if ci%10==0:print('TESTED',ci,'/',len(cfg),flush=True)
assert np.array_equal(lo[0],original_day) and np.array_equal(hi[0],original_day)

def dd(a):
 b=np.cumsum(a);return float(np.max(np.maximum.accumulate(np.r_[0,b])[1:]-b))
def metrics(a,b,n,u):
 ml=np.bincount(mi,weights=a,minlength=len(months));mh=np.bincount(mi,weights=b,minlength=len(months));yl=[float(a[yi==i].sum()) for i in range(3)];yh=[float(b[yi==i].sum()) for i in range(3)];pl=float(a.sum());ph=float(b.sum());ndd=dd(a)
 positives=np.sort(a[a>0])[::-1];top5=float(positives[:5].sum()/positives.sum()) if len(positives) else 0
 return dict(points_lower=pl,points_upper=ph,DD_upper=ndd,DD_lower=dd(b),operations=int(n),uncertain_trades=int(u),months_positive_lower=int((ml>0).sum()),months_negative_lower=int((ml<0).sum()),months_zero_lower=int((ml==0).sum()),worst_month_lower=float(ml.min()),best_month_lower=float(ml.max()),top5_share_positive_days_lower=top5,year2024_lower=yl[0],year2024_upper=yh[0],year2025_lower=yl[1],year2025_upper=yh[1],year2026_JanOct_lower=yl[2],year2026_JanOct_upper=yh[2],training_2024_25_lower=yl[0]+yl[1],validation_2026_lower=yl[2],points_after_cost5_lower=pl-5*n,points_after_cost10_lower=pl-10*n,points_after_cost20_lower=pl-20*n,break_even_cost_lower=pl/n if n else 0,points_DD_ratio_lower=pl/max(1,ndd))
subsets=[];allscenario=[];scenario_daily={}
for mask in range(1,32):
 use=[i for i in range(5) if mask>>i&1];a=original_day[:,use].sum(1);n=counts[:,use].sum();name='EXC_'+str(mask).zfill(2)
 row=dict(id=name,levels='|'.join(LEVELS[i] for i in use),**metrics(a,a,n,0));subsets.append(row);scenario_daily[name]=(a,a)
write('EXCLUSOES_31_COMBINACOES_EXATAS.csv',subsets)
levelmetrics=[]
for ci,c in enumerate(cfg):
 a=lo[ci].sum(1);b=hi[ci].sum(1);row=dict(id=c['id'],family='SAME_RULE_ALL_LEVELS',rule=json.dumps(c),**metrics(a,b,counts.sum(),uncertain[ci].sum()));allscenario.append(row);scenario_daily[c['id']]=(a,b)
 for l in range(5):levelmetrics.append(dict(variant=c['id'],level=LEVELS[l],**metrics(lo[ci,:,l],hi[ci,:,l],counts[:,l].sum(),uncertain[ci,:,l].sum())))
write('VARIANTES_POR_NIVEL.csv',levelmetrics)
# Select per-level candidates using only 2024/25, before examining 2026.
choices=[];selection=[]
for l in range(5):
 def score(i):
  a=lo[i,train,l];p=a.sum();return p/max(1,dd(a))
 byratio=sorted(range(len(cfg)),key=score,reverse=True)[:2]
 byprofit=max(range(len(cfg)),key=lambda i:lo[i,train,l].sum())
 ids=list(dict.fromkeys([-1,0,*byratio,byprofit]));choices.append(ids)
 for i in ids:selection.append(dict(level=LEVELS[l],variant='OFF' if i==-1 else cfg[i]['id'],selection_period='2024-2025_ONLY',training_points_lower=0 if i==-1 else float(lo[i,train,l].sum()),training_DD_upper=0 if i==-1 else dd(lo[i,train,l])))
write('SELECAO_POR_NIVEL_TREINO_2024_2025.csv',selection)
for ix,comb in enumerate(itertools.product(*choices)):
 if all(i==-1 for i in comb):continue
 a=np.zeros(nd);b=np.zeros(nd);n=u=0;desc=[]
 for l,i in enumerate(comb):
  if i<0:desc.append(LEVELS[l]+':OFF');continue
  a+=lo[i,:,l];b+=hi[i,:,l];n+=counts[:,l].sum();u+=uncertain[i,:,l].sum();desc.append(LEVELS[l]+':'+cfg[i]['id'])
 name=f'MIX_{ix:04d}';allscenario.append(dict(id=name,family='DIFFERENT_RULE_BY_LEVEL_OR_OFF',rule='|'.join(desc),**metrics(a,b,n,u)));scenario_daily[name]=(a,b)
write('CENARIOS_SAIDAS_E_MISTOS.csv',allscenario);write('PARAMETROS_VARIANTES.csv',cfg);write('LIMITES_POR_OPERACAO.csv',trade_bounds)
windowrows=[dict(date=k[0],level=k[1],minute=k[2],reason=k[3],variants_count=len(v),variants='|'.join(sorted(v))) for k,v in sorted(windows.items())]
write('PENDENCIAS_TODAS_VARIANTES.csv',windowrows)
# Full monthly/yearly outputs; all bounds, not synthetic best-case realization.
monthly=[]
for row in allscenario+subsets:
 a,b=scenario_daily[row['id']]
 for i,m in enumerate(months):monthly.append(dict(scenario=row['id'],month=m,points_lower=float(a[mi==i].sum()),points_upper=float(b[mi==i].sum())))
write('RESULTADO_MENSAL_TODOS_CENARIOS.csv',monthly)
(CACHE/'resultados.pickle').write_bytes(pickle.dumps(dict(data=data,cfg=cfg,lo=lo,hi=hi,uncertain=uncertain,counts=counts,subsets=subsets,scenarios=allscenario,levelmetrics=levelmetrics,scenario_daily=scenario_daily,windows=windowrows,baseline_bad=bad),protocol=4))
summary=dict(period='2024-01 a2026-10',days=nd,ops=len(ops),original_points=3950,original_DD=dd(original_day.sum(1)),exit_rules=len(cfg),per_level_rule_tests=len(levelmetrics),exact_exclusion_combinations=len(subsets),mixed_candidates=len(allscenario)-len(cfg),total_scenarios=len(allscenario)+len(subsets),source_baseline_inconsistent_trades=len(bad),ambiguous_window_rows=len(windowrows),selection_training='2024-2025',validation='2026JanOct;alreadyknownhistorically,notindependentfuture',raw_cedro_missing=True,no_parameter_promoted=True)
(P/'RESUMO_ESTUDO.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');print(json.dumps(summary,indent=2),flush=True)
