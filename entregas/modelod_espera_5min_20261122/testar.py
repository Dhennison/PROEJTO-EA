from pathlib import Path
import csv,pickle,json,collections,itertools,re,datetime
import numpy as np
P=Path(__file__).parent;R=P.parents[1];E=R/'entregas';C=Path('/workspace/work/modelod_espera_5min_20261122');C.mkdir(exist_ok=True)
base=pickle.load(open('/workspace/work/novos_niveis_20261119/resultados.pickle','rb'));data=base['data'];days=data['days'];di={d:i for i,d in enumerate(days)};ops={(r['date'],r['level']):r for r in data['ops']};levels=['R38.2','R61.8','S38.2','S50','S61.8'];symbols={r['date']:r['contract'] for r in base['alllevels'] if r['level']=='S23.6'}
source_paths=[]
def read(p):
 source_paths.append(str(p.relative_to(R)));return list(csv.DictReader(p.open(encoding='utf-8-sig'),delimiter=';'))
def write(name,rs):
 if not rs:return
 with (P/name).open('w',encoding='utf-8-sig',newline='') as f:
  keys=list(dict.fromkeys(k for r in rs for k in r));w=csv.DictWriter(f,fieldnames=keys,delimiter=';');w.writeheader();w.writerows(rs)
def minute(t):return int(t[:2])*60+int(t[3:5])
def ms(t):
 t=t.split(' ')[-1].split('T')[-1];h,m,s=t.split(':');s,_,f=s.partition('.');return int(h)*3600000+int(m)*60000+int(s)*1000+int((f+'000')[:3])
def fmt(t):return f'{t//3600000:02d}:{t//60000%60:02d}:{t//1000%60:02d}.{t%1000:03d}'
def mm(t):return f'{t//60:02d}:{t%60:02d}'
def exact(s):
 match=re.fullmatch(r'(?:\d{4}[.-]\d{2}[.-]\d{2}[ T])?(\d{2}:\d{2}:\d{2}\.\d{3})',s or '')
 return ms(match[1]) if match else None
first_open={};open_source={};first_touch={};touch_source={}
for r in read(E/'cedro_extrator_win_v1_00/retorno_geral_20261112/CONTRATOS.csv'):
 d=r['dia'][:4]+'-'+r['dia'][4:6]+'-'+r['dia'][6:]
 if d in symbols and r['ativo']==symbols[d]:first_open[d]=ms(r['primeiro_timestamp_na_ordem']);open_source[d]='CEDRO_FIRST_BUSINESS_RECEIPT'
def record(d,l,v,source):
 if v is None or (d,l) not in ops:return
 assert v//60000==minute(ops[(d,l)]['entry_minute']),(d,l,v,ops[(d,l)])
 if (d,l) in first_touch:assert first_touch[d,l]==v,(d,l,first_touch[d,l],v,source)
 first_touch[d,l]=v;touch_source[d,l]=source
for folder in ['validacao_replay_2024_20261117','validacao_lote_2025_20261116']:
 for f in (E/folder).glob('*/OPERACOES_FINAIS.csv'):
  for r in read(f):record(r['date'],r['level'],exact(r.get('entry','')),str(f.relative_to(R)))
for folder in ['profit_dezembro_2025_20261115','profit_janeiro_20261115','profit_fevereiro_20261114','profit_marco_20261113','profit_abril_20261113','profit_maio_20261113','profit_junho_20261113']:
 f=E/folder/'OPERACOES_FINAIS.csv'
 for r in read(f):record(r['date'],r['level'],exact(r.get('entry','')),str(f.relative_to(R)))
for r in read(E/'profit_winq26_julho_20261113/REPLAY_OPERACOES_RESOLVIDAS.csv'):record(r['date'],r['level'],exact(r.get('entry_time','')),'JULY_VALIDATED_REPLAY')
for mo,sub in [('agosto','resultado'),('setembro','resultado'),('outubro','resultado_mensal')]:
 f=E/f'cedro_modelod_{mo}_2026'/sub/'TODOS_NIVEIS.csv'
 for r in read(f):
  if r['estado']=='ENCERRADA':record(r['data'],r['nivel'],exact(r.get('hora_entrada','')),str(f.relative_to(R)))
