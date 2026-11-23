from pathlib import Path
import pickle,csv,json,collections,hashlib,shutil
import numpy as np
from openpyxl import Workbook
from openpyxl.styles import Font
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4,landscape
from reportlab.lib import colors
P=Path(__file__).parent;R=P.parents[1];E=R/'entregas';C=Path('/workspace/work/combinacao_4_niveis_r61_venda_20261122');C.mkdir(exist_ok=True)
prior=pickle.load(open('/workspace/work/combinacao_s23_s38_s61_20261122/resultados.pickle','rb'));m=pickle.load(open('/workspace/work/modelod_espera_5min_20261122/resultados.pickle','rb'));days=m['base']['data']['days'];di={d:i for i,d in enumerate(days)};sale=m['recipes']['R61_375_1000'];assert len(sale)==255 and sum(r['points'] for r in sale)==5725
s=np.zeros(709)
for r in sale:s[di[r['date']]]+=r['points']
assert np.array_equal(s,m['curves']['R61_375_1000']['orig'])
def dd(a):
 cumulative=np.cumsum(a);return float(np.max(np.maximum.accumulate(np.r_[0,cumulative])[1:]-cumulative))
def write(name,rows):
 with (P/name).open('w',encoding='utf-8-sig',newline='') as f:
  keys=list(dict.fromkeys(k for r in rows for k in r));w=csv.DictWriter(f,fieldnames=keys,delimiter=';');w.writeheader();w.writerows(rows)
summary=[];annual=[];monthly=[];daily=[];operations=[];curves={}
for old in prior['summary']:
 case=old['case'];selected=[r.copy() for r in prior['operations'] if r['case']==case]+[dict(**r,case=case,configuration='R61_STOP375_TARGET1000_NO_WAIT',waiting_ms=0,selection='CLOSED_SALE_ADDED_UNCHANGED') for r in sale]
 a=prior['curves'][case]+s;count=np.zeros(709,dtype=int)
 for r in selected:count[di[r['date']]]+=1
 cumulative=np.cumsum(a);peak=np.maximum.accumulate(np.r_[0,cumulative])[1:]
 r=dict(case=case,operations=len(selected),points=float(a.sum()),DD_continuous=dd(a),monthly_average=float(a.sum())/34,TP=sum(r['reason']=='TP' for r in selected),SL=sum(r['reason']=='SL' for r in selected),CUT=sum(r['reason']=='CUT' for r in selected),pending_clock_cases=14)
 for year in [2024,2025,2026]:
  mask=np.array([d.startswith(str(year)) for d in days]);r[f'year{year}']=float(a[mask].sum());annual.append(dict(case=case,year=year,scope='JanOut' if year==2026 else 'AnoCompleto',operations=int(count[mask].sum()),points=float(a[mask].sum()),DD_year=dd(a[mask])))
 for month in sorted({d[:7] for d in days}):
  mask=np.array([d.startswith(month) for d in days]);monthly.append(dict(case=case,month=month,operations=int(count[mask].sum()),points=float(a[mask].sum()),DD_month=dd(a[mask])))
 for i,d in enumerate(days):daily.append(dict(case=case,date=d,operations=int(count[i]),points=a[i],cumulative=cumulative[i],peak=peak[i],drawdown=peak[i]-cumulative[i]))
 summary.append(r);operations.extend(selected);curves[case]=a
comparisons=[dict(scenario='TRES_COMPRAS_'+r['case'],points=r['points'],DD_continuous=r['DD_continuous'],operations=r['operations']) for r in prior['summary']]+[dict(scenario='QUATRO_NIVEIS_'+r['case'],points=r['points'],DD_continuous=r['DD_continuous'],operations=r['operations']) for r in summary]
write('RESUMO_EXTREMOS.csv',summary);write('ANUAL_EXTREMOS.csv',annual);write('MENSAL_EXTREMOS.csv',monthly);write('DIARIO_EXTREMOS.csv',daily);write('OPERACOES_EXTREMOS.csv',operations);write('COMPARATIVO_3_E_4_NIVEIS.csv',comparisons);write('R61_VENDA_FECHADA.csv',sale)
for name in ['DECISAO_DOS_14_CASOS.csv','REPLAY_14_DATAS_28_JANELAS.csv']:shutil.copyfile(E/'combinacao_s23_s38_s61_20261122'/name,P/name)
w=Workbook();w.remove(w.active)
for name,rows in [('Extremos',summary),('Anual',annual),('Mensal',monthly),('Diario',daily),('Comparativo',comparisons),('Operacoes',operations),('R61_Venda_255',sale),('14_Casos',prior['decisions']),('Replay_28_Janelas',prior['requests'])]:
 sh=w.create_sheet(name);keys=list(dict.fromkeys(k for r in rows for k in r));sh.append(keys)
 for r in rows:sh.append([r.get(k) for k in keys])
 sh.freeze_panes='A2';sh.auto_filter.ref=sh.dimensions
 for c in sh[1]:c.font=Font(bold=True)
 for col in sh.columns:sh.column_dimensions[col[0].column_letter].width=min(48,max(13,max(len(str(c.value or '')) for c in list(col)[:40])+2))
