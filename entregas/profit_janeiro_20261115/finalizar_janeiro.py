"""Freeze January and extend closed M1+targeted Replay curve; no edits to prior months."""
from pathlib import Path
from decimal import Decimal as D
from collections import Counter
import json,csv,zipfile,hashlib,textwrap
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import fitz
P=Path(__file__).parent;ROOT=P.parents[1]
def read(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter=';'))
def write(p,rows):
 with p.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter=';',lineterminator='\n');w.writeheader();w.writerows(rows)
s=json.loads((P/'REPLAY_TODAS_ABAS_RESULTADO.json').read_text());checks=read(P/'REPLAY_TODAS_ABAS_M1.csv');ops=read(P/'OPERACOES_POSSIBILIDADES.csv');daily=read(P/'DIARIO_APOS_JANELAS.csv')
assert all(r['mathematical_tie_invariant'] for r in s['results'])
assert s['pending_operation_count']==0 and s['resolved_original_pending']==4 and s['grade_controls']==0
assert s['test_points']=='-1620' and s['work_points']=='140.280331'
assert all(r['resolved'] and r['entry_minute_coverage_ok'] and r['tie_invariant'] and not r['mixed_exit_barrier_ms'] for r in s['results'])
assert sum(r['full_minute_from_bounds']=='True' for r in checks)==2
assert all(r['ohlc_match']=='True' and r['quantity_match']=='True' for r in checks if r['full_minute_from_bounds']=='True')
lookup={(r['date'],r['level']):r['primary'] for r in s['results']};final=[]
for o in ops:
 pr=lookup.get((o['date'],o['level']))
 if pr:reason,points=pr['reason'],pr['points'];basis=pr['exit_source'];en=pr['entry']['time'];ex=pr['exit']['time']
 else:
  assert o['determined']=='True';reason,points=o['outcomes'].split(':');basis='M1_DETERMINED';en=o['entry_minute']+':00_CANDLE';ex=o['exit_candidates']
 final.append(dict(date=o['date'],contract=o['contract'],level=o['level'],reason=reason,points=points,basis=basis,entry=en,exit=ex,work_reason=o['work_reason'],work_points=o['work_points']))
assert len(final)==48 and sum(D(r['points']) for r in final)==D(-1620)
write(P/'OPERACOES_FINAIS.csv',final)
flips=Counter((r['work_reason'],r['reason']) for r in final if r['work_reason']!=('ALVO' if r['reason']=='TP' else 'STOP' if r['reason']=='SL' else 'ZERAGEM 18H'))
assert flips=={('ALVO','SL'):4,('STOP','TP'):2},flips
months={'2026-01':daily}
months['2026-02']=read(P.parent/'profit_fevereiro_20261114/DIARIO_APOS_JANELAS.csv')
for name,month in [('marco','03'),('abril','04'),('maio','05'),('junho','06'),('winq26_julho','07')]:months['2026-'+month]=read(P.parent/f'profit_{name}_20261113/DIARIO_APOS_JANELAS.csv')
expected=[D(-1620),D(-3545),D(350),D(5720),D(-780),D(3405),D(1100)];tb=tp=td=wb=wp=wd=D(0);curve=[];stats={}
for (month,rs),expected_total in zip(months.items(),expected):
 assert sum(D(r['test_points']) for r in rs)==expected_total
 assert [r['date'] for r in rs]==sorted(set(r['date'] for r in rs))
 for r in rs:
  tb+=D(r['test_points']);tp=max(tp,tb);td=max(td,tp-tb)
  if r['work_points']!='':wb+=D(r['work_points']);wp=max(wp,wb);wd=max(wd,wp-wb)
  curve.append(dict(date=r['date'],test_points=r['test_points'],test_balance=str(tb),test_current_DD=str(tp-tb),test_max_DD=str(td),work_points=r['work_points'],work_balance=str(wb) if r['work_points']!='' else '',work_max_DD=str(wd) if r['work_points']!='' else ''))
 stats[month]=dict(test_points=str(expected_total),work_points=str(sum(D(r['work_points']) for r in rs if r['work_points']!='')),test_DD_accum=str(td),work_DD_accum=str(wd))
