"""Audit only accessible21Augtext. Main workbook not transferred (>32MiB).
No fabricated records in auction gaps,no deduplication,no monthly close.
"""
from pathlib import Path
from decimal import Decimal as D
import csv,io,json,zipfile,collections,hashlib,shutil,sys,datetime as dt
P=Path(__file__).parent;R=P.parents[1]
sys.path.insert(0,str(R/'entregas/fechamento_agosto_v1_11/analise'))
from motor_precos import levels
SOURCE=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/workspace/dados_brutos_modelo_d/replay_profit/2025_08_21_Texto_Recebimento01.txt')
def read(p):
 with p.open(encoding='utf-8-sig') as f:return list(csv.DictReader(f,delimiter=';'))
def write(name,rs):
 with (P/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rs[0]),delimiter=';',lineterminator='\n');w.writeheader();w.writerows(rs)
def integer(s):
 d=D(s.replace('.','').replace(',','.'));assert d==d.to_integral_value();return int(d)
rows=[]
with SOURCE.open(encoding='utf-8-sig',newline='') as f:
 for ordinal,r in enumerate(csv.reader(f,delimiter='\t'),1):
  if ordinal==1:assert r[:6]==['Data','Compradora','Valor','Quantidade','Vendedora','Agressor'];continue
  if not r or not r[0]:continue
  dt.datetime.strptime(r[0],'%H:%M:%S.%f');p,q=integer(r[2]),integer(r[3]);assert p>0 and q>0
  rows.append(dict(time=r[0],price=p,quantity=q,source_row=ordinal))
assert all(a['time']>=b['time'] for a,b in zip(rows,rows[1:]))
chron=rows[::-1];alternate=sorted(rows,key=lambda r:r['time'])
arc=R/'entregas/arquivo_conversa_20261111/originais/ORIGINAIS_PARTE_005.zip'
with zipfile.ZipFile(arc) as z:raw=z.read(next(n for n in z.namelist() if n.endswith('/EXPORT110_1794243035_5791.zip')))
assert hashlib.sha256(raw).hexdigest()=='0e4a1cf44e37c4409ea856e8a52f754669819c338b080346ec643fdfbcbb7093'
with zipfile.ZipFile(io.BytesIO(raw)) as z:rawm=z.read(next(n for n in z.namelist() if n.endswith('/M1_202508.csv')))
m1={r['time'][11:]:r for r in csv.DictReader(io.StringIO(rawm.decode('utf-8-sig')),delimiter=';') if r['time'].startswith('2025.08.21')}
checks=[]
for minute in sorted({r['time'][:5] for r in chron}):
 es=[e for e in chron if e['time'][:5]==minute];ref=m1.get(minute);oh=[es[0]['price'],max(e['price'] for e in es),min(e['price'] for e in es),es[-1]['price']];q=sum(e['quantity'] for e in es)
 checks.append(dict(minute=minute,records=len(es),OHLC=str(oh),quantity=q,M1_OHLC=str([D(ref[k]) for k in ('open','high','low','close')]) if ref else '',M1_quantity=int(ref['real_volume']) if ref else '',OHLC_match=bool(ref and oh==[D(ref[k]) for k in ('open','high','low','close')]),quantity_match=bool(ref and q==int(ref['real_volume'])),interior_minute=chron[0]['time'][:5]<minute<chron[-1]['time'][:5]))
gaps=[]
for a,b in zip(chron,chron[1:]):
 t1=dt.datetime.strptime(a['time'],'%H:%M:%S.%f');t2=dt.datetime.strptime(b['time'],'%H:%M:%S.%f')
 if t2-t1>dt.timedelta(minutes=1):gaps.append(dict(last_trade=a['time'],next_trade=b['time'],next_price=b['price'],elapsed_seconds=(t2-t1).total_seconds(),user_explanation='LEILAO_REPORTADO_PELO_USUARIO'))
