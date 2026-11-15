"""Freeze February and extend closed M1+targeted Replay curve; no edits to prior months."""
from pathlib import Path
from decimal import Decimal as D
from collections import Counter
import json,csv,zipfile,hashlib,textwrap
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import fitz
P=Path(__file__).parent;ROOT=P.parents[1]
def read(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter=';'))
def write(p,rows):
 with p.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter=';',lineterminator='\n');w.writeheader();w.writerows(rows)
s=json.loads((P/'REPLAY_TODAS_ABAS_RESULTADO.json').read_text());checks=read(P/'REPLAY_TODAS_ABAS_M1.csv');ops=read(P/'OPERACOES_POSSIBILIDADES.csv');daily=read(P/'DIARIO_APOS_JANELAS.csv')
assert s['pending_operation_count']==0 and s['resolved_original_pending']==3 and s['grade_controls']==0
assert s['test_points']=='-3545' and s['work_points']=='-664.311665'
assert all(r['resolved'] and r['entry_minute_coverage_ok'] and r['tie_invariant'] and not r['mixed_exit_barrier_ms'] for r in s['results'])
assert sum(r['full_minute_from_bounds']=='True' for r in checks)==3
assert all(r['ohlc_match']=='True' and r['quantity_match']=='True' for r in checks if r['full_minute_from_bounds']=='True')
old=json.loads((P/'recebimento01_parcial/REPLAY_TODAS_ABAS_RESULTADO.json').read_text())
for prior in old['results']:
 if prior['resolved']:
  new=next(r for r in s['results'] if (r['date'],r['level'])==(prior['date'],prior['level']))
  assert new['primary']==prior['primary'] and new['tie_control']==prior['tie_control']
lookup={(r['date'],r['level']):r['primary'] for r in s['results']};final=[]
for o in ops:
 pr=lookup.get((o['date'],o['level']))
 if pr:reason,points=pr['reason'],pr['points'];basis=pr['exit_source'];en=pr['entry']['time'];ex=pr['exit']['time']
 else:
  assert o['determined']=='True';reason,points=o['outcomes'].split(':');basis='M1_DETERMINED';en=o['entry_minute']+':00_CANDLE';ex=o['exit_candidates']
 final.append(dict(date=o['date'],contract=o['contract'],level=o['level'],reason=reason,points=points,basis=basis,entry=en,exit=ex,work_reason=o['work_reason'],work_points=o['work_points']))
assert len(final)==39 and sum(D(r['points']) for r in final)==D(-3545)
write(P/'OPERACOES_FINAIS.csv',final)
flips=Counter((r['work_reason'],r['reason']) for r in final if r['work_reason']!=('ALVO' if r['reason']=='TP' else 'STOP' if r['reason']=='SL' else 'ZERAGEM 18H'))
assert flips=={('ALVO','SL'):4},flips
months={'2026-02':daily}
for name,month in [('marco','03'),('abril','04'),('maio','05'),('junho','06'),('winq26_julho','07')]:months['2026-'+month]=read(P.parent/f'profit_{name}_20261113/DIARIO_APOS_JANELAS.csv')
expected=[D(-3545),D(350),D(5720),D(-780),D(3405),D(1100)];tb=tp=td=wb=wp=wd=D(0);curve=[];stats={}
for (month,rs),expected_total in zip(months.items(),expected):
 assert sum(D(r['test_points']) for r in rs)==expected_total
 assert [r['date'] for r in rs]==sorted(set(r['date'] for r in rs))
 for r in rs:
  tb+=D(r['test_points']);tp=max(tp,tb);td=max(td,tp-tb)
  if r['work_points']!='':wb+=D(r['work_points']);wp=max(wp,wb);wd=max(wd,wp-wb)
  curve.append(dict(date=r['date'],test_points=r['test_points'],test_balance=str(tb),test_current_DD=str(tp-tb),test_max_DD=str(td),work_points=r['work_points'],work_balance=str(wb) if r['work_points']!='' else '',work_max_DD=str(wd) if r['work_points']!='' else ''))
 stats[month]=dict(test_points=str(expected_total),work_points=str(sum(D(r['work_points']) for r in rs if r['work_points']!='')),test_DD_accum=str(td),work_DD_accum=str(wd))
