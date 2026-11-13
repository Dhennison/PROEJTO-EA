"""Audit all submitted Replay sheets, retain records, resolve D conditional prices."""
from pathlib import Path
import csv,json,collections,datetime as dt,sys,hashlib
from decimal import Decimal as D
import openpyxl
OUT=Path(__file__).parent;ROOT=OUT.parents[1]
sys.path.insert(0,str(ROOT/'entregas/fechamento_agosto_v1_11/analise'))
from motor_precos import levels
XLS=Path('/workspace/attachments/5a8ae9ea-8406-4706-9d89-14638baf4c7c/Mês de Abril.xlsx')
SOURCE=Path('/workspace/candles_originais_modelo_d/WINFUT_F_0_1min_01-01-2026_22-09-2026.csv')
def read(n):
 with (OUT/n).open(encoding='utf-8-sig') as f:return list(csv.DictReader(f,delimiter=';'))
def write(n,rr):
 if not rr:return
 with (OUT/n).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rr[0]),delimiter=';',lineterminator='\n');w.writeheader();w.writerows(rr)
def dec(x):return D(str(x).replace(',','.'))
bars=collections.defaultdict(list);qty={}
for r in csv.reader(SOURCE.read_bytes().decode('cp1252').splitlines(),delimiter=';'):
 if r[0]=='Ativo':continue
 day=dt.datetime.strptime(r[1],'%d/%m/%Y').date().isoformat();tm=r[2][:5];bars[day].append((tm,*[D(x.replace('.','').replace(',','.')) for x in r[3:7]]));qty[(day,tm)]=int(r[8].replace('.',''))
for bs in bars.values():bs.sort()
work_dates={r['Data'] for r in csv.DictReader((ROOT/'entregas/historico_work_modelo_d_20261105/Referencia_D_diário.csv').open(encoding='utf-8-sig'),delimiter=';')}
refs={r['date']:r for r in read('REFERENCIAS_ABRIL.csv')};ops=read('OPERACOES_POSSIBILIDADES.csv')
streams={};checks=[];sheets=[];ignored_sheets=[]
w=openpyxl.load_workbook(XLS,read_only=True,data_only=True)
for sh in w:
 day='2026-04-'+sh.title[:2];events=[]
 for ordinal,row in enumerate(sh.iter_rows(min_row=2,values_only=True),2):
  if row[0] is None:continue
  assert isinstance(row[0],str) and len(row[0])==12,(sh.title,ordinal,row)
  events.append(dict(time=row[0],price=int(row[2]),quantity=int(row[3]),source_row=ordinal))
 if not events:
  ignored_sheets.append({'sheet':sh.title,'reason':'EMPTY_NO_BUSINESS_RECORDS'});continue
 assert all(a['time']>=b['time'] for a,b in zip(events,events[1:])),sh.title
 chron=list(reversed(events));alt=sorted(events,key=lambda e:e['time']);streams[sh.title]=(day,chron,alt)
 sheets.append(dict(sheet=sh.title,date=day,records=len(events),start=chron[0]['time'],end=chron[-1]['time'],at_observed_limit=len(events)>=200001))
 for minute in sorted({e['time'][:5] for e in chron}):
  es=[e for e in chron if e['time'].startswith(minute)];b=next((b for b in bars[day] if b[0]==minute),None)
  oh=[es[0]['price'],max(e['price'] for e in es),min(e['price'] for e in es),es[-1]['price']];volume=sum(e['quantity'] for e in es)
  checks.append(dict(sheet=sh.title,date=day,minute=minute,records=len(es),quantity=volume,csv_quantity=qty.get((day,minute)),ohlc=str(oh),csv_ohlc=str(list(b[1:])) if b else '',ohlc_match=bool(b and oh==list(b[1:])),quantity_match=volume==qty.get((day,minute)),full_minute_from_bounds=minute>chron[0]['time'][:5] and minute<chron[-1]['time'][:5]))

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
# Regression: do not re-read a completed entry candle and credit its PRE-entry high.
fake_day='2099-01-01';fake_level={'buy':True,'entry5':D(100),'tp5':D(115),'sl5':D(90),'entry':D(100),'tp':D(115),'sl':D(90)}
fake_events=[{'time':'09:00:00.001','price':110,'quantity':1},{'time':'09:00:01.001','price':120,'quantity':1},{'time':'09:00:59.999','price':95,'quantity':1}]
bars[fake_day]=[('09:00',D(110),D(120),D(95),D(95)),('09:01',D(95),D(100),D(85),D(85))];qty[(fake_day,'09:00')]=3
regression=resolve(fake_events,fake_level,fake_day)
assert regression['reason']=='SL' and regression['exit']['time'].startswith('09:01')
qty[(fake_day,'09:00')]=4
assert resolve(fake_events,fake_level,fake_day)['reason']=='INCOMPLETE_ENTRY_MINUTE'
del bars[fake_day];del qty[(fake_day,'09:00')]
resolved=[];results=[]
for op in ops:
 is_control=False
 if op['determined']=='True' and not is_control:continue
 day=op['date'];lev=next(l for l in levels(refs[day]) if l['name']==op['level'])
 candidates=[(name,c,a) for name,(d,c,a) in streams.items() if d==day and (is_control or c[0]['time'][:5]<=op['entry_minute']<=c[-1]['time'][:5])]
 if not candidates:
  results.append({'date':day,'level':op['level'],'resolved':False,'reason':'MISSING_REPLAY_WINDOW'});continue
 assert len(candidates)==1,(op,candidates)
 name,c,a=candidates[0]
 known_entry={'time':op['entry_minute']+':00_CANDLE','price':int(lev['entry5']),'source':'ENTRY_MINUTE_PREVIOUSLY_DETERMINED_FROM_CANDLES'} if is_control else None
 primary=resolve(c,lev,day,known_entry=known_entry);control=resolve(a,lev,day,known_entry=known_entry);math=resolve(c,lev,day,False,known_entry=known_entry)
 same=primary.get('reason')==control.get('reason') and primary.get('points')==control.get('points')
 # Check mixed TP/SL trade groups inside the position; opposite barriers at a shared ms are not ordered by timestamps.
 en=primary.get('entry',{}).get('time','');ex=primary.get('exit',{}).get('time','');mixed=[]
 if en and ex:
  buckets=collections.defaultdict(list)
  for ev in c:
   if en<=ev['time']<=ex:buckets[ev['time']].append(ev['price'])
  for tm,prices in buckets.items():
   if min(prices)<=min(lev['tp5'],lev['sl5']) and max(prices)>=max(lev['tp5'],lev['sl5']):mixed.append(tm)
 valid=same and not mixed and primary['reason'] in ('TP','SL','CORTE')
 results.append(dict(date=day,level=op['level'],sheet=name,contract=refs[day]['contrato_Replay'],grade_control=is_control,primary=primary,tie_control=control,mathematical=math,tie_invariant=same,mixed_exit_barrier_ms=mixed,resolved=valid))
 if valid:
  assert primary['points'] in [v.split(':',1)[1] for v in op['outcomes'].split('|') if v.startswith(primary['reason']+':')],(op,primary)
  required=next(x for x in checks if x['sheet']==name and x['minute']==('17:00' if is_control else op['entry_minute']))
  assert required['ohlc_match'] and required['quantity_match'],required
 if valid:resolved.append(dict(date=day,level=op['level'],reason=primary['reason'],points=primary['points'],entry_time=primary['entry']['time'],exit_time=primary['exit']['time'],exit_source=primary['exit_source'],sheet=name,contract=refs[day]['contrato_Replay'],grade_control=is_control,work_reason=op['work_reason'],work_points=op['work_points']))
