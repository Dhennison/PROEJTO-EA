from pathlib import Path
import pickle,csv,json,collections,hashlib,itertools
from openpyxl import Workbook
from openpyxl.styles import Font
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4,landscape
from reportlab.lib import colors
P=Path(__file__).parent;R=P.parents[1];E=R/'entregas';x=pickle.load(open('/workspace/work/modelod_espera_5min_20261122/resultados.pickle','rb'))
def write(name,rs):
 with (P/name).open('w',encoding='utf-8-sig',newline='') as f:
  keys=list(dict.fromkeys(k for r in rs for k in r));w=csv.DictWriter(f,fieldnames=keys,delimiter=';');w.writeheader();w.writerows(rs)
# All current ambiguous operations fall on distinct dates. Frequencies can be bounded
# jointly by retaining ambiguous targets versus retaining ambiguous non-targets.
assert len(x['pending'])==len({r['date'] for r in x['pending']})
freq=[];effects=[];cost=[]
for s in x['scenarios']:
 rr=[r for key in s['recipes'] for r in x['recipes'][key]];ret=[r for r in rr if x['gates'][r['date'],r['level']]['row']['status']=='RETAINED'];unc=[r for r in rr if x['gates'][r['date'],r['level']]['row']['status']=='CLOCK_BOUNDARY_PENDING'];gone=[r for r in rr if x['gates'][r['date'],r['level']]['row']['status']=='CONSUMED_DURING_WAIT'];r=dict(scenario=s['id'],retained_lower=len(ret),retained_upper=len(ret)+len(unc))
 for reason in ['TP','SL','CUT']:
  n=sum(v['reason']==reason for v in ret);u=sum(v['reason']==reason for v in unc);other=len(unc)-u;r[reason+'_lower']=n;r[reason+'_upper']=n+u;r['entries_per_'+reason+'_lower']=(len(ret)+u)/(n+u) if n+u else '';r['entries_per_'+reason+'_upper']=(len(ret)+other)/n if n else ''
 freq.append(r);effects.append(dict(scenario=s['id'],consumed=len(gone),consumed_original_points=sum(v['points'] for v in gone),consumed_TP=sum(v['reason']=='TP' for v in gone),consumed_SL=sum(v['reason']=='SL' for v in gone),consumed_CUT=sum(v['reason']=='CUT' for v in gone)))
 grouped=collections.defaultdict(list)
 for p in x['patterns']:
  if p['scenario']==s['id']:grouped[p['date']].append(p)
 for fee in [0,5,10]:
  lo=[];hi=[]
  for d in x['base']['data']['days']:
   ps=grouped.get(d,[dict(points=0,operations=0)]);vals=[p['points']-fee*p['operations'] for p in ps];lo.append(min(vals));hi.append(max(vals))
  def dd(a):
   cum=peak=draw=0
   for v in a:cum+=v;peak=max(peak,cum);draw=max(draw,peak-cum)
   return draw
  cost.append(dict(scenario=s['id'],hypothetical_cost_per_operation=fee,points_lower=sum(lo),points_upper=sum(hi),DD_lower=dd(hi),DD_upper=dd(lo)))
write('FREQUENCIAS.csv',freq);write('EFEITO_OPERACOES_CONSUMIDAS.csv',effects);write('CUSTOS_HIPOTETICOS.csv',cost)
priority_levels={'S38.2','S61.8'};priorities=[r for r in x['requests'] if set(r['levels'].split('|'))&priority_levels];write('REPLAY_PRIORIDADE_S38_S61.csv',priorities)
# Shared minutes already listed for S23 are flagged, without requesting its other dates.
prev=list(csv.DictReader((E/'s23_espera_5min_20261122/REPLAY_DEZ_JANELAS.csv').open(encoding='utf-8-sig'),delimiter=';'));prior_keys={(r['date'],r['contract'],r['start']) for r in prev}
requests=[dict(**r,also_in_previous_S23_clock_list=(r['date'],r['contract'],r['start']) in prior_keys) for r in x['requests']];write('REPLAY_JANELAS_UNIFICADAS.csv',requests)
w=Workbook();w.remove(w.active)
for name,rows in [('Resultados',x['summary']),('Anual',x['annual']),('Mensal',x['monthly']),('Diario',x['daily']),('Frequencia',freq),('Consumo',effects),('1485_Horarios',x['diagnostic']),('29_Duvidas',x['pending']),('Replay_58_Janelas',requests),('Prioridade_S38_S61',priorities),('Custos_Hipoteticos',cost)]:
 sh=w.create_sheet(name);keys=list(dict.fromkeys(k for r in rows for k in r));sh.append(keys)
 for r in rows:sh.append([r.get(k) for k in keys])
 sh.freeze_panes='A2';sh.auto_filter.ref=sh.dimensions
 for cell in sh[1]:cell.font=Font(bold=True)
 for col in sh.columns:sh.column_dimensions[col[0].column_letter].width=min(48,max(13,max(len(str(c.value or '')) for c in list(col)[:40])+2))
