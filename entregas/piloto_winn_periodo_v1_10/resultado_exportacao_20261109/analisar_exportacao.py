"""Audit exported M1 windows against original Work sources at matching timeframes."""
import argparse,csv,io,json,hashlib
from pathlib import Path
from zipfile import ZipFile
from collections import defaultdict,Counter
from datetime import datetime,timedelta
from decimal import Decimal as D
p=argparse.ArgumentParser();p.add_argument('--zip',type=Path,required=True);p.add_argument('--diary',type=Path,required=True);p.add_argument('--work-m1',type=Path,required=True);p.add_argument('--work-m5-feb',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
def read(data):return list(csv.DictReader(io.StringIO(data.decode('utf-8-sig')),delimiter=';'))
def pn(s):return D(s.replace('.','').replace(',','.'))
def prices(r):return [D(r[k]) for k in ['open','high','low','close']]
def stamp(text):return datetime.strptime(text,'%Y.%m.%d %H:%M')
def agg(rows):
 rows=sorted(rows,key=lambda r:r['time']);return [D(rows[0]['open']),max(D(r['high']) for r in rows),min(D(r['low']) for r in rows),D(rows[-1]['close'])]
def write(name,rows):
 if not rows:return
 with (a.out/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter=';',lineterminator='\n');w.writeheader();w.writerows(rows)
with ZipFile(a.zip) as z:
 entries=[n for n in z.namelist() if not n.endswith('/')];assert len({Path(n).name for n in entries})==len(entries)
 data={Path(n).name:z.read(n) for n in entries}
status=read(data['STATUS.csv']);assert len(status)==44
native={};months=[];prior_end=None;month_data={}
for row in status:
 start=datetime.strptime(row['from_inclusive'],'%Y.%m.%d %H:%M:%S');end=datetime.strptime(row['to_exclusive'],'%Y.%m.%d %H:%M:%S');assert start<end
 if prior_end:assert start==prior_end
 prior_end=end
 file=row['file'];rows=[]
 if row['state']=='EXPORTADO_ESTAVEL':
  assert row['error']=='0' and row['attempts']=='2';rows=read(data[file]);assert len(rows)==int(row['rows']) and len(rows)>0
  for r in rows:
   key=r['time'];assert key not in native and start<=stamp(key)<end;native[key]=r
   v=prices(r);assert all(x.is_finite() and x>0 for x in v) and v[2]<=min(v[0],v[3])<=max(v[0],v[3])<=v[1]
  assert [r['time'] for r in rows]==sorted(r['time'] for r in rows)
 else:assert row['state']=='PENDENTE_SEM_DUAS_LEITURAS_VALIDAS_IGUAIS' and row['error']=='4401' and row['rows']=='-1' and row['attempts']=='10' and file==''
 month_data[start.strftime('%Y-%m')]=rows
 months.append({'janela_inicio':row['from_inclusive'],'janela_fim_exclusivo':row['to_exclusive'],'estado':row['state'],'erro':row['error'],'linhas':len(rows),'primeira_barra':rows[0]['time'] if rows else '', 'ultima_barra':rows[-1]['time'] if rows else ''})
assert len(native)==81535 and len(data)==10
assert len([r for r in status if r['state']=='EXPORTADO_ESTAVEL'])==8
assert min(native)=='2026.02.23 17:38' and max(native)=='2026.09.21 18:24'
def work_source(path):
 result={}
 for r in csv.reader(io.StringIO(path.read_bytes().decode('cp1252')),delimiter=';'):
  if len(r)>=9 and r[0]=='WINFUT':
   key=datetime.strptime(r[1]+' '+r[2],'%d/%m/%Y %H:%M:%S').strftime('%Y.%m.%d %H:%M');assert key not in result
   result[key]={'time':key,**dict(zip(['open','high','low','close'],[pn(x) for x in r[3:7]])),'quantity':pn(r[8])}
 return result
work=work_source(a.work_m1);old=work_source(a.work_m5_feb)
keys={k for k in native if k>='2026.03.01'};wk={k for k in work if k>='2026.03.01'};common=keys&wk;missing=wk-keys;extra=keys-wk
assert len(keys)==79228 and len(wk)==len(common)==79227 and len(missing)==0 and len(extra)==1
price_diff=[];quantity_diff=[]
for k in sorted(common):
 n,w=native[k],work[k];np=prices(n);wp=prices(w)
 if np!=wp:price_diff.append({'time':k,**{'MT5_'+v:str(np[i]) for i,v in enumerate(['open','high','low','close'])},**{'Work_'+v:str(wp[i]) for i,v in enumerate(['open','high','low','close'])},'campos_diferentes':'|'.join(v for i,v in enumerate(['open','high','low','close']) if np[i]!=wp[i]),'apos_corte_18h':str(k[11:]>='18:00')})
 if D(n['real_volume'])!=w['quantity']:quantity_diff.append({'time':k,'MT5_real_volume':n['real_volume'],'Work_quantity':str(w['quantity']),'MT5_menos_Work':str(D(n['real_volume'])-w['quantity'])})
assert len(price_diff)==1 and price_diff[0]['time']=='2026.03.10 18:24' and len(quantity_diff)==39 and extra=={'2026.03.10 18:25'}
closing_keys=['2026.03.10 18:24','2026.03.10 18:25'];merged=agg([native[k] for k in closing_keys]);merged_qty=sum(D(native[k]['real_volume']) for k in closing_keys)
assert merged==prices(work[closing_keys[0]]) and merged_qty==work[closing_keys[0]]['quantity']==26792
native_days=defaultdict(list);work_days=defaultdict(list)
for k in keys:native_days[k[:10]].append(native[k])
for k in wk:work_days[k[:10]].append(work[k])
assert set(native_days)==set(work_days) and len(native_days)==141
per_day=[];gaps=[]
for day in sorted(native_days):
 n=sorted(native_days[day],key=lambda r:r['time']);w=sorted(work_days[day],key=lambda r:r['time']);assert agg(n)==agg(w)
 ks=[r['time'] for r in n]
 for before,after in zip(ks,ks[1:]):
  if stamp(after)-stamp(before)!=timedelta(minutes=1):gaps.append({'data':day,'antes':before,'depois':after,'gap_compartilhado_Work':str(before in work and after in work and all((stamp(before)+timedelta(minutes=i)).strftime('%Y.%m.%d %H:%M') not in work for i in range(1,int((stamp(after)-stamp(before)).total_seconds()/60))))})
 per_day.append({'data':day,'barras_MT5':len(n),'barras_Work':len(w),'primeira_MT5':n[0]['time'],'primeira_Work':w[0]['time'],'ultima_MT5':n[-1]['time'],'ultima_Work':w[-1]['time'],'OHLC_agregado_dia':'IGUAL_EXATO_NO_CONJUNTO_FORNECIDO','diferencas_OHLC_M1':sum(r['time'].startswith(day) for r in price_diff),'diferencas_quantidade':sum(r['time'].startswith(day) for r in quantity_diff)})
# February is compared to its actual Work M5 reference, not the partial M1 context file.
buckets=defaultdict(list)
for k in sorted(native):
 if k.startswith('2026.02'):
  dt=stamp(k);key=dt.replace(minute=dt.minute//5*5).strftime('%Y.%m.%d %H:%M');buckets[key].append(native[k])
checked_m5=[];partial=[]
for k,rows in sorted(buckets.items()):
 assert k in old
 if len(rows)!=5:partial.append({'time':k,'M1_disponiveis':len(rows),'estado':'PARCIAL_NAO_APROVADO_COMO_M5_COMPLETO'});continue
 assert agg(rows)==prices(old[k]) and sum(D(r['real_volume']) for r in rows)==old[k]['quantity']
 checked_m5.append({'time':k,'M1_agrupados':5,'OHLC_Work_M5':'IGUAL_EXATO','quantidade_Work_M5':'IGUAL_EXATO'})
assert len(checked_m5)==461 and len(partial)==1 and partial[0]['time']=='2026.02.23 17:35'
log=a.diary.read_text(encoding='utf-8-sig');assert 'END;months=44;pending_months=36;rows=81535;io_failed=false' in log
spec=dict(x.split('=',1) for x in data['ESPECIFICACAO.txt'].decode('utf-8-sig').splitlines() if '=' in x)
assert spec['server']=='GenialInvestimentos-PRD' and spec['build']=='6231' and spec['tester']=='0'
result={'source':'Native terminal GenialInvestimentos-PRD, build 6231, not Tester','requested_windows':44,'exported_stable_windows':8,'pending_windows':36,'pending_error':4401,'pending_scope':['2023-02-27','2026-01-31'],'exported_rows':81535,'first_returned_M1':'2026.02.23 17:38','last_returned_M1':'2026.09.21 18:24','February_M1_rows':2307,'February_coverage':'PARTIAL','March_September':{'MT5_rows':len(keys),'Work_rows':len(wk),'common':len(common),'missing_Work_rows_in_MT5':len(missing),'extra_MT5_rows':len(extra),'exact_OHLC_rows':len(common)-len(price_diff),'different_OHLC_rows':len(price_diff),'price_difference_time':'2026.03.10 18:24','quantity_difference_rows':len(quantity_diff),'days_with_same_aggregated_OHLC':141,'intraday_price_differences_before_18':0,'closing_two_MT5_bars_aggregate_exactly_to_one_Work_bar':True,'merged_closing_quantity':str(merged_qty),'integrity_scope':'Matching supplied records is not proof that every session is complete; shared gaps and late openings remain documented.'},'February_M5_comparison':{'full_buckets_checked':len(checked_m5),'exact_OHLC_and_quantity':len(checked_m5),'partial_buckets':partial},'shared_intraday_gaps':gaps,'local_max_chart_bars_confirmed_by_user':100000,'bar_limit_diagnosis':'Local configuration insufficient for requested full M1 history; mid-session cutoff consistent with truncation. Server absence not established. Increase limit and restart only this terminal before controlled retry.','recommended_max_chart_bars':1000000,'retry_from_inclusive':'2023.02.27 00:00:00','retry_to_exclusive':'2026.03.01 00:00:00','retry_month_windows':37,'retry_scope':'36 pending windows plus incomplete February 2026. Preserve verified March-September export.','io_failed':False,'trading_or_history_mutation':False,'sha256':{**{name:hashlib.sha256(v).hexdigest() for name,v in data.items()},**{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [a.zip,a.diary,a.work_m1,a.work_m5_feb]}}}
write('COBERTURA_POR_JANELA.csv',months);write('OHLC_M1_DIVERGENTE.csv',price_diff);write('QUANTIDADE_M1_DIVERGENTE.csv',quantity_diff);write('OHLC_AGREGADO_POR_DIA.csv',per_day);write('FEVEREIRO_M5_CONFERIDO.csv',checked_m5);write('LACUNAS_COMPARTILHADAS.csv',gaps)
write('BARRA_EXTRA_MT5.csv',[{'time':k,**{key:native[k][key] for key in ['open','high','low','close','real_volume']}} for k in sorted(extra)])
(a.out/'CONFERENCIA_EXPORTACAO.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='sha256'},ensure_ascii=False,indent=2))
