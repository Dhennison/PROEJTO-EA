import argparse,csv,io,json,re,hashlib
from pathlib import Path
from datetime import datetime,timezone
from decimal import Decimal as D
from collections import Counter
p=argparse.ArgumentParser();p.add_argument('--a',type=Path,required=True);p.add_argument('--b',type=Path,required=True);p.add_argument('--txt-a',type=Path,required=True);p.add_argument('--txt-b',type=Path,required=True);p.add_argument('--work',type=Path,required=True);p.add_argument('--saida',type=Path,required=True);args=p.parse_args();args.saida.mkdir(parents=True,exist_ok=True)
def read(path):
 return list(csv.DictReader(io.StringIO(path.read_bytes().decode('utf-8-sig')),delimiter=';'))
a=read(args.a);b=read(args.b);assert len(a)==0 and len(b)==30327
lo=int(datetime(2026,9,21,9,0,tzinfo=timezone.utc).timestamp()*1000);hi=lo+600000
previous=lo
for r in b:
 stamp=int(r['time_msc']);assert lo<=stamp<hi and stamp>=previous;previous=stamp
 assert all(D(r[k]).is_finite() for k in ['bid','ask','last','volume','volume_real'])
 assert D(r['last'])>0 and D(r['volume'])>0 and D(r['volume_real'])>0
flags=Counter(int(r['flags']) for r in b);assert flags=={30:30325,24:2}
for path,rows in [(args.txt_a,a),(args.txt_b,b)]:
 text=path.read_bytes().decode('cp1252');assert 'STATUS=ESTAVEL' in text
 for label,expected in [('ALL',len(rows)),('TRADE',sum(bool(int(r['flags'])&120) and D(r['last'])>0 for r in rows)),('INFO',sum(bool(int(r['flags'])&6) for r in rows))]:
  line=next(x for x in text.splitlines() if x.startswith('['+label+']'))
  assert int(re.search(r'\bn=(\d+)',line)[1])==expected and 'err=0' in line
work={}
for r in csv.reader(io.StringIO(args.work.read_bytes().decode('cp1252')),delimiter=';'):
 if len(r)>=7 and r[0]=='WINFUT' and r[1]=='21/09/2026':
  key=r[2][:5];assert key not in work
  work[key]=[D(x.replace('.','').replace(',','.')) for x in r[3:7]]
minutes=[]
for minute in range(10):
 start=lo+minute*60000;rows=[r for r in b if start<=int(r['time_msc'])<start+60000]
 values=[D(r['last']) for r in rows];ohlc=[values[0],max(values),min(values),values[-1]] if values else None
 key=f'09:{minute:02}';ref=work.get(key)
 assert (ohlc is None)==(ref is None)
 if ref is not None:assert ohlc==ref
 minutes.append(dict(minute=key,ticks=len(rows),generated_ohlc=None if ohlc is None else list(map(str,ohlc)),Work_ohlc=None if ref is None else list(map(str,ref)),status='SEM_REGISTROS_NOS_DOIS' if ref is None else 'OHLC_IGUAL'))
assert sum(m['status']=='OHLC_IGUAL' for m in minutes)==8
assert [m['ticks'] for m in minutes]==[0,0,3524,3884,3844,3992,3903,3635,3670,3875]
result={'A_ALL':len(a),'B_ALL':len(b),'B_flags':dict(flags),'B_last_equals_bid_rows':sum(D(r['last'])==D(r['bid']) for r in b),'B_ask_minus_bid':sorted({str(D(r['ask'])-D(r['bid'])) for r in b}),
 'available_candles':8,'OHLC_exact_matches':8,'individual_price_fields_matched':32,'minutes':minutes,
 'provenance':'GERACAO_SUBSTITUTA_EXPLICITA_NO_DIARIO_NAO_TICKS_REAIS','scope':'Eight candles in one ten-minute window, not all September or the whole Work period; no EA orders or ambiguity resolution.',
 'sha256':{path.name:hashlib.sha256(path.read_bytes()).hexdigest() for path in [args.a,args.b,args.txt_a,args.txt_b,args.work]}}
(args.saida/'CONFERENCIA.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))
