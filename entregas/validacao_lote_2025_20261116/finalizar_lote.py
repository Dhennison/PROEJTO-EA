"""Freeze ten closed2025months and retain April pending. Separate DD blocks at missing
months,never insert zero or reset monthly. Preserve every previously closed daily point.
"""
from pathlib import Path
from decimal import Decimal as D
from collections import Counter
import json,csv,hashlib,zipfile,textwrap
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import fitz,openpyxl
from openpyxl.styles import Font,PatternFill,Alignment
P=Path(__file__).parent;R=P.parents[1];PRE=R/'entregas/preparacao_jan_nov_2025_20261115'
def read(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter=';'))
def write(p,rs):
 if not rs:return
 with p.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rs[0]),delimiter=';',lineterminator='\n');w.writeheader();w.writerows(rs)
def n(v):return format(D(v).normalize(),'f')
def val(v):return D(v.replace(',','.'))
def fmt(v):return '-' if v is None or v=='' else 'PENDENTE' if v=='PENDENTE' else f'{D(v):,.2f}'.replace(',','X').replace('.',',').replace('X','.')
ss=json.loads((P/'RESULTADOS_TODOS_MESES.json').read_text());assert len(ss)==11
assert [(s['month'],s['pending']) for s in ss if s['pending']]==[('2025-04',1)]
expected={'2025-01':-2405,'2025-02':-1180,'2025-03':-970,'2025-05':-2915,'2025-06':895,'2025-07':2740,'2025-08':-460,'2025-09':-385,'2025-10':-1055,'2025-11':-300}
monthly=[];days={};stats={};allops=[];proofs=[];grades=[]
for s in ss:
 folder=next(d for d in P.iterdir() if d.is_dir() and d.name.startswith(s['month'][-2:]+'_'))
 src=next(d for d in PRE.iterdir() if d.is_dir() and d.name.startswith(s['month'][-2:]+'_'))
 ops=read(folder/'OPERACOES_APOS_REPLAY.csv');daily=read(folder/'DIARIO_APOS_REPLAY.csv');days[s['month']]=daily;complete=s['pending']==0
 cmp=[r for r in daily if r['work_points']!=''];extra=[r for r in daily if r['work_points']==''];cmp_complete=all(r['test_points']!='PENDENTE' for r in cmp)
 cmp_test=sum((D(r['test_points']) for r in cmp),D(0)) if cmp_complete else None;work=sum((val(r['work_points']) for r in cmp),D(0));ext_complete=all(r['test_points']!='PENDENTE' for r in extra);ext=sum((D(r['test_points']) for r in extra),D(0)) if ext_complete else None
 principal=sum((D(r['test_points']) for r in daily),D(0)) if complete else None
 assert principal is None or principal==D(expected[s['month']])
 for r in daily:
  if r['test_points']!='PENDENTE':r['test_points']=n(r['test_points'])
  if r['work_points']:r['work_points']=n(val(r['work_points']))
  if r['difference']:r['difference']=n(r['difference'])
 row=dict(month=s['month'],status='ENCERRADO_M1_REPLAY' if complete else 'PENDENTE_COMPLEMENTO',pregoes=len(daily),operacoes=len(ops),pendentes=s['pending'],principal=n(principal) if complete else None,comparavel_Work_teste=n(cmp_test) if cmp_test is not None else None,Work_referencia=n(work),diferenca_comparavel=n(cmp_test-work) if cmp_test is not None else None,complemento_fora_Work=n(ext) if ext is not None else None,datas_fora_Work=','.join(r['date'] for r in extra),motivos=dict(Counter(o['reason'] for o in ops)))
 monthly.append(row);allops.extend(ops)
 for r in s['results']:
  if not r['resolved']:continue
  if r.get('partial_prefix_invariance_proof'):proofs.append(dict(month=s['month'],**r))
  if r['primary']['reason']!=r['mathematical'].get('reason'):grades.append(dict(date=r['date'],level=r['level'],grade_reason=r['primary']['reason'],grade_points=r['primary']['points'],mathematical_reason=r['mathematical']['reason'],mathematical_points=r['mathematical'].get('points',''),grade_control=r['grade_control']))
 s.update(status=row['status'],principal=row['principal'],comparavel_Work_teste=row['comparavel_Work_teste'],diferenca_comparavel=row['diferenca_comparavel'],complemento_fora_Work=row['complemento_fora_Work'],final_operation_reasons=row['motivos'],closed=complete,coverage_controls_conferred='CONFERENCIA_FINAL.json',main_is_grade5=True,source_method='M1_MT5_PLUS_TARGETED_PROFIT_REPLAY;WORK_M5_CONTEXT;NO_CERTIFIED_FILLS')
 (folder/('RESULTADO_FINAL.json' if complete else 'RESULTADO_PARCIAL.json')).write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
 (folder/'PROGRESSO_RESOLUCAO.json').write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n')
 write(folder/'DIARIO_APOS_REPLAY.csv',daily)
 if complete:write(folder/'OPERACOES_FINAIS.csv',ops)
 notes=f'''{s['month']} — MODELO D — {row['status']}
Principal:{row['principal'] if complete else 'PENDENTE;NAO SOMAR SUBTOTAL'} pontos.
Work original:{row['Work_referencia']};nosso comparável:{row['comparavel_Work_teste']};
diferença comparável:{row['diferenca_comparavel']}. Complemento foraWork:
{row['complemento_fora_Work']};datas:{row['datas_fora_Work'] or 'nenhuma'}.
{len(daily)}pregões/{len(ops)}operações conhecidas;{s['pending']}pendentes.
M1+Replay pontual,grade5,1contrato/nível,toqueinclusivo,corte18h,parametrosD originais.
Sem custos/fila/slippage ou fills certificados. Não é mês inteiro de negócios.
Preparo,referências,ajustes ecomparaçõesM1/M5 preservados na pasta depreparação.
Resultados anteriores não alterados. Fonte:XLSXdaRelease,39abas/1940063registros,
SHA256e0992ed7c4b603a1a24307f30b94713952af9bebae9f5c417fd81c010817fd13.
Bruto preservado localmente;não duplicado no históricoGit;Release indicada no manifesto.
'''
 for r in s['results']:
  if r['resolved']:
   pr=r['primary'];notes+=f"{r['date']} {r['level']}: {pr['reason']} {pr['points']};entrada {pr['entry']['time']};saída {pr['exit']['time']};fonte {pr['exit_source']}.\n"
   if r.get('partial_prefix_invariance_proof'):notes+='Prefixo parcial aceito apenas para motivo/pontos:barreiraoposta fora de todoM1;entrada/saída reais podem ser anteriores. Não certificar horários observados como únicos.\n'
  else:notes+=f"PENDENTE {r['date']} {r['level']} {r['required_minute']}: {r['reason']}.\n"
 notes+='CANDLE indica minuto,não horário exato. Dois desempatesms ebarreiras opostas foramconferidos. Dadosde leilão:relato do usuário +cópias/M1;semcriar negócios ausentes. Ressalvas quantitativas preservadas.\n'
 (folder/'LEIA_RESULTADO.txt').write_text(notes)
