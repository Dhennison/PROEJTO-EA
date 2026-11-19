from pathlib import Path
import pickle,csv,json,collections,ast,hashlib
import numpy as np
from openpyxl import Workbook
from openpyxl.styles import Font
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4,landscape
from reportlab.lib import colors
P=Path(__file__).parent;R=P.parents[1];E=R/'entregas';C=Path('/workspace/work/fechamento_s23_cedro_20261119');x=pickle.load(open(C/'resultados.pickle','rb'));prior=x['prior'];days=prior['data']['days'];di={d:i for i,d in enumerate(days)}
def read(p):return list(csv.DictReader(p.open(encoding='utf-8-sig'),delimiter=';'))
def write(name,rows):
 with (P/name).open('w',encoding='utf-8-sig',newline='') as f:
  keys=list(dict.fromkeys(k for r in rows for k in r));w=csv.DictWriter(f,fieldnames=keys,delimiter=';');w.writeheader();w.writerows(rows)
def dd(a):
 b=np.cumsum(a);return float(np.max(np.maximum.accumulate(np.r_[0,b])[1:]-b))
trades=[r.copy() for r in prior['trades']];proof={r['date']:r for r in x['results']}
for r in trades:
 if r['date'] not in proof:continue
 p=proof[r['date']];assert r['pending'];v=p['points'];reason=p['reason'];assert r['lower']<=v<=r['upper'];r.update(lower=v,upper=v,outcomes=f'{reason}:{v}',pending=False,source='FULL_CEDRO_RAW_CPP_AND_PYTHON_VERIFIED',**{f'{k}_guaranteed':reason==k for k in ['TP','SL','CUT']},**{f'{k}_possible':reason==k for k in ['TP','SL','CUT']})
assert len(trades)==386 and not any(r['pending'] for r in trades);a=np.zeros(709)
for r in trades:assert r['lower']==r['upper'];a[di[r['date']]]=r['lower']
summary=dict(level='S23.6',stop=200,target=500,period='2024Jan-2026Oct',operations=386,total=float(a.sum()),DD_daily_continuous=dd(a),pending=0,closed_under_saved_methodology=True)
annual=[];monthly=[];daily=[]
for y in [2024,2025,2026]:
 mask=np.array([d.startswith(str(y)) for d in days]);summary[f'year{y}']=float(a[mask].sum());annual.append(dict(year=y,scope='JanOut' if y==2026 else 'AnoCompleto',operations=sum(r['date'].startswith(str(y)) for r in trades),points=float(a[mask].sum()),DD_year=dd(a[mask]),pending=0))
for m in sorted({d[:7] for d in days}):
 mask=np.array([d.startswith(m) for d in days]);monthly.append(dict(month=m,operations=sum(r['date'].startswith(m) for r in trades),points=float(a[mask].sum()),DD_month=dd(a[mask]),pending=0))
cum=np.cumsum(a);peak=np.maximum.accumulate(np.r_[0,cum])[1:]
for i,d in enumerate(days):daily.append(dict(date=d,points=a[i],cumulative=cum[i],peak=peak[i],drawdown=peak[i]-cum[i]))
ns={};src=(E/'estudo_niveis_auxiliares_20261119/frequencias_relatorio.py').read_text()
for f in ast.parse(src).body:
 if isinstance(f,ast.FunctionDef) and f.name in ['longest','freq']:exec(compile(ast.Module(body=[f],type_ignores=[]),'preserved_frequency_definition','exec'),ns)
