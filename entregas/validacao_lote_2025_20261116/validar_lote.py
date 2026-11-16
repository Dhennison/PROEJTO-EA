"""Resolve targeted Replay against frozenD references;never close incomplete months."""
from pathlib import Path
from decimal import Decimal as D
import csv,json,zipfile,io,pickle,collections,datetime as dt,sys,hashlib
P=Path(__file__).parent;R=P.parents[1];PRE=R/'entregas/preparacao_jan_nov_2025_20261115'
sys.path.insert(0,str(R/'entregas/fechamento_agosto_v1_11/analise'))
from motor_precos import levels
sys.path.insert(0,str(R/'entregas/profit_marco_20261113'))
from analisar_marco import choices
def read(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter=';'))
def write(p,rows,fields=None):
 fields=fields or (list(rows[0]) if rows else ['estado'])
 with p.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields,delimiter=';',lineterminator='\n');w.writeheader();w.writerows(rows)
def dec(s):return D(s.replace(',','.'))
inv=json.loads((P/'INVENTARIO_ABAS.json').read_text())
if (P/'COMPLEMENTO_02JAN.json').exists():
 replacement=json.loads((P/'COMPLEMENTO_02JAN.json').read_text());inv=[replacement if x['sheet']=='JAN 02-01-25' else x for x in inv]
if (P/'COMPLEMENTO_09ABR.json').exists():
 replacement=json.loads((P/'COMPLEMENTO_09ABR.json').read_text());inv=[replacement if x['sheet']=='ABR 09-04-25' else x for x in inv]
(P/'INVENTARIO_FONTES_EM_USO.json').write_text(json.dumps(inv,ensure_ascii=False,indent=2)+'\n')
with zipfile.ZipFile(R/'entregas/arquivo_conversa_20261111/originais/ORIGINAIS_PARTE_005.zip') as z:raw=z.read(next(n for n in z.namelist() if n.endswith('/EXPORT110_1794243035_5791.zip')))
assert hashlib.sha256(raw).hexdigest()=='0e4a1cf44e37c4409ea856e8a52f754669819c338b080346ec643fdfbcbb7093'
bars=collections.defaultdict(list);qty={}
with zipfile.ZipFile(io.BytesIO(raw)) as z:
 for month in range(1,12):
  rawm=z.read(next(n for n in z.namelist() if n.endswith(f'/M1_2025{month:02d}.csv')))
  for r in csv.DictReader(io.StringIO(rawm.decode('utf-8-sig')),delimiter=';'):
   day=r['time'][:10].replace('.','-');tm=r['time'][11:];bars[day].append((tm,*[D(r[k]) for k in ('open','high','low','close')]));qty[(day,tm)]=int(r['real_volume'])
for bs in bars.values():bs.sort()
streams={};checks=[];boundaries=[]
for meta in inv:
 rawrows=pickle.loads(Path(meta['cache']).read_bytes());es=[dict(time=t,price=p,quantity=q,source_row=n) for t,p,q,n in rawrows];chron=es[::-1];alt=sorted(es,key=lambda e:e['time']);day=meta['date'];name=meta['sheet'];streams[name]=(day,chron,alt)
 bymin=collections.defaultdict(list)
 for e in chron:bymin[e['time'][:5]].append(e)
 bm={b[0]:b for b in bars[day]}
 for minute,rr in sorted(bymin.items()):
  b=bm.get(minute);oh=[rr[0]['price'],max(e['price'] for e in rr),min(e['price'] for e in rr),rr[-1]['price']];q=sum(e['quantity'] for e in rr)
  checks.append(dict(sheet=name,date=day,minute=minute,records=len(rr),quantity=q,M1_quantity=qty.get((day,minute),''),OHLC=str(oh),M1_OHLC=str(list(b[1:])) if b else '',OHLC_match=bool(b and oh==list(b[1:])),quantity_match=q==qty.get((day,minute)),interior=chron[0]['time'][:5]<minute<chron[-1]['time'][:5]))
 for a,b in zip(chron,chron[1:]):
  t1=dt.datetime.strptime(a['time'],'%H:%M:%S.%f');t2=dt.datetime.strptime(b['time'],'%H:%M:%S.%f')
  if t2-t1>dt.timedelta(minutes=1):boundaries.append(dict(sheet=name,date=day,last_trade=a['time'],next_trade=b['time'],seconds=(t2-t1).total_seconds()))
