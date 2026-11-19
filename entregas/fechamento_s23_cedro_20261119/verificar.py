from pathlib import Path
import pickle,json,collections,csv,hashlib
P=Path(__file__).parent;x=pickle.load(open('/workspace/work/fechamento_s23_cedro_20261119/fechado.pickle','rb'))
assert len(x['trades'])==386 and not any(r['pending'] for r in x['trades'])
assert sum(r['lower'] for r in x['trades'])==sum(r['points'] for r in x['daily'])==12915
assert [r['date'] for r in x['daily']]==sorted(r['date'] for r in x['daily'])
cumulative=peak=dd=0
for r in x['daily']:
 cumulative+=r['points'];peak=max(peak,cumulative);dd=max(dd,peak-cumulative);assert r['cumulative']==cumulative and r['drawdown']==peak-cumulative
assert dd==x['summary']['DD_daily_continuous']==4915
for year in [2024,2025,2026]:assert sum(r['points'] for r in x['daily'] if r['date'].startswith(str(year)))==x['summary']['year'+str(year)]
f=x['frequency'][0];assert (f['TP_guaranteed'],f['SL_guaranteed'],f['CUT_guaranteed'])==(126,253,7)
assert 126*500-253*200+sum(r['lower'] for r in x['trades'] if r['CUT_guaranteed'])==12915
for r in x['results']:assert r['resolved'] and r['same_ms_order_invariant'] and r['full_direct_cpp_and_python_match'] and r['points']==-200
assert len(x['audits'])==5 and sum(r['full_stream_records'] for r in x['audits'])==26558920
assert all(r['full_stream_records']==r['expected_records'] and r['original_5_states_match'] and r['python_all6_states_match'] for r in x['audits'])
for index in json.loads((P/'INDICE_26_ZIPS_RESTAURADOS.json').read_text()):
 q=Path(index['preserved_path']);assert q.stat().st_size==int(index['bytes']) and hashlib.sha256(q.read_bytes()).hexdigest()==index['sha256']
# Independently recalculate every updated combination curve and continuous DD.
for s in x['combinations']:
 rows=[r for r in x['combo_daily'] if r['label']==s['label']];assert len(rows)==709
 for side,ddfield in [('lower','DD_upper'),('upper','DD_lower')]:
  c=p=d=0
  for r in rows:c+=r[side];p=max(p,c);d=max(d,p-c)
  assert c==s['total_'+side] and d==s[ddfield]
result=dict(closed_operations=386,zero_pending_S23=True,scalar_total_and_daily_DD_verified=True,original_states_preserved=25,full_cpp_vs_python_states_checked=30,new_full_stream_records=26558920,restored_files_hash_verified=26,updated_combinations_checked=3,other_levels_pending_not_closed=16)
(P/'VERIFICACAO.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