lookup={(r['date'],r['level']):r for r in resolved};daily=[];unresolved=[]
for day in refs:
 total=D(0);work=D(0);n=0;pending=0;tick=0
 for op in ops:
  if op['date']!=day:continue
  n+=1;work+=dec(op['work_points']) if op['work_points'] else 0
  if (day,op['level']) in lookup:total+=D(lookup[(day,op['level'])]['points']);tick+=1
  elif op['determined']=='True':total+=D(op['min_points'])
  else:pending+=1;unresolved.append((day,op['level']))
 daily.append(dict(date=day,operations=n,resolved_by_candles=n-tick-pending,resolved_by_Replay_window=tick,pending=pending,test_points=str(total) if not pending else 'PENDENTE',work_points=str(work) if day in work_dates else '',difference=(str(total-work) if not pending else 'PENDENTE') if day in work_dates else ''))
daily.sort(key=lambda r:r['date']);total=sum((D(r['test_points']) for r in daily if not r['pending']),D(0));worktotal=sum((D(r['work_points']) for r in daily if r['work_points']!=''),D(0))
assert all(r['resolved'] for r in results if r.get('reason')!='MISSING_REPLAY_WINDOW'),results
summary=dict(status='ABRIL_PARCIAL_AGUARDANDO_REPLAY_09ABR' if unresolved else 'ABRIL_ENCERRADO_M1_REPLAY',workbook_sha256=hashlib.sha256(XLS.read_bytes()).hexdigest(),sheets=sheets,ignored_sheets=ignored_sheets,records=sum(s['records'] for s in sheets),pending_operation_count=len(unresolved),resolved_original_pending=sum(not r['grade_control'] for r in resolved),grade_controls=sum(r['grade_control'] for r in resolved),operations=len(ops),test_points=None if unresolved else str(total),work_points=str(worktotal),difference=None if unresolved else str(total-worktotal),unresolved_operations=unresolved,method='33resultados determinados nos candles+3resolvidos por Replay;nao e mes integral tick a tick. Grade5,niveis,sem custos/fills.',gap_control='Sem lacunas intradiarias nos M1 fornecidos.',results=results)
write('REPLAY_TODAS_ABAS_AUDITORIA.csv',sheets);write('REPLAY_TODAS_ABAS_M1.csv',checks);write('REPLAY_OPERACOES_RESOLVIDAS.csv',resolved);write('DIARIO_APOS_JANELAS.csv',daily)
(OUT/'REPLAY_TODAS_ABAS_RESULTADO.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k!='results'},ensure_ascii=False,indent=2));print('OPERATIONS');print(json.dumps(resolved,ensure_ascii=False,indent=2));print('MINUTE MISMATCHES');print(json.dumps([x for x in checks if not x['ohlc_match'] or not x['quantity_match']],ensure_ascii=False,indent=2))