frequency=[ns['freq'](trades if y=='ALL' else [r for r in trades if r['date'].startswith(y)],'S23.6','N089',y) for y in ['ALL','2024','2025','2026']]
oldA=np.array([r['lower'] for r in prior['daily']]);oldB=np.array([r['upper'] for r in prior['daily']]);deltaA=a-oldA;deltaB=a-oldB;combinations=[];combo_daily=[]
rr=read(E/'atualizacao_s23_replay_20261119/DIARIO_COMBINACOES.csv')
for label in dict.fromkeys(r['label'] for r in rr):
 rows=[r for r in rr if r['label']==label];assert [r['date'] for r in rows]==days
 lo=np.array([float(r['lower']) for r in rows])+deltaA;hi=np.array([float(r['upper']) for r in rows])+deltaB
 r=dict(label=label,total_lower=float(lo.sum()),total_upper=float(hi.sum()),DD_lower=dd(hi),DD_upper=dd(lo),pending_other_levels=16,S23_pending=0)
 for y in [2024,2025,2026]:mask=np.array([d.startswith(str(y)) for d in days]);r[f'year{y}_lower']=float(lo[mask].sum());r[f'year{y}_upper']=float(hi[mask].sum())
 combinations.append(r)
 for i,d in enumerate(days):combo_daily.append(dict(label=label,date=d,lower=lo[i],upper=hi[i]))
cost=[]
for fee in [0,5,10]:
 adj=a.copy()
 for r in trades:adj[di[r['date']]]-=fee
 cost.append(dict(hypothetical_cost_per_operation=fee,points=float(adj.sum()),DD_continuous=dd(adj)))
write('RESULTADO_FINAL_S23.csv',[summary]);write('ANUAL_FINAL.csv',annual);write('MENSAL_FINAL.csv',monthly);write('DIARIO_FINAL.csv',daily);write('OPERACOES_FINAIS.csv',trades);write('FREQUENCIAS_FINAIS.csv',frequency);write('COMBINACOES_ATUALIZADAS.csv',combinations);write('DIARIO_COMBINACOES.csv',combo_daily);write('SENSIBILIDADE_CUSTOS.csv',cost)
# Current explicit recovery index includes all 26 restored ZIPs, without changing old receipts.
restored=json.loads((E/'coletas_s61_e_teste_50_250_20261118/RESTAURACAO_FONTES.json').read_text())+json.loads((P/'RESTAURACAO_FONTES.json').read_text());assert len(restored)==26 and len({r['arquivo'] for r in restored})==26
(P/'INDICE_26_ZIPS_RESTAURADOS.json').write_text(json.dumps(restored,ensure_ascii=False,indent=2)+'\n')
w=Workbook();w.remove(w.active)
for name,rows in [('Resumo',[summary]),('Anual',annual),('Mensal',monthly),('Diario',daily),('Operacoes',trades),('Cinco_Cedro',x['results']),('Frequencia',frequency),('Combinacoes',combinations),('Custos',cost),('Auditoria',x['audits'])]:
 s=w.create_sheet(name);keys=list(dict.fromkeys(k for r in rows for k in r));s.append(keys)
 for r in rows:s.append([r.get(k) for k in keys])
 s.freeze_panes='A2';s.auto_filter.ref=s.dimensions
 for cell in s[1]:cell.font=Font(bold=True)
 for col in s.columns:s.column_dimensions[col[0].column_letter].width=min(45,max(13,max(len(str(c.value or '')) for c in list(col)[:40])+2))
w.save(P/'S23_Stop200_Alvo500_Fechado_2024_2026.xlsx')
styles=getSampleStyleSheet();story=[]
def para(t):story.append(Paragraph(t,styles['BodyText']));story.append(Spacer(1,8))
def title(t):story.append(Paragraph(t,styles['Heading1']));story.append(Spacer(1,10))
def table(head,rows):
 t=Table([[Paragraph(str(v),styles['BodyText']) for v in row] for row in [head]+rows],repeatRows=1);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#DDE7EF')),('GRID',(0,0),(-1,-1),.3,colors.grey),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),6)]));story.append(t);story.append(Spacer(1,12))
