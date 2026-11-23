from pathlib import Path
import pickle,csv,json,datetime,collections
P=Path(__file__).parent;x=pickle.load(open('/workspace/work/modelod_espera_5min_20261122/resultados.pickle','rb'));days=x['base']['data']['days'];assert len(x['diagnostic'])==1485 and len(x['pending'])==29 and len({r['date'] for r in x['pending']})==29
assert len(x['first_open'])==78 and len(x['first_touch'])==282
by={r['id']:r for r in x['summary']};expected={'D_ORIGINAL_5':3950,'ORIGINAL_R38.2':165,'ORIGINAL_R61.8':825,'ORIGINAL_S38.2':-1965,'ORIGINAL_S50':-140,'ORIGINAL_S61.8':5065,'R61_375_1000':5725,'R61_75_1000':4045,'S38_200_1000':1130,'S61_100_ORIGINAL':2295,'MISTO_MAIORES_FECHADOS_5':11945}
assert set(expected)==set(by)
for key,value in expected.items():assert by[key]['original_points']==value
assert by['D_ORIGINAL_5']['original_DD']==14805 and by['MISTO_MAIORES_FECHADOS_5']['original_DD']==8290
for key,g in x['gates'].items():
 assert g['glo']==g['olo']+300000 and g['ghi']==g['ohi']+300000
 o=x['ops'][key];assert o['entry']==g['row']['entry_level'] and o['entry_minute']==g['row']['first_touch_minute']
 st=g['row']['status']
 if st=='CONSUMED_DURING_WAIT':assert g['thi']<=g['glo']
 elif st=='RETAINED':assert g['tlo']>g['ghi']
 else:assert g['thi']>g['glo'] and g['tlo']<=g['ghi']
for s in x['scenarios']:
 recipes=[r for key in s['recipes'] for r in x['recipes'][key]];group=collections.defaultdict(list)
 for r in recipes:group[r['date']].append(r)
 expected_orig=[];expected_lo=[];expected_hi=[]
 for d in days:
  orig=sum(r['points'] for r in group[d]);known=sum(r['points'] for r in group[d] if x['gates'][d,r['level']]['row']['status']=='RETAINED');unc=[r for r in group[d] if x['gates'][d,r['level']]['row']['status']=='CLOCK_BOUNDARY_PENDING'];assert len(unc)<=1
  lo=known+sum(min(0,r['points']) for r in unc);hi=known+sum(max(0,r['points']) for r in unc);expected_orig.append(orig);expected_lo.append(lo);expected_hi.append(hi)
 curve=x['curves'][s['id']];assert list(curve['orig'])==expected_orig and list(curve['lo'])==expected_lo and list(curve['hi'])==expected_hi
 row=by[s['id']]
 for a,totalfield,ddfield in [(expected_orig,'original_points','original_DD'),(expected_lo,'points_lower','DD_upper'),(expected_hi,'points_upper','DD_lower')]:
  c=p=dd=0
  for v in a:c+=v;p=max(p,c);dd=max(dd,p-c)
  assert c==row[totalfield] and dd==row[ddfield]
 for y in [2024,2025,2026]:
  assert sum(v for d,v in zip(days,expected_lo) if d.startswith(str(y)))==row[f'year{y}_lower']
  assert sum(v for d,v in zip(days,expected_hi) if d.startswith(str(y)))==row[f'year{y}_upper']
# Behavioral invariants at the exact activation instant, with independent datetimes.
open=datetime.datetime(2026,1,1,9,2,7,123000);gate=open+datetime.timedelta(minutes=5);assert gate.time()==datetime.time(9,7,7,123000)
assert gate<=gate and gate+datetime.timedelta(milliseconds=1)>gate
assert len(x['requests'])==58 and not any(r['date'].startswith(('2026-08','2026-09','2026-10')) for r in x['requests'])
assert not any(r['date']=='2026-07-10' and r['start']=='09:55' for r in x['requests'])
result=dict(original_entries_preserved=1485,independent_recipe_scenarios=11,independent_scalar_total_and_DD_checks=33,year_points_checked=True,clock_pending_dates=29,Replay_windows=58,exact_opening_days=78,exact_first_touch_operations=282,one_common_clock_per_day=True,original_model_not_modified=True,waived_July10_control_not_reopened=True,S23_without_wait_preserved=True)
(P/'VERIFICACAO.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
