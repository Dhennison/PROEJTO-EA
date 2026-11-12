"""Arquiva resultado Cedro e gera dois PDFs internos, sem misturar fontes no DD."""
from pathlib import Path
from decimal import Decimal as D
import csv,json,hashlib,importlib.util
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4,landscape
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import fitz
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent;OUT=HERE/'resultado'
def read(p):return list(csv.DictReader(p.open(encoding='utf-8-sig'),delimiter=';'))
def write(p,rows):
 with p.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter=';');w.writeheader();w.writerows(rows)
s=json.loads((OUT/'RESULTADO.json').read_text());daily=read(OUT/'DIARIO_PRINCIPAL.csv');ops=read(OUT/'POR_OPERACAO.csv');states=read(OUT/'TODOS_NIVEIS.csv')
source=json.loads((ROOT/'entregas/compilado_work_modelod/MODELO_D_FONTE_PDF_VALIDADA.json').read_text())
month=next(m for m in source['months'] if m['month']=='2026-08');assert [r['data'] for r in daily]==month['dates']
for r in daily:assert D(r['Work_pontos'])==D(source['daily'][r['data']]['value_exact6'])
original=read(ROOT/'entregas/fechamento_agosto_v1_11/analise/WORK_AGOSTO.csv')
assert {(r['data'],r['nivel']) for r in ops if r['escopo']=='WORK_ORIGINAL'}=={(r['Data'],r['Nível']) for r in original}
prev=read(ROOT/'entregas/fechamento_agosto_v1_11/retorno_nativo_20261111/POR_OPERACAO.csv')
old=[r for r in prev if r['cenario']=='GRADE5_TOQUE' and r['escopo']=='WORK_ORIGINAL'];new={(r['data'],r['nivel']):r for r in ops}
for r in old:
 n=new[r['data'].replace('.','-'),r['nivel']];assert (D(r['pontos']),r['motivo'])==(D(n['pontos']),n['motivo'])
assert len(old)==30
levels=read(ROOT/'entregas/fechamento_agosto_v1_11/analise/NIVEIS_AUDITADOS.csv');by={(r['date'].replace('.','-'),r['nivel']):r for r in levels}
for r in states:
 l=by[r['data'],r['nivel']];assert D(l['stop_grade5'])==D(r['stop_grade5']) and D(l['alvo_grade5'])==D(r['alvo_grade5'])
 if r['hora_entrada']:assert D(l['entrada_grade5'])==D(r['entrada_teorica'])
curve=[];balance={k:D(0) for k in ['Work','teste']};peak=balance.copy();ddmax=balance.copy()
for r in daily:
 d={'data':r['data'],'Work_pontos':r['Work_pontos'],'teste_pontos':r['nosso_pontos']}
 for side,key in [('Work','Work_pontos'),('teste','nosso_pontos')]:
  balance[side]+=D(r[key]);peak[side]=max(peak[side],balance[side]);dd=peak[side]-balance[side];ddmax[side]=max(ddmax[side],dd)
  d.update({side+'_saldo':str(balance[side]),side+'_DD':str(dd),side+'_DD_max_acumulado':str(ddmax[side])})
 curve.append(d)
