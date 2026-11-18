"""Fixed stop50/target250 on unchanged D entries. Outcomes are bounded, not cherry-picked.
Use saved auditM1, validated full Replay minutes, closed-original implications,
and full recovered Cedro for8days. No new entries, re-entry or broker fills.
"""
from pathlib import Path
from decimal import Decimal as D
import csv,json,pickle,ast,math,collections
import numpy as np
P=Path(__file__).parent;R=P.parents[1];E=R/'entregas';data=pickle.loads(Path('/workspace/work/estudo_saidas/dados.pickle').read_bytes());days=data['days'];ops=data['ops'];assert len(days)==709 and len(ops)==1485

def read(p):
 with p.open(encoding='utf-8-sig') as f:return list(csv.DictReader(f,delimiter=';'))
def write(name,rs):
 with (P/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rs[0]),delimiter=';',lineterminator='\n');w.writeheader();w.writerows(rs)
# Use all21saved August audit files, not Profit proxy.
aug=[]
for p in (E/'cedro_extrator_win_v1_00').rglob('retorno_agosto*/M1_WIN*.csv'):
 rr=read(p);day=rr[0]['time'][:10].replace('.','-');data['bars'][day]=[(r['time'][11:],*[int(D(r[k])) for k in ['open','high','low','close']],int(D(r['soma_campo4']))) for r in rr];data['source'][day]='CEDRO_AUDIT_M1';aug.append(day)
assert len(set(aug))==21
# Read actual original exit labels, not infer them from point totals.
reason={}
for p in [E/'validacao_replay_2024_20261117/OPERACOES_FINAIS_2024.csv',*list((E/'validacao_lote_2025_20261116').glob('[01][0-9]_*/OPERACOES_FINAIS.csv')),*list(E.glob('profit_*/OPERACOES_FINAIS.csv'))]:
 for r in read(p):reason[(r['date'],r['level'])]=r['reason']
p=E/'profit_winq26_julho_20261113';resolved={(r['date'],r['level']):r['reason'] for r in read(p/'REPLAY_OPERACOES_RESOLVIDAS.csv')}
for r in read(p/'OPERACOES_POSSIBILIDADES.csv'):reason[(r['date'],r['level'])]=resolved.get((r['date'],r['level']),r['outcomes'].split(':')[0])
for mo,sub in [('agosto','resultado'),('setembro','resultado'),('outubro','resultado_mensal')]:
 for r in read(E/f'cedro_modelod_{mo}_2026'/sub/'TODOS_NIVEIS.csv'):
  if r['estado']=='ENCERRADA':reason[(r['data'],r['nivel'])]={'STOP':'SL','ALVO':'TP','CORTE_LAST':'CORTE'}[r['motivo']]
assert all((o['date'],o['level']) in reason for o in ops)
bars={d:[(int(b[0][:2])*60+int(b[0][3:]),*b[1:5]) for b in data['bars'][d]] for d in days};replay=data['replay'];known_noquote={'2024-02-06','2024-06-07','2025-06-03','2025-07-30','2025-08-21'}
ns=dict(collections=collections)
for f in ast.parse((E/'estudo_saidas_niveis_20261117/testar_cenarios.py').read_text()).body:
 if isinstance(f,ast.FunctionDef) and f.name=='tick_choices':exec(compile(ast.Module(body=[f],type_ignores=[]),'validated_tick_choices','exec'),ns)