ref=next(r for r in read(R/'entregas/preparacao_jan_nov_2025_20261115/08_Agosto/REFERENCIAS.csv') if r['date']=='2025-08-21')
ls=levels(ref);lev=next(l for l in ls if l['name']=='S61.8')
prior=next(r for r in read(R/'entregas/preparacao_jan_nov_2025_20261115/08_Agosto/OPERACOES_POSSIBILIDADES.csv') if r['date']=='2025-08-21' and r['level']=='S61.8')
assert prior['entry_minute']=='09:03' and prior['exit_candidates']=='TP@2025-08-21T10:26:00'
def finish(es):
 for e in es:
  if D(e['price'])<=lev['sl5'] or D(e['price'])>=lev['tp5']:
   reason='SL' if D(e['price'])<=lev['sl5'] else 'TP';return dict(reason=reason,points=str((lev['tp5'] if reason=='TP' else lev['sl5'])-lev['entry5']),exit_time=e['time'],observed_price=e['price'],source_row=e['source_row'])
 return dict(reason='OPEN')
a=finish(chron);b=finish(alternate);assert a['reason']==b['reason'] and a['points']==b['points']
# Coverage begins well before the first missing interval; entire interior minutes
# including reopen print must match the supplied source to approve this control.
interior=[c for c in checks if c['interior_minute']];coverage=all(c['OHLC_match'] and c['quantity_match'] for c in interior)
exitcheck=next(c for c in checks if c['minute']==a['exit_time'][:5]);assert exitcheck['OHLC_match'] and exitcheck['quantity_match']
print('MINUTE_MISMATCHES',json.dumps([c for c in interior if not c['OHLC_match'] or not c['quantity_match']],ensure_ascii=False,indent=2))
assert all(c['OHLC_match'] for c in interior)
assert [(c['minute'],c['quantity']-c['M1_quantity']) for c in interior if not c['quantity_match']]==[('09:16',-1)]
assert min(e['price'] for e in chron)>lev['sl5']
assert max(D(r['high']) for r in m1.values())==max(e['price'] for e in chron)
eligible=[]
for l in ls:
 if l['eligible'] and not l['buy']:
  eligible.append(dict(level=l['name'],entry=str(l['entry5']),max_copy=max(e['price'] for e in chron),entry_hit_in_copy=max(e['price'] for e in chron)>=l['entry5']))
rawdest=Path('/workspace/dados_brutos_modelo_d/replay_profit/2025_08_21_Texto_Recebimento01.txt');rawdest.parent.mkdir(parents=True,exist_ok=True)
if SOURCE.resolve()!=rawdest.resolve():shutil.copy2(SOURCE,rawdest)
assert hashlib.sha256(rawdest.read_bytes()).hexdigest()==hashlib.sha256(SOURCE.read_bytes()).hexdigest()
s=dict(status='CONTROLE_COBERTURA_21AGO_CONFERIDO_MES_AINDA_PENDENTE',date='2025-08-21',contract='WINV25',records=len(rows),observed_limit_200001=len(rows)==200001,start=chron[0]['time'],end=chron[-1]['time'],opening_windows_0901_0903_in_this_text=False,raw_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),preserved_raw=str(rawdest),raw_published=False,matched_interior_minutes=sum(c['OHLC_match'] and c['quantity_match'] for c in interior),interior_quantity_discrepancies=[c for c in interior if not c['quantity_match']],all_interior_prices_match=all(c['OHLC_match'] for c in interior),minute_checks=checks,gaps=gaps,S61_8=dict(entry_source='M1_PREVIAMENTE_DETERMINADO_09:03_ANTES_DA_COPIA',entry=str(lev['entry5']),tp=str(lev['tp5']),sl=str(lev['sl5']),primary=a,tie_control=b,coverage_resolved=True,coverage_note='Price control confirmed with user-reported auction explanation;quantity09:16 differs by1,not certified perfect tape.'),eligible_sells=eligible,main_workbook_status='DOWNLOAD_REJECTED_OVER32MiB_NO_CONTENT_INSPECTED',monthly_principal=None,monthly_DD=None,limitation='Text starts09:09 and has200001records:earlier records truncated;do not use for09:01/09:02 entries. All10interiorOHLC match;9quantities match and09:16 differs by1. Exit minute matches OHLC/quantity. This validates the price control with retained quantitative remark,not a perfect full-day tape. Auction labels are user explanation,not official event flags in this layout.')
write('21AGO_MINUTOS_CONFERIDOS.csv',checks);write('21AGO_INTERVALOS_SEM_NEGOCIOS_NA_COPIA.csv',gaps)
(P/'AUDITORIA_TEXTO_21AGO.json').write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in s.items() if k!='minute_checks'},ensure_ascii=False,indent=2))
