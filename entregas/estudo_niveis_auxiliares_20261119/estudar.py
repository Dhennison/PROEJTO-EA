from pathlib import Path
from decimal import Decimal as D,localcontext
import csv,json,pickle,ast,collections,math,hashlib,itertools,sys
import numpy as np
P=Path(__file__).parent;R=P.parents[1];E=R/'entregas';CACHE=Path('/workspace/work/novos_niveis_20261119');CACHE.mkdir(exist_ok=True)
sys.path.insert(0,str(E/'fechamento_agosto_v1_11/analise'));from motor_precos import round5,levels
# Reuse only the reference-loading part of the preparation script, without rewriting its artifacts.
pre=E/'estudo_saidas_niveis_20261117/preparar_dados.py';source=pre.read_text();prefix=source[:source.index('base_daily=')];ns={'__file__':str(pre)};exec(compile(prefix,str(pre),'exec'),ns);refs=ns['refs'];sources=ns['sources']
for f in [E/'fechamento_agosto_v1_11/MQL5/Files/MD_Agosto_2026_Referencias.csv',E/'cedro_modelod_setembro_2026/referencias/REFERENCIAS.csv',E/'cedro_modelod_outubro_2026/resultado_mensal/REFERENCIAS.csv']:
 sources.append(str(f.relative_to(R)))
 for r in csv.DictReader(f.open(encoding='utf-8-sig'),delimiter=';'):refs[r['date'].replace('.','-')]=r
x=pickle.load(open('/workspace/work/estudo_s61/resultados.pickle','rb'));data=x['data'];days=data['days'];di={d:i for i,d in enumerate(days)};assert len(days)==709 and set(days)<=refs.keys()
audit=pickle.load(open('/workspace/work/replay_s61_20261119/auditoria.pickle','rb'));data['replay'].update(audit['accepted'])
original=data['ops'];contract={d:next((o['contract'] for o in original if o['date']==d),'') for d in days}
for d in days:
 ref=refs[d]
 if not contract[d]:contract[d]=ref.get('contract',ref.get('contrato_Replay',ref.get('symbol','')))
 if d.startswith('2026-07-'):contract[d]='WINQ26' # Same contract explicitly used by the preserved July source folder.
 if '|' in contract[d] or not contract[d]:
  # Infer from the saved daily source configuration only, never arbitrary expiry rules.
  month={'08':'agosto','09':'setembro','10':'outubro'}.get(d[5:7]) if d.startswith('2026-') else None
  paths=list((E/f'cedro_modelod_{month}_2026').rglob(d.replace('-','')+'.config')) if month else []
  if paths:contract[d]=paths[0].read_text().split()[0]
 assert contract[d] and '|' not in contract[d],(d,ref)
# Confirm recomputation of the five original rounded entry levels against every frozen trade.
for o in original:
 lv=next(l for l in levels(refs[o['date']]) if l['name']==o['level']);assert int(lv['entry5'])==o['entry'],(o,lv)
newops=[];alllevels=[]
for d in days:
 ref=refs[d]
 with localcontext() as ctx:
  ctx.prec=40;o,h,l,c,adj=map(D,(ref['open'],ref['high_prev'],ref['low_prev'],ref['close_prev'],ref['adjustment']));pp=(h+l+c)/3;r200=o+2*abs(l-pp);s200=o-2*abs(h-pp)
  rr={f:adj+(r200-adj)*D(f) for f in ['0.236','0.382','0.5']};ss={f:adj+(s200-adj)*D(f) for f in ['0.236','0.382']}
  for name,buy,en,nexttarget,blocked in [('R23.6',False,rr['0.236'],adj,adj>=r200),('R50',False,rr['0.5'],rr['0.382'],adj>=r200),('S23.6',True,ss['0.236'],adj,adj<=s200)]:
   eligible=(o>=en if buy else o<=en) and not blocked;entry=int(round5(en));target=int(round5(nexttarget));distance=abs(target-entry)
   bs=data['bars'][d];first=next((b[0][:5] for b in bs if b[0][:5]<'18:00' and (b[3]<=entry if buy else b[2]>=entry)),None) if eligible else None
   row=dict(date=d,contract=contract[d],level=name,buy=buy,entry=entry,reference_target=target,reference_distance=distance,eligible=eligible,entry_minute=first or '',status='ENTRY' if first else 'NO_TOUCH' if eligible else 'INELIGIBLE',source=data['source'][d]);alllevels.append(row)
   if first:newops.append(row)
