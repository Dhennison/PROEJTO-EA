import argparse,csv,io,json,zipfile,hashlib
from pathlib import Path
from collections import Counter,defaultdict
p=argparse.ArgumentParser();p.add_argument('--fonte',type=Path,required=True);p.add_argument('--tester',type=Path,required=True);p.add_argument('--importacao',type=Path,required=True);p.add_argument('--saida',type=Path,required=True);args=p.parse_args();args.saida.mkdir(parents=True,exist_ok=True)
fields=('time','time_msc','bid','ask','last','volume','volume_real','flags')
def read(raw):
 rows=[]
 for r in csv.DictReader(io.StringIO(raw.decode('utf-8-sig')),delimiter=';'):
  r.setdefault('time',str(int(r['time_msc'])//1000))
  rows.append(tuple(int(r[k]) if k in ('time','time_msc','volume','flags') else float(r[k]) for k in fields))
 return rows
raw=args.fonte.read_bytes();assert hashlib.sha256(raw).hexdigest()=='a3acba0e6d6e8f10ab1f6c24143c63d46fa8ce9767c2f87b87220fd3c2e0ed0b'
source=read(raw)
with zipfile.ZipFile(args.tester) as z:
 assert z.testzip() is None
 event_raw=z.read('ONTICK.csv');query_raw=z.read('TESTER_COPYTICKS.csv');report=z.read('RESULTADO.txt').decode('utf-8-sig');m1=z.read('TESTER_M1.csv')
with zipfile.ZipFile(args.importacao) as z:
 baseline=read(z.read('IMPORT_READBACK.csv'));original_m1=z.read('IMPORT_M1.csv')
events=read(event_raw);query=read(query_raw)
assert len(source)==len(events)==len(baseline)==204027 and len(query)==204025
assert all(a[:-1]==b[:-1] and (a[-1]&126)==b[-1] for a,b in zip(source,baseline))
for seq in [source,events,query,baseline]:
 assert all(1793264400000<=r[1]<1793265000000 and r[0]==r[1]//1000 for r in seq)
 assert all(x[1]<=y[1] for x,y in zip(seq,seq[1:]))
source_trades=[r for r in source if r[-1]&120 and r[4]>0]
source_trade_events=[e for s,e in zip(source,events) if s[-1]&120 and s[4]>0]
assert len(source_trades)==128669
assert all(a[:-1]==b[:-1] and a[-1]&126==b[-1] for a,b in zip(source_trades,source_trade_events))
assert all(bool(e[-1]&120) for s,e in zip(source,events) if not s[-1]&120)
num_events=[dict(index=i,source=a,observed=b) for i,(a,b) in enumerate(zip(source,events)) if a[:-1]!=b[:-1]]
assert len(num_events)==1 and num_events[0]['index']==8501
sa=defaultdict(list);qa=defaultdict(list)
for i,r in enumerate(source):sa[r[1]].append((i,r))
for r in query:qa[r[1]].append(r)
assert set(sa)==set(qa)
matched=[];removed=[]
for stamp,group in sa.items():
 seen=qa[stamp];j=0
 for index,a in group:
  if j<len(seen) and a[:-1]==seen[j][:-1]:matched.append((index,a,seen[j]));j+=1
  else:removed.append(dict(index=index,source=a))
 assert j==len(seen)
assert len(removed)==2 and [r['index'] for r in removed]==[72953,72954]
assert all(r['source'][1]==1793264548680 for r in removed)
assert all(r['source'][-1]&120 for r in removed)
query_quote_promoted=sum(not(a[-1]&120) and bool(b[-1]&120) for _,a,b in matched)
assert query_quote_promoted==41877
query_true_trades=[(a,b) for _,a,b in matched if a[-1]&120]
assert len(query_true_trades)==128667 and all((a[-1]&126)==b[-1] for a,b in query_true_trades)
result={
 'input_sha256':hashlib.sha256(raw).hexdigest(),'tester_zip_sha256':hashlib.sha256(args.tester.read_bytes()).hexdigest(),
 'snapshots_sha256':{'ONTICK.csv':hashlib.sha256(event_raw).hexdigest(),'TESTER_COPYTICKS.csv':hashlib.sha256(query_raw).hexdigest()},
 'source':{'ALL':len(source),'business':len(source_trades),'quote_only':75358,'time_groups':len(sa)},
 'OnTick':{'records':len(events),'numeric_positional_differences':{f:sum(a[i]!=b[i] for a,b in zip(source,events)) for i,f in enumerate(fields[:-1])},
  'numeric_differing_records':num_events,'original_trade_records_preserved_numeric_time_order_and_public_flags':128669,
  'classified_business_by_observed_flags':sum(bool(r[-1]&120) and r[4]>0 for r in events),
  'source_quotes_acquired_business_flags':75358,'flags':dict(Counter(r[-1] for r in events))},
 'tester_ALL_query':{'records':len(query),'time_groups':len(qa),'numeric_source_subsequence':True,'numeric_source_subsequence_removed':removed,
  'matched_original_trades':128667,'source_quotes_acquired_business_flags':query_quote_promoted,'classified_business_by_query_flags':sum(bool(r[-1]&120) and r[4]>0 for r in query),
  'flags':dict(Counter(r[-1] for r in query)),
  'TRADE_selection_API_called':False,'INFO_selection_API_called':False},
 'M1_identical_to_importer_automatic_output':m1==original_m1,
 'conclusion':'INITIALIZATION_WORKS_BUT_FLAG_SEMANTICS_AND_TESTER_HISTORY_NOT_FAITHFUL;CALLBACK_TRADE_PAYLOAD_PRESERVED;PILOT_NOT_APPROVED_AS_GENERAL_EA_FEED',
 'limits':'Align by timestamp/ordered numeric payload before interpreting positional mismatches. No cause inferred for API state/flag changes or the missing group records.'}
(args.saida/'CONFERENCIA.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
