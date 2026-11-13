"""Freeze June result and chronological June-July curve within M1+Replay series."""
from pathlib import Path
from decimal import Decimal as D
import csv,json,zipfile
from collections import Counter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import fitz
P=Path(__file__).parent;J=P.parent/'profit_winq26_julho_20261113'
def read(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter=';'))
def write(p,rows):
 with p.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter=';',lineterminator='\n');w.writeheader();w.writerows(rows)
s=json.loads((P/'REPLAY_TODAS_ABAS_RESULTADO.json').read_text());ops=read(P/'OPERACOES_POSSIBILIDADES.csv');daily=read(P/'DIARIO_APOS_JANELAS.csv');checks=read(P/'REPLAY_TODAS_ABAS_M1.csv');lookup={(r['date'],r['level']):r for r in s['results']}
assert s['pending_operation_count']==0 and s['resolved_original_pending']==8 and s['grade_controls']==1
assert s['test_points']=='3405' and s['work_points']=='7214.523331'
assert all(r['resolved'] and r['tie_invariant'] and not r['mixed_exit_barrier_ms'] for r in s['results'])
assert all(r['ohlc_match']=='True' and r['quantity_match']=='True' for r in checks if r['full_minute_from_bounds']=='True')
final=[]
for op in ops:
 key=(op['date'],op['level']);r=lookup.get(key)
 if r:
  pr=r['primary'];reason=pr['reason'];points=pr['points'];basis='REPLAY_PLUS_LATER_CANDLES' if pr['exit_source']=='CANDLES_AFTER_WINDOW' else 'REPLAY_WINDOW';entry=pr['entry']['time'];exit=pr['exit']['time']
 else:
  assert op['determined']=='True';reason,points=op['outcomes'].split(':');basis='M1_DETERMINED';entry=op['entry_minute']+':00_CANDLE';exit=op['exit_candidates']
 final.append(dict(date=op['date'],contract='WINM26' if op['date']<'2026-06-17' else 'WINQ26',level=op['level'],reason=reason,points=points,basis=basis,entry=entry,exit=exit,work_reason=op['work_reason'],work_points=op['work_points']))
assert len(final)==43 and sum(D(r['points']) for r in final)==D(3405)
write(P/'OPERACOES_FINAIS.csv',final)
flips=Counter((r['work_reason'],r['reason']) for r in final if r['work_reason']!=('ALVO' if r['reason']=='TP' else 'STOP' if r['reason']=='SL' else 'ZERAGEM 18H'))
assert flips=={('ALVO','SL'):7,('STOP','TP'):1,('ZERAGEM 18H','TP'):1},flips
# One curve for this shared candle+targeted-Replay methodology, not merged with Cedro tape.
months={'2026-06':daily,'2026-07':read(J/'DIARIO_APOS_JANELAS.csv')};tb=tp=td=wb=wp=wd=D(0);curve=[];stats={}
for month,rs in months.items():
 for r in rs:
  tb+=D(r['test_points']);tp=max(tp,tb);td=max(td,tp-tb)
  if r['work_points']!='':wb+=D(r['work_points']);wp=max(wp,wb);wd=max(wd,wp-wb)
  curve.append(dict(date=r['date'],test_points=r['test_points'],test_balance=str(tb),test_current_DD=str(tp-tb),test_max_DD=str(td),work_points=r['work_points'],work_balance=str(wb) if r['work_points']!='' else '',work_max_DD=str(wd) if r['work_points']!='' else ''))
 stats[month]=dict(test_points=str(sum(D(r['test_points']) for r in rs)),work_points=str(sum(D(r['work_points']) for r in rs if r['work_points']!='')),test_DD_accum=str(td),work_DD_accum=str(wd))
