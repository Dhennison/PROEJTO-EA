import csv,json,collections,datetime as dt,hashlib,itertools
from pathlib import Path
from decimal import Decimal as D
P=Path('/workspace/attachments/11ba83ad-e850-4af2-b952-66b61094a638/Texto colado.txt');OUT=Path(__file__).parent
with P.open(encoding='utf-8-sig') as f:r=list(csv.reader(f,delimiter='\t'))[1:]
r=[x for x in r if any(x)];assert all(len(x)==6 for x in r)
assert all(a[0]>=b[0] for a,b in zip(r,r[1:]))
def price(x):return int(x[2].replace('.','').replace(',',''))
def event(i,x):return {'ordinal_copia':i+1,'hora':x[0],'preco':price(x),'quantidade':int(x[3].replace('.',''))}
e=[event(i,x) for i,x in enumerate(r)];chron=list(reversed(e));group=sorted(e,key=lambda x:x['hora'])
with (OUT/'REFERENCIAS_JULHO.csv').open(encoding='utf-8-sig') as f:ref=next(x for x in csv.DictReader(f,delimiter=';') if x['date']=='2026-07-01')
import sys
sys.path.insert(0,str(OUT.parents[1]/'fechamento_agosto_v1_11/analise'))
# Resolve repository path independently of execution cwd.
sys.path.insert(0,str(OUT.parent/'fechamento_agosto_v1_11/analise'))
from motor_precos import levels
lev=next(x for x in levels(ref) if x['name']=='S38.2')
def replay(events,grid):
 en,tp,sl=[lev[k+('5' if grid else '')] for k in ('entry','tp','sl')];entered=None
 for x in events:
  p=D(x['preco'])
  if entered is None:
   if p<=en:entered=x
   continue
  if p<=sl or p>=tp:
   reason='SL' if p<=sl else 'TP';return {'entrada':entered,'saida':x,'motivo':reason,'pontos_niveis':str((sl if reason=='SL' else tp)-en)}
 return {'entrada':entered,'motivo':'ABERTA'}
source=Path('/workspace/attachments/6340f23a-420a-4dcd-8f7d-09045a9bacd4/WINQ26_F_0_1min_17-06-2026_12-08-2026.csv')
bars={}
for row in csv.reader(source.read_bytes().decode('cp1252').splitlines(),delimiter=';'):
 if row[1]=='01/07/2026' and row[2][:5] in ('09:02','09:03','09:04'):bars[row[2][:5]]=[D(x.replace(',','.')) for x in row[3:7]]+[int(row[8])]
checks=[]
for minute in sorted(bars):
 a=[x for x in chron if x['hora'].startswith(minute)];b=[x for x in group if x['hora'].startswith(minute)]
 def ohlc(xs):return [xs[0]['preco'],max(x['preco'] for x in xs),min(x['preco'] for x in xs),xs[-1]['preco']]
 checks.append({'minuto':minute,'negocios':len(a),'quantidade':sum(x['quantidade'] for x in a),'ohlc_reversao':ohlc(a),'ohlc_estavel':ohlc(b),'ohlc_csv':list(map(float,bars[minute][:4])),'volume_csv':bars[minute][4],'igual_ohlc_reversao':ohlc(a)==bars[minute][:4],'igual_ohlc_estavel':ohlc(b)==bars[minute][:4],'igual_volume':sum(x['quantidade'] for x in a)==bars[minute][4]})
res={'data':'2026-07-01','contrato_informado':'WINQ26','origem':'Profit Times & Trades Replay,identidade informada pelo usuario/contexto; nao consta em cada linha','sha256':hashlib.sha256(P.read_bytes()).hexdigest(),'registros':len(r),'inicio':chron[0]['hora'],'fim':chron[-1]['hora'],'grade5_reversao':replay(chron,True),'grade5_estavel':replay(group,True),'matematico_reversao':replay(chron,False),'matematico_estavel':replay(group,False),'conferencia_m1':checks,'limite':'Dois desempates de mesmo milissegundo controlados,sem sequencia oficial. Precos nos niveis,nao fills. Nenhum registro identico removido.'}
(OUT/'REPLAY_20260701_RESULTADO.json').write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n');print(json.dumps(res,ensure_ascii=False,indent=2))
