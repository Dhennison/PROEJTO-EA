from pathlib import Path
from decimal import Decimal as D
from collections import defaultdict
import csv,json,hashlib
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import fitz
P=Path(__file__).resolve().parent; R=P.parents[1]; E=R/'entregas'
LEVELS=['R38.2','R61.8','S38.2','S50','S61.8']; names=['Janeiro','Fevereiro','Março','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro','Novembro','Dezembro']
sources=[]; ops=[]; daily={}; expected={}
def read(p):
 sources.append({'path':str(p.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 with p.open(encoding='utf-8-sig') as f:return list(csv.DictReader(f,delimiter=';'))
def add(rs,dc,lk,pk):
 for r in rs:
  if r[pk]=='':continue
  assert r[lk] in LEVELS,r
  ops.append(dict(date=r[dc],level=r[lk],points=D(r[pk])))
for folder in sorted((E/'validacao_lote_2025_20261116').glob('[01][0-9]_*')):
 if not folder.is_dir():continue
 add(read(folder/'OPERACOES_FINAIS.csv'),'date','level','points')
 for r in read(folder/'DIARIO_APOS_REPLAY.csv'):daily[r['date']]=D(r['test_points'])
old=['profit_dezembro_2025_20261115','profit_janeiro_20261115','profit_fevereiro_20261114','profit_marco_20261113','profit_abril_20261113','profit_maio_20261113','profit_junho_20261113','profit_winq26_julho_20261113']
for folder in old:
 p=E/folder
 if (p/'OPERACOES_FINAIS.csv').exists():add(read(p/'OPERACOES_FINAIS.csv'),'date','level','points')
 else:
  resolved={(r['date'],r['level']):r for r in read(p/'REPLAY_OPERACOES_RESOLVIDAS.csv')}
  rs=read(p/'OPERACOES_POSSIBILIDADES.csv')
  for r in rs:
   if r['determined']=='True':r['points']=r['min_points']
   else:r['points']=resolved[(r['date'],r['level'])]['points']
  add(rs,'date','level','points')
 for r in read(p/'DIARIO_APOS_JANELAS.csv'):daily[r['date']]=D(r['test_points'])
for month,folder,sub in [('08','agosto','resultado'),('09','setembro','resultado'),('10','outubro','resultado_mensal')]:
 p=E/f'cedro_modelod_{folder}_2026'/sub
 rs=read(p/'TODOS_NIVEIS.csv'); actual=[r for r in rs if r['estado']=='ENCERRADA']
 add(actual,'data','nivel','pontos')
 # Include all recorded dates, including days with no entry.
 for r in rs:daily.setdefault(r['data'],D(0))
for r in read(E/'compilado_cedro_modelod/CURVA_MODELO_D_MESES_COMPLETOS.csv'):daily[r['data']]=D(r['pontos'])
keys=[(r['date'],r['level']) for r in ops];assert len(keys)==len(set(keys))
byday=defaultdict(lambda:D(0)); bylevel=defaultdict(lambda:D(0))
for r in ops:byday[r['date']]+=r['points'];bylevel[(r['date'],r['level'])]+=r['points']
assert set(byday)<=set(daily)
for day,points in daily.items():assert byday[day]==points,(day,byday[day],points)
months=sorted({d[:7] for d in daily});assert len(months)==22
fixed=[-2405,-1180,-970,865,-2915,895,2740,-460,-385,-1055,-300,3135,-1620,-3545,350,5720,-780,3405,1100,-2375,2855,3830]
for m,v in zip(months,fixed):assert sum(vv for dd,vv in daily.items() if dd.startswith(m))==v
state={l:[D(0),D(0),D(0)] for l in LEVELS+['TOTAL']}; rows=[]; curves=[]
for m in months:
 days=sorted(d for d in daily if d.startswith(m))
 for l in LEVELS+['TOTAL']:
  bal=peak=dd=D(0);cb,cp,cd=state[l];start=cb
  for day in days:
   v=daily[day] if l=='TOTAL' else bylevel[(day,l)]
   bal+=v;peak=max(peak,bal);dd=max(dd,peak-bal)
   cb+=v;cp=max(cp,cb);cd=max(cd,cp-cb)
   curves.append(dict(date=day,level=l,points=str(v),balance=str(cb),DD_current=str(cp-cb),DD_max_continuous=str(cd),method='CEDRO' if m>='2026-08' else 'M1_REPLAY_PONTUAL'))
  state[l]=[cb,cp,cd]
  n=sum(1 for r in ops if r['date'].startswith(m) and (l=='TOTAL' or r['level']==l))
  rows.append(dict(month=m,level=l,operations=n,points=str(bal),DD_month=str(dd),DD_max_until_month=str(cd),balance_until_month=str(cb)))
def write(name,rs):
 with (P/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rs[0]),delimiter=';',lineterminator='\n');w.writeheader();w.writerows(rs)
write('RESULTADO_MENSAL_POR_NIVEL.csv',rows);write('CURVAS_DIARIAS_POR_NIVEL.csv',curves)
write('OPERACOES_NORMALIZADAS.csv',[dict(date=r['date'],level=r['level'],points=str(r['points'])) for r in ops])
def fmt(v):return f'{D(v):,.0f}'.replace(',','.')
def label(l):return 'TOTAL DO MODELO D' if l=='TOTAL' else l.replace('.',',')+'%'
pdf=P/'Modelo_D_Resultados_por_Nivel_Jan2025_Out2026.pdf'; c=canvas.Canvas(str(pdf),pagesize=A4);W,H=A4
c.setTitle('Modelo D — resultados e drawdown por nível — janeiro/2025 a outubro/2026')
for ix,m in enumerate(months):
 c.setFillColorRGB(.06,.16,.25);c.rect(0,H-120,W,120,fill=1,stroke=0);c.setFillColorRGB(1,1,1)
 c.setFont('Helvetica-Bold',22);c.drawString(36,H-49,names[int(m[5:])-1]+' / '+m[:4]);c.setFont('Helvetica',11);c.drawString(36,H-76,'Modelo D original | resultado por nível | pontos')
 c.drawString(36,H-98,'Mês completo Cedro' if m>='2026-08' else 'Base M1 e Replay pontual')
 headers=['Nível','Operações','Resultado','DD no mês','DD acum.¹'];xs=[36,226,326,436,558];y=H-164
 c.setFillColorRGB(.06,.16,.25);c.setFont('Helvetica-Bold',10)
 for x,t in zip(xs,headers):
  (c.drawString if x==36 else c.drawRightString)(x,y,t)
 for j,r in enumerate(x for x in rows if x['month']==m):
  y-=43
  if j%2==0:c.setFillColorRGB(.94,.96,.98);c.rect(30,y-14,535,39,fill=1,stroke=0)
  c.setFillColorRGB(.06,.16,.25);c.setFont('Helvetica-Bold' if r['level']=='TOTAL' else 'Helvetica',10)
  c.drawString(36,y,label(r['level']))
  for x,v in zip(xs[1:],[r['operations'],fmt(r['points']),fmt(r['DD_month']),fmt(r['DD_max_until_month'])]):c.drawRightString(x,y,str(v))
 y-=58;c.setFont('Helvetica-Bold',10);c.drawString(36,y,'Como ler o DD de cada nível');c.setFont('Helvetica',9)
 notes=['DD no mês: maior queda entre pico e vale dos fechamentos diários', 'do próprio nível dentro deste mês, começando com saldo zero.', '¹ DD acum.: maior queda da curva diária do próprio nível desde janeiro/2025', 'até o fim deste mês, sem reiniciar entre meses. Inclui a troca de fonte em ago/2026.', 'Dias sem operação do nível têm resultado zero. DD exibido como magnitude positiva.', 'O DD total é calculado na curva conjunta; não é a soma dos DDs dos níveis.', '', 'Parâmetros e resultados fechados preservados. Um contrato por nível; grade de 5 pontos.', 'Sem custos, slippage ou garantia de execução. DD por fechamento diário, não intradiário.', 'M1 + Replay pontual não significa auditoria integral tick a tick.', 'Agosto a outubro/2026: meses completos Cedro, sem recortes comparáveis ao Work.']
 for t in notes:y-=15;c.drawString(36,y,t)
 c.setFont('Helvetica',8);c.drawString(36,32,'Emitido em 16/11/2026 | Fontes e conferências no manifesto e CSVs anexos.');c.drawRightString(558,32,f'{ix+1} / 22');c.showPage()
c.save()
manifest=dict(period='2025-01 a 2026-10',levels=LEVELS,months=22,operations=len(ops),monthly_totals=fixed,source_files=sources,method='Aggregate closed operations; DD daily by level; monthly and continuous since Jan2025; mixed source transition explicitly marked',checks=['Unique date-level','Every daily total equals closed source','22 monthly totals equal frozen results','No R50','No re-simulation'],original_files_unchanged=True)
(P/'MANIFESTO.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
doc=fitz.open(pdf);assert len(doc)==22
assert all('DD no mês' in page.get_text() for page in doc)
print(json.dumps(dict(months=len(months),operations=len(ops),points=str(sum(daily.values())),pdf=str(pdf)),ensure_ascii=False))
