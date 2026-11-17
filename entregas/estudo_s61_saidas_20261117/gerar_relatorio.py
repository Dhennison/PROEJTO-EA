from pathlib import Path
import csv,json,pickle,hashlib,textwrap,collections,re
import numpy as np
import openpyxl,fitz
from openpyxl.styles import Font,PatternFill
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
P=Path(__file__).parent;R=P.parents[1];E=R/'entregas';d=pickle.loads(Path('/workspace/work/estudo_s61/resultados.pickle').read_bytes());cfg={c['id']:c for c in d['configs']};S={r['id']:r for r in d['summary']}
def read(p):
 with p.open(encoding='utf-8-sig') as f:return list(csv.DictReader(f,delimiter=';'))
def write(name,rows):
 with (P/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter=';',lineterminator='\n');w.writeheader();w.writerows(rows)
def n(v):return f'{float(v):,.0f}'.replace(',','.')
def ran(a,b):return n(a) if a==b else n(a)+' a '+n(b)
def rule(c):
 stop=f"{n(c['stop_value'])} pontos" if c['stop_mode']=='FIXED_POINTS' else f"{c['stop_value']:g}x o novo alvo"+(' (teto 650)' if c['stop_mode'].endswith('CAP650') else '')
 return 'Stop '+stop+'; alvo '+f"{c['target_multiplier']:g}x a distância original até S50"
# Replay requests for the primary risk-reduction candidate only.
primary='S61_42';req=[]
for w in d['windows']:
 if w['variant']!=primary:continue
 assert w['minute']!='ALL' and w['reason']!='CEDRO_RAW_AND_AUDIT_M1_MISSING'
 h,m=map(int,w['minute'].split(':'));stop=(h*60+m+1);req.append(dict(date=w['date'],contract=w['contract'],start=w['minute']+':00',end_exclusive=f'{stop//60:02d}:{stop%60:02d}:00',variant=primary,level='S61.8',stop_points=100,target='S50_ORIGINAL',instruction='Minuto completo,alguns segundos antes/depois;preservar ms,ordem e negocios identicos'))
# Remove duplicated requested windows, never original trades.
unique={tuple(r[k] for k in ['date','contract','start','end_exclusive']):r for r in req};req=sorted(unique.values(),key=lambda r:(r['date'],r['start']));write('REPLAY_NECESSARIO_STOP100_ALVO_ORIGINAL.csv',req)
# Exact logical implications are audited against actual original reason labels.
labels={r['date']:r['original_reason'] for r in read(P/'ROTULOS_ORIGINAIS_CONFERIDOS.csv')};original={o['date']:o for o in d['ops']};tr={(r['variant'],r['date']):r for r in d['trade']}
for p in d['proofs']:
 t=tr[(p['variant'],p['date'])];o=original[p['date']];reason=labels[p['date']];td=abs(o['tp']-o['entry'])
 if 'ORIGINAL_STOP' in p['proof']:assert reason=='SL' and t['stop_points']<=650 and t['target_points']>=td and t['lower']==t['upper']==-t['stop_points']
 elif 'ORIGINAL_CUT' in p['proof']:assert reason=='CORTE' and t['stop_points']>=650 and t['target_points']>=td and t['lower']==t['upper']==o['original']
 elif 'ORIGINAL_TARGET' in p['proof']:assert reason=='TP' and t['stop_points']>=650 and t['target_points']<=td and t['lower']==t['upper']==t['target_points']
 else:raise AssertionError(p)
assert d['lo'][0].sum()==d['hi'][0].sum()==5065
# All88results reconcile by operation,month andyear.
for ci,c in enumerate(d['configs']):
 oo=[r for r in d['trade'] if r['variant']==c['id']];assert len(oo)==233
 assert sum(r['lower'] for r in oo)==d['lo'][ci].sum() and sum(r['upper'] for r in oo)==d['hi'][ci].sum()
 assert sum(r['lower'] for r in d['annual'] if r['variant']==c['id'])==d['lo'][ci].sum()
 assert sum(r['upper'] for r in d['monthly'] if r['variant']==c['id'])==d['hi'][ci].sum()
