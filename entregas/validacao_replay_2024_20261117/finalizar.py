from pathlib import Path
from decimal import Decimal as D
from collections import defaultdict,Counter
import csv,json,hashlib,zipfile
import openpyxl,fitz
from openpyxl.styles import Font,PatternFill
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
P=Path(__file__).parent;R=P.parents[1];PRE=R/'entregas/preparacao_2024_20261117'
def read(p):
 with p.open(encoding='utf-8-sig') as f:return list(csv.DictReader(f,delimiter=';'))
def write(p,rs):
 with p.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rs[0]),delimiter=';',lineterminator='\n');w.writeheader();w.writerows(rs)
def fmt(v):return '—' if v is None or v=='' else f'{D(v):,.2f}'.replace(',','X').replace('.',',').replace('X','.')
ss=json.loads((P/'RESULTADOS_TODOS_MESES.json').read_text());assert len(ss)==12 and all(s['pending']==0 for s in ss)
assert len(json.loads((P/'CONFERENCIA_COBERTURA_OPERACOES.json').read_text()))==3
assert sum(s['operations'] for s in ss)==530
allops=[];days=[];monthly=[];b=peak=dd=D(0);maxdate='SALDO_ZERO';worst={};curve=[];levelrows=[];lstate={l:[D(0),D(0),D(0)] for l in ['R38.2','R61.8','S38.2','S50','S61.8']}
for s in ss:
 out=next(p for p in P.iterdir() if p.is_dir() and p.name.startswith(s['month'][-2:]+'_'))
 ops=read(out/'OPERACOES_APOS_REPLAY.csv');daily=read(out/'DIARIO_APOS_REPLAY.csv');assert all(o['reason']!='PENDENTE' for o in ops)
 assert sum(D(o['points']) for o in ops)==D(s['principal'])
 assert len({(o['date'],o['level']) for o in ops})==len(ops)
 for d in daily:assert sum(D(o['points']) for o in ops if o['date']==d['date'])==D(d['test_points'])
 # Carry explicit coverage audit provenance for the three previously pending cases.
 for o in ops:
  if (o['date'],o['level']) in [('2024-02-06','R61.8'),('2024-06-07','S50'),('2024-06-07','S61.8')]:o['basis']='M1_PLUS_AUDITED_AUCTION_WINDOW_USER_REPORT'
 write(out/'OPERACOES_FINAIS.csv',ops)
 s.update(status='ENCERRADO_M1_REPLAY_PONTUAL',closed=True,main='MODELO_D_ORIGINAL_GRADE5',coverage_audits='CONFERENCIA_COBERTURA_OPERACOES.json')
 (out/'RESULTADO_FINAL.json').write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
 mb=mp=md=D(0)
 for d in daily:
  v=D(d['test_points']);mb+=v;mp=max(mp,mb);md=max(md,mp-mb);b+=v
  if b>peak:peak=b;maxdate=d['date']
  if peak-b>dd:dd=peak-b;worst=dict(peak_date=maxdate,valley_date=d['date'],peak=str(peak),valley=str(b))
  curve.append(dict(date=d['date'],points=str(v),balance=str(b),peak=str(peak),DD_current=str(peak-b),DD_max=str(dd),method='M1_PLUS_TARGETED_REPLAY'))
 cmp=[d for d in daily if d['work_points']!=''];extra=[d for d in daily if d['work_points']=='']
 monthly.append(dict(month=s['month'],days=len(daily),operations=len(ops),points=str(mb),DD_month=str(md),DD_continuous_2024=str(dd),Work_comparable=str(sum(D(d['work_points']) for d in cmp)),test_comparable=str(sum(D(d['test_points']) for d in cmp)),outside_Work_points=str(sum(D(d['test_points']) for d in extra)),outside_Work_dates=','.join(d['date'] for d in extra)))
 for l in lstate:
  lb=lp=ld=D(0);cb,cp,cd=lstate[l]
  for d in daily:
   v=sum((D(o['points']) for o in ops if o['date']==d['date'] and o['level']==l),D(0));lb+=v;lp=max(lp,lb);ld=max(ld,lp-lb);cb+=v;cp=max(cp,cb);cd=max(cd,cp-cb)
  lstate[l]=[cb,cp,cd];levelrows.append(dict(month=s['month'],level=l,operations=sum(o['level']==l for o in ops),points=str(lb),DD_month=str(ld),DD_continuous_2024=str(cd)))
 allops+=ops;days+=daily
assert len(days)==251 and b==D(-2955)
write(P/'RESUMO_MENSAL.csv',monthly);write(P/'OPERACOES_FINAIS_2024.csv',allops);write(P/'DIARIO_FINAL_2024.csv',days);write(P/'CURVA_DIARIA_2024.csv',curve);write(P/'RESULTADO_POR_NIVEL.csv',levelrows)
# New derived continuous series; never modify old curves or their scopes.
extended=[dict(date=d['date'],points=d['test_points'],method='M1_PLUS_TARGETED_REPLAY') for d in days];frozen=[]
for src,dc,pc,method in [(R/'entregas/validacao_lote_2025_20261116/CURVA_M1_REPLAY_2025_01_2026_07.csv','date','test_points','M1_PLUS_TARGETED_REPLAY'),(R/'entregas/compilado_cedro_modelod/CURVA_MODELO_D_MESES_COMPLETOS.csv','data','pontos','CEDRO_FULL_MONTH')]:
 frozen.append(dict(path=str(src.relative_to(R)),sha256=hashlib.sha256(src.read_bytes()).hexdigest()))
 extended += [dict(date=d[dc],points=d[pc],method=method) for d in read(src)]
