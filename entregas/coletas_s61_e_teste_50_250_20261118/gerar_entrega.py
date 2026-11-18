from pathlib import Path
import csv,json,hashlib,datetime as dt,textwrap,re
from collections import Counter
import numpy as np
import openpyxl,fitz
from openpyxl.styles import Font,PatternFill,Alignment
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
P=Path(__file__).parent;R=P.parents[1];E=R/'entregas'
def read(p):
 with p.open(encoding='utf-8-sig') as f:return list(csv.DictReader(f,delimiter=';'))
def n(v):return f'{float(v):,.0f}'.replace(',','.')
def ran(a,b):return n(a) if float(a)==float(b) else n(a)+' a '+n(b)
def yes(v):return v is True or str(v)=='True'
monthly=read(P/'MENSAL_50_250.csv');annual=read(P/'ANUAL_50_250.csv');daily=read(P/'DIARIO_50_250.csv');ops=read(P/'OPERACOES_50_250.csv');windows=read(P/'JANELAS_AGRUPADAS_50_250.csv');priority=read(P/'20_JANELAS_PRIORITARIAS_E_COINCIDENCIAS.csv');extras=read(P/'JANELAS_EXTRAS_2_E_3_COLOCADOS.csv');summary=json.loads((P/'RESULTADO_50_250.json').read_text());cross=json.loads((P/'CRUZAMENTO_PENDENCIAS.json').read_text())
# Confirm all source-snapshot hashes: existing S61 studies remain byte-identical.
preserved=json.loads((P/'ESTUDOS_PRESERVADOS_SHA256.json').read_text())
for r in preserved['files']:assert hashlib.sha256((R/r['path']).read_bytes()).hexdigest()==r['sha256'],r['path']
assert len(monthly)==34 and len(ops)==1485 and len(daily)==709 and len(priority)==20
for a in annual:
 rs=[m for m in monthly if m['month'].startswith(a['year'])]
 for k in ['lower','upper','operations']:assert sum(float(r[k]) for r in rs)==float(a[k])
for d in daily:
 rr=[o for o in ops if o['date']==d['date']];assert len(rr)==int(d['operations'])<=5
 for k in ['lower','upper']:assert sum(float(r[k]) for r in rr)==float(d[k])
 assert len({r['level'] for r in rr})==len(rr)
assert sum(yes(r['unresolved']) for r in ops)==140
assert sum(float(r['lower']) for r in monthly)==-8495 and sum(float(r['upper']) for r in monthly)==33505
assert cross['shared_second_minutes']==20 and cross['shared_third_minutes']==13
# Account for the three cuts exactly; all uncertain trades are TP/SL alternatives.
stop=sum(r['outcomes']=='SL:-50' for r in ops);target=sum(r['outcomes']=='TP:250' for r in ops);cuts=[r for r in ops if r['outcomes'].startswith('CORTE:') and '|' not in r['outcomes']]
assert (stop,target,len(cuts))==(1124,218,3)
assert sum(float(r['lower']) for r in cuts)==205
assert -8495+300*29>0 and -8495+300*28<0
checks=dict(preserved_study_files=len(preserved['files']),preserved_base_commit=preserved['base_commit'],prior_studies_hashes_unchanged=True,month_year_and_day_trade_reconciliation=True,max_entries_per_day=5,no_duplicate_level_date=True,exact_stop_operations=stop,exact_target_operations=target,exact_cut_operations=len(cuts),exact_cut_points=205,unresolved_operations=140,unknown_targets_needed_for_gross_positive=29,out_of_unknown_operations=140,monthly_rows=34,no_lower_day_below_minus250=True,coincidence_second_minutes=20,coincidence_third_minutes=13)
(P/'CONFERENCIA_FINAL.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n')
# Main workbook.
def style(sh):
 sh.freeze_panes='A2';sh.auto_filter.ref=sh.dimensions
 for c in sh[1]:c.font=Font(color='FFFFFF',bold=True);c.fill=PatternFill('solid',fgColor='17354E');c.alignment=Alignment(wrap_text=True)
 for col in sh.columns:sh.column_dimensions[col[0].column_letter].width=min(60,max(15,max(len(str(c.value or '')) for c in list(col)[:80])+2))
def table(wb,name,rs):
 sh=wb.create_sheet(name)
 if not rs:sh.append(['Sem itens']);return sh
 keys=list(rs[0]);sh.append(keys)
 for r in rs:
  out=[]
  for k in keys:
   v=r[k]
   if k not in ['date','month','year','contract','level','outcomes','entry_minute','source','start','end_exclusive','minute']:
    try:v=float(v)
    except (TypeError,ValueError):pass
   out.append(v)
  sh.append(out)
 style(sh);return sh