# Per-year original totals remain frozen.
assert [S['S61_ORIGINAL'][f'year{y}_lower'] for y in [2024,2025,2026]]==[1510,4790,-1235]
checks=dict(scenarios=88,operations_each=233,total_operation_scenarios=88*233,source_CedroAugust_days=21,baseline_original_points=5065,baseline_original_DD=4765,source_baseline_mismatches=0,logical_proofs_checked=len(d['proofs']),original_labels_independently_checked=233,all_month_year_and_operation_sums_equal=True,primary_Replay_windows=len(req),primary_Replay_dates=len({r['date'] for r in req}),raw_logs_not_requested_again=True)
(P/'CONFERENCIA_FINAL.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n')
# Workbook coversall88,eachyear andmonth,notonlyhighlighted candidates.
wb=openpyxl.Workbook();wb.remove(wb.active)
for name,rows in [('Todos_S61',d['summary']),('2024',[r for r in d['annual'] if r['year']==2024]),('2025',[r for r in d['annual'] if r['year']==2025]),('2026_JanOut',[r for r in d['annual'] if r['year']==2026]),('Mensal',d['monthly']),('Com_R61',d['combined']),('Operacoes',d['trade']),('Replay_Stop100',req),('Fontes_Agosto',read(P/'FONTES_CEDRO_AGOSTO_M1_LOCALIZADAS.csv'))]:
 sh=wb.create_sheet(name);keys=list(rows[0]);sh.append(keys)
 for r in rows:sh.append([r[k] for k in keys])
 sh.freeze_panes='A2';sh.auto_filter.ref=sh.dimensions
 for cell in sh[1]:cell.fill=PatternFill('solid',fgColor='17354E');cell.font=Font(color='FFFFFF',bold=True)
 for col in sh.columns:sh.column_dimensions[col[0].column_letter].width=min(58,max(14,max(len(str(c.value or '')) for c in list(col)[:60])+2))
wb.save(P/'S61_Testes_Stop_Alvo_2024_2025_2026.xlsx')
# Full PDF with every recipe's annual outcomes.
c=canvas.Canvas(str(P/'S61_Testes_Stop_Alvo_2024_2025_2026.pdf'),pagesize=A4);c.setTitle('S61.8 — stops e alvos — 2024,2025 e2026jan-out');page=0;y=0
header_current=''
def new(title,sub='2024 e 2025 completos | 2026: janeiro a outubro | pontos brutos'):
 global page,y,header_current
 if page:c.showPage()
 page+=1;header_current=title;c.setFillColorRGB(.06,.16,.25);c.rect(0,764,595,78,fill=1,stroke=0);c.setFillColorRGB(1,1,1);c.setFont('Helvetica-Bold',16);c.drawString(32,807,title);c.setFont('Helvetica',10);c.drawString(32,784,sub);c.setFillColorRGB(.06,.16,.25);y=735
 c.setFont('Helvetica',8);c.drawString(32,26,f'17/11/2026 | S61,8% | D original preservado | Página {page}')
def para(text,bold=False):
 global y
 text=re.sub(r'(?<=[a-zà-ÿ])(?=\d)|(?<=\d)(?=[a-zà-ÿ])',' ',text)
 text=re.sub(r'(?<=DD)(?=\d)',' ',text)
 text=re.sub(r';(?=\S)','; ',text)
 text=re.sub(r',(?=[A-Za-zÀ-ÿ])',', ',text)
 text=re.sub(r'(?<=[a-zà-ÿ]),(?=\d)',', ',text)
 c.setFont('Helvetica-Bold' if bold else 'Helvetica',10)
 for line in textwrap.wrap(text,99) or ['']:
  if y<70:new(header_current+' (continuação)');c.setFont('Helvetica-Bold' if bold else 'Helvetica',10)
  c.drawString(32,y,line);y-=15
 y-=8
def card(r):
 global y
 if y<140:new(header_current+' (continuação)')
 para(r['id']+' | '+rule(cfg[r['id']]),True)
 para('2024: '+ran(r['year2024_lower'],r['year2024_upper'])+' | 2025: '+ran(r['year2025_lower'],r['year2025_upper'])+' | 2026*: '+ran(r['year2026_lower'],r['year2026_upper']))
 para('Total: '+ran(r['points_lower'],r['points_upper'])+' | DD diário: '+ran(r['DD_lower'],r['DD_upper'])+' | Operações pendentes: '+str(r['unresolved']))
 y-=4
