from pathlib import Path
import csv,pickle,collections,json,hashlib,itertools,datetime
import numpy as np
P=Path(__file__).parent;R=P.parents[1];E=R/'entregas';C=Path('/workspace/work/s23_espera_5min_20261122');C.mkdir(exist_ok=True)
prior=pickle.load(open('/workspace/work/fechamento_s23_cedro_20261119/fechado.pickle','rb'));base=pickle.load(open('/workspace/work/novos_niveis_20261119/resultados.pickle','rb'));data=base['data'];days=data['days'];di={d:i for i,d in enumerate(days)};ops={o['date']:o for o in base['newops'] if o['level']=='S23.6'};trades={r['date']:r for r in prior['trades']};alllv={r['date']:r for r in base['alllevels'] if r['level']=='S23.6'}
assert len(days)==709 and len(trades)==386 and sum(r['lower'] for r in trades.values())==12915 and not any(r['pending'] for r in trades.values())
def read(p):return list(csv.DictReader(p.open(encoding='utf-8-sig'),delimiter=';'))
def write(name,rs):
 if not rs:return
 with (P/name).open('w',encoding='utf-8-sig',newline='') as f:
  keys=list(dict.fromkeys(k for r in rs for k in r));w=csv.DictWriter(f,fieldnames=keys,delimiter=';');w.writeheader();w.writerows(rs)
def ms(t):
 t=t.split(' ')[-1];hh,mm,ss=t.split(':');return int(hh)*3600000+int(mm)*60000+round(float(ss)*1000)
def minute(t):return int(t[:2])*60+int(t[3:5])
def fmt(t):
 t=int(t);return f'{t//3600000:02d}:{t//60000%60:02d}:{t//1000%60:02d}.{t%1000:03d}'
def minute_fmt(t):return f'{t//60:02d}:{t%60:02d}'
# Cedro metadata gives actual first business timestamps for the correct contract in all 63 days.
inventory=read(E/'cedro_extrator_win_v1_00/retorno_geral_20261112/CONTRATOS.csv');opening_exact={}
for d in days:
 symbol=alllv[d]['contract'];rr=[r for r in inventory if r['dia']==d.replace('-','') and r['ativo']==symbol]
 if rr:
  assert len(rr)==1;opening_exact[d]=ms(rr[0]['primeiro_timestamp_na_ordem'])
# Restore the latest five validated Replay minutes as well as prior accepted minute copies.
new_replay=pickle.load(open('/workspace/work/replay_s23_20261119/auditoria.pickle','rb'))['accepted'];replay=dict(data['replay']);replay.update(new_replay)
# Earliest touch is exact for the 13 Cedro days where full-stream checks exposed entry ms.
entry_exact={}
for p in [E/'fechamento_s23_cedro_20261119/CINCO_OPERACOES_RESOLVIDAS.csv']:
 for r in read(p):entry_exact[r['date']]=ms(r['entry_time'])
for r in read(E/'estudo_niveis_auxiliares_20261119/CEDRO_RESULTADOS_CONFIRMADOS.csv'):
 if r['level']=='S23.6' and r['variant']=='N089' and r['resolved']=='True':entry_exact[r['date']]=int(r['entry_ms'])
