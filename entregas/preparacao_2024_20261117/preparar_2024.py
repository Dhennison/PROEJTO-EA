"""Prepare Jan-Dec2024 without modifying closed months. No synthetic ticks or monthly totals.
Sources remain in versioned archives. All uncertain windows stay explicit.
"""
from pathlib import Path
import csv,io,zipfile,datetime as dt,collections,json,hashlib
from decimal import Decimal as D
R=Path(__file__).resolve().parents[2]
with zipfile.ZipFile(R/'entregas/arquivo_conversa_20261111/originais/ORIGINAIS_PARTE_005.zip') as z:b=z.read(next(n for n in z.namelist() if n.endswith('/EXPORT110_1794243035_5791.zip')))
assert hashlib.sha256(b).hexdigest()=='0e4a1cf44e37c4409ea856e8a52f754669819c338b080346ec643fdfbcbb7093'
m1=collections.defaultdict(list);m5=collections.defaultdict(list)
with zipfile.ZipFile(io.BytesIO(b)) as z:
 status=list(csv.DictReader(io.StringIO(z.read(next(n for n in z.namelist() if n.endswith('/STATUS.csv'))).decode('utf-8-sig')),delimiter=';'))
 for month_check in range(1,13):
  st=next(r for r in status if r['file']==f'M1_2024{month_check:02d}.csv')
  assert st['state']=='EXPORTADO_ESTAVEL' and st['attempts']=='2' and st['error']=='0'
 for n in z.namelist():
  if n.endswith('M1_202312.csv') or any(n.endswith(f'M1_2024{m:02d}.csv') for m in range(1,13)):
   for r in csv.DictReader(io.StringIO(z.read(n).decode('utf-8-sig')),delimiter=';'):
    t=dt.datetime.strptime(r['time'],'%Y.%m.%d %H:%M');m1[t.date()].append((t,*[D(r[k]) for k in ('open','high','low','close')],int(r['real_volume'])))
with zipfile.ZipFile(R/'entregas/historico_work_modelo_d_20261105/replay_setembro_20261106/originais/Candles_Originais_Modelo_D_2023_2026.zip') as z:
 for n in ['WINFUT_F_0_5min_01-01-2024_31-12-2024.csv']:
  for r in csv.reader(io.StringIO(z.read(n).decode('cp1252')),delimiter=';'):
   if r[0]=='Ativo':continue
   t=dt.datetime.strptime(r[1]+' '+r[2],'%d/%m/%Y %H:%M:%S');m5[t.date()].append((t,*[D(v.replace('.','').replace(',','.')) for v in r[3:7]],int(r[8].replace('.',''))))
for series in [m1,m5]:
 for b in series.values():b.sort()
def agg(bs):return list((bs[0][1],max(b[2] for b in bs),min(b[3] for b in bs),bs[-1][4]))

import sys,hashlib
P=Path(__file__).parent
sys.path.insert(0,str(R/'entregas/fechamento_agosto_v1_11/analise'))
from motor_precos import levels
sys.path.insert(0,str(R/'entregas/profit_marco_20261113'))
from analisar_marco import choices
def branch(bs,lev,grid):
 sign=1 if lev['buy'] else -1;suffix='5' if grid else '';e,t,s=[sign*lev[k+suffix] for k in ('entry','tp','sl')]
 active=False;en=None;ends=set();asks=[]
 for stamp,bo,bh,bl,bc,*_ in bs:
  o,h,l,c=(bo,bh,bl,bc) if sign==1 else (-bo,-bl,-bh,-bc)
  if stamp.time()>=dt.time(18):
   if active:ends.add(('CORTE',stamp.isoformat(),str(sign*bo-e)));active=False
   break
  entering=en is None
  if entering:
   if l>e:continue
   active=True;en=stamp
  if not active:continue
  ch=choices(o,h,l,c,e,t,s,entering)
  if len(ch)>1:asks.append(dict(minute=stamp.strftime('%H:%M'),phase='ENTRADA' if entering else 'POSICAO_ABERTA',choices='|'.join(sorted(ch))))
  for reason in ch-{'OPEN'}:ends.add((reason,stamp.isoformat(),str((t if reason=='TP' else s)-e)))
  active='OPEN' in ch
 if en is None:return None
 assert not active and ends,(bs[0][0],lev)
 outcomes=sorted(set((r,p) for r,tm,p in ends))
 return dict(entry_minute=en.strftime('%H:%M'),outcomes='|'.join(f'{r}:{p}' for r,p in outcomes),determined=len(outcomes)==1,min_points=str(min(D(p) for r,p in outcomes)),max_points=str(max(D(p) for r,p in outcomes)),branch_minutes='|'.join(a['minute'] for a in asks),exit_candidates='|'.join(f'{r}@{tm}' for r,tm,p in sorted(ends)),asks=asks)

