from pathlib import Path
import csv,pickle,json,ast,collections,hashlib,itertools
import numpy as np
P=Path(__file__).parent;R=P.parents[1];E=R/'entregas';C=Path('/workspace/work/replay_s23_20261119')
x=pickle.load(open('/workspace/work/novos_niveis_20261119/resultados.pickle','rb'));audit=pickle.load(open(C/'auditoria.pickle','rb'));assert len(audit['accepted'])==5
data=x['data'];data['replay'].update(audit['accepted']);ns=dict(np=np,data=data,replays={},noquote={'2024-02-06','2024-06-07','2025-06-03','2025-07-30','2025-08-21'})
for key,events in data['replay'].items():
 prices=np.array([v[1] for v in events],dtype=np.int32);times=np.array([int(v[0].replace(':','').replace('.','')) for v in events],dtype=np.int64);borders=np.r_[0,np.flatnonzero(times[1:]!=times[:-1])+1,len(times)];idx=np.concatenate([np.arange(i,j)[::-1] for i,j in zip(borders[:-1],borders[1:])]);ns['replays'][key]=(prices,times,prices[idx],times[idx])
src=(E/'estudo_niveis_auxiliares_20261119/estudar.py').read_text()
for f in ast.parse(src).body:
 if isinstance(f,ast.FunctionDef) and f.name in ['ticks','evaluate']:exec(compile(ast.Module(body=[f],type_ignores=[]),'preserved_sequence_engine','exec'),ns)
# Only the requested S23 stop200/target500 is updated; previous studies stay immutable.
ops={o['date']:o for o in x['newops'] if o['level']=='S23.6'};trades=[r.copy() for r in x['trades'] if r['level']=='S23.6' and r['variant']=='N089'];changes=[];outwindows=[]
newdates={d for d,tm in audit['accepted']}
for r in trades:
 if r['date'] not in newdates:continue
 old=r.copy();ends,pend=ns['evaluate'](ops[r['date']],500,200);a=min(v for k,v in ends);b=max(v for k,v in ends);assert old['lower']<=a<=b<=old['upper']
 r.update(lower=a,upper=b,outcomes='|'.join(f'{k}:{v}' for k,v in sorted(ends)),pending=len(ends)>1,source='M1_PLUS_VALIDATED_NOVAS_DATAS_REPLAY',**{f'{k}_guaranteed':all(reason==k for reason,v in ends) for k in ['TP','SL','CUT']},**{f'{k}_possible':any(reason==k for reason,v in ends) for k in ['TP','SL','CUT']})
 changes.append(dict(date=r['date'],contract=r['contract'],entry_minute=r['entry_minute'],entry=r['entry'],stop=r['entry']-200,target=r['entry']+500,previous_lower=old['lower'],previous_upper=old['upper'],lower=a,upper=b,outcomes=r['outcomes'],resolved=len(ends)==1))
 if len(ends)>1:
  for tm,why in pend:outwindows.append(dict(date=r['date'],contract=r['contract'],minute=tm,reason=why))
assert all(r['resolved'] for r in changes)
def write(name,rows):
 if not rows:return
 with (P/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for r in rows for k in r)),delimiter=';');w.writeheader();w.writerows(rows)
def dd(a):
 b=np.cumsum(a);return float(np.max(np.maximum.accumulate(np.r_[0,b])[1:]-b))
days=data['days'];di={d:i for i,d in enumerate(days)};a=np.zeros(709);b=a.copy()
for r in trades:a[di[r['date']]]=r['lower'];b[di[r['date']]]=r['upper']
summary=dict(level='S23.6',stop=200,target=500,operations=386,total_lower=float(a.sum()),total_upper=float(b.sum()),DD_lower=dd(b),DD_upper=dd(a),pending=sum(r['pending'] for r in trades))
annual=[];monthly=[];daily=[]
for y in [2024,2025,2026]:
 mask=np.array([d.startswith(str(y)) for d in days]);summary[f'year{y}_lower']=float(a[mask].sum());summary[f'year{y}_upper']=float(b[mask].sum());annual.append(dict(year=y,scope='JanOut' if y==2026 else 'Completo',operations=sum(r['date'].startswith(str(y)) for r in trades),lower=float(a[mask].sum()),upper=float(b[mask].sum()),DD_year_lower=dd(b[mask]),DD_year_upper=dd(a[mask]),pending=sum(r['pending'] for r in trades if r['date'].startswith(str(y)))))
