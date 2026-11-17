from pathlib import Path
import csv,json,datetime as dt,zipfile,io,hashlib,collections
from decimal import Decimal as D
import openpyxl
from openpyxl.styles import Font,PatternFill
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
P=Path(__file__).parent;R=P.parents[1]
def read(p):
 with p.open(encoding='utf-8-sig') as f:return list(csv.DictReader(f,delimiter=';'))
def write(p,rs):
 with p.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rs[0]),delimiter=';',lineterminator='\n');w.writeheader();w.writerows(rs)
ss=json.loads((P/'RESUMO_TODOS_MESES.json').read_text());ws=read(P/'COLETAS_TODOS_MESES.csv');cs=read(P/'CONTROLES_COBERTURA_TODOS_MESES.csv')
allw=[dict(data=w['data'],contrato=w['contrato'],inicio=w['inicio'],fim_exclusivo=w['fim_exclusivo'],niveis=w['niveis'],tipo=w['tipo']) for w in ws+cs]
merged=[]
for w in sorted(allw,key=lambda w:(w['data'],w['inicio'])):
 if merged and w['data']==merged[-1]['data'] and w['contrato']==merged[-1]['contrato'] and w['inicio']<=merged[-1]['fim_exclusivo']:
  g=merged[-1];g['fim_exclusivo']=max(g['fim_exclusivo'],w['fim_exclusivo'])
  g['niveis']=','.join(dict.fromkeys((g['niveis']+','+w['niveis']).split(',')));g['tipo']='|'.join(dict.fromkeys((g['tipo']+'|'+w['tipo']).split('|')))
 else:merged.append(dict(w))
for w in merged:
 day=dt.date.fromisoformat(w['data']);a=dt.datetime.fromisoformat(w['data']+'T'+w['inicio']);b=dt.datetime.fromisoformat(w['data']+'T'+w['fim_exclusivo'])
 w.update(capturar_desde=(a-dt.timedelta(seconds=3)).strftime('%H:%M:%S'),capturar_ate=(b+dt.timedelta(seconds=3)).strftime('%H:%M:%S'),contrato_status='ESPERADO_PELA_ROLAGEM;CONFIRMAR_PRECOS_NO_REPLAY',disponibilidade_Profit='NAO_VERIFICADA',minutos=int((b-a).total_seconds()/60))
 assert w['contrato']==('WING24' if day<dt.date(2024,2,14) else 'WINJ24' if day<dt.date(2024,4,17) else 'WINM24' if day<dt.date(2024,6,12) else 'WINQ24' if day<dt.date(2024,8,14) else 'WINV24' if day<dt.date(2024,10,16) else 'WINZ24' if day<dt.date(2024,12,18) else 'WING25')
write(P/'REPLAY_LISTA_FINAL.csv',merged)
# Independent crosschecks on every prepared source/operation.
ops=[];groups=[]
for s in ss:
 folder=next(p for p in P.iterdir() if p.is_dir() and p.name.startswith(s['mes'][-2:]+'_'))
 oo=read(folder/'OPERACOES_POSSIBILIDADES.csv');ops+=oo
 assert len(oo)==s['operacoes'];assert not s['work_missing'];assert not s['mathematical_differences']
 assert len({(o['date'],o['level']) for o in oo})==len(oo)
 gg=read(folder/'CONFERENCIA_M1_M5.csv');groups+=gg
 assert all(g['OHLC_igual']=='True' for g in gg if g['hora']<'18:00'),s['mes']
 for o in oo:
  assert o['level'] in ['S38.2','S50','S61.8','R38.2','R61.8']
  assert all(D(o[k])%5==0 for k in ['entry','tp','sl'])
 for r in read(folder/'COMPARATIVO_WORK_M5_M1.csv'):
  m1={ (x.split(':')[0],D(x.split(':')[1])) for x in r['M1_grade'].split('|')}
  m5={ (x.split(':')[0],D(x.split(':')[1])) for x in r['M5_grade'].split('|')}
  assert m1<=m5,r
# Full calendar: M1 early dates absent from Work and their adjustment availability.
raw=R/'entregas/arquivo_conversa_20261111/originais/ORIGINAIS_PARTE_005.zip'
with zipfile.ZipFile(raw) as z:blob=z.read(next(n for n in z.namelist() if n.endswith('/EXPORT110_1794243035_5791.zip')))
with zipfile.ZipFile(io.BytesIO(blob)) as z:
 status=readstatus=list(csv.DictReader(io.StringIO(z.read(next(n for n in z.namelist() if n.endswith('/STATUS.csv'))).decode('utf-8-sig')),delimiter=';'))
 for m in range(1,13):
  st=next(r for r in status if r['file']==f'M1_2024{m:02d}.csv');assert st['state']=='EXPORTADO_ESTAVEL' and st['error']=='0' and st['attempts']=='2'
 early=list(csv.DictReader(io.StringIO(z.read(next(n for n in z.namelist() if n.endswith('/M1_202401.csv'))).decode('utf-8-sig')),delimiter=';'))
 counts=collections.Counter(r['time'][:10].replace('.','-') for r in early)