def n(v):return f'{float(v):,.0f}'.replace(',','.')
title('S23,6% stop200 / alvo500 - resultado fechado')
para('Janeiro/2024 a outubro/2026. Mesmas referencias, 386 entradas, uma por nivel/dia, sem reentrada. Pontos brutos com execucao teorica na grade de 5 pontos; sem custos ou slippage. Nenhuma variante promovida ao resultado principal.')
table(['Ano','Escopo','Operacoes','Pontos','DD do ano'],[[r['year'],r['scope'],r['operations'],n(r['points']),n(r['DD_year'])] for r in annual])
para('<b>Total: '+n(summary['total'])+' pontos. DD diario continuo: '+n(summary['DD_daily_continuous'])+' pontos. Zero operacoes pendentes neste S23.</b> O DD continuo usa os fechamentos diarios em ordem cronologica, pico inicial zero, sem reinicio mensal/anual; nao e soma dos DDs anuais.')
para('Os dez ZIPs recebidos novamente conferem tamanho e SHA256 com os recibos historicos. Reprocessadas as duas partes completas de cinco pregoes Cedro, selecionando o contrato correto, verificando ordinais e milissegundos. Os 25 estados originais desses dias sao iguais aos salvos. As cinco novas operacoes restantes foram stop de -200 pontos cada.')
table(['Data','Contrato','Entrada','Saida','Pontos'],[[r['date'],r['contract'],r['entry_time'],r['exit_time'],n(r['points'])] for r in x['results']])
story.append(PageBreak());title('Frequencia e leitura dos resultados')
f=frequency[0];table(['Entradas','Alvos','Stops cheios','Cortes','1 alvo a cada','1 stop a cada','Maior seq. SL'],[[f['operations'],f['TP_guaranteed'],f['SL_guaranteed'],f['CUT_guaranteed'],f'{f["entries_per_TP_min"]:.2f}',f'{f["entries_per_SL_min"]:.2f}',f['max_consecutive_SL_guaranteed']]])
para('A frequencia e empirica, em numero de entradas; nao indica periodicidade garantida nem probabilidade da proxima operacao. Cortes por horario sao separados de alvo e stop cheio. Dias sem entrada nao interrompem a sequencia de operacoes.')
para('2026 terminou em apenas +95 pontos antes de custos: resultado bem inferior a 2024 e 2025. A escolha dos parametros veio de uma exploracao historica e esta sujeita a sobreajuste. O fechamento das ambiguidades nao transforma o estudo em validacao futura independente.')
table(['Custo hipotetico por operacao','Total apos custo','DD continuo'],[[r['hypothetical_cost_per_operation'],n(r['points']),n(r['DD_continuous'])] for r in cost])
para('As tres combinacoes anteriores foram atualizadas apenas na contribuicao do S23 N089. Cada combinacao ainda tem 16 operacoes pendentes nos outros niveis (R23,6/R50), portanto seus totais continuam sendo faixas. Nao declarar esses conjuntos fechados.')
para('Fontes do periodo: M1 MT5/Profit/Cedro auditado, Replay pontual validado e negocios individuais Cedro onde disponiveis. Os novos resultados foram comparados entre motor C++ no fluxo completo e motor Python em eventos reduzidos que preservam todas as barreiras. Conferida invariancia aos empates no mesmo milissegundo. Nao e auditoria integral tick a tick de todos os 34 meses.')
para('Observacao de 31/07/2026 preservada: leilao com retorno as 12:34:07; primeiro negocio fornecido em 12:34:07.958. Modelo D original e estudos anteriores intactos. 50/250 dos cinco niveis continua em stand-by.')
SimpleDocTemplate(str(P/'S23_Stop200_Alvo500_Fechado_2024_2026.pdf'),pagesize=landscape(A4),leftMargin=26,rightMargin=26,topMargin=24,bottomMargin=24).build(story)
(C/'fechado.pickle').write_bytes(pickle.dumps(dict(summary=summary,annual=annual,monthly=monthly,daily=daily,trades=trades,frequency=frequency,combinations=combinations,combo_daily=combo_daily,audits=x['audits'],results=x['results'])))
manifest=dict(summary=summary,new_raw_files=10,total_current_restored_raw_files=26,new_full_stream_records=sum(r['full_stream_records'] for r in x['audits']),original_states_unchanged=25,python_vs_full_cpp_states=30,remaining_S23_pending=0,remaining_combination_pending=16,source_recovery_index='INDICE_26_ZIPS_RESTAURADOS.json',original_not_modified=True,no_variant_promoted=True)
(P/'MANIFESTO.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(summary=summary,annual=annual,frequency=frequency[0]),ensure_ascii=False,indent=2))