w.save(P/'Modelo_D_e_Fechados_Espera_5min_2024_2026.xlsx')
w=Workbook();sh=w.active;sh.title='Lista';keys=list(requests[0]);sh.append(keys)
for r in requests:
 sh.append([r[k] for k in keys]);ws=w.create_sheet(r['date']+'_'+r['start'].replace(':',''));ws.append(['Data','Compradora','Valor','Quantidade','Vendedora','Agressor','Total (BRL)','Agente Agressor','Núm','Var'])
w.save(P/'Coleta_Relogio_29_Datas_58_Janelas.xlsx')
def n(v):return f'{float(v):,.0f}'.replace(',','.')
def rng(a,b):return n(a) if a==b else n(a)+' a '+n(b)
styles=getSampleStyleSheet();story=[]
def para(t):story.append(Paragraph(t,styles['BodyText']));story.append(Spacer(1,8))
def title(t):story.append(Paragraph(t,styles['Heading1']));story.append(Spacer(1,10))
def table(head,rows,size=None):
 t=Table([[Paragraph(str(v),styles['BodyText']) for v in r] for r in [head]+rows],colWidths=size,repeatRows=1);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#DDE7EF')),('GRID',(0,0),(-1,-1),.3,colors.grey),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),6)]));story.append(t);story.append(Spacer(1,12))