def read(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter=';'))
def dec(x):return D(x.replace(',','.'))
def write(p,rs,fields=None):
 fields=fields or (list(rs[0]) if rs else ['estado'])
 with p.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields,delimiter=';',lineterminator='\n');w.writeheader();w.writerows(rs)
REF=R/'entregas/historico_work_modelo_d_20261105'
adj={r['DataOperacional']:r for r in read(REF/'Ajustes_Diarios_Modelo_D_20230301_20260921.csv')}
# Supplemental dates are outside the original Work comparison, but their adjustments
# are available in the original coverage table; keep their results separate.
with zipfile.ZipFile(REF/'originais/Pacote_Modelo_D_Historico_20230301_20260921.zip') as z:
 coverage_adjustments=list(csv.DictReader(io.StringIO(z.read('Cobertura_Ajustes_Fonte_Todas_Datas.csv').decode('utf-8-sig')),delimiter=';'))
supplemental={r['DataOperacional']:r for r in coverage_adjustments if r['DataOperacional'] not in adj}
adj.update(supplemental)
work=read(REF/'Operacoes_Modelo_D_20230301_20260921_ORIGINAL.csv');workdays={r['Data']:r for r in read(REF/'Referencia_D_diário.csv')}
# Expiry-day roll is the preserved Work convention, subject to price matching of copies.
rolls=[(dt.date(2024,2,14),'WINJ24'),(dt.date(2024,4,17),'WINM24'),(dt.date(2024,6,12),'WINQ24'),(dt.date(2024,8,14),'WINV24'),(dt.date(2024,10,16),'WINZ24'),(dt.date(2024,12,18),'WING25')]
def contract(day):
 c='WING24'
 for date,name in rolls:
  if day>=date:c=name
 return c
