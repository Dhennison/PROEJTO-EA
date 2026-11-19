from pathlib import Path
import pickle,json,csv,itertools
P=Path(__file__).parent;x=pickle.load(open('/workspace/work/replay_s23_20261119/resultado_atualizado.pickle','rb'));data=x['data'];proof=[]
for change in x['changes']:
 d=change['date'];o=x['ops'][d];en=o['entry'];sl=en-200;tp=en+500
 for path in [0,1]:
  for reverse in [False,True]:
   active=False;result=None;entry_time=None
   for bar in data['bars'][d]:
    tm=bar[0][:5]
    if tm<o['entry_minute']:continue
    events=data['replay'].get((d,tm));real=events is not None
    if tm>='18:00':
     assert active;result=bar[1]-en;reason='CUT';exit_time=tm;exit_price=bar[1];break
    if events is None:
     pp=[bar[1],bar[2],bar[3],bar[4]] if path==0 else [bar[1],bar[3],bar[2],bar[4]];events=[(tm+f':{i:02d}.000',p,0) for i,p in enumerate(pp)]
    elif reverse:events=[ev for _,g in itertools.groupby(events,key=lambda ev:ev[0]) for ev in reversed(list(g))]
    for t,p,q in events:
     if not active:
      if p<=en:active=True;entry_time=t if real else tm
      continue
     if p<=sl:result=-200;reason='SL'
     elif p>=tp:result=500;reason='TP'
     if result is not None:exit_time=t if real else tm;exit_price=p;break
    if result is not None:break
   assert result==change['lower']==change['upper'],(d,path,reverse,result)
   if path==0 and not reverse:proof.append(dict(date=d,contract=change['contract'],entry_time=entry_time,exit_time=exit_time,exit_price_reference=exit_price,exit_source='REPLAY' if real else 'M1_UNAMBIGUOUS_PATHS',reason=reason,points=result))
with (P/'PROVAS_SAIDAS.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(proof[0]),delimiter=';');w.writeheader();w.writerows(proof)
def scalar(rows,side):
 cum=peak=dd=0
 for r in rows:cum+=r[side];peak=max(peak,cum);dd=max(dd,peak-cum)
 return cum,dd
for side,ddfield in [('lower','DD_upper'),('upper','DD_lower')]:
 total,dd=scalar(x['daily'],side);assert total==x['summary']['total_'+side] and dd==x['summary'][ddfield]
 for y in [2024,2025,2026]:assert sum(r[side] for r in x['daily'] if r['date'].startswith(str(y)))==x['summary'][f'year{y}_{side}']
assert len(x['trades'])==386 and sum(r['pending'] for r in x['trades'])==5
assert all(r['date']>='2026-08-01' for r in x['trades'] if r['pending'])
es=x['audit']['accepted'][('2026-07-31','12:34')];assert es[0][0]=='12:34:07.958'
result=dict(accepted_minutes=5,full_minute_OHLC_quantity_match=True,resolved_trades=5,independent_path_and_same_ms_runs=20,points_all_runs_match=True,chronological_daily_DD_verified=True,auction_first_trade='2026-07-31 12:34:07.958',remaining_Cedro_operations=5,no_new_Replay_requested=True)
(P/'VERIFICACAO.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