assert len({(o['date'],o['level']) for o in newops})==len(newops)
# Preserve and compact validated replay as price arrays. Same-ms alternative is tested separately.
replays={}
for key,events in data['replay'].items():
 a=np.array([v[1] for v in events],dtype=np.int32);tm=np.array([int(v[0].replace(':','').replace('.','')) for v in events],dtype=np.int64)
 idx=np.concatenate([np.arange(i,j)[::-1] for i,j in zip(np.r_[0,np.flatnonzero(tm[1:]!=tm[:-1])+1],np.r_[np.flatnonzero(tm[1:]!=tm[:-1])+1,len(tm)])])
 replays[key]=(a,tm,a[idx],tm[idx])
def ticks(key,e,tp,sl,sign,entering):
 def once(prices,times):
  p=prices*sign;start=0
  if entering:
   ii=np.flatnonzero(p<=e)
   if not len(ii):return 'OPEN'
   i=int(ii[0]);start=i+1
   # Entry and target in one ms are conservatively unresolved.
   if np.any(p[times==times[i]]>=tp):return None
  hit=np.flatnonzero((p[start:]>=tp)|(p[start:]<=sl))
  if not len(hit):return 'OPEN'
  i=start+int(hit[0]);group=p[times==times[i]]
  if min(group)<=sl and max(group)>=tp:return None
  return 'TP' if p[i]>=tp else 'SL'
 a,t,b,u=replays[key];v=once(a,t);w=once(b,u)
 return {v} if v is not None and v==w else None
noquote={'2024-02-06','2024-06-07','2025-06-03','2025-07-30','2025-08-21'}
# Outcome sets distinguish target, full stop and time exits even where point values coincide.
def evaluate(o,td,sd):
 sign=1 if o['buy'] else -1;e=sign*o['entry'];tp=e+td;sl=e-sd;start=o['entry_minute'];ends=set();pending=[];last=start
 for tm,bo,bh,bl,bc,q in data['bars'][o['date']]:
  tm=tm[:5]
  if tm<start:continue
  if tm>='18:00':ends.add(('CUT',sign*bo-e));return ends,pending
  def minutes(t):return int(t[:2])*60+int(t[3:])
  if minutes(tm)-minutes(last)>1 and o['date'] not in noquote:
   ends.update([('SL',-sd),('TP',td)]);pending.append((last,'GAP_AFTER_ENTRY'))
  last=tm;O,H,L,C=(bo,bh,bl,bc) if sign==1 else (-bo,-bl,-bh,-bc);entering=tm==start
  if entering:
   poss=H>=tp;forced=poss and (O<=e or C>=tp);stop=L<=sl;choices=({'TP'} if poss else set())|({'SL'} if stop else set())|({'OPEN'} if not forced and not stop else set())
  else:choices={'TP'} if O>=tp else {'SL'} if O<=sl else ({'TP'} if H>=tp else set())|({'SL'} if L<=sl else set()) or {'OPEN'}
  if len(choices)>1:
   exact=ticks((o['date'],tm),e,tp,sl,sign,entering) if (o['date'],tm) in replays else None
   if exact:choices=exact
   else:pending.append((tm,'SEQUENCE_M1'))
  if 'TP' in choices:ends.add(('TP',td))
  if 'SL' in choices:ends.add(('SL',-sd))
  if 'OPEN' not in choices:return ends,pending if len(ends)>1 else []
 # Explicitly keep unfinished exits unresolved; never invent a cut price.
 ends.update([('SL',-sd),('TP',td)]);pending.append(('18:00','CUT_MISSING'));return ends,pending
