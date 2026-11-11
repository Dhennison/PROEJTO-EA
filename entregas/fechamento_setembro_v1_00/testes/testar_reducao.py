"""Verify the reduced event stream against full received business ticks."""
import sys,csv,random,json
from pathlib import Path
from decimal import Decimal as D
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'analise'))
from motor_precos import levels,replay,reduce_events,summary,epoch
root=Path(__file__).resolve().parents[1]
def read(path):
 with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter=';'))
refs={r['date']:r for r in read(root/'MQL5/Files/MD_Setembro_2026_Referencias.csv')}
fixtures=[('2026.09.10','/workspace/attachments/da05c399-e4d7-49bf-9533-fbbe4dc3b075'),('2026.09.10','/workspace/attachments/200f64e0-e8b5-49be-b2cc-b9b0495a84e3'),('2026.09.14','/workspace/attachments/22de8774-fa34-48aa-9fe8-29ba82d3d382'),('2026.09.16','/workspace/attachments/aba1df05-2540-472b-8a62-bbabdbfe05b8'),('2026.09.17','/workspace/retorno_sequencia_20260917'),('2026.09.14','/workspace/attachments/5042edda-c8f7-4f82-b10c-17fc85f98b9a')]
results=[];checks=0
for day,directory in fixtures:
 p=next(Path(directory).glob('*.csv'));ev=[]
 with p.open(encoding='utf-8-sig',newline='') as f:
  for i,r in enumerate(csv.DictReader(f,delimiter=';')):
   if int(r['flags'])&120:ev.append({'ord':i+1,'msc':int(r['time_msc']),'p':D(r['last'])})
 ls=levels(refs[day]);compressed=list(reduce_events(ev,ls))
 for grid in (False,True):
  for strict in (False,True):
   assert summary(replay(ev,ls,None,grid,strict))==summary(replay(compressed,ls,None,grid,strict)),(day,grid,strict)
   checks+=5
 results.append({'file':p.name,'business_records':len(ev),'reduced_events':len(compressed),'all_5_levels_4_variants_identical':True})
 print('PASS',day,len(ev),len(compressed),flush=True)
# Gaps past entry and SL, repeated timestamps, non-grid prices, first cutoff event.
ls=[dict(name='S38.2',buy=True,eligible=True,entry=D(100),sl=D(90),tp=D(110),entry5=D(100),sl5=D(90),tp5=D(110)),dict(name='R38.2',buy=False,eligible=True,entry=D(110),sl=D(120),tp=D(100),entry5=D(110),sl5=D(120),tp5=D(100))]
for seed in range(100):
 rng=random.Random(seed);ev=[{'ord':i+1,'msc':(i//3)*1000,'p':D(rng.choice([85,90,95,100,105,110,115,120,125]))} for i in range(200)]
 for grid in (False,True):
  for strict in (False,True):
   assert summary(replay(ev,ls,60000,grid,strict))==summary(replay(list(reduce_events(ev,ls)),ls,60000,grid,strict));checks+=2
# Non-grid events are never discarded.
ev=[{'ord':i+1,'msc':i,'p':D('100.1')+D(i)/1000} for i in range(30)]
assert list(reduce_events(ev,ls))==ev;checks+=1
result={'checks':checks,'full_tick_fixtures':results,'native_MT5_compile_or_execution':False,'scope':'Exact comparison of all replay fields and event identities, full stream versus reduced stream; seeded gap/equality/timestamp/cutoff controls.'}
(root/'testes/RESULTADO_REDUCAO.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print('PASS checks',checks)
