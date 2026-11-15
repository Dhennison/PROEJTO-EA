"""Freeze March using saved M1 decisions and audited targeted Replay; preserve prior months."""
from pathlib import Path
from decimal import Decimal as D
from collections import Counter
import csv,json,hashlib,shutil,zipfile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import fitz
P=Path(__file__).parent

def read(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter=';'))
def write(p,rs):
 with p.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rs[0]),delimiter=';',lineterminator='\n');w.writeheader();w.writerows(rs)
s=json.loads((P/'REPLAY_TODAS_ABAS_RESULTADO.json').read_text());ops=read(P/'OPERACOES_POSSIBILIDADES.csv');checks=read(P/'REPLAY_TODAS_ABAS_M1.csv');daily=read(P/'DIARIO_APOS_JANELAS.csv')
assert s['pending_operation_count']==0 and s['resolved_original_pending']==4 and s['grade_controls']==1
assert all(r['resolved'] and r['tie_invariant'] and not r['mixed_exit_barrier_ms'] for r in s['results'])
assert all(r['ohlc_match']=='True' and r['quantity_match']=='True' for r in checks if r['full_minute_from_bounds']=='True')
assert sum(r['full_minute_from_bounds']=='True' for r in checks)==5
lookup={(r['date'],r['level']):r['primary'] for r in s['results']};final=[]
for o in ops:
 pr=lookup.get((o['date'],o['level']))
 if pr:reason,points=pr['reason'],pr['points'];basis=pr['exit_source'];en=pr['entry']['time'];ex=pr['exit']['time']
 else:
  assert o['determined']=='True';reason,points=o['outcomes'].split(':');basis='M1_DETERMINED';en=o['entry_minute']+':00_CANDLE';ex=o['exit_candidates']
 final.append(dict(date=o['date'],contract='WINJ26',level=o['level'],reason=reason,points=points,basis=basis,entry=en,exit=ex,work_reason=o['work_reason'],work_points=o['work_points']))
assert len(final)==50 and sum(D(r['points']) for r in final)==D(350)
write(P/'OPERACOES_FINAIS.csv',final)
months={'2026-03':daily}
for name,month in [('abril','04'),('maio','05'),('junho','06'),('winq26_julho','07')]:months['2026-'+month]=read(P.parent/f'profit_{name}_20261113/DIARIO_APOS_JANELAS.csv')
expected=[D(350),D(5720),D(-780),D(3405),D(1100)];tb=tp=td=wb=wp=wd=D(0);curve=[];stats={}
for (month,rs),expect in zip(months.items(),expected):
 assert sum(D(r['test_points']) for r in rs)==expect
 assert [r['date'] for r in rs]==sorted(set(r['date'] for r in rs))
 for r in rs:
  tb+=D(r['test_points']);tp=max(tp,tb);td=max(td,tp-tb)
  if r['work_points']!='':wb+=D(r['work_points']);wp=max(wp,wb);wd=max(wd,wp-wb)
  curve.append(dict(date=r['date'],test_points=r['test_points'],test_balance=str(tb),test_current_DD=str(tp-tb),test_max_DD=str(td),work_points=r['work_points'],work_balance=str(wb) if r['work_points']!='' else '',work_max_DD=str(wd) if r['work_points']!='' else ''))
 stats[month]=dict(test_points=str(expect),work_points=str(sum(D(r['work_points']) for r in rs if r['work_points']!='')),test_DD_accum=str(td),work_DD_accum=str(wd))
