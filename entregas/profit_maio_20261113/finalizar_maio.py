"""Freeze May and extend chronological M1+targeted-Replay curve back to May."""
from pathlib import Path
from decimal import Decimal as D
from collections import Counter
import csv,json,zipfile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import fitz
P=Path(__file__).parent;U=P.parent/'profit_junho_20261113';J=P.parent/'profit_winq26_julho_20261113'
def read(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter=';'))
def write(p,rs):
 with p.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rs[0]),delimiter=';',lineterminator='\n');w.writeheader();w.writerows(rs)
s=json.loads((P/'REPLAY_TODAS_ABAS_RESULTADO.json').read_text());ops=read(P/'OPERACOES_POSSIBILIDADES.csv');daily=read(P/'DIARIO_APOS_JANELAS.csv');checks=read(P/'REPLAY_TODAS_ABAS_M1.csv');lookup={(r['date'],r['level']):r for r in s['results']}
assert s['pending_operation_count']==0 and s['resolved_original_pending']==5 and s['grade_controls']==0
assert s['test_points']=='-780' and s['work_points']=='2032.313668'
assert all(r['resolved'] and r['tie_invariant'] and not r['mixed_exit_barrier_ms'] for r in s['results'])
assert all(r['ohlc_match']=='True' and r['quantity_match']=='True' for r in checks if r['full_minute_from_bounds']=='True')
final=[]
for op in ops:
 r=lookup.get((op['date'],op['level']))
 if r:
  pr=r['primary'];reason=pr['reason'];points=pr['points'];basis='REPLAY_PLUS_LATER_CANDLES' if pr['exit_source']=='CANDLES_AFTER_WINDOW' else 'REPLAY_WINDOW';entry=pr['entry']['time'];exit=pr['exit']['time']
 else:
  assert op['determined']=='True';reason,points=op['outcomes'].split(':');basis='M1_DETERMINED';entry=op['entry_minute']+':00_CANDLE';exit=op['exit_candidates']
 final.append(dict(date=op['date'],contract='WINM26',level=op['level'],reason=reason,points=points,basis=basis,entry=entry,exit=exit,work_reason=op['work_reason'],work_points=op['work_points']))
assert len(final)==45 and sum(D(r['points']) for r in final)==D(-780)
write(P/'OPERACOES_FINAIS.csv',final)
flips=Counter((r['work_reason'],r['reason']) for r in final if r['work_reason']!=('ALVO' if r['reason']=='TP' else 'STOP' if r['reason']=='SL' else 'ZERAGEM 18H'))
assert flips=={('ALVO','SL'):4},flips
months={'2026-05':daily,'2026-06':read(U/'DIARIO_APOS_JANELAS.csv'),'2026-07':read(J/'DIARIO_APOS_JANELAS.csv')}
expected={'2026-05':D(-780),'2026-06':D(3405),'2026-07':D(1100)}
tb=tp=td=wb=wp=wd=D(0);curve=[];stats={}
for month,rs in months.items():
 assert [r['date'] for r in rs]==sorted({r['date'] for r in rs})
 assert sum(D(r['test_points']) for r in rs)==expected[month]
 for r in rs:
  tb+=D(r['test_points']);tp=max(tp,tb);td=max(td,tp-tb)
  if r['work_points']!='':wb+=D(r['work_points']);wp=max(wp,wb);wd=max(wd,wp-wb)
  curve.append(dict(date=r['date'],test_points=r['test_points'],test_balance=str(tb),test_current_DD=str(tp-tb),test_max_DD=str(td),work_points=r['work_points'],work_balance=str(wb) if r['work_points']!='' else '',work_max_DD=str(wd) if r['work_points']!='' else ''))
 stats[month]=dict(test_points=str(sum(D(r['test_points']) for r in rs)),work_points=str(sum(D(r['work_points']) for r in rs if r['work_points']!='')),test_DD_accum=str(td),work_DD_accum=str(wd))
