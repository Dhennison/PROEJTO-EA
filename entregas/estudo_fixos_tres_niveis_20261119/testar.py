from pathlib import Path
import ast,csv,json,pickle,collections,math,itertools
import numpy as np
P=Path(__file__).parent;R=P.parents[1];E=R/'entregas';C=Path('/workspace/work/fixos_tres_niveis_20261119');C.mkdir(exist_ok=True)
x=pickle.load(open('/workspace/work/novos_niveis_20261119/resultados.pickle','rb'));data=x['data'];days=data['days'];di={d:i for i,d in enumerate(days)}
# Use exactly the same source and sequence engine as the new-level study.
ns=dict(np=np,data=data,replays={},noquote={'2024-02-06','2024-06-07','2025-06-03','2025-07-30','2025-08-21'})
for key,events in data['replay'].items():
 prices=np.array([v[1] for v in events],dtype=np.int32);times=np.array([int(v[0].replace(':','').replace('.','')) for v in events],dtype=np.int64);borders=np.r_[0,np.flatnonzero(times[1:]!=times[:-1])+1,len(times)];idx=np.concatenate([np.arange(i,j)[::-1] for i,j in zip(borders[:-1],borders[1:])]);ns['replays'][key]=(prices,times,prices[idx],times[idx])
src=(E/'estudo_niveis_auxiliares_20261119/estudar.py').read_text()
for f in ast.parse(src).body:
 if isinstance(f,ast.FunctionDef) and f.name in ['ticks','evaluate']:exec(compile(ast.Module(body=[f],type_ignores=[]),'same_sequence_engine','exec'),ns)
def read(p):return list(csv.DictReader(p.open(encoding='utf-8-sig'),delimiter=';'))
def write(name,rs):
 if not rs:return
 with (P/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rs[0]),delimiter=';');w.writeheader();w.writerows(rs)
labels={(r['date'],r['level']):r['outcomes'].split(':')[0] for r in read(E/'estudo_niveis_auxiliares_20261119/ROTULOS_ORIGINAIS_CONFERIDOS.csv')}
names=['R61.8','S38.2','S61.8'];ops=[o for o in data['ops'] if o['level'] in names];assert len(ops)==834
cfg=[dict(id=f'F{i:03d}',stop_points=s,target_points=t) for i,(s,t) in enumerate(itertools.product([25,50,75,100,150,200,250,375,500,650],[50,100,150,200,250,375,500,750,1000]))]
assert len(cfg)==90
rawfile=P/'CEDRO_RESULTADOS_CONFIRMADOS.csv';rawproof={(r['date'],r['level'],r['variant']):r for r in read(rawfile) if r['resolved']=='True'} if rawfile.exists() else {}
lo=np.zeros((3,90,709));hi=lo.copy();unc=np.zeros_like(lo,dtype=np.int16);trades=[];windows=[];proofs=[]
for li,name in enumerate(names):
 for ci,c in enumerate(cfg):
  td,sd=c['target_points'],c['stop_points']
  for o in [v for v in ops if v['level']==name]:
   originaltd=abs(o['tp']-o['entry']);originalsd=abs(o['sl']-o['entry']);reason=labels[(o['date'],name)];basis='M1_PLUS_VALIDATED_REPLAY';pend=[]
   if td==originaltd and sd==originalsd:ends={(reason,o['original'])};basis='FROZEN_ORIGINAL_IDENTICAL_DISTANCES'
   elif reason=='SL' and sd<=originalsd and td>=originaltd:ends={('SL',-sd)};basis='PROVEN_ORIGINAL_SL_TIGHTER_STOP_FARTHER_TARGET'
   elif reason=='TP' and sd>=originalsd and td<=originaltd:ends={('TP',td)};basis='PROVEN_ORIGINAL_TP_WIDER_STOP_NEARER_TARGET'
   elif reason=='CUT' and sd>=originalsd and td>=originaltd:ends={('CUT',o['original'])};basis='PROVEN_ORIGINAL_CUT_RELAXED_BARRIERS'
   else:ends,pend=ns['evaluate'](o,td,sd)
   proof=rawproof.get((o['date'],name,c['id']))
   if proof:
    value=int(proof['points']);assert min(v for _,v in ends)<=value<=max(v for _,v in ends);ends={(proof['reason'],value)};pend=[];basis='CEDRO_FULL_RECOVERED_RAW_SAME_MS_INVARIANT'
   a=min(v for _,v in ends);b=max(v for _,v in ends);idx=di[o['date']];lo[li,ci,idx]=a;hi[li,ci,idx]=b;unc[li,ci,idx]=len(ends)>1
   tr=dict(level=name,variant=c['id'],date=o['date'],contract=o['contract'],entry_minute=o['entry_minute'],entry=o['entry'],target_points=td,stop_points=sd,lower=a,upper=b,outcomes='|'.join(f'{r}:{v}' for r,v in sorted(ends)),pending=len(ends)>1,source=basis,**{f'{r}_guaranteed':all(k==r for k,v in ends) for r in ['TP','SL','CUT']},**{f'{r}_possible':any(k==r for k,v in ends) for r in ['TP','SL','CUT']});trades.append(tr)
   if basis.startswith('PROVEN'):proofs.append(dict(level=name,variant=c['id'],date=o['date'],original_reason=reason,original_target=originaltd,original_stop=originalsd,proof=basis,new_points=a))
   if len(ends)>1:
    for tm,why in pend:windows.append(dict(level=name,variant=c['id'],date=o['date'],contract=o['contract'],minute=tm,reason=why))
  if ci%18==0:print(name,ci,flush=True)
