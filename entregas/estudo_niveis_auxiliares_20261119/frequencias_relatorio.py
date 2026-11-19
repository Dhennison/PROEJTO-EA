from pathlib import Path
import csv,pickle,json,collections,math,hashlib,zipfile
import numpy as np
from openpyxl import Workbook
from openpyxl.styles import Font,PatternFill
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4,landscape
from reportlab.lib import colors
P=Path(__file__).parent;R=P.parents[1];E=R/'entregas';x=pickle.load(open('/workspace/work/novos_niveis_20261119/resultados.pickle','rb'));days=x['data']['days'];di={d:i for i,d in enumerate(days)}
def read(p):return list(csv.DictReader(p.open(encoding='utf-8-sig'),delimiter=';'))
def write(name,rs):
 if not rs:return
 with (P/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rs[0]),delimiter=';');w.writeheader();w.writerows(rs)
def dd(a):
 b=np.cumsum(a);return float(np.max(np.maximum.accumulate(np.r_[0,b])[1:]-b))
reasons={}
for folder in ['validacao_replay_2024_20261117','validacao_lote_2025_20261116']:
 for f in (E/folder).glob('*/OPERACOES_FINAIS.csv'):
  for r in read(f):reasons[(r['date'],r['level'])]=r['reason']
for folder in ['profit_dezembro_2025_20261115','profit_janeiro_20261115','profit_fevereiro_20261114','profit_marco_20261113','profit_abril_20261113','profit_maio_20261113','profit_junho_20261113']:
 for r in read(E/folder/'OPERACOES_FINAIS.csv'):reasons[(r['date'],r['level'])]=r['reason']
for r in read(E/'profit_winq26_julho_20261113/OPERACOES_POSSIBILIDADES.csv'):
 if r['determined']=='True':reasons[(r['date'],r['level'])]=r['outcomes'].split(':')[0]
for r in read(E/'profit_winq26_julho_20261113/REPLAY_OPERACOES_RESOLVIDAS.csv'):reasons[(r['date'],r['level'])]=r['reason']
for month,sub in [('agosto','resultado'),('setembro','resultado'),('outubro','resultado_mensal')]:
 for r in read(E/f'cedro_modelod_{month}_2026'/sub/'TODOS_NIVEIS.csv'):
  if r['estado']=='ENCERRADA':reasons[(r['data'],r['nivel'])]={'STOP':'SL','ALVO':'TP','CORTE_LAST':'CUT'}[r['motivo']]
oldtr=[]
for o in x['data']['ops']:
 reason=reasons[(o['date'],o['level'])]
 if reason.startswith('CORTE'):reason='CUT'
 assert reason in ['TP','SL','CUT'],(o,reason)
 if reason=='SL':assert o['original']==-abs(o['sl']-o['entry'])
 if reason=='TP':assert o['original']==abs(o['tp']-o['entry'])
 oldtr.append(dict(level=o['level'],variant='ORIGINAL',date=o['date'],contract=o['contract'],entry=o['entry'],target_points=abs(o['tp']-o['entry']),stop_points=abs(o['sl']-o['entry']),lower=o['original'],upper=o['original'],outcomes=f'{reason}:{o["original"]}',pending=False,**{f'{r}_{b}':reason==r for r in ['TP','SL','CUT'] for b in ['guaranteed','possible']}))
assert len(oldtr)==1485
write('ROTULOS_ORIGINAIS_CONFERIDOS.csv',oldtr)
def longest(flags):
 m=k=0
 for flag in flags:k=k+1 if flag else 0;m=max(m,k)
 return m
def freq(rr,level,variant,period):
 rr=sorted(rr,key=lambda r:r['date']);n=len(rr);r=dict(level=level,variant=variant,period=period,operations=n,pending=sum(v['pending'] for v in rr),lower=sum(v['lower'] for v in rr),upper=sum(v['upper'] for v in rr))
 for reason in ['TP','SL','CUT']:
  lower=sum(v[reason+'_guaranteed'] for v in rr);upper=sum(v[reason+'_possible'] for v in rr)
  r[reason+'_guaranteed']=lower;r[reason+'_possible']=upper;r[reason+'_pct_lower']=100*lower/n if n else 0;r[reason+'_pct_upper']=100*upper/n if n else 0
  r['entries_per_'+reason+'_min']=n/upper if upper else '';r['entries_per_'+reason+'_max']=n/lower if lower else ''
 r['max_consecutive_SL_guaranteed']=longest(v['SL_guaranteed'] for v in rr);r['max_consecutive_SL_possible']=longest(v['SL_possible'] for v in rr)
 r['max_consecutive_TP_guaranteed']=longest(v['TP_guaranteed'] for v in rr);r['max_consecutive_TP_possible']=longest(v['TP_possible'] for v in rr)
 return r
