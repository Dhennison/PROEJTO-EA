from pathlib import Path
import pickle,csv,json,collections,hashlib
import numpy as np
from openpyxl import Workbook
from openpyxl.styles import Font
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4,landscape
from reportlab.lib import colors
P=Path(__file__).parent;R=P.parents[1];E=R/'entregas';C=Path('/workspace/work/combinacao_s23_s38_s61_20261122');C.mkdir(exist_ok=True)
x=pickle.load(open('/workspace/work/modelod_espera_5min_20261122/resultados.pickle','rb'));s23=pickle.load(open('/workspace/work/fechamento_s23_cedro_20261119/fechado.pickle','rb'));days=x['base']['data']['days'];di={d:i for i,d in enumerate(days)}
base=[dict(date=r['date'],level='S23.6',configuration='STOP200_TARGET500_NO_WAIT',waiting_ms=0,points=r['lower'],reason=r['outcomes'].split(':')[0],entry=r['entry']) for r in s23['trades']]
other=[]
for key in ['S38_200_1000','S61_100_ORIGINAL']:
 for r in x['recipes'][key]:other.append(dict(**r,configuration=key,waiting_ms=300000,status=x['gates'][r['date'],r['level']]['row']['status']))
pending=[r for r in other if r['status']=='CLOCK_BOUNDARY_PENDING'];assert len(pending)==14 and len({r['date'] for r in pending})==14
assert collections.Counter(r['points'] for r in pending)=={-200:10,-100.0:3,205.0:1}
def dd(a):
 cum=np.cumsum(a);return float(np.max(np.maximum.accumulate(np.r_[0,cum])[1:]-cum))
def write(name,rows):
 with (P/name).open('w',encoding='utf-8-sig',newline='') as f:
  keys=list(dict.fromkeys(k for r in rows for k in r));w=csv.DictWriter(f,fieldnames=keys,delimiter=';');w.writeheader();w.writerows(rows)
summary=[];annual=[];monthly=[];daily=[];operations=[];decisions=[];curves={}
for case in ['PIOR_TOTAL','MELHOR_TOTAL']:
 selected=[dict(**r,case=case,selection='S23_UNCHANGED_NO_WAIT') for r in base]
 for r in other:
  keep=r['status']=='RETAINED' or (r['status']=='CLOCK_BOUNDARY_PENDING' and (r['points']<0 if case=='PIOR_TOTAL' else r['points']>0))
  if r['status']=='CLOCK_BOUNDARY_PENDING':decisions.append(dict(case=case,date=r['date'],level=r['level'],points_if_retained=r['points'],retained=keep,points_in_case=r['points'] if keep else 0,assumption='TOUCH_AFTER_ACTIVATION' if keep else 'TOUCH_BEFORE_OR_AT_ACTIVATION'))
  if keep:selected.append(dict(**r,case=case,selection='EXACT_RETAINED' if r['status']=='RETAINED' else 'CONDITIONAL_CLOCK_EXTREME'))
 a=np.zeros(709);n=np.zeros(709,dtype=int)
 for r in selected:a[di[r['date']]]+=r['points'];n[di[r['date']]]+=1
 curves[case]=a;row=dict(case=case,operations=len(selected),points=float(a.sum()),DD_continuous=dd(a),monthly_average=float(a.sum())/34,TP=sum(r['reason']=='TP' for r in selected),SL=sum(r['reason']=='SL' for r in selected),CUT=sum(r['reason']=='CUT' for r in selected),pending_clock_cases=14)
 for year in [2024,2025,2026]:
  mask=np.array([d.startswith(str(year)) for d in days]);row['year'+str(year)]=float(a[mask].sum());annual.append(dict(case=case,year=year,scope='JanOut' if year==2026 else 'AnoCompleto',operations=int(n[mask].sum()),points=float(a[mask].sum()),DD_year=dd(a[mask])))
 for month in sorted({d[:7] for d in days}):
  mask=np.array([d.startswith(month) for d in days]);monthly.append(dict(case=case,month=month,operations=int(n[mask].sum()),points=float(a[mask].sum()),DD_month=dd(a[mask])))
 cumulative=np.cumsum(a);peak=np.maximum.accumulate(np.r_[0,cumulative])[1:]
 for i,d in enumerate(days):daily.append(dict(case=case,date=d,operations=int(n[i]),points=a[i],cumulative=cumulative[i],peak=peak[i],drawdown=peak[i]-cumulative[i]))
 summary.append(row);operations.extend(selected)
