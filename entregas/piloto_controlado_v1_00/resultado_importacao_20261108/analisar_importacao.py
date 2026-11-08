"""Audita a releitura nativa e barras automáticas; os ZIPs brutos ficam locais."""
import argparse,csv,io,json,hashlib,zipfile
from pathlib import Path
from collections import Counter
p=argparse.ArgumentParser();p.add_argument('--fonte',type=Path,required=True);p.add_argument('--retorno',type=Path,required=True);p.add_argument('--saida',type=Path,required=True);args=p.parse_args()
args.saida.mkdir(parents=True,exist_ok=True)
def rows(raw):
 rr=list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig')),delimiter=';'))
 return [tuple(int(r[k]) if k in ('time','time_msc','volume','flags') else float(r[k]) for k in ('time','time_msc','bid','ask','last','volume','volume_real','flags')) for r in [dict(time=int(x['time_msc'])//1000,**x) if 'time' not in x else x for x in rr]]
raw=args.fonte.read_bytes();assert hashlib.sha256(raw).hexdigest()=='a3acba0e6d6e8f10ab1f6c24143c63d46fa8ce9767c2f87b87220fd3c2e0ed0b'
a=rows(raw)
with zipfile.ZipFile(args.retorno) as z:
 assert z.testzip() is None
 back=z.read('IMPORT_READBACK.csv');report=z.read('RESULTADO.txt').decode('utf-8-sig');b=rows(back)
 m1_raw=z.read('IMPORT_M1.csv');auto_raw=z.read('IMPORT_M1_AUTO.csv')
 bar_lines=io.StringIO(m1_raw.decode('utf-8-sig'));next(bar_lines);bars=list(csv.DictReader(bar_lines,delimiter=';'))
 assert 'M1_CONSTRUCTION_REQUESTED=0' in report and 'stable=1' in report
 assert len(a)==len(b)==204027
 differences={k:sum(x[i]!=y[i] for x,y in zip(a,b)) for i,k in enumerate(('time','time_msc','bid','ask','last','volume','volume_real','flags'))}
 public_equal=all(x[:-1]==y[:-1] and (x[-1]&126)==(y[-1]&126) for x,y in zip(a,b))
 native_mask=all(y[-1]==(x[-1]&126) for x,y in zip(a,b))
 mapping=Counter((x[-1],y[-1]) for x,y in zip(a,b))
 minutes=[]
 for i,bar in enumerate(bars):
  lo=1793264400000+i*60000;all_rows=[r for r in a if lo<=r[1]<lo+60000];trades=[r for r in all_rows if r[-1]&120 and r[4]>0]
  def ohlc(rr):return [rr[0][4],max(r[4] for r in rr),min(r[4] for r in rr),rr[-1][4]]
  actual=[float(bar['actual_'+k]) for k in 'OHLC']
  minutes.append(dict(minute=bar['minute'],source_ALL=len(all_rows),source_trades=len(trades),OHLC_ALL=ohlc(all_rows),OHLC_trades=ohlc(trades),OHLC_auto=actual,
   auto_matches_ALL=actual==ohlc(all_rows),auto_matches_trades=actual==ohlc(trades),source_trade_volume=sum(r[5] for r in trades),source_ALL_volume=sum(r[5] for r in all_rows),auto_real_volume=int(bar['actual_real_volume']),auto_tick_volume=int(bar['actual_tick_volume'])))
 assert differences==dict(time=0,time_msc=0,bid=0,ask=0,last=0,volume=0,volume_real=0,flags=204027)
 assert public_equal and native_mask
 assert len(minutes)==10 and all(m['auto_matches_ALL'] for m in minutes)
 assert sum(m['auto_matches_trades'] for m in minutes)==6
 assert all(m['auto_real_volume']==m['source_ALL_volume'] for m in minutes)
 assert sum(bool(r[-1]&120) and r[4]>0 for r in a)==sum(bool(r[-1]&120) and r[4]>0 for r in b)==128669
 result=dict(source_sha256=hashlib.sha256(raw).hexdigest(),return_zip_sha256=hashlib.sha256(args.retorno.read_bytes()).hexdigest(),readback_sha256=hashlib.sha256(back).hexdigest(),
  rows=204027,business_source=128669,business_readback=128669,positional_differences=differences,full_identity=False,all_numeric_time_order_preserved=True,documented_flag_bits_equal=public_equal,readback_flags_equal_source_and_126=native_mask,
  flag_mapping=[dict(source=k[0],readback=k[1],count=v) for k,v in sorted(mapping.items())],
  stripped_bits=dict(bit1024=sum(bool(r[-1]&1024) for r in a),bit256=sum(bool(r[-1]&256) for r in a)),
  M1_auto_equals_final=m1_raw==auto_raw,minutes=minutes,trade_volume_total=sum(m['source_trade_volume'] for m in minutes),ALL_volume_total=sum(m['source_ALL_volume'] for m in minutes),
  tick_volume_different_from_ALL_minutes=[m['minute'] for m in minutes if m['auto_tick_volume']!=m['source_ALL']],
  conclusion='Roundtrip de dados numéricos/tempo exato, bits extras removidos, M1 automático representa ALL inclusive Last/volume carregados; diagnóstico do Tester ainda pendente.')
 (args.saida/'CONFERENCIA.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:v for k,v in result.items() if k!='minutes'},ensure_ascii=False,indent=2))
