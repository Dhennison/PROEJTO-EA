"""February D: restore archived originals, audit M1 against Work M5, branch chronology.
No invented tick paths, no change to frozen months. Reproducible from repository archives.
"""
from pathlib import Path
import csv,io,json,zipfile,hashlib,sys,datetime as dt,collections
from decimal import Decimal as D
ROOT=Path(__file__).resolve().parents[2];P=Path(__file__).parent
sys.path.insert(0,str(ROOT/'entregas/fechamento_agosto_v1_11/analise'))
from motor_precos import levels
sys.path.insert(0,str(ROOT/'entregas/profit_marco_20261113'))
from analisar_marco import choices

def read(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter=';'))
def write(name,rs):
 if not rs:return
 with (P/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rs[0]),delimiter=';',lineterminator='\n');w.writeheader();w.writerows(rs)
def dec(v):return D(v.replace(',','.'))
def digest(b):return hashlib.sha256(b).hexdigest()
archive=ROOT/'entregas/arquivo_conversa_20261111/originais/ORIGINAIS_PARTE_005.zip'
with zipfile.ZipFile(archive) as z:
 n=next(n for n in z.namelist() if n.endswith('/EXPORT110_1794243035_5791.zip'));raw=z.read(n)
assert digest(raw)=='0e4a1cf44e37c4409ea856e8a52f754669819c338b080346ec643fdfbcbb7093'
with zipfile.ZipFile(io.BytesIO(raw)) as z:
 files={Path(n).name:z.read(n) for n in z.namelist() if not n.endswith('/')}
 print(files['ESPECIFICACAO.txt'].decode('utf-8-sig'))
 status=list(csv.DictReader(io.StringIO(files['STATUS.csv'].decode('utf-8-sig')),delimiter=';'))
 for r in status:
  if '2026.02.01' in str(r):print('FEB STATUS',r)
 feb_status=next(r for r in status if r['file']=='M1_202602.csv')
 assert feb_status['state']=='EXPORTADO_ESTAVEL' and feb_status['attempts']=='2' and feb_status['error']=='0' and feb_status['rows']=='9930'
 m1=collections.defaultdict(list)
 for name in ('M1_202601.csv','M1_202602.csv'):
  for r in csv.DictReader(io.StringIO(files[name].decode('utf-8-sig')),delimiter=';'):
   t=dt.datetime.strptime(r['time'],'%Y.%m.%d %H:%M');m1[t.date()].append((t,*[D(r[k]) for k in ('open','high','low','close')],int(r['real_volume'])))
arc5=ROOT/'entregas/historico_work_modelo_d_20261105/replay_setembro_20261106/originais/Candles_Originais_Modelo_D_2023_2026.zip'
with zipfile.ZipFile(arc5) as z:raw5=z.read('WINFUT_F_0_5min_01-01-2026_28-02-2026.csv')
m5=collections.defaultdict(list)
for r in csv.reader(io.StringIO(raw5.decode('cp1252')),delimiter=';'):
 if r[0]=='Ativo':continue
 t=dt.datetime.strptime(r[1]+' '+r[2],'%d/%m/%Y %H:%M:%S');m5[t.date()].append((t,*[D(v.replace('.','').replace(',','.')) for v in r[3:7]],int(r[8].replace('.',''))))
for series in (m1,m5):
 for bs in series.values():bs.sort()
refroot=ROOT/'entregas/historico_work_modelo_d_20261105'
adj={r['DataOperacional']:r for r in read(refroot/'Ajustes_Diarios_Modelo_D_20230301_20260921.csv')}
work=[r for r in read(refroot/'Operacoes_Modelo_D_20230301_20260921_ORIGINAL.csv') if r['Data'].startswith('2026-02')];wi={(r['Data'],r['Nível']):r for r in work}
workdaily={r['Data']:r for r in read(refroot/'Referencia_D_diário.csv') if r['Data'].startswith('2026-02')}
def agg(bs):return bs[0][1],max(b[2] for b in bs),min(b[3] for b in bs),bs[-1][4]
checks=[];coverage=[];gaps=[]
for day in sorted(d for d in m5 if d.month==2 or d==dt.date(2026,1,30)):
 aa=m1[day];bb=m5[day];assert aa and len({b[0] for b in aa})==len(aa)
 assert agg(aa)==agg(bb),(day,agg(aa),agg(bb))
 for b1,b2 in zip(aa,aa[1:]):
  if b2[0]-b1[0]!=dt.timedelta(minutes=1):gaps.append(dict(date=str(day),before=str(b1[0]),after=str(b2[0])))
 for b in bb:
  rr=[a for a in aa if b[0]<=a[0]<b[0]+dt.timedelta(minutes=5)]
  ck=dict(date=str(day),minute=b[0].strftime('%H:%M'),M1_count=len(rr),OHLC_match=agg(rr)==b[1:5] if rr else False,quantity_match=sum(a[5] for a in rr)==b[5])
  checks.append(ck)
 coverage.append(dict(date=str(day),M1=len(aa),M5=len(bb),first=str(aa[0][0]),last=str(aa[-1][0]),daily_OHLC_match=True,adjustment=adj[str(day)]['Ajuste'] if str(day) in adj else ''))
