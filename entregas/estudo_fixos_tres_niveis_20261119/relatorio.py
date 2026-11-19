from pathlib import Path
import csv,pickle,ast,collections,json,hashlib,zipfile
import numpy as np
from openpyxl import Workbook
from openpyxl.styles import Font
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4,landscape
from reportlab.lib import colors
P=Path(__file__).parent;R=P.parents[1];E=R/'entregas';x=pickle.load(open('/workspace/work/fixos_tres_niveis_20261119/resultados.pickle','rb'))
def read(p):return list(csv.DictReader(p.open(encoding='utf-8-sig'),delimiter=';'))
def write(name,rs):
 if not rs:return
 with (P/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rs[0]),delimiter=';');w.writeheader();w.writerows(rs)
# Reuse the exact frequency definitions, without executing the earlier report.
ns={};src=(E/'estudo_niveis_auxiliares_20261119/frequencias_relatorio.py').read_text()
for f in ast.parse(src).body:
 if isinstance(f,ast.FunctionDef) and f.name in ['longest','freq']:exec(compile(ast.Module(body=[f],type_ignores=[]),'same_frequency_definitions','exec'),ns)
frequency=[];group=collections.defaultdict(list)
for r in x['trades']:group[(r['level'],r['variant'])].append(r)
for (level,id),rr in group.items():
 for period in ['ALL','2024','2025','2026']:frequency.append(ns['freq'](rr if period=='ALL' else [r for r in rr if r['date'].startswith(period)],level,id,period))
write('FREQUENCIAS_TODOS_TESTES.csv',frequency)
fixedid=next(c['id'] for c in x['configs'] if c['stop_points']==200 and c['target_points']==500);fixedfreq=[r for r in frequency if r['variant']==fixedid];write('FREQUENCIA_200_500.csv',fixedfreq)
selectedkeys={(r['level'],r['id']) for r in x['selected']}|{(r['level'],r['id']) for r in x['fixed']};selectedfreq=[r for r in frequency if (r['level'],r['variant']) in selectedkeys];write('FREQUENCIAS_SELECIONADOS.csv',selectedfreq)
requests=read(P/'S23_200_500_PENDENCIAS_RECLASSIFICADAS.csv');replay=[r for r in requests if r['status']=='REPLAY_SOLICITADO'];recover=[r for r in requests if r['status']!='REPLAY_SOLICITADO'];assert len(replay)==len(recover)==5
write('S23_200_500_REPLAY_5_DATAS.csv',replay)
receipts=read(P/'ACERVO_CEDRO_RECEBIDO_E_ACESSO_ATUAL.csv');tags={r['date'].replace('-','') for r in recover};missing=[r for r in receipts if any(tag in r['arquivo'] for tag in tags)];assert len(missing)==10 and all(r['accessible']=='False' for r in missing);write('S23_CEDRO_10_ZIPS_JA_RECEBIDOS_A_RESTAURAR.csv',missing)
# Prepare an empty return workbook only for actual Replay requests.
w=Workbook();w.active.title='Lista'
headers=['Data','Contrato','Inicio','Fim_exclusivo','Opcao']
w.active.append(headers)
for r in replay:
 w.active.append([r['date'],r['contract'],r['start'],r['end_exclusive'],'S23.6 stop200 alvo500']);s=w.create_sheet(r['date']);s.append(['Data','Compradora','Valor','Quantidade','Vendedora','Agressor','Total (BRL)','Agente Agressor','Núm','Var'])
w.save(P/'Coleta_S23_200_500_5_Datas.xlsx')
# Main report includes every finite-grid recipe and annual/monthly results.
w=Workbook();w.remove(w.active)
for name,rows in [('200_500',x['fixed']),('Destaques',x['selected']),('Frequencia_200_500',fixedfreq),('Frequencia_Destaques',selectedfreq),('270_Testes',x['summary']),('Anual_Todos',x['annual']),('Mensal_Todos',x['monthly']),('Replay_S23_5',replay),('Cedro_S23_5',recover),('Brutos_a_Restaurar',missing),('Parametros',x['configs'])]:
 s=w.create_sheet(name);keys=list(rows[0]);s.append(keys)
 for r in rows:s.append([r.get(k) for k in keys])
 s.freeze_panes='A2';s.auto_filter.ref=s.dimensions
 for c in s[1]:c.font=Font(bold=True)
 for col in s.columns:s.column_dimensions[col[0].column_letter].width=min(45,max(13,max(len(str(c.value or '')) for c in list(col)[:40])+2))
w.save(P/'Stops_Alvos_Fixos_3_Niveis_2024_2026.xlsx')
def n(v):return f'{float(v):,.0f}'.replace(',','.')
def rng(a,b):return n(a) if a==b else n(a)+' a '+n(b)
styles=getSampleStyleSheet();story=[]
def para(s):story.append(Paragraph(s,styles['BodyText']));story.append(Spacer(1,7))
def title(s):story.append(Paragraph(s,styles['Heading1']));story.append(Spacer(1,8))
def table(head,rows):
 cells=[[Paragraph(str(c),styles['BodyText']) for c in row] for row in [head]+rows];t=Table(cells,repeatRows=1);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#DDE7EF')),('GRID',(0,0),(-1,-1),.3,colors.grey),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),6)]));story.append(t);story.append(Spacer(1,12))
