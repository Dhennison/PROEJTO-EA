"""Entrega solicitada:PDF unico,3paginas,mes completo por pagina;calculos preservados."""
from pathlib import Path
from decimal import Decimal as D
from datetime import datetime
from collections import Counter
import csv,json,hashlib,zipfile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4,landscape
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import fitz
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
A=ROOT/'entregas/cedro_modelod_agosto_2026/resultado';S=ROOT/'entregas/cedro_modelod_setembro_2026/resultado';O=ROOT/'entregas/cedro_modelod_outubro_2026/resultado_mensal'
def read(p):return list(csv.DictReader(p.open(encoding='utf-8-sig'),delimiter=';'))
def write(p,rows):
 with p.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter=';',lineterminator='\n');w.writeheader();w.writerows(rows)
months={'2026-08':sorted(read(A/'DIARIO_COMPLEMENTAR.csv')+read(A/'DIARIO_PRINCIPAL.csv'),key=lambda r:r['data']),'2026-09':read(S/'DIARIO_MES_COMPLETO.csv'),'2026-10':read(O/'DIARIO_MES_COMPLETO.csv')}
assert all(len(rows)==21 and [r['data'] for r in rows]==sorted({r['data'] for r in rows}) for rows in months.values())
expected={'2026-08':D(-2375),'2026-09':D(2855),'2026-10':D(3830)}
for m,rows in months.items():assert sum(D(r['nosso_pontos']) for r in rows)==expected[m]
# Duas curvas separadas:meses completos para modelos e base comum para Work.
full_balance=full_peak=full_dd=D(0);wb=wp=wd=tb=tp=td=D(0);curve=[];common_curve=[];summaries={}
for month,rows in months.items():
 common=[r for r in rows if r['Work_pontos']!='']
 for r in rows:
  value=D(r['nosso_pontos']);full_balance+=value;full_peak=max(full_peak,full_balance);dd=full_peak-full_balance;full_dd=max(full_dd,dd)
  curve.append({'data':r['data'],'pontos':str(value),'saldo':str(full_balance),'pico':str(full_peak),'DD_atual':str(dd),'DD_max_acumulado':str(full_dd)})
  if r['Work_pontos']!='':
   wb+=D(r['Work_pontos']);wp=max(wp,wb);wd=max(wd,wp-wb);tb+=value;tp=max(tp,tb);td=max(td,tp-tb)
   common_curve.append({'data':r['data'],'Work_pontos':r['Work_pontos'],'Cedro_pontos':str(value),'Work_saldo':str(wb),'Cedro_saldo':str(tb),'Work_DD_max_acumulado':str(wd),'Cedro_DD_max_acumulado':str(td)})
 summaries[month]={'mes':month,'pregoes_mes':len(rows),'pontos_mes_completo':str(expected[month]),'operacoes_mes':sum(int(r['operacoes_nossas']) for r in rows),'pregoes_comparaveis':len(common),'Work_comparavel':str(sum(D(r['Work_pontos']) for r in common)) if common else None,'Cedro_comparavel':str(sum(D(r['nosso_pontos']) for r in common)) if common else None,'Work_DD_comparavel_acumulado':str(wd) if common else None,'Cedro_DD_comparavel_acumulado':str(td) if common else None,'Cedro_DD_geral_acumulado':str(full_dd)}