assert not gaps
# Timestamps are local source labels, not converted to UTC.
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
ops=[];refs=[];gran=[];asks=[];mathdiff=[];missing=[]
for day in sorted(d for d in m5 if d.month==2):
 prior=max(d for d in m5 if d<day);pb=m5[prior];bs=m5[day];a=dec(adj[str(day)]['Ajuste'])
 ref=dict(open=str(bs[0][1]),high_prev=str(max(b[2] for b in pb)),low_prev=str(min(b[3] for b in pb)),close_prev=str(pb[-1][4]),adjustment=str(a))
 # Work rolling context preserved, including previous contract day at expiry.
 contract='WING26' if day<dt.date(2026,2,18) else 'WINJ26'
 refs.append(dict(date=str(day),previous=str(prior),previous_source='WORK_M5_FULL_CROSSCHECK_M1',previous_first=str(pb[0][0]),previous_last=str(pb[-1][0]),previous_bars=len(pb),**ref,contrato_Replay=contract,contract_status='CALENDARIO_E_CONVENCAO_WORK;CONFERIR_PRECOS_NA_COPIA'))
 for lev in levels(ref):
  if not lev['eligible']:continue
  a1=branch(m1[day],lev,True);a5=branch(bs,lev,True);am=branch(m1[day],lev,False);am5=branch(bs,lev,False)
  assert bool(a1)==bool(a5)
  if a1 is None:continue
  assert set(a1['outcomes'].split('|'))<=set(a5['outcomes'].split('|')),(day,lev['name'],'M1 must refine M5')
  assert set(am['outcomes'].split('|'))<=set(am5['outcomes'].split('|')),(day,lev['name'],'Mathematical refinement')
  wr=wi.get((str(day),lev['name']))
  if wr:
   for k,wk in [('entry','Entrada'),('sl','Stop'),('tp','Alvo')]:
    if abs(lev[k]-dec(wr[wk]))>D('.00001'):mathdiff.append(dict(date=str(day),level=lev['name'],field=k,ours=str(lev[k]),work=wr[wk]))
  op=dict(date=str(day),level=lev['name'],contract=contract,entry=str(lev['entry5']),tp=str(lev['tp5']),sl=str(lev['sl5']),**{k:v for k,v in a1.items() if k!='asks'},work_reason=wr['Motivo'] if wr else '',work_points=wr['Pontos'] if wr else '')
  ops.append(op)
  gran.append(dict(date=str(day),level=lev['name'],M5_entry=a5['entry_minute'],M1_entry=a1['entry_minute'],M5_grid_outcomes=a5['outcomes'],M1_grid_outcomes=a1['outcomes'],M5_math_outcomes=am5['outcomes'] if am5 else 'NO_ENTRY',M1_math_outcomes=am['outcomes'] if am else 'NO_ENTRY',resolved_by_M1=a1['determined'] and not a5['determined'],still_sequence_ambiguous=not a1['determined'],work_reason=op['work_reason']))
  assert set(x.split(':')[0] for x in am['outcomes'].split('|'))==set(x.split(':')[0] for x in a1['outcomes'].split('|')),(day,lev['name'],'Review grade-specific window')
  if not a1['determined']:
   for ask in a1['asks']:asks.append(dict(date=str(day),level=lev['name'],contract=contract,reason='SEQUENCIA_M1',**ask))
  elif wr and ('ALVO' if a1['outcomes'].startswith('TP:') else 'STOP' if a1['outcomes'].startswith('SL:') else 'ZERAGEM 18H')!=wr['Motivo']:
   # Distinguish M1-granularity resolution from actual grade-dependent classification.
   # Compare reasons instead of numeric rounding alone.
   math_reasons=set(x.split(':')[0] for x in am['outcomes'].split('|')) if am else {'NO_ENTRY'}
   grid_reason=a1['outcomes'].split(':')[0]
   if grid_reason not in math_reasons or len(math_reasons)>1:
    minute=a1['exit_candidates'].split('|')[0].split('@',1)[1][11:16]
    asks.append(dict(date=str(day),level=lev['name'],contract=contract,reason='CONTROLE_GRADE5',minute=minute,phase='CONTROLE_SAIDA',choices=a1['outcomes']))
