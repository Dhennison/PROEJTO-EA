from pathlib import Path
import csv,pickle,json,collections,datetime,itertools
P=Path(__file__).parent;x=pickle.load(open('/workspace/work/s23_espera_5min_20261122/resultados.pickle','rb'))
assert len(x['rows'])==709 and len(x['boundary'])==5 and len(x['cases'])==32
trades={r['date']:r for r in x['prior']['trades']};assert len(trades)==386 and sum(r['lower'] for r in trades.values())==12915
counts=collections.Counter(r['status'] for r in x['rows']);assert counts['CONSUMED_DURING_WAIT']==146 and counts['RETAINED']==235 and counts['CLOCK_BOUNDARY_PENDING']==5
# Independent datetime comparisons of source intervals; no exit or entry is changed.
def t(s):return datetime.datetime.strptime(s,'%H:%M:%S.%f')
for r in x['rows']:
 assert t(r['activation_lower'])-t(r['opening_time_lower'])==datetime.timedelta(minutes=5)
 assert t(r['activation_upper'])-t(r['opening_time_upper'])==datetime.timedelta(minutes=5)
 if r['date'] not in trades:assert r['new_lower']==r['new_upper']==0;continue
 assert r['original_points']==trades[r['date']]['lower']
 if r['status']=='CONSUMED_DURING_WAIT':assert t(r['first_touch_upper'])<=t(r['activation_lower']) and r['new_lower']==r['new_upper']==0
 elif r['status']=='RETAINED':assert t(r['first_touch_lower'])>t(r['activation_upper']) and r['new_lower']==r['new_upper']==r['original_points']
 else:assert not t(r['first_touch_upper'])<=t(r['activation_lower']) and not t(r['first_touch_lower'])>t(r['activation_upper'])
# Toy activation checks, including a touch at the exact activation timestamp.
open=t('09:02:07.123');gate=open+datetime.timedelta(minutes=5);assert gate==t('09:07:07.123')
assert t('09:07:07.122')<=gate and t('09:07:07.123')<=gate and t('09:07:07.124')>gate
assert t('09:08:00.000')+datetime.timedelta(minutes=5)==t('09:13:00.000')
# Rebuild the 32 chronological curves using independent scalar operations.
for case,(a,ct) in zip(x['cases'],x['curves']):
 vals={r['date']:r['original_points'] for r in x['rows'] if r['status']=='RETAINED'}
 for i,r in enumerate(x['boundary']):
  if case['clock_retention_mask']>>i&1:vals[r['date']]=r['original_points']
 cumulative=peak=dd=0
 for d in x['base']['data']['days']:cumulative+=vals.get(d,0);peak=max(peak,cumulative);dd=max(dd,peak-cumulative)
 assert cumulative==case['points'] and dd==case['DD_daily_continuous'] and len(vals)==case['operations']
 for y in [2024,2025,2026]:assert sum(v for d,v in vals.items() if d.startswith(str(y)))==case['year'+str(y)]
 assert len(vals)==case['TP']+case['SL']+case['CUT']
assert max(r['points'] for r in x['cases'])==4915<12915
assert sum(r['original_points'] for r in x['rows'] if r['status']=='CONSUMED_DURING_WAIT')==8600
assert len(x['requests'])==10 and all(r['date']<'2026-08-01' for r in x['requests'])
result=dict(original_frozen_operations=386,original_points=12915,all_days_checked=709,waiting_rule_ms=300000,retained_first_entry_and_exit_unchanged=True,clock_cases_scalar_DD_verified=32,exact_gate_touch_consumes=True,original_results_unchanged=True,upper_new_points_below_original=True,Replay_dates=5,Replay_minutes=10)
(P/'VERIFICACAO.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
