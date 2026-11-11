"""Audit business-tick price chronology, without assuming an executable fill.
Timestamp fields are decoded as server calendar fields; no client timezone shift.
Usage: --csv SOURCE --report SOURCE --native M1_CSV --work WORK_M1 --operations AUDITED_OPERATIONS --out OUTPUT_DIRECTORY
"""
import argparse,csv,json,hashlib
from pathlib import Path
from collections import Counter,defaultdict
from decimal import Decimal as D
from datetime import datetime,timezone
p=argparse.ArgumentParser()
for name in ('csv','report','native','work','operations','out'):p.add_argument('--'+name,type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
def read(path,encoding='utf-8-sig'):
 with path.open(encoding=encoding,newline='') as f:return list(csv.DictReader(f,delimiter=';'))
def write(name,rows):
 with (a.out/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter=';',lineterminator='\n');w.writeheader();w.writerows(rows)
def calendar(ms):return datetime.fromtimestamp(ms//1000,timezone.utc).strftime('%Y.%m.%d %H:%M:%S')+f'.{ms%1000:03d}'
def ohlc(r):return tuple(D(r[k]) for k in ('open','high','low','close'))
rows=read(a.csv);assert len(rows)==180021
assert list(rows[0])==['time_msc','bid','ask','last','volume','volume_real','flags']
assert [int(r['time_msc']) for r in rows]==sorted(int(r['time_msc']) for r in rows)
trades=[];flags=Counter();groups=defaultdict(list)
for i,r in enumerate(rows):
 flags[int(r['flags'])]+=1
 if int(r['flags'])&120:
  assert D(r['last']).is_finite() and D(r['last'])>0
  trade={'csv_data_row':i+1,'time_msc':int(r['time_msc']),'last':D(r['last']),'volume_real':D(r['volume_real']),'flags':int(r['flags'])}
  trades.append(trade);groups[calendar(trade['time_msc'])[:16]].append(trade)
assert len(trades)==125185 and sum(flags.values())-len(trades)==54836
assert flags==Counter({1026:27303,1336:62124,1368:56778,1400:6283,1028:27532,1030:1})
report=a.report.read_text(encoding='cp1252');assert 'STATUS=ESTAVEL' in report and 'hash_negocios ALL==TRADE: sim' in report and 'tf_n=125185' in report
native={r['time']:r for r in read(a.native)};work={}
with a.work.open(encoding='cp1252',newline='') as f:
 for r in csv.reader(f,delimiter=';'):
  if len(r)<9 or r[0]!='WINFUT':continue
  key=datetime.strptime(r[1]+' '+r[2],'%d/%m/%Y %H:%M:%S').strftime('%Y.%m.%d %H:%M')
  v=[D(x.replace('.','').replace(',','.')) for x in r[3:7]]
  work[key]={'time':key,**dict(zip(('open','high','low','close'),v)),'quantity':D(r[8].replace('.','').replace(',','.'))}
candles=[]
for key,g in sorted(groups.items()):
 v=[r['last'] for r in g];p=(v[0],max(v),min(v),v[-1]);q=sum(r['volume_real'] for r in g)
 assert p==ohlc(native[key])==ohlc(work[key]) and q==D(native[key]['real_volume'])==work[key]['quantity']
 candles.append({'time':key,'trade_records':len(g),'ticks_OHLC':'|'.join(map(str,p)),'WINN_OHLC':'|'.join(map(str,ohlc(native[key]))),'Work_OHLC':'|'.join(map(str,ohlc(work[key]))),'OHLC_identico':True,'quantity':str(q),'quantity_identica':True})
assert len(candles)==7
operation=next(r for r in read(a.operations) if r['data']=='2026-09-14' and r['nivel']=='S38.2')
# Earlier candles prevent overlooking a first touch before this short export.
earlier=[]
assert min(groups)=='2026.09.14 09:03'
assert not any('2026.09.14 09:00'<=k<'2026.09.14 09:03' for k in native)
assert not any('2026.09.14 09:00'<=k<'2026.09.14 09:03' for k in work)
def event(t):return {'csv_data_row':t['csv_data_row'],'time_msc':t['time_msc'],'server_time':calendar(t['time_msc']),'last':str(t['last']),'flags':t['flags']}
variants=[]
for grid in ('MATEMATICA','GRADE5'):
 en=D(operation['entrada_math' if grid=='MATEMATICA' else 'entrada_grade5'])
 tp=D(operation['TP_math' if grid=='MATEMATICA' else 'TP_grade5'])
 sl=en-D(375) if grid=='MATEMATICA' else D(operation['SL_grade5'])
 for strict in (False,True):
  j=next(j for j,t in enumerate(trades) if t['last']<en or (not strict and t['last']==en))
  enter=trades[j]
  exitj=next(jj for jj in range(j+1,len(trades)) if trades[jj]['last']>=tp or trades[jj]['last']<=sl)
  leave=trades[exitj];kind='ALVO' if leave['last']>=tp else 'STOP'
  segment=trades[j+1:exitj+1]
  high=max(segment,key=lambda t:t['last'])
  prevtarget=next((t for t in reversed(trades[:j]) if t['last']>=tp),None)
  firsttargetafter=next((t for t in trades[j+1:] if t['last']>=tp),None)
  assert kind=='ALVO' and leave['last']>=tp
  assert min(t['last'] for t in trades[j:exitj+1])>sl
  # Entries/exits below have distinct milliseconds, so tie ordering cannot invert them.
  assert enter['time_msc']<leave['time_msc']
  variants.append({'grade':grid,'entrada_estrita':strict,'entrada_linha':str(en),'alvo_linha':str(tp),'stop_linha':str(sl),'entrada_observada':event(enter),'primeira_saida_por_preco':event(leave),'motivo':kind,'maximo_apos_entrada_ate_primeira_saida':event(high),'minimo_entre_entrada_e_primeira_saida':str(min(t['last'] for t in trades[j:exitj+1])),'ultimo_alvo_antes_entrada':event(prevtarget) if prevtarget else None,'primeiro_alvo_apos_entrada_na_janela':event(firsttargetafter) if firsttargetafter else None,'Work_alvo_na_barra_sustentado':True})
result={'instrument':'WINV26','server':'GenialInvestimentos-PRD','window_server':['2026.09.14 09:00:00','2026.09.14 09:10:00'],'csv_ALL_records':len(rows),'business_records':len(trades),'quote_records_excluded':len(rows)-len(trades),'flags_counts':flags,'minute_trade_counts':[c['trade_records'] for c in candles],'minute_OHLC_and_quantity_match_native_WINN_and_original_Work':7,'first_business':event(trades[0]),'window_minutes_without_business_records_and_without_bars_in_both_references':['2026.09.14 09:00','2026.09.14 09:01','2026.09.14 09:02'],'same_millisecond_records_preserved':True,'Work_points':operation['Work_pontos'],'Tester_generated_points':operation['EA_pontos'],'Tester_generated_entry_time':operation['EA_entrada_hora'],'Tester_generated_exit_time':operation['EA_saida_hora'],'variants':variants,'classification':'WORK_SEQUENCIA_ENTRADA_ALVO_SUSTENTADA_PELA_COLETA;ALVO_PRIMEIRO_NAS_QUATRO_VARIANTES','limits':['Stability and agreement with bars do not certify the independent completeness of the upstream tick feed.','Price-touch reconstruction does not certify order acceptance, queue priority, partial fills, spread, execution price or real PnL.','Strict entry is sensitivity to touch, not a queue simulation.','Decimal math prices come from the audited operation table; precision beyond those digits does not change any crossing for this sample of five-point prices.','CSV order preserved at equal milliseconds; no timestamp deduplication.','Do not extrapolate this single operation to the other five or overwrite original Work results.'],'sha256':{x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in [a.csv,a.report,a.native,a.work,a.operations]}}
(a.out/'CONFERENCIA.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
write('CORRESPONDENCIA_7_MINUTOS.csv',candles)
write('SEQUENCIA_QUATRO_VARIANTES.csv',[{'grade':r['grade'],'entrada_estrita':r['entrada_estrita'],'entrada_linha':r['entrada_linha'],'alvo_linha':r['alvo_linha'],'stop_linha':r['stop_linha'],'primeiro_negocio_entrada':r['entrada_observada']['server_time'],'preco_entrada_negocio':r['entrada_observada']['last'],'primeira_saida':r['primeira_saida_por_preco']['server_time'],'preco_saida_negocio':r['primeira_saida_por_preco']['last'],'motivo':r['motivo'],'maximo_apos_entrada_ate_primeira_saida':r['maximo_apos_entrada_ate_primeira_saida']['last'],'minimo_entre_entrada_e_primeira_saida':r['minimo_entre_entrada_e_primeira_saida'],'ultimo_alvo_antes_entrada':r['ultimo_alvo_antes_entrada']['server_time'] if r['ultimo_alvo_antes_entrada'] else ''} for r in variants])
print(json.dumps({k:v for k,v in result.items() if k!='sha256'},ensure_ascii=False,indent=2))