replay=dict(data['replay']);replay.update(pickle.load(open('/workspace/work/replay_s23_20261119/auditoria.pickle','rb'))['accepted'])
for d in days:
 tm=data['bars'][d][0][0][:5];assert data['bars'][d][0][1]==int(float(base['refs'][d]['open']))
 if (d,tm) in replay:
  es=replay[d,tm];v=ms(es[0][0])
  if d in first_open:assert first_open[d]==v
  first_open[d]=v;open_source[d]='VALIDATED_COMPLETE_OPENING_MINUTE_REPLAY'
for (d,l),o in ops.items():
 key=(d,o['entry_minute'])
 if key in replay:
  es=[e for e in replay[key] if (e[1]<=o['entry'] if o['buy'] else e[1]>=o['entry'])];assert es;record(d,l,ms(es[0][0]),'VALIDATED_COMPLETE_ENTRY_MINUTE_REPLAY')
# Exact entry at an opening-price touch also exposes the first business timestamp.
for (d,l),v in first_touch.items():
 o=ops[d,l];bar=data['bars'][d][0];price=bar[1]
 if v//60000==minute(bar[0]) and (price<=o['entry'] if o['buy'] else price>=o['entry']):
  if d in first_open:assert first_open[d]==v
  first_open[d]=v;open_source[d]='VERIFIED_ORIGINAL_ENTRY_AT_FIRST_OPENING_PRICE'
gates={};diagnostic=[]
for (d,l),o in sorted(ops.items()):
 first=data['bars'][d][0];fm=minute(first[0]);olo=first_open.get(d,fm*60000);ohi=first_open.get(d,fm*60000+59999);assert fm*60000<=olo<=ohi<(fm+1)*60000
 tm=o['entry_minute'];lo=first_touch.get((d,l),minute(tm)*60000);hi=first_touch.get((d,l),minute(tm)*60000+59999);glo=olo+300000;ghi=ohi+300000
 status='CONSUMED_DURING_WAIT' if hi<=glo else 'RETAINED' if lo>ghi else 'CLOCK_BOUNDARY_PENDING'
 eb=next(b for b in data['bars'][d] if b[0][:5]==tm);group='FIRST_PRINT_'+tm if (eb[1]<=o['entry'] if o['buy'] else eb[1]>=o['entry']) else ''
 r=dict(date=d,contract=o['contract'],level=l,buy=o['buy'],entry_level=o['entry'],opening_minute=first[0][:5],opening_lower=fmt(olo),opening_upper=fmt(ohi),opening_source=open_source.get(d,'M1_MINUTE_SECONDS_UNKNOWN'),gate_lower=fmt(glo),gate_upper=fmt(ghi),first_touch_minute=tm,touch_lower=fmt(lo),touch_upper=fmt(hi),touch_source=touch_source.get((d,l),'M1_FIRST_TOUCH_MINUTE'),same_minute_first_print_group=group,status=status)
 gates[d,l]=dict(row=r,olo=olo,ohi=ohi,glo=glo,ghi=ghi,tlo=lo,thi=hi,group=group,o=o);diagnostic.append(r)
# Every configuration remains a frozen-entry/frozen-exit subset, never a retest entry.
origlabels={(r['date'],r['level']):r for r in read(E/'estudo_niveis_auxiliares_20261119/ROTULOS_ORIGINAIS_CONFERIDOS.csv')}
recipes={}
for l in levels:
 rr=[]
 for (d,ll),o in ops.items():
  if l!=ll:continue
  lab=origlabels[d,l];assert float(lab['lower'])==o['original'];rr.append(dict(date=d,level=l,contract=o['contract'],points=o['original'],reason=lab['outcomes'].split(':')[0],entry=o['entry']))
 recipes['ORIGINAL_'+l]=rr
fix=pickle.load(open('/workspace/work/fixos_tres_niveis_20261119/resultados.pickle','rb'))
for name,l,id in [('R61_375_1000','R61.8','F071'),('R61_75_1000','R61.8','F026'),('S38_200_1000','S38.2','F053')]:
 rr=[r for r in fix['trades'] if r['level']==l and r['variant']==id];assert all(r['lower']==r['upper'] and not r['pending'] for r in rr)
 recipes[name]=[dict(date=r['date'],level=l,contract=r['contract'],points=r['lower'],reason=r['outcomes'].split(':')[0],entry=r['entry']) for r in rr]