def evaluate(o):
 sign=1 if o['buy'] else -1;e=sign*o['entry'];tp=e+250;sl=e-50;start=int(o['entry_minute'][:2])*60+int(o['entry_minute'][3:]);bs=bars[o['date']];cut=next((sign*b[1]-e for b in bs if b[0]>=1080),None);label=reason[(o['date'],o['level'])];oldtd=abs(o['tp']-o['entry'])
 if label=='SL' and oldtd<=250:return {('SL',-50)},[],'PROVEN_ORIGINAL_STOP_TIGHTER_STOP_NOT_NEARER_TARGET'
 if cut is None:return {('SL',-50),('TP',250)},[('18:00','CUT_MISSING')],'SOURCE_PENDING'
 eb=next((b for b in bs if b[0]==start),None)
 if eb is None or (eb[3]>o['entry'] if sign==1 else eb[2]<o['entry']):return {('SL',-50),('TP',250),('CORTE',cut)},[(o['entry_minute'],'ENTRY_SOURCE_MISMATCH')],'SOURCE_PENDING'
 ends=set();active=True;asks=[];last=start
 for minute,bo,bh,bl,bc in bs:
  if minute<start:continue
  if minute>=1080:
   if active:ends.add(('CORTE',sign*bo-e))
   active=False;break
  if not active:break
  if minute-last>1 and o['date'] not in known_noquote:ends|={('SL',-50),('TP',250)};asks.append((f'{(last+1)//60:02d}:{(last+1)%60:02d}','GAP_AFTER_ENTRY'))
  last=minute;O,H,L,C=(bo,bh,bl,bc) if sign==1 else (-bo,-bl,-bh,-bc);entering=minute==start
  if entering:
   poss=H>=tp;forced=poss and (O<=e or C>=tp);stop=L<=sl
   choices=({'TP'} if poss else set())|({'SL'} if stop else set())|({'OPEN'} if not forced and not stop else set())
  else:choices={'TP'} if O>=tp else {'SL'} if O<=sl else ({'TP'} if H>=tp else set())|({'SL'} if L<=sl else set()) or {'OPEN'}
  tm=f'{minute//60:02d}:{minute%60:02d}'
  if len(choices)>1:
   exact=ns['tick_choices'](replay[(o['date'],tm)],e,tp,sl,sign,entering) if (o['date'],tm) in replay else None
   if exact:choices=exact
   else:asks.append((tm,'SEQUENCE_M1'))
  if 'TP' in choices:ends.add(('TP',250))
  if 'SL' in choices:ends.add(('SL',-50))
  active='OPEN' in choices
 if active:ends|={('SL',-50),('TP',250),('CORTE',cut)};asks.append(('18:00','UNFINISHED_SOURCE'))
 assert ends,(o,'nooutcomes')
 if label=='CORTE' and oldtd<=250:
  # Original never hit its nearer target before cut. Exclude inconsistent TP paths.
  ends={v for v in ends if v[0]!='TP'}
  if not ends:ends={('SL',-50),('CORTE',o['original'])};asks.append((o['entry_minute'],'ORIGINAL_SOURCE_CONSTRAINT'))
 pts={v[1] for v in ends}
 return ends,asks if len(pts)>1 else [],'M1_AND_VALIDATED_REPLAY'
raw={(r['date'],r['level']):r for r in read(P/'CEDRO_50_250_OPERACOES_EXATAS.csv')};trades=[];windows=[];proofs=[]
for o in ops:
 ends,asks,basis=evaluate(o);a=min(v[1] for v in ends);b=max(v[1] for v in ends);rr=raw.get((o['date'],o['level']))
 if rr and rr['resolved']=='True':
  v=int(D(rr['points']));label={'STOP':'SL','ALVO':'TP','CORTE_LAST':'CORTE'}[rr['reason']];assert a<=v<=b,(o,ends,rr);ends={(label,v)};a=b=v;asks=[];basis='FULL_CEDRO_DIRECT_PLUS_INDEPENDENT_PYTHON'
 uncertain=a!=b
 tr=dict(date=o['date'],level=o['level'],contract=o['contract'],entry_minute=o['entry_minute'],entry_level=o['entry'],target_level=o['entry']+(250 if o['buy'] else -250),stop_level=o['entry']+(-50 if o['buy'] else 50),original_points=o['original'],lower=a,upper=b,unresolved=uncertain,outcomes='|'.join(f'{r}:{v}' for r,v in sorted(ends)),target_guaranteed=all(r=='TP' for r,v in ends),target_possible=any(r=='TP' for r,v in ends),cut_possible=any(r=='CORTE' for r,v in ends),source=basis)
 trades.append(tr)
 if basis.startswith('PROVEN'):proofs.append(dict(date=o['date'],level=o['level'],old_reason=reason[(o['date'],o['level'])],old_target_distance=abs(o['tp']-o['entry']),new_points=-50))
 if uncertain:
  for tm,why in asks:windows.append(dict(date=o['date'],contract=o['contract'],level=o['level'],minute=tm,reason=why,lower=a,upper=b))