assert full_balance==4310
write(HERE/'CURVA_MODELO_D_MESES_COMPLETOS.csv',curve);write(HERE/'CURVA_COMPARAVEL_WORK.csv',common_curve);write(HERE/'MODELO_D_TRES_MESES_COMPLETOS.csv',list(summaries.values()))
pdfmetrics.registerFont(TTFont('DV','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'));pdfmetrics.registerFont(TTFont('DVB','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
navy=colors.HexColor('#193b61');light=colors.HexColor('#edf3fa');gray=colors.HexColor('#62738a');red=colors.HexColor('#c73636');green=colors.HexColor('#087c68')
def pt(x):return f'{D(x):,.2f}'.replace(',','@').replace('.',',').replace('@','.')
pdf=HERE/'Modelo_D_Cedro_Agosto_Setembro_Outubro_2026.pdf';c=canvas.Canvas(str(pdf),pagesize=A4);W,H=A4
for page,(month,rows) in enumerate(months.items(),1):
 summary=summaries[month];common=[r for r in rows if r['Work_pontos']!=''];last_common=common[-1]['data'] if common else None
 title={'2026-08':'AGOSTO 2026','2026-09':'SETEMBRO 2026','2026-10':'OUTUBRO 2026'}[month]
 c.setFillColor(navy);c.rect(0,H-82,W,82,fill=1,stroke=0);c.setFillColor(colors.white);c.setFont('DVB',21);c.drawString(39,H-40,title);c.setFont('DV',9);c.drawString(40,H-64,'WIN | Modelo D | Work x Cedro | todos os pregões')
 c.setFillColor(navy);c.setFont('DV',8.5);c.drawString(40,H-108,f'21 pregões | {len(common)} comparáveis ao Work' if common else '21 pregões | outubro fora da referência Work');c.drawRightString(W-40,H-108,'1 contrato por nível | grade5 | toque')
 top=H-134;c.setFillColor(light);c.rect(40,top-22,W-80,22,fill=1,stroke=0);c.setFillColor(navy);c.setFont('DVB',8)
 for label,x,right in [('DATA',48,False),('DIA',130,False),('MODELO D — WORK',300,True),('CEDRO',424,True),('DIFERENÇA',W-48,True)]:
  (c.drawRightString if right else c.drawString)(x,top-15,label)
 y=top-22
 for i,r in enumerate(rows):
  y-=19
  if i%2==0:c.setFillColor(colors.HexColor('#f6f9fd'));c.rect(40,y,W-80,19,fill=1,stroke=0)
  date=datetime.strptime(r['data'],'%Y-%m-%d');label=date.strftime('%d/%m/%Y')+('*' if r['data']==last_common else '')
  c.setFillColor(navy);c.setFont('DV',9);c.drawString(48,y+5,label);c.drawString(130,y+5,['seg','ter','qua','qui','sex','sáb','dom'][date.weekday()])
  vals=[(r['Work_pontos'] if r['Work_pontos']!='' else None,300),(r['nosso_pontos'],424),(str(D(r['nosso_pontos'])-D(r['Work_pontos'])) if r['Work_pontos']!='' else None,W-48)]
  for v,x in vals:
   c.setFillColor(gray if v is None else red if D(v)<0 else navy);c.drawRightString(x,y+5,'—' if v is None else pt(v))
  if r['data']==last_common:c.setStrokeColor(colors.HexColor('#a5bad2'));c.line(40,y,W-40,y)
 y-=29;c.setStrokeColor(light);c.line(40,y+22,W-40,y+22)
 work=D(summary['Work_comparavel']) if common else None;test=D(summary['Cedro_comparavel']) if common else None
 wcdd=D(summary['Work_DD_comparavel_acumulado']) if common else None;tcdd=D(summary['Cedro_DD_comparavel_acumulado']) if common else None
 metrics=[('TOTAL COMPARÁVEL*' if common else 'TOTAL COMPARÁVEL',work,test,test-work if common else None),('TOTAL GERAL CEDRO',None,expected[month],None),('DD ACUM. COMPARÁVEL',wcdd,tcdd,tcdd-wcdd if common else None),('DD ACUM. GERAL CEDRO',None,D(summary['Cedro_DD_geral_acumulado']),None)]
 for j,(label,wv,tv,delta) in enumerate(metrics):
  c.setFont('DVB',8.1);c.setFillColor(navy if j<2 else gray);c.drawString(48,y,label)
  for v,x in [(wv,300),(tv,424),(delta,W-48)]:
   c.setFillColor(gray if v is None or j>=2 else red if v<0 else green);c.drawRightString(x,y,'—' if v is None else pt(v))
  y-=25
 notes=[]
 if common:
  start=datetime.strptime(common[0]['data'],'%Y-%m-%d').strftime('%d/%m');end=datetime.strptime(common[-1]['data'],'%Y-%m-%d').strftime('%d/%m')
  notes.append(f'* Total Comparável: somente as {len(common)} datas com Work, de {start} a {end}.')
 else:notes.append('Outubro está fora do Work. Traço significa referência indisponível, não resultado zero.')
 notes+=['Total Geral Cedro: todos os 21 pregões do mês. Pontos brutos condicionais, sem custos/fila.',
         'DD comparável: datas comuns ao Work; DD geral: todos os pregões Cedro desde 03/08.',
         'DD sobre fechamentos diários, em ordem agosto → setembro → outubro, sem reinício mensal.',
         'Ressalvas de sequência/contagem: 22 e 24/09, 27 e 28/10. Controles detalhados no projeto.']
 c.setFont('DV',6.8);c.setFillColor(gray)
 for i,text in enumerate(notes):c.drawString(40,78-i*12,text)
 c.drawRightString(W-40,18,f'{page} / 3');c.showPage()
c.save()
with fitz.open(pdf) as doc:
 assert len(doc)==3
 for i,(m,rs) in enumerate(months.items()):
  text=doc[i].get_text();assert pt(expected[m]) in text
  for r in rs:assert datetime.strptime(r['data'],'%Y-%m-%d').strftime('%d/%m/%Y') in text
  assert 'TOTAL GERAL CEDRO' in text
 assert '21/09/2026*' in doc[1].get_text()
 doc[2].get_pixmap(matrix=fitz.Matrix(1,1)).save('/tmp/modelod_outubro_pagina.png')
# Link do enxuto em andamento continua apontando para a entrega completa.
(HERE/'Comparativo_Diario_ModeloD_Enxuto_Em_Andamento.pdf').write_bytes(pdf.read_bytes())
download=pdf.with_suffix('.zip')
with zipfile.ZipFile(download,'w',zipfile.ZIP_DEFLATED) as z:z.write(pdf,pdf.name)
metadata={'modelo':'D','fonte':'CEDRO_TICK_BMF','status':'TRES_MESES_COMPLETOS','meses':summaries,'pregoes_totais':63,'operacoes_totais':sum(v['operacoes_mes'] for v in summaries.values()),'total_tres_meses':'4310','DD_geral':str(full_dd),'arquivo':str(pdf.relative_to(ROOT)),'paginas':3,'sha256':hashlib.sha256(pdf.read_bytes()).hexdigest(),'zip_sha256':hashlib.sha256(download.read_bytes()).hexdigest(),'custos_fila_inclusos':False,'dados_originais_anteriores_preservados':True}
(HERE/'RELATORIO_TRES_MESES.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')
(O/'RESUMO_TRES_MESES.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n');print(json.dumps(metadata,ensure_ascii=False,indent=2))

# Manter apendice tecnico de outubro em regeneracoes,sem duplicar paginas.
monthly_tech=O/'Analise_Tecnica_Outubro.pdf'
tech=HERE/'Comparativo_Work_ModeloD_Tecnico_Em_Andamento.pdf'
if monthly_tech.exists() and tech.exists():
 merged=fitz.open()
 with fitz.open(tech) as previous,fitz.open(monthly_tech) as addition:
  for i,page in enumerate(previous):
   if 'OUTUBRO 2026 - MODELO D' not in page.get_text():merged.insert_pdf(previous,from_page=i,to_page=i)
  merged.insert_pdf(addition)
 temporary=tech.with_name('_tecnico_tres_meses.pdf');merged.save(temporary);merged.close();temporary.replace(tech)
