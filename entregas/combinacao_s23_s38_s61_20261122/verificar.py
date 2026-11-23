from pathlib import Path
import pickle,csv,json,collections
import numpy as np
P=Path(__file__).parent;x=pickle.load(open('/workspace/work/combinacao_s23_s38_s61_20261122/resultados.pickle','rb'));m=pickle.load(open('/workspace/work/modelod_espera_5min_20261122/resultados.pickle','rb'));days=m['base']['data']['days'];di={d:i for i,d in enumerate(days)}
for s in x['summary']:
 rows=[r for r in x['operations'] if r['case']==s['case']];assert len(rows)==s['operations'] and len({(r['date'],r['level']) for r in rows})==len(rows)
 assert sum(r['level']=='S23.6' for r in rows)==386
 daily=collections.defaultdict(float)
 for r in rows:daily[r['date']]+=r['points']
 c=p=dd=0
 for d in days:c+=daily[d];p=max(p,c);dd=max(dd,p-c)
 assert c==s['points'] and dd==s['DD_continuous']==4855
 for year in [2024,2025,2026]:assert sum(v for d,v in daily.items() if d.startswith(str(year)))==s['year'+str(year)]
pending=[];fixed=np.zeros(709);fixedcount=0
for r in [r for r in x['operations'] if r['case']=='PIOR_TOTAL' and r['level']=='S23.6']:fixed[di[r['date']]]+=r['points'];fixedcount+=1
for key in ['S38_200_1000','S61_100_ORIGINAL']:
 for r in m['recipes'][key]:
  status=m['gates'][r['date'],r['level']]['row']['status']
  if status=='RETAINED':fixed[di[r['date']]]+=r['points'];fixedcount+=1
  elif status=='CLOCK_BOUNDARY_PENDING':pending.append(r)
assert len(pending)==14 and len({r['date'] for r in pending})==14 and fixed.sum()==22540 and fixedcount==852
# Enumerate all 16,384 clock choices in small batches, without summing component DDs.
minpoints=float('inf');maxpoints=-float('inf');mindd=float('inf');maxdd=-float('inf')
for start in range(0,1<<14,256):
 ids=np.arange(start,min(start+256,1<<14),dtype=np.int64);mat=np.tile(fixed,(len(ids),1))
 for i,r in enumerate(pending):mat[:,di[r['date']]]+=((ids>>i)&1)*r['points']
 cumulative=np.cumsum(mat,axis=1);peak=np.maximum.accumulate(np.column_stack([np.zeros(len(ids)),cumulative]),axis=1)[:,1:];dds=np.max(peak-cumulative,axis=1);totals=mat.sum(axis=1)
 minpoints=min(minpoints,float(totals.min()));maxpoints=max(maxpoints,float(totals.max()));mindd=min(mindd,float(dds.min()));maxdd=max(maxdd,float(dds.max()))
assert (minpoints,maxpoints,mindd,maxdd)==(20240,22745,4855,4855)
assert x['summary'][0]['operations']==865 and x['summary'][1]['operations']==853
result=dict(time_choices_verified=16384,pending_dates_independent=14,fixed_operations=852,fixed_points=22540,worst_points=20240,best_points=22745,all_choices_DD_min=4855,all_choices_DD_max=4855,worst_operations=865,best_operations=853,originals_preserved=True)
(P/'VERIFICACAO.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