wb=openpyxl.Workbook();wb.remove(wb.active)
table(wb,'Anual',annual)
for yr in ['2024','2025','2026']:table(wb,yr+'_Mensal',[r for r in monthly if r['month'].startswith(yr)])
for name,rs in [('Diario',daily),('Por_Nivel',read(P/'POR_NIVEL_50_250.csv')),('Operacoes',ops),('Janelas_50_250',windows),('S61_Coleta_Prioritaria',priority),('Outras_Coletas',extras),('Cedro_Exato',read(P/'CEDRO_50_250_OPERACOES_EXATAS.csv'))]:table(wb,name,rs)
wb.save(P/'Teste_50_250_Resultados_2024_2025_2026.xlsx')
# Standalone data collection template, only20prioritywindows.
w=openpyxl.Workbook();w.remove(w.active);table(w,'Coleta_20_Janelas',priority)
table(w,'Instrucoes',[dict(item='Prioridade',texto='Somente estas20janelas paraS61stop100/alvoS50original. Asmesmas cópias ajudam o2ºem20minutos eo3ºem13.'),dict(item='Captura',texto='Copiar minuto inteiro e alguns segundos antes/depois. Manter milissegundos,ordem e negócios idênticos. Não filtrar nem deduplicar.'),dict(item='Sem negócios',texto='Informar leilão/ausência de cotação sem inventar linhas. ConfirmaremosOHLC/quantidade ecompletude antes de fechar.'),dict(item='Outros pedidos',texto='Os139intervalos do50/250 não são solicitação automática. Primeiro finalizar os20doS61.'),dict(item='Contratos',texto='Esperados pelas referências preservadas. Confirmar correspondência depreços na cópia.')])
for r in priority:
 sh=w.create_sheet(r['date'][8:]+'-'+r['date'][5:7]+'_'+r['start'][:5].replace(':',''));sh.append(['Data','Compradora','Valor','Quantidade','Vendedora','Agressor','Total (BRL)','Agente Agressor']);sh.freeze_panes='A2'
w.save(P/'Coleta_S61_Stop100_20_Janelas.xlsx')
# PDF for priority windows.
c=canvas.Canvas(str(P/'Coleta_S61_Stop100_20_Janelas.pdf'),pagesize=A4);W,H=A4;c.setTitle('ColetaS61stop100 —20janelas prioritárias')
c.setFont('Helvetica-Bold',18);c.drawString(30,H-40,'S61 stop100 | Coleta prioritária');c.setFont('Helvetica',10);c.drawString(30,H-63,'20/20minutos coincidem com o2º;13/20também com o3º.');y=H-99
c.setFont('Helvetica-Bold',9)
for x,t in [(30,'Data'),(120,'Contrato'),(220,'Intervalo'),(350,'3º mesmo minuto?'),(475,'50/250?')]:c.drawString(x,y,t)
c.setFont('Helvetica',9)
for r in priority:
 y-=24;c.drawString(30,y,r['date']);c.drawString(120,y,r['contract']);c.drawString(220,y,r['start'][:5]+'–'+r['end_exclusive'][:5]);c.drawString(370,y,'Sim' if yes(r['third_place_same_minute']) else 'Não');c.drawString(480,y,'Sim' if yes(r['also_helps_50_250']) else 'Não')
y-=33
for t in ['Fim exclusivo. Horário de São Paulo/fonte; copiar alguns segundos antes/depois.','Minuto inteiro, sem filtros ou deduplicação. Preservar milissegundos e ordem.','2º=S61_48/S61_68;3º=S61_60. Não é garantia de fechamento sem validar negócios.','Depois destas20:2ºtem8minutos adicionais em7datas;3ºtem1data adicional.','O estudoS61 e os resultados originais permanecem preservados.']:
 c.drawString(30,y,t);y-=16