assert tb==D(6250)
# Confirm per-day equality of ALL frozen historical months; only history/DD is extended.
previous_curve=read(P.parent/'profit_marco_20261113/CURVA_MARCO_ABRIL_MAIO_JUNHO_JULHO_M1_REPLAY.csv')
assert [(r['date'],r['test_points'],r['work_points']) for r in curve if r['date']>='2026-03-01']==[(r['date'],r['test_points'],r['work_points']) for r in previous_curve]
curve_name='CURVA_FEVEREIRO_MARCO_ABRIL_MAIO_JUNHO_JULHO_M1_REPLAY.csv';write(P/curve_name,curve)
s.update(final_operation_reasons=dict(Counter(r['reason'] for r in final)),Work_flips=[dict(Work=a,test=b,count=n) for (a,b),n in flips.items()],chronological_stats=stats,February_July_test=str(tb),February_July_Work=str(wb),no_new_replay_requested=True,series='M1_PLUS_TARGETED_REPLAY_SEPARATE_FROM_CEDRO',complete_matching_minutes=3,partial_boundary_minutes=6,previous_month_daily_points_unchanged=True,receipt01_preserved='recebimento01_parcial',receipt02_overlap_audit='AUDITORIA_RECEBIMENTO02_SOBREPOSICAO.json')
(P/'RESULTADO_FINAL.json').write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
(P/'PROGRESSO_RESOLUCAO.json').write_text(json.dumps({k:v for k,v in s.items() if k not in ('results','sheets')},ensure_ascii=False,indent=2)+'\n')
text='''FEVEREIRO/2026 — MODELO D ENCERRADO
Principal: -3545 pontos. Work: -664,311665. Diferença: -2880,688335.
39 operações, 18 pregões. Parâmetros originais, grade5, um contrato por nível,
toque inclusivo, corte18h. Pontos nos níveis, sem custos/fila/slippage.
M1 + Replay pontual; não é mês inteiro de negócios nem certificação de fills.
36 resultados determinados emM1 +3ambiguidades resolvidas porReplay.

ACERVO E GRANULARIDADE
M5ProfitWork:1986barras;M1MT5WIN$N:9930barras. OHLC/quantidade exatos nos
1986grupos completos;contexto30/01:113M5 contra565M1 também exato.
18ajustes Work presentes e39conjuntos matemáticos iguais,tolerância0,00001.
Oito operações ambíguas emM5;cinco determinadas peloM1:13fevS38.2SL,
19fevR38.2SL,20fevS38.2SL,25fevR38.2TP,27fevS50SL. As três primeiras
mudam ALVO Work paraSL por granularidade,também nos níveis matemáticos.
Dados e evidências por operação preservados,sem inventar trajetória de candles.

REPLAY CONCLUÍDO
Recebimento02:trêsabas,175183negócios. Trêsminutos completos conferem em
OHLC/quantidade;seisbordas parciais esperadas. Sem limite200001 poraba.
11/02 WING26 R61.8:SL-450,entrada09:02:31.309,saída minuto09:04 peloM1.
24/02 WINJ26 R38.2:SL-375,entrada09:06:11.210,saída minuto09:11 peloM1.
27/02 WINJ26 S38.2:SL-375,entrada09:01:38.671,saída minuto09:03 peloM1.
CANDLE indica minuto,não instante exato do negócio. Controles matemáticosSL
nos3casos. Dois desempatesms mantêm motivos/pontos;sem barreiras opostas
no mesmo ms. Regressões de máxima pré-entrada e barra incompleta passaram.
11fev/27fev confirmamSTOPWork;24fev mudaALVOWork paraSL. Total4ALVOWork->SL,
três resolvidos porM1 e um porReplay. Nenhum controle extra de grade necessário.

COMPLEMENTO DE27/02 CONFERIDO
Novaaba cobre09:00:53.413–09:02:16.152. Minuto09:01 temquantidade133520,
O193930/H194055/L193200/C193265,iguais à referênciaM1.
A cópia antiga de66698negócios é um bloco contíguo exatamente igual na nova,
com multiplicidade/ordem/linhas idênticas preservadas. Não houve deduplicação
nem necessidade de emenda sintética. Usado fluxo novo completo de27/02.
Abas11fev/24fev inteiramente idênticas;resultados/timestamps anteriores
preservados. Auditoria emAUDITORIA_RECEBIMENTO02_SOBREPOSICAO.json.
Recebimento01 parcial e seus derivados guardados emrecebimento01_parcial.
DoisXLSX brutos preservados comSHA256;manifestos separados,brutos não publicados.
A antiga COLETA_COMPLEMENTAR_PENDENTE.csv é histórica e está atendida.
Nenhuma coleta adicional necessária para fechar fevereiro.

DRAWDOWN POR FECHAMENTO DIÁRIO, SEM REINÍCIO MENSAL
SérieM1+Replay emordemfevereiro->março->abril->maio->junho->julho.
'''
for m,st in stats.items():text+=f"Até {m}: DD teste {st['test_DD_accum']}; Work {st['work_DD_accum']}.\n"
text+='''Total fevereiro-julho:teste6250;curva ampliada sem alterar nenhum dia/mês fechado.
Março+350/Abril+5720/Maio-780/Junho+3405/Julho+1100 intactos.
CedroAgo-2375/Set+2855/Out+3830 eDD3620 intactos,separados eidentificados.
ComparáveisWorkAgo-2275/Set+1380 preservados àparte dos mesescompletos.
DoisPDFs correntes técnico/enxuto cobremfevereiro-julho comdiárioWork versus
nosso teste. CompiladosCedro anteriores preservados. Controle10/07dispensado,
não reabrir. Próxima expansão cronológica:janeiro,seguindo plano aprovado.
Quando contratos anteriores indisponíveis,tentar negóciosWINFUT comms e
correspondência de preços/ajustes;sem compra. Só depois daexpansão estudar
alvos/stops pornível;depoisA/B/C. Novasvariantes podem exigir outrasjanelas.
'''
(P/'LEIA_RESULTADO_FINAL.txt').write_text(text)
def fmt(x):return '-' if x=='' else f'{D(x):,.2f}'.replace(',','X').replace('.',',').replace('X','.')
name='Modelo_D_Fevereiro_Marco_Abril_Maio_Junho_Julho_M1_Replay';pdf=P/(name+'_Diario.pdf');c=canvas.Canvas(str(pdf),pagesize=A4);W,H=A4
for month,rs in months.items():
 st=stats[month];label={'02':'FEVEREIRO','03':'MARCO','04':'ABRIL','05':'MAIO','06':'JUNHO','07':'JULHO'}[month[-2:]]
 c.setFont('Helvetica-Bold',16);c.drawString(35,H-40,f'MODELO D - {label} / 2026');c.setFont('Helvetica',9);c.drawString(35,H-62,'M1 + Replay pontual | Grade 5 | Pontos brutos nos niveis | Mes encerrado')
 y=H-100
 for x,t in [(35,'Data'),(205,'Work'),(320,'Nosso'),(445,'Diferenca')]:c.drawString(x,y,t)
 for r in rs:
  y-=19;c.drawString(35,y,r['date'][8:]+'/'+r['date'][5:7]+'/2026')
  for x,k in [(270,'work_points'),(390,'test_points'),(555,'difference')]:c.drawRightString(x,y,fmt(r[k]))
 y-=30;c.setFont('Helvetica-Bold',11);c.drawString(35,y,'TOTAL');c.drawRightString(270,y,fmt(st['work_points']));c.drawRightString(390,y,fmt(st['test_points']));c.drawRightString(555,y,fmt(D(st['test_points'])-D(st['work_points'])))
 y-=28;c.setFont('Helvetica',9);c.drawString(35,y,f'DD acumulado desde fevereiro: Work {fmt(st["work_DD_accum"])} | Nosso {fmt(st["test_DD_accum"])}')
 for line in ['DD diario cronologico sem reinicio mensal; separado da serie Cedro.','Sem custos, fila ou garantia de preenchimento. Traco: Work indisponivel.','Julho: controle adicional de 10/07 dispensado pelo usuario.']:
  y-=18;c.drawString(35,y,line)
 c.showPage()