missing=sorted(set(wi)-{(r['date'],r['level']) for r in ops});extra=sorted({(r['date'],r['level']) for r in ops}-set(wi))
write('INVENTARIO_POR_DATA.csv',coverage);write('CONFERENCIA_M1_AGREGADO_M5.csv',checks);write('REFERENCIAS_FEVEREIRO.csv',refs);write('OPERACOES_POSSIBILIDADES.csv',ops);write('GRANULARIDADE_M5_VS_M1.csv',gran);write('JANELAS_REPLAY.csv',asks)
daily=[]
for day in sorted(workdaily):
 rr=[r for r in ops if r['date']==day]
 daily.append(dict(date=day,operations=len(rr),determined=sum(r['determined'] for r in rr),pending=sum(not r['determined'] for r in rr),test_points='AGUARDANDO_REPLAY',work_points=workdaily[day]['Pontos'],difference='AGUARDANDO_REPLAY'))
write('DIARIO_PROVISORIO.csv',daily)
summary=dict(status='FEVEREIRO_ANALISADO_AGUARDANDO_REPLAY',days=len(refs),operations=len(ops),determined=sum(o['determined'] for o in ops),pending=sum(not o['determined'] for o in ops),grade_controls=sum(a['reason']=='CONTROLE_GRADE5' for a in asks),work_points=str(sum(dec(r['Pontos']) for r in work)),work_operations=len(work),mathematical_differences=mathdiff,work_missing=missing,work_extra=extra,M1_February_bars=sum(len(bs) for day,bs in m1.items() if day.month==2),M5_February_bars=sum(len(bs) for day,bs in m5.items() if day.month==2),M5_buckets_checked=len(checks),M5_OHLC_mismatches=[c for c in checks if not c['OHLC_match']],M5_quantity_mismatches=[c for c in checks if not c['quantity_match']],intraday_M1_gaps=gaps,M5_pending=sum('|' in g['M5_grid_outcomes'] for g in gran),resolved_by_granularity=sum(g['resolved_by_M1'] for g in gran),raw_hashes={'EXPORT110_1794243035_5791.zip':digest(raw),'M1_202602.csv':digest(files['M1_202602.csv']),'M1_202601.csv':digest(files['M1_202601.csv']),'Work_M5.csv':digest(raw5)},first_day_context=refs[0],principal='AGUARDANDO_REPLAY;nao somar subtotais nem inserir fevereiro no DD',source='M1 nativo MT5 WIN$N;referencia Work Profit M5;ajustes Work preservados;Replay futuro por contrato real. Sem fita integral ou fills certificados.')
evidence=[]
for g in gran:
 if not g['resolved_by_M1']:continue
 op=next(o for o in ops if (o['date'],o['level'])==(g['date'],g['level']))
 end=max(x.split('@')[1][11:16] for x in op['exit_candidates'].split('|'))
 for b in m1[dt.date.fromisoformat(g['date'])]:
  minute=b[0].strftime('%H:%M')
  if g['M5_entry']<=minute<=max(end,(dt.datetime.strptime(g['M5_entry'],'%H:%M')+dt.timedelta(minutes=4)).strftime('%H:%M')):
   evidence.append(dict(date=g['date'],level=g['level'],minute=minute,open=str(b[1]),high=str(b[2]),low=str(b[3]),close=str(b[4]),entry=op['entry'],tp=op['tp'],sl=op['sl'],entry_minute=op['entry_minute'],exit_candidates=op['exit_candidates'],outcome=op['outcomes'],after_certain_exit=minute>end))
write('EVIDENCIA_CINCO_RESOLUCOES_M1.csv',evidence)
(P/'RESULTADO_PROVISORIO.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False,indent=2));print('JANELAS',json.dumps(asks,ensure_ascii=False,indent=2))
assert not mathdiff and not missing and not extra
assert len(refs)==18 and all(c['OHLC_match'] and c['quantity_match'] for c in checks)