c.setFont('Helvetica',8);c.drawString(30,24,'18/11/2026 | Prioridade solicitada pelo usuário | Fonte e auditorias preservadas');c.save()
# Main monthly PDF: one page per year, plus method/results limitations.
names=['Janeiro','Fevereiro','Março','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro','Novembro','Dezembro']
c=canvas.Canvas(str(P/'Teste_50_250_Mensal_2024_2025_2026.pdf'),pagesize=A4);c.setTitle('Modelo D — stop50 alvo250 — resultado mensal')
for yr in ['2024','2025','2026']:
 c.setFillColorRGB(.06,.16,.25);c.rect(0,H-110,W,110,fill=1,stroke=0);c.setFillColorRGB(1,1,1);c.setFont('Helvetica-Bold',22);c.drawString(30,H-43,yr+' | Stop50 / alvo250');c.setFont('Helvetica',11);c.drawString(30,H-70,'Cinco níveis do D; mesmas entradas; até uma operação por nível/dia.');c.drawString(30,H-91,'Janeiro a outubro' if yr=='2026' else 'Ano completo');c.setFillColorRGB(.06,.16,.25);y=H-150
 xs=[30,255,365,462,558];c.setFont('Helvetica-Bold',10)
 for x,t in zip(xs,['Mês','Limite inferior','Limite superior','Operações','Pendentes']):(c.drawString if x==30 else c.drawRightString)(x,y,t)
 c.setFont('Helvetica',10)
 for r in monthly:
  if not r['month'].startswith(yr):continue
  y-=30;c.drawString(30,y,names[int(r['month'][5:])-1])
  for x,k in zip(xs[1:],['lower','upper','operations','pending_operations']):c.drawRightString(x,y,n(r[k]))
 a=next(r for r in annual if r['year']==yr);y-=37;c.setFont('Helvetica-Bold',11);c.drawString(30,y,'TOTAL');c.drawRightString(255,y,n(a['lower']));c.drawRightString(365,y,n(a['upper']));c.drawRightString(462,y,n(a['operations']));c.drawRightString(558,y,n(a['pending_operations']));y-=35;c.setFont('Helvetica',10)
 for t in ['DD diário isolado do ano: '+ran(a['DD_year_lower'],a['DD_year_upper'])+' pontos.',str(a['pending_days'])+' dias com pendência. Valores brutos; nenhuma sequência favorável escolhida.','Faixa não é lucro realizado nem estimativa de probabilidade.','Corte18h preservado; houve3cortes no período, por isso totais não são só múltiplos50.','Não foi adicionado bloqueio após o primeiro alvo nem stop financeiro diário.']:
  c.drawString(30,y,t);y-=18
 c.setFont('Helvetica',8);c.drawString(30,25,'18/11/2026 | M1 + Replay disponível + Cedro recuperado | D original preservado');c.showPage()
c.setFont('Helvetica-Bold',18);c.drawString(30,H-40,'O que a conta diária permite concluir');y=H-77

def para(t,bold=False):
 global y
 t=re.sub(r'(?<=[a-zà-ÿ])(?=\d)|(?<=\d)(?=[a-zà-ÿ])',' ',t)
 c.setFont('Helvetica-Bold' if bold else 'Helvetica',10)
 for line in textwrap.wrap(t,95):c.drawString(30,y,line);y-=15
 y-=9