# Freeze original results; only verify compatibility with the source/engine.
bad=[]
for o in original:
 ends,pend=evaluate(o,abs(o['tp']-o['entry']),abs(o['sl']-o['entry']));vals=[v for _,v in ends]
 if not min(vals)<=o['original']<=max(vals):bad.append(dict(date=o['date'],level=o['level'],original=o['original'],outcomes=str(ends)))
assert not bad,bad
config=[]
for target_mode,targets in [('FIXED',[50,100,150,200,250,375,500,750]),('REFERENCE_MULT',[.5,1,1.5,2])]:
 for tv in targets:
  for stop_mode,stops in [('FIXED',[25,50,75,100,150,200,250,375,500,650]),('TARGET_RATIO',[.5,1,1.5,2])]:
   for sv in stops:config.append(dict(id=f'N{len(config):03d}',target_mode=target_mode,target_value=tv,stop_mode=stop_mode,stop_value=sv))
assert len(config)==168
def distances(c,o):
 td=max(5,int(math.floor((c['target_value'] if c['target_mode']=='FIXED' else o['reference_distance']*c['target_value'])/5+.5))*5)
 sd=max(5,int(math.floor((c['stop_value'] if c['stop_mode']=='FIXED' else td*c['stop_value'])/5+.5))*5)
 return td,sd
def dd(a):
 b=np.cumsum(a);return float(np.max(np.maximum.accumulate(np.r_[0,b])[1:]-b))
newnames=['R23.6','R50','S23.6'];oldnames=['R38.2','R61.8','S38.2','S50','S61.8'];train=np.array([d<'2026-01-01' for d in days]);yearmasks={y:np.array([d.startswith(str(y)) for d in days]) for y in [2024,2025,2026]}
rawfile=P/'CEDRO_RESULTADOS_CONFIRMADOS.csv'
rawproof={(r['date'],r['level'],r['variant']):r for r in csv.DictReader(rawfile.open(encoding='utf-8-sig'),delimiter=';') if r['resolved']=='True'} if rawfile.exists() else {}
lo=np.zeros((3,168,709));hi=lo.copy();unc=np.zeros_like(lo,dtype=np.int16);trades=[];windows=[];summaries=[]
for li,name in enumerate(newnames):
 oo=[o for o in newops if o['level']==name]
 for ci,c in enumerate(config):
  for o in oo:
   td,sd=distances(c,o);ends,pend=evaluate(o,td,sd)
   proof=rawproof.get((o['date'],o['level'],c['id']))
   if proof:
    value=int(proof['points']);assert min(v for _,v in ends)<=value<=max(v for _,v in ends);ends={(proof['reason'],value)};pend=[]
   a=min(v for _,v in ends);b=max(v for _,v in ends);idx=di[o['date']];lo[li,ci,idx]=a;hi[li,ci,idx]=b;unc[li,ci,idx]=len(ends)>1
   tr=dict(level=name,variant=c['id'],date=o['date'],contract=o['contract'],entry_minute=o['entry_minute'],entry=o['entry'],target_points=td,stop_points=sd,lower=a,upper=b,outcomes='|'.join(f'{r}:{v}' for r,v in sorted(ends)),pending=len(ends)>1,TP_guaranteed=all(r=='TP' for r,v in ends),TP_possible=any(r=='TP' for r,v in ends),SL_guaranteed=all(r=='SL' for r,v in ends),SL_possible=any(r=='SL' for r,v in ends),CUT_guaranteed=all(r=='CUT' for r,v in ends),CUT_possible=any(r=='CUT' for r,v in ends));trades.append(tr)
   if len(ends)>1:
    for tm,why in pend:windows.append(dict(level=name,variant=c['id'],date=o['date'],contract=o['contract'],minute=tm,reason=why))
  a=lo[li,ci];b=hi[li,ci];row=dict(level=name,**c,operations=len(oo),lower=float(a.sum()),upper=float(b.sum()),DD_lower_path=dd(b),DD_upper_path=dd(a),pending=int(unc[li,ci].sum()),training_lower=float(a[train].sum()),training_upper=float(b[train].sum()),training_DD=dd(a[train]),training_score=float(a[train].sum())/max(1,dd(a[train])),points_per_DD=float(a.sum())/max(1,dd(a)))
  for y,m in yearmasks.items():row[f'year{y}_lower']=float(a[m].sum());row[f'year{y}_upper']=float(b[m].sum())
  summaries.append(row)
  if ci%28==0:print('GRID',name,ci,'entries',len(oo),flush=True)
