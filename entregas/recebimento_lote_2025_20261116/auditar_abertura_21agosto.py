"""Audit accessible21Augopening text;do not close August from a partial copy."""
from pathlib import Path
from decimal import Decimal as D
import csv,io,json,hashlib,zipfile,sys,collections,datetime as dt,shutil
P=Path(__file__).parent;R=P.parents[1]
sys.path.insert(0,str(R/'entregas/fechamento_agosto_v1_11/analise'))
from motor_precos import levels
SOURCE=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/workspace/dados_brutos_modelo_d/replay_profit/2025_08_21_Abertura_Recebimento02.txt')
def read(p):
 with p.open(encoding='utf-8-sig') as f:return list(csv.DictReader(f,delimiter=';'))
def number(s):return int(s.replace('.',''))
es=[]
with SOURCE.open(encoding='utf-8-sig',newline='') as f:
 for n,r in enumerate(csv.reader(f,delimiter='\t'),1):
  if n==1:continue
  if r and r[0]:es.append(dict(time=r[0],price=number(r[2]),quantity=number(r[3]),source_row=n))
assert all(a['time']>=b['time'] for a,b in zip(es,es[1:]))
chron=es[::-1];alt=sorted(es,key=lambda x:x['time'])
with zipfile.ZipFile(R/'entregas/arquivo_conversa_20261111/originais/ORIGINAIS_PARTE_005.zip') as z:raw=z.read(next(n for n in z.namelist() if n.endswith('/EXPORT110_1794243035_5791.zip')))
assert hashlib.sha256(raw).hexdigest()=='0e4a1cf44e37c4409ea856e8a52f754669819c338b080346ec643fdfbcbb7093'
with zipfile.ZipFile(io.BytesIO(raw)) as z:m=z.read(next(n for n in z.namelist() if n.endswith('/M1_202508.csv')))
bars=collections.defaultdict(list);qty={}
for r in csv.DictReader(io.StringIO(m.decode('utf-8-sig')),delimiter=';'):
 if r['time'].startswith('2025.08.21'):
  minute=r['time'][11:];bars['2025-08-21'].append((minute,*[D(r[k]) for k in ('open','high','low','close')]));qty[('2025-08-21',minute)]=int(r['real_volume'])
bars['2025-08-21'].sort();checks=[]
for minute in sorted({e['time'][:5] for e in chron}):
 rr=[e for e in chron if e['time'][:5]==minute];b=next(b for b in bars['2025-08-21'] if b[0]==minute);oh=[rr[0]['price'],max(e['price'] for e in rr),min(e['price'] for e in rr),rr[-1]['price']];q=sum(e['quantity'] for e in rr)
 checks.append(dict(minute=minute,records=len(rr),OHLC=str(oh),quantity=q,M1_OHLC=str(list(b[1:])),M1_quantity=qty[('2025-08-21',minute)],OHLC_match=oh==list(b[1:]),quantity_match=q==qty[('2025-08-21',minute)]))
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

ref=next(r for r in read(R/'entregas/preparacao_jan_nov_2025_20261115/08_Agosto/REFERENCIAS.csv') if r['date']=='2025-08-21')
ls=levels(ref);results=[]
for level in ['S38.2','S50']:
 lev=next(l for l in ls if l['name']==level);primary=resolve(chron,lev,'2025-08-21');tie=resolve(alt,lev,'2025-08-21');math=resolve(chron,lev,'2025-08-21',False)
 required=next(c for c in checks if c['minute']==('09:01' if level=='S38.2' else '09:02'))
 same=primary.get('reason')==tie.get('reason') and primary.get('points')==tie.get('points')
 valid=required['OHLC_match'] and required['quantity_match'] and same and primary['reason'] in ('TP','SL','CORTE')
 results.append(dict(level=level,primary=primary,tie_control=tie,mathematical=math,resolved=valid,tie_invariant=same,required_minute=required))
assert results[0]['resolved'] and results[0]['primary']['reason']=='SL' and results[0]['primary']['points']=='-375'
assert not results[1]['resolved'] and results[1]['primary']['reason']=='INCOMPLETE_ENTRY_MINUTE'
dest=Path('/workspace/dados_brutos_modelo_d/replay_profit/2025_08_21_Abertura_Recebimento02.txt')
if SOURCE.resolve()!=dest.resolve():shutil.copy2(SOURCE,dest)
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==hashlib.sha256(dest.read_bytes()).hexdigest()
summary=dict(status='21AGO_S38_RESOLVIDO_S50_PENDENTE_PLANILHA',date='2025-08-21',contract='WINV25',records=len(chron),start=chron[0]['time'],end=chron[-1]['time'],records_at_200001_limit=False,minute_checks=checks,results=results,raw_preserved=str(dest),raw_sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),raw_published=False,monthly_principal=None,monthly_DD=None,no_extra_copy_requested='Remaining09:02may be in main workbook;await GitHubasset instead of requesting duplicate Replay.')
(P/'AUDITORIA_ABERTURA_21AGO.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False,indent=2))
