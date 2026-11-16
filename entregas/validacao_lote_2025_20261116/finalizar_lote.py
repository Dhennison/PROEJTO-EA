"""Finalize eleven closed2025months and one continuous Jan2025-Jul2026curve.
Preserve all previously closed monthly files and daily points;no monthly reset.
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
assert all(s['pending']==0 for s in ss)
expected={'2025-04':865,'2025-01':-2405,'2025-02':-1180,'2025-03':-970,'2025-05':-2915,'2025-06':895,'2025-07':2740,'2025-08':-460,'2025-09':-385,'2025-10':-1055,'2025-11':-300}
monthly=[];days={};stats={};allops=[];proofs=[];grades=[]
for s in ss:
 folder=next(d for d in P.iterdir() if d.is_dir() and d.name.startswith(s['month'][-2:]+'_'))
 src=next(d for d in PRE.iterdir() if d.is_dir() and d.name.startswith(s['month'][-2:]+'_'))
 frozen=(folder/'RESULTADO_FINAL.json').exists()
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
 if frozen:
  previous_month=json.loads((folder/'RESULTADO_FINAL.json').read_text());assert D(previous_month['principal'])==principal
 else:
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
 if not frozen:(folder/'LEIA_RESULTADO.txt').write_text(notes)
# Append previously CLOSED sources without touching them.
oldmonths=[('2025-12','profit_dezembro_2025_20261115'),('2026-01','profit_janeiro_20261115'),('2026-02','profit_fevereiro_20261114'),('2026-03','profit_marco_20261113'),('2026-04','profit_abril_20261113'),('2026-05','profit_maio_20261113'),('2026-06','profit_junho_20261113'),('2026-07','profit_winq26_julho_20261113')]
old_expected=[3135,-1620,-3545,350,5720,-780,3405,1100]
old_sources=[]
for (m,folder),expected_total in zip(oldmonths,old_expected):
 path=R/'entregas'/folder/'DIARIO_APOS_JANELAS.csv';rs=read(path);assert sum(D(r['test_points']) for r in rs)==expected_total
 old_sources.append(dict(path=str(path.relative_to(R)),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),points=expected_total))
 days[m]=rs
# All19months are now complete,so there is one continuous chronological series.
blocks={'2025_01_2026_07':sorted(days)}
curves={};blockstats={}
for key,months in blocks.items():
 rows=[];balance=peak=maxdd=D(0);wb=wp=wd=ct=cp=cd=D(0);aligned=[];peak_date='INICIO_SALDO_ZERO';worst_peak_date=worst_valley_date=None;worst_peak=worst_valley=D(0)
 for m in months:
  assert all(r['test_points']!='PENDENTE' for r in days[m])
  for r in days[m]:
   pts=D(r['test_points']);balance+=pts
   if balance>peak:peak=balance;peak_date=r['date']
   if peak-balance>maxdd:maxdd=peak-balance;worst_peak_date=peak_date;worst_valley_date=r['date'];worst_peak=peak;worst_valley=balance
   rows.append(dict(date=r['date'],test_points=n(pts),test_balance=n(balance),test_peak=n(peak),test_current_DD=n(peak-balance),test_max_DD=n(maxdd),series='M1_PLUS_TARGETED_REPLAY',block=key))
   if r['work_points']!='':
    w=val(r['work_points']);wb+=w;wp=max(wp,wb);wd=max(wd,wp-wb);ct+=pts;cp=max(cp,ct);cd=max(cd,cp-ct)
    aligned.append(dict(date=r['date'],test_points=n(pts),test_balance=n(ct),test_max_DD=n(cd),work_points=n(w),work_balance=n(wb),work_max_DD=n(wd),scope='WORK_COMPARABLE_DATES_ONLY',block=key))
  stats[m]=dict(block=key,test_DD_accum=n(maxdd),test_balance=n(balance),Work_comparable_DD=n(wd),test_comparable_DD=n(cd))
 assert [r['date'] for r in rows]==sorted(set(r['date'] for r in rows))
 curves[key]=rows;write(P/f'CURVA_M1_REPLAY_{key}.csv',rows);write(P/f'CURVA_COMPARAVEL_WORK_{key}.csv',aligned)
 blockstats[key]=dict(start=rows[0]['date'],end=rows[-1]['date'],days=len(rows),test_points=n(balance),test_DD=n(maxdd),worst_peak_date=worst_peak_date,worst_peak_balance=n(worst_peak),worst_valley_date=worst_valley_date,worst_valley_balance=n(worst_valley),Work_DD_on_comparable_dates=n(wd),test_DD_on_comparable_dates=n(cd),monthly_reset=False)
# Exact equality of old daily results against the new current extension.
previous=read(R/'entregas/profit_dezembro_2025_20261115/CURVA_DEZEMBRO2025_JANEIRO_FEVEREIRO_MARCO_ABRIL_MAIO_JUNHO_JULHO_M1_REPLAY.csv')
assert [(r['date'],D(r['test_points'])) for r in curves['2025_01_2026_07'] if r['date']>='2025-12-01']==[(r['date'],D(r['test_points'])) for r in previous]
write(P/'RESUMO_MENSAL.csv',monthly);write(P/'DIFERENCAS_GRADE_MATEMATICO.csv',grades)
# Precise missing fragments only. Existing copies remain intact.
pending_rows=[]
with (P/'COMPLEMENTO_PENDENTE.csv').open('w',encoding='utf-8-sig',newline='') as f:csv.writer(f,delimiter=';').writerow(['date','contract','level','capture_start','capture_end_exclusive','reason','do_not_repeat'])
summary=dict(status='ONZE_MESES_2025_ENCERRADOS',newly_closed_months=[s['month'] for s in ss if not s['pending']],pending_months=[],monthly=monthly,continuous_blocks=blockstats,global_DD_since_January2025=blockstats['2025_01_2026_07']['test_DD'],newly_closed_now=['2025-04'],January_complement=json.loads((P/'COMPLEMENTO_02JAN.json').read_text()),April_complement=json.loads((P/'COMPLEMENTO_09ABR.json').read_text()),DD_global_unavailable_reason=None,current_continuous_curve='CURVA_M1_REPLAY_2025_01_2026_07.csv',old_daily_results_preserved=old_sources,source_records=1940063,source_sheets=39,source_asset='https://github.com/Dhennison/PROEJTO-EA/releases/download/dados-replay-2025-20261116/Janeiro.a.Novembro.2025.xlsx',source_sha256='e0992ed7c4b603a1a24307f30b94713952af9bebae9f5c417fd81c010817fd13',source_local='/workspace/dados_brutos_modelo_d/replay_profit/Janeiro_a_Novembro_2025_Release.xlsx',source_published_by_user=True,raw_copied_into_Git_history=False,main='D_ORIGINAL_GRADE5',method='M1_PLUS_TARGETED_REPLAY_NO_CERTIFIED_FILLS',costs=False,full_tape=False,pending=pending_rows,partial_prefix_proof=proofs[0]['partial_prefix_invariance_proof'])
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
 for line in ['Curva diaria continua desde02/01/2025,sem reinicio mensal.','Serie Cedro agosto-outubro2026 permanece separada.','Sem custos/fila/slippage ou garantia de preenchimento; nao e fita integral.']:
  c.drawString(32,y,line);y-=15
 c.showPage()
c.save()
with fitz.open(pdf) as d:
 assert len(d)==19
 for page,m in zip(d,months):
  text=page.get_text()
  for r in days[m]:assert r['date'][8:]+'/'+r['date'][5:7]+'/'+r['date'][:4] in text
  assert 'PENDENTE DE COMPLEMENTO' not in text
  if m=='2025-04':assert '865,00' in text
notes='''LOTE JANEIRO A NOVEMBRO/2025 — ENCERRADO EM16/11/2026
Planilha daRelease:39abas,1940063registros,56091431bytes,SHA256 conferido.
Complementos TXT02jan e09abr preservados separadamente,sem deduplicação.
Onze meses encerrados,478operações determinadas,nenhuma pendênciaReplay.
42casos conferidos porReplay/grade:40ambiguidades originais e2controlesgrade.
D original/grade5/1contrato/toque inclusivo/corte18h,pontos condicionais nos
níveis,sem custos/fila/slippage ou fills garantidos. M1+Replay pontual,
não mês inteiro auditado por negócios. Meses fechados antes destaetapa intactos.

PRINCIPAIS E RECORTES COMPARÁVEIS
'''
for row in monthly:notes+=f"{row['month']}: principal{row['principal']}, nosso comparável{row['comparavel_Work_teste']}, Work{row['Work_referencia']}, complemento{row['complemento_fora_Work']}.\n"
notes+='''
ÚLTIMO COMPLEMENTO09ABR CONFERIDO
WINJ25R61.8,75799negócios,14:19:58.000–14:21:03.869.
Minuto14:20:67641negócios/177981contratos,OHLC e quantidade iguaisM1.
Entrada grade125430 às14:20:25.497,stop125880 às14:20:38.402,SL-450.
ConfirmaSTOPWork. MatemáticoSL-450,doisdesempatesms com mesmoresultado,
sem barreirasopostas nomesmo ms. Abrilfechado+865,37operações/20pregões.
A cópia incorreta09:20 foi preservada como histórico,não usada em14:20.
TXToriginal e réplicaSHA256idêntica preservados,COMPLEMENTO_09ABR.json.
02jan já complementado:09:01 completo,sequência antiga toda contida no novo
TXT. Jan completo-2405;comparávelWork-1630;complemento02jan-775 separado.
Julho completo2740;comparável2170;complementos10/11jul+570 separados.
Não somar comparáveis aos completos,nem preencher Work ausente comzero.

CASOS DE SEQUÊNCIA E GRADE
07marS50 entrou09:47M1,Replay10:30 pósentrada,como preparado.
13marR61.8:prefixo parcial,TP60 invariável:stop126275 acima de toda a máxima
M1125830. Estados possíveis do prefixo:sem entrada,aberta oujáTP;após a cópia
todos levamTP. Não certificar horários observados11:13:52.410/11:13:54.829
como únicos possíveis;entrada/saída anteriores podem existir no prefixo.
02jan antigo não passava essecontrole,efoi corretamente complementado.
Controles de máxima préentrada/entrada incompleta eordem temporal passaram.
Posição só transportada se entrada precede a cópia;se entrar durante a cópia,
aguardar o toque antes de qualquer saída. Não reprocessar extremo préentrada.
'''
for g in grades:notes+=f"{g['date']} {g['level']}: grade{g['grade_reason']} {g['grade_points']};matemático{g['mathematical_reason']} {g['mathematical_points']}.\n"
notes+='''
LEILÕES,ABERTURAS E RESSALVAS
03jun pausa09:03:09.264–09:56:21.720:relato do usuário,cópia eM1 compatíveis.
Não há novas entradas elegíveis nospreços copiados;quantidade09:03difere-1.
30julTP80 às15:42:37.020,antesleilão15:42:39.719–15:47:23.012.
09out/11nov iniciam09:03,OHLC/quantidade das aberturas conferem;sem criar
negócios anteriores.21ago S38.2SL-375 eS50SL-375 conferidos na planilha.
S61.8TP17010:26:23.070 doTXT longo preservado;três pausas compatíveis com
relato/M1. TXT longo200001registros,limiteobservado;não é fita inteira.
Quantidade09:16difere-1. Layoutnão traz flag oficialde leilão;origem do relato
identificada. Nenhuma trajetória/candle/negócio artificial foi criado.
41grupos de quantidade M1/M5 divergem.20mai fechamentoM1141510 vsWork141500,
após18h mas contexto21mai:mantida referênciaWork original141500,sem recalibrar
resultado. Todasressalvas de fonte são preservadas;sem certificar fita perfeita.

DD POR FECHAMENTOS DIÁRIOS,SEM REINÍCIO MENSAL
Agora todosos19meses janeiro2025-julho2026 estão fechados,permitindo uma única
curva contínua. Os blocos anteriores jan-mar e maio2025-jul2026 ficam como
histórico;não são reiniciados nem concatenados com zero. Apenas abril foi
acrescentado aos resultados antes fechados. Curvas comparáveisWork utilizam
somente as mesmas datas com referênciaWork;complementos continuam separados.
SérieCedro agosto-outubro2026 permanece separada,DD3620 e resultados antigos
intactos. Não apresentar fontes mistas como fita integral de negócios.
'''
for key,st in blockstats.items():notes+=f"{key}: {st['start']} a{st['end']},saldo{st['test_points']},DD{st['test_DD']},pico{st['worst_peak_date']} saldo{st['worst_peak_balance']},vale{st['worst_valley_date']} saldo{st['worst_valley_balance']};DDWorkcomparável{st['Work_DD_on_comparable_dates']}.\n"
notes+='''
PRESERVAÇÃO E PRÓXIMOS PASSOS
Todos os brutos/referências/auditorias e meses fechados anteriores preservados.
Dez2025+3135/Jan2026-1620/Fev-3545/Mar+350/Abr+5720/Mai-780/Jun+3405/Jul+1100;
CedroAgo-2375/Set+2855/Out+3830 e recortesWorkAgo-2275/Set+1380 intactos.
Controle adicional10/07/2026 dispensado permanece encerrado. Nenhuma coleta
adicional parajan-nov2025. Continuar retroativamente pelos contratosProfit
acessíveis;se indisponíveis,verificar negóciosWINFUT commilissegundos e
correspondência de preços/ajustes,semcompra. Só depois daexpansão estudar
alvos/stops pornível;depoisABC nosmesmosmeses,variantesseparadas. Novasbarreiras
podem exigir outrasjanelas;preservar brutos,não apenasreduções doD atual.
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
sheet('Resumo_Mensal',monthly);sheet('Pendencias',[dict(estado='SEM PENDENCIAS DE REPLAY NESTE LOTE')]);sheet('Comparacao_Grade',grades)
for s in ss:
 folder=next(d for d in P.iterdir() if d.is_dir() and d.name.startswith(s['month'][-2:]+'_'))
 sheet(s['month']+'_Diario',read(folder/'DIARIO_APOS_REPLAY.csv'));sheet(s['month']+'_Operacoes',read(folder/'OPERACOES_APOS_REPLAY.csv'))
wb.save(P/'Resultados_2025_Apos_Release.xlsx')
# Small publication package excludes raw XLSX/TXT and scratch cache.
with zipfile.ZipFile(P/'Resultados_Lote_2025_Apos_Release.zip','w',zipfile.ZIP_DEFLATED) as z:
 for f in sorted(P.rglob('*')):
  if f.is_file() and f.suffix in ('.csv','.json','.txt','.py','.pdf','.xlsx'):z.write(f,f.relative_to(P))
print(json.dumps(dict(monthly=monthly,blocks=blockstats),ensure_ascii=False,indent=2))