names=['Janeiro','Fevereiro','Março','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro','Novembro','Dezembro']
allsummary=[];allwindows=[];allcoverage=[];allissues=[]
for month in range(1,13):
 out=P/f'{month:02d}_{names[month-1]}';out.mkdir(exist_ok=True)
 days=sorted(d for d in m5 if d.year==2024 and d.month==month and d>=dt.date(2024,1,8));wi={(w['Data'],w['Nível']):w for w in work if w['Data'].startswith(f'2024-{month:02d}')}
 ops=[];refs=[];gran=[];checks=[];inventory=[];issues=[];windows=[];gap_audit=[];grade=[];matdiff=[];gap_requests=[];missing_source=[];evidence=[];daylevels={};branchmap={}
 context=max(d for d in m5 if d<days[0])
 for day in [context]+days:
  aa=m1.get(day,[]);bb=m5[day]
  if not aa:missing_source.append(str(day));continue
  buckets=collections.defaultdict(list)
  for a in aa:buckets[a[0].replace(minute=a[0].minute//5*5)].append(a)
  pricebad=qtybad=0
  for b in bb:
   rr=buckets[b[0]];oh=agg(rr) if rr else [];diff=sum(a[5] for a in rr)-b[5];match=oh==list(b[1:5]);pricebad+=not match;qtybad+=diff!=0
   checks.append(dict(data=str(day),hora=b[0].strftime('%H:%M'),M1=len(rr),OHLC_igual=match,OHLC_M1=str(oh),OHLC_M5=str(list(b[1:5])),quantidade_M1=sum(a[5] for a in rr),quantidade_M5=b[5],diferenca_quantidade=diff))
   if not match or diff:
    issues.append(dict(mes=f'2024-{month:02d}',data=str(day),inicio=b[0].strftime('%H:%M'),fim=(b[0]+dt.timedelta(minutes=5)).strftime('%H:%M'),tipo='PRECO' if not match else 'QUANTIDADE',detalhe=f'M1 {oh}; M5 {list(b[1:5])}; quantidade M1-M5 {diff}',acao='Preservar HLC Work no contexto;conferir fonte,sem mudar referencias' if not match else 'Ressalva quantitativa;precos iguais,nao prova de fita completa',contexto=day==context))
  inventory.append(dict(data=str(day),contexto=day==context,M1=len(aa),M5=len(bb),primeiro_M1=str(aa[0][0]),ultimo_M1=str(aa[-1][0]),OHLC_diario_igual=agg(aa)==agg(bb),grupos_preco_divergente=pricebad,grupos_quantidade_divergente=qtybad,ajuste=adj.get(str(day),{}).get('Ajuste','AUSENTE'),contrato=contract(day)))
 for day in days:
  if str(day) not in adj:
   issues.append(dict(mes=f'2024-{month:02d}',data=str(day),inicio='',fim='',tipo='AJUSTE_E_WORK_AUSENTES',detalhe='Candles existem,mas ajuste operacional e referencia diaria Work ausentes;nao atribuir zero nem calcular niveis',acao='Recuperar ajuste da fonte original antes de delimitar Replay;dia complementar separado',contexto=False));continue
  prior=max(d for d in m5 if d<day);pb=m1[prior] if day==dt.date(2024,1,8) else m5[prior];bs=m5[day];a=dec(adj[str(day)]['Ajuste'])
  ref=dict(open=str(bs[0][1]),high_prev=str(max(b[2] for b in pb)),low_prev=str(min(b[3] for b in pb)),close_prev=str(pb[-1][4]),adjustment=str(a));daylevels[day]=levels(ref)
  refs.append(dict(date=str(day),previous=str(prior),previous_source='MT5_M1_FULL_SUPPLEMENTAL_CONTEXT' if day==dt.date(2024,1,8) else 'WORK_M5_FULL',previous_first=str(pb[0][0]),previous_last=str(pb[-1][0]),previous_bars=len(pb),**ref,contrato_Replay=contract(day)))
  for lev in daylevels[day]:
   if not lev['eligible']:continue
   a1=branch(m1[day],lev,True);a5=branch(bs,lev,True);am=branch(m1[day],lev,False);am5=branch(bs,lev,False)
   branchmap[(day,lev['name'])]=a1
   if not a1:continue
   wr=wi.get((str(day),lev['name']))
   if wr:
    for k,wk in [('entry','Entrada'),('tp','Alvo'),('sl','Stop')]:
     if abs(lev[k]-dec(wr[wk]))>D('.00001'):matdiff.append((str(day),lev['name'],k,str(lev[k]),wr[wk]))
   # Every pre-cut OHLC bucket is equal; M1 cannot create a new outcome outside M5.
   grid_refines = bool(a5 and {(x.split(':')[0],D(x.split(':')[1])) for x in a1['outcomes'].split('|')}<={(x.split(':')[0],D(x.split(':')[1])) for x in a5['outcomes'].split('|')})
   math_refines = (am is None and am5 is None) or bool(am and am5 and {(x.split(':')[0],D(x.split(':')[1])) for x in am['outcomes'].split('|')} <= {(x.split(':')[0],D(x.split(':')[1])) for x in am5['outcomes'].split('|')})
   op=dict(date=str(day),level=lev['name'],contract=contract(day),entry=str(lev['entry5']),tp=str(lev['tp5']),sl=str(lev['sl5']),**{k:v for k,v in a1.items() if k!='asks'},work_reason=wr['Motivo'] if wr else 'SEM_OPERACAO_WORK',work_points=wr['Pontos'] if wr else '',coverage_pending=not(grid_refines and math_refines))
   if not(grid_refines and math_refines):issues.append(dict(mes=f'2024-{month:02d}',data=str(day),inicio=a1['entry_minute'],fim='',tipo='DIVERGENCIA_REFINAMENTO_M1_M5',detalhe=f'{lev["name"]}:grade={grid_refines},matematico={math_refines}',acao='Conferir divergencia de fontes antes de encerrar',contexto=False))
   ops.append(op)
   gran.append(dict(data=str(day),nivel=lev['name'],Work_entrada=wr['Hora entrada'] if wr else '',Work_saida=wr['Hora saída'] if wr else '',M5_entrada=a5['entry_minute'] if a5 else '',M1_entrada=a1['entry_minute'],M1_saidas_possiveis=a1['exit_candidates'],Work_motivo=op['work_reason'],Work_pontos=op['work_points'],M5_grade=a5['outcomes'] if a5 else '',M1_grade=a1['outcomes'],M1_matematico=am['outcomes'] if am else 'SEM_ENTRADA',resolvida_por_M1=a1['determined'] and not (a5 and a5['determined']),ainda_ambigua=not a1['determined']))
   if not a1['determined']:
    for ask in a1['asks']:
     start=dt.datetime.combine(day,dt.time.fromisoformat(ask['minute']));windows.append(dict(mes=f'2024-{month:02d}',data=str(day),contrato=contract(day),inicio=start.strftime('%H:%M:%S'),fim_exclusivo=(start+dt.timedelta(minutes=1)).strftime('%H:%M:%S'),nivel=lev['name'],tipo='SEQUENCIA',entrada=op['entry'],alvo=op['tp'],stop=op['sl'],motivo='Ramos M1 ainda permitem desfechos diferentes',prioridade='COLETAR'))
   else:
    # Extra control only when price normalization changes exit reason/entry existence.
    reasons={x.split(':')[0] for x in am['outcomes'].split('|')} if am else {'SEM_ENTRADA'}
    reason=a1['outcomes'].split(':')[0]
    if reasons!={reason}:
     tm=a1['exit_candidates'].split('|')[0].split('@')[1];start=dt.datetime.combine(day,dt.time.fromisoformat(a1['entry_minute'])) if am is None else dt.datetime.fromisoformat(tm)
     windows.append(dict(mes=f'2024-{month:02d}',data=str(day),contrato=contract(day),inicio=start.strftime('%H:%M:%S'),fim_exclusivo=(start+dt.timedelta(minutes=1)).strftime('%H:%M:%S'),nivel=lev['name'],tipo='CONTROLE_GRADE5',entrada=op['entry'],alvo=op['tp'],stop=op['sl'],motivo=f'Grade {a1["outcomes"]} versus matematico {am['outcomes'] if am else 'SEM_ENTRADA'}',prioridade='COLETAR'))
     grade.append((str(day),lev['name']))
 # Missing-minute audit. Do not certify a position based on shared long gaps.
 for day in days:
  if day not in daylevels:continue
  aa=m1[day]
  for before,after in zip(aa,aa[1:]):
   if after[0]-before[0]<=dt.timedelta(minutes=1):continue
   start=before[0]+dt.timedelta(minutes=1);end=after[0];affected=[];unbounded=False
   if start.time()<dt.time(18):
    # Bounds exist only if each missing minute belongs to an actual Work M5 bar.
    missing=[];t=start
    while t<end:
     if t.time()<dt.time(18):missing.append(t)
     t+=dt.timedelta(minutes=1)
    bs_by_time={b[0]:b for b in m5[day]};bounds=[bs_by_time.get(t.replace(minute=t.minute//5*5)) for t in missing]
    unbounded=any(b is None for b in bounds)
    hi=max((b[2] for b in bounds if b is not None),default=D(0));lo=min((b[3] for b in bounds if b is not None),default=D(0))
    for lev in daylevels[day]:
     if not lev['eligible']:continue
     op=next((o for o in ops if o['date']==str(day) and o['level']==lev['name']),None)
     done=op is not None and all(dt.datetime.fromisoformat(x.split('@')[1])<start for x in op['exit_candidates'].split('|'))
     if done:continue
     entry=dt.datetime.combine(day,dt.time.fromisoformat(op['entry_minute'])) if op else None
     unentered=not entry or entry>=start
     hit=unbounded or ((lo<=lev['entry5'] if lev['buy'] else hi>=lev['entry5']) if unentered else (lo<=min(lev['tp5'],lev['sl5']) or hi>=max(lev['tp5'],lev['sl5'])))
     if hit:
      affected.append(lev['name'])
      if op:op['coverage_pending']=True
    if affected:
     gap_requests.append(dict(mes=f'2024-{month:02d}',data=str(day),contrato=contract(day),inicio=start.strftime('%H:%M:%S'),fim_exclusivo=end.strftime('%H:%M:%S'),niveis=','.join(affected),tipo='COBERTURA_COMPARTILHADA_SEM_M5' if unbounded else 'COBERTURA_MINUTOS_M1',acao='Verificar no Replay se houve negocios;recuperar candles M1 primeiro,nao copiar toda fita longa' if unbounded else 'Conferir negocios apenas nos minutos ausentes;possivel efeito nos niveis listados',minutos=int((end-start).total_seconds()/60)))
   gap_audit.append(dict(data=str(day),inicio=start.strftime('%H:%M:%S'),fim_exclusivo=end.strftime('%H:%M:%S'),minutos=int((end-start).total_seconds()/60),sem_limites_M5=unbounded,niveis_possivelmente_afetados=','.join(affected),acao='PENDENTE_COBERTURA' if affected else 'SEM_EFEITO_D_ATUAL'))
 seq=sum(not o['determined'] for o in ops);coverage_known=sum(o['coverage_pending'] for o in ops)
 clear=sum(o['determined'] and not o['coverage_pending'] and (o['date'],o['level']) not in grade for o in ops)
 missing=sorted(set(wi)-{(o['date'],o['level']) for o in ops});extra=sorted({(o['date'],o['level']) for o in ops}-set(wi))
 # Differences are retained in RESUMO for explicit reconciliation.
 # Merge collection windows by exact date/time; preserve per-operation detail separately.
 grouped=[]
 for w in windows:
  k=next((g for g in grouped if all(g[x]==w[x] for x in ['data','contrato','inicio','fim_exclusivo'])),None)
  if k:k['niveis']+=','+w['nivel'];k['tipo']+='|'+w['tipo']
  else:grouped.append({x:w[x] for x in ['mes','data','contrato','inicio','fim_exclusivo','tipo','prioridade']}|{'niveis':w['nivel'],'instrucoes':'Alguns segundos antes/depois;sem filtros,saltos ou deduplicacao;manter ms eordem.'})
 grouped.sort(key=lambda x:(x['data'],x['inicio']))
 summary=dict(mes=f'2024-{month:02d}',nome=names[month-1],pregoes=len(days),operacoes=len(ops),determinadas_candles= sum(o['determined'] for o in ops),concretas_sem_ressalva_de_sequencia_cobertura_grade=clear,pendentes_sequencia=seq,controles_grade=len(grade),operacoes_conhecidas_com_cobertura_pendente=coverage_known,janelas_replay=len(grouped),minutos_replay=sum(int((dt.datetime.fromisoformat(g['data']+'T'+g['fim_exclusivo'])-dt.datetime.fromisoformat(g['data']+'T'+g['inicio'])).total_seconds()/60) for g in grouped),intervalos_cobertura_a_conferir=len(gap_requests),Work_pontos=str(sum(dec(w['Pontos']) for w in wi.values())),ajustes=len(refs),M1=sum(len(m1[d]) for d in days),M5=sum(len(m5[d]) for d in days),grupos_preco_divergente=sum(not c['OHLC_igual'] for c in checks if c['data'] in [str(d) for d in days]),grupos_quantidade_divergente=sum(c['diferenca_quantidade']!=0 for c in checks if c['data'] in [str(d) for d in days]),contexto=refs[0],principal=None,DD_teste=None,ajustes_complementares=[str(d) for d in days if str(d) in supplemental],ajustes_ausentes=[str(d) for d in days if str(d) not in adj],datas_fora_Work=[str(d) for d in days if str(d) not in workdays],status='PREPARADO_AGUARDANDO_REPLAY_E_CONTROLES',resultado_mensal_fechado=False,mathematical_differences=matdiff,work_missing=missing,work_extra=extra)
 write(out/'COLETAS_REPLAY.csv',grouped,['mes','data','contrato','inicio','fim_exclusivo','tipo','prioridade','niveis','instrucoes']);write(out/'JANELAS_POR_OPERACAO.csv',windows)
 write(out/'CONTROLES_COBERTURA.csv',gap_requests);write(out/'AUDITORIA_LACUNAS.csv',gap_audit)
 write(out/'DATAS_E_DIVERGENCIAS.csv',issues);write(out/'CONFERENCIA_M1_M5.csv',checks);write(out/'INVENTARIO_POR_DATA.csv',inventory);write(out/'REFERENCIAS.csv',refs);write(out/'OPERACOES_POSSIBILIDADES.csv',ops);write(out/'COMPARATIVO_WORK_M5_M1.csv',gran)
 (out/'RESUMO.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
 allsummary.append(summary);allwindows.extend(grouped);allcoverage.extend(gap_requests);allissues.extend(issues)
 print(json.dumps({k:v for k,v in summary.items() if k not in ('contexto','mathematical_differences','work_missing','work_extra')},ensure_ascii=False))
write(P/'COLETAS_TODOS_MESES.csv',allwindows);write(P/'CONTROLES_COBERTURA_TODOS_MESES.csv',allcoverage);write(P/'DATAS_DIVERGENTES_TODOS_MESES.csv',allissues)
(P/'RESUMO_TODOS_MESES.json').write_text(json.dumps(allsummary,ensure_ascii=False,indent=2)+'\n')