def resolve(events,lev,day,grid=True,known_entry=None):
 buy=lev['buy'];sgn=1 if buy else -1;e,tp,sl=[sgn*lev[k+('5' if grid else '')] for k in ('entry','tp','sl')]
 entered=known_entry;exit=None;reason=None
 for ev in events:
  p=sgn*D(ev['price'])
  if entered is None:
   if p<=e:entered=ev
   continue
  if p<=sl or p>=tp:exit=ev;reason='SL' if p<=sl else 'TP';break
 if entered is None:return dict(reason='NO_ENTRY_IN_COPY')
 if exit is None:
  lastminute=events[-1]['time'][:5]
  last_complete=sum(x['quantity'] for x in events if x['time'][:5]==lastminute)==qty.get((day,lastminute))
  for minute,bo,bh,bl,bc in bars[day]:
   if minute<lastminute or (minute==lastminute and last_complete):continue
   if minute==lastminute and entered['time'][:5]==lastminute:return dict(reason='INCOMPLETE_ENTRY_MINUTE',minute=minute,entry=entered)
   if minute>='18:00':exit=dict(time=minute+':00_CANDLE',price=int(bo));reason='CORTE';break
   o,h,l=(bo,bh,bl) if buy else (-bo,-bl,-bh)
   if minute>lastminute and (o>=tp or o<=sl):reason='TP' if o>=tp else 'SL'
   else:
    hit_tp=h>=tp;hit_sl=l<=sl
    if hit_tp and hit_sl:return dict(reason='UNRESOLVED_AFTER_COPY',minute=minute,entry=entered)
    if not hit_tp and not hit_sl:continue
    reason='TP' if hit_tp else 'SL'
   exit=dict(time=minute+':00_CANDLE',price=int(sgn*(tp if reason=='TP' else sl)));break
 if exit is None:return dict(reason='OPEN_WITHOUT_CUT')
 points=(tp if reason=='TP' else sl)-e if reason!='CORTE' else sgn*D(exit['price'])-e
 return dict(reason=reason,points=str(points),entry=entered,exit=exit,exit_source='CANDLES_AFTER_WINDOW' if 'CANDLE' in exit['time'] else 'REPLAY')
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

# Price-engine regressions retain prior protocol,including rejection of incomplete entry bar.
fake='2099-01-01';lv={k:D(v) for k,v in {'entry':100,'tp':115,'sl':90,'entry5':100,'tp5':115,'sl5':90}.items()}|{'buy':True}
events=[dict(time='09:00:00.001',price=110,quantity=1),dict(time='09:00:01.001',price=120,quantity=1),dict(time='09:00:59.999',price=95,quantity=1)]
bars[fake]=[('09:00',D(110),D(120),D(95),D(95)),('09:01',D(95),D(100),D(85),D(85))];qty[(fake,'09:00')]=3
assert resolve(events,lv,fake)['reason']=='SL';qty[(fake,'09:00')]=4;assert resolve(events,lv,fake)['reason']=='INCOMPLETE_ENTRY_MINUTE'
del bars[fake];del qty[(fake,'09:00')]
# Coverage information is user-reported and checked against accessible copies.
coverage_audits=[]
for day,names,kind in [('2025-06-03',['Cobertura 03-06-25'],'USER_NO_QUOTES_0903_TO0956'),('2025-07-30',['JUL 30-07-25'],'USER_AUCTION_1543_TO1547')]:
 name=names[0];day0,c,a=streams[name];cc=[x for x in checks if x['sheet']==name]
 coverage_audits.append(dict(date=day,sheet=name,explanation=kind,first=c[0]['time'],last=c[-1]['time'],observed_gaps=[x for x in boundaries if x['sheet']==name],minute_checks=cc))