allfreq=[];bygroup=collections.defaultdict(list)
for r in oldtr+x['trades']:bygroup[(r['level'],r['variant'])].append(r)
for (level,variant),rr in bygroup.items():
 for period in ['ALL','2024','2025','2026']:
  part=rr if period=='ALL' else [r for r in rr if r['date'].startswith(period)]
  allfreq.append(freq(part,level,variant,period))
write('FREQUENCIAS_TODAS_CONFIGURACOES.csv',allfreq)
origfreq=[r for r in allfreq if r['variant']=='ORIGINAL'];write('FREQUENCIAS_ORIGINAIS.csv',origfreq)
selectedkeys={(s['level'],s['id']) for s in x['selections']}
# Also show best ex-post ratio/points per level, always labeled exploratory.
posthoc=[]
for level in x['newnames']:
 rr=[s for s in x['summaries'] if s['level']==level]
 for objective,key in [('TOTAL',lambda r:r['lower']),('RATIO',lambda r:r['points_per_DD'])]:
  s=max(rr,key=key);posthoc.append(dict(objective=objective,**s));selectedkeys.add((level,s['id']))
write('MELHORES_EXPLORATORIOS_POR_NIVEL.csv',posthoc)
selectedfreq=[r for r in allfreq if (r['level'],r['variant']) in selectedkeys];write('FREQUENCIAS_NOVOS_SELECIONADOS.csv',selectedfreq)
# Subsets selected in training, without consulting 2026 outcomes for the primary ranking.
trainrank=sorted(x['combinations'],key=lambda r:(r['training_score'],r['training_lower']),reverse=True)
seen=set();unique=[]
for r in trainrank:
 if r['levels'] in seen:continue
 seen.add(r['levels']);unique.append(dict(rank=len(unique)+1,**r))
write('RANKING_SELECAO_TREINO.csv',unique)
postrank=sorted(x['combinations'],key=lambda r:r['points_per_DD'],reverse=True);bestpoints=max(x['combinations'],key=lambda r:r['lower']);bestratio=postrank[0];primary=unique[0]
# Reconstruct curves only for reported candidates and save a month/year breakdown.
reported=[dict(label='PRINCIPAL_SELECAO_TREINO',**primary),dict(label='EXPLORATORIO_MAIOR_TOTAL',**bestpoints),dict(label='EXPLORATORIO_MELHOR_RATIO',**bestratio)]
monthly=[];daily=[]
for record in reported:
 fam=record['family'];sels=[next(s for s in x['selections'] if s['family']==fam and s['level']==level) for level in x['newnames']];indices=[int(s['id'][1:]) for s in sels];a=np.zeros(709);b=a.copy()
 for i in range(8):
  if not record['mask']>>i&1:continue
  a+=x['oldcurve'][i] if i<5 else x['lo'][i-5,indices[i-5]];b+=x['oldcurve'][i] if i<5 else x['hi'][i-5,indices[i-5]]
 assert a.sum()==record['lower'] and b.sum()==record['upper'] and dd(a)==record['DD_upper_path']
 for m in sorted({d[:7] for d in days}):
  mask=np.array([d.startswith(m) for d in days]);monthly.append(dict(label=record['label'],id=record['id'],month=m,lower=float(a[mask].sum()),upper=float(b[mask].sum()),DD_month_lower=dd(b[mask]),DD_month_upper=dd(a[mask])))
 for i,d in enumerate(days):daily.append(dict(label=record['label'],id=record['id'],date=d,lower=a[i],upper=b[i]))
write('CANDIDATOS_DESTAQUE.csv',reported);write('MENSAL_CANDIDATOS.csv',monthly);write('DIARIO_CANDIDATOS.csv',daily)
# Per-level month breakdown and Replay shortlist; no automatic request to collect everything.
monthlylevels=[]
for level,variant in sorted(selectedkeys):
 for m in sorted({d[:7] for d in days}):
  rr=[r for r in bygroup[(level,variant)] if r['date'].startswith(m)];monthlylevels.append(freq(rr,level,variant,m))
write('MENSAL_NOVOS_SELECIONADOS.csv',monthlylevels)
shortlist=collections.defaultdict(lambda:dict(levels=set(),variants=set(),reasons=set()))
for r in x['windows']:
 if (r['level'],r['variant']) not in selectedkeys:continue
 key=(r['date'],r['contract'],r['minute']);s=shortlist[key];s['levels'].add(r['level']);s['variants'].add(r['level']+':'+r['variant']);s['reasons'].add(r['reason'])
windows=[]
for (d,c,m),r in sorted(shortlist.items()):
 hh,mm=map(int,m.split(':'));end=hh*60+mm+1
 windows.append(dict(date=d,contract=c,start=m,end_exclusive=f'{end//60:02d}:{end%60:02d}',levels='|'.join(sorted(r['levels'])),variants='|'.join(sorted(r['variants'])),reason='|'.join(sorted(r['reasons'])),status='TRIAGEM_NAO_SOLICITADA_AUTOMATICAMENTE'))