# Append previously CLOSED sources without touching them.
oldmonths=[('2025-12','profit_dezembro_2025_20261115'),('2026-01','profit_janeiro_20261115'),('2026-02','profit_fevereiro_20261114'),('2026-03','profit_marco_20261113'),('2026-04','profit_abril_20261113'),('2026-05','profit_maio_20261113'),('2026-06','profit_junho_20261113'),('2026-07','profit_winq26_julho_20261113')]
old_expected=[3135,-1620,-3545,350,5720,-780,3405,1100]
old_sources=[]
for (m,folder),expected_total in zip(oldmonths,old_expected):
 path=R/'entregas'/folder/'DIARIO_APOS_JANELAS.csv';rs=read(path);assert sum(D(r['test_points']) for r in rs)==expected_total
 old_sources.append(dict(path=str(path.relative_to(R)),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),points=expected_total))
 days[m]=rs
# Two continuous blocks only. Missing April must not become zero.
blocks={'2025_01_03':['2025-01','2025-02','2025-03'],'2025_05_2026_07':[m for m in sorted(days) if m>='2025-05']}
curves={};blockstats={}
for key,months in blocks.items():
 rows=[];balance=peak=maxdd=D(0);wb=wp=wd=ct=cp=cd=D(0);aligned=[]
 for m in months:
  assert all(r['test_points']!='PENDENTE' for r in days[m])
  for r in days[m]:
   pts=D(r['test_points']);balance+=pts;peak=max(peak,balance);maxdd=max(maxdd,peak-balance)
   rows.append(dict(date=r['date'],test_points=n(pts),test_balance=n(balance),test_peak=n(peak),test_current_DD=n(peak-balance),test_max_DD=n(maxdd),series='M1_PLUS_TARGETED_REPLAY',block=key))
   if r['work_points']!='':
    w=val(r['work_points']);wb+=w;wp=max(wp,wb);wd=max(wd,wp-wb);ct+=pts;cp=max(cp,ct);cd=max(cd,cp-ct)
    aligned.append(dict(date=r['date'],test_points=n(pts),test_balance=n(ct),test_max_DD=n(cd),work_points=n(w),work_balance=n(wb),work_max_DD=n(wd),scope='WORK_COMPARABLE_DATES_ONLY',block=key))
  stats[m]=dict(block=key,test_DD_accum=n(maxdd),test_balance=n(balance),Work_comparable_DD=n(wd),test_comparable_DD=n(cd))
 assert [r['date'] for r in rows]==sorted(set(r['date'] for r in rows))
 curves[key]=rows;write(P/f'CURVA_M1_REPLAY_{key}.csv',rows);write(P/f'CURVA_COMPARAVEL_WORK_{key}.csv',aligned)
 blockstats[key]=dict(start=rows[0]['date'],end=rows[-1]['date'],days=len(rows),test_points=n(balance),test_DD=n(maxdd),Work_DD_on_comparable_dates=n(wd),test_DD_on_comparable_dates=n(cd),monthly_reset=False)
