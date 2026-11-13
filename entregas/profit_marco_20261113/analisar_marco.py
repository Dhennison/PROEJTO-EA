"""Candle-only March D: branch unresolved chronology; never invent ticks or fills."""
import csv,json,sys,collections,datetime as dt
from pathlib import Path
from decimal import Decimal as D
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'entregas/fechamento_agosto_v1_11/analise'))
from motor_precos import levels
OUT=Path(__file__).parent
CSV=Path('/workspace/candles_originais_modelo_d/WINFUT_F_0_1min_01-01-2026_22-09-2026.csv')
REF=Path('/workspace/historico_modelo_d_20230301_20260921')
CONTEXT_M5=Path('/workspace/candles_originais_modelo_d/WINFUT_F_0_5min_01-01-2026_28-02-2026.csv')
def read(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter=';'))
def write(name,rs):
 if not rs:return
 with (OUT/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rs[0]),delimiter=';',lineterminator='\n');w.writeheader();w.writerows(rs)
def dec(x):return D(str(x).replace(',','.'))
def choices(o,h,l,c,e,t,s,entry):
 """Orient all trades as buys. Sets describe exits in THIS candle, not final trade."""
 if not entry:
  if o>=t:return {'TP'}
  if o<=s:return {'SL'}
  target=h>=t;stop=l<=s
  return ({'TP'} if target else set())|({'SL'} if stop else set()) or {'OPEN'}
 # Entry known to occur since l<=e. Extreme stop lies below entry.
 possible=h>=t;forced=possible and (o<=e or c>=t);stop=l<=s
 return ({'TP'} if possible else set())|({'SL'} if stop else set())|({'OPEN'} if not forced and not stop else set())
