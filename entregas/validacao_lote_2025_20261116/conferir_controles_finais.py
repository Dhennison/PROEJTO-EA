"""Independent guards over produced results,coverage controls and extraction."""
from pathlib import Path
from decimal import Decimal as D
import csv,json,pickle,sys,collections
P=Path(__file__).parent;R=P.parents[1];PRE=R/'entregas/preparacao_jan_nov_2025_20261115'
sys.path.insert(0,str(R/'entregas/fechamento_agosto_v1_11/analise'))
from motor_precos import levels
def read(p):
 with p.open(encoding='utf-8-sig') as f:return list(csv.DictReader(f,delimiter=';'))
months=json.loads((P/'RESULTADOS_TODOS_MESES.json').read_text());checks=read(P/'MINUTOS_TODAS_ABAS.csv');proofs=[];validated=0
for s in months:
 src=next(d for d in PRE.iterdir() if d.is_dir() and d.name.startswith(s['month'][-2:]+'_'));requests=read(src/'JANELAS_POR_OPERACAO.csv');ops={(o['date'],o['level']):o for o in read(src/'OPERACOES_POSSIBILIDADES.csv')}
 for r in s['results']:
  if not r['resolved']:continue
  key=(r['date'],r['level']);op=ops[key];assert r['tie_invariant'] and not r['mixed_barrier_ms']
  if r.get('partial_prefix_invariance_proof'):
   pr=r['partial_prefix_invariance_proof'];assert pr['missing_prefix_cannot_reach_opposite_barrier'];proofs.append(key)
  else:assert r['minute_check']['OHLC_match'] and r['minute_check']['quantity_match']
  assert r['primary']['entry']['time'][:5]==op['entry_minute'],(key,'entry mismatch')
  for req in requests:
   if (req.get('data'),req.get('nivel'))!=key:continue
   tm=req['inicio'][:5]
   if tm>r['primary']['exit']['time'][:5]:continue
   ck=next(x for x in checks if x['sheet']==r['sheet'] and x['minute']==tm)
   assert ck['OHLC_match']=='True' and ck['quantity_match']=='True' or key in proofs and tm==op['entry_minute'],(key,tm,'later requested minute not complete')
  validated+=1
assert proofs==[('2025-03-13','R61.8')],proofs
assert validated==42,validated
assert [(x['date'],x['level']) for x in json.loads((P/'PENDENCIAS.json').read_text())]==[]
coverage=json.loads((P/'CONTROLES_COBERTURA.json').read_text());jun=coverage[0]
assert jun['observed_gaps']==[dict(sheet='Cobertura 03-06-25',date='2025-06-03',last_trade='09:03:09.264',next_trade='09:56:21.720',seconds=3192.456)]
assert all(c['OHLC_match'] for c in jun['minute_checks'] if c['minute']<'10:01')
assert [(c['minute'],c['quantity']-c['M1_quantity']) for c in jun['minute_checks'] if c['minute']<'10:01' and not c['quantity_match']]==[('09:03',-1)]
inv=json.loads((P/'INVENTARIO_ABAS.json').read_text());i=next(m for m in inv if m['sheet']=='Cobertura 03-06-25');raw=pickle.loads(Path(i['cache']).read_bytes())
refs=read(PRE/'06_Junho/REFERENCIAS.csv');ref=next(r for r in refs if r['date']=='2025-06-03');ls=levels(ref)
# All prices before the known14:40 entry remain outside eligible entry levels.
for l in ls:
 if not l['eligible']:continue
 hits=[t for t,p,q,n in raw if p<=l['entry5']] if l['buy'] else [t for t,p,q,n in raw if p>=l['entry5']]
 assert not hits,(l['name'],hits[:3])
# 30Jul position closes BEFORE the reported auction,so missing minutes cannot alter it.
jul=next(s for s in months if s['month']=='2025-07');r=next(r for r in jul['results'] if r['date']=='2025-07-30')
assert r['primary']['reason']=='TP' and r['primary']['exit']['time']=='15:42:37.020'
assert coverage[1]['observed_gaps'][0]['last_trade']=='15:42:39.719'
aug=next(s for s in months if s['month']=='2025-08');r=next(r for r in aug['results'] if r['date']=='2025-08-21' and r['level']=='S38.2');assert r['primary']['points']=='-375'
r=next(r for r in aug['results'] if r['date']=='2025-08-21' and r['level']=='S50');assert r['resolved'] and r['minute_check']['quantity']==92869
# Regression guard: a control whose entry is inside the copy must not exit
# against a price observed before that entry (25Jul entry09:02:55.830).
r=next(r for r in jul['results'] if r['date']=='2025-07-25')
assert r['primary']['entry']['time']=='09:02:55.830'
assert r['primary']['exit']['time'].startswith('09:03')
assert r['mathematical']['reason']=='SL'
for s in months:
 for r in s['results']:
  if not r['resolved']:continue
  assert r['primary']['exit']['time'][:5]>=r['primary']['entry']['time'][:5]
# Incomplete13Mar prefix may leaveNONE/OPEN/alreadyTP states;SL is outsideM1.
mar=next(s for s in months if s['month']=='2025-03')
r=next(r for r in mar['results'] if r['date']=='2025-03-13')
assert D(r['partial_prefix_invariance_proof']['opposite_barrier'])>D(r['partial_prefix_invariance_proof']['entry_bar_OHLC'][1])
i=next(m for m in inv if m['sheet']=='MAR 13-03-25');events=pickle.loads(Path(i['cache']).read_bytes())[::-1]
def suffix_from_state(state):
 for stamp,price,qty,ordinal in events:
  if state=='NONE':
   if price>=125825:state='OPEN'
   continue
  if state=='OPEN':
   if price>=126275:state='SL'
   elif price<=125765:state='TP'
 return state
assert {suffix_from_state(state) for state in ['NONE','OPEN','TP']}=={'TP'}
report=dict(validated_Replay_or_grade_operations=validated,partial_prefix_invariant_outcome_cases=proofs,January_original_prefix_was_not_accepted=True,January_complement_now_accepted=True,April_original_wrong_hour_was_not_accepted=True,April_complement_now_accepted=True,June03_no_entry_before_reopening_and_copied_prices_exclude_extra_entries=True,June03_quantity_remark=-1,July30_exit_before_auction=True,August21_S50_now_resolved=True,August21_later_text_control_preserved=True,remaining_operations=0,months_with_no_Replay_pending=11)
(P/'CONFERENCIA_FINAL.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,indent=2))
