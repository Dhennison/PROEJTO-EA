"""Propagate only proven R61V164August exits; do not certify other new exits."""
from pathlib import Path
import json,csv,pickle,ast
import numpy as np
P=Path(__file__).parent;R=P.parents[1];B=R/'entregas/estudo_saidas_niveis_20261117';src=Path('/workspace/work/estudo_saidas/resultados.pickle');d=pickle.loads(src.read_bytes());days=d['data']['days'];levels=['R38.2','R61.8','S38.2','S50','S61.8'];ix={c['id']:i for i,c in enumerate(d['cfg'])};ci=ix['V164'];dayindex={x:i for i,x in enumerate(days)}
def read(p):
 with p.open(encoding='utf-8-sig') as f:return list(csv.DictReader(f,delimiter=';'))
def write(name,rs):
 with (P/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rs[0]),delimiter=';',lineterminator='\n');w.writeheader();w.writerows(rs)
for r in read(P/'OITO_OPERACOES_REPROCESSADAS.csv'):
 k=dayindex[r['date']];v=float(r['variant_points']);assert d['lo'][ci,k,1]<=v<=d['hi'][ci,k,1];d['lo'][ci,k,1]=d['hi'][ci,k,1]=v;d['uncertain'][ci,k,1]=0
months=sorted({x[:7] for x in days});mi=np.array([months.index(x[:7]) for x in days]);yi=np.array([int(x[:4])-2024 for x in days]);ns=dict(np=np,months=months,mi=mi,yi=yi)
for f in ast.parse((B/'testar_cenarios.py').read_text()).body:
 if isinstance(f,ast.FunctionDef) and f.name in ['dd','metrics']:exec(compile(ast.Module(body=[f],type_ignores=[]),'metrics_frozen','exec'),ns)
annual=[];changed=[];dailyrows=[];monthly=[]
for r in d['scenarios']:
 if r['family']=='SAME_RULE_ALL_LEVELS':use={l:ix[r['id']] for l in range(5)}
 else:use={levels.index(l):ix[v] for l,v in (x.split(':') for x in r['rule'].split('|')) if v!='OFF'}
 if use.get(1)!=ci:continue
 a=np.zeros(len(days));b=np.zeros(len(days));n=u=0
 for l,i in use.items():a+=d['lo'][i,:,l];b+=d['hi'][i,:,l];n+=d['counts'][:,l].sum();u+=d['uncertain'][i,:,l].sum()
 r.update(ns['metrics'](a,b,n,u));changed.append(r.copy());d['scenario_daily'][r['id']]=(a,b)
 for year in range(3):
  mask=yi==year;nn=sum(d['counts'][mask,l].sum() for l in use);uu=sum(d['uncertain'][i,mask,l].sum() for l,i in use.items())
  annual.append(dict(scenario=r['id'],year=str(2024+year),scope='JanOut' if year==2 else 'AnoCompleto',points_lower=float(a[mask].sum()),points_upper=float(b[mask].sum()),DD_year_lower=ns['dd'](b[mask]),DD_year_upper=ns['dd'](a[mask]),operations=int(nn),unresolved_operations=int(uu)))
 for m in range(len(months)):
  mask=mi==m;monthly.append(dict(scenario=r['id'],month=months[m],points_lower=float(a[mask].sum()),points_upper=float(b[mask].sum())))
write('CENARIOS_RELACIONADOS_ATUALIZADOS.csv',changed);write('ANUAIS_CENARIOS_RELACIONADOS_ATUALIZADOS.csv',annual);write('MENSAIS_CENARIOS_RELACIONADOS_ATUALIZADOS.csv',monthly)
Path('/workspace/work/cedro_recuperado/resultados_atualizados.pickle').write_bytes(pickle.dumps(d,protocol=4))
summary=dict(affected_scenarios=len(changed),fully_closed_after_recovery=sum(r['uncertain_trades']==0 for r in changed),only_propagated_change='R61.8 V164 eight August days;others kept as originally bounded',source_files_preserved=True)
(P/'PROPAGACAO_AUDITADA.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(summary)