rr=[r for r in read(E/'fechamento_s61_replay_20261119/OPERACOES.csv') if r['variant']=='S61_42'];assert len(rr)==233
recipes['S61_100_ORIGINAL']=[dict(date=r['date'],level='S61.8',contract=r['contract'],points=float(r['lower']),reason='SL' if float(r['lower'])==-100 else 'TP' if float(r['lower'])==float(r['target_points']) else 'CUT',entry=float(r['entry'])) for r in rr]
assert sum(r['points'] for r in recipes['S61_100_ORIGINAL'])==2295
scenarios=[dict(id='D_ORIGINAL_5',recipes=['ORIGINAL_'+l for l in levels],label='Modelo D original - cinco niveis')]+[dict(id=k,recipes=[k],label=k) for k in recipes]+[dict(id='MISTO_MAIORES_FECHADOS_5',recipes=['ORIGINAL_R38.2','R61_375_1000','S38_200_1000','ORIGINAL_S50','ORIGINAL_S61.8'],label='Cinco niveis - maiores totais fechados individuais')]
def dd(a):
 b=np.cumsum(a);return float(np.max(np.maximum.accumulate(np.r_[0,b])[1:]-b))
# Feasible clock patterns share a common gate within the day. Same-side first-touch order
# and same-minute opening-print equivalences constrain combinations conservatively.
def day_patterns(rr):
 always=[r for r in rr if gates[r['date'],r['level']]['row']['status']=='RETAINED'];unc=[r for r in rr if gates[r['date'],r['level']]['row']['status']=='CLOCK_BOUNDARY_PENDING'];fixed=[r for r in rr if r not in unc];valid=[]
 for bits in itertools.product([0,1],repeat=len(unc)):
  statuses={r['level']:bit for r,bit in zip(unc,bits)}
  statuses.update({r['level']:int(r in always) for r in fixed})
  lower=max(gates[r['date'],r['level']]['glo'] for r in rr);upper=min(gates[r['date'],r['level']]['ghi'] for r in rr)
  for r in rr:
   g=gates[r['date'],r['level']]
   if statuses[r['level']]:upper=min(upper,g['thi']-1)
   else:lower=max(lower,g['tlo'])
  if lower>upper:continue
  ok=True
  for a,b in itertools.combinations(rr,2):
   ga=gates[a['date'],a['level']];gb=gates[b['date'],b['level']];sa=statuses[a['level']];sb=statuses[b['level']]
   if ga['group'] and ga['group']==gb['group'] and sa!=sb:ok=False;break
   if ga['o']['buy']==gb['o']['buy']:
    # shallower order is touched no later than the deeper order.
    early,later=(a,b) if ((a['entry']>=b['entry']) if ga['o']['buy'] else (a['entry']<=b['entry'])) else (b,a)
    if statuses[early['level']]==1 and statuses[later['level']]==0:ok=False;break
  if not ok:continue
  selected=[r for r in rr if statuses[r['level']]]
  valid.append(dict(points=sum(r['points'] for r in selected),operations=len(selected),TP=sum(r['reason']=='TP' for r in selected),SL=sum(r['reason']=='SL' for r in selected),CUT=sum(r['reason']=='CUT' for r in selected),retained_levels='|'.join(sorted(r['level'] for r in selected))))
 assert valid,rr
 return valid
