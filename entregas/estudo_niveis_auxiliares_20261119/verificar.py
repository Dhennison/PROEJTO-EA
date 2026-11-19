from pathlib import Path
import ast,csv,pickle,collections,json,math
import numpy as np
P=Path(__file__).parent;x=pickle.load(open('/workspace/work/novos_niveis_20261119/resultados.pickle','rb'))
ns=dict(np=np,data={'bars':{}},replays={},noquote=set())
src=(P/'estudar.py').read_text()
for f in ast.parse(src).body:
 if isinstance(f,ast.FunctionDef) and f.name in ['ticks','evaluate']:exec(compile(ast.Module(body=[f],type_ignores=[]),'engine_check','exec'),ns)
d='2099-01-01';o=dict(date=d,buy=True,entry=100,entry_minute='09:00')
ns['data']['bars'][d]=[('09:00',110,120,95,99,5),('09:01',95,100,85,90,5),('18:00',100,100,100,100,5)]
a,pp=ns['evaluate'](o,15,10);assert a=={('SL',-10),('TP',15)}
p=np.array([110,120,95]);t=np.array([1,2,3]);ns['replays'][(d,'09:00')]=(p,t,p,t)
a,pp=ns['evaluate'](o,15,10);assert a=={('SL',-10)},'pre-entry target must not count'
# Exact sign symmetry between buying and selling.
ns['data']['bars'][d]=[(tm,200-O,200-L,200-H,200-C,q) for tm,O,H,L,C,q in ns['data']['bars'][d]]
p=200-p;ns['replays'][(d,'09:00')]=(p,t,p,t);a,_=ns['evaluate'](o|{'buy':False},15,10);assert a=={('SL',-10)}
ns['replays'].clear();ns['data']['bars'][d]=[('09:00',100,110,99,105,5),('18:00',104,104,104,104,5)];a,_=ns['evaluate'](o,50,30);assert a=={('CUT',4)}
ns['data']['bars'][d].insert(1,('09:02',105,110,101,107,5));a,_=ns['evaluate'](o,50,30);assert ('SL',-30) in a and ('TP',50) in a
# Same millisecond spanning both exit barriers stays unresolved.
ns['replays'][(d,'09:00')]=(np.array([90,120]),np.array([1,1]),np.array([120,90]),np.array([1,1]));assert ns['ticks']((d,'09:00'),100,115,90,1,False) is None
# All original labels, counts and points remain exact.
rows=list(csv.DictReader((P/'ROTULOS_ORIGINAIS_CONFERIDOS.csv').open(encoding='utf-8-sig'),delimiter=';'))
assert len(rows)==1485 and sum(float(r['lower']) for r in rows)==3950
for r in rows:assert r['lower']==r['upper']
# Independently recompute the three reported subset daily curves and DD using Python scalars.
def scalar_dd(values):
 cumulative=peak=dd=0
 for v in values:cumulative+=float(v);peak=max(peak,cumulative);dd=max(dd,peak-cumulative)
 return cumulative,dd
reported=list(csv.DictReader((P/'CANDIDATOS_DESTAQUE.csv').open(encoding='utf-8-sig'),delimiter=';'))
daily=list(csv.DictReader((P/'DIARIO_CANDIDATOS.csv').open(encoding='utf-8-sig'),delimiter=';'))
for r in reported:
 rr=[v for v in daily if v['label']==r['label']];assert len(rr)==709 and [v['date'] for v in rr]==x['data']['days']
 for side,ddfield in [('lower','DD_upper_path'),('upper','DD_lower_path')]:
  total,dd=scalar_dd([v[side] for v in rr]);assert total==float(r[side]) and dd==float(r[ddfield])
  for y in [2024,2025,2026]:assert sum(float(v[side]) for v in rr if v['date'].startswith(str(y)))==float(r[f'year{y}_{side}'])
# Every frequency count includes time exits and ambiguity explicitly.
for r in list(csv.DictReader((P/'FREQUENCIAS_ORIGINAIS.csv').open(encoding='utf-8-sig'),delimiter=';')):
 assert sum(int(r[k+'_guaranteed']) for k in ['SL','TP','CUT'])==int(r['operations'])
proof=list(csv.DictReader((P/'CEDRO_RESULTADOS_CONFIRMADOS.csv').open(encoding='utf-8-sig'),delimiter=';'))
assert len(proof)==965 and sum(r['resolved']=='True' for r in proof)==923
result=dict(synthetic_engine_checks=6,frozen_original_operations=1485,original_points=3950,reported_curves_checked=3,year_and_continuous_DD_checks=True,raw_variant_checks=965,raw_resolved=923)
(P/'VERIFICACAO.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