# Meaningful branch tests, including pre-entry high and later return.
assert choices(110,120,95,99,100,115,90,True)=={'TP','OPEN'}
assert choices(110,120,85,99,100,115,90,True)=={'TP','SL'}
assert choices(100,120,95,99,100,115,90,True)=={'TP'}
assert choices(105,110,95,101,100,115,90,False)=={'OPEN'}
assert choices(116,120,85,99,100,115,90,False)=={'TP'}
assert choices(100,120,85,99,100,115,90,False)=={'TP','SL'}
def run():
 days=collections.defaultdict(list)
 for r in csv.reader(CSV.read_bytes().decode('cp1252').splitlines(),delimiter=';'):
  if r[0]=='Ativo':continue
  stamp=dt.datetime.strptime(r[1]+' '+r[2],'%d/%m/%Y %H:%M:%S');days[stamp.date()].append((stamp,*[D(x.replace('.','').replace(',','.')) for x in r[3:7]]))
 # Work context on02March uses complete27February M5,not partial overlapping M1.
 prior=dt.date(2026,2,27);full_prev=[]
 for r in csv.reader(CONTEXT_M5.read_bytes().decode('cp1252').splitlines(),delimiter=';'):
  if r[0]=='Ativo' or r[1]!='27/02/2026':continue
  stamp=dt.datetime.strptime(r[1]+' '+r[2],'%d/%m/%Y %H:%M:%S');full_prev.append((stamp,*[D(x.replace('.','').replace(',','.')) for x in r[3:7]]))
 assert full_prev and min(x[0].hour for x in full_prev)==9
 days[prior]=full_prev
 for bs in days.values():bs.sort()
 wa={r['DataOperacional']:dec(r['Ajuste']) for r in read(REF/'Ajustes_Diarios_Modelo_D_20230301_20260921.csv')}
 adj={dt.date.fromisoformat(d):{a} for d,a in wa.items()}
 work=[r for r in read(REF/'Operacoes_Modelo_D_20230301_20260921_ORIGINAL.csv') if r['Data'].startswith('2026-03')]
 wi={(r['Data'],r['Nível']):r for r in work}
 ops=[];contexts=[];asks=[];gaps=[];eligible=0;mathdiff=[];workdiff=[]
 for day in sorted(d for d in days if d.month==3):
  prev=max(d for d in days if d<day);bs=days[day];pb=days[prev];a=next(iter(adj[day]));assert len(adj[day])==1; assert day.isoformat() not in wa or wa[day.isoformat()]==a
  ref=dict(open=str(bs[0][1]),high_prev=str(max(b[2] for b in pb)),low_prev=str(min(b[3] for b in pb)),close_prev=str(pb[-1][4]),adjustment=str(a))
  contexts.append(dict(date=day.isoformat(),previous=prev.isoformat(),previous_source='WORK_M5_COMPLETE' if prev==prior else 'WORK_M1',previous_first=str(pb[0][0]),previous_last=str(pb[-1][0]),previous_bars=len(pb),**ref))
  for b1,b2 in zip(bs,bs[1:]):
   if b2[0]-b1[0]>dt.timedelta(minutes=1) and b1[0].hour<18:gaps.append(dict(date=str(day),start=str(b1[0]),end=str(b2[0])))
  for lev in levels(ref):
   if not lev['eligible']:continue
   eligible+=1;sgn=1 if lev['buy'] else -1
   e,t,s=[sgn*lev[k] for k in ('entry5','tp5','sl5')];active=False;ends=set();entrytime=None;branchbars=[];workreason=None;workpoints=None
   for stamp,bo,bh,bl,bc in bs:
    o,h,l,c=(bo,bh,bl,bc) if sgn==1 else (-bo,-bl,-bh,-bc)
    if stamp.time()>=dt.time(18):
     if active:ends.add(('CORTE',stamp.isoformat(),str(sgn*bo-e)));active=False
     break
    entering=entrytime is None
    if entering:
     if l>e:continue
     active=True;entrytime=stamp
    if not active:continue
    ch=choices(o,h,l,c,e,t,s,entering)
    if len(ch)>1:
     branchbars.append(stamp.isoformat());asks.append(dict(date=str(day),level=lev['name'],minute=stamp.strftime('%H:%M'),phase='ENTRADA' if entering else 'POSICAO_ABERTA',possibilities='|'.join(sorted(ch)),entry=str(sgn*e),tp=str(sgn*t),sl=str(sgn*s),open=str(bo),high=str(bh),low=str(bl),close=str(bc)))
    for reason in ch-{'OPEN'}:ends.add((reason,stamp.isoformat(),str((t if reason=='TP' else s)-e)))
    active='OPEN' in ch
   if entrytime is None:continue
   assert not active and ends, (day,lev['name'],'cut missing')
   outcomes=sorted(set((reason,p) for reason,tm,p in ends));pts=[D(p) for _,_,p in ends]
   wr=wi.get((str(day),lev['name']))
   if wr:
    for key,wkey in [('entry','Entrada'),('tp','Alvo'),('sl','Stop')]:
     if abs(lev[key]-dec(wr[wkey]))>D('.00001'):mathdiff.append((str(day),lev['name'],key))
   else:workdiff.append((str(day),lev['name'],'extra'))
   ops.append(dict(date=str(day),level=lev['name'],entry_minute=entrytime.strftime('%H:%M'),entry=str(sgn*e),tp=str(sgn*t),sl=str(sgn*s),outcomes='|'.join(f'{r}:{p}' for r,p in outcomes),determined=len(outcomes)==1,min_points=str(min(pts)),max_points=str(max(pts)),work_reason=wr['Motivo'] if wr else '',work_points=wr['Pontos'] if wr else '',branch_minutes='|'.join(branchbars),exit_candidates='|'.join(f'{r}@{tm}' for r,tm,p in sorted(ends))))
 assert not mathdiff,mathdiff
 missing=set(wi)-{(o['date'],o['level']) for o in ops}
 daily=[]
 for day in sorted(d for d in days if d.month==3):
  rr=[o for o in ops if o['date']==str(day)];ww=[r for r in work if r['Data']==str(day)]
  daily.append(dict(date=str(day),operations=len(rr),determined=sum(o['determined'] for o in rr),pending=sum(not o['determined'] for o in rr),min_points=str(sum((D(o['min_points']) for o in rr),D(0))),max_points=str(sum((D(o['max_points']) for o in rr),D(0))),work_points=str(sum((dec(r['Pontos']) for r in ww),D(0)))))
 write('OPERACOES_POSSIBILIDADES.csv',ops);write('JANELAS_REPLAY.csv',asks);write('REFERENCIAS_MARCO.csv',contexts);write('DIARIO_PROVISORIO.csv',daily);write('LACUNAS.csv',gaps)
 res=dict(status='PROVISORIO_CANDLES_M1_AGUARDANDO_REPLAY',days=len(daily),operations=len(ops),determined=sum(o['determined'] for o in ops),pending=sum(not o['determined'] for o in ops),work_operations=len(work),work_points=str(sum((dec(r['Pontos']) for r in work),D(0))),outer_min=str(sum((D(o['min_points']) for o in ops),D(0))),outer_max=str(sum((D(o['max_points']) for o in ops),D(0))),pending_dates=sorted(set(o['date'] for o in ops if not o['determined'])),branch_minutes=len(asks),adjustments_Work_available=sum(str(d) in wa for d in days if d.month==3),mathematical_level_differences=mathdiff,work_missing=sorted(missing),work_extra=workdiff,gaps=gaps,limits='Outer envelope per operation, not jointly attainable guaranteed. Normalized levels only, no costs/fills. No tick path invented. Candle range does not prove tape completeness. Unresolved chronology requires Replay; intra-minute exit time not determined.')
 (OUT/'RESULTADO_PROVISORIO.json').write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n');print(json.dumps(res,ensure_ascii=False,indent=2))
if __name__=='__main__':run()