assert tb==D(4505) and wb==D('12470.323999')
write(P/'CURVA_JUNHO_JULHO_M1_REPLAY.csv',curve)
s.update(final_operation_reasons=dict(Counter(r['reason'] for r in final)),Work_flips=[{'Work':w,'test':t,'count':n} for (w,t),n in flips.items()],ohlc_quantity_matching_minutes=sum(r['ohlc_match']=='True' and r['quantity_match']=='True' for r in checks),partial_boundary_minutes=sum(r['ohlc_match']!='True' or r['quantity_match']!='True' for r in checks),chronological_stats=stats,June_July_test='4505',June_July_Work='12470.323999',no_new_replay_requested=True,series='M1_PLUS_TARGETED_REPLAY_SEPARATE_FROM_FULL_CEDRO',grade_effects='22junS38.2:WorkSL mas grade5TP;23junR38.2:Workcorte mas grade5TP. Niveis matematicos controle reproduzem motivosWork.')
(P/'RESULTADO_FINAL.json').write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
(P/'PROGRESSO_RESOLUCAO.json').write_text(json.dumps({k:s[k] for k in ('status','operations','test_points','work_points','difference','resolved_original_pending','grade_controls','pending_operation_count','chronological_stats','no_new_replay_requested')},ensure_ascii=False,indent=2)+'\n')
text=f'''JUNHO/2026 — ENCERRADO — MODELO D
RESULTADO PRINCIPAL: +3.405 pontos,na grade5. Work:+7.214,523331.
Diferenca:-3.809,523331.43operacoes em21pregoes.
Parametros originais,1contrato por nivel,toque inclusivo,corte18h.
Niveis creditados,sem custos/fila/slippage ou certificacao de fills reais.
34resultados determinados nos candles+8ambiguidades Replay+1controle grade.
Nao e mes integral tick a tick. Zero operacoes pendentes. Nenhuma nova coleta.

AUDITORIA
5abas,278766negocios,sem atingir limite observado200001.7minutos completos
reconstituem OHLC/quantidade do CSV.10bordasparciais esperadas;sem divergencia
em minutos integralmente cobertos. Entradas das8operacoes,agrupadas em6minutos,e minuto17:00 do controle
conferem. Dois desempates de ms com mesmo resultado,
sem barreirasTP/SL opostas no mesmo ms dentro das posicoes investigadas.
Sem deduplicar registros. ContratosM26ate16jun,Q26desde17jun.

RESULTADOS DOS CASOS
03jun:tres suportesSL;15junR61.8SL;22junS38.2TP,S50SL,S61.8SL;
30junS38.2SL.23junR38.2TP na grade5,preco174245,17:00:35.664.
SeteALVO Work viramSL. UmSTOP viraTP e umaZERAGEM18H viraTP.
Doisultimos casos sao efeitos da grade5:execucao matematica mantemSTOP
em22junS38.2 eZERAGEM55,092 em23junR38.2. Nao selecionar variante pelo ganho.
Saidas posteriores a janela verificadas em candles sem ambiguidade;
sufixoCANDLE marca minuto,nao segundo exato. Regressao:nao reutilizar
maxima/minima pre-entrada de barra ja inteiramente coletada. Testes passaram.

DRAWDOWN E CONTINUIDADE
Curva M1+Replay calculada em junho->julho,sem reinicio. JunhoDDteste:
{stats['2026-06']['test_DD_accum']};Work:{stats['2026-06']['work_DD_accum']}.
JulhoDDacumulado aposjunho:teste{stats['2026-07']['test_DD_accum']},
Work{stats['2026-07']['work_DD_accum']}. Julho continua+1100;soDDatualizado.
Cedro integral agosto/setembro/outubro permanece serie separada e intacta.
Julho controle10juldispensado usuario,nao pedir novamente. Fontes preservadas.
PDFs M1+Replay enxuto(2paginas) e tecnico salvos internamente,para compilacao
final com meses identificados por fonte/metodo. Sem PDF misturando curvasDD.
'''
(P/'LEIA_RESULTADO_FINAL.txt').write_text(text)
def fmt(x):
 if x=='':return '-'
 return f'{D(x):,.2f}'.replace(',','X').replace('.',',').replace('X','.')