def metrics(rows):return [[r['level'],str(r['stop_points'])+'/'+str(r['target_points']),rng(r['year2024_lower'],r['year2024_upper']),rng(r['year2025_lower'],r['year2025_upper']),rng(r['year2026_lower'],r['year2026_upper']),rng(r['lower'],r['upper']),rng(r['DD_lower'],r['DD_upper']),r['pending']] for r in rows]
head=['Nivel','Stop/alvo','2024','2025','2026 JanOut','Total','DD continuo','Pend.']
title('Stops e alvos fixos: R61,8 / S38,2 / S61,8')
para('Janeiro/2024 a outubro/2026. 709 pregoes; mesmas 834 entradas desses tres niveis (255/346/233), uma por nivel/dia. Sem reentrada; grade 5; corte a partir de 18h. Sem custos, slippage ou simulacao de fila. Original preservado.')
para('90 receitas por nivel = 270 testes. Stops 25/50/75/100/150/200/250/375/500/650; alvos 50/100/150/200/250/375/500/750/1000. Todos fixos, sem dependencia de distancia Fibonacci. Nao e busca de todos os parametros possiveis.')
para('M1 e Replay pontual, provas dos desfechos originais e 16 ZIPs Cedro acessiveis. Os 132 ZIPs dos tres meses foram recebidos historicamente; ausencia atual de acesso a parte dos brutos nao significa falta de envio. Faixas mantidas onde sequencia permanece incerta. Nao e auditoria integral tick a tick.')
table(head,metrics(x['fixed']))
para('O par stop200/alvo500 nao reproduz, nestes niveis, o desempenho do S23,6. Nao transferir o parametro entre niveis sem conferir os resultados.')
story.append(PageBreak());title('Destaques dentro da grade')
para('Melhor relacao limite inferior de pontos / limite superior de DD, no periodo completo. Selecao exploratoria, sujeita a sobreajuste.')
table(head,metrics([r for r in x['selected'] if r['criterion']=='FULL_RATIO_EXPLORATORY']))
para('Maior total conservador por nivel no periodo completo:')
table(head,metrics([r for r in x['selected'] if r['criterion']=='FULL_POINTS_EXPLORATORY']))
para('Tambem salva a selecao por pontos/DD usando somente 2024-2025. Como 2026 ja e conhecido, nao representa validacao futura independente. DD diario em ordem cronologica, pico inicial zero, sem reinicio mensal/anual. Nenhuma variante promovida.')
story.append(PageBreak());title('S23,6 stop200/alvo500: lista corrigida')
para('Cinco datas para nova coleta no Replay. Capturar minuto completo com alguns segundos de margem, preservar milissegundos, ordem e negocios identicos:')
table(['Data','Contrato','Intervalo'],[[r['date'],r['contract'],r['start']+' - '+r['end_exclusive']] for r in replay])
para('Cinco janelas Cedro abaixo NAO sao pedido de nova captura: os brutos ja foram enviados e tiveram hashes conferidos. No ambiente atual faltam os 10 ZIPs identificados no CSV de restauracao; resultados nao foram fechados artificialmente:')
table(['Data','Contrato','Intervalo'],[[r['date'],r['contract'],r['start']+' - '+r['end_exclusive']] for r in recover])
para('Planilha de retorno com cinco abas vazias entregue separadamente. O estudo 50/250 dos cinco niveis originais permanece em stand-by; esta varredura dos tres niveis foi autorizada pelo pedido atual.')
SimpleDocTemplate(str(P/'Stops_Alvos_Fixos_3_Niveis_2024_2026.pdf'),pagesize=landscape(A4),leftMargin=24,rightMargin=24,topMargin=24,bottomMargin=24).build(story)
with zipfile.ZipFile(P/'Tabelas_Completas.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for name in ['OPERACOES_TODOS_TESTES.csv','PENDENCIAS_TODOS_TESTES.csv','FREQUENCIAS_TODOS_TESTES.csv']:z.write(P/name,arcname=name)
for name in ['OPERACOES_TODOS_TESTES.csv','PENDENCIAS_TODOS_TESTES.csv','FREQUENCIAS_TODOS_TESTES.csv']:(P/name).unlink()
manifest=dict(period='2024Jan-2026Oct',recipes_per_level=90,tests=270,entries=dict(collections.Counter(o['level'] for o in x['ops'])),fixed200500=x['fixed'],selected=x['selected'],S23_replay_requested=5,S23_recover_received_raw_windows=5,S23_received_raw_files_not_accessible=missing,raw_audit=json.loads((P/'AUDITORIA_CEDRO.json').read_text()),original_unchanged=True,no_model_promoted=True,source_note='Full Cedro receipt exists for 132 ZIPs; only 16 currently accessible; remaining exact names in inventory. Do not ask fresh Replay for already-supplied Cedro periods.',sources=[dict(path=str(f),sha256=hashlib.sha256(f.read_bytes()).hexdigest()) for f in [E/'estudo_niveis_auxiliares_20261119/ROTULOS_ORIGINAIS_CONFERIDOS.csv',E/'estudo_niveis_auxiliares_20261119/REPLAY_CANDIDATOS_SELECIONADOS.csv',E/'coletas_s61_e_teste_50_250_20261118/RESTAURACAO_FONTES.json']])
(P/'MANIFESTO.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'fixed':x['fixed'],'selected':x['selected']},indent=2))