# Exact equality of old daily results against the new current extension.
previous=read(R/'entregas/profit_dezembro_2025_20261115/CURVA_DEZEMBRO2025_JANEIRO_FEVEREIRO_MARCO_ABRIL_MAIO_JUNHO_JULHO_M1_REPLAY.csv')
assert [(r['date'],D(r['test_points'])) for r in curves['2025_05_2026_07'] if r['date']>='2025-12-01']==[(r['date'],D(r['test_points'])) for r in previous]
write(P/'RESUMO_MENSAL.csv',monthly);write(P/'DIFERENCAS_GRADE_MATEMATICO.csv',grades)
# Precise missing fragments only. Existing copies remain intact.
pending_rows=[dict(date='2025-04-09',contract='WINJ25',level='R61.8',capture_start='14:20:00',capture_end_exclusive='14:21:00',reason='Aba recebida cobre09:20;necessario14:20',do_not_repeat='02jan complementado e validado;demais dias/abas validados')]
write(P/'COMPLEMENTO_PENDENTE.csv',pending_rows)
summary=dict(status='DEZ_MESES_ENCERRADOS_ABRIL_PENDENTE',newly_closed_months=[s['month'] for s in ss if not s['pending']],pending_months=['2025-04'],monthly=monthly,continuous_blocks=blockstats,global_DD_since_January2025=None,January_complement=json.loads((P/'COMPLEMENTO_02JAN.json').read_text()),DD_global_unavailable_reason='April2025 incomplete;no zero insertion/no concatenation across incomplete months',current_continuous_curve='CURVA_M1_REPLAY_2025_05_2026_07.csv',old_daily_results_preserved=old_sources,source_records=1940063,source_sheets=39,source_asset='https://github.com/Dhennison/PROEJTO-EA/releases/download/dados-replay-2025-20261116/Janeiro.a.Novembro.2025.xlsx',source_sha256='e0992ed7c4b603a1a24307f30b94713952af9bebae9f5c417fd81c010817fd13',source_local='/workspace/dados_brutos_modelo_d/replay_profit/Janeiro_a_Novembro_2025_Release.xlsx',source_published_by_user=True,raw_copied_into_Git_history=False,main='D_ORIGINAL_GRADE5',method='M1_PLUS_TARGETED_REPLAY_NO_CERTIFIED_FILLS',costs=False,full_tape=False,pending=pending_rows,partial_prefix_proof=proofs[0]['partial_prefix_invariance_proof'])
(P/'RESULTADOS_TODOS_MESES.json').write_text(json.dumps(ss,ensure_ascii=False,indent=2)+'\n')
(P/'RESULTADO_CONSOLIDADO.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
# Reports:19months,including explicit pending page;no manufactured monthly totals.
months=sorted(days);pdf=P/'Modelo_D_Janeiro2025_Julho2026_Diario.pdf';c=canvas.Canvas(str(pdf),pagesize=A4);W,H=A4
ptnames={'01':'JANEIRO','02':'FEVEREIRO','03':'MARCO','04':'ABRIL','05':'MAIO','06':'JUNHO','07':'JULHO','08':'AGOSTO','09':'SETEMBRO','10':'OUTUBRO','11':'NOVEMBRO','12':'DEZEMBRO'}
for m in months:
 rs=days[m];state=next((x for x in monthly if x['month']==m),None);pend=any(r['test_points']=='PENDENTE' for r in rs)
 c.setFont('Helvetica-Bold',15);c.drawString(32,H-38,f'MODELO D - {ptnames[m[-2:]]} / {m[:4]}')
 c.setFont('Helvetica',9);c.drawString(32,H-57,'M1 + Replay pontual | Grade 5 | Pontos nos niveis | '+('PENDENTE DE COMPLEMENTO' if pend else 'ENCERRADO'))
 y=H-87
 for x,label in [(32,'Data'),(210,'Work'),(327,'Nosso'),(455,'Diferenca')]:c.drawString(x,y,label)
 for r in rs:
  y-=18;c.drawString(32,y,r['date'][8:]+'/'+r['date'][5:7]+'/'+r['date'][:4])
  for x,k in [(278,'work_points'),(407,'test_points'),(563,'difference')]:c.drawRightString(x,y,fmt(r[k].replace(',','.') if k=='work_points' and r[k] else r[k]))
 y-=28;c.setFont('Helvetica-Bold',10);c.drawString(32,y,'TOTAL DO MES')
 work=sum((val(r['work_points']) for r in rs if r['work_points']!=''),D(0));total=None if pend else sum(D(r['test_points']) for r in rs)
 c.drawRightString(278,y,fmt(work));c.drawRightString(407,y,'PENDENTE' if pend else fmt(total));c.drawRightString(563,y,'-' if pend or any(r['work_points']=='' for r in rs) else fmt(total-work))
 y-=22;c.setFont('Helvetica',8.5)
 if any(r['work_points']=='' for r in rs):
  c.drawString(32,y,'Work: apenas datas comparaveis; traco indica ausencia de referencia.');y-=15
  if state and not pend:c.drawString(32,y,f'Nosso comparavel {fmt(state["comparavel_Work_teste"])} | Complemento {fmt(state["complemento_fora_Work"])}');y-=15
 if m in stats:
  st=stats[m];start=blockstats[st['block']]['start'];c.drawString(32,y,f'DD nosso continuo desde {start}: {fmt(st["test_DD_accum"])} (sem reinicio mensal).');y-=15
  c.drawString(32,y,f'DD em datas comparaveis: nosso {fmt(st["test_comparable_DD"])} | Work {fmt(st["Work_comparable_DD"])}.');y-=15
 else:c.drawString(32,y,'DD do teste nao ampliado atraves de mes pendente.');y-=15
 for line in ['Blocos separados pela pendencia de abril2025; nao inserir zero.','Serie Cedro agosto-outubro2026 permanece separada.','Sem custos/fila/slippage ou garantia de preenchimento; nao e fita integral.']:
  c.drawString(32,y,line);y-=15
 c.showPage()
c.save()
with fitz.open(pdf) as d:
 assert len(d)==19
 for page,m in zip(d,months):
  text=page.get_text()
  for r in days[m]:assert r['date'][8:]+'/'+r['date'][5:7]+'/'+r['date'][:4] in text
  if m=='2025-04':assert 'PENDENTE DE COMPLEMENTO' in text
notes=f'''LOTE JANEIRO A NOVEMBRO/2025 — VALIDACAO16/11/2026
Release recebida:39abas,1940063registros,XLSX56091431bytes,SHA256 conferido.
Dez meses encerrados;Abril permanecependente de um complemento.02jan foi complementado.
D original/grade5/toqueinclusivo/1contrato/corte18h,sem custos/fills certificados.
M1+Replay pontual,não mês inteiro de negócios. Brutos preservados,sem deduplicação.

FECHAMENTOS E COMPARAVEIS
'''
for row in monthly:notes+=f"{row['month']}: principal{row['principal'] if row['principal'] is not None else 'PENDENTE'}, comparavel{row['comparavel_Work_teste']}, Work{row['Work_referencia']}, complemento{row['complemento_fora_Work']}.\n"
notes+='''
02JAN COMPLEMENTADO E VALIDADO
NovoTXT56878registros09:00:38.125–09:02:12.123;minuto09:01completo.
Todos42252registrosanteriores formambloco contiguo igual emhorario/preco/quantidade.
Usado novo fluxo completo,sem concatenar ou deduplicar. R38.2SL-375
no minuto09:04,com entrada09:01:16.180. Janeirofechado-2405,Workcomparavel separado.

UNICO COMPLEMENTO NECESSARIO
09abrWINJ25R61.8:enviar14:20–14:21 algunssegundosantes/depois;
aba recebida e09:19:58–09:21:04. Demaiscopias preservadas,nao repetir.

VALIDACAO E CASOS DE SEQUENCIA
41operacoesReplay/grade validadas,39ambiguidades originais e2controlesgrade.
Mar07S50 entrou09:47M1 e precisouReplay10:30 aposentrada,como preparado;
nao exigir repetir09:47,poisposicao antes da copia e conhecida pelos candles.
Mar13R61.8:copia comeca11:13:20.698,parcial. Alvo60 observado aposentrada,
stop126275 fora de toda a faixaM1(high125830). Qualquer ramo do prefixo
omitido fica aberto ou ja terminaTP;nao podeSL. LogoTP60 e invariavel.
Nao certificar entrada11:13:52.410/saida11:13:54.829 como unicos instantes
possiveis,poisuma entrada/saida anteriores no prefixo nao sao excluidas.
Janeiro02 nao passava essa prova no primeiro arquivo:alvo poderia ser anterior
no prefixo. NovoTXTcompleto resolveu a pendencia,sem aprovar o trecho antigo sozinho.
Doisdesempatesms ebarreirasopostas conferidos. Regressoes contra maxima
preentrada eentrada incompleta passaram. Nivel ja aberto so e transportado
seentradaM1 precede a copia;seentrada ocorre dentro da copia,aguardar toque.

DIFERENCAS DE GRADE,CONTROLES MATEMATICOS SEPARADOS
'''
for g in grades:notes+=f"{g['date']} {g['level']}: grade{g['grade_reason']} {g['grade_points']};matematico{g['mathematical_reason']} {g['mathematical_points']}.\n"
notes+='''
LEILOES/ABERTURAS E COBERTURA
03jun:copia09:00:49.714–10:01:12.000,ultimoantespausa09:03:09.264,
retorno09:56:21.720. Semnovasentradas elegiveis nosprecos copiados;
minutos relevantesOHLCiguais,M1quantidade09:03difere-1,ressalvapreservada.
30jul:R61.8TP80 as15:42:37.020,antesleilaoentre15:42:39.719 e15:47:23.012.
09out abre09:03:31.490 e11nov09:03:09.401;OHLC/quantidade dasaberturas
conferemM1. Nao pedir negocios anteriores semnegociacao.
21ago:aba29 AGO21 cobre09:00:55.663–09:03:07.533,agora minuto09:02
completo92869contratos;S50SL-375 no minuto09:06. S38.2SL-375 preservado.
S61.8TP170 as10:26:23.070 confirmado noTXT anterior;leiloes reportados
pelo usuario compatíveiscomausencias. TXTtem200001registros,limiteobservado;
nao e fita inteira. Quantidade09:16difere-1. Statusleilao nao temflag oficial
neste layout. Nenhum negocio/candle artificial foi criado nas pausas.

FONTES/RESSALVAS/PRESERVACAO
41gruposquantidade divergemM1/M5,umfechamento20maiM1141510 vsWork141500
apos18h:referenciaWork141500 mantida nocontexto21mai,sem recalibrar lucro.
02jan/10jul/11jul foraWork,comajustes originais conferidos;resultados
complementares separados,Work em branco. Julho2025 principal inclui esses
complementos;comparavel separado. Controle10jul2026dispensado nao reaberto.
Todosresultadosdez2025-jul2026 eCedroago-out2026 intactos;curvas anteriores
preservadas. Semcompra,nova parametrizacao oumodelosABC nesta etapa.

DD EM ORDEM CRONOLOGICA,SEM REINICIO MENSAL
Nao existe DDglobal desdejan2025 enquantoabril estiverpendente.
Bloco fechadojan-mar2025 e separado do bloco continuomaio2025-julho2026.
Nosso principal completo inclui complementos;curvas comparaveisWork apenas
nasdatas onde existeWork,para compararDD sobre mesmasdatas. Nao inserir
zeros nosmeses/diaspendentes,nem confundir essesblocos comserieCedro.
'''
for key,st in blockstats.items():notes+=f"{key}: {st['start']} a{st['end']},saldo{st['test_points']},DD{st['test_DD']},WorkcomparavelDD{st['Work_DD_on_comparable_dates']}.\n"
notes+='''
PROXIMO PASSO
Receber apenas09abr14:20–14:21,validar minuto completo,
fecharabril eentao atualizarcurva2025inteira+meses2026 emordem.
Continuar retroativamente ate limiteProfit;secontratos ausentes,verificar
negociosWINFUTcommilissegundos/precos/ajustes,semcompra. Depoisalvos/stops,
posteriormenteABC,nosmesmosmeses,variantesseparadas. M1+janelaspodemnaocobrir
novosparametros;preservar brutos,auditorias,referencias ePDFs.
'''
(P/'LEIA_RESULTADO.txt').write_text(notes)
appendix=P/'Nota_Tecnica_Validacao.pdf';c=canvas.Canvas(str(appendix),pagesize=A4);y=H-30;c.setFont('Helvetica',8.5)
for paragraph in notes.splitlines():
 for line in textwrap.wrap(paragraph,width=110) or ['']:
  if y<30:c.showPage();c.setFont('Helvetica',8.5);y=H-30
  c.drawString(24,y,line);y-=13
c.save()
tech=P/'Modelo_D_Janeiro2025_Julho2026_Tecnico.pdf'
with fitz.open() as doc:
 with fitz.open(pdf) as d:doc.insert_pdf(d)
 with fitz.open(appendix) as d:doc.insert_pdf(d)
 doc.save(tech)
# Review workbook,not raw tapes. Keep results and complementary dates explicit.
wb=openpyxl.Workbook();wb.remove(wb.active)
def sheet(name,rows):
 sh=wb.create_sheet(name)
 if rows:
  fields=list(rows[0]);sh.append(fields)
  for r in rows:
   values=[]
   for k in fields:
    v=r.get(k)
    if isinstance(v,(dict,list)):v=json.dumps(v,ensure_ascii=False)
    elif k in ('principal','comparavel_Work_teste','Work_referencia','diferenca_comparavel','complemento_fora_Work','test_points','work_points','difference','points') and v not in ('',None,'PENDENTE'):
     d=D(str(v).replace(',','.'));v=int(d) if d==d.to_integral_value() else float(d)
    values.append(v)
   sh.append(values)
 else:sh.append(['Sem dados'])
 sh.freeze_panes='A2';sh.auto_filter.ref=sh.dimensions
 for cell in sh[1]:cell.fill=PatternFill('solid',fgColor='17405D');cell.font=Font(color='FFFFFF',bold=True)
 for col in sh.columns:sh.column_dimensions[col[0].column_letter].width=min(55,max(14,len(str(col[0].value))+3))
 return sh
sheet('Resumo_Mensal',monthly);sheet('Complemento_Pendente',pending_rows);sheet('Comparacao_Grade',grades)
for s in ss:
 folder=next(d for d in P.iterdir() if d.is_dir() and d.name.startswith(s['month'][-2:]+'_'))
 sheet(s['month']+'_Diario',read(folder/'DIARIO_APOS_REPLAY.csv'));sheet(s['month']+'_Operacoes',read(folder/'OPERACOES_APOS_REPLAY.csv'))
wb.save(P/'Resultados_2025_Apos_Release.xlsx')
# Small publication package excludes raw XLSX/TXT and scratch cache.
with zipfile.ZipFile(P/'Resultados_Lote_2025_Apos_Release.zip','w',zipfile.ZIP_DEFLATED) as z:
 for f in sorted(P.rglob('*')):
  if f.is_file() and f.suffix in ('.csv','.json','.txt','.py','.pdf','.xlsx'):z.write(f,f.relative_to(P))
print(json.dumps(dict(monthly=monthly,blocks=blockstats),ensure_ascii=False,indent=2))