write('REPLAY_CANDIDATOS_SELECIONADOS.csv',windows)
# Workbook avoids giant multi-scenario operation sheet; all operation rows are preserved in the archive.
w=Workbook();w.remove(w.active)
for name,rs in [('Destaques',reported),('Selecao_Treino',x['selections']),('Melhores_por_Nivel',posthoc),('Frequencia_Original',origfreq),('Frequencia_Novos',selectedfreq),('Mensal_Candidatos',monthly),('Mensal_Novos',monthlylevels),('Parametros',x['configs']),('Todos_504_Testes',x['summaries']),('Combinacoes_765',x['combinations']),('Replay_Triagem',windows)]:
 s=w.create_sheet(name);keys=list(rs[0]);s.append(keys)
 for r in rs:s.append([r.get(k) for k in keys])
 s.freeze_panes='A2';s.auto_filter.ref=s.dimensions
 for cell in s[1]:cell.font=Font(bold=True,color='FFFFFF');cell.fill=PatternFill('solid',fgColor='17354E')
 for col in s.columns:s.column_dimensions[col[0].column_letter].width=min(50,max(12,max(len(str(c.value or '')) for c in list(col)[:60])+2))
w.save(P/'Novos_Niveis_e_Frequencias_2024_2026.xlsx')
def n(v):return f'{float(v):,.0f}'.replace(',','.')
def rng(a,b):return n(a) if a==b else n(a)+' a '+n(b)
def fnum(v):return f'{v:.2f}'.replace('.',',') if isinstance(v,(int,float)) else '-'
styles=getSampleStyleSheet();story=[]
def para(t):story.append(Paragraph(t,styles['BodyText']));story.append(Spacer(1,7))
def title(t):story.append(Paragraph(t,styles['Heading1']));story.append(Spacer(1,10))
def table(headers,rows,widths=None):
 cells=[[Paragraph(str(c),styles['BodyText']) for c in row] for row in [headers]+rows];t=Table(cells,colWidths=widths,repeatRows=1);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#DDE7EF')),('GRID',(0,0),(-1,-1),.3,colors.grey),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),6)]));story.append(t);story.append(Spacer(1,12))
title('Modelo D: novos niveis e frequencias')
para('Janeiro de 2024 a outubro de 2026. Estudo exploratorio, pontos brutos, um contrato por nivel. Modelo D original preservado: +3.950 pontos e DD diario continuo de 14.805 pontos. Nenhuma variante promovida.')
para('Novas entradas: vendas no R23,6% e R50%; compras no S23,6%. Mesma elegibilidade de abertura, bloqueio geometrico, grade de 5 pontos, uma oportunidade por nivel/dia, sem reentrada ou bloqueio apos alvo. Corte no primeiro negocio/candle a partir de 18h. Niveis independentes podem operar simultaneamente.')
para('168 receitas por nivel: 504 testes. Alvos fixos 50, 100, 150, 200, 250, 375, 500 e 750 pontos; alvos 0,5x, 1x, 1,5x e 2x a distancia de referencia. Stops fixos 25, 50, 75, 100, 150, 200, 250, 375, 500 e 650; stops 0,5x, 1x, 1,5x e 2x o alvo. Referencia: R23,6 ate Ajuste; R50 ate R38,2; S23,6 ate Ajuste. Referencia e hipotese nova, nao regra original.')
para('2024-2025 usados para selecionar parametros; 2026 apresentado como comparacao cronologica. Como esse periodo ja era conhecido, nao equivale a teste futuro independente. Combinacoes: 255 subconjuntos dos oito niveis em tres familias de selecao = 765 avaliacoes, com duplicatas explicitas.')
para('Valores com faixa permanecem condicionais a sequencia. O limite inferior e conservador; o superior nao e lucro confirmado. DD diario continuo, com zero inicial e sem reiniciar por mes, mostrado como faixa entre os envelopes. Custos e slippage podem mudar substancialmente a conclusao. Nao se trata de auditoria integral tick a tick.')
story.append(PageBreak());title('Candidatos e comparacao anual')
for r in reported:
 para('<b>'+r['label']+'</b>: '+r['levels'])
 table(['2024','2025','2026 jan-out','Total','DD continuo','Pendencias'],[[rng(r['year2024_lower'],r['year2024_upper']),rng(r['year2025_lower'],r['year2025_upper']),rng(r['year2026_lower'],r['year2026_upper']),rng(r['lower'],r['upper']),rng(r['DD_lower_path'],r['DD_upper_path']),r['pending']]])
