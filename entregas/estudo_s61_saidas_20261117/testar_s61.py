"""Dedicated S61 stop/target study. Keep original entries and source distinctions.
Recover correctly named CedroAugust audit M1, and apply original-outcome implications.
"""
from pathlib import Path
import csv,json,pickle,ast,math,collections,hashlib
import numpy as np
P=Path(__file__).parent;R=P.parents[1];E=R/'entregas';DATA=pickle.loads(Path('/workspace/work/estudo_saidas/dados.pickle').read_bytes());days=DATA['days'];di={d:i for i,d in enumerate(days)};ops=[o for o in DATA['ops'] if o['level']=='S61.8'];assert len(ops)==233 and all(abs(o['sl']-o['entry'])==650 for o in ops)
def read(p):
 with p.open(encoding='utf-8-sig') as f:return list(csv.DictReader(f,delimiter=';'))
def write(name,rs):
 with (P/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rs[0]),delimiter=';',lineterminator='\n');w.writeheader();w.writerows(rs)
# These files existed in the repository; their name is M1_CONTRACT_DATE.csv,
# unlike DATE_M1.csv in the September/October audit folders.
found=[]
for p in (E/'cedro_extrator_win_v1_00').rglob('retorno_agosto*/M1_WIN*.csv'):
 rr=read(p);assert rr
 day=rr[0]['time'][:10].replace('.','-');assert day.startswith('2026-08')
 DATA['bars'][day]=[(r['time'][11:],*[int(float(r[k])) for k in ['open','high','low','close']],int(float(r['soma_campo4']))) for r in rr];DATA['source'][day]='CEDRO_AUDIT_M1_RECOVERED_FROM_SAVED_FOLDER'
 found.append(dict(date=day,path=str(p.relative_to(R)),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bars=len(rr)))
assert len(found)==21 and len({r['date'] for r in found})==21
write('FONTES_CEDRO_AGOSTO_M1_LOCALIZADAS.csv',sorted(found,key=lambda r:r['date']))
bars={d:[(int(b[0][:2])*60+int(b[0][3:]),*b[1:5]) for b in DATA['bars'][d]] for d in days}
ns=dict(data=DATA,math=math,collections=collections,bars=bars,replay=DATA['replay'],known_noquote={'2024-02-06','2024-06-07','2025-06-03','2025-07-30','2025-08-21'})
tree=ast.parse((E/'estudo_saidas_niveis_20261117/testar_cenarios.py').read_text())
for f in tree.body:
 if isinstance(f,ast.FunctionDef) and f.name in ['tick_choices','evaluate']:
  source=ast.get_source_segment((E/'estudo_saidas_niveis_20261117/testar_cenarios.py').read_text(),f)
  source=source.replace(" if o['date'].startswith('2026-08'):return min(-sd,cut),max(td,cut),[('ALL','CEDRO_RAW_AND_AUDIT_M1_MISSING')]",'')
  exec(compile(source,'focused_s61_engine','exec'),ns)
# Frozen original labels remain the basis for valid monotonic implications.
origops=read(E/'resultado_niveis_202401_202610_20261117/OPERACOES_NORMALIZADAS.csv');origS={(r['date'],r['level']):float(r['points']) for r in origops if r['level']=='S61.8'}
original_labels={r['date']:r['original_reason'] for r in read(P/'ROTULOS_ORIGINAIS_CONFERIDOS.csv')}
assert len(original_labels)==233
config=[]
for stop in [650,500,375,325,250,200,150,100]:
 for tf in [1,1.25,1.5,2,3,4]:
  fam='ORIGINAL' if stop==650 and tf==1 else '1_STOP650_ALVO_MAIOR' if stop==650 else '2_STOP_MENOR_ALVO_ORIGINAL' if tf==1 else '3_STOP_MENOR_ALVO_MAIOR'
  config.append(dict(id='S61_ORIGINAL' if fam=='ORIGINAL' else f'S61_{len(config):02d}',family=fam,stop_mode='FIXED_POINTS',stop_value=stop,target_multiplier=tf))
for ratio in [.5,.75,1,1.5,2]:
 for tf in [1,1.5,2,3]:config.append(dict(id=f'S61_{len(config):02d}',family='EXTRA_STOP_PROPORCIONAL_NOVO_ALVO',stop_mode='PROPORTIONAL_NEW_TARGET',stop_value=ratio,target_multiplier=tf))