# 21Aug later TXT audited in previous receipt;use that preserved audit,not synthetic joins.
aug_audit=json.loads((R/'entregas/recebimento_lote_2025_20261116/AUDITORIA_TEXTO_21AGO.json').read_text())
assert aug_audit['S61_8']['primary']['reason']=='TP' and aug_audit['S61_8']['primary']['points']=='170'
coverage_audits.append(dict(date='2025-08-21',explanation='USER_THREE_AUCTIONS_TEXT_AUDITED',previous_audit='entregas/recebimento_lote_2025_20261116/AUDITORIA_TEXTO_21AGO.json',result=aug_audit['S61_8'],quantity_remark_0916=-1))
allsummary=[];allpending=[];allresolved=[]
for month in range(1,12):
 src=next(p for p in PRE.iterdir() if p.is_dir() and p.name.startswith(f'{month:02d}_'));out=P/src.name;out.mkdir(exist_ok=True)
 if (out/'RESULTADO_FINAL.json').exists():
  saved=json.loads((out/'RESULTADO_FINAL.json').read_text());allsummary.append(saved);allresolved.extend(r for r in saved['results'] if r['resolved']);print('PRESERVED_CLOSED_MONTH',saved['month'],flush=True);continue
 ops=read(src/'OPERACOES_POSSIBILIDADES.csv');refs={r['date']:r for r in read(src/'REFERENCIAS.csv')};ws=read(src/'JANELAS_POR_OPERACAO.csv');gradekeys={(r['data'],r['nivel']):r for r in ws if r.get('tipo')=='CONTROLE_GRADE5'}
 results=[];lookup={};pending=[]
 for op in ops:
  key=(op['date'],op['level']);is_control=key in gradekeys
  if op['determined']=='True' and not is_control:continue
  day=op['date'];lev=next(l for l in levels(refs[day]) if l['name']==op['level'])
  requests=[w for w in ws if w.get('data')==day and w.get('nivel')==op['level'] and w.get('tipo')=='SEQUENCIA']
  minute=gradekeys[key]['inicio'][:5] if is_control else min(w['inicio'][:5] for w in requests)
  candidates=[(name,c,a) for name,(d,c,a) in streams.items() if d==day and c[0]['time'][:5]<=minute<=c[-1]['time'][:5] and not name.startswith('Cobertura')]
  if not candidates:
   avail=[m for m in inv if m['date']==day]
   r=dict(date=day,level=op['level'],contract=op['contract'],resolved=False,reason='MISSING_REQUIRED_WINDOW',required_minute=minute,available_windows=[(m['sheet'],m['start'],m['end']) for m in avail]);results.append(r);pending.append(r);continue
  assert len(candidates)==1,(key,[x[0] for x in candidates])
  name,c,a=candidates[0]
  known=dict(time=op['entry_minute']+':00_CANDLE',price=int(lev['entry5']),source='ENTRY_PREVIOUSLY_DETERMINED_M1') if op['entry_minute']<c[0]['time'][:5] else None
  primary=resolve(c,lev,day,known_entry=known);tie=resolve(a,lev,day,known_entry=known)
  math_bars=[(dt.datetime.fromisoformat(day+'T'+b[0]),*b[1:]) for b in bars[day]]
  math_branch=branch(math_bars,lev,False)
  math_known=dict(time=math_branch['entry_minute']+':00_CANDLE',price=str(lev['entry']),source='MATHEMATICAL_ENTRY_PREVIOUSLY_DETERMINED_M1') if math_branch and math_branch['entry_minute']<c[0]['time'][:5] else None
  math=resolve(c,lev,day,False,math_known);math_tie=resolve(a,lev,day,False,math_known)
  if math['reason']=='NO_ENTRY_IN_COPY' and math_branch and math_branch['determined'] and math_branch['entry_minute']>=c[-1]['time'][:5]:
   reason,points=math_branch['outcomes'].split(':');math=dict(reason=reason,points=points,entry=dict(time=math_branch['entry_minute']+':00_CANDLE',source='M1_AFTER_COPY'),exit=dict(time=math_branch['exit_candidates']),exit_source='MATHEMATICAL_M1_DETERMINED_AFTER_COPY');math_tie=dict(math)
  check=next((x for x in checks if x['sheet']==name and x['minute']==minute),None)
  same=primary.get('reason')==tie.get('reason') and primary.get('points')==tie.get('points');msame=math.get('reason')==math_tie.get('reason') and math.get('points')==math_tie.get('points')
  coverage_ok=bool(check and check['OHLC_match'] and check['quantity_match'])
  prefix_proof=None
  # An incomplete prefix need not be recollected if ALL prefix states lead
  # to the observed result: opposite barrier lies outside entire M1 entry bar.
  if not coverage_ok and not known and primary.get('reason') in ('TP','SL') and c[0]['time'][:5]==op['entry_minute'] and primary.get('entry',{}).get('time','')[:5]==op['entry_minute']:
   bar=next(b for b in bars[day] if b[0]==op['entry_minute']);opposite=lev['sl5'] if primary['reason']=='TP' else lev['tp5']
   unreachable=(opposite<bar[3] if lev['buy'] and primary['reason']=='TP' or not lev['buy'] and primary['reason']=='SL' else opposite>bar[2])
   if unreachable and same:
    prefix_proof=dict(method='M1_ENTRY_BAR_BOUNDS_PLUS_OBSERVED_LATER_ENTRY_EXIT',entry_bar_OHLC=[str(v) for v in bar[1:]],opposite_barrier=str(opposite),missing_prefix_cannot_reach_opposite_barrier=True,earlier_entry_or_same_result_exit_possible=True,exact_entry_exit_timestamps_not_certified=True)
  valid=same and (coverage_ok or prefix_proof is not None) and primary['reason'] in ('TP','SL','CORTE')
  # Reject opposite barriers in a shared ms even if two deterministic orders agree.
  groups=collections.defaultdict(list);en=primary.get('entry',{}).get('time','');ex=primary.get('exit',{}).get('time','');mixed=[]
  for e in c:
   if en<=e['time']<=ex:groups[e['time']].append(e['price'])
  for stamp,prices in groups.items():
   if min(prices)<=min(lev['tp5'],lev['sl5']) and max(prices)>=max(lev['tp5'],lev['sl5']):mixed.append(stamp)
  valid=bool(valid and not mixed)
  if primary.get('entry') and primary.get('exit'):assert primary['exit']['time'][:5]>=primary['entry']['time'][:5],(key,'exit before entry')
  r=dict(date=day,level=op['level'],contract=op['contract'],sheet=name,required_minute=minute,grade_control=is_control,primary=primary,tie_control=tie,tie_invariant=same,mathematical=math,mathematical_tie_invariant=msame,mathematical_levels={k:str(lev[k]) for k in ('entry','tp','sl')},minute_check=check,partial_prefix_invariance_proof=prefix_proof,timestamps_conditional_on_no_earlier_entry=prefix_proof is not None,mixed_barrier_ms=mixed,resolved=valid)
  if valid:
   allowed=[(x.split(':')[0],D(x.split(':')[1])) for x in op['outcomes'].split('|')];assert (primary['reason'],D(primary['points'])) in allowed,(op,primary)
   lookup[key]=r
  else:
   r['reason']='INCOMPLETE_ENTRY_OR_CONTROL_MINUTE' if not check or not check['OHLC_match'] or not check['quantity_match'] else primary['reason'];pending.append(r)
  results.append(r)
 final=[];daily=[]
 for op in ops:
  key=(op['date'],op['level']);r=lookup.get(key);control_failed=key in gradekeys and key not in lookup
  if r:
   reason,points=r['primary']['reason'],r['primary']['points'];basis=r['primary']['exit_source'];entry=r['primary']['entry']['time'];exit=r['primary']['exit']['time']
   if r.get('partial_prefix_invariance_proof'):basis='M1_BOUNDS_PLUS_PARTIAL_REPLAY_RESULT_INVARIANT';entry+=' OBSERVADO_POSSIVEL_ANTERIOR';exit+=' OBSERVADO_POSSIVEL_ANTERIOR'
  elif op['determined']=='True' and not control_failed:reason,points=op['outcomes'].split(':');basis='M1_DETERMINED';entry=op['entry_minute']+':00_CANDLE';exit=op['exit_candidates']
  else:reason='PENDENTE';points='';basis='PENDING_REPLAY';entry=op['entry_minute'];exit=''
  # User auction statements are preserved;coverage copies are audited separately.
  if op['date']=='2025-08-21' and op['level']=='S61.8':reason,points,basis,exit='TP','170','M1_PLUS_AUDITED_LATER_TEXT',aug_audit['S61_8']['primary']['exit_time']
  final.append(dict(date=op['date'],contract=op['contract'],level=op['level'],reason=reason,points=points,basis=basis,entry=entry,exit=exit,work_reason=op['work_reason'],work_points=op['work_points'],outside_Work=not op['work_points']))
 for day in refs:
  rr=[r for r in final if r['date']==day];unresolved=sum(r['reason']=='PENDENTE' for r in rr);work_available=all(r['work_points']!='' for r in rr) if rr else day not in json.loads((src/'RESUMO.json').read_text())['datas_fora_Work'];work=sum((dec(r['work_points']) for r in rr if r['work_points']),D(0));total=sum((D(r['points']) for r in rr if r['points']),D(0))
  daily.append(dict(date=day,operations=len(rr),pending=unresolved,test_points=str(total) if not unresolved else 'PENDENTE',work_points=str(work) if work_available else '',difference=str(total-work) if not unresolved and work_available else '',scope='WORK_COMPARAVEL' if work_available else 'COMPLEMENTO_FORA_WORK'))
 daily.sort(key=lambda r:r['date']);complete=not pending;total=sum((D(r['test_points']) for r in daily),D(0)) if complete else None
 summary=dict(month=f'2025-{month:02d}',status='REPLAY_RESOLVIDO_AGUARDA_CONFERENCIA_FINAL' if complete else 'PARCIAL_AGUARDA_COMPLEMENTO',operations=len(ops),resolved_original_pending=sum(r['resolved'] and not r.get('grade_control') for r in results),grade_controls_resolved=sum(r['resolved'] and r.get('grade_control') for r in results),pending=len(pending),principal=str(total) if total is not None else None,work_points=str(sum((dec(r['work_points']) for r in final if r['work_points']),D(0))),outside_Work_dates=json.loads((src/'RESUMO.json').read_text())['datas_fora_Work'],results=results,unresolved=pending,source_workbook_sha256='e0992ed7c4b603a1a24307f30b94713952af9bebae9f5c417fd81c010817fd13')
 write(out/'OPERACOES_APOS_REPLAY.csv',final);write(out/'DIARIO_APOS_REPLAY.csv',daily)
 (out/'RESULTADO_RECEBIMENTO.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
 allsummary.append(summary);allpending.extend(pending);allresolved.extend(r for r in results if r['resolved'])
 print(json.dumps({k:v for k,v in summary.items() if k not in ('results','unresolved')},ensure_ascii=False),flush=True)
write(P/'MINUTOS_TODAS_ABAS.csv',checks);write(P/'INTERVALOS_SEM_REGISTROS_ABAS.csv',boundaries)
(P/'CONTROLES_COBERTURA.json').write_text(json.dumps(coverage_audits,ensure_ascii=False,indent=2)+'\n')
(P/'RESULTADOS_TODOS_MESES.json').write_text(json.dumps(allsummary,ensure_ascii=False,indent=2)+'\n')
(P/'PENDENCIAS.json').write_text(json.dumps(allpending,ensure_ascii=False,indent=2)+'\n')
print('PENDING',json.dumps(allpending,ensure_ascii=False,indent=2))
