import csv, io, json, re, math, hashlib, zipfile, argparse
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter, defaultdict
HERE=Path(__file__).resolve().parent

def stamp(ms):return datetime.fromtimestamp(ms/1000,timezone.utc).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
def ohlc(v):return [v[0],max(v),min(v),v[-1]] if v else None
parser=argparse.ArgumentParser(description='Confere o ZIP original fornecido pelo usuário; arquivo bruto não publicado no repositório.')
parser.add_argument('--zip', type=Path, required=True)
args=parser.parse_args()
results=[];minutes=[];manifest={}
with zipfile.ZipFile(args.zip) as z:
 assert z.testzip() is None
 names=[n for n in z.namelist() if n.endswith('_ALL.csv')]
 assert len(names)==7
 for name in sorted(names):
  raw=z.read(name);txtname=name[:-8]+'.txt';txt=z.read(txtname).decode('cp1252')
  manifest[name]=hashlib.sha256(raw).hexdigest();manifest[txtname]=hashlib.sha256(z.read(txtname)).hexdigest()
  match=re.search(r'janela=(.*?) -> (.*?) \(hora',txt)
  lo,hi=[int(datetime.strptime(v,'%Y.%m.%d %H:%M:%S').replace(tzinfo=timezone.utc).timestamp()*1000) for v in match.groups()]
  rows=list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig')),delimiter=';'))
  flags=Counter();lasts=Counter();vols=Counter();biz=[];times=[];byminute=defaultdict(list);info=0;bad=0;inverted=0
  for r in rows:
   tm=int(r['time_msc']);f=int(r['flags']);lp=float(r['last']);vr=float(r['volume_real'])
   assert lo<=tm<hi
   assert all(math.isfinite(float(r[k])) for k in ['bid','ask','last','volume','volume_real'])
   times.append(tm);flags[f]+=1;lasts[lp]+=1;vols[vr]+=1
   if f&120:
    if lp>0:biz.append(r)
    else:bad+=1
   if f&6:info+=1
   inverted+=float(r['bid'])>float(r['ask'])
   byminute[tm//60000*60000].append(r)
  assert times==sorted(times)
  report_line=next(line for line in txt.splitlines() if line.startswith('[ALL]'))
  expected_n=int(re.search(r'\bn=(\d+)',report_line)[1]);expected_tf=int(re.search(r'tf_n=(\d+)',report_line)[1])
  assert len(rows)==expected_n and len(biz)+bad==expected_tf
  trline=next(line for line in txt.splitlines() if line.startswith('[TRADE]'))
  infoline=next(line for line in txt.splitlines() if line.startswith('[INFO]'))
  assert int(re.search(r'\bn=(\d+)',trline)[1])==len(biz)+bad
  assert int(re.search(r'\bn=(\d+)',infoline)[1])==info
  declared_flags={int(a):int(b) for a,b in re.findall(r'(\d+) x(\d+)',txt.split('flags:',1)[1].splitlines()[0])}
  assert dict(flags)==declared_flags
  per=[]
  for minute in range(lo,hi,60000):
   mr=byminute[minute];bs=[float(r['last']) for r in mr if int(r['flags'])&120 and float(r['last'])>0]
   per.append(len(bs))
   minutes.append(dict(file=Path(name).name,minute=stamp(minute),ALL=len(mr),business_valid=len(bs),bid_OHLC=ohlc([float(r['bid']) for r in mr]),ask_OHLC=ohlc([float(r['ask']) for r in mr]),last_OHLC=ohlc([float(r['last']) for r in mr]),business_OHLC=ohlc(bs)))
  assert per==[int(x) for x in re.search(r'neg_por_minuto\(tf\):([^\r\n]+)',txt)[1].split()]
  results.append(dict(file=Path(name).name,sha256=manifest[name],window_from=stamp(lo),window_to_exclusive=stamp(hi),tag=re.search(r'tag=([^\r\n]+)',txt)[1],stable='STATUS=ESTAVEL' in txt,ALL=len(rows),TRADE=len(biz),INFO=info,business_invalid_Last=bad,flags=dict(flags),last_positive=sum(n for p,n in lasts.items() if p>0),last_distinct=len(lasts),last_min=min(lasts),last_max=max(lasts),last_constant=next(iter(lasts)) if len(lasts)==1 else None,volume_real_distinct=len(vols),volume_real_top=vols.most_common(5),volume_real_positive=sum(n for p,n in vols.items() if p>0),last_equal_bid=sum(float(r['last'])==float(r['bid']) for r in rows),first_tick=stamp(times[0]),last_tick=stamp(times[-1]),bid_greater_ask=inverted,per_minute_business=per))
assert [r['ALL'] for r in results]==[5200,15966,29650,30350,37831,256971,36926]
assert [r['TRADE'] for r in results]==[0,0,0,0,0,162331,36926]
(HERE/'CONFERENCIA_CSV.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
(HERE/'OHLC_POR_MINUTO.json').write_text(json.dumps(minutes,ensure_ascii=False,indent=2)+'\n')
(HERE/'FONTES_SHA256.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(results,ensure_ascii=False,indent=2))
# Cross-check generated Bid against the ten native M1 bars from the earlier focal.
focal=HERE.parents[2]/'entregas/diagnostico_focal_genial_v1_02/resultado_genial_20261107/analise/OHLC_RECALCULADO.csv'
with focal.open(encoding='utf-8-sig',newline='') as f:refs={r['MinutoServidor'].replace('T',' '):r for r in csv.DictReader(f,delimiter=';')}
comparison=[]
for m in minutes:
 if not ('GTR_01_' in m['file'] or 'GTR_02_' in m['file']):continue
 key=m['minute'][:-4];ref=refs[key];bar=[float(ref['M1_'+x]) for x in 'OHLC']
 comparison.append(dict(minute=key,generated_bid=m['bid_OHLC'],server_M1=bar,equal=m['bid_OHLC']==bar,terminal_business=[float(ref['TRADE_'+x]) for x in 'OHLC']))
assert len(comparison)==10 and all(r['equal'] for r in comparison)
(HERE/'CONFRONTO_BID_GERADO_M1.json').write_text(json.dumps(comparison,ensure_ascii=False,indent=2)+'\n')