pdf=P/'Modelo_D_Junho_Julho_M1_Replay_Diario.pdf';c=canvas.Canvas(str(pdf),pagesize=A4);W,H=A4
for month,rs in months.items():
 name='JUNHO' if month.endswith('06') else 'JULHO';st=stats[month]
 c.setFont('Helvetica-Bold',16);c.drawString(35,H-40,f'MODELO D - {name} / 2026')
 c.setFont('Helvetica',9);c.drawString(35,H-59,'M1 + Replay pontual | Grade 5 | Pontos brutos nos niveis')
 c.drawString(35,H-75,'Junho encerrado.' if name=='JUNHO' else 'Julho encerrado; controle adicional de 10/07 dispensado pelo usuario.')
 y=H-105;c.setFont('Helvetica-Bold',9)
 for x,t in [(35,'Data'),(205,'Work'),(320,'Nosso'),(445,'Diferenca')]:c.drawString(x,y,t)
 y-=21
 for r in rs:
  c.setFont('Helvetica',9);c.drawString(35,y,r['date'][8:]+'/'+r['date'][5:7]+'/2026')
  for x,k in [(270,'work_points'),(390,'test_points'),(555,'difference')]:c.drawRightString(x,y,fmt(r[k]))
  y-=19
 y-=10;c.setFont('Helvetica-Bold',11);c.drawString(35,y,'TOTAL');c.drawRightString(270,y,fmt(st['work_points']));c.drawRightString(390,y,fmt(st['test_points']));c.drawRightString(555,y,fmt(str(D(st['test_points'])-D(st['work_points']))))
 y-=28;c.setFont('Helvetica',9);c.drawString(35,y,f'DD acumulado desde junho: Work {fmt(st["work_DD_accum"])} | Nosso {fmt(st["test_DD_accum"])}')
 y-=24
 for line in ['DD em ordem junho -> julho, sobre fechamentos diarios, sem reinicio.','Serie de M1 + Replay pontual, separada dos meses Cedro integral.','Sem custos, fila ou garantia de preenchimento. Traco significa Work indisponivel.']:
  c.drawString(35,y,line);y-=15
 c.showPage()
c.save()
with fitz.open(pdf) as d:
 assert len(d)==2 and '3.405,00' in d[0].get_text() and '1.100,00' in d[1].get_text()
tech=P/'Modelo_D_Junho_Julho_M1_Replay_Tecnico.pdf';c=canvas.Canvas(str(tech),pagesize=A4);y=H-40;c.setFont('Helvetica',9)
for line in text.splitlines():
 if y<40:c.showPage();c.setFont('Helvetica',9);y=H-40
 c.drawString(25,y,line);y-=14
c.showPage();c.setFont('Helvetica-Bold',13);c.drawString(30,H-40,'JULHO - CONTINUIDADE APOS INCLUIR JUNHO');c.setFont('Helvetica',10);y=H-70
for line in [f'Resultado de julho preservado: +1.100 pontos.',f'DD acumulado teste: {fmt(stats["2026-07"]["test_DD_accum"])} pontos.',f'DD acumulado Work: {fmt(stats["2026-07"]["work_DD_accum"])} pontos.','Curva de junho e julho: mesma metodologia M1 + Replay pontual.','Controle de 10/07 dispensado expressamente; ressalva preservada.','Agosto a outubro Cedro: calculos e curva originais preservados.']:
 c.drawString(30,y,line);y-=19
c.save()
with zipfile.ZipFile(P/'Junho_Modelo_D_Resultado.zip','w',zipfile.ZIP_DEFLATED) as z:
 for n in ['LEIA_RESULTADO_FINAL.txt','DIARIO_APOS_JANELAS.csv','OPERACOES_FINAIS.csv','REPLAY_OPERACOES_RESOLVIDAS.csv','PROGRESSO_RESOLUCAO.json',pdf.name,tech.name]:z.write(P/n,n)
print(json.dumps({k:v for k,v in s.items() if k not in ('results','sheets')},ensure_ascii=False,indent=2))