rows=[];boundary=[];known=np.zeros(709);original=np.zeros(709)
for d in days:
 lv=alllv[d];firstbar=data['bars'][d][0];firstminute=minute(firstbar[0]);opening_price=int(float(base['refs'][d]['open']));assert opening_price==firstbar[1]
 lower=opening_exact.get(d,firstminute*60000);upper=opening_exact.get(d,firstminute*60000+59999)
 assert firstminute*60000<=lower<=upper<(firstminute+1)*60000
 gate_lo=lower+300000;gate_hi=upper+300000
 r=dict(date=d,contract=lv['contract'],opening_price=opening_price,opening_minute=firstbar[0][:5],opening_time_lower=fmt(lower),opening_time_upper=fmt(upper),opening_time_exact=d in opening_exact,activation_lower=fmt(gate_lo),activation_upper=fmt(gate_hi),eligible=lv['eligible'],entry_level=lv['entry'],original_entry_minute='',first_touch_lower='',first_touch_upper='',original_points=0,new_lower=0,new_upper=0,status='INELIGIBLE' if not lv['eligible'] else 'NO_TOUCH',classification_source='FROZEN_ELIGIBILITY_NO_TOUCH')
 if d in trades:
  o=ops[d];t=trades[d];tm=o['entry_minute'];touch_lo=minute(tm)*60000;touch_hi=touch_lo+59999;source='M1_FIRST_TOUCH_MINUTE'
  if d in entry_exact:touch_lo=touch_hi=entry_exact[d];source='VERIFIED_FULL_CEDRO_FIRST_TOUCH'
  elif (d,tm) in replay:
   es=replay[(d,tm)];matches=[ev for ev in es if ev[1]<=lv['entry']];assert matches;touch_lo=touch_hi=ms(matches[0][0]);source='VALIDATED_COMPLETE_REPLAY_FIRST_TOUCH'
  assert minute(tm)*60000<=touch_lo<=touch_hi<(minute(tm)+1)*60000
  pts=t['lower'];assert pts==t['upper'];original[di[d]]=pts
  r.update(original_entry_minute=tm,first_touch_lower=fmt(touch_lo),first_touch_upper=fmt(touch_hi),original_points=pts,classification_source=source)
  # The quote at the activation instant is checked before placing the pending order.
  if touch_hi<=gate_lo:r['status']='CONSUMED_DURING_WAIT'
  elif touch_lo>gate_hi:r.update(status='RETAINED',new_lower=pts,new_upper=pts);known[di[d]]=pts
  else:
   r.update(status='CLOCK_BOUNDARY_PENDING',new_lower=min(0,pts),new_upper=max(0,pts));boundary.append(r)
 rows.append(r)
assert len(boundary)==5
# Exhaust all 2^5 retain/exclude combinations; these are time uncertainty, not exit uncertainty.
possibilities=[];curves=[]
def dd(a):
 b=np.cumsum(a);return float(np.max(np.maximum.accumulate(np.r_[0,b])[1:]-b))
base_retained=[r for r in rows if r['status']=='RETAINED'];indices=[di[r['date']] for r in boundary]
for mask in range(1<<len(boundary)):
 a=known.copy();ct=np.zeros(709,dtype=int)
 for r in base_retained:ct[di[r['date']]]=1
 for i,r in enumerate(boundary):
  if mask>>i&1:a[di[r['date']]]=r['original_points'];ct[di[r['date']]]=1
 selected=[trades[d] for j,d in enumerate(days) if ct[j]];row=dict(case=f'T{mask:02d}',clock_retention_mask=mask,operations=int(ct.sum()),points=float(a.sum()),DD_daily_continuous=dd(a),TP=sum(r['TP_guaranteed'] for r in selected),SL=sum(r['SL_guaranteed'] for r in selected),CUT=sum(r['CUT_guaranteed'] for r in selected))
 for y in [2024,2025,2026]:
  m=np.array([d.startswith(str(y)) for d in days]);row[f'year{y}']=float(a[m].sum());row[f'year{y}_operations']=int(ct[m].sum());row[f'year{y}_DD']=dd(a[m])
 for fee in [5,10]:row[f'points_cost{fee}']=float((a-fee*ct).sum());row[f'DD_cost{fee}']=dd(a-fee*ct)
 streak=best=0
 for r in selected:streak=streak+1 if r['SL_guaranteed'] else 0;best=max(best,streak)
 row['max_consecutive_SL']=best;row['entries_per_TP']=len(selected)/row['TP'] if row['TP'] else '';row['entries_per_SL']=len(selected)/row['SL'] if row['SL'] else ''
 possibilities.append(row);curves.append((a,ct))
