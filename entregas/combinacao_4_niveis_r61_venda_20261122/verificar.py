from pathlib import Path
import pickle,json,collections
import numpy as np
P=Path(__file__).parent;x=pickle.load(open('/workspace/work/combinacao_4_niveis_r61_venda_20261122/resultados.pickle','rb'));m=pickle.load(open('/workspace/work/modelod_espera_5min_20261122/resultados.pickle','rb'));days=m['base']['data']['days'];di={d:i for i,d in enumerate(days)}
assert len(x['sale'])==255 and sum(r['points'] for r in x['sale'])==5725
for s in x['summary']:
 rr=[r for r in x['operations'] if r['case']==s['case']];assert len(rr)==s['operations'] and len({(r['date'],r['level']) for r in rr})==len(rr)
 assert sum(r['level']=='R61.8' for r in rr)==255 and sum(r['level']=='S23.6' for r in rr)==386
 by=collections.defaultdict(float)
 for r in rr:by[r['date']]+=r['points']
 cumulative=peak=dd=0
 for d in days:cumulative+=by[d];peak=max(peak,cumulative);dd=max(dd,peak-cumulative)
 assert cumulative==s['points'] and dd==s['DD_continuous']
 for year in [2024,2025,2026]:assert sum(v for d,v in by.items() if d.startswith(str(year)))==s[f'year{year}']
 prior=next(r for r in x['prior']['summary'] if r['case']==s['case']);assert s['points']-prior['points']==5725 and s['operations']-prior['operations']==255
# Enumerate the same 14 independent clock decisions with the added fixed sale curve.
fixed=x['sale_curve'].copy();fixedcount=255
for r in x['prior']['operations']:
 if r['case']=='PIOR_TOTAL' and r['level']=='S23.6':fixed[di[r['date']]]+=r['points'];fixedcount+=1
pending=[]
for key in ['S38_200_1000','S61_100_ORIGINAL']:
 for r in m['recipes'][key]:
  status=m['gates'][r['date'],r['level']]['row']['status']
  if status=='RETAINED':fixed[di[r['date']]]+=r['points'];fixedcount+=1
  elif status=='CLOCK_BOUNDARY_PENDING':pending.append(r)
assert len(pending)==14 and len({r['date'] for r in pending})==14 and fixedcount==1107 and fixed.sum()==28265
minpoints=float('inf');maxpoints=-float('inf');mindd=float('inf');maxdd=-float('inf')
for start in range(0,1<<14,256):
 masks=np.arange(start,min(start+256,1<<14),dtype=np.int64);a=np.tile(fixed,(len(masks),1))
 for i,r in enumerate(pending):a[:,di[r['date']]]+=((masks>>i)&1)*r['points']
 cumulative=np.cumsum(a,axis=1);peak=np.maximum.accumulate(np.column_stack([np.zeros(len(masks)),cumulative]),axis=1)[:,1:];dd=np.max(peak-cumulative,axis=1);tot=a.sum(axis=1)
 minpoints=min(minpoints,float(tot.min()));maxpoints=max(maxpoints,float(tot.max()));mindd=min(mindd,float(dd.min()));maxdd=max(maxdd,float(dd.max()))
assert (minpoints,maxpoints,mindd,maxdd)==(25965,28470,7705,7835)
result=dict(clock_choices_checked=16384,new_sale_operations_preserved=255,new_sale_points=5725,exact_shared_pending_dates=14,worst_points=minpoints,best_points=maxpoints,DD_min=mindd,DD_max=maxdd,independent_scalar_daily_curves_checked=2,originals_preserved=True)
(P/'VERIFICACAO.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