for ratio in [.5,.75,1,1.5,2]:
 for tf in [1,1.5,2,3]:config.append(dict(id=f'S61_{len(config):02d}',family='EXTRA_STOP_PROPORCIONAL_TETO650',stop_mode='PROPORTIONAL_NEW_TARGET_CAP650',stop_value=ratio,target_multiplier=tf))
assert len(config)==88
lo=np.zeros((len(config),len(days)));hi=np.zeros_like(lo);pending=np.zeros_like(lo,dtype=int);trade=[];windows=[];proofs=[];baseline_bad=[]
# M1 baseline must remain compatible with each original before new exits.
for o in ops:
 a,b,_=ns['evaluate'](o,abs(o['tp']-o['entry']),650)
 if not a<=o['original']<=b:baseline_bad.append(dict(date=o['date'],original=o['original'],M1_lower=a,M1_upper=b))
assert not baseline_bad,baseline_bad
for ci,c in enumerate(config):
 for o in ops:
  originaltd=abs(o['tp']-o['entry']);td=max(5,int(math.floor(originaltd*c['target_multiplier']/5+.5))*5);sd=int(c['stop_value']) if c['stop_mode']=='FIXED_POINTS' else max(5,int(math.floor(td*c['stop_value']/5+.5))*5)
  if c['stop_mode']=='PROPORTIONAL_NEW_TARGET_CAP650':sd=min(650,sd)
  basis='M1_PLUS_COMPLETE_EXISTING_REPLAY';pp=[]
  if td==originaltd and sd==650:a=b=o['original'];basis='FROZEN_ORIGINAL'
  elif original_labels[o['date']]=='TP' and sd>=650 and td<=originaltd:
   a=b=td;basis='PROVEN_ORIGINAL_TARGET_WITH_NOT_TIGHTER_STOP_AND_NOT_FARTHER_TARGET'
  elif original_labels[o['date']]=='SL' and sd<=650 and td>=originaltd:
   # Original hit stop before its nearer target. A tighter stop with a target
   # no nearer must also exit at stop, regardless of within-minute ordering.
   a=b=-sd;basis='PROVEN_ORIGINAL_STOP_WITH_TIGHTER_STOP_AND_NOT_NEARER_TARGET'
  elif original_labels[o['date']]=='CORTE' and sd>=650 and td>=originaltd:
   a=b=o['original'];basis='PROVEN_ORIGINAL_CUT_WITH_BOTH_BARRIERS_RELAXED'
  else:
   a,b,pp=ns['evaluate'](o,td,sd)
   # A known original cutoff excludes reaching any farther target before cut.
   if original_labels[o['date']]=='CORTE' and td>=originaltd:
    aa=max(a,min(-sd,o['original']));bb=min(b,max(-sd,o['original']))
    assert aa<=bb,(c,o,a,b,'originalcutconstraint');a,b=aa,bb
    if a==b:basis='M1_PLUS_PROVEN_ORIGINAL_CUT_CONSTRAINT';pp=[]
  if a==b and basis.startswith('PROVEN'):proofs.append(dict(variant=c['id'],date=o['date'],original=o['original'],new_points=a,proof=basis))
  lo[ci,di[o['date']]]=a;hi[ci,di[o['date']]]=b;pending[ci,di[o['date']]]=a!=b
  trade.append(dict(variant=c['id'],date=o['date'],contract=o['contract'],entry_minute=o['entry_minute'],entry=o['entry'],target_points=td,stop_points=sd,original_points=o['original'],lower=a,upper=b,source=basis,unresolved=a!=b))
  if a!=b:
   for tm,why in pp:windows.append(dict(variant=c['id'],date=o['date'],contract=o['contract'],minute=tm,reason=why,lower=a,upper=b))
 print('TESTED',c['id'],c['family'],flush=True)
original=np.array([sum(o['original'] for o in ops if o['date']==day) for day in days]);assert np.array_equal(lo[0],original) and np.array_equal(hi[0],original)
months=sorted({d[:7] for d in days});mi=np.array([months.index(d[:7]) for d in days]);yi=np.array([int(d[:4])-2024 for d in days]);yearcounts={y:sum(o['date'].startswith(str(y)) for o in ops) for y in [2024,2025,2026]}
counts=np.array([sum(o['date']==d for o in ops) for d in days]);r61orig=DATA['ops'];R61O=np.array([sum(o['original'] for o in r61orig if o['date']==day and o['level']=='R61.8') for day in days]);r61v=read(E/'fechamento_variante_r61_750_150_20261117/CURVA_DIARIA_VARIANTE_FECHADA.csv');R61N=np.array([float(r['variant_R61_points']) for r in r61v]);assert len(r61v)==len(days) and [r['date'] for r in r61v]==days
r61counts=np.array([sum(o['date']==day and o['level']=='R61.8' for o in r61orig) for day in days])
def dd(a):
 b=np.cumsum(a);return float(np.max(np.maximum.accumulate(np.r_[0,b])[1:]-b))