# Selection uses 2024-25 only. 2026 is chronological comparison, not unseen independent evidence.
selections=[]
for li,name in enumerate(newnames):
 candidates=[s for s in summaries if s['level']==name]
 for family,key in [('TRAIN_SCORE',lambda s:s['training_score']),('TRAIN_POINTS',lambda s:s['training_lower']),('TRAIN_STABILITY',lambda s:(min(s['year2024_lower'],s['year2025_lower']),s['training_score']))]:
  s=max(candidates,key=key);selections.append(dict(family=family,**s))
oldcurve=np.zeros((5,709));oldcounts=np.zeros_like(oldcurve,dtype=int)
for o in original:i=oldnames.index(o['level']);j=di[o['date']];oldcurve[i,j]=o['original'];oldcounts[i,j]=1
assert oldcurve.sum()==3950 and dd(oldcurve.sum(0))==14805
combinations=[]
for family in ['TRAIN_SCORE','TRAIN_POINTS','TRAIN_STABILITY']:
 selected=[next(s for s in selections if s['family']==family and s['level']==name) for name in newnames];indices=[int(s['id'][1:]) for s in selected]
 curveslo=np.vstack([oldcurve,*[lo[i,indices[i]] for i in range(3)]]);curveshi=np.vstack([oldcurve,*[hi[i,indices[i]] for i in range(3)]])
 counts=np.vstack([oldcounts,*[np.array([sum(o['date']==d and o['level']==name for o in newops) for d in days]) for name in newnames]])
 for mask in range(1,256):
  use=[i for i in range(8) if mask>>i&1];a=curveslo[use].sum(0);b=curveshi[use].sum(0);labels=[oldnames[i] if i<5 else newnames[i-5]+':'+selected[i-5]['id'] for i in use]
  row=dict(id=family+'_'+str(mask).zfill(3),family=family,mask=mask,levels='|'.join(labels),lower=float(a.sum()),upper=float(b.sum()),DD_lower_path=dd(b),DD_upper_path=dd(a),points_per_DD=float(a.sum())/max(1,dd(a)),training_lower=float(a[train].sum()),training_DD=dd(a[train]),training_score=float(a[train].sum())/max(1,dd(a[train])),operations=int(counts[use].sum()),pending=sum(int(unc[i-5,indices[i-5]].sum()) for i in use if i>=5))
  for y,m in yearmasks.items():row[f'year{y}_lower']=float(a[m].sum());row[f'year{y}_upper']=float(b[m].sum())
  combinations.append(row)
def write(name,rs):
 if not rs:return
 with (P/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rs[0]),delimiter=';');w.writeheader();w.writerows(rs)
write('REFERENCIAS_NOVOS_NIVEIS.csv',alllevels);write('PARAMETROS.csv',config);write('CENARIOS_POR_NIVEL.csv',summaries);write('SELECAO_TREINO_2024_2025.csv',selections);write('COMBINACOES_765.csv',combinations);write('OPERACOES_TODOS_TESTES.csv',trades);write('PENDENCIAS_TODOS_TESTES.csv',windows)
cache=dict(data=data,refs=refs,newops=newops,alllevels=alllevels,configs=config,lo=lo,hi=hi,unc=unc,trades=trades,windows=windows,summaries=summaries,selections=selections,combinations=combinations,oldnames=oldnames,newnames=newnames,oldcurve=oldcurve,oldcounts=oldcounts,sources=sources)
(CACHE/'resultados.pickle').write_bytes(pickle.dumps(cache,protocol=4))
print('DONE',len(newops),len(trades),len(windows),len(combinations),flush=True)
