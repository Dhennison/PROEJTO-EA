"""Regenerate technical and lean PDFs; daily/monthly PnL frozen, DD chronological."""
from pathlib import Path
from decimal import Decimal as D,ROUND_HALF_EVEN
from datetime import datetime
import csv,json,hashlib
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4,landscape
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import fitz
root=Path(__file__).resolve().parent
source=json.loads((root.parent/'compilado_work_modelod/MODELO_D_FONTE_PDF_VALIDADA.json').read_text())
metadata=json.loads((root/'MANIFESTO_COMPILADO.json').read_text())
def read(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter=';'))
def write(p,rows):
 with p.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter=';',lineterminator='\n');w.writeheader();w.writerows(rows)
def pt(x,n=2):return f'{D(x):,.{n}f}'.replace(',','@').replace('.',',').replace('@','.')
def ddlocal(values):
 b=p=dd=D(0)
 for x in values:b+=x;p=max(p,b);dd=max(dd,p-b)
 return dd
full_months={r['mes']:r for r in read(root/'MODELO_D_MESES_COMPLETOS.csv')}
index=read(root/'INDICE_MENSAL.csv');done=sorted(r['mes'] for r in index if r['estado'].startswith('CONCLUIDO'))
allmonths=sorted(m['month'] for m in source['months']);positions=[allmonths.index(m) for m in done]
assert done and positions==list(range(positions[0],positions[-1]+1)),'Nao concatenar meses com lacuna como curva continua'
monthly_source={m['month']:m for m in source['months']};daily={}
for month in done:
 file=root/'diarios_principais'/f"{month.replace('-','_')}.csv";rows=read(file)
 assert [r['data'] for r in rows]==monthly_source[month]['dates']
 for r in rows:
  assert r['data'] not in daily and D(r['Work_pontos'])==D(source['daily'][r['data']]['value_exact6'])
  daily[r['data']]={'work':D(r['Work_pontos']),'test':D(r['nosso_pontos'])}
 expected=next(r for r in index if r['mes']==month)
 assert sum(daily[r['data']]['test'] for r in rows)==D(expected['nosso_resultado_principal']),'Resultado mensal congelado mudou'
 assert sum(daily[r['data']]['work'] for r in rows)==D(expected['Work_pontos'])
period_start=min(daily);period_end=max(daily);provisional=done[0]!=allmonths[0]
balance={'work':D(0),'test':D(0)};peak={'work':D(0),'test':D(0)};maxdd={'work':D(0),'test':D(0)};ddrows=[];months={}
for date,row in sorted(daily.items()):
 month=date[:7]
 if month not in months:
  months[month]={'mes':month,'Work_acumulado_anterior':balance['work'],'teste_acumulado_anterior':balance['test'],'Work_DD_continuo_no_mes':D(0),'teste_DD_continuo_no_mes':D(0),'base_DD_inicio':period_start,'base_DD_fim':period_end,'DD_provisorio_por_meses_anteriores_pendentes':provisional}
 record={'data':date,'Work_pontos':row['work'],'teste_pontos':row['test']}
 for side,prefix in (('work','Work'),('test','teste')):
  balance[side]+=row[side];peak[side]=max(peak[side],balance[side]);drawdown=peak[side]-balance[side];maxdd[side]=max(maxdd[side],drawdown)
  record.update({prefix+'_saldo':balance[side],prefix+'_pico':peak[side],prefix+'_DD_atual':drawdown,prefix+'_DD_max_acumulado':maxdd[side]})
  months[month][prefix+'_DD_continuo_no_mes']=max(months[month][prefix+'_DD_continuo_no_mes'],drawdown)
  months[month][prefix+'_DD_max_acumulado']=maxdd[side];months[month][prefix+'_acumulado_ate_mes']=balance[side]
 ddrows.append(record)