by={r['id']:r for r in x['summary']};original=by['D_ORIGINAL_5']
title('Modelo D: cinco niveis com espera de cinco minutos')
para('Regra mantida: primeiro negocio da abertura efetiva+300segundos. Toque ate o instante de verificacao inclusive consome a oportunidade daquele nivel. Sem toque: ordem limitada no nivel, nunca ordem a mercado. Parametros originais e todas as demais regras preservados. Os niveis sao independentes: toque num deles nao bloqueia os demais.')
table(['Ano','Original sem espera','Original com espera','Operacoes com espera'],[[r['year'],n(r['original_points']),rng(r['points_lower'],r['points_upper']),rng(r['operations_lower'],r['operations_upper'])] for r in x['annual'] if r['scenario']=='D_ORIGINAL_5'])
table(['Cenario','Total','DD diario continuo','Operacoes'],[['Original sem espera','3.950','14.805','1.485'],['Original com espera',rng(original['points_lower'],original['points_upper']),rng(original['DD_lower'],original['DD_upper']),rng(original['operations_lower'],original['operations_upper'])]])
para('2024 permanece negativo mesmo no limite favoravel. As faixas nao permitem concluir que o total melhorou, pois incluem valores abaixo e acima do original. O DD cai em todos os casos de horario considerados. Sao29operacoes em29datas na fronteira; nao sao novas duvidas de alvo/stop.')
table(['Nivel original','Antes','Depois5min','DD depois','Pend.'],[[l,n(by['ORIGINAL_'+l]['original_points']),rng(by['ORIGINAL_'+l]['points_lower'],by['ORIGINAL_'+l]['points_upper']),rng(by['ORIGINAL_'+l]['DD_lower'],by['ORIGINAL_'+l]['DD_upper']),by['ORIGINAL_'+l]['clock_pending_operations']] for l in ['R38.2','R61.8','S38.2','S50','S61.8']])
story.append(PageBreak());title('Configuracoes fechadas anteriores: efeito da espera')
ids=['R61_375_1000','R61_75_1000','S38_200_1000','S61_100_ORIGINAL'];labels={'R61_375_1000':'R61,8 stop375/alvo1000','R61_75_1000':'R61,8 stop75/alvo1000','S38_200_1000':'S38,2 stop200/alvo1000','S61_100_ORIGINAL':'S61,8 stop100/alvooriginal'}
table(['Configuracao','Antes','DD antes','Depois5min','DD depois','Pend.'],[[labels[i],n(by[i]['original_points']),n(by[i]['original_DD']),rng(by[i]['points_lower'],by[i]['points_upper']),rng(by[i]['DD_lower'],by[i]['DD_upper']),by[i]['clock_pending_operations']] for i in ids])
table(['Configuracao','2024 depois','2025 depois','2026jan-out depois'],[[labels[i],rng(by[i]['year2024_lower'],by[i]['year2024_upper']),rng(by[i]['year2025_lower'],by[i]['year2025_upper']),rng(by[i]['year2026_lower'],by[i]['year2026_upper'])] for i in ids])
para('S38,2 stop200/alvo1000 e S61,8 stop100/alvooriginal melhoram total e DD em todos os casos restantes. R61,8 nas duas receitas fixas perde pontos e aumenta DD. O filtro nao oferece vantagem uniforme por nivel. Frequencias e custos hipoteticos em tabelas separadas. Nenhuma receita foi promovida a principal.')
story.append(PageBreak());title('Conjunto com maiores totais fechados individuais')
m=by['MISTO_MAIORES_FECHADOS_5'];para('Este conjunto usa R38,2original; R61,8stop375/alvo1000; S38,2stop200/alvo1000; S50original; S61,8original. Todos os componentes sem espera estavam fechados. E uma composicao dos maiores totais individuais, nao uma alegacao de melhor conjunto global.')
table(['Ano','Sem espera','Com espera'],[[y,n(m[f'year{y}_original']),rng(m[f'year{y}_lower'],m[f'year{y}_upper'])] for y in [2024,2025,2026]])
table(['Cenario','Total','DD continuo'],[['Sem espera',n(m['original_points']),n(m['original_DD'])],['Com espera',rng(m['points_lower'],m['points_upper']),rng(m['DD_lower'],m['DD_upper'])]])
para('O total pode aumentar, mas o DD aumenta mesmo no limite favoravel. Mantem29casos de relogio nos mesmos dias do original. Nao somar melhores limites individuais sem respeitar o relogio comum do dia.')
para('Metodo: o filtro apenas conserva/exclui operacoes fechadas. Primeiro toque apos liberacao mantem a mesma entrada/saida/pontos; primeiro toque anterior elimina a entrada, sem autorizar reteste. Foram preservados1485primeiros toques e todos os pontos anteriores. Aberturas exatas em78dias e primeiros toques exatos em282operacoes, conformeReplay/recibos Cedro/execucoes historicas documentadas. Nos demais, segundos desconhecidos ficam em intervalo, sem presumir segundo00.')
para('Padroes por dia usam uma unica liberacao para o contrato e respeitam ordem de primeiros toques dos niveis do mesmo lado e equivalencias de primeiro negocio. Neste conjunto ha somente um nivel incerto por data; os extremos diarios se propagam pelas curvas cronologicas. DD tem pico inicialzero, sem reinicio mensal/anual. Faixas sao limites, nao probabilidades. Pontos brutos sem custos, slippage, latencia ou fila. Fontes M1/Replay pontual/Cedro; nao e auditoria integral tickatick.')
para('S23,6% continua sem espera, +12.915/DD4.915, conforme decisao do usuario. ModeloDoriginal semespera+3.950/DD14.805 e estudos anteriores preservados. 50/250 doscinconiveis segueemstand-by.')
story.append(PageBreak());title('Triagem de Replay: duvidas de relogio')
para('29datas/58minutos: abertura efetiva e minuto do primeiro toque. E inventario de pendencias, nao pedido automatico para coletar tudo. Os destaques S38,2stop200/alvo1000 e S61,8stop100/alvooriginal compartilham14dessasdatas,28minutos. Todos os horarios estao fora de agosto-outubroCedro ja enviado. Capturar minuto completo com margem, milissegundos e negocios identicos.')
rows=[]
for r in x['pending']:
 req=[v for v in requests if v['date']==r['date']];op=next(v for v in req if 'OPENING' in v['purpose']);to=next(v for v in req if 'FIRST_TOUCH_AT_GATE' in v['purpose']);rows.append([r['date'],r['contract'],r['level'],op['start']+'-'+op['end_exclusive'],to['start']+'-'+to['end_exclusive']])
table(['Data','Contrato','Nivel','Abertura','Primeiro toque'],rows)
SimpleDocTemplate(str(P/'Modelo_D_e_Fechados_Espera_5min_2024_2026.pdf'),pagesize=landscape(A4),leftMargin=25,rightMargin=25,topMargin=24,bottomMargin=24).build(story)
manifest=dict(period='2024Jan-2026Oct',rule='Five elapsed minutes from first actual business; any touch at or before activation consumes level; pending limit order only afterwards.',scenario_count=len(x['summary']),frozen_original_operations=1485,opening_exact_days=len(x['first_open']),first_touch_exact_operations=len(x['first_touch']),clock_pending_operations=len(x['pending']),clock_pending_dates=len({r['date'] for r in x['pending']}),Replay_windows=len(requests),priority_S38_S61_windows=len(priorities),original_unchanged=True,S23_unchanged_and_without_wait=True,no_model_promoted=True,sources=[dict(path=s,sha256=hashlib.sha256((R/s).read_bytes()).hexdigest()) for s in x['source_paths']])
(P/'MANIFESTO.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');print('PDF/XLSX/frequencies/templates generated. Requests',len(requests),'priority',len(priorities))