new('S61,8% | Três grupos de saídas')
para('88 parametrizações nas mesmas 233 entradas do S61,8%, ao longo de 709 pregões. Não houve mudança de entrada, referência, elegibilidade, tamanho, reentrada ou corte às 18h. Grade de 5 pontos.',True)
para('1. Stop650 e alvo maior: multiplicadores1,25/1,5/2/3/4 da distância original entre entrada eS50. 2. Alvo original e stops500/375/325/250/200/150/100. 3. Combinação desses sete stops com os cinco alvos maiores. Mais20 receitas de stop proporcional ao novo alvo e20 com teto650, além do original. Receitas podem coincidir em certos dias; não são88 trajetórias independentes.')
para('Referência S61,8% original: 2024+1.510;2025+4.790;2026jan-out-1.235. Total+5.065,DD diário contínuo4.765. Todos os resultados antigos permanecem preservados.')
para('Resultado1: nenhum dos cinco testes de apenas alongar alvo com stop650 superou o total original, mesmo no limite superior. O melhor total superior foi4.240,abaixo de5.065; o menorDD inferior foi5.540,acima de4.765.',True)
para('Resultado2: stop100 com alvo original reduziu a envoltória deDD para785a1.370,com pontos2.075a7.300. Há20operações pendentes. Faixa não significa lucro realizado, média provável ou duas trajetórias garantidas.',True)
para('Resultado3: stop100 e alvo1,5x somam-225a3.290,com2024 sempre negativo. As35combinações de stopmenor/alvomaior têm total superior de no máximo3.290,abaixo do original. Podem reduzir risco,mas não aumentam o bruto total nesta grade.')
para('Correção de acervo:21 arquivos de candles M1 de auditoria Cedro deagosto, um por pregão estavam salvos em retorno_agosto_lote*/M1_CONTRATO_DATA.csv. A afirmação anterior de que não existiam essesM1 estava errada. Agora os usamos; negócios individuais só são necessários nas novas dúvidas de sequência.')
new('Referência e grupo1 | Stop650, alvo maior')
for r in d['summary']:
 if r['family'] in ['ORIGINAL','1_STOP650_ALVO_MAIOR']:card(r)
new('Grupo2 | Stop menor, alvo original')
for r in d['summary']:
 if r['family']=='2_STOP_MENOR_ALVO_ORIGINAL':card(r)
new('Grupo3 | Stop menor e alvo maior')
for r in d['summary']:
 if r['family']=='3_STOP_MENOR_ALVO_MAIOR':card(r)
new('Extra | Stop proporcional ao novo alvo')
para('Stop=razão vezes a NOVA distância do alvo. Sem teto,pode exceder650. Exemplo:razão1,5 com alvo original teve stops de25a1.165,mediana265;18das233entradas tiveram stop acima650. Não classificar essa família inteira como redução de stop.',True)
for r in d['summary']:
 if r['family']=='EXTRA_STOP_PROPORCIONAL_NOVO_ALVO':card(r)
new('Extra | Stop proporcional com teto650')
para('Stop=min(650,razão vezes o NOVO alvo),arredondado à grade5. Aqui o stop nunca supera o original. Exibir junto com a versão semteto evita esconder as diferenças de risco.')
for r in d['summary']:
 if r['family']=='EXTRA_STOP_PROPORCIONAL_TETO650':card(r)
new('S61 em conjunto com R61 | Regras explícitas')
para('Cada receita S61 também foi somada ao R61 original e, separadamente, ao R61alvo750/stop150 fechado comCedro. Demais níveis ficamOFF. Não confundir as duas regras deR61.',True)
for id,comb in [('S61_ORIGINAL','COM_R61_ORIGINAL'),('S61_ORIGINAL','COM_R61_750_150'),('S61_42','COM_R61_ORIGINAL'),('S61_42','COM_R61_750_150'),('S61_05','COM_R61_750_150'),('S61_60','COM_R61_ORIGINAL')]:
 r=next(x for x in d['combined'] if x['variant']==id and x['combination']==comb);para(id+' + '+comb,True)
 para('2024: '+ran(r['year2024_lower'],r['year2024_upper'])+' | 2025: '+ran(r['year2025_lower'],r['year2025_upper'])+' | 2026*: '+ran(r['year2026_lower'],r['year2026_upper']))
 para('Total '+ran(r['lower'],r['upper'])+';DD '+ran(r['DD_lower'],r['DD_upper'])+';'+str(r['unresolved'])+' pendentes.')