para('O principal acima foi escolhido pela maior relacao pontos/DD em 2024-2025. Os outros destaques foram escolhidos depois de ver todo o periodo: sao exploratorios e sujeitos a sobreajuste. Nao sao as melhores combinacoes possiveis fora da grade testada.')
story.append(PageBreak());title('Novos niveis: selecao por pontos/DD no treino')
rr=[r for r in x['selections'] if r['family']=='TRAIN_SCORE']
for r in rr:
 para('<b>'+r['level']+' / '+r['id']+'</b>: alvo '+str(r['target_value'])+' ('+r['target_mode']+'); stop '+str(r['stop_value'])+' ('+r['stop_mode']+').')
 table(['2024','2025','2026 jan-out','Total','DD','Entradas','Pendentes'],[[rng(r['year2024_lower'],r['year2024_upper']),rng(r['year2025_lower'],r['year2025_upper']),rng(r['year2026_lower'],r['year2026_upper']),rng(r['lower'],r['upper']),rng(r['DD_lower_path'],r['DD_upper_path']),r['operations'],r['pending']]])
story.append(PageBreak());title('Frequencia dos cinco niveis originais')
para('A cada X entradas = numero de entradas dividido pela quantidade de eventos. E frequencia historica, nao promessa de periodicidade nem probabilidade da proxima entrada. Dias sem entrada nao entram no denominador. Saidas por horario sao separadas de alvo e stop cheio.')
rr=[r for r in origfreq if r['period']=='ALL']
table(['Nivel','Entradas','Alvos','Stops','Cortes','1 alvo a cada','1 stop a cada','Maior seq. SL'],[[r['level'],r['operations'],r['TP_guaranteed'],r['SL_guaranteed'],r['CUT_guaranteed'],fnum(r['entries_per_TP_min']),fnum(r['entries_per_SL_min']),r['max_consecutive_SL_guaranteed']] for r in rr])
story.append(PageBreak());title('Frequencia dos novos niveis selecionados')
for s in [r for r in x['selections'] if r['family']=='TRAIN_SCORE']:
 r=next(r for r in selectedfreq if r['level']==s['level'] and r['variant']==s['id'] and r['period']=='ALL')
 para('<b>'+r['level']+' / '+r['variant']+'</b>')
 table(['Entradas','Alvos','Stops','Cortes','1 alvo a cada','1 stop a cada','Seq. SL'],[[r['operations'],rng(r['TP_guaranteed'],r['TP_possible']),rng(r['SL_guaranteed'],r['SL_possible']),rng(r['CUT_guaranteed'],r['CUT_possible']),fnum(r['entries_per_TP_min'])+' a '+fnum(r['entries_per_TP_max']),fnum(r['entries_per_SL_min'])+' a '+fnum(r['entries_per_SL_max']),rng(r['max_consecutive_SL_guaranteed'],r['max_consecutive_SL_possible'])]])
para('Faixas de frequencia e sequencias consideram desfechos possiveis onde ainda ha duvida. Os extremos de contagens distintas nao devem ser somados como se fossem simultaneos. Tabelas anuais, mensais e todas as receitas estao no Excel/CSVs.')
SimpleDocTemplate(str(P/'Novos_Niveis_e_Frequencias_2024_2026.pdf'),pagesize=landscape(A4),rightMargin=28,leftMargin=28,topMargin=25,bottomMargin=25).build(story)
manifest=dict(period='2024Jan-2026Oct',days=709,original_ops=1485,original_points=3950,original_DD=14805,new_entries=dict(collections.Counter(o['level'] for o in x['newops'])),recipes_per_level=168,new_level_tests=504,combinations_tested=765,original_unchanged=True,standby='Original five-level fixed stop50 target250 test remains on hold; not resumed.',primary_selection=primary,posthoc_best_points=bestpoints,posthoc_best_ratio=bestratio,frequency_original_all=[r for r in origfreq if r['period']=='ALL'],selected_replay_windows=len(windows),selected_replay_days=len({r['date'] for r in windows}),no_variant_promoted=True,sources=[dict(path=s,sha256=hashlib.sha256((R/s).read_bytes()).hexdigest()) for s in sorted(set(x['sources']))])
(P/'MANIFESTO.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in manifest.items() if k!='sources'},ensure_ascii=False,indent=2))
# Keep large complete operation and frequency tables in a lossless archive, not duplicated uncompressed in git.
with zipfile.ZipFile(P/'Tabelas_Completas.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for name in ['OPERACOES_TODOS_TESTES.csv','PENDENCIAS_TODOS_TESTES.csv','FREQUENCIAS_TODAS_CONFIGURACOES.csv']:z.write(P/name,arcname=name)
for name in ['OPERACOES_TODOS_TESTES.csv','PENDENCIAS_TODOS_TESTES.csv','FREQUENCIAS_TODAS_CONFIGURACOES.csv']:(P/name).unlink()
