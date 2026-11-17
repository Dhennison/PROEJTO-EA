"""Add four user-supplied operational adjustments without changing prior analyses.
M1 only for these four dates; no fabricated M5 series or Work comparison.
"""
from pathlib import Path
from decimal import Decimal as D
import csv,json,io,zipfile,datetime as dt,collections,sys,ast
P=Path(__file__).resolve().parent;BASE=P.parent;R=BASE.parents[1]
sys.path.insert(0,str(R/'entregas/fechamento_agosto_v1_11/analise'))
from motor_precos import levels
sys.path.insert(0,str(R/'entregas/profit_marco_20261113'))
from analisar_marco import choices
# Reuse the preserved candle branch implementation without executing annual preparation.
source=(BASE/'preparar_2024.py').read_text();tree=ast.parse(source)
node=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='branch')
exec(compile(ast.Module(body=[node],type_ignores=[]),str(BASE/'preparar_2024.py'),'exec'))
adjustments={'2024-01-02':135790,'2024-01-03':134206,'2024-01-04':134398,'2024-01-05':132609}
raw=R/'entregas/arquivo_conversa_20261111/originais/ORIGINAIS_PARTE_005.zip'
with zipfile.ZipFile(raw) as z:blob=z.read(next(n for n in z.namelist() if n.endswith('/EXPORT110_1794243035_5791.zip')))
bs=collections.defaultdict(list)
with zipfile.ZipFile(io.BytesIO(blob)) as z:
 for m in ['202312','202401']:
  n=next(n for n in z.namelist() if n.endswith('/M1_'+m+'.csv'))
  for r in csv.DictReader(io.StringIO(z.read(n).decode('utf-8-sig')),delimiter=';'):
   t=dt.datetime.strptime(r['time'],'%Y.%m.%d %H:%M');bs[t.date()].append((t,*[D(r[k]) for k in ['open','high','low','close']],int(r['real_volume'])))
for b in bs.values():b.sort()
def write(name,rs):
 with (P/name).open('w',encoding='utf-8-sig',newline='') as f:
  fields=list(rs[0]) if rs else ['estado'];w=csv.DictWriter(f,fieldnames=fields,delimiter=';',lineterminator='\n');w.writeheader();w.writerows(rs)
ops=[];refs=[];windows=[];summary=[];audits=[]
for date,a in adjustments.items():
 day=dt.date.fromisoformat(date);prior=max(d for d in bs if d<day);pb=bs[prior];b=bs[day]
 assert len(b)==565 and b[0][0].strftime('%H:%M')=='09:00' and b[-1][0].strftime('%H:%M')=='18:24'
 assert all(y[0]-x[0]==dt.timedelta(minutes=1) for x,y in zip(b,b[1:]))
 assert len(pb)==565 and pb[0][0].strftime('%H:%M')=='09:00' and pb[-1][0].strftime('%H:%M')=='18:24'
 ref=dict(open=str(b[0][1]),high_prev=str(max(x[2] for x in pb)),low_prev=str(min(x[3] for x in pb)),close_prev=str(pb[-1][4]),adjustment=str(a))
 refs.append(dict(date=date,contract='WING24',previous=str(prior),previous_source='MT5_WIN$N_M1_FULL',adjustment_source='USUARIO_MENSAGEM_2026-11-17',**ref))
 audits.append(dict(date=date,bars=len(b),first=str(b[0][0]),last=str(b[-1][0]),internal_gaps=0,previous=str(prior),previous_bars=len(pb),M5_independent='AUSENTE_02A04;PARCIAL_05',Work='SEM_REFERENCIA'))
 for lev in levels(ref):
  if not lev['eligible']:continue
  g=branch(b,lev,True);m=branch(b,lev,False)
  if g is None:continue
  reasons={v.split(':')[0] for v in m['outcomes'].split('|')} if m else {'SEM_ENTRADA'}
  grade=g['determined'] and reasons!={g['outcomes'].split(':')[0]}
  ops.append(dict(date=date,level=lev['name'],contract='WING24',entry=str(lev['entry5']),tp=str(lev['tp5']),sl=str(lev['sl5']),**{k:v for k,v in g.items() if k!='asks'},mathematical=m['outcomes'] if m else 'SEM_ENTRADA',grade_control=grade,source='M1_MT5;AJUSTE_USUARIO;SEM_WORK'))
  requests=[]
  if not g['determined']:requests=[(dt.datetime.combine(day,dt.time.fromisoformat(x['minute'])),'SEQUENCIA') for x in g['asks']]
  elif grade:requests=[(dt.datetime.combine(day,dt.time.fromisoformat(g['entry_minute'])) if m is None else dt.datetime.fromisoformat(g['exit_candidates'].split('|')[0].split('@')[1]),'CONTROLE_GRADE5')]
  for t,kind in requests:windows.append(dict(data=date,contrato='WING24',inicio=t.strftime('%H:%M:%S'),fim_exclusivo=(t+dt.timedelta(minutes=1)).strftime('%H:%M:%S'),niveis=lev['name'],tipo=kind))
 oo=[o for o in ops if o['date']==date]
 summary.append(dict(date=date,adjustment=a,operations=len(oo),determined=sum(o['determined'] for o in oo),ambiguous=sum(not o['determined'] for o in oo),grade_controls=sum(o['grade_control'] for o in oo),points_if_all_determined=str(sum(D(o['min_points']) for o in oo)) if all(o['determined'] for o in oo) else 'PENDENTE',closed=False))
write('AJUSTES_USUARIO.csv',[dict(date=d,adjustment=a,source='Mensagem do usuario em17/11/2026;nao validado contra boletim independente') for d,a in adjustments.items()]);write('REFERENCIAS.csv',refs);write('OPERACOES_POSSIBILIDADES.csv',ops);write('JANELAS_POR_OPERACAO.csv',windows);write('RESUMO_POR_DATA.csv',summary);write('AUDITORIA_M1.csv',audits)
(P/'RESULTADO.json').write_text(json.dumps(dict(summary=summary,operations=ops,new_windows=windows,monthly_closed=False,method='M1_MT5_PLUS_USER_ADJUSTMENT;NO_INDEPENDENT_M5_FOR_FULL_PERIOD;NOT_FULL_TICK_AUDIT'),ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(summary=summary,new_windows=windows),ensure_ascii=False,indent=2))
