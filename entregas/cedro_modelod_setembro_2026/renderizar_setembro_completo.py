"""Imagem solicitada:21pregoes,21/09* e TOTAL COMPARAVEL*,sem alterar calculos."""
from pathlib import Path
from decimal import Decimal as D
from datetime import datetime
import csv,json,hashlib,zipfile,sys
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import fitz
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent/'resultado'
rows=list(csv.DictReader((OUT/'DIARIO_MES_COMPLETO.csv').open(encoding='utf-8-sig'),delimiter=';'))
assert len(rows)==21 and [r['data'] for r in rows]==sorted({r['data'] for r in rows})
common=[r for r in rows if r['Work_pontos']!=''];assert len(common)==14
work=sum((D(r['Work_pontos']) for r in common),D(0));test=sum((D(r['nosso_pontos']) for r in common),D(0));full=sum((D(r['nosso_pontos']) for r in rows),D(0))
assert work==D('3839.308998') and test==1380 and full==2855
pdfmetrics.registerFont(TTFont('DV','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'));pdfmetrics.registerFont(TTFont('DVB','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
navy=colors.HexColor('#193b61');light=colors.HexColor('#edf3fa');gray=colors.HexColor('#62738a');red=colors.HexColor('#c73636');green=colors.HexColor('#087c68')
def pt(x):return f'{D(x):,.2f}'.replace(',','@').replace('.',',').replace('@','.')
pdf=OUT/'Setembro_2026_Mes_Completo_Modelo_D.pdf';png=pdf.with_suffix('.png');download=pdf.with_suffix('.zip')
c=canvas.Canvas(str(pdf),pagesize=A4);W,H=A4
c.setFillColor(navy);c.rect(0,H-82,W,82,fill=1,stroke=0);c.setFillColor(colors.white);c.setFont('DVB',21);c.drawString(39,H-40,'SETEMBRO 2026');c.setFont('DV',9);c.drawString(40,H-64,'WIN | Modelo D | Work x Cedro | todos os pregoes')
c.setFillColor(navy);c.setFont('DV',8.5);c.drawString(40,H-108,'21 pregões no mês | 14 comparáveis ao Work');c.drawRightString(W-40,H-108,'1 contrato por nível | grade5 | toque')
top=H-134;c.setFillColor(light);c.rect(40,top-22,W-80,22,fill=1,stroke=0);c.setFillColor(navy);c.setFont('DVB',8)
for label,x,right in [('DATA',48,False),('DIA',130,False),('MODELO D — WORK',300,True),('NOSSO TESTE',424,True),('DIFERENÇA',W-48,True)]:
 (c.drawRightString if right else c.drawString)(x,top-15,label)
y=top-22
for i,r in enumerate(rows):
 y-=20
 if i%2==0:c.setFillColor(colors.HexColor('#f6f9fd'));c.rect(40,y,W-80,20,fill=1,stroke=0)
 dt=datetime.strptime(r['data'],'%Y-%m-%d');label=dt.strftime('%d/%m/%Y')+('*' if r['data']=='2026-09-21' else '')
 c.setFillColor(navy);c.setFont('DV',9);c.drawString(48,y+6,label);c.drawString(130,y+6,['seg','ter','qua','qui','sex','sáb','dom'][dt.weekday()])
 for val,x in [(r['Work_pontos'],300),(r['nosso_pontos'],424),(r['diferenca'],W-48)]:
  if val=='':c.setFillColor(gray);c.drawRightString(x,y+6,'—')
  else:c.setFillColor(red if D(val)<0 else navy);c.drawRightString(x,y+6,pt(val))
 if r['data']=='2026-09-21':c.setStrokeColor(colors.HexColor('#a5bad2'));c.line(40,y,W-40,y)
y-=30;c.setStrokeColor(light);c.line(40,y+23,W-40,y+23)
for label,wv,tv,delta in [('TOTAL COMPARÁVEL*',work,test,test-work),('TOTAL GERAL CEDRO',None,full,None),('DD MÁX. ACUMULADO',D('2248.559'),D(3620),D(3620)-D('2248.559'))]:
 c.setFillColor(navy);c.setFont('DVB',8.5);c.drawString(48,y,label)
 for v,x in [(wv,300),(tv,424),(delta,W-48)]:
  if v is None:c.setFillColor(gray);c.drawRightString(x,y,'—')
  else:c.setFillColor(red if v<0 else green if label!='DD MÁX. ACUMULADO' else gray);c.drawRightString(x,y,pt(v))
 y-=26
notes=['* O Work termina em 21/09. O Total Comparável* usa apenas os pregões até essa data.',
       'De 22 a 30/09, somente Cedro. Traço indica dado Work indisponível, não resultado zero.',
       'Total Geral Cedro: setembro inteiro, de 01 a 30/09, nos 21 pregões apresentados.',
       'DD acumulado desde 04/08, na base comum ao Work; saldo e pico não reiniciam no mês.',
       'Pontos condicionais nos níveis, sem custos/fila. Ressalvas de dados no relatório técnico.']
c.setFont('DV',7);c.setFillColor(gray)
for i,n in enumerate(notes):c.drawString(40,78-i*12,n)
c.showPage();c.save()
with fitz.open(pdf) as doc:
 text=doc[0].get_text();assert '21/09/2026*' in text and 'TOTAL COMPARÁVEL*' in text and '30/09/2026' in text and '2.855,00' in text
 doc[0].get_pixmap(matrix=fitz.Matrix(2,2)).save(png)
with zipfile.ZipFile(download,'w',zipfile.ZIP_DEFLATED) as z:z.write(png,png.name)
if '--atualizar-compilado' in sys.argv:
 target=ROOT/'entregas/compilado_cedro_modelod/Comparativo_Diario_ModeloD_Enxuto_Em_Andamento.pdf'
 if target.exists():
  merged=fitz.open();replaced=0
  with fitz.open(target) as old,fitz.open(pdf) as new:
   for i,page in enumerate(old):
    if 'SETEMBRO 2026' in page.get_text():merged.insert_pdf(new);replaced+=1
    else:merged.insert_pdf(old,from_page=i,to_page=i)
  assert replaced==1
  temp=target.with_name('_enxuto_atualizado.pdf');merged.save(temp);merged.close();temp.replace(target)
(OUT/'IMAGEM_MES_COMPLETO_MANIFESTO.json').write_text(json.dumps({'pregoes':21,'comparaveis':14,'Work_pontos':str(work),'total_comparavel_Cedro':str(test),'total_geral_Cedro':str(full),'asterisco_data':'2026-09-21','asterisco_total':'TOTAL COMPARAVEL*','Work_extra_indisponivel':'TRACO_NAO_ZERO','png_sha256':hashlib.sha256(png.read_bytes()).hexdigest(),'zip_sha256':hashlib.sha256(download.read_bytes()).hexdigest()},ensure_ascii=False,indent=2)+'\n')
print('Imagem pronta:',png)
