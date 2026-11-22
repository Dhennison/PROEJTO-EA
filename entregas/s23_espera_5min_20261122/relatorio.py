from pathlib import Path
import pickle,csv,json,collections,hashlib
from openpyxl import Workbook
from openpyxl.styles import Font
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4,landscape
from reportlab.lib import colors
P=Path(__file__).parent;R=P.parents[1];E=R/'entregas';x=pickle.load(open('/workspace/work/s23_espera_5min_20261122/resultados.pickle','rb'));s=x['summary']
excluded=[r for r in x['rows'] if r['status']=='CONSUMED_DURING_WAIT'];old={r['date']:r for r in x['prior']['trades']};breakdown=dict(operations=len(excluded),TP=sum(old[r['date']]['TP_guaranteed'] for r in excluded),SL=sum(old[r['date']]['SL_guaranteed'] for r in excluded),CUT=sum(old[r['date']]['CUT_guaranteed'] for r in excluded),points=sum(r['original_points'] for r in excluded))
frequency=dict(operations_lower=s['operations_lower'],operations_upper=s['operations_upper'],TP_lower=min(r['TP'] for r in x['cases']),TP_upper=max(r['TP'] for r in x['cases']),SL_lower=min(r['SL'] for r in x['cases']),SL_upper=max(r['SL'] for r in x['cases']),CUT=7,entries_per_TP_lower=min(r['entries_per_TP'] for r in x['cases']),entries_per_TP_upper=max(r['entries_per_TP'] for r in x['cases']),entries_per_SL_lower=min(r['entries_per_SL'] for r in x['cases']),entries_per_SL_upper=max(r['entries_per_SL'] for r in x['cases']),max_consecutive_SL_lower=min(r['max_consecutive_SL'] for r in x['cases']),max_consecutive_SL_upper=max(r['max_consecutive_SL'] for r in x['cases']))
with (P/'FREQUENCIA_RESUMO.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(frequency),delimiter=';');w.writeheader();w.writerow(frequency)
w=Workbook();w.remove(w.active)
for name,rows in [('Resumo',[s]),('Anual',x['annual']),('Mensal',x['monthly']),('Diario',x['daily']),('709_Pregoes',x['rows']),('32_Casos_Relogio',x['cases']),('Frequencia',[frequency]),('Excluidas_146',[breakdown]),('5_Duvidas',x['boundary']),('Replay_10_Janelas',x['requests'])]:
 sh=w.create_sheet(name);keys=list(dict.fromkeys(k for r in rows for k in r));sh.append(keys)
 for r in rows:sh.append([r.get(k) for k in keys])
 sh.freeze_panes='A2';sh.auto_filter.ref=sh.dimensions
 for c in sh[1]:c.font=Font(bold=True)
 for col in sh.columns:sh.column_dimensions[col[0].column_letter].width=min(48,max(13,max(len(str(c.value or '')) for c in list(col)[:40])+2))
w.save(P/'S23_Espera_5_Minutos_2024_2026.xlsx')
# Empty copy template for only the ten targeted minutes, not a request for whole days.
w=Workbook();sh=w.active;sh.title='Lista';keys=list(x['requests'][0]);sh.append(keys)
for r in x['requests']:
 sh.append([r[k] for k in keys]);name=r['date']+'_'+r['start'].replace(':','');ws=w.create_sheet(name);ws.append(['Data','Compradora','Valor','Quantidade','Vendedora','Agressor','Total (BRL)','Agente Agressor','Núm','Var'])
w.save(P/'Coleta_Relogio_5_Datas_10_Janelas.xlsx')
def n(v):return f'{float(v):,.0f}'.replace(',','.')
def rng(a,b):return n(a) if a==b else n(a)+' a '+n(b)
styles=getSampleStyleSheet();story=[]
def para(t):story.append(Paragraph(t,styles['BodyText']));story.append(Spacer(1,8))
def title(t):story.append(Paragraph(t,styles['Heading1']));story.append(Spacer(1,10))
def table(head,rows):
 t=Table([[Paragraph(str(v),styles['BodyText']) for v in r] for r in [head]+rows],repeatRows=1);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#DDE7EF')),('GRID',(0,0),(-1,-1),.3,colors.grey),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),6)]));story.append(t);story.append(Spacer(1,12))
title('S23,6% stop200 / alvo500: espera de cinco minutos')
para('Regra escolhida pelo usuario: cinco minutos corridos a partir do primeiro negocio da abertura efetiva, com segundos/milissegundos quando disponiveis. Exemplo: abriu09:02:07.123, libera09:07:07.123. Nao e fechamento de M5 no relogio da bolsa. Nao inclui latencia de leitura/envio.')
para('Durante a espera, qualquer toque no nivel consome a oportunidade. O negocio no instante exato de liberacao tambem e verificado antes da ordem. Se consumiu, nao ha ordem nesse nivel no restante do dia. Se nao tocou, ordem limitada de compra no S23,6; sem entrada a mercado. Demais regras preservadas: abertura/elegibilidade/bloqueio geometrico, grade5, uma oportunidade, sem reentrada, stop200/alvo500, corte18h.')
table(['Periodo','Sem espera','Com espera5min','Operacoes novas','Duvidas de horario'],[[r['year'],n(r['original_points']),rng(r['points_lower'],r['points_upper']),rng(r['retained_lower'],r['retained_upper']),r['clock_pending']] for r in x['annual']])
table(['Cenario','Total bruto','DD continuo','Operacoes'],[['S23 sem espera, fechado','12.915','4.915','386'],['Espera5min, limites de horario',rng(s['points_lower'],s['points_upper']),rng(s['DD_lower'],s['DD_upper']),rng(s['operations_lower'],s['operations_upper'])]])
para('Mesmo o limite favoravel do filtro fica abaixo do S23 sem espera. 146operacoes foram certamente consumidas antes da liberacao:54alvos,92stops,0cortes; saldo original conjunto+8.600pontos. 235operacoes certamente permanecem; cinco dependem dos segundos de abertura/primeiro toque. Nao ha nova duvida de stop versus alvo.')
para('DD por fechamentos diarios cronologicos, pico inicial zero, sem reiniciar por mes/ano. Enumeradas todas as32combinacoes de reter/excluir os cinco casos: faixa de DD e frequencia calculada em trajetorias completas, sem misturar extremos de casos diferentes. Valores brutos; execucao teorica, sem custos, slippage ou fila.')
story.append(PageBreak());title('Cinco fronteiras de horario: coleta focal')
para('M1 informa o minuto do primeiro negocio e do primeiro toque, mas nao seus segundos. Nao foi presumida abertura no segundo00. Precisamos comparar o primeiro negocio do dia+300segundos com o primeiro toque. Dois minutos por data, com alguns segundos de margem, sem filtrar/deduplicar:')
rows=[]
for r in x['boundary']:
 q=[v for v in x['requests'] if v['date']==r['date']];rows.append([r['date'],r['contract'],q[0]['start']+'-'+q[0]['end_exclusive'],q[1]['start']+'-'+q[1]['end_exclusive'],n(r['original_points'])])
table(['Data','Contrato','Primeiro negocio','Primeiro toque','Se operar'],rows)
para('Os cinco negocios de saida dessas operacoes ja estao fechados na metodologia anterior. A duvida nova e somente se a ordem existiria apos a espera. Resolver o relogio seleciona entre zero operacao e a operacao original; nao altera os pontos das operacoes originais.')
para('Fontes: mesmos709pregoes e referencias, M1MT5/Profit/Cedro auditado, janelasReplay validadas e proofs do S23 fechado. Metadados Cedro preservados fornecem primeiro timestamp do contrato correto nos63dias de agosto-outubro. Para os demais, a abertura fica no intervalo dos59,999segundos do primeiro minuto M1; fora da fronteira, isso nao muda a classificacao. Quando ha Replay completo ou prova bruta de entrada, seus milissegundos sao usados. Preco da abertura M1 coincide com a referencia nos709dias.')
para('As janelas novas sao fora de agosto-outubroCedro: nao se pede novamente o acervo ja enviado. Qualquer leilao posterior nao reinicia os cinco minutos corridos. Ausencia de negocio nao e toque ficticio. O resultado nao e auditoria integral tickatick dos34meses. Nenhuma mudanca em stops/alvos, noModeloDprincipal ou noestudo50/250 emstand-by.')
SimpleDocTemplate(str(P/'S23_Espera_5_Minutos_2024_2026.pdf'),pagesize=landscape(A4),leftMargin=26,rightMargin=26,topMargin=24,bottomMargin=24).build(story)
manifest=dict(summary=s,excluded_breakdown=breakdown,frequency=frequency,user_selected_rule='Cinco minutos corridos da abertura efetiva',user_selected_date='2026-11-22',pending_kind='CLOCK_ACTIVATION_VS_FIRST_TOUCH_ONLY',finite_time_cases=32,original_not_modified=True,new_exit_reprocessing_needed=False,sources=[dict(path=str(f.relative_to(R)),sha256=hashlib.sha256(f.read_bytes()).hexdigest()) for f in [E/'fechamento_s23_cedro_20261119/RESULTADO_FINAL_S23.csv',E/'fechamento_s23_cedro_20261119/OPERACOES_FINAIS.csv',E/'cedro_extrator_win_v1_00/retorno_geral_20261112/CONTRATOS.csv',E/'atualizacao_s23_replay_20261119/CONFERENCIA_JANELAS.csv']])
(P/'MANIFESTO.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');print('Workbook, PDF and template saved.')
