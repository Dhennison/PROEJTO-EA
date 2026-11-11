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
rows=read(a.csv);assert len(rows)==414529
assert list(rows[0])==['time_msc','bid','ask','last','volume','volume_real','flags']
assert [int(r['time_msc']) for r in rows]==sorted(int(r['time_msc']) for r in rows)
trades=[];flags=Counter();groups=defaultdict(list)
for i,r in enumerate(rows):
 flags[int(r['flags'])]+=1
 if int(r['flags'])&120:
  assert D(r['last']).is_finite() and D(r['last'])>0
  trade={'csv_data_row':i+1,'time_msc':int(r['time_msc']),'last':D(r['last']),'volume_real':D(r['volume_real']),'flags':int(r['flags'])}
  trades.append(trade);groups[calendar(trade['time_msc'])[:16]].append(trade)
assert len(trades)==297486 and sum(flags.values())-len(trades)==117043
assert flags==Counter({1026:58459,1336:129946,1368:132372,1400:35168,1028:58584})
report=a.report.read_text(encoding='cp1252');assert 'STATUS=ESTAVEL' in report and 'hash_negocios ALL==TRADE: sim' in report and 'tf_n=297486' in report
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
 assert p==ohlc(native[key])==ohlc(work[key])
 candles.append({'time':key,'trade_records':len(g),'ticks_OHLC':'|'.join(map(str,p)),'WINN_OHLC':'|'.join(map(str,ohlc(native[key]))),'Work_OHLC':'|'.join(map(str,ohlc(work[key]))),'OHLC_identico':True,'quantity':str(q),'WINN_quantity':native[key]['real_volume'],'Work_quantity':str(work[key]['quantity']),'quantity_identica':q==D(native[key]['real_volume'])==work[key]['quantity']})
assert len(candles)==15
assert [c['time'] for c in candles if not c['quantity_identica']]==['2026.09.17 10:40']

operations=[r for r in read(a.operations) if r['data']=='2026-09-17' and r['nivel'] in ('S38.2','S61.8')]
assert len(operations)==2
quantity_diff=[c for c in candles if not c['quantity_identica']]
def event(t):return {'csv_data_row':t['csv_data_row'],'time_msc':t['time_msc'],'server_time':calendar(t['time_msc']),'last':str(t['last']),'flags':t['flags']}
results=[];csv_variants=[]
for operation in operations:
 earlier=[r for k,r in native.items() if '2026.09.17 09:00'<=k<'2026.09.17 10:30']
 assert earlier and min(D(r['low']) for r in earlier)>D(operation['entrada_grade5'])
 variants=[]
 for grid in ('MATEMATICA','GRADE5'):
  en=D(operation['entrada_math' if grid=='MATEMATICA' else 'entrada_grade5'])
  tp=D(operation['TP_math' if grid=='MATEMATICA' else 'TP_grade5'])
  distance=D(375 if operation['nivel']=='S38.2' else 650)
  sl=en-distance if grid=='MATEMATICA' else D(operation['SL_grade5'])
  for strict in (False,True):
   j=next(j for j,t in enumerate(trades) if t['last']<en or (not strict and t['last']==en))
   enter=trades[j]
   exitj=next(jj for jj in range(j+1,len(trades)) if trades[jj]['last']>=tp or trades[jj]['last']<=sl)
   leave=trades[exitj];kind='ALVO' if leave['last']>=tp else 'STOP'
   segment=trades[j+1:exitj+1];high=max(segment,key=lambda t:t['last'])
   prevtarget=next((t for t in reversed(trades[:j]) if t['last']>=tp),None)
   firsttargetafter=next((t for t in trades[j+1:] if t['last']>=tp),None)
   assert enter['time_msc']<leave['time_msc']
   affected=[c['time'] for c in quantity_diff if calendar(enter['time_msc'])[:16]<=c['time']<=calendar(leave['time_msc'])[:16]]
   variants.append({'grade':grid,'entrada_estrita':strict,'entrada_linha':str(en),'alvo_linha':str(tp),'stop_linha':str(sl),'entrada_observada':event(enter),'primeira_saida_por_preco':event(leave),'motivo_observado':kind,'maximo_apos_entrada_ate_primeira_saida':event(high),'ultimo_alvo_antes_entrada':event(prevtarget) if prevtarget else None,'primeiro_alvo_apos_entrada_na_janela':event(firsttargetafter) if firsttargetafter else None,'minutos_com_divergencia_quantitativa_no_intervalo_da_operacao':affected,'homologacao_integral_de_correspondencia':not affected})
   csv_variants.append({'nivel':operation['nivel'],'grade':grid,'entrada_estrita':strict,'entrada_linha':str(en),'alvo_linha':str(tp),'stop_linha':str(sl),'primeiro_negocio_entrada':calendar(enter['time_msc']),'preco_negocio_entrada':str(enter['last']),'primeira_saida':calendar(leave['time_msc']),'preco_negocio_saida':str(leave['last']),'motivo_observado':kind,'maximo_apos_entrada_ate_primeira_saida':str(high['last']),'ultimo_alvo_antes_entrada':calendar(prevtarget['time_msc']) if prevtarget else '', 'ressalva_quantidade':('|'.join(affected))})
 results.append({'nivel':operation['nivel'],'Work_points':operation['Work_pontos'],'Tester_generated_points':operation['EA_pontos'],'Tester_generated_entry_time':operation['EA_entrada_hora'],'Tester_generated_exit_time':operation['EA_saida_hora'],'variants':variants,'classification':('STOP_OBSERVADO_NAS_QUATRO_VARIANTES;RESSALVA_QUANTITATIVA_NO_MINUTO_DA_SAIDA;AUDITORIA_INTEGRAL_PENDENTE' if any(v['minutos_com_divergencia_quantitativa_no_intervalo_da_operacao'] for v in variants) else 'WORK_ALVO_NAO_SUSTENTADO_PELA_SEQUENCIA_COLETADA;STOP_PRIMEIRO_NAS_QUATRO_VARIANTES')})
result={'instrument':'WINV26','server':'GenialInvestimentos-PRD','window_server':['2026.09.17 10:30:00','2026.09.17 10:45:00'],'csv_ALL_records':len(rows),'business_records':len(trades),'quote_records_excluded':len(rows)-len(trades),'flags_counts':flags,'minute_trade_counts':[c['trade_records'] for c in candles],'minute_OHLC_match_native_WINN_and_original_Work':15,'minute_quantity_match_all_three':14,'quantity_differences':quantity_diff,'same_millisecond_records_preserved':True,'operations':results,'limits':['Price chronology describes only the received feed and does not certify fills, queue, partial execution or real PnL.','The 10:40 quantity is short by one contract against both references; do not label full correspondence as passed.','S61.8 has an observed STOP but integral feed correspondence remains pending because 10:40 includes its exit.','S38.2 exits before the minute with quantity discrepancy.','All OHLC values match both references; do not infer the missing quantity represents a known missing record or a specific price.','Strict entry is sensitivity to touch, not queue simulation.','Work original results and Tester deals are preserved.'],'sha256':{x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in [a.csv,a.report,a.native,a.work,a.operations]}}
(a.out/'CONFERENCIA.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
write('CORRESPONDENCIA_15_MINUTOS.csv',candles)
write('DIVERGENCIA_QUANTIDADE.csv',quantity_diff)
write('SEQUENCIA_OITO_VARIANTES.csv',csv_variants)
print(json.dumps({k:v for k,v in result.items() if k!='sha256'},ensure_ascii=False,indent=2))