assert tb==D(3725) and wb==D('14502.637667')
write(P/'CURVA_MAIO_JUNHO_JULHO_M1_REPLAY.csv',curve)
s.update(final_operation_reasons=dict(Counter(r['reason'] for r in final)),Work_flips=[{'Work':w,'test':t,'count':n} for (w,t),n in flips.items()],ohlc_quantity_matching_minutes=sum(r['ohlc_match']=='True' and r['quantity_match']=='True' for r in checks),partial_boundary_minutes=sum(r['ohlc_match']!='True' or r['quantity_match']!='True' for r in checks),chronological_stats=stats,May_July_test='3725',May_July_Work='14502.637667',no_new_replay_requested=True,series='M1_PLUS_TARGETED_REPLAY_SEPARATE_FROM_FULL_CEDRO')
(P/'RESULTADO_FINAL.json').write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
progress={k:s[k] for k in ('status','operations','test_points','work_points','difference','resolved_original_pending','grade_controls','pending_operation_count','chronological_stats','no_new_replay_requested')}
(P/'PROGRESSO_RESOLUCAO.json').write_text(json.dumps(progress,ensure_ascii=False,indent=2)+'\n')
text=f'''MAIO/2026 — ENCERRADO — MODELO D
RESULTADO PRINCIPAL: -780 pontos,grade5. Work:+2032,313668.
Diferenca:-2812,313668.45operacoes em20pregoes.
Parametros D originais,1contrato/nivel,toqueinclusivo,corte18h.
40resultados determinados emM1+5resolvidos por janelasReplay.
NAO e mes inteiro por negocios nem resultado de preenchimentos reais.
Pontos nos niveis,sem custos/fila/slippage. Nenhuma coleta adicional.

CONFERENCIA
4abas,174927negocios. Semlimite observado200001. Quatro minutos requeridos
conferem OHLC/quantidade;7bordasparciais divergem como esperado. Primeira
cotacao19maio09:03:07.863 coincide com abertura da barra nos dados
exportados;quantidade inteira do minuto confere,nao exigir segundos sem
negocios. Dois desempatesms produzem mesmo motivo/pontos;sem barreiras
TP/SL opostas no mesmo ms nas posicoes. Sem remover negociosidenticos.
TodosWINM26. Ajustes/referencias Work preservados e niveis conferidos.

DESFECHOS
15maioS61.8SL-650;19maioS38.2SL-375 eS50SL-375;
26maioS38.2SL-375;27maioR61.8SL-450.
QuatroALVO Work passaram aSL;19maioS38.2 confirmaSL doWork.
UmSL esta diretamente na copia;outros4determinados pelos candles seguintes
apos resolver cronologia na barra deentrada. SufixoCANDLE indica somente
minuto,nao instante exato da saida. Controles matematicos tambem daoSL.
Regressao testada:nao reutilizar maxima/minima preentrada de barra completa;
barraentrada incompleta nao se resolve por extrema anterior. Cinco casos
pertencem aos conjuntos de desfecho previstos antes de olhar as copias.

DRAWDOWN EM ORDEM CRONOLOGICA MAIO->JUNHO->JULHO
Fechamentos diarios,sem reinicio mensal,na mesma serieM1+Replay.
Ate maio:teste{stats['2026-05']['test_DD_accum']},Work{stats['2026-05']['work_DD_accum']}.
Ate junho:teste{stats['2026-06']['test_DD_accum']},Work{stats['2026-06']['work_DD_accum']}.
Ate julho:teste{stats['2026-07']['test_DD_accum']},Work{stats['2026-07']['work_DD_accum']}.
Junho+3405 eJulho+1100inalterados;so historico/DD ampliados desde maio.
Total serieM1+Replaymaio-julho3725;nao somar como se fosse Cedro integral.
Cedro agosto/outubro ecurva originais intactos,separados e identificados.
Julho10julcontrole dispensado pelo usuario,nao pedir novamente.
PDFenxuto3paginas e tecnico internos para compilacao final.
'''
(P/'LEIA_RESULTADO_FINAL.txt').write_text(text)
def fmt(x):
 if x=='':return '-'
 return f'{D(x):,.2f}'.replace(',','X').replace('.',',').replace('X','.')
