"""Compare a short tick reread with the original minute, without modifying inputs."""
import argparse,csv,json,hashlib
from pathlib import Path
from decimal import Decimal as D
from collections import Counter
p=argparse.ArgumentParser()
for n in ('csv','report','previous','native','work','out'):p.add_argument('--'+n,type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
def read(path):
 with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter=';'))
rows=read(a.csv)
with a.previous.open(encoding='utf-8-sig',newline='') as f:
 previous=[r for r in csv.DictReader(f,delimiter=';') if 1789641600000<=int(r['time_msc'])<1789641660000]
assert len(rows)==len(previous)==26519 and rows==previous
assert all(1789641600000<=int(r['time_msc'])<1789641660000 for r in rows)
trades=[r for r in rows if int(r['flags'])&120 and D(r['last']).is_finite() and D(r['last'])>0]
assert len(trades)==19368
flags=Counter(int(r['flags']) for r in rows)
assert flags==Counter({1026:3651,1028:3500,1336:7779,1368:9243,1400:2346})
report=a.report.read_text(encoding='cp1252')
assert 'STATUS=ESTAVEL' in report and 'tf_n=19368' in report and 'hash_negocios ALL==TRADE: sim' in report
prices=[D(r['last']) for r in trades];actual=(prices[0],max(prices),min(prices),prices[-1]);quantity=sum(D(r['volume_real']) for r in trades)
native=next(r for r in read(a.native) if r['time']=='2026.09.17 10:40')
with a.work.open(encoding='cp1252',newline='') as f:
 work=next(r for r in csv.reader(f,delimiter=';') if len(r)>=9 and r[0]=='WINFUT' and r[1]=='17/09/2026' and r[2]=='10:40:00')
def number(s):return D(s.replace('.','').replace(',','.'))
native_p=tuple(D(native[k]) for k in ('open','high','low','close'));work_p=tuple(number(x) for x in work[3:7])
assert actual==native_p==work_p
assert quantity==139969 and D(native['real_volume'])==number(work[8])==139970
stop=next(r for r in trades if D(r['last'])<=185315)
assert int(stop['time_msc'])==1789641637330 and D(stop['last'])==185315
result={'window_server':['2026.09.17 10:40:00','2026.09.17 10:41:00'],'rows_ALL':26519,'business_rows':19368,'quote_rows':7151,'flags':flags,'reread_equal_to_previous_minute_all_fields_and_order':True,'OHLC_ticks':list(map(str,actual)),'OHLC_identical_to_native_WINN_and_original_Work':True,'quantity_ticks':str(quantity),'quantity_native_WINN':native['real_volume'],'quantity_Work':str(number(work[8])),'difference_ticks_minus_reference':str(quantity-number(work[8])),'first_normalized_S618_stop_business':{'time_msc':int(stop['time_msc']),'server_time':'2026.09.17 10:40:37.330','last':stop['last'],'flags':stop['flags']},'classification':'CONTROLE_CONCLUIDO;DIVERGENCIA_QUANTITATIVA_REPRODUZIDA;STOP_OBSERVADO_NAO_HOMOLOGA_INTEGRIDADE_INTEGRAL','unique_new_minutes':0,'unique_new_records':0,'limits':['Exact reread proves repeatability of returned data, not independent feed completeness or cause of the discrepancy.','One missing contract in aggregate does not prove exactly one missing tick.','Do not fabricate a tick, adjust volume or certify real fills.','No further identical manual rereads are required for this control.'],'sha256':{x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in [a.csv,a.report,a.previous,a.native,a.work]}}
(a.out/'CONFERENCIA_CONTROLE.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
with (a.out/'COMPARACAO_MINUTO.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f,delimiter=';',lineterminator='\n');w.writerow(['time','ALL_registros','negocios','releitura_igual','OHLC_igual','quantidade_ticks','quantidade_WINN','quantidade_Work','diferenca']);w.writerow(['2026.09.17 10:40',26519,19368,True,True,quantity,native['real_volume'],number(work[8]),quantity-number(work[8])])
print(json.dumps({k:v for k,v in result.items() if k!='sha256'},ensure_ascii=False,indent=2))