assert tb==D(4630)
# Confirm per-day equality of ALL frozen historical months; only history/DD is extended.
previous_curve=read(P.parent/'profit_fevereiro_20261114/CURVA_FEVEREIRO_MARCO_ABRIL_MAIO_JUNHO_JULHO_M1_REPLAY.csv')
assert [(r['date'],r['test_points'],r['work_points']) for r in curve if r['date']>='2026-02-01']==[(r['date'],r['test_points'],r['work_points']) for r in previous_curve]
curve_name='CURVA_JANEIRO_FEVEREIRO_MARCO_ABRIL_MAIO_JUNHO_JULHO_M1_REPLAY.csv';write(P/curve_name,curve)
s.update(grade_sensitive_replay_cases=[dict(date=r['date'],level=r['level'],primary=r['primary']['reason'],mathematical=r['mathematical']['reason'],mathematical_levels=r['mathematical_levels']) for r in s['results'] if r['primary']['reason']!=r['mathematical']['reason']],final_operation_reasons=dict(Counter(r['reason'] for r in final)),Work_flips=[dict(Work=a,test=b,count=n) for (a,b),n in flips.items()],chronological_stats=stats,January_July_test=str(tb),January_July_Work=str(wb),no_new_replay_requested=True,series='M1_PLUS_TARGETED_REPLAY_SEPARATE_FROM_CEDRO',complete_matching_minutes=2,partial_boundary_minutes=4,previous_month_daily_points_unchanged=True)
(P/'RESULTADO_FINAL.json').write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
(P/'PROGRESSO_RESOLUCAO.json').write_text(json.dumps({k:v for k,v in s.items() if k not in ('results','sheets')},ensure_ascii=False,indent=2)+'\n')
text=(P/'NOTA_BASE_FECHAMENTO.txt').read_text()
for m,st in stats.items():text+=f"Até {m}: DD teste {st['test_DD_accum']}; Work {st['work_DD_accum']}.\n"
text+='\nTotal janeiro-julho:teste4630. Meses anteriores preservados. SérieCedro separada.\n'
(P/'LEIA_RESULTADO_FINAL.txt').write_text(text)
def fmt(x):return '-' if x=='' else f'{D(x):,.2f}'.replace(',','X').replace('.',',').replace('X','.')
name='Modelo_D_Janeiro_Fevereiro_Marco_Abril_Maio_Junho_Julho_M1_Replay';pdf=P/(name+'_Diario.pdf');c=canvas.Canvas(str(pdf),pagesize=A4);W,H=A4
for month,rs in months.items():
 st=stats[month];label={'01':'JANEIRO','02':'FEVEREIRO','03':'MARCO','04':'ABRIL','05':'MAIO','06':'JUNHO','07':'JULHO'}[month[-2:]]
 c.setFont('Helvetica-Bold',16);c.drawString(35,H-40,f'MODELO D - {label} / 2026');c.setFont('Helvetica',9);c.drawString(35,H-62,'M1 + Replay pontual | Grade 5 | Pontos brutos nos niveis | Mes encerrado')
 y=H-100
 for x,t in [(35,'Data'),(205,'Work'),(320,'Nosso'),(445,'Diferenca')]:c.drawString(x,y,t)
 for r in rs:
  y-=19;c.drawString(35,y,r['date'][8:]+'/'+r['date'][5:7]+'/2026')
  for x,k in [(270,'work_points'),(390,'test_points'),(555,'difference')]:c.drawRightString(x,y,fmt(r[k]))
 y-=30;c.setFont('Helvetica-Bold',11);c.drawString(35,y,'TOTAL');c.drawRightString(270,y,fmt(st['work_points']));c.drawRightString(390,y,fmt(st['test_points']));c.drawRightString(555,y,fmt(D(st['test_points'])-D(st['work_points'])))
 y-=28;c.setFont('Helvetica',9);c.drawString(35,y,f'DD acumulado desde janeiro: Work {fmt(st["work_DD_accum"])} | Nosso {fmt(st["test_DD_accum"])}')
 for line in ['DD diario cronologico sem reinicio mensal; separado da serie Cedro.','Sem custos, fila ou garantia de preenchimento. Traco: Work indisponivel.','Julho: controle adicional de 10/07 dispensado pelo usuario.']:
  y-=18;c.drawString(35,y,line)
 c.showPage()
c.save()
with fitz.open(pdf) as d:
 assert len(d)==7 and '-1.620,00' in d[0].get_text()
 for page,rs in zip(d,months.values()):
  for r in rs:assert r['date'][8:]+'/'+r['date'][5:7]+'/2026' in page.get_text()
appendix=P/'Janeiro_Nota_Tecnica.pdf';c=canvas.Canvas(str(appendix),pagesize=A4);y=H-35;c.setFont('Helvetica',9)
for paragraph in text.splitlines():
 for line in textwrap.wrap(paragraph,width=100) or ['']:
  if y<35:c.showPage();y=H-35;c.setFont('Helvetica',9)
  c.drawString(25,y,line);y-=14
c.save()
tech=P/(name+'_Tecnico.pdf')
with fitz.open() as d:
 with fitz.open(pdf) as base:d.insert_pdf(base)
 with fitz.open(appendix) as note:d.insert_pdf(note)
 d.save(tech)
with fitz.open(tech) as d:assert len(d)>7
with zipfile.ZipFile(P/'Janeiro_Modelo_D_Resultado.zip','w',zipfile.ZIP_DEFLATED) as z:
 for n in ['RESULTADO_FINAL.json','PROGRESSO_RESOLUCAO.json','LEIA_RESULTADO_FINAL.txt','OPERACOES_FINAIS.csv','DIARIO_APOS_JANELAS.csv','REPLAY_OPERACOES_RESOLVIDAS.csv','REPLAY_TODAS_ABAS_M1.csv','PRESERVACAO_BRUTO.json',curve_name,pdf.name,tech.name]:z.write(P/n,n)
print(json.dumps(dict(reasons=s['final_operation_reasons'],stats=stats),indent=2))