c.save()
with fitz.open(pdf) as d:
 assert len(d)==6 and '-3.545,00' in d[0].get_text()
 for page,rs in zip(d,months.values()):
  for r in rs:assert r['date'][8:]+'/'+r['date'][5:7]+'/2026' in page.get_text()
appendix=P/'Fevereiro_Nota_Tecnica.pdf';c=canvas.Canvas(str(appendix),pagesize=A4);y=H-35;c.setFont('Helvetica',9)
for paragraph in text.splitlines():
 for line in textwrap.wrap(paragraph,width=100) or ['']:
  if y<35:c.showPage();y=H-35;c.setFont('Helvetica',9)
  c.drawString(25,y,line);y-=14
c.save()
tech=P/(name+'_Tecnico.pdf')
with fitz.open() as d:
 with fitz.open(pdf) as base:d.insert_pdf(base)
 with fitz.open(appendix) as note:d.insert_pdf(note)
 d.save(tech)
with fitz.open(tech) as d:assert len(d)>6
with zipfile.ZipFile(P/'Fevereiro_Modelo_D_Resultado.zip','w',zipfile.ZIP_DEFLATED) as z:
 for n in ['RESULTADO_FINAL.json','PROGRESSO_RESOLUCAO.json','LEIA_RESULTADO_FINAL.txt','OPERACOES_FINAIS.csv','DIARIO_APOS_JANELAS.csv','REPLAY_OPERACOES_RESOLVIDAS.csv','REPLAY_TODAS_ABAS_M1.csv','AUDITORIA_RECEBIMENTO02_SOBREPOSICAO.json',curve_name,pdf.name,tech.name]:z.write(P/n,n)
print(json.dumps(dict(reasons=s['final_operation_reasons'],stats=stats),indent=2))