summary=[];annual=[];monthly=[];combined=[]
for ci,c in enumerate(config):
 a=lo[ci];b=hi[ci];ml=np.bincount(mi,weights=a,minlength=34);row=dict(**c,points_lower=float(a.sum()),points_upper=float(b.sum()),DD_lower=dd(b),DD_upper=dd(a),unresolved=int(pending[ci].sum()),months_positive_lower=int((ml>0).sum()),months_negative_lower=int((ml<0).sum()),worst_month_lower=float(ml.min()),cost5_lower=float(a.sum()-5*233),cost10_lower=float(a.sum()-10*233),training_2024_25_lower=float(a[yi<2].sum()),training_2024_25_upper=float(b[yi<2].sum()))
 for y in [2024,2025,2026]:
  mask=yi==y-2024;row[f'year{y}_lower']=float(a[mask].sum());row[f'year{y}_upper']=float(b[mask].sum())
  annual.append(dict(variant=c['id'],family=c['family'],year=y,scope='JanOut' if y==2026 else 'AnoCompleto',operations=yearcounts[y],lower=float(a[mask].sum()),upper=float(b[mask].sum()),DD_year_lower=dd(b[mask]),DD_year_upper=dd(a[mask]),unresolved=int(pending[ci,mask].sum())))
 for m in range(34):mask=mi==m;monthly.append(dict(variant=c['id'],month=months[m],lower=float(a[mask].sum()),upper=float(b[mask].sum()),unresolved=int(pending[ci,mask].sum())))
 for name,other in [('S61_ISOLADO',np.zeros(len(days))),('COM_R61_ORIGINAL',R61O),('COM_R61_750_150',R61N)]:
  aa=a+other;bb=b+other;nr=233 if name=='S61_ISOLADO' else 488;cr=dict(variant=c['id'],combination=name,lower=float(aa.sum()),upper=float(bb.sum()),DD_lower=dd(bb),DD_upper=dd(aa),operations=nr,unresolved=int(pending[ci].sum()),cost5_lower=float(aa.sum()-5*nr),cost10_lower=float(aa.sum()-10*nr))
  for y in [2024,2025,2026]:mask=yi==y-2024;cr[f'year{y}_lower']=float(aa[mask].sum());cr[f'year{y}_upper']=float(bb[mask].sum())
  combined.append(cr)
 summary.append(row)
write('PARAMETROS_CENARIOS.csv',config);write('RESULTADO_S61_CENARIOS.csv',summary);write('RESULTADO_ANUAL.csv',annual);write('RESULTADO_MENSAL.csv',monthly);write('COMBINACOES_COM_R61.csv',combined);write('LIMITES_POR_OPERACAO.csv',trade);write('PENDENCIAS_POR_VARIANTE.csv',windows);write('PROVAS_MONOTONICAS_ORIGINAL.csv',proofs)
cache=dict(data=DATA,ops=ops,configs=config,lo=lo,hi=hi,pending=pending,summary=summary,annual=annual,monthly=monthly,combined=combined,trade=trade,windows=windows,proofs=proofs)
Path('/workspace/work/estudo_s61/resultados.pickle').write_bytes(pickle.dumps(cache,protocol=4))
result=dict(period='2024Jan-2026Oct',operations=233,days=len(days),scenarios=88,families=dict(collections.Counter(c['family'] for c in config)),saved_Cedro_August_audit_days_found=21,correction='Previous claim of no saved CedroAugustM1 was wrong;files located under cedro_extrator.../retorno_agosto_lote*/M1_CONTRACT_DATE.csv',original_points=float(original.sum()),original_DD=dd(original),source_baseline_mismatches=len(baseline_bad),monotonic_proofs=len(proofs),new_source_original_not_changed=True)
(P/'RESUMO_ESTUDO.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,indent=2),flush=True)
