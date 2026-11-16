"""Validate only Apr09complement;preserve all ten previously frozen2025months.
No replay of other months. Main worksheet09:20 remains archived,not rewritten.
"""
from pathlib import Path
from decimal import Decimal as D
import csv,json,io,zipfile,hashlib,pickle,shutil,sys,datetime as dt,collections
P=Path(__file__).parent;R=P.parents[1]
sys.path.insert(0,str(R/'entregas/fechamento_agosto_v1_11/analise'))
from motor_precos import levels
SOURCE=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/workspace/dados_brutos_modelo_d/replay_profit/2025_04_09_Complemento_20261116.txt')
def read(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter=';'))
def write(p,rs):
 with p.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rs[0]),delimiter=';',lineterminator='\n');w.writeheader();w.writerows(rs)
def integer(s):
 d=D(s.replace('.','').replace(',','.'));assert d==d.to_integral_value();return int(d)
rows=[]
with SOURCE.open(encoding='utf-8-sig',newline='') as f:
 for n,r in enumerate(csv.reader(f,delimiter='\t'),1):
  if n==1:assert r[:6]==['Data','Compradora','Valor','Quantidade','Vendedora','Agressor'];continue
  if not r or not r[0]:continue
  dt.datetime.strptime(r[0],'%H:%M:%S.%f');p,q=integer(r[2]),integer(r[3]);assert p>0 and q>0
  rows.append(dict(time=r[0],price=p,quantity=q,source_row=n))
assert rows and all(a['time']>=b['time'] for a,b in zip(rows,rows[1:]))
chron=rows[::-1];alt=sorted(rows,key=lambda r:r['time']);day='2025-04-09'
with zipfile.ZipFile(R/'entregas/arquivo_conversa_20261111/originais/ORIGINAIS_PARTE_005.zip') as z:raw=z.read(next(n for n in z.namelist() if n.endswith('/EXPORT110_1794243035_5791.zip')))
assert hashlib.sha256(raw).hexdigest()=='0e4a1cf44e37c4409ea856e8a52f754669819c338b080346ec643fdfbcbb7093'
with zipfile.ZipFile(io.BytesIO(raw)) as z:rawm=z.read(next(n for n in z.namelist() if n.endswith('/M1_202504.csv')))
bars=collections.defaultdict(list);qty={}
for r in csv.DictReader(io.StringIO(rawm.decode('utf-8-sig')),delimiter=';'):
 if r['time'].startswith('2025.04.09'):
  tm=r['time'][11:];bars[day].append((tm,*[D(r[k]) for k in ('open','high','low','close')]));qty[(day,tm)]=int(r['real_volume'])
bars[day].sort();checks=[]
for minute in sorted({r['time'][:5] for r in chron}):
 es=[e for e in chron if e['time'][:5]==minute];b=next(b for b in bars[day] if b[0]==minute);oh=[es[0]['price'],max(e['price'] for e in es),min(e['price'] for e in es),es[-1]['price']];q=sum(e['quantity'] for e in es)
 checks.append(dict(minute=minute,records=len(es),quantity=q,M1_quantity=qty[(day,minute)],OHLC=str(oh),M1_OHLC=str(list(b[1:])),OHLC_match=oh==list(b[1:]),quantity_match=q==qty[(day,minute)]))
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

src=R/'entregas/preparacao_jan_nov_2025_20261115/04_Abril';ref=next(r for r in read(src/'REFERENCIAS.csv') if r['date']==day);lev=next(l for l in levels(ref) if l['name']=='R61.8')
op=next(r for r in read(src/'OPERACOES_POSSIBILIDADES.csv') if r['date']==day and r['level']=='R61.8')
a=resolve(chron,lev,day);b=resolve(alt,lev,day);math=resolve(chron,lev,day,False);mtie=resolve(alt,lev,day,False)
check=next(c for c in checks if c['minute']=='14:20');same=a.get('reason')==b.get('reason') and a.get('points')==b.get('points')
groups=collections.defaultdict(list)
for e in chron:
 if a.get('entry',{}).get('time','')<=e['time']<=a.get('exit',{}).get('time',''):groups[e['time']].append(e['price'])