summary=[];annual=[];monthly=[];daily=[];patterns=[];curves={}
for s in scenarios:
 rr=[r for k in s['recipes'] for r in recipes[k]];assert len({(r['date'],r['level']) for r in rr})==len(rr)
 orig=np.zeros(709);a=orig.copy();b=orig.copy();nlo=orig.copy();nhi=orig.copy();grouped=collections.defaultdict(list)
 for r in rr:orig[di[r['date']]]+=r['points'];grouped[r['date']].append(r)
 count=collections.Counter(gates[r['date'],r['level']]['row']['status'] for r in rr)
 for d,part in grouped.items():
  ps=day_patterns(part);i=di[d];a[i]=min(p['points'] for p in ps);b[i]=max(p['points'] for p in ps);nlo[i]=min(p['operations'] for p in ps);nhi[i]=max(p['operations'] for p in ps)
  for p in ps:patterns.append(dict(scenario=s['id'],date=d,**p))
 row=dict(id=s['id'],label=s['label'],original_operations=len(rr),original_points=float(orig.sum()),original_DD=dd(orig),consumed=count['CONSUMED_DURING_WAIT'],definitely_retained=count['RETAINED'],clock_pending_operations=count['CLOCK_BOUNDARY_PENDING'],clock_pending_dates=len({r['date'] for r in rr if gates[r['date'],r['level']]['row']['status']=='CLOCK_BOUNDARY_PENDING'}),operations_lower=int(nlo.sum()),operations_upper=int(nhi.sum()),points_lower=float(a.sum()),points_upper=float(b.sum()),DD_lower=dd(b),DD_upper=dd(a))
 for y in [2024,2025,2026]:
  mask=np.array([d.startswith(str(y)) for d in days]);row[f'year{y}_original']=float(orig[mask].sum());row[f'year{y}_lower']=float(a[mask].sum());row[f'year{y}_upper']=float(b[mask].sum());annual.append(dict(scenario=s['id'],year=y,original_points=float(orig[mask].sum()),points_lower=float(a[mask].sum()),points_upper=float(b[mask].sum()),operations_lower=int(nlo[mask].sum()),operations_upper=int(nhi[mask].sum()),DD_year_lower=dd(b[mask]),DD_year_upper=dd(a[mask])))
 for m in sorted({d[:7] for d in days}):
  mask=np.array([d.startswith(m) for d in days]);monthly.append(dict(scenario=s['id'],month=m,original_points=float(orig[mask].sum()),points_lower=float(a[mask].sum()),points_upper=float(b[mask].sum()),DD_month_lower=dd(b[mask]),DD_month_upper=dd(a[mask])))
 for i,d in enumerate(days):daily.append(dict(scenario=s['id'],date=d,original_points=orig[i],new_lower=a[i],new_upper=b[i],operations_lower=int(nlo[i]),operations_upper=int(nhi[i])))
 curves[s['id']]=dict(orig=orig,lo=a,hi=b,nlo=nlo,nhi=nhi);summary.append(row)
# One chronological list of Replay windows for clock questions, shared by all configurations.
pending=[r for r in diagnostic if r['status']=='CLOCK_BOUNDARY_PENDING'];req=collections.defaultdict(lambda:dict(levels=set(),purposes=set()))
for r in pending:
 for typ,tm in [('OPENING',r['opening_minute']),('FIRST_TOUCH_AT_GATE',r['first_touch_minute'])]:
  q=req[r['date'],r['contract'],tm];q['levels'].add(r['level']);q['purposes'].add(typ)
requests=[dict(date=d,contract=c,start=tm,end_exclusive=mm(minute(tm)+1),levels='|'.join(sorted(v['levels'])),purpose='|'.join(sorted(v['purposes']))) for (d,c,tm),v in sorted(req.items())]
write('DIAGNOSTICO_1485_ENTRADAS.csv',diagnostic);write('RESULTADOS_CENARIOS.csv',summary);write('ANUAL.csv',annual);write('MENSAL.csv',monthly);write('DIARIO.csv',daily);write('PADROES_DIARIOS_RELOGIO.csv',patterns);write('PENDENCIAS_RELOGIO.csv',pending);write('REPLAY_JANELAS_UNIFICADAS.csv',requests)
(C/'resultados.pickle').write_bytes(pickle.dumps(dict(base=base,ops=ops,gates=gates,diagnostic=diagnostic,recipes=recipes,scenarios=scenarios,summary=summary,annual=annual,monthly=monthly,daily=daily,patterns=patterns,requests=requests,curves=curves,pending=pending,source_paths=sorted(set(source_paths)),first_open=first_open,first_touch=first_touch)))
print(json.dumps(dict(opening_exact_days=len(first_open),exact_touch_operations=len(first_touch),pending_operations=len(pending),pending_dates=len({r['date'] for r in pending}),requested_minutes=len(requests),summary=summary),ensure_ascii=False,indent=2))