missing=[dict(data=f'2024-01-{i:02d}',contrato='WING24',M1_barras=counts[f'2024-01-{i:02d}'],arquivo_ausente='AJUSTE_OPERACIONAL_DA_DATA',M5_Work='AUSENTE' if i<5 else 'PARCIAL',acao='Recuperar ajuste da fonte original;M1 disponível;nao atribuir zero nem pedir fita integral sem niveis') for i in range(2,6)]
write(P/'DATAS_SEM_AJUSTE.csv',missing)
# Clear labels for operations, all 12 months.
for s in ss:
 folder=next(p for p in P.iterdir() if p.is_dir() and p.name.startswith(s['mes'][-2:]+'_'))
 grade={(w['data'],w['nivel']) for w in read(folder/'JANELAS_POR_OPERACAO.csv') if w.get('tipo')=='CONTROLE_GRADE5'}
 flat=[]
 for o in read(folder/'OPERACOES_POSSIBILIDADES.csv'):
  pending=[]
  if o['determined']=='False':pending.append('SEQUENCIA')
  if (o['date'],o['level']) in grade:pending.append('GRADE5')
  if o['coverage_pending']=='True':pending.append('COBERTURA')
  flat.append(dict(data=o['date'],nivel=o['level'],contrato=o['contract'],estado='PENDENTE_'+'_'.join(pending) if pending else 'DETERMINADA_M1',resultados_possiveis=o['outcomes'],entrada=o['entry'],alvo=o['tp'],stop=o['sl']))
 write(folder/'CONCRETO_E_PENDENTE.csv',flat)
# Workbook with summary, consolidated requests, references and empty raw-return tabs.
wb=openpyxl.Workbook();wb.remove(wb.active)
def table(wb,name,rows):
 sh=wb.create_sheet(name)
 if rows:
  keys=list(rows[0]);sh.append(keys)
  for r in rows:sh.append([r.get(k,'') for k in keys])
 else:sh.append(['Sem pedidos de Replay neste mês'])
 sh.freeze_panes='A2';sh.auto_filter.ref=sh.dimensions
 for cell in sh[1]:cell.fill=PatternFill('solid',fgColor='17354D');cell.font=Font(color='FFFFFF',bold=True)
 for col in sh.columns:sh.column_dimensions[col[0].column_letter].width=min(58,max(15,max(len(str(c.value or '')) for c in col)+2))
 return sh
summ=[]
for s in ss:
 ww=[w for w in merged if w['data'].startswith(s['mes'])]
 summ.append(dict(mes=s['mes'],pregoes_preparados=s['pregoes'],operacoes=s['operacoes'],concretas_M1=s['concretas_sem_ressalva_de_sequencia_cobertura_grade'],operacoes_ambiguas=s['pendentes_sequencia'],controles_grade=s['controles_grade'],datas_Replay=len({w['data'] for w in ww}),intervalos=len(ww),minutos=sum(w['minutos'] for w in ww)))
write(P/'RESUMO_MENSAL.csv',summ)
table(wb,'Resumo',summ);table(wb,'Replay_Final',merged);table(wb,'Sem_Ajuste',missing)
headers=['Data','Compradora','Valor','Quantidade','Vendedora','Agressor','Total (BRL)','Agente Agressor']
for s in ss:
 ww=[w for w in merged if w['data'].startswith(s['mes'])];table(wb,s['mes'],ww)
 for w in ww:
  sh=wb.create_sheet(w['data'][8:]+'-'+w['data'][5:7]+'_'+w['inicio'][:5].replace(':',''));sh.append(headers);sh.freeze_panes='A2'
wb.save(P/'Replay_2024_Preparacao_e_Abas_Retorno.xlsx')
# PDF and plain text list make every month directly readable.
lines=['CONFERÊNCIA 2024 — MODELO D ORIGINAL','32 datas candidatas ao Replay; disponibilidade no Profit ainda não verificada.','Intervalos abaixo: início inclusivo, fim exclusivo, horário de São Paulo.','Copiar alguns segundos antes/depois, minuto completo, sem filtros ou deduplicação.','Preservar milissegundos e ordem; se não houver negócios, informar a ausência.','Contratos esperados pela rolagem; validar correspondência de preços antes de concluir.','']
for s in ss:
 ww=[w for w in merged if w['data'].startswith(s['mes'])]
 lines.append(s['nome']+'/2024')
 if not ww:lines.append('Sem janela de Replay necessária para o Modelo D original nos dados preparados.')
 for w in ww:lines.append(f"{dt.date.fromisoformat(w['data']).strftime('%d/%m')} | {w['inicio'][:5]}–{w['fim_exclusivo'][:5]} | {w['contrato']} | {w['niveis']} | {w['tipo']}")
 lines.append('')