summary=dict(period='2024Jan-2026Oct',waiting_ms=300000,opening_anchor='FIRST_ACTUAL_BUSINESS',touch_before_or_at_activation='CONSUMES_OPPORTUNITY_NO_ORDER',order='BUY_LIMIT_AT_S23.6',stop=200,target=500,original_operations=386,original_points=12915,original_DD=4915,consumed=sum(r['status']=='CONSUMED_DURING_WAIT' for r in rows),definitely_retained=len(base_retained),clock_boundary_pending=len(boundary),operations_lower=min(r['operations'] for r in possibilities),operations_upper=max(r['operations'] for r in possibilities),points_lower=min(r['points'] for r in possibilities),points_upper=max(r['points'] for r in possibilities),DD_lower=min(r['DD_daily_continuous'] for r in possibilities),DD_upper=max(r['DD_daily_continuous'] for r in possibilities),opening_time_exact_days=len(opening_exact),time_cases_enumerated=len(possibilities),exit_sequence_pending=0)
annual=[];monthly=[];daily=[]
for y in [2024,2025,2026]:
 mask=np.array([d.startswith(str(y)) for d in days]);annual.append(dict(year=y,scope='JanOut' if y==2026 else 'AnoCompleto',original_operations=sum(d.startswith(str(y)) for d in trades),original_points=float(original[mask].sum()),consumed=sum(r['date'].startswith(str(y)) and r['status']=='CONSUMED_DURING_WAIT' for r in rows),retained_lower=min(r[f'year{y}_operations'] for r in possibilities),retained_upper=max(r[f'year{y}_operations'] for r in possibilities),points_lower=min(r[f'year{y}'] for r in possibilities),points_upper=max(r[f'year{y}'] for r in possibilities),DD_year_lower=min(r[f'year{y}_DD'] for r in possibilities),DD_year_upper=max(r[f'year{y}_DD'] for r in possibilities),clock_pending=sum(r['date'].startswith(str(y)) for r in boundary)))
for m in sorted({d[:7] for d in days}):
 mask=np.array([d.startswith(m) for d in days]);sums=[float(a[mask].sum()) for a,ct in curves];counts=[int(ct[mask].sum()) for a,ct in curves];monthly.append(dict(month=m,original_points=float(original[mask].sum()),operations_lower=min(counts),operations_upper=max(counts),points_lower=min(sums),points_upper=max(sums),DD_lower=min(dd(a[mask]) for a,ct in curves),DD_upper=max(dd(a[mask]) for a,ct in curves)))
for i,d in enumerate(days):daily.append(dict(date=d,original_points=original[i],new_lower=min(a[i] for a,ct in curves),new_upper=max(a[i] for a,ct in curves),status=rows[i]['status']))
requests=[]
for r in boundary:
 for typ,m in [('OPENING_FIRST_BUSINESS',minute(r['opening_minute'])),('FIRST_TOUCH_VS_ACTIVATION',minute(r['original_entry_minute']))]:
  requests.append(dict(date=r['date'],contract=r['contract'],start=minute_fmt(m),end_exclusive=minute_fmt(m+1),purpose=typ,entry_level=r['entry_level'],outcome_if_retained=r['original_points'],capture='Minuto inteiro, alguns segundos de margem, preservar milissegundos e negocios identicos'))
write('DIAGNOSTICO_709_PREGOES.csv',rows);write('RESULTADO_RESUMO.csv',[summary]);write('ANUAL.csv',annual);write('MENSAL.csv',monthly);write('DIARIO_COMPARATIVO.csv',daily);write('32_CENARIOS_RELOGIO.csv',possibilities);write('CINCO_DUVIDAS_DE_HORARIO.csv',boundary);write('REPLAY_DEZ_JANELAS.csv',requests)
(C/'resultados.pickle').write_bytes(pickle.dumps(dict(prior=prior,base=base,rows=rows,boundary=boundary,summary=summary,annual=annual,monthly=monthly,daily=daily,cases=possibilities,curves=curves,requests=requests,known=known,original=original)))
print(json.dumps(dict(summary=summary,annual=annual,cases_extremes=[min(possibilities,key=lambda r:r['points']),max(possibilities,key=lambda r:r['points'])]),ensure_ascii=False,indent=2))