pdf=P/'Modelo_D_Maio_Junho_Julho_M1_Replay_Diario.pdf';c=canvas.Canvas(str(pdf),pagesize=A4);W,H=A4
for month,rs in months.items():
 name={'2026-05':'MAIO','2026-06':'JUNHO','2026-07':'JULHO'}[month];st=stats[month]
 c.setFont('Helvetica-Bold',16);c.drawString(35,H-40,f'MODELO D - {name} / 2026')
 c.setFont('Helvetica',9);c.drawString(35,H-59,'M1 + Replay pontual | Grade 5 | Pontos brutos nos niveis')
 c.drawString(35,H-75,'Mes encerrado.' if name!='JULHO' else 'Julho encerrado; controle adicional de 10/07 dispensado pelo usuario.')
 y=H-105;c.setFont('Helvetica-Bold',9)
 for x,t in [(35,'Data'),(205,'Work'),(320,'Nosso'),(445,'Diferenca')]:c.drawString(x,y,t)
 y-=21
 for r in rs:
  c.setFont('Helvetica',9);c.drawString(35,y,r['date'][8:]+'/'+r['date'][5:7]+'/2026')
  for x,k in [(270,'work_points'),(390,'test_points'),(555,'difference')]:c.drawRightString(x,y,fmt(r[k]))
  y-=19
 y-=10;c.setFont('Helvetica-Bold',11);c.drawString(35,y,'TOTAL');c.drawRightString(270,y,fmt(st['work_points']));c.drawRightString(390,y,fmt(st['test_points']));c.drawRightString(555,y,fmt(str(D(st['test_points'])-D(st['work_points']))))
 y-=28;c.setFont('Helvetica',9);c.drawString(35,y,f'DD acumulado desde maio: Work {fmt(st["work_DD_accum"])} | Nosso {fmt(st["test_DD_accum"])}')
 y-=24
 for line in ['DD em ordem maio -> junho -> julho, sobre fechamentos diarios, sem reinicio.','Serie de M1 + Replay pontual, separada dos meses Cedro integral.','Sem custos, fila ou garantia de preenchimento. Traco significa Work indisponivel.']:
  c.drawString(35,y,line);y-=15
 c.showPage()
c.save()
with fitz.open(pdf) as d:
 assert len(d)==3 and '-780,00' in d[0].get_text() and '3.405,00' in d[1].get_text() and '1.100,00' in d[2].get_text()
 for i,rs in enumerate(months.values()):
  t=d[i].get_text()
  for r in rs:assert r['date'][8:]+'/'+r['date'][5:7]+'/2026' in t
tech=P/'Modelo_D_Maio_Junho_Julho_M1_Replay_Tecnico.pdf';c=canvas.Canvas(str(tech),pagesize=A4);y=H-40;c.setFont('Helvetica',9)
for line in text.splitlines():
 if y<40:c.showPage();c.setFont('Helvetica',9);y=H-40
 c.drawString(25,y,line);y-=14
c.save()
with zipfile.ZipFile(P/'Maio_Modelo_D_Resultado.zip','w',zipfile.ZIP_DEFLATED) as z:
 for n in ['LEIA_RESULTADO_FINAL.txt','DIARIO_APOS_JANELAS.csv','OPERACOES_FINAIS.csv','REPLAY_OPERACOES_RESOLVIDAS.csv','PROGRESSO_RESOLUCAO.json',pdf.name,tech.name]:z.write(P/n,n)
print(json.dumps({k:v for k,v in s.items() if k not in ('results','sheets')},ensure_ascii=False,indent=2))