assert len(trades)==1485 and len({(r['date'],r['level']) for r in trades})==1485
# Independent daily entry conservation, one per level/day.
daily=[];bal_lo=bal_hi=peak_lo=peak_hi=DD_lo=DD_hi=0
for day in days:
 rs=[r for r in trades if r['date']==day];assert len(rs)<=5
 lo=sum(r['lower'] for r in rs);hi=sum(r['upper'] for r in rs);bal_lo+=lo;bal_hi+=hi;peak_lo=max(peak_lo,bal_lo);peak_hi=max(peak_hi,bal_hi);DD_lo=max(DD_lo,peak_lo-bal_lo);DD_hi=max(DD_hi,peak_hi-bal_hi)
 daily.append(dict(date=day,operations=len(rs),lower=lo,upper=hi,unresolved_operations=sum(r['unresolved'] for r in rs),target_count_min=sum(r['target_guaranteed'] for r in rs),target_count_max=sum(r['target_possible'] for r in rs),balance_lower=bal_lo,balance_upper=bal_hi,DD_lower=DD_hi,DD_upper=DD_lo,all_stops_floor=-50*len(rs),below_stop_only_floor=lo<-50*len(rs),one_target_guaranteed=any(r['target_guaranteed'] for r in rs),source=data['source'][day]))

def dd(a):
 bal=np.cumsum(a);return float(np.max(np.maximum.accumulate(np.r_[0,bal])[1:]-bal))
monthly=[];annual=[]
for month in sorted({d[:7] for d in days}):
 rs=[r for r in daily if r['date'].startswith(month)];monthly.append(dict(month=month,days=len(rs),operations=sum(r['operations'] for r in rs),lower=sum(r['lower'] for r in rs),upper=sum(r['upper'] for r in rs),DD_month_lower=dd([r['upper'] for r in rs]),DD_month_upper=dd([r['lower'] for r in rs]),pending_operations=sum(r['unresolved_operations'] for r in rs),pending_days=sum(r['unresolved_operations']>0 for r in rs),exact_days=sum(r['unresolved_operations']==0 for r in rs),positive_days_guaranteed=sum(r['lower']>0 for r in rs),negative_days_guaranteed=sum(r['upper']<0 for r in rs)))
for year in ['2024','2025','2026']:
 rs=[r for r in daily if r['date'].startswith(year)];nn=sum(r['operations'] for r in rs);lo=sum(r['lower'] for r in rs);hi=sum(r['upper'] for r in rs)
 annual.append(dict(year=year,scope='JanOut' if year=='2026' else 'AnoCompleto',days=len(rs),operations=nn,lower=lo,upper=hi,DD_year_lower=dd([r['upper'] for r in rs]),DD_year_upper=dd([r['lower'] for r in rs]),pending_operations=sum(r['unresolved_operations'] for r in rs),pending_days=sum(r['unresolved_operations']>0 for r in rs),after_cost5_lower=lo-5*nn,after_cost5_upper=hi-5*nn,after_cost10_lower=lo-10*nn,after_cost10_upper=hi-10*nn))