para('Quatro stops de50 e um alvo250 somam+50pontos brutos. Se todas as saídas foremTP/SL, resultado=300vezes o número de alvos-50vezes o número de operações. Comaté5entradas,um alvo basta para resultado positivo antes decustos.',True)
para('Isso não garante um alvo por dia. Na base709pregões:100dias sem entrada,110com1,226com2,195com3,52com4 e26com5entradas. As entradas dependem da elegibilidade e do toque nos níveis originais; não foram forçadas cinco.')
para('Total ainda não fechado:-8.495a+33.505pontos;DDdiáriocontínuo2.050a10.195;140operações pendentes em116dias,139intervalos distintos. Os extremos de níveis diferentes podem exigir sequências incompatíveis; são limites,não trajetórias confirmadas.',True)
para('Foram determinados1.124stops,218alvos e3cortes(+60,+105,+40). As140restantes permitemSL/TP. Seriam necessários pelo menos29alvos dentreessas140para o total bruto ficar positivo(29dariam+205). Isso não atribui probabilidade a esses alvos.')
para('Apenas saídasTP/SL exigem mais de16,67% de alvos para lucro bruto no longo prazo. Comcustos a exigência sobe. Um alvo e4stops são+50brutos;comcusto10pontos poroperação completa,essas5operações ficamnozero.')
para('Nenhum limiteinferior poroperação ficou abaixo-50 neste teste,e nenhum dia abaixo-250. Isso é resultado sob a convenção depreços do modelo; não certifica preenchimentos nem garante teto deperda real comgaps,custos ou slippage.')
para('As8datasCedrorecuperadas foram percorridas em39.031.316negócios;20novasoperações e todasstop-50,total-1.000. MotorC++integral confrontado comPython independente;40estadosoriginais reproduzidos. Demaisdatas usamM1auditado/Profit/MT5 comReplayválido eprovas baseadas no original.')
para('Os20pedidosS61continuam prioridade.20também ajudam o2º,13o3º,e5contêm dúvidas deste50/250. Não pedir as139janelas novas automaticamente antes de revisar o resultado. Custos5/10na planilha são sensibilidades hipotéticas. Sem compra dehistórico.')
c.setFont('Helvetica',8);c.drawString(30,25,'18/11/2026 | 2026 limitado a janeiro-outubro | Não fechar a estratégia escolhendo o limite superior.');c.save()
# Minimal synthetic motor checks: chronology and no same-entry business exit.
# Verify raw inputs never changed; previous closed source hash list unchanged.
old=json.loads((E/'estudo_saidas_niveis_20261117/MANIFESTO.json').read_text())
for h in old['source_closed_files']:assert hashlib.sha256((R/h['path']).read_bytes()).hexdigest()==h['sha256']
(P/'.gitattributes').write_text('*.pdf binary\n*.xlsx binary\n');(P/'.gitignore').write_text('__pycache__/\n')
manifest=dict(date='2026-11-18',first_priority='S61_42_STOP100_ALVO_ORIGINAL',previous_studies_preserved=True,snapshot='ESTUDOS_PRESERVADOS_SHA256.json',coleta_summary=cross,fixed_test_summary=summary,checks=checks,source_origins=dict(Counter(r['source'] for r in daily)),not_closed_while_pending=True,no_new_entry_rules=True,no_forced_five_entries=True,no_reentry=True,no_stop_after_first_target=True,raw_source_ids_retained='RESTAURACAO_FONTES.json',main_original_unchanged=True)
(P/'MANIFESTO.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
(P/'LEIA_PRIMEIRO.md').write_text('''# Duas tarefas preservadas — S61stop100 e stop50/alvo250

Estudos anteriores preservados byte a byte,com hashes e commit emESTUDOS_PRESERVADOS_SHA256.json. A primeira prioridade é fecharS61_42stop100/alvoS50original:20janelas,comcontrato/horário,noTXT/PDF/planilha de coleta. Todas20coincidem emdata E minuto comS61_48/S61_68;13comS61_60. Para o2ºrestam8minutos em7datas;para o3ºresta15/05/2026. Não prometer fechamento de outroscenários sem validar os negócios. NenhumresultadoS61foi alterado nestaentrega.

Em paralelo,triagemnova emtodoscinconíveis:stop50/alvo250,umaentrada pornível/dia,mesmaelegibilidade/referência,toqueinclusive,grade5,corte18h,semreentrada,semforçarcincoentradas,sem bloqueioapósprimeiroalvo. Não foi criado stopfinanceirodiário. De709dias,só26tiveramcincoentradas;100tiveramzero. Conferência de20operações em39.031.316negóciosCedrorecuperados,comestados originais reproduzidos ePython independente;foram20stops-50.

Resultado mensal nos3anos comlimites:2024-3590a1210,2025-2555a4345,2026jan-out-2350a27950. Total-8495a33505,DD diário contínuo2050a10195,140operações pendentes em116dias e139janelas. Não declarar lucroouprejuízoúnico antes de resolver sequência. Valoresbrutos,semcustos/fillscertificados. Limites entre níveis podem não ser simultaneamente realizáveis.

Foi conferida a conta quatrostops+umalvo=+50brutos. Cincoentradas máximas não garantemumalvo,nem entradas independentes. Os3cortes do período somaram205(+60,+105,+40). Determinados1124SL/218TP;as140incertas permitemSL/TP. Precisam29novosTPentreas140para saldo bruto positivo,sem atribuirprobabilidade. Sob os preços do modelo não houve dia abaixo-250;isso não certifica teto realcomslippage,custos ougaps.

Sóos20pedidosS61são prioridade de coleta.139janelas50/250 estão listadas paraauditoria,não como solicitação automática. Cinco das20cópiasS61também ajudam50/250. Arquivosbrutospreservados localmente;16IDs para restauração registrados. OriginalD emesesfechados intactos. Controle10/07/2026dispensado não reaberto para ooriginal.
''')
for name,expected in [('Coleta_S61_Stop100_20_Janelas.pdf',1),('Teste_50_250_Mensal_2024_2025_2026.pdf',4)]:
 doc=fitz.open(P/name);assert len(doc)==expected
 for i,page in enumerate(doc):
  for b in page.get_text('dict')['blocks']:
   for ln in b.get('lines',[]):
    for sp in ln['spans']:
     assert sp['bbox'][2]<595 and sp['bbox'][3]<842,(name,i,sp['text'])
print('Conferido:20coletas,34meses,140pendencias;26diascom5entradas;estudosanterioresintactos')
