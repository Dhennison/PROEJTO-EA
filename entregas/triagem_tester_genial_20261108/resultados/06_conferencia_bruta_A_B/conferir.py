import argparse,csv,io,json,hashlib,zipfile,math,re
from collections import Counter
from pathlib import Path
from datetime import datetime,timezone
p=argparse.ArgumentParser();p.add_argument('--a',type=Path,required=True);p.add_argument('--b',type=Path,required=True);p.add_argument('--anterior',type=Path,required=True);args=p.parse_args()
out=Path(__file__).resolve().parent
cols=['time_msc','bid','ask','last','volume','volume_real','flags']
def read(raw):
 rr=list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig')),delimiter=';'))
 rows=[]
 for r in rr:
  row=tuple(int(r[k]) if k in ['time_msc','volume','flags'] else float(r[k]) for k in cols)
  assert 1793264400000<=row[0]<1793265000000
  assert all(math.isfinite(v) for v in row)
  rows.append(row)
 assert [r[0] for r in rows]==sorted(r[0] for r in rows)
 return rows
with zipfile.ZipFile(args.anterior) as z:
 name=next(n for n in z.namelist() if '762822359_ALL.csv' in n)
 raw0=z.read(name)
rawa=args.a.read_bytes();rawb=args.b.read_bytes();a=read(rawa);b=read(rawb);before=read(raw0)
def stat(rows,raw):
 business=[r for r in rows if r[6]&120 and r[3]>0]
 return dict(ALL=len(rows),negocios_flags_Last=len(business),INFO=sum(bool(r[6]&6) for r in rows),flags=dict(Counter(r[6] for r in rows)),Last_positivo=sum(r[3]>0 for r in rows),volume_real_positivo=sum(r[5]>0 for r in rows),primeiro_msc=rows[0][0],ultimo_msc=rows[-1][0],Last_negocios_min=min((r[3] for r in business),default=None),Last_negocios_max=max((r[3] for r in business),default=None),bid_maior_ask=sum(r[1]>r[2] for r in rows),sha256=hashlib.sha256(raw).hexdigest())
assert len(b)==len(before)==36926 and len(a)==204027
s={name:stat(rows,raw) for name,rows,raw in [('A',a,rawa),('B_antes',before,raw0),('B_apos',b,rawb)]}
assert s['A']['negocios_flags_Last']==128669 and s['B_apos']['negocios_flags_Last']==0
compare={k:sum(x[i]!=y[i] for x,y in zip(before,b)) for i,k in enumerate(cols)}
s['comparacao_posicional_B']={'linhas':len(b),'linhas_diferentes_por_campo':compare,'mesmos_time_bid_ask':all(x[:3]==y[:3] for x,y in zip(before,b))}
per=[]
for minute in range(10):
 lo=1793264400000+minute*60000;hi=lo+60000
 ar=[r for r in a if lo<=r[0]<hi and r[6]&120 and r[3]>0]
 br=[r for r in b if lo<=r[0]<hi]
 def oh(rs,idx):
  v=[r[idx] for r in rs];return [v[0],max(v),min(v),v[-1]] if v else None
 av=oh(ar,3);bv=oh(br,1)
 per.append(dict(minuto=f'09:{minute:02}',A_negocios=len(ar),B_registros=len(br),A_Last_OHLC=av,B_bid_OHLC=bv,OHLC_iguais=av==bv,volume_real_A_negocios=sum(r[5] for r in ar)))
s['minutos']=per
s['minutos_OHLC_iguais']=sum(r['OHLC_iguais'] for r in per)
s['limite']='Dados do snapshot; não prova causa interna, integridade da sessão ou execução de ordens. Timestamps tratados como hora do servidor, sem certificação de fuso.'
(out/'CONFERENCIA.json').write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(s,ensure_ascii=False,indent=2))