lines += ['Fora da preparação: 02,03,04,05/01 sem ajuste operacional nas fontes disponíveis.','08/01 complementar: ajuste 133414; contexto 05/01 M1 completo, pois M5 é parcial.','Divergência de preços:04/09 18:20, mínima M1 137780 versus M5 137920.','Após corte18h; preservar referência HLC Work do pregão seguinte, sem recalibrar.','Nenhum resultado mensal ou DD de2024 é apresentado como fechado nesta etapa.']
(P/'LISTA_REPLAY_POR_MES.txt').write_text('\n'.join(lines)+'\n')
c=canvas.Canvas(str(P/'Conferencia_2024_Replay_por_Mes.pdf'),pagesize=A4)
for s in ss:
 c.setTitle('Conferência 2024 — datas e janelas de Replay');c.setFont('Helvetica-Bold',19);c.drawString(35,795,s['nome']+' / 2024');c.setFont('Helvetica',10)
 y=766
 text=[f"{s['pregoes']} pregões preparados | {s['operacoes']} operações conhecidas",f"{s['concretas_sem_ressalva_de_sequencia_cobertura_grade']} determinadas sem pendência de sequência/cobertura/grade.",f"Sequência: {s['pendentes_sequencia']} operações | Controles de grade: {s['controles_grade']}",'','Janelas candidatas de Replay (fim exclusivo):','']
 ww=[w for w in merged if w['data'].startswith(s['mes'])]
 text += [f"{w['data'][8:]}/{w['data'][5:7]}  {w['inicio'][:5]}–{w['fim_exclusivo'][:5]}  {w['contrato']}  {w['niveis']}" for w in ww] or ['Nenhuma janela necessária nos dados preparados deste mês.']
 text += ['','Conferir disponibilidade do contrato no Profit. Contrato esperado pela rolagem.','Copiar alguns segundos antes/depois; preservar minuto inteiro, ms e ordem.','Não filtrar nem deduplicar. Não inventar negócios em lacunas/leilões.','M1 + Replay pontual não equivale a auditoria integral tick a tick.','Parâmetros originais, grade 5, um contrato/nível, toque inclusivo, corte 18h.','Fontes, ajustes, referências e operações detalhadas nos CSVs e manifesto.','Não há resultado mensal fechado ou DD nesta etapa.']
 if s['mes']=='2024-01':text += ['','02–05/01: M1 existe, mas ajuste operacional está ausente.','08/01 suplementar: contexto 05/01 completo em M1; M5 anterior parcial.']
 if s['mes']=='2024-09':text += ['','04/09 18:20: mínima divergente entre M1/M5, após corte18h.','Preservado HLC Work no contexto seguinte; ressalva registrada.']
 for t in text:c.drawString(35,y,t);y-=21
 c.setFont('Helvetica',8);c.drawString(35,30,'17/11/2026 | Modelo D | Conferência preliminar para coleta de Replay');c.showPage()
c.save()
manifest=dict(date='2026-11-17',months=12,prepared_days=sum(s['pregoes'] for s in ss),operations=len(ops),concrete=sum(s['concretas_sem_ressalva_de_sequencia_cobertura_grade'] for s in ss),ambiguous_operations=sum(s['pendentes_sequencia'] for s in ss),grade_controls=sum(s['controles_grade'] for s in ss),coverage_intervals=2,Replay_dates=len({w['data'] for w in merged}),merged_intervals=len(merged),unique_requested_minutes=sum(w['minutos'] for w in merged),contracts_available_in_Profit='NOT_VERIFIED',closed_results=False,missing_adjustment_dates=[r['data'] for r in missing],original_source_hashes=[dict(path=str(raw.relative_to(R)),sha256=hashlib.sha256(raw.read_bytes()).hexdigest()),dict(path='nested EXPORT110_1794243035_5791.zip',sha256=hashlib.sha256(blob).hexdigest())],checks=['All prepared M1 outcomes subset of M5 outcomes','All pre18h OHLC groups exact','All existing Work operations present','Mathematical entry/target/stop match Work','Only D original five levels','All 12 M1 exports stable twice with zero error'],price_difference='2024-09-04 18:20: M1 low137780 / WorkM5 low137920; after cut; previous Work HLC preserved',quantity_difference_groups=sum(s['grupos_quantidade_divergente'] for s in ss))
(P/'MANIFESTO.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(manifest,ensure_ascii=False,indent=2))
