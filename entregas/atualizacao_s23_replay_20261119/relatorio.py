from pathlib import Path
import pickle,csv,json,hashlib
from openpyxl import Workbook
from openpyxl.styles import Font
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4,landscape
from reportlab.lib import colors
P=Path(__file__).parent;R=P.parents[1];E=R/'entregas';x=pickle.load(open('/workspace/work/replay_s23_20261119/resultado_atualizado.pickle','rb'))
def read(p):return list(csv.DictReader(p.open(encoding='utf-8-sig'),delimiter=';'))
w=Workbook();w.remove(w.active)
for name,rows in [('Resumo',[x['summary']]),('Anual',x['annual']),('Mensal',x['monthly']),('Diario',x['daily']),('Cinco_Resolvidas',x['changes']),('Operacoes',x['trades']),('Frequencia',x['freq']),('Conferencia',x['audit']['audit']),('Combinacoes',x['combinations']),('Pendencias_Cedro',[r for r in x['trades'] if r['pending']]),('ZIPs_Ja_Recebidos',read(P/'S23_CEDRO_10_ZIPS_JA_RECEBIDOS_A_RESTAURAR.csv'))]:
 s=w.create_sheet(name);keys=list(dict.fromkeys(k for r in rows for k in r));s.append(keys)
 for r in rows:s.append([r.get(k) for k in keys])
 s.freeze_panes='A2';s.auto_filter.ref=s.dimensions
 for c in s[1]:c.font=Font(bold=True)
 for col in s.columns:s.column_dimensions[col[0].column_letter].width=min(45,max(13,max(len(str(c.value or '')) for c in list(col)[:40])+2))
w.save(P/'S23_200_500_Atualizado_20261119.xlsx')
def n(v):return f'{float(v):,.0f}'.replace(',','.')
def rng(a,b):return n(a) if a==b else n(a)+' a '+n(b)
styles=getSampleStyleSheet();story=[]
def para(t):story.append(Paragraph(t,styles['BodyText']));story.append(Spacer(1,8))
def title(t):story.append(Paragraph(t,styles['Heading1']));story.append(Spacer(1,10))
def table(head,rows):
 t=Table([[Paragraph(str(v),styles['BodyText']) for v in r] for r in [head]+rows],repeatRows=1);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#DDE7EF')),('GRID',(0,0),(-1,-1),.3,colors.grey),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),6)]));story.append(t);story.append(Spacer(1,12))
title('S23,6%: stop200 / alvo500 - atualizacao de Replay')
para('Recebido Novas datas.xlsx em 19/11/2026. Cinco abas conferem OHLC e soma das quantidades com os minutos de referencia. Cinco operacoes resolvidas em stop de -200 pontos cada. Resultado original do Modelo D e estudos anteriores preservados.')
table(['Data','Contrato','Entrada','Stop','Alvo','Resultado'],[[r['date'],r['contract'],n(r['entry']),n(r['stop']),n(r['target']),n(r['lower'])] for r in x['changes']])
para('31/07/2026: usuario informou leilao e retorno as 12h34min07s. Primeiro negocio da janela: 12:34:07.958; preco 177.470. A ausencia de negocios antes do retorno nao foi classificada como falha de captura nem preenchida com negocios inventados.')
table(['Periodo','Operacoes','Resultado','Pendentes'],[[r['year'],r['operations'],rng(r['lower'],r['upper']),r['pending']] for r in x['annual']])
s=x['summary'];para('Total: <b>'+rng(s['total_lower'],s['total_upper'])+'</b> pontos brutos. DD diario continuo: <b>'+rng(s['DD_lower'],s['DD_upper'])+'</b> pontos. 386 operacoes; cinco pendencias restantes, todas Cedro. DD por fechamentos diarios cronologicos, pico inicial zero, sem reinicio mensal/anual.')
story.append(PageBreak());title('Pendencias e metodologia')
remaining=[r for r in x['trades'] if r['pending']]
requests=read(E/'estudo_fixos_tres_niveis_20261119/S23_200_500_PENDENCIAS_RECLASSIFICADAS.csv');dates={r['date'] for r in remaining};rr=[r for r in requests if r['date'] in dates]
table(['Data','Contrato','Janela','Estado'],[[r['date'],r['contract'],r['start']+' - '+r['end_exclusive'],'Recuperar bruto Cedro JA recebido; nao e coleta nova'] for r in rr])
para('Os logs completos de agosto-outubro foram enviados historicamente, com 132 ZIPs e hashes conferidos. Neste ambiente, somente 16 ZIPs foram restaurados. Os 10 ZIPs correspondentes a estas cinco datas estao nomeados no CSV de restauracao. Nao pedir nova captura, compra ou reextracao dessas janelas. Nao declarar 2026 fechado antes de comprovar a sequencia.')
f=x['freq'][0];para('Frequencia atual: alvos '+str(f['TP_guaranteed'])+' a '+str(f['TP_possible'])+'; stops '+str(f['SL_guaranteed'])+' a '+str(f['SL_possible'])+'; cortes '+str(f['CUT_guaranteed'])+'. As faixas sao contagens possiveis, nao probabilidades ou promessa de periodicidade.')
para('Fontes: mesmas referencias e entradas, M1 MT5/Profit/Cedro auditado, Replay pontual validado e provas Cedro ja registradas. Nenhuma maxima anterior a entrada foi contada como alvo posterior. Ordens alternativas no mesmo milissegundo foram verificadas; casos com barreiras opostas no mesmo grupo permanecem conservadores. Saidas posteriores a janela podem ser determinadas por M1; horarios sinteticos de trajetorias M1 nao sao negocios reais identificados.')
para('Verificacao independente das cinco operacoes: 20 execucoes, combinando duas trajetorias M1 fora do Replay com duas ordens dos empates no Replay. Totais e DD recalculados por somas escalares. Nao e auditoria integral tick a tick. Resultados brutos sem custos/slippage; nenhuma variante promovida.')
SimpleDocTemplate(str(P/'S23_200_500_Atualizado_20261119.pdf'),pagesize=landscape(A4),leftMargin=28,rightMargin=28,topMargin=24,bottomMargin=24).build(story)
raw=Path('/workspace/dados_brutos_modelo_d/replay_profit/Novas_datas_S23_20261119.xlsx');manifest=dict(uploaded_name='Novas datas.xlsx',sediment_file_id='file_000000002dc8820e9d982c6f9fb32ac1',preserved_path=str(raw),bytes=raw.stat().st_size,sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),user_observation='31/07/2026 houve leilao; voltou as 12h34min07s.',observed_first_trade='2026-07-31 12:34:07.958',accepted_minutes=5,resolved_operations=5,all_five_results='SL:-200',summary=x['summary'],verification=json.loads((P/'VERIFICACAO.json').read_text()),original_and_previous_results_unchanged=True,scope='Only S23.6 N089 stop200 target500 and its contribution in three previously reported combinations updated.',new_Replay_requests=0,remaining_Cedro_recovery_windows=5,sources=[dict(path=str(f.relative_to(R)),sha256=hashlib.sha256(f.read_bytes()).hexdigest()) for f in [E/'estudo_niveis_auxiliares_20261119/MANIFESTO.json',E/'estudo_fixos_tres_niveis_20261119/S23_200_500_REPLAY_5_DATAS.csv',E/'estudo_fixos_tres_niveis_20261119/S23_CEDRO_10_ZIPS_JA_RECEBIDOS_A_RESTAURAR.csv']])
(P/'MANIFESTO.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print('PDF/Excel/manifest saved',x['summary'])