new('Pendências prioritárias | Stop100, alvo original')
para(f'{len(req)}janelas em{len({r["date"] for r in req})}datas. São novas dúvidas geradas pelo novo stop, não falta de envio dos logs antigos. Intervalo com fimexclusivo; capturar minuto inteiro e alguns segundos antes/depois. Horário da fonte preservado. Não filtrar nem deduplicar.')
for r in req:para(r['date']+' | '+r['contract']+' | '+r['start'][:5]+'–'+r['end_exclusive'][:5])
new('Método, custos e limites')
para('Todos os anos foram calculados:2024/2025completos e2026janeiro-outubro. Não há novembro/dezembro2026 na base fechada. A comparação é exploratória; o histórico inteiro já era conhecido,não validação futura independente.')
para('M1 mantém todas as sequências compatíveis quando alvo e stop podem mudar de ordem. Replay só entra quando minuto completo confereOHLC equantidade. A máxima anterior à entrada não é tratada como alvo posterior. A posição continua depois da saída original quando a variante ainda está aberta.')
para('Foram aplicadas provas lógicas a partir do desfecho original:STOPoriginal comstop maiscurto ealvo não maispróximo obrigaSTOPnovo;CORTEoriginal comambasbarreiras relaxadas mantémCORTE;ALVOoriginal comalvo não maisdistante estop não maiscurto mantémALVO. Os rótulosSL/TP/CORTE vieram dos fechamentos, não foram inferidos apenas do número depontos.')
para('DD diário contínuo por nível e pelas somas dosníveis,nunca soma dosDDs individuais,sem reinício mensal. OsDDs de séries delimits dão limites conservadores. Limites deníveis diferentes podem exigir ordens incompatíveis na mesma vela; não são trajetórias certificadas.')
para('Sem custos/slippage,fila ou garantia deexecução no resultado principal. Stop100 S61isolado:comcusto hipotético5pontos/operação,o limiteinferior cai de2.075 para910;com10pontos,cai para-255. Na dupla comR61original,há488operações e o custo pesa mais.')
para('Planilha contém88receitas x3anos,34meses,limites poroperação,DD,pendências e264combinações isolada/comR61. Não houve exclusão de ano desfavorável nem substituição doDoriginal. Novos parâmetros não foram aprovados para operar.')
c.save();doc=fitz.open(P/'S61_Testes_Stop_Alvo_2024_2025_2026.pdf')
(P/'.gitattributes').write_text('*.pdf binary\n*.xlsx binary\n');(P/'.gitignore').write_text('__pycache__/\n')
(P/'LEIA_PRIMEIRO.md').write_text('''# S61.8 — três grupos de stop/alvo, nos três anos

88parametrizações,mesmas233entradas,2024/2025completos e2026janeiro-outubro. Cinco alvos maiores comstop650;sete stops menores comalvooriginal;35combinações stopmenor/alvomaior;20stops proporcionais e20comteto650;original como referência. Alvo1x significa oS50original;alvoNx significa entrada+Nvezes a distância até esseS50. Stop proporcional usa distância do NOVO alvo.

PDF comtodos88resultadosanuais eplanilha com264linhasanuais,34mesesporreceita,operações,DD,pendências ecombinações comR61original ouR61alvo750/stop150. As regras deR61 estão explícitas; não confundir saídas originais enovas.

Correção material:21M1deauditoriaCedroagosto estavam salvos em outro diretório/padrão de nome. Foram localizados em cedro_extrator.../retorno_agosto_lote*/M1_CONTRATO_DATA.csv e usados. A afirmação anterior de indisponibilidade deM1Cedroagosto estava errada. Brutos de negócios individuais e candles deauditoria são distintos; novasambiguidades podem continuar requerendoReplay. Não pedir reenvio dos16ZIPs já recuperados.

Os cinco testes de apenasalongar alvo comstop650 têm total superior abaixo5065dooriginal. Os35testes de stopmenor/alvomaior também têm total superior abaixo5065. Stop100 comalvooriginal é uma opção de menorDD,mas20operações ainda são ambíguas:2.075a7.300pontos,DD785a1370. ComR61original:2.900a8.125pontos,DD1675a2825,anos com limitesinferiores positivos,antes decustos. Isso não é lucro certificado.

Resultados limitados por candles são intervalos; não usar extremo favorável como realizado. Provasmonotônicas foram verificadas contra os rótulos originais. OriginalS61permanece5065/DD4765;Doriginalcompleto3950/DD14805. Nenhumresultado fechado foi alterado.
''')
manifest=dict(period='2024-01a2026-10',scenarios=88,operations_per_scenario=233,baseline_points=5065,baseline_DD=4765,sources_august=[r for r in read(P/'FONTES_CEDRO_AGOSTO_M1_LOCALIZADAS.csv')],checks=checks,earlier_August_M1_absence_claim_corrected=True,all_three_years_included=True,original_closed_files_unchanged=True,no_variant_promoted=True)
(P/'MANIFESTO.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(pdf_pages=len(doc),scenarios=88,primary_replay_windows=len(req),primary_replay_dates=len({r['date'] for r in req}),logical_proofs=len(d['proofs'])),ensure_ascii=False))