for m in sorted({d[:7] for d in days}):
 mask=np.array([d.startswith(m) for d in days]);monthly.append(dict(month=m,operations=sum(r['date'].startswith(m) for r in trades),lower=float(a[mask].sum()),upper=float(b[mask].sum()),DD_month_lower=dd(b[mask]),DD_month_upper=dd(a[mask]),pending=sum(r['pending'] for r in trades if r['date'].startswith(m))))
ca=np.cumsum(a);cb=np.cumsum(b);pa=np.maximum.accumulate(np.r_[0,ca])[1:];pb=np.maximum.accumulate(np.r_[0,cb])[1:]
for i,d in enumerate(days):daily.append(dict(date=d,lower=a[i],upper=b[i],cumulative_lower=ca[i],cumulative_upper=cb[i],drawdown_lower=pb[i]-cb[i],drawdown_upper=pa[i]-ca[i]))
nsfreq={};src=(E/'estudo_niveis_auxiliares_20261119/frequencias_relatorio.py').read_text()
for f in ast.parse(src).body:
 if isinstance(f,ast.FunctionDef) and f.name in ['longest','freq']:exec(compile(ast.Module(body=[f],type_ignores=[]),'same_frequency_definitions','exec'),nsfreq)
freq=[nsfreq['freq'](trades if y=='ALL' else [r for r in trades if r['date'].startswith(y)],'S23.6','N089',y) for y in ['ALL','2024','2025','2026']]
# Update only the S23 contribution in the three already-reported combinations.
oldA=x['lo'][2,89];oldB=x['hi'][2,89];deltaA=a-oldA;deltaB=b-oldB
prior=list(csv.DictReader((E/'estudo_niveis_auxiliares_20261119/DIARIO_CANDIDATOS.csv').open(encoding='utf-8-sig'),delimiter=';'));combinations=[];combined_daily=[]
for label in dict.fromkeys(r['label'] for r in prior):
 rr=[r for r in prior if r['label']==label];assert [r['date'] for r in rr]==days
 aa=np.array([float(r['lower']) for r in rr])+deltaA;bb=np.array([float(r['upper']) for r in rr])+deltaB
 result=dict(label=label,total_lower=float(aa.sum()),total_upper=float(bb.sum()),DD_lower=dd(bb),DD_upper=dd(aa),pending=sum(r['pending'] for r in x['trades'] if (r['level'],r['variant']) in [('R23.6','N154'),('R50','N155')])+summary['pending'])
 for y in [2024,2025,2026]:mask=np.array([d.startswith(str(y)) for d in days]);result[f'year{y}_lower']=float(aa[mask].sum());result[f'year{y}_upper']=float(bb[mask].sum())
 combinations.append(result)
 for i,d in enumerate(days):combined_daily.append(dict(label=label,date=d,lower=aa[i],upper=bb[i]))
remaining=[r for r in trades if r['pending']];assert len(remaining)==5 and all(r['date']>='2026-08-01' for r in remaining)
write('RESULTADO_S23.csv',[summary]);write('ANUAL_S23.csv',annual);write('MENSAL_S23.csv',monthly);write('DIARIO_S23.csv',daily);write('OPERACOES_S23.csv',trades);write('RESOLUCAO_5_DATAS.csv',changes);write('FREQUENCIAS_S23.csv',freq);write('COMBINACOES_ATUALIZADAS.csv',combinations);write('DIARIO_COMBINACOES.csv',combined_daily);write('PENDENCIAS_CEDRO_JA_RECEBIDO.csv',remaining)
# Carry forward exact missing-recovery names and receipts, never request new Replay for Cedro months.
import shutil
shutil.copyfile(E/'estudo_fixos_tres_niveis_20261119/S23_CEDRO_10_ZIPS_JA_RECEBIDOS_A_RESTAURAR.csv',P/'S23_CEDRO_10_ZIPS_JA_RECEBIDOS_A_RESTAURAR.csv')
(C/'resultado_atualizado.pickle').write_bytes(pickle.dumps(dict(data=data,ops=ops,trades=trades,changes=changes,summary=summary,annual=annual,monthly=monthly,daily=daily,freq=freq,combinations=combinations,audit=audit)))
print(json.dumps(dict(summary=summary,resolved=changes,frequency=freq[0]),ensure_ascii=False,indent=2))