w.save(P/'Combinacao_4_Niveis_com_Venda_R61.xlsx')
styles=getSampleStyleSheet();story=[]
def para(t):story.append(Paragraph(t,styles['BodyText']));story.append(Spacer(1,8))
def table(head,rows):
 t=Table([[Paragraph(str(v),styles['BodyText']) for v in r] for r in [head]+rows],repeatRows=1);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#DDE7EF')),('GRID',(0,0),(-1,-1),.3,colors.grey),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),6)]));story.append(t);story.append(Spacer(1,12))
def n(v):return f'{float(v):,.0f}'.replace(',','.')
story.append(Paragraph('Quatro niveis: tres compras e venda no R61,8%',styles['Heading1']));story.append(Spacer(1,10))
para('S23,6 compra stop200/alvo500 SEM espera; S38,2 compra stop200/alvo1000 COM espera5min; S61,8 compra stop100/alvooriginalS50 COM espera5min; R61,8 VENDA stop375/alvo1000 SEM espera. Um contrato por nivel, niveis independentes e simultaneidade permitida. Sem novo stop financeiro conjunto, cancelamento cruzado ou reentrada.')
a,b=summary
table(['Periodo','Pior total','Melhor total'],[[str(y),n(a[f'year{y}']),n(b[f'year{y}'])] for y in [2024,2025,2026]]+[['Total',n(a['points']),n(b['points'])],['DD diario continuo',n(a['DD_continuous']),n(b['DD_continuous'])],['Operacoes',a['operations'],b['operations']]])
para('2026 refere-se somente a janeiro-outubro. Pontos brutos sem custos, slippage, fila ou latencia. Media34meses: '+n(a['monthly_average'])+' a '+n(b['monthly_average'])+' pontos/mes. O R61acrescenta5725pontos fechados(2315/1705/1705porano) em ambos os extremos. A mesma venda esta presente sem filtro em todos os casos,255operacoes.')
table(['Comparacao','Total','DD continuo'],[[r['scenario'],n(r['points']),n(r['DD_continuous'])] for r in comparisons])
para('A venda aumenta pontos e tambem o drawdown em relacao as tres compras. O DD e apurado DEPOIS de somar a curva diaria dos quatro niveis em709pregoes, cronologicamente, pico inicialzero e sem reinicio mensal/anual. Nao somarDDs individuais nem presumir que uma venda reduz o DD de uma carteira compradora.')
para('Mesmas14duvidas de horario do S38,2 e S61,8:13operacoes de stop(-2300somadas) e1alvo+205. Pior mantem13stops e exclui alvo; melhor exclui13stops e mantem alvo. O R61nao acrescenta pendencias. Sao extremos condicionais, nao resultado fechado do conjunto. Os desfechos de saida ja estavam apurados; falta saber se a ordem seria liberada antes do primeiro toque.')
para('Fontes M1/Replaypontual/Cedro e resultados congelados anteriores. Nao e auditoria integral tickatick de34meses. Escolha de parametros historica, nao validacao futura independente. ModeloDprincipal e estudos anteriores preservados; nenhuma variante promovida. 50/250dos5continua emstand-by.')
SimpleDocTemplate(str(P/'Combinacao_4_Niveis_com_Venda_R61.pdf'),pagesize=landscape(A4),leftMargin=26,rightMargin=26,topMargin=24,bottomMargin=24).build(story)
(C/'resultados.pickle').write_bytes(pickle.dumps(dict(summary=summary,annual=annual,monthly=monthly,daily=daily,operations=operations,curves=curves,sale=sale,sale_curve=s,comparisons=comparisons,prior=prior)))
manifest=dict(levels=['S23.6 BUY stop200 target500 NO_WAIT','S38.2 BUY stop200 target1000 WAIT5MIN','S61.8 BUY stop100 target_original_S50 WAIT5MIN','R61.8 SELL stop375 target1000 NO_WAIT'],summary=summary,unchanged_clock_cases=14,new_exit_pending=0,sale_closed_operations=255,sale_added_points=5725,no_model_promoted=True,originals_preserved=True,sources=[dict(path=str(f.relative_to(R)),sha256=hashlib.sha256(f.read_bytes()).hexdigest()) for f in [E/'combinacao_s23_s38_s61_20261122/DIARIO_EXTREMOS.csv',E/'combinacao_s23_s38_s61_20261122/OPERACOES_EXTREMOS.csv',E/'modelod_espera_5min_20261122/DIARIO.csv',E/'estudo_fixos_tres_niveis_20261119/RESULTADOS_270_TESTES.csv']])
(P/'MANIFESTO.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');print(json.dumps(summary,indent=2))
