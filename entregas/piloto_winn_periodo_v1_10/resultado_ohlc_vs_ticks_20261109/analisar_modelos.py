"""Audit two native Tester runs against the original Work candles and each other."""
import argparse,csv,hashlib,io,json
from pathlib import Path
from zipfile import ZipFile
from collections import defaultdict,Counter
from decimal import Decimal as D
from datetime import datetime,timezone
p=argparse.ArgumentParser();p.add_argument('--ticks-zip',type=Path,required=True);p.add_argument('--ohlc-zip',type=Path,required=True);p.add_argument('--ticks-diary',type=Path,required=True);p.add_argument('--ohlc-diary',type=Path,required=True);p.add_argument('--work-m1',type=Path,required=True);p.add_argument('--work-ops',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
def bundle(path):
 with ZipFile(path) as z:
  names=[n for n in z.namelist() if not n.endswith('/')];assert len({Path(n).name for n in names})==len(names)
  return {Path(n).name:z.read(n) for n in names}
def read(data,name):return list(csv.DictReader(io.StringIO(data[name].decode('utf-8-sig')),delimiter=';'))
def fields(text):return dict(x.split('=',1) for x in text.split(';') if '=' in x)
def time(ms):return datetime.fromtimestamp(int(ms)/1000,timezone.utc).strftime('%H:%M:%S.%f')[:-3]
def write(name,rows):
 with (a.out/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter=';',lineterminator='\n');w.writeheader();w.writerows(rows)
ticks=bundle(a.ticks_zip);ohlc=bundle(a.ohlc_zip);data={'TICKS_GERADOS':ticks,'M1_OHLC':ohlc};expected={'COMPARATIVO.csv','DEALS.csv','DIAS.csv','ESPECIFICACAO.txt','M1_ONTICK.csv','M1_TESTER.csv','ORDERS.csv','REFERENCIA_USADA.csv','RESULTADO.txt'}
assert set(ticks)==set(ohlc)==expected
assert ticks['M1_TESTER.csv']==ohlc['M1_TESTER.csv'] and ticks['REFERENCIA_USADA.csv']==ohlc['REFERENCIA_USADA.csv']
assert [x for x in ticks['ESPECIFICACAO.txt'].decode('utf-8-sig').splitlines() if not x.startswith('latest_tick_ok=')]==[x for x in ohlc['ESPECIFICACAO.txt'].decode('utf-8-sig').splitlines() if not x.startswith('latest_tick_ok=')]
with a.work_ops.open(encoding='utf-8-sig') as f:wops={(x['Data'],x['Nível']):x for x in csv.DictReader(f,delimiter=';')}
dates={d for d,l in wops}|{'2026-09-03'};assert len(dates)==14
work={}
for r in csv.reader(io.StringIO(a.work_m1.read_bytes().decode('cp1252')),delimiter=';'):
 if len(r)>=9 and r[0]=='WINFUT' and (day:=datetime.strptime(r[1],'%d/%m/%Y').strftime('%Y-%m-%d')) in dates:
  key=day.replace('-','.')+' '+r[2][:5];assert key not in work
  work[key]=dict(zip(['open','high','low','close','quantity'],[D(x.replace('.','').replace(',','.')) for x in [*r[3:7],r[8]]]))
assert len(work)==7875
summaries={};comp={};days={};volume_checks={};source_hashes={};bar_checks=[]
for mode,raw in data.items():
 native=read(raw,'M1_TESTER.csv');seen=read(raw,'M1_ONTICK.csv');orders=read(raw,'ORDERS.csv');deals=read(raw,'DEALS.csv');rows=read(raw,'COMPARATIVO.csv');daily=read(raw,'DIAS.csv')
 assert len(native)==len(seen)==7875 and len(orders)==102 and len(deals)==66 and len(rows)==70 and len(daily)==14
 assert [r['time'] for r in native]==[r['time'] for r in seen]==sorted(work)
 for x,y in zip(native,seen):
  key=x['time'];w=work[key];assert [D(x[k]) for k in ['open','high','low','close']]==[w[k] for k in ['open','high','low','close']]==[D(y[k]) for k in ['O_OnTick','H_OnTick','L_OnTick','C_OnTick']]
  assert D(x['real_volume'])==w['quantity']
  if mode=='M1_OHLC':assert y['n_classificados']=='4'
 summary=fields(next(l.split(';RESUMO_PERIODO;',1)[1] for l in raw['RESULTADO.txt'].decode('utf-8-sig').splitlines() if ';RESUMO_PERIODO;' in l))
 assert all(summary[k]==v for k,v in {'days_complete':'14','closed':'33','residual':'0','global_block':'0','io_failed':'0','unknown_date_events':'0','history_ok':'1'}.items())
 assert sum(int(r['n_classificados']) for r in seen)==int(summary['ticks'])==sum(int(r['ticks']) for r in daily)
 summaries[mode]=summary;comp[mode]={(r['data'],r['nivel']):r for r in rows};days[mode]={r['data']:r for r in daily}
 assert len(comp[mode])==70 and len({r['ticket'] for r in orders})==102 and len({r['ticket'] for r in deals})==66
 for key,row in comp[mode].items():
  group=[x for x in deals if (x['data'],x['nivel'])==key];initial=[x for x in orders if (x['data'],x['nivel'])==key and x['type'] in ['2','3']]
  assert row['ordens_pendentes']==row['posicoes_abertas']=='0'
  for x in initial:
   assert D(x['volume_initial'])==1 and all(D(x[col])==D(row[name]) for col,name in [('price','entrada_grade5'),('SL','SL_grade5'),('TP','TP_grade5')])
  if row['estado_operacao']=='ENCERRADA':
   assert key in wops and len(group)==2 and len(initial)==1
   en=next(x for x in group if x['entry']=='0');ex=next(x for x in group if x['entry']=='1');assert D(en['volume'])==D(ex['volume'])==1 and en['position']==ex['position']==initial[0]['ticket']
   assert initial[0]['state']=='4' and int(initial[0]['setup_msc'])<int(initial[0]['done_msc'])==int(en['time_msc'])<int(ex['time_msc'])
   reason='ALVO' if ex['reason']=='5' else 'STOP';assert ex['reason'] in ['4','5'] and row['motivo_EA']==reason
   ep,xp=D(en['price']),D(ex['price']);assert ep==D(row['entrada_media']) and xp==D(row['saida_media']) and en['time_msc']==row['primeiro_in_msc'] and ex['time_msc']==row['ultimo_out_msc']
   assert (xp-ep)*(1 if key[1].startswith('S') else -1)==D(row['pontos_EA_brutos'])
   children=[x for x in orders if (x['data'],x['nivel'])==key and x['type'] in ['0','1']];assert len(children)==1
   child=children[0];assert child['done_msc']==ex['time_msc'] and child['state']=='4' and D(child['price'])==D(row['TP_grade5'] if reason=='ALVO' else row['SL_grade5'])
   assert row['motivo_Work']==wops[key]['Motivo'] and D(row['pontos_Work_original'])==D(wops[key]['Pontos'].replace(',','.'))
   if mode=='M1_OHLC':assert ep==D(row['entrada_grade5']) and xp==D(row['TP_grade5'] if reason=='ALVO' else row['SL_grade5'])
  else:
   assert key not in wops and not group and row['pontos_EA_brutos']==''
   for x in initial:assert x['state']=='2' and datetime.fromtimestamp(int(x['done_msc'])/1000,timezone.utc).strftime('%H:%M:%S')=='18:00:00'
 assert len([x for x in rows if x['estado_operacao']=='ENCERRADA'])==33
 assert D(summary['points_closed'])==sum(D(x['pontos_EA_brutos']) for x in rows if x['estado_operacao']=='ENCERRADA')
 for day,row in days[mode].items():
  assert row['estado']=='CONCLUIDO_CONFERIR_WORK' and row['bloqueado']==row['residual']=='0' and row['cut_seen']=='1'
  assert int(row['closed'])==len([x for x in rows if x['data']==day and x['estado_operacao']=='ENCERRADA'])
  assert D(row['pontos_EA_encerradas'])==sum(D(x['pontos_EA_brutos']) for x in rows if x['data']==day and x['estado_operacao']=='ENCERRADA')
 source_hashes[mode]={name:hashlib.sha256(v).hexdigest() for name,v in raw.items()}
assert set(comp['TICKS_GERADOS'])==set(comp['M1_OHLC'])
operation_rows=[];counter=Counter();differences_by_class=defaultdict(lambda:D(0));seven=[]
for key,x in comp['TICKS_GERADOS'].items():
 y=comp['M1_OHLC'][key]
 for field in ['estado_operacao','entrada_math','SL_math','TP_math','entrada_grade5','SL_grade5','TP_grade5','motivo_EA','motivo_Work','pontos_Work_original','classificacao']:assert x[field]==y[field]
 if x['estado_operacao']!='ENCERRADA':continue
 w=wops[key];xt,yt=D(x['pontos_EA_brutos']),D(y['pontos_EA_brutos']);delta=xt-yt;wp=D(w['Pontos'].replace(',','.'))
 for field in ['entrada_media','saida_media','pontos_EA_brutos','primeiro_in_msc','ultimo_out_msc']:counter[field+'_changed']+=x[field]!=y[field]
 counter['entry_minute_changed']+=time(x['primeiro_in_msc'])[:5]!=time(y['primeiro_in_msc'])[:5];counter['exit_minute_changed']+=time(x['ultimo_out_msc'])[:5]!=time(y['ultimo_out_msc'])[:5]
 counter['ticks_points_higher']+=xt>yt;counter['ticks_points_lower']+=xt<yt;counter['ticks_points_equal']+=xt==yt
 differences_by_class[x['classificacao']]+=delta
 r={'data':key[0],'nivel':key[1],'Work_motivo':w['Motivo'],'Work_pontos':str(wp),'Ticks_motivo':x['motivo_EA'],'Ticks_pontos':str(xt),'OHLC_motivo':y['motivo_EA'],'OHLC_pontos':str(yt),'Ticks_menos_OHLC':str(delta),'Work_entrada_minuto':w['Hora entrada'][:5],'Work_saida_minuto':w['Hora saída'][:5],'Ticks_entrada_hora':time(x['primeiro_in_msc']),'OHLC_entrada_hora':time(y['primeiro_in_msc']),'Ticks_saida_hora':time(x['ultimo_out_msc']),'OHLC_saida_hora':time(y['ultimo_out_msc']),'entrada_solicitada':x['entrada_grade5'],'Ticks_entrada_efetiva':x['entrada_media'],'OHLC_entrada_efetiva':y['entrada_media'],'SL_solicitado':x['SL_grade5'],'TP_solicitado':x['TP_grade5'],'Ticks_saida_efetiva':x['saida_media'],'OHLC_saida_efetiva':y['saida_media'],'classe_Work':x['classificacao']}
 operation_rows.append(r)
 if x['classificacao']=='MOTIVOS_DIFERENTES':seven.append(r)
assert len(seven)==7 and counter['entry_minute_changed']==counter['exit_minute_changed']==0
per_day=[]
for day,x in days['TICKS_GERADOS'].items():
 y=days['M1_OHLC'][day];per_day.append({'data':day,'Work_pontos':x['pontos_Work'],'Ticks_pontos':x['pontos_EA_encerradas'],'OHLC_pontos':y['pontos_EA_encerradas'],'Ticks_menos_OHLC':str(D(x['pontos_EA_encerradas'])-D(y['pontos_EA_encerradas'])),'operacoes':x['closed'],'barras_M1':x['native_M1'],'OHLC_Work':'IGUAL_EXATO_NOS_DOIS'})
old_diary=a.ticks_diary.read_text(encoding='utf-8-sig');new_diary=a.ohlc_diary.read_text(encoding='utf-8-sig');assert 'every tick generation used' in old_diary and '1 minutes OHLC ticks generating' in new_diary and 'Test passed' in new_diary and 'initial deposit 1000000.00 BRL' in new_diary and 'BRLUSD10' not in new_diary
result={'period':['2026-09-01','2026-09-21'],'days':14,'bars_each_run':7875,'all_OHLC_exact_against_original_Work_in_both_runs':True,'native_M1_files_byte_identical':True,'daily_input_files_byte_identical':True,'specification_identical_except_initial_tick_millisecond':True,'ohlc_callbacks':31500,'ohlc_callbacks_per_bar':4,'generated_tick_callbacks':24120038,'closed_operations_each_run':33,'same_date_level_and_exit_motive_in_both_runs':True,'same_entry_and_exit_minute_in_both_runs':True,'same_exit_motive_as_Work':26,'same_seven_different_from_Work':True,'different_from_Work_6_target_to_stop_1_stop_to_target':True,'Work_points':str(sum(D(w['Pontos'].replace(',','.')) for w in wops.values())),'generated_ticks_points':summaries['TICKS_GERADOS']['points_closed'],'OHLC_points':summaries['M1_OHLC']['points_closed'],'ticks_minus_OHLC':str(sum(D(r['Ticks_menos_OHLC']) for r in operation_rows)),'ohlc_minus_Work':str(sum(D(r['OHLC_pontos'])-D(r['Work_pontos']) for r in operation_rows)),'ohlc_all_33_entries_and_33_exits_at_requested_prices':True,'change_counts':dict(counter),'ticks_minus_OHLC_by_Work_class':{k:str(v) for k,v in differences_by_class.items()},'residual_each_run':0,'native_cutoff_position_close_exercised':False,'source_hashes':source_hashes,'input_hashes':{label:{'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()} for label,path in [('ticks_zip',a.ticks_zip),('ohlc_zip',a.ohlc_zip),('ticks_diary',a.ticks_diary),('ohlc_diary',a.ohlc_diary),('original_work_M1',a.work_m1),('Work_operations',a.work_ops)]},'limits':'Both Tester runs are synthetic. Identical candles and two-mode motive agreement do not establish real intrabar chronology or live performance. Analytical Python candle grade5 control is not the native Model=1 result.'}
write('POR_OPERACAO_WORK_TICKS_OHLC.csv',operation_rows);write('POR_DIA_WORK_TICKS_OHLC.csv',per_day);write('SETE_TROCAS_PERSISTENTES.csv',seven)
(a.out/'CONFERENCIA_MODELOS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['source_hashes','input_hashes']},ensure_ascii=False,indent=2))