assert tb==9795
write(P/'CURVA_MARCO_ABRIL_MAIO_JUNHO_JULHO_M1_REPLAY.csv',curve)
s.update(final_operation_reasons=dict(Counter(r['reason'] for r in final)),chronological_stats=stats,March_July_test=str(tb),March_July_Work=str(wb),no_new_replay_requested=True,series='M1_PLUS_TARGETED_REPLAY_SEPARATE_FROM_CEDRO',complete_matching_minutes=5,partial_boundary_minutes=8)
(P/'RESULTADO_FINAL.json').write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
(P/'PROGRESSO_RESOLUCAO.json').write_text(json.dumps({k:v for k,v in s.items() if k not in ('results','sheets')},ensure_ascii=False,indent=2)+'\n')
text='''MARÇO/2026 — MODELO D ENCERRADO
Principal +350 pontos; Work +3451,037332; diferença -3101,037332.
50 operações / 22 pregões. 45 determinadas em M1 + 4 ambiguidades e
1 controle de grade conferidos por Replay. Parâmetros originais, WINJ26,
grade5, um contrato/nível, toque inclusivo, corte18h, sem custos/fila/slippage.
Não é mês integral por negócios nem certificação de preenchimento real.

XLSX: quatro abas, 212494 negócios; cinco minutos completos iguais em
OHLC/quantidade; oito bordas parciais esperadas. Sem limite200001 por aba.
Linhas vazias/formatadas não contam como negócios. Sem deduplicação.
Duas ordenações de empates ms mantêm motivo/pontos; sem barreiras opostas
no mesmo ms. Regressões de máxima pré-entrada e barra incompleta passaram.
17mar R61.8 SL -450: entrada10:21:37.660; saída minuto10:28 M1.
19mar S38.2 SL -375: entrada09:03:59.887; saída minuto09:05 M1.
19mar S61.8 SL -650: entrada minuto09:27 M1; stop177480 às09:31:41.874.
19mar R38.2 SL -375: entrada16:01:35.544; saída16:02:19.359.
19mar R61.8 TP +80: entrada16:02:12.608; saída16:02:13.342.
CANDLE indica minuto, não instante exato da saída ou entrada.
Quatro ALVO Work passam a SL. R61.8 da tarde confirma TP na grade5,
mas controle matemático resulta SL: entrada181990 contra181993,842,
alvo181910 contra181912,559667. Não misturar séries nem escolher parâmetros.
S61.8 confirma stop normalizado177480; matemático177477,898 não tocado,
controle conserva TP posterior10:17. Controles matemáticos são diagnósticos.
Contexto02mar continua27fevM5 completo; referências originais preservadas.

DD por fechamento diário em ordem março->abril->maio->junho->julho,
sem reinício mensal. Série M1+Replay separada da série Cedro.
'''
for m,st in stats.items():text+=f"Até {m}: DD teste {st['test_DD_accum']}; Work {st['work_DD_accum']}.\n"
text+='Abril+5720/Maio-780/Junho+3405/Julho+1100 e Cedro intactos.\nNenhuma nova coleta necessária. Julho10jul dispensado, não solicitar novamente.\n'
(P/'LEIA_RESULTADO_FINAL.txt').write_text(text)
raw=Path('/workspace/attachments/77d537df-5f30-4dc1-a288-49b740bc28a4/Mês de Março.xlsx');dest=Path('/workspace/dados_brutos_modelo_d/replay_profit/Marco_2026.xlsx');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(raw,dest)
assert hashlib.sha256(dest.read_bytes()).hexdigest()==s['workbook_sha256']
(P/'PRESERVACAO_BRUTO.json').write_text(json.dumps(dict(source=str(raw),preserved=str(dest),sha256=s['workbook_sha256'],size=dest.stat().st_size,raw_published=False),ensure_ascii=False,indent=2)+'\n')
def fmt(x):return '-' if x=='' else f'{D(x):,.2f}'.replace(',','X').replace('.',',').replace('X','.')
pdf=P/'Modelo_D_Marco_Abril_Maio_Junho_Julho_M1_Replay_Diario.pdf';c=canvas.Canvas(str(pdf),pagesize=A4);W,H=A4
for month,rs in months.items():
 st=stats[month];c.setFont('Helvetica-Bold',16);c.drawString(35,H-40,'MODELO D - '+{'03':'MARCO','04':'ABRIL','05':'MAIO','06':'JUNHO','07':'JULHO'}[month[-2:]]+' / 2026');c.setFont('Helvetica',9);c.drawString(35,H-62,'M1 + Replay pontual | Grade 5 | Pontos brutos nos niveis | Mes encerrado')
 y=H-100
 for x,t in [(35,'Data'),(205,'Work'),(320,'Nosso'),(445,'Diferenca')]:c.drawString(x,y,t)
 for r in rs:
  y-=19;c.drawString(35,y,r['date'][8:]+'/'+r['date'][5:7]+'/2026')
  for x,k in [(270,'work_points'),(390,'test_points'),(555,'difference')]:c.drawRightString(x,y,fmt(r[k]))
 y-=30;c.setFont('Helvetica-Bold',11);c.drawString(35,y,'TOTAL');c.drawRightString(270,y,fmt(st['work_points']));c.drawRightString(390,y,fmt(st['test_points']));c.drawRightString(555,y,fmt(D(st['test_points'])-D(st['work_points'])))
 y-=28;c.setFont('Helvetica',9);c.drawString(35,y,f'DD acumulado desde marco: Work {fmt(st["work_DD_accum"])} | Nosso {fmt(st["test_DD_accum"])}')
 for line in ['DD diario cronologico sem reinicio mensal; separado de Cedro integral.','Sem custos, fila ou garantia de preenchimento. Traco: Work indisponivel.','Julho: controle de 10/07 dispensado pelo usuario.']:
  y-=18;c.drawString(35,y,line)
 c.showPage()
c.save()
with fitz.open(pdf) as d:
 assert len(d)==5
 for page,rs in zip(d,months.values()):
  for r in rs:assert r['date'][8:]+'/'+r['date'][5:7]+'/2026' in page.get_text()
tech=P/'Modelo_D_Marco_Tecnico.pdf';c=canvas.Canvas(str(tech),pagesize=A4);y=H-35;c.setFont('Helvetica',9)
for line in text.splitlines():
 if y<35:c.showPage();y=H-35;c.setFont('Helvetica',9)
 c.drawString(25,y,line);y-=14
c.save()
with zipfile.ZipFile(P/'Marco_Modelo_D_Resultado.zip','w',zipfile.ZIP_DEFLATED) as z:
 for n in ['RESULTADO_FINAL.json','PROGRESSO_RESOLUCAO.json','LEIA_RESULTADO_FINAL.txt','OPERACOES_FINAIS.csv','DIARIO_APOS_JANELAS.csv','REPLAY_OPERACOES_RESOLVIDAS.csv','REPLAY_TODAS_ABAS_M1.csv','CURVA_MARCO_ABRIL_MAIO_JUNHO_JULHO_M1_REPLAY.csv',pdf.name,tech.name]:z.write(P/n,n)
print(json.dumps(dict(reasons=s['final_operation_reasons'],stats=stats),indent=2))
