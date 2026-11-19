from pathlib import Path
import csv,json,pickle,datetime,re,collections
from openpyxl import load_workbook
P=Path(__file__).parent;R=P.parents[1]
x=pickle.load(open('/workspace/work/novos_niveis_20261119/resultados.pickle','rb'));data=x['data']
requested=list(csv.DictReader((R/'entregas/estudo_fixos_tres_niveis_20261119/S23_200_500_REPLAY_5_DATAS.csv').open(encoding='utf-8-sig'),delimiter=';'))
wb=load_workbook('/workspace/dados_brutos_modelo_d/replay_profit/Novas_datas_S23_20261119.xlsx',read_only=True,data_only=True)
accepted={};audit=[];all_events={}
for s,r in zip(wb,requested):
 d=datetime.datetime.strptime(s.title[:8],'%d-%m-%y').date().isoformat();assert d==r['date'],(s.title,r)
 es=[];bad=0
 for row in s.iter_rows(min_row=2,values_only=True):
  if not any(v is not None for v in row):continue
  t,p,q=row[0],row[2],row[3]
  if not isinstance(t,str) or not re.fullmatch(r'\d\d:\d\d:\d\d\.\d{3}',t) or not isinstance(p,(int,float)) or not isinstance(q,(int,float)):
   bad+=1;continue
  assert p==int(p) and q==int(q) and p%5==0 and q>0,(s.title,row)
  es.append((t,int(p),int(q)))
 assert not bad,(s.title,bad)
 assert all(a[0]>=b[0] for a,b in zip(es,es[1:])),s.title
 es.reverse();tm=r['start'][:5];minute=[e for e in es if e[0][:5]==tm]
 b=next(v for v in data['bars'][d] if v[0][:5]==tm)
 ohlc=(minute[0][1],max(e[1] for e in minute),min(e[1] for e in minute),minute[-1][1]);qty=sum(e[2] for e in minute)
 # Same-ms open/close can be order-sensitive; compare exact canonical source OHLC.
 ok=ohlc==tuple(b[1:5]) and qty==b[5]
 row=dict(sheet=s.title,date=d,contract=r['contract'],minute=tm,rows=len(es),minute_records=len(minute),first=es[0][0],last=es[-1][0],open=ohlc[0],high=ohlc[1],low=ohlc[2],close=ohlc[3],quantity=qty,expected_OHLC=str(b[1:5]),expected_quantity=b[5],OHLC_match=ohlc==tuple(b[1:5]),quantity_match=qty==b[5],accepted=ok)
 audit.append(row);all_events[(d,tm)]=minute
 if ok:accepted[(d,tm)]=minute
 print(s.title,'OK' if ok else 'MISMATCH',qty,b[5],ohlc,b[1:5],flush=True)
with (P/'CONFERENCIA_JANELAS.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(audit[0]),delimiter=';');w.writeheader();w.writerows(audit)
cache=Path('/workspace/work/replay_s23_20261119');cache.mkdir(exist_ok=True)
(cache/'auditoria.pickle').write_bytes(pickle.dumps(dict(accepted=accepted,all_events=all_events,audit=audit)))
print('TOTAL',len(audit),'ACCEPTED',len(accepted),flush=True)
