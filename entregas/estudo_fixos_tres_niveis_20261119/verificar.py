from pathlib import Path
import pickle,csv,json,collections,zipfile
P=Path(__file__).parent;x=pickle.load(open('/workspace/work/fixos_tres_niveis_20261119/resultados.pickle','rb'))
assert len(x['ops'])==834 and len(x['configs'])==90 and len(x['summary'])==270
old={(o['date'],o['level']):o for o in x['data']['ops']}
for r in x['trades']:
 o=old[(r['date'],r['level'])];assert r['entry']==o['entry'] and r['entry_minute']==o['entry_minute'] and r['contract']==o['contract']
 assert r['lower']<=r['upper'] and -r['stop_points']<=r['lower']<=r['target_points']
 assert r['outcomes'] and (not r['pending'] or len(r['outcomes'].split('|'))>1)
# Recompute every recipe using Python scalar sums/DD in chronological order.
def totals(rr,side):
 daily={d:0 for d in x['days']}
 for r in rr:daily[r['date']]+=r[side]
 total=peak=dd=0
 for v in daily.values():total+=v;peak=max(peak,total);dd=max(dd,peak-total)
 return total,dd
by=collections.defaultdict(list)
for r in x['trades']:by[(r['level'],r['variant'])].append(r)
for s in x['summary']:
 rr=by[(s['level'],s['id'])];assert len(rr)==s['operations']
 for side,ddfield in [('lower','DD_upper'),('upper','DD_lower')]:
  total,dd=totals(rr,side);assert total==s[side] and dd==s[ddfield]
  for y in [2024,2025,2026]:assert sum(r[side] for r in rr if r['date'].startswith(str(y)))==s[f'year{y}_{side}']
for s in x['fixed']:assert s['stop_points']==200 and s['target_points']==500
requests=list(csv.DictReader((P/'S23_200_500_PENDENCIAS_RECLASSIFICADAS.csv').open(encoding='utf-8-sig'),delimiter=';'))
assert len(requests)==10 and sum(r['status']=='REPLAY_SOLICITADO' for r in requests)==5
assert all(r['status']!='REPLAY_SOLICITADO' for r in requests if r['date']>='2026-08-01')
raw=list(csv.DictReader((P/'CEDRO_RESULTADOS_CONFIRMADOS.csv').open(encoding='utf-8-sig'),delimiter=';'));assert len(raw)==213 and sum(r['resolved']=='True' for r in raw)==190
with zipfile.ZipFile(P/'Tabelas_Completas.zip') as z:assert z.testzip() is None
result=dict(frozen_entries_verified=834,tested_recipes_verified=270,trade_scenarios_verified=len(x['trades']),independent_scalar_DD_checks=540,raw_scenarios_checked=213,raw_resolved=190,original_results_unchanged=True,S23_new_Replay_requests=5,S23_existing_Cedro_raw_recovery_windows=5)
(P/'VERIFICACAO.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