# Daily covariance matters: add the level curves before computing drawdown.
s23curve=np.array([r['points'] for r in s23['daily']]);expected_lo=s23curve+x['curves']['S38_200_1000']['lo']+x['curves']['S61_100_ORIGINAL']['lo'];expected_hi=s23curve+x['curves']['S38_200_1000']['hi']+x['curves']['S61_100_ORIGINAL']['hi']
assert np.array_equal(curves['PIOR_TOTAL'],expected_lo) and np.array_equal(curves['MELHOR_TOTAL'],expected_hi)
before=s23curve+x['curves']['S38_200_1000']['orig']+x['curves']['S61_100_ORIGINAL']['orig'];comparisons=[dict(scenario='S23_ISOLADO_SEM_ESPERA',points=12915,DD=4915,operations=386),dict(scenario='TRES_NIVEIS_TODOS_SEM_ESPERA',points=float(before.sum()),DD=dd(before),operations=965)]+[dict(scenario=r['case'],points=r['points'],DD=r['DD_continuous'],operations=r['operations']) for r in summary]
requests=[r for r in x['requests'] if r['date'] in {p['date'] for p in pending}];assert len(requests)==28
write('RESUMO_EXTREMOS.csv',summary);write('ANUAL_EXTREMOS.csv',annual);write('MENSAL_EXTREMOS.csv',monthly);write('DIARIO_EXTREMOS.csv',daily);write('OPERACOES_EXTREMOS.csv',operations);write('DECISAO_DOS_14_CASOS.csv',decisions);write('COMPARATIVO.csv',comparisons);write('REPLAY_14_DATAS_28_JANELAS.csv',requests)
w=Workbook();w.remove(w.active)
for name,rows in [('Extremos',summary),('Anual',annual),('Mensal',monthly),('Diario',daily),('Comparativo',comparisons),('14_Casos',decisions),('Operacoes',operations),('Replay_28_Janelas',requests)]:
 sh=w.create_sheet(name);keys=list(dict.fromkeys(k for r in rows for k in r));sh.append(keys)
 for r in rows:sh.append([r.get(k) for k in keys])
 sh.freeze_panes='A2';sh.auto_filter.ref=sh.dimensions
 for c in sh[1]:c.font=Font(bold=True)
 for col in sh.columns:sh.column_dimensions[col[0].column_letter].width=min(45,max(13,max(len(str(c.value or '')) for c in list(col)[:40])+2))
w.save(P/'Combinacao_S23_S38_S61_Pior_Melhor.xlsx')
styles=getSampleStyleSheet();story=[]
def para(t):story.append(Paragraph(t,styles['BodyText']));story.append(Spacer(1,8))
def table(head,rows):
 t=Table([[Paragraph(str(v),styles['BodyText']) for v in r] for r in [head]+rows],repeatRows=1);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#DDE7EF')),('GRID',(0,0),(-1,-1),.3,colors.grey),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),6)]));story.append(t);story.append(Spacer(1,12))
def fmt(v):return f'{float(v):,.0f}'.replace(',','.')
story.append(Paragraph('S23,6 + S38,2 + S61,8: pior e melhor caso',styles['Heading1']));story.append(Spacer(1,10))
para('S23,6% stop200/alvo500 SEM espera; S38,2% stop200/alvo1000 COM espera5min; S61,8% stop100/alvooriginalS50 COM espera5min. Cinco minutos corridos da abertura efetiva, toque ate a liberacao inclusive consome a oportunidade. Uma entrada por nivel/dia; niveis independentes e simultaneidade permitida, sem reentrada nem stop financeiro conjunto novo.')
worst,best=summary
table(['Periodo','Pior total','Melhor total'],[[str(y),fmt(worst['year'+str(y)]),fmt(best['year'+str(y)])] for y in [2024,2025,2026]]+[['Total',fmt(worst['points']),fmt(best['points'])],['DD diario continuo',fmt(worst['DD_continuous']),fmt(best['DD_continuous'])],['Operacoes',worst['operations'],best['operations']]])
para('2026 corresponde apenas a janeiro-outubro. Pior: reter13operacoes de stop (10x-200 e3x-100) e excluir a de alvo+205. Melhor: excluir os13stops e reter o alvo+205. Sao desfechos de horario: a duvida e se a ordem existiria; a saida de cada operacao ja foi apurada. Nao sao probabilidades nem resultados fechados do conjunto.')
para('O conjunto sem os14casos contribui22.540pontos e852operacoes. Pior=22.540-2.300=20.240,865operacoes. Melhor=22.540+205=22.745,853operacoes. O pior total nao corresponde ao menor numero de entradas; evitar confundir os extremos de pontos com extremos de quantidade.')
para('DD calculado APOS somar resultados diarios dos tres niveis, em709pregoes cronologicos, pico inicialzero e sem reinicio mensal/anual. Nao somar DDs individuais. As curvas inferior e superior tem o mesmo DD4.855; portanto nenhuma combinacao intermediaria das14duvidas pode alterar esse maximo na precisao utilizada.')
table(['Comparacao','Total','DD continuo'],[[r['scenario'],fmt(r['points']),fmt(r['DD'])] for r in comparisons])
para('Pontos brutos, um contrato por nivel, sem custos/slippage/fila/latencia. Os dois extremos sao positivos nos tres anos, mas2026 e bem mais fraco. Fontes M1/Replaypontual/Cedro e resultados fechados anteriores; nao e auditoria integral tickatick. Escolha de parametros historica, nao validacao futura independente. Originais preservados e nenhuma variante promovida.')
SimpleDocTemplate(str(P/'Combinacao_S23_S38_S61_Pior_Melhor.pdf'),pagesize=landscape(A4),leftMargin=26,rightMargin=26,topMargin=24,bottomMargin=24).build(story)
manifest=dict(levels=['S23.6 stop200 target500 no wait','S38.2 stop200 target1000 wait5min','S61.8 stop100 original_target wait5min'],time_uncertainties=14,negative_pending_trades=13,positive_pending_trades=1,total_pending_negative_points=-2300,one_pending_target_points=205,summary=summary,original_not_modified=True,conditional_not_closed=True,sources=[dict(path=str(f.relative_to(R)),sha256=hashlib.sha256(f.read_bytes()).hexdigest()) for f in [E/'fechamento_s23_cedro_20261119/OPERACOES_FINAIS.csv',E/'modelod_espera_5min_20261122/DIARIO.csv',E/'modelod_espera_5min_20261122/PENDENCIAS_RELOGIO.csv']])
(P/'MANIFESTO.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');(C/'resultados.pickle').write_bytes(pickle.dumps(dict(summary=summary,annual=annual,monthly=monthly,daily=daily,operations=operations,decisions=decisions,requests=requests,curves=curves,comparisons=comparisons)))
print(json.dumps(summary,indent=2))