write(OUT/'CURVA_DIARIA_DRAWDOWN_CEDRO.csv',curve)
changed=[r for r in ops if r['escopo']=='WORK_ORIGINAL' and r['Work_motivo']=='ALVO' and r['motivo']=='STOP'];assert len(changed)==3
flips=sum((D(r['pontos'])-D(r['Work_pontos']) for r in changed),D(0));rest=D(s['diferenca'])-flips
s['drawdown']={'base_inicio':daily[0]['data'],'base_fim':daily[-1]['data'],'Work':str(ddmax['Work']),'teste':str(ddmax['teste']),'ordem':'CRONOLOGICA_CRESCENTE_SALDO_E_PICO_NAO_REINICIAM_POR_MES','medida':'MAXIMO_SOBRE_FECHAMENTOS_DIARIOS','provisorio_por_meses_anteriores_ausentes':True,'serie':'CEDRO','setembro_nativo_nao_concatenado_a_esta_curva':True}
s['conferencia_com_Genial_anterior']={'operacoes':30,'pontos_e_desfechos_identicos':True,'total':str(sum(D(r['pontos']) for r in old))}
s['divergencias_Work']={'alvos_Work_que_viraram_stop':len(changed),'diferenca_nesses_casos':str(flips),'demais_diferencas_grade_e_corte':str(rest)}
s['referencias_niveis_105_conferidos']=True
(OUT/'RESULTADO.json').write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
pdfmetrics.registerFont(TTFont('DV','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'));pdfmetrics.registerFont(TTFont('DVB','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
navy=colors.HexColor('#193b61');gray=colors.HexColor('#62738a');red=colors.HexColor('#c73636');light=colors.HexColor('#edf3fa')
def pt(x):return f'{D(x):,.2f}'.replace(',','@').replace('.',',').replace('@','.')
lean=OUT/'Comparativo_Diario_ModeloD_Cedro_Enxuto_Em_Andamento.pdf';c=canvas.Canvas(str(lean),pagesize=A4);W,H=A4
c.setFillColor(navy);c.rect(0,H-82,W,82,fill=1,stroke=0);c.setFillColor(colors.white);c.setFont('DVB',21);c.drawString(39,H-40,'AGOSTO 2026');c.setFont('DV',9);c.drawString(40,H-64,'WIN | Modelo D | Work x Cedro | pontos diarios')
c.setFillColor(navy);c.setFont('DV',9);c.drawString(40,H-109,'20 pregoes comparados | 1 contrato por nivel | grade5 | toque')
top=H-134;c.setFillColor(light);c.rect(40,top-22,W-80,22,fill=1,stroke=0);c.setFillColor(navy);c.setFont('DVB',8)
for label,x,right in [('DATA',48,False),('DIA',130,False),('MODELO D - WORK',300,True),('NOSSO TESTE',424,True),('DIFERENCA',W-48,True)]:
 (c.drawRightString if right else c.drawString)(x,top-15,label)
y=top-22
for i,r in enumerate(daily):
 y-=20
 if i%2==0:c.setFillColor(colors.HexColor('#f6f9fd'));c.rect(40,y,W-80,20,fill=1,stroke=0)
 c.setFont('DV',9);c.setFillColor(navy);c.drawString(48,y+6,datetime.strptime(r['data'],'%Y-%m-%d').strftime('%d/%m/%Y'));c.drawString(130,y+6,source['daily'][r['data']]['weekday'])
 for val,x in [(r['Work_pontos'],300),(r['nosso_pontos'],424),(r['diferenca'],W-48)]:
  c.setFillColor(red if D(val)<0 else navy);c.drawRightString(x,y+6,pt(val))
y-=30
for label,w,t in [('TOTAL DO MES',s['Work_pontos'],s['nosso_principal_pontos']),('DD MAX. ACUMULADO',ddmax['Work'],ddmax['teste'])]:
 c.setFont('DVB',9);c.setFillColor(navy);c.drawString(48,y,label);c.drawRightString(300,y,pt(w));c.drawRightString(424,y,pt(t));c.drawRightString(W-48,y,pt(D(t)-D(w)));y-=26
c.setFont('DV',7);c.setFillColor(gray)
for i,line in enumerate(['03/08 e complemento fora do Work original, apresentado no PDF tecnico.','DD da serie Cedro em ordem crescente, por fechamento diario; provisorio.','Setembro anterior preservado em outra fonte; aguardando reprocessamento Cedro.','Pontos condicionais nos niveis, sem custos/fila ou comprovacao de preenchimento.']):c.drawString(40,70-12*i,line)
c.showPage();c.save()
tech=OUT/'Comparativo_ModeloD_Cedro_Tecnico_Em_Andamento.pdf';c=canvas.Canvas(str(tech),pagesize=landscape(A4))
def page(title,lines):
 c.setFillColor(navy);c.setFont('DVB',19);c.drawString(36,550,title);y=510
 for line in lines:
  c.setFillColor(navy);c.setFont('DV',10);c.drawString(36,y,line);y-=24
 c.showPage()
page('Agosto/2026 - resultado principal',[
 'Work: '+pt(s['Work_pontos'])+' | Nosso Cedro: '+pt(s['nosso_principal_pontos'])+' | Diferenca: '+pt(s['diferenca']),
 'Mesmas 20 datas e 43 operacoes: 23 alvos, 18 stops e 2 saidas por horario.',
 '1 contrato por nivel, grade de cinco pontos e entrada por toque inclusivo.',
 'Replay direto dos registros Cedro, sem MT5 ou trajetoria gerada pelo Tester.',
 'Entrada/SL/TP creditados nos niveis; saida exige um registro posterior a entrada.',
 'Registros no mesmo milissegundo seguem a ordem do arquivo, preservada sem deduplicacao.',
 '03/08: '+pt(s['complemento_03_agosto']['nosso_pontos'])+' pontos em 3 operacoes, fora do principal comparavel ao Work.',
 'DD por fechamento diario: Work '+pt(ddmax['Work'])+' | Cedro '+pt(ddmax['teste'])+'.',
 'DD provisório em ordem cronologica. Nao concatenar a nova fonte com o setembro anterior.',
 'Pontos brutos condicionais; custos, fila e preenchimento real nao estao comprovados.'
])
lines=['Tres alvos do Work se tornam stop na sequencia dos negocios:']
for r in changed:lines.append(r['data']+' '+r['nivel']+': Work '+pt(r['Work_pontos'])+' | Cedro '+pt(r['pontos']))
lines+=['Diferenca nesses tres casos: '+pt(flips)+' pontos; demais ajustes: '+pt(rest)+'.',
 'Cortes: 06/08 S61,8 -530 em18:00:00.040; 25/08 R61,8 -145 em18:00:00.012.',
 '30 operacoes da coleta antiga Genial repetidas em desfecho e pontos (subtotal -620).',
 '105 estados/niveis validados: Python anterior em eventos reduzidos x C++ em fluxo integral.',
 '400 estados sinteticos: conservacao da reducao, empates, repeticoes e corte.',
 '42 ZIPs/21 datas, hashes/tamanhos/CRC/contagens e ordinais conferidos.',
 'OHLC/quantidades M1 iguais ao Work no horario operado; diferencas apenas18:24.',
 'OHLC/quantidade/registros diarios do contrato de referencia iguais ao EOD em21 datas.',
 'A rolagem mantem referencias do Work: abertura V em12/08, contexto anterior Q.',
 'Layout de condicoes/fuso e ordem oficial entre empates seguem sem certificacao independente.'
]
page('Diferencas e controles',lines)
c.save()
for p in [lean,tech]:
 with fitz.open(p) as doc:
  text=''.join(pg.get_text() for pg in doc);assert '-2.275,00' in text
  assert all(pg.rect.width>0 for pg in doc)
manifest={'serie':'CEDRO','meses_concluidos':['2026-08'],'pendentes':['2026-09','2026-10'],'pontos_principais':s['nosso_principal_pontos'],'DD':s['drawdown'],'PDFs_guardados_para_entrega_final':[str(p.relative_to(ROOT)) for p in [tech,lean]],'sha256_PDFs':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [tech,lean]},'originais_e_setembro_anterior_preservados':True}
(OUT/'MANIFESTO_RELATORIOS.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print('RELATORIOS SALVOS. DD',ddmax,'105 niveis,43 chaves Work,30 operacoes anteriores conferidos.')
