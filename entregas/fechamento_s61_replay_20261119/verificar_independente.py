from pathlib import Path
import csv,pickle,itertools,json
import numpy as np
P=Path(__file__).parent
rows=list(csv.DictReader((P/'RESOLUCAO_PENDENCIAS.csv').open(encoding='utf-8-sig'),delimiter=';'))
x=pickle.load(open('/workspace/work/estudo_s61/resultados.pickle','rb'));audit=pickle.load(open('/workspace/work/replay_s61_20261119/auditoria.pickle','rb'))
ops={o['date']:o for o in x['ops']};out=[]
for r in rows:
 d=r['date'];o=ops[d];e=float(r['entry']);tp=e+float(r['target_points']);sl=e-float(r['stop_points']);assert o['buy']
 for path_order in [0,1]:
  for reverse in [False,True]:
   active=False;result=None;entry_time=None
   for bar in x['data']['bars'][d]:
    tm=bar[0][:5]
    if tm<o['entry_minute']:continue
    if tm>='18:00':
     assert active;result=bar[1]-e;reason='CORTE';exit_time=tm;exit_price=bar[1];break
    events=audit['accepted'].get((d,tm),x['data']['replay'].get((d,tm)))
    if events is None:
     prices=[bar[1],bar[2],bar[3],bar[4]] if path_order==0 else [bar[1],bar[3],bar[2],bar[4]]
     events=[(tm+f':{i:02d}.000',p,0) for i,p in enumerate(prices)]
    elif reverse:events=[ev for _,g in itertools.groupby(events,key=lambda ev:ev[0]) for ev in reversed(list(g))]
    for t,p,q in events:
     if not active:
      if p<=e:active=True;entry_time=t
      continue
     if p<=sl:result=-float(r['stop_points']);reason='SL'
     elif p>=tp:result=float(r['target_points']);reason='TP'
     if result is not None:exit_time=t;exit_price=p;break
    if result is not None:break
   assert result==float(r['new_lower'])==float(r['new_upper']),(r,path_order,reverse,result)
   if not reverse and path_order==0:out.append(dict(variant=r['variant'],date=d,contract=r['contract'],entry_time=entry_time,exit_time=exit_time if (d,exit_time[:5]) in audit['accepted'] or (d,exit_time[:5]) in x['data']['replay'] else exit_time[:5],exit_trade_price=exit_price,result=reason,points=result,exit_source='REPLAY' if (d,exit_time[:5]) in audit['accepted'] or (d,exit_time[:5]) in x['data']['replay'] else 'M1_UNAMBIGUOUS_PATHS',time_precision='MILLISECOND_REPLAY' if (d,exit_time[:5]) in audit['accepted'] or (d,exit_time[:5]) in x['data']['replay'] else 'MINUTE_ONLY_SYNTHETIC_PATH'))
with (P/'PROVA_NEGOCIO_DE_SAIDA.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(out[0]),delimiter=';');w.writeheader();w.writerows(out)
# Independently derive sums and DD by Python scalars, without numpy engine metrics.
alltr=list(csv.DictReader((P/'OPERACOES.csv').open(encoding='utf-8-sig'),delimiter=';'))
summary=list(csv.DictReader((P/'RESULTADO_TRES_OPCOES.csv').open(encoding='utf-8-sig'),delimiter=';'))
for s in summary:
 rr=[r for r in alltr if r['variant']==s['id']];assert len(rr)==233
 daily={d:0 for d in x['data']['days']}
 for r in rr:assert r['lower']==r['upper'];daily[r['date']]+=float(r['lower'])
 cum=peak=dd=0
 for d,v in sorted(daily.items()):cum+=v;peak=max(peak,cum);dd=max(dd,peak-cum)
 assert cum==float(s['total_lower']) and dd==float(s['DD_upper'])
 for y in [2024,2025,2026]:assert sum(v for d,v in daily.items() if d.startswith(str(y)))==float(s[f'year{y}_lower'])
result=dict(pending_trades_checked=len(rows),independent_runs=len(rows)*4,matching_exit_values=len(rows)*4,chronological_daily_checks=3,zero_remaining_pending=True)
(P/'VERIFICACAO_INDEPENDENTE.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