mixed=[tm for tm,prices in groups.items() if min(prices)<=min(lev['tp5'],lev['sl5']) and max(prices)>=max(lev['tp5'],lev['sl5'])]
valid=same and not mixed and check['OHLC_match'] and check['quantity_match'] and a['reason'] in ('TP','SL','CORTE')
case=dict(date=day,level='R61.8',contract='WINJ25',sheet='TXT_COMPLEMENTO09ABR',required_minute='14:20',grade_control=False,primary=a,tie_control=b,tie_invariant=same,mathematical=math,mathematical_tie_invariant=math.get('reason')==mtie.get('reason') and math.get('points')==mtie.get('points'),mathematical_levels={k:str(lev[k]) for k in ('entry','tp','sl')},minute_check=check,partial_prefix_invariance_proof=None,timestamps_conditional_on_no_earlier_entry=False,mixed_barrier_ms=mixed,resolved=bool(valid))
cache=Path('/workspace/work/lote2025/cache/complemento09abr.pickle');cache.write_bytes(pickle.dumps([(e['time'],e['price'],e['quantity'],e['source_row']) for e in rows],protocol=4))
dest=Path('/workspace/dados_brutos_modelo_d/replay_profit/2025_04_09_Complemento_20261116.txt');dest.parent.mkdir(parents=True,exist_ok=True)
if SOURCE.resolve()!=dest.resolve():shutil.copy2(SOURCE,dest)
sha=hashlib.sha256(dest.read_bytes()).hexdigest();assert sha==hashlib.sha256(SOURCE.read_bytes()).hexdigest()
audit=dict(date=day,contract='WINJ25',sheet='TXT_COMPLEMENTO09ABR',index='TXT09ABR',cache=str(cache),source_raw=str(dest),source_sha256=sha,raw_published=False,records=len(rows),start=chron[0]['time'],end=chron[-1]['time'],at_limit_200001=len(rows)>=200001,checks=checks,case=case,original_worksheet='ABR09-04-25 09:20 retained;no temporal overlap with this14:20complement',no_deduplication=True)
(P/'COMPLEMENTO_09ABR.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
selected=json.loads((P/'INVENTARIO_FONTES_EM_USO.json').read_text());selected=[audit if x['date']==day and x['sheet'] in ('ABR 09-04-25','TXT_COMPLEMENTO09ABR') else x for x in selected];(P/'INVENTARIO_FONTES_EM_USO.json').write_text(json.dumps(selected,ensure_ascii=False,indent=2)+'\n')
assert valid,audit
current_checks=read(P/'MINUTOS_TODAS_ABAS.csv');current_checks=[c for c in current_checks if c['sheet']!='TXT_COMPLEMENTO09ABR']
for ck in checks:
 current_checks.append(dict(sheet='TXT_COMPLEMENTO09ABR',date=day,**ck,interior=chron[0]['time'][:5]<ck['minute']<chron[-1]['time'][:5]))
write(P/'MINUTOS_TODAS_ABAS.csv',current_checks)
assert (a['reason'],D(a['points'])) in [(r.split(':')[0],D(r.split(':')[1])) for r in op['outcomes'].split('|')]
assert a['entry']['time'][:5]=='14:20'
# Snapshot tenclosedmonths and partialApril BEFORE making the new result concrete.
h=P/'historico_antes_09abr';h.mkdir(exist_ok=True)
closed=[]
for folder in sorted(P.iterdir()):
 if folder.is_dir() and folder.name[:2].isdigit() and folder.name[:2]!='04':
  for name in ['RESULTADO_FINAL.json','OPERACOES_FINAIS.csv','DIARIO_APOS_REPLAY.csv','LEIA_RESULTADO.txt','PROGRESSO_RESOLUCAO.json']:
   f=folder/name
   if f.exists():closed.append(dict(path=str(f.relative_to(R)),sha256=hashlib.sha256(f.read_bytes()).hexdigest()))
if not(h/'HASHES_MESES_FECHADOS.json').exists():(h/'HASHES_MESES_FECHADOS.json').write_text(json.dumps(closed,indent=2)+'\n')
for name in ['RESULTADO_CONSOLIDADO.json','RESULTADOS_TODOS_MESES.json','PENDENCIAS.json','COMPLEMENTO_PENDENTE.csv','RESUMO_MENSAL.csv','CURVA_M1_REPLAY_2025_01_03.csv','CURVA_M1_REPLAY_2025_05_2026_07.csv','CURVA_COMPARAVEL_WORK_2025_01_03.csv','CURVA_COMPARAVEL_WORK_2025_05_2026_07.csv']:
 f=P/name
 if f.exists() and not(h/name).exists():shutil.copy2(f,h/name)
folder=P/'04_Abril';partial=h/'04_Abril';partial.mkdir(exist_ok=True)
for f in folder.iterdir():
 if f.is_file() and not(partial/f.name).exists():shutil.copy2(f,partial/f.name)
allmonths=json.loads((P/'RESULTADOS_TODOS_MESES.json').read_text());s=next(s for s in allmonths if s['month']=='2025-04')
if s.get('closed') or s.get('pending')==0:
 assert s['principal'] is not None and next(r for r in s['results'] if r['date']==day)['primary']==case['primary'];print('Already validated',json.dumps(audit,indent=2));raise SystemExit
before=[r for r in s['results'] if not(r['date']==day and r['level']=='R61.8')]
s['results']=before+[case];s['results'].sort(key=lambda r:(r['date'],r['level']));s.update(pending=0,resolved_original_pending=6,status='REPLAY_RESOLVIDO_AGUARDA_CONFERENCIA_FINAL',unresolved=[],April_complement='COMPLEMENTO_09ABR.json')
ops=read(folder/'OPERACOES_APOS_REPLAY.csv');row=next(o for o in ops if o['date']==day and o['level']=='R61.8');assert row['reason']=='PENDENTE';row.update(reason=a['reason'],points=a['points'],basis=a['exit_source'],entry=a['entry']['time'],exit=a['exit']['time'])
daily=read(folder/'DIARIO_APOS_REPLAY.csv');dr=next(d for d in daily if d['date']==day);rr=[o for o in ops if o['date']==day];assert all(o['points']!='' for o in rr);total=sum(D(o['points']) for o in rr);work=D(dr['work_points']);dr.update(pending='0',test_points=format(total.normalize(),'f'),difference=format((total-work).normalize(),'f'))
s['principal']=format(sum(D(d['test_points']) for d in daily).normalize(),'f')
write(folder/'OPERACOES_APOS_REPLAY.csv',ops);write(folder/'DIARIO_APOS_REPLAY.csv',daily)
(folder/'RESULTADO_RECEBIMENTO.json').write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n');(P/'RESULTADOS_TODOS_MESES.json').write_text(json.dumps(allmonths,ensure_ascii=False,indent=2)+'\n');(P/'PENDENCIAS.json').write_text('[]\n')
print(json.dumps(dict(audit=audit,April_points=s['principal']),ensure_ascii=False,indent=2))