extended.sort(key=lambda d:d['date']);assert len(extended)==709 and len({r['date'] for r in extended})==709
cb=cp=cd=D(0)
for r in extended:
 cb+=D(r['points']);cp=max(cp,cb);cd=max(cd,cp-cb);r.update(balance=str(cb),DD_current=str(cp-cb),DD_max=str(cd))
write(P/'CURVA_EXTENSAO_2024_01_2026_10.csv',extended)
# Exact reconciliation to every frozen monthly total previously reported.
for h in frozen:assert hashlib.sha256((R/h['path']).read_bytes()).hexdigest()==h['sha256']
summary=dict(status='DOZE_MESES_2024_ENCERRADOS',months=monthly,days=251,operations=530,points=str(b),DD_2024=str(dd),DD_2024_peak_valley=worst,extended_curve=dict(start=extended[0]['date'],end=extended[-1]['date'],days=len(extended),points=str(cb),DD=str(cd),method='M1_REPLAY_JAN2024_JUL2026;CEDRO_AUG_OCT2026',monthly_reset=False),original_closed_sources_preserved=frozen,pending=[],raw_source='GitHub Release XLSX;original chat ZIP not transferred',full_tick_audit=False,fill_certification=False,costs=False)
(P/'RESULTADO_CONSOLIDADO.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
wb=openpyxl.Workbook();wb.remove(wb.active)
def table(name,rs):
 sh=wb.create_sheet(name);keys=list(rs[0]);sh.append(keys)
 for r in rs:sh.append([float(D(str(r[k]).replace(',','.'))) if k in ['points','DD_month','DD_continuous_2024','test_points','work_points','difference'] and r[k]!='' else r[k] for k in keys])
 sh.freeze_panes='A2';sh.auto_filter.ref=sh.dimensions
 for c in sh[1]:c.font=Font(color='FFFFFF',bold=True);c.fill=PatternFill('solid',fgColor='15354E')
 for col in sh.columns:sh.column_dimensions[col[0].column_letter].width=min(52,max(14,max(len(str(c.value or '')) for c in list(col)[:100])+2))
table('Resumo',monthly);table('Por_Nivel',levelrows)
for s in ss:table(s['month']+'_Diario',[d for d in days if d['date'].startswith(s['month'])]);table(s['month']+'_Ops',[o for o in allops if o['date'].startswith(s['month'])])
wb.save(P/'Modelo_D_Resultados_2024.xlsx')
names=['Janeiro','Fevereiro','Março','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro','Novembro','Dezembro']
for tech in [False,True]:
 filename='Modelo_D_2024_Tecnico.pdf' if tech else 'Modelo_D_2024_Diario.pdf';c=canvas.Canvas(str(P/filename),pagesize=A4)
 c.setTitle('Modelo D — 2024 — '+('Técnico' if tech else 'Comparação diária'))
 if tech:
  c.setFont('Helvetica-Bold',18);c.drawString(35,795,'Modelo D original | 2024');c.setFont('Helvetica',10);y=760
  notes=[f"12 meses | 251 pregões | 530 operações | Resultado: {fmt(b)} pontos",f"DD diário contínuo de 2024: {fmt(dd)} pontos, sem reinício mensal.",'Fonte: M1 MT5 WIN$N + Replay pontual Profit; não é fita integral tick a tick.','Grade de 5 pontos, um contrato por nível, toque inclusivo, corte18h.','Sem custos, slippage, fila ou garantia de execução.','Arquivo recebido pela Release: Janeiro.a.Dezembro.2024.xlsx; 33 abas.','1.313.080 negócios preservados, sem deduplicação; nenhuma cópia no limite200001.','Ajustes02–05jan fornecidos pelo usuário; não confrontados com boletim independente.','Work M5 preservado como referência; dias fora do Work continuam sem valor Work.','06fev: leilão após10:16 relatado pelo usuário; primeiro negócio copiado10:18:37.198.','Minuto10:18 completo confere M1;R61.8 permanece SL-450.','07jun: pausa09:30:15.140–09:32:39.957 observada na cópia.','Minutos09:30/09:32 completos;relato de leilão preservado,sem flag oficial.','18jan S50 e29ago S50: entrada no prefixo anterior à cópia,provada pelo M1.','Resultado TP é invariável; horários reais podem ser anteriores aos observados.','Empatesms conferidos em duas ordens;barreiras opostas no mesmo ms rejeitadas.','04set18:20: mínima M1/M5 divergente após corte; contexto Work preservado.','A curva estendida2024–out2026 é derivada e marca transição para Cedro em ago2026.','Curvas antigas e seus DDs mantêm os escopos originais;nenhum dado fechado alterado.']
  for line in notes:c.drawString(35,y,line);y-=23
  c.showPage()
 for ix,s in enumerate(ss):
  m=s['month'];ms=monthly[ix];c.setFont('Helvetica-Bold',18);c.drawString(35,798,names[ix]+' / 2024');c.setFont('Helvetica',9)
  c.drawString(35,777,f"{ms['days']} pregões | {ms['operations']} operações | Modelo D original, grade5")
  c.drawString(35,761,f"DD no mês: {fmt(ms['DD_month'])} | DD contínuo desdejan2024: {fmt(ms['DD_continuous_2024'])}")
  y=733;c.setFont('Helvetica-Bold',9)
  for x,t in [(35,'Data'),(255,'Work'),(400,'Nosso teste'),(555,'Diferença')]: (c.drawString if x==35 else c.drawRightString)(x,y,t)
  c.setFont('Helvetica',9)
  for d in [x for x in days if x['date'].startswith(m)]:
   y-=19;c.drawString(35,y,d['date'][8:]+'/'+d['date'][5:7])
   for x,k in [(255,'work_points'),(400,'test_points'),(555,'difference')]:c.drawRightString(x,y,fmt(d[k]))
  y-=25;c.setFont('Helvetica-Bold',10);c.drawString(35,y,'TOTAL PRINCIPAL');c.drawRightString(400,y,fmt(ms['points']))
  c.setFont('Helvetica',8);y-=21;c.drawString(35,y,'Work em branco: data fora da referência original; não representa resultado zero.')
  y-=15;c.drawString(35,y,f"Nosso comparável: {fmt(ms['test_comparable'])} | Work comparável: {fmt(ms['Work_comparable'])}")
  if tech:
   y-=30;c.setFont('Helvetica-Bold',9);c.drawString(35,y,'Por nível | operações | pontos | DD mensal | DD contínuo2024');c.setFont('Helvetica',9)
   for l in [r for r in levelrows if r['month']==m]:y-=18;c.drawString(35,y,f"{l['level']}   |   {l['operations']}   |   {fmt(l['points'])}   |   {fmt(l['DD_month'])}   |   {fmt(l['DD_continuous_2024'])}")
  c.setFont('Helvetica',8);c.drawString(35,30,'17/11/2026 | M1+Replay pontual | DD por fechamentos diários; sem reinício mensal.');c.showPage()
 c.save();doc=fitz.open(P/filename);assert len(doc)==(13 if tech else 12)
(P/'.gitattributes').write_text('*.pdf binary\n*.xlsx binary\n*.zip binary\n');(P/'.gitignore').write_text('__pycache__/\n')
(P/'LEIA_PRIMEIRO.md').write_text('''# Fechamento de 2024 — Modelo D original

Doze meses encerrados com M1 e Replay pontual; não é auditoria integral tick a tick. Resultado, operações, DD diário contínuo e ressalvas em RESULTADO_CONSOLIDADO.json. Planilha Modelo_D_Resultados_2024.xlsx e dois PDFs: técnico e comparação diária Work/teste.

O arquivo efetivamente analisado foi Janeiro.a.Dezembro.2024.xlsx, disponibilizado pelo usuário na Release; o ZIP anexado no chat não pôde ser transferido. Bruto da Release preservado localmente, link/hash em FONTE_RELEASE.json. Nenhuma deduplicação ou negociação sintética. Dados originais e resultados2025/2026 não foram alterados.

06/02: leilão após10:16 relatado pelo usuário; primeiro negócio copiado10:18:37.198 e minuto10:18 completo coincide com M1. 07/06: pausa observada09:30:15.140–09:32:39.957, compatível com relato de leilão;09:30/09:32 conferidos. Relatos não são confirmação de flags oficiais de leilão.

18/01 S50 e29/08 S50: preço de entrada aparece no M1, mas não na parte copiada desse minuto; portanto a entrada ocorreu no prefixo anterior. Stop fora de todo o candle de entrada e resultado TP invariável nas duas ordensms da cópia. Entrada/saída reais podem ser anteriores; não certificar horário único.

Ajustes02–05jan fornecidos pelo usuário. Work independente em M5 ausente nesses dias; contexto28/12/2023 para02jan em M1 completo. Parâmetros e seleção original Work preservados; datas adicionais separadas. 04/09 18:20: mínima divergente após corte, contextoWork preservado. Custos/fila/slippage não incluídos; resultados condicionais aos preços do modelo,sem garantia de fills.

Curva estendida2024–out2026 é novo arquivo derivado; não substitui curvas anteriores. Marca troca M1+Replay para Cedro em agosto2026. Não houve testes de variantes de stop/alvo nesta entrega.
''')
with zipfile.ZipFile(P/'Modelo_D_2024_Resultados_e_Auditorias.zip','w',zipfile.ZIP_DEFLATED) as z:
 for f in sorted(P.rglob('*')):
  if f.is_file() and f.suffix in ['.json','.csv','.pdf','.xlsx','.py','.md']:z.write(f,f.relative_to(P))
print(json.dumps(summary,ensure_ascii=False,indent=2))