level_stats=[]
for level in ['R38.2','R61.8','S38.2','S50','S61.8']:
 for year in ['2024','2025','2026']:
  rs=[r for r in trades if r['level']==level and r['date'].startswith(year)];level_stats.append(dict(level=level,year=year,operations=len(rs),lower=sum(r['lower'] for r in rs),upper=sum(r['upper'] for r in rs),pending_operations=sum(r['unresolved'] for r in rs)))
write('OPERACOES_50_250.csv',trades);write('DIARIO_50_250.csv',daily);write('MENSAL_50_250.csv',monthly);write('ANUAL_50_250.csv',annual);write('POR_NIVEL_50_250.csv',level_stats);write('JANELAS_PENDENTES_50_250.csv',windows);write('PROVAS_ORIGINAL_50_250.csv',proofs)
# Coalesce only collection windows, not trades. Exclude waived historical control
# from automatic requests; a variant-specific unknown remains explicitly pending.
merged={}
for r in windows:
 key=(r['date'],r['contract'],r['minute'],r['reason'])
 if key not in merged:merged[key]=dict(date=r['date'],contract=r['contract'],minute=r['minute'],reason=r['reason'],levels=r['level'])
 else:merged[key]['levels']+=','+r['level']
write('JANELAS_AGRUPADAS_50_250.csv',sorted(merged.values(),key=lambda r:(r['date'],r['minute'])))
# Which priority S61copies can also help this new fixed-exit test?
priority=read(P/'20_JANELAS_PRIORITARIAS_E_COINCIDENCIAS.csv')
for r in priority:
 same=[w for w in merged.values() if w['date']==r['date'] and w['minute']==r['start'][:5]];r['also_helps_50_250']=bool(same);r['levels_50_250']='|'.join(w['levels'] for w in same)
write('20_JANELAS_PRIORITARIAS_E_COINCIDENCIAS.csv',priority)
# Check the proposed arithmetic without assuming all five entries occur daily.
for count in range(1,6):
 for wins in range(count+1):
  theoretical=250*wins-50*(count-wins)
  assert theoretical==300*wins-50*count
  if wins>=1:assert theoretical>=50
cutbelow=[r for r in trades if r['lower']<-50];write('CONTROLES_PERDA_ALEM_STOP_POR_CORTE_OU_FONTE.csv',cutbelow or [dict(status='NENHUM_CASO_LOWER_BELOW_MINUS50')])
summary=dict(period='Jan2024Oct2026',status='TRIAGEM_COM_LIMITES_DE_SEQUENCIA',target_points=250,stop_points=50,max_one_entry_per_level=True,no_reentries=True,daily_hard_stop_added=False,daily_take_profit_stop_after_first_target=False,max_entries_per_day=5,entries_total=1485,days=709,total_lower=bal_lo,total_upper=bal_hi,DD_lower=DD_hi,DD_upper=DD_lo,unresolved_operations=sum(r['unresolved'] for r in trades),unresolved_days=sum(r['unresolved_operations']>0 for r in daily),unique_pending_windows=len(merged),daily_entry_distribution=dict(collections.Counter(r['operations'] for r in daily)),days_with_guaranteed_target=sum(r['one_target_guaranteed'] for r in daily),days_with_possible_target=sum(r['target_count_max']>0 for r in daily),days_proven_positive=sum(r['lower']>0 for r in daily),days_proven_negative=sum(r['upper']<0 for r in daily),trades_cut_or_source_bound_below_minus50=len(cutbelow),days_lower_below_minus250=sum(r['lower']<-250 for r in daily),priority_windows_also_helping_fixed_test=sum(r['also_helps_50_250'] for r in priority),raw_Cedro_operations_verified=len(raw),raw_Cedro_records=39031316,monotonic_stop_proofs=len(proofs),one_target_four_stops_gross=50,break_even_target_fraction_if_only_TP_SL=1/6,costs_in_main=False,certified_fills=False,original_results_unchanged=True)
(P/'RESULTADO_50_250.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');print(json.dumps(summary,ensure_ascii=False,indent=2));print('ANNUAL',annual)
