"""Confere duas rodadas nativas completas, sem publicar dados brutos."""
import argparse,csv,io,zipfile,hashlib,json,math
from pathlib import Path
from collections import Counter
p=argparse.ArgumentParser();p.add_argument('--rodada1',type=Path,required=True);p.add_argument('--rodada2',type=Path,required=True);p.add_argument('--fonte',type=Path,required=True);p.add_argument('--piloto100',type=Path,required=True);p.add_argument('--saida',type=Path,required=True);args=p.parse_args();args.saida.mkdir(parents=True,exist_ok=True)
FIELDS=('time','time_msc','bid','ask','last','volume','volume_real','flags');LO=1793264400000;HI=1793265000000
def read(raw):
 parsed=[];reader=csv.DictReader(io.StringIO(raw.decode('utf-8-sig')),delimiter=';')
 for r in reader:
  r.setdefault('time',str(int(r['time_msc'])//1000))
  x=tuple(int(r[k]) if k in ('time','time_msc','volume','flags') else float(r[k]) for k in FIELDS)
  assert all(math.isfinite(v) for v in x) and LO<=x[1]<HI and x[0]==x[1]//1000
  parsed.append(x)
 assert all(a[1]<=b[1] for a,b in zip(parsed,parsed[1:]))
 return parsed
raw=args.fonte.read_bytes();assert hashlib.sha256(raw).hexdigest()=='a3acba0e6d6e8f10ab1f6c24143c63d46fa8ce9767c2f87b87220fd3c2e0ed0b';source=read(raw)
results={};manifest={}
with zipfile.ZipFile(args.rodada1) as za,zipfile.ZipFile(args.rodada2) as zb:
 assert za.testzip() is None and zb.testzip() is None
 aa={Path(n).name:n for n in za.namelist() if not n.endswith('/')};bb={Path(n).name:n for n in zb.namelist() if not n.endswith('/')}
 assert aa.keys()==bb.keys() and len(aa)==20
 for name in aa:
  raw=za.read(aa[name]);other=zb.read(bb[name]);assert raw==other,name
  manifest[name]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'byte_identical_between_rounds':True}
  if name.endswith('.csv') and name!='TESTER_M1.csv':results[name]=read(raw)
  if name=='RESULTADO.txt':report=raw.decode('utf-8-sig')
 with zipfile.ZipFile(args.piloto100) as z:
  old_events=z.read('ONTICK.csv');old_query=z.read('TESTER_COPYTICKS.csv');old_m1=z.read('TESTER_M1.csv')
 zeroing_same={'ONTICK.csv':za.read(aa['ONTICK.csv'])==old_events,'TESTER_COPYTICKS.csv':za.read(aa['TESTER_COPYTICKS.csv'])==old_query,'TESTER_M1.csv':za.read(aa['TESTER_M1.csv'])==old_m1}
full=results['TESTER_COPYTICKS.csv'];events=results['ONTICK.csv'];trade=results['MODE_TRADE.csv'];info=results['MODE_INFO.csv'];minute=results['MINUTES_COMBINED.csv']
assert trade==[r for r in full if r[-1]&120 and r[4]>0]
assert info==[r for r in full if r[-1]&6]
assert len(trade)==170544 and len(info)==75358
source_info=[r for r in source if r[-1]&6];assert len(source_info)==len(info)
assert all(a[:-1]==b[:-1] for a,b in zip(source_info,info))
assert sum(bool(r[-1]&120) for r in info)==41877
assert full==results['ALL_AFTER_MODES.csv']
combined=[]
for m in range(10):combined.extend(results[f'MINUTE_{m}.csv'])
assert combined==minute and len(minute)==204024
assert minute==full[:2874]+full[2875:]
boundary_lost=full[2874];assert boundary_lost[1]==1793264459999 and boundary_lost[-1]==2
assert results['GROUP_ALL.csv']==results['GROUP_TRADE.csv']
assert len(results['GROUP_ALL.csv'])==3
# Exact reconstruction: prefix from stored public-flag view plus observed-event tail.
cut=len(source)-131072;prefix=[(*r[:-1],r[-1]&126) for r in source[:cut-2]]
assert cut==72955 and len(prefix)==72953
assert full==prefix+events[cut:]
assert source[cut-2][1]==source[cut][1] and source[cut-1][1]==source[cut][1]==1793264548680
assert [source[cut-2][5],source[cut-1][5]]==[8,4]
def price_path(rows):
 out=[];last=None
 for r in rows:
  if not r[-1]&120 or r[4]<=0:continue
  if r[4]!=last:out.append((r[1],r[4]));last=r[4]
 return out
ref=price_path(source);assert len(ref)==64898
paths={}
for name,rr in [('OnTick',events),('ALL',full),('TRADE',trade),('MINUTES_COMBINED',minute)]:
 path=price_path(rr);assert path==ref
 paths[name]={'changes':len(path),'first_change_times_and_Last_equal_to_source':True}
assert all(zeroing_same.values())
summary={
 'archive_sha256':{'round1':hashlib.sha256(args.rodada1.read_bytes()).hexdigest(),'round2':hashlib.sha256(args.rodada2.read_bytes()).hexdigest()},
 'files_per_round':20,'all_file_payloads_byte_identical':True,'tick_rows_verified_per_round':sum(len(r) for r in results.values()),
 'source_ALL':len(source),'source_business':sum(bool(r[-1]&120) for r in source),'source_INFO':len(source_info),
 'returned_counts':{k:len(v) for k,v in results.items()},'API_TRADE_equals_filter_of_API_ALL':True,'API_INFO_equals_filter_of_API_ALL':True,
 'MODE_INFO_numeric_time_order_equals_original_INFO':True,'INFO_records_with_business_flags':41877,
 'zeroing_comparison_vs_v100':zeroing_same,'source_vs_OnTick_numeric_differences':{k:sum(a[i]!=b[i] for a,b in zip(source,events)) for i,k in enumerate(FIELDS[:-1])},
 'minute_boundary_additional_absence':{'row':boundary_lost,'time':'09:00:59.999','source_kind':'QUOTE_ONLY','cause':'NOT_ISOLATED_POSSIBLE_BOUNDARY_SEMANTICS'},
 'full_query_reconstruction':{'source_prefix_rows':72953,'callback_tail_rows':131072,'tail_is_power_of_two':17,'callback_tail_start_index_zero_based':72955,
 'exact_in_all_eight_fields':True,'missing_in_join_indices_zero_based':[72953,72954],
 'meaning':'Exact algebraic reconstruction of observed output, NOT proof of internal cache architecture or capacity.'},
 'compressed_Last_path':paths,'compressed_path_sha256':hashlib.sha256(json.dumps(ref,separators=(',',':')).encode()).hexdigest(),
 'overall':'REPRODUCIBLE_BUT_NOT_APPROVED_AS_GENERAL_EA_DATA_SOURCE',
 'price_path_limit':'Only this ten-minute sample; equality of compressed Last does not certify raw flags/volume, M1 integrity, fills or whole-EA behavior.'}
(args.saida/'CONFERENCIA.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
(args.saida/'ARQUIVOS_SHA256.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False,indent=2))