def dd(a):
 b=np.cumsum(a);return float(np.max(np.maximum.accumulate(np.r_[0,b])[1:]-b))
train=np.array([d<'2026-01-01' for d in days]);summary=[];annual=[];monthly=[]
for li,name in enumerate(names):
 for ci,c in enumerate(cfg):
  a,b=lo[li,ci],hi[li,ci];row=dict(level=name,**c,operations=sum(o['level']==name for o in ops),lower=float(a.sum()),upper=float(b.sum()),DD_lower=dd(b),DD_upper=dd(a),pending=int(unc[li,ci].sum()),points_per_DD=float(a.sum())/max(1,dd(a)),training_lower=float(a[train].sum()),training_DD=dd(a[train]),training_score=float(a[train].sum())/max(1,dd(a[train])))
  for y in [2024,2025,2026]:
   mask=np.array([d.startswith(str(y)) for d in days]);row[f'year{y}_lower']=float(a[mask].sum());row[f'year{y}_upper']=float(b[mask].sum());annual.append(dict(level=name,variant=c['id'],year=y,scope='JanOut' if y==2026 else 'Completo',lower=float(a[mask].sum()),upper=float(b[mask].sum()),DD_year_lower=dd(b[mask]),DD_year_upper=dd(a[mask]),pending=int(unc[li,ci,mask].sum())))
  for m in sorted({d[:7] for d in days}):
   mask=np.array([d.startswith(m) for d in days]);monthly.append(dict(level=name,variant=c['id'],month=m,lower=float(a[mask].sum()),upper=float(b[mask].sum()),DD_month_lower=dd(b[mask]),DD_month_upper=dd(a[mask]),pending=int(unc[li,ci,mask].sum())))
  summary.append(row)
selected=[]
for name in names:
 rr=[r for r in summary if r['level']==name]
 for criterion,key in [('TRAIN_RATIO',lambda r:r['training_score']),('FULL_RATIO_EXPLORATORY',lambda r:r['points_per_DD']),('FULL_POINTS_EXPLORATORY',lambda r:r['lower'])]:selected.append(dict(criterion=criterion,**max(rr,key=key)))
fixed=[r for r in summary if r['stop_points']==200 and r['target_points']==500]
write('PARAMETROS.csv',cfg);write('RESULTADOS_270_TESTES.csv',summary);write('SELECIONADOS_POR_NIVEL.csv',selected);write('RESULTADO_200_500.csv',fixed);write('ANUAL_TODOS_TESTES.csv',annual);write('MENSAL_TODOS_TESTES.csv',monthly);write('OPERACOES_TODOS_TESTES.csv',trades);write('PENDENCIAS_TODOS_TESTES.csv',windows);write('PROVAS_ORIGINAIS.csv',proofs)
cache=dict(data=data,days=days,names=names,ops=ops,configs=cfg,lo=lo,hi=hi,unc=unc,trades=trades,windows=windows,summary=summary,annual=annual,monthly=monthly,selected=selected,fixed=fixed)
(C/'resultados.pickle').write_bytes(pickle.dumps(cache,protocol=4));print('DONE',len(trades),len(windows),flush=True)