for month,m in months.items():
 dates=monthly_source[month]['dates'];m['Work_DD_local_mensal_referencia']=ddlocal([daily[d]['work'] for d in dates]);m['teste_DD_local_mensal_referencia']=ddlocal([daily[d]['test'] for d in dates])
write(root/'CURVA_DIARIA_E_DRAWDOWN.csv',ddrows);write(root/'DRAWDOWN_CRONOLOGICO_POR_MES.csv',list(months.values()))
if done==['2026-09']:
 assert maxdd=={'work':D('1087.585333'),'test':D('1575.000000')}
for row in index:
 month=row['mes'];row['Work_DD_max_acumulado_base_comum']=str(months[month]['Work_DD_max_acumulado']) if month in months else ''
 row['teste_DD_max_acumulado_base_comum']=str(months[month]['teste_DD_max_acumulado']) if month in months else ''
 row['base_DD_inicio']=period_start if month in months else '';row['DD_provisorio']=str(provisional) if month in months else ''
write(root/'INDICE_MENSAL.csv',index)
pdfmetrics.registerFont(TTFont('DV','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'));pdfmetrics.registerFont(TTFont('DVB','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
navy=colors.HexColor('#193b61');light=colors.HexColor('#edf3fa');red=colors.HexColor('#c73636');green=colors.HexColor('#087c68');gray=colors.HexColor('#62738a')
monthnames=['JANEIRO','FEVEREIRO','MARÇO','ABRIL','MAIO','JUNHO','JULHO','AGOSTO','SETEMBRO','OUTUBRO','NOVEMBRO','DEZEMBRO']
lean=root/'Comparativo_Diario_ModeloD_Enxuto_Em_Andamento.pdf';c=canvas.Canvas(str(lean),pagesize=A4);W,H=A4
for page,month in enumerate(done,1):
 src=monthly_source[month];dates=src['dates'];m=months[month];worktotal=sum(daily[d]['work'] for d in dates);testtotal=sum(daily[d]['test'] for d in dates)
 c.setFillColor(navy);c.rect(0,H-82,W,82,fill=1,stroke=0);c.setFillColor(colors.white);c.setFont('DVB',21);c.drawString(39,H-40,monthnames[int(month[5:])-1]+' '+month[:4]);c.setFont('DV',8.5);c.drawString(40,H-64,'WIN  |  Modelo D  |  Work × Cedro  |  pontos diários')
 c.setFillColor(navy);c.setFont('DVB',9);c.drawString(40,H-109,f'{len(dates)} pregões comparados');c.setFont('DV',8.5);c.drawRightString(W-40,H-109,'Teste: 1 contrato por nível • grade5 • toque')
 top=H-134;rowheight=min(20,460/max(len(dates),1));x=[40,122,166,310,434,W-40]
 c.setFillColor(light);c.roundRect(39,top-22,W-78,22,4,fill=1,stroke=0);c.setFillColor(navy);c.setFont('DVB',8)
 for text,pos,align in [('DATA',48,'left'),('DIA',130,'left'),('MODELO D — WORK',300,'right'),('NOSSO TESTE',424,'right'),('DIFERENÇA',W-48,'right')]:
  (c.drawString if align=='left' else c.drawRightString)(pos,top-15,text)
 y=top-22
 for i,date in enumerate(dates):
  y-=rowheight
  if i%2==0:c.setFillColor(colors.HexColor('#f6f9fd'));c.rect(40,y,W-80,rowheight,fill=1,stroke=0)
  v=daily[date];workdisplay=source['daily'][date]['display'];dt=datetime.strptime(date,'%Y-%m-%d')
  c.setFont('DV',9);c.setFillColor(navy);c.drawString(48,y+6,dt.strftime('%d/%m/%Y'));c.drawString(130,y+6,source['daily'][date]['weekday'])
  for value,display,pos in [(v['work'],workdisplay,300),(v['test'],pt(v['test']),424),(v['test']-v['work'],pt(v['test']-v['work']),W-48)]:
   c.setFillColor(red if value<0 else navy);c.drawRightString(pos,y+6,display)
 y-=30;c.setStrokeColor(light);c.line(40,y+24,W-40,y+24)
 summaries=[('TOTAL COMPARÁVEL',worktotal,testtotal,False),('FECHAMENTO CEDRO',None,D(full_months[month]['pontos']),False),('DD MÁX. ACUMULADO',m['Work_DD_max_acumulado'],m['teste_DD_max_acumulado'],True),('ACUMULADO ANTERIOR',m['Work_acumulado_anterior'],m['teste_acumulado_anterior'],False),('ACUMULADO ATÉ O MÊS',m['Work_acumulado_ate_mes'],m['teste_acumulado_ate_mes'],False)]
 for j,(label,wv,tv,risk) in enumerate(summaries):
  if wv is None:
   c.setFont('DVB',8.5);c.setFillColor(navy);c.drawString(48,y,label)
   c.drawRightString(300,y,'—');c.setFillColor(red if tv<0 else green);c.drawRightString(424,y,pt(tv))
   c.setFillColor(gray);c.drawRightString(W-48,y,'—');y-=25;continue
  c.setFont('DVB',8.5);c.setFillColor(navy if j==0 else gray);c.drawString(48,y,label)
  for v,pos in ((wv,300),(tv,424)):
   c.setFillColor(green if j==0 else gray);c.drawRightString(pos,y,pt(v))
  delta=tv-wv;c.setFillColor(red if (delta>0 if risk else delta<0) else green);c.drawRightString(W-48,y,pt(delta));y-=25
 c.setStrokeColor(light);c.line(40,83,W-40,83);c.setFillColor(gray);c.setFont('DV',7)
 notes=[f'Acumulados e DD em ordem cronológica, na base comum: {period_start[8:]}/{period_start[5:7]}/{period_start[:4]} a {period_end[8:]}/{period_end[5:7]}/{period_end[:4]}.',
 'DD da base disponível; será recalculado se a cobertura histórica for ampliada.' if provisional else 'DD da curva contínua completa; saldo e pico não reiniciam a cada mês.',
 'DD por saldo no fechamento diário; não é DD intradiário. Resultados diários/mensais preservados.',
 'Pontos brutos condicionais nos níveis. Ressalvas de alimentação no relatório técnico.']
 for i,line in enumerate(notes):c.drawString(40,68-i*12,line)
 c.drawRightString(W-40,18,f'{page} / {len(done)}');c.showPage()
c.save()
# Technical cover and risk appendix; original monthly PDFs stay byte-identical.
cover=root/'_capa_e_drawdown_temporario.pdf';c=canvas.Canvas(str(cover),pagesize=landscape(A4));c.setFont('DVB',21);c.drawString(40,535,'Work × Modelo D — compilado técnico')
c.setFont('DV',11);c.drawString(40,505,'Resultado principal: um contrato por nível, grade de cinco pontos e entrada por toque.')
y=455;c.setFont('DVB',12);c.drawString(40,y,'Resultados no recorte comparável ao Work');y-=35
for month in done:
 dates=monthly_source[month]['dates'];wv=sum(daily[d]['work'] for d in dates);tv=sum(daily[d]['test'] for d in dates)
 c.setFont('DVB',13);c.drawString(45,y,month+'  |  Work '+pt(wv)+'  |  nosso '+pt(tv)+'  |  diferença '+pt(tv-wv));y-=32
c.setFont('DV',10);c.drawString(40,150,'O PDF enxuto apresenta somente a comparação diária principal. Este PDF mantém observações e controles técnicos.');c.drawString(40,128,'Relatórios originais mensais preservados; dados e drawdown da base comum são atualizados nesta abertura.');c.drawString(40,106,'Pontos condicionais; não são lucro líquido nem comprovação de execução em conta real.');c.showPage()
c.setFont('DVB',18);c.drawString(40,535,'Drawdown: ordem cronológica e base comparável');c.setFont('DV',11)
lines=[f'Base atual: {period_start} a {period_end}. Meses apresentados: '+', '.join(done)+'.',
       'A sequência de coleta pode ser setembro, agosto, julho; a curva sempre é calculada julho, agosto, setembro.',
       'O saldo, o pico e o maior drawdown passam para o mês seguinte, sem reiniciar em zero.',
       'O zero inicial pertence ao começo da base comparável, não a cada mês.',
       'Resultados diários e mensais são congelados. Acumulados e DD são recalculados com os meses acrescentados.',
       'O DD refere-se à base disponível; períodos sem dados não recebem resultado zero.',
       'A comparação usa exatamente os mesmos dias para Work e teste.',
       'A medida principal é o maior DD acumulado sobre fechamentos diários, não marcação intradiária.',
       'O PDF original do Work reiniciava o DD local em cada mês; essa referência local foi preservada nos dados,',
       'mas fica separada da medida contínua solicitada agora pelo usuário.']
for i,line in enumerate(lines):c.drawString(40,493-i*23,line)
y=205
for month in done:
 m=months[month];c.setFont('DVB',12);c.drawString(40,y,month+' — DD máximo acumulado: Work '+pt(m['Work_DD_max_acumulado'])+' | teste '+pt(m['teste_DD_max_acumulado']));y-=25
 c.setFont('DV',10);c.drawString(40,y,'Referência local do mês: Work '+pt(m['Work_DD_local_mensal_referencia'])+' | teste '+pt(m['teste_DD_local_mensal_referencia'])+'. Não substituir DD contínuo por essa medida.');y-=33
c.showPage();c.save()
tech=root/'Comparativo_Work_ModeloD_Tecnico_Em_Andamento.pdf';merged=fitz.open()
with fitz.open(cover) as d:merged.insert_pdf(d)
for month in done:
 row=next(x for x in index if x['mes']==month);original=Path(row['pdf_preservado']);original=original if original.is_absolute() else root.parents[1]/original
 assert hashlib.sha256(original.read_bytes()).hexdigest()==row['pdf_sha256'],'PDF original mensal foi alterado'
 with fitz.open(original) as d:merged.insert_pdf(d)
merged.save(tech);merged.close();cover.unlink()
# Keep the old technical link compatible.
# Dois PDFs finais; sem terceira copia de compatibilidade nesta serie.
serial=lambda obj:json.loads(json.dumps(obj,default=str,ensure_ascii=False))
metadata.update({'entregas_finais_solicitadas':['PDF técnico com observações e análises','PDF enxuto no estilo da fonte, somente Modelo D, Work e teste lado a lado'],'pdf_tecnico':str(tech.relative_to(root.parents[1])),'pdf_enxuto':str(lean.relative_to(root.parents[1])),'regra_drawdown_continuo':{'calculo':'Iterar fechamentos diarios em ordem crescente, saldo e pico carregados entre meses; DD max acumulado ate cada mes.','coleta_em_ordem_inversa_nao_altera_ordem_da_curva':True,'resultado_diario_e_mensal_congelado':True,'recalcular_saldo_acumulado_e_DD_quando_chegam_meses_anteriores':True,'meses_ausentes_nao_sao_zero':True,'base_comum_atual':[period_start,period_end],'provisorio':provisional,'DD_Work':str(maxdd['work']),'DD_teste':str(maxdd['test']),'DD_intradiario':False},'risco_por_mes':serial(months),'meses':index})
(root/'MANIFESTO_COMPILADO.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')
print('Created lean and technical PDFs; monthly results frozen; chronological drawdown',maxdd,'base',period_start,period_end,'provisional',provisional)

# IMAGEM_SETEMBRO_COMPLETO
import subprocess,sys
subprocess.run([sys.executable,str(root.parent/'cedro_modelod_setembro_2026/renderizar_setembro_completo.py'),'--atualizar-compilado'],check=True)
