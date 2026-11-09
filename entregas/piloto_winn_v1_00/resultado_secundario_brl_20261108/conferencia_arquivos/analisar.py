"""Audit user-returned ZIP against original Work data. No MT5 or trading calls."""
import argparse,csv,hashlib,io,json
from pathlib import Path
from decimal import Decimal as D,localcontext
from datetime import datetime,timezone
from zipfile import ZipFile
p=argparse.ArgumentParser();p.add_argument('--zip',type=Path,required=True);p.add_argument('--work-m1',type=Path,required=True);p.add_argument('--work-ops',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
with ZipFile(a.zip) as z:
 required={'COMPARATIVO.csv','DEALS.csv','ESPECIFICACAO.txt','M1_ONTICK.csv','M1_TESTER.csv','ORDERS.csv','RESULTADO.txt'}
 assert set(z.namelist())==required
 data={name:z.read(name) for name in required}
def read(name):return list(csv.DictReader(io.StringIO(data[name].decode('utf-8-sig')),delimiter=';'))
def fields(line):return dict(x.split('=',1) for x in line.split(';') if '=' in x)
def ms(text):return int(datetime.strptime(text,'%Y.%m.%d %H:%M').replace(tzinfo=timezone.utc).timestamp()*1000)
def number(value):return D(value.replace('.','').replace(',','.'))
on=read('M1_ONTICK.csv');native=read('M1_TESTER.csv');deals=read('DEALS.csv');orders=read('ORDERS.csv');cmp=read('COMPARATIVO.csv')
work={}
for r in csv.reader(io.StringIO(a.work_m1.read_bytes().decode('cp1252')),delimiter=';'):
 if len(r)>=9 and r[0]=='WINFUT' and r[1]=='21/09/2026':
  key='2026.09.21 '+r[2][:5];assert key not in work;work[key]=dict(ohlc=list(map(number,r[3:7])),volume=number(r[8]))
assert len(on)==len(native)==len(work)==563
assert len(set(r['time'] for r in on))==len(on) and len(set(r['time'] for r in native))==len(native)
assert set(work)=={r['time'] for r in on}=={r['time'] for r in native}
checks=[]
for i,(x,y) in enumerate(zip(on,native)):
 assert x['time']==y['time'];key=x['time'];w=work[key]
 if i:assert ms(key)-ms(on[i-1]['time'])==60000
 xo=[D(x[k]) for k in ('O_OnTick','H_OnTick','L_OnTick','C_OnTick')];yo=[D(y[k]) for k in ('open','high','low','close')]
 assert xo==yo==w['ohlc'] and D(y['real_volume'])==w['volume']
 assert int(x['n_classificados'])>0
 checks.append({'time':key,'OHLC_OnTick_Work':'IGUAL_EXATO','OHLC_Tester_Work':'IGUAL_EXATO','volume_Tester_Work':'IGUAL_EXATO'})
assert on[0]['time']=='2026.09.21 09:02' and on[-1]['time']=='2026.09.21 18:24'
summary=fields(next(l.split(';RESUMO;',1)[1] for l in data['RESULTADO.txt'].decode('utf-8-sig').splitlines() if ';RESUMO;' in l))
assert sum(int(r['n_classificados']) for r in on)==int(summary['ticks'])==int(summary['classified'])==1699111
assert all(summary[k]==v for k,v in {'started':'1','blocked':'0','history_ok':'1','cut_seen':'1','requests':'5','accepted':'5','closed':'2','residual':'0','points_closed':'930.0000000000','M1_n':'563','M1_error':'0','io_failed':'0'}.items())
spec=fields(';'.join(data['ESPECIFICACAO.txt'].decode('utf-8-sig').splitlines()))
assert spec['account_currency']=='BRL' and spec['server']=='GenialInvestimentos-PRD' and spec['build']=='6295'
assert len(deals)==4 and len(orders)==7 and len(cmp)==5
assert len({r['ticket'] for r in deals})==4 and len({r['ticket'] for r in orders})==7
original=list(csv.DictReader(io.StringIO(a.work_ops.read_text(encoding='utf-8-sig')),delimiter=';'));original=[r for r in original if r['Data']=='2026-09-21'];assert len(original)==2
original={r['Nível']:r for r in original};rows=[]
for name in ['R38.2','R61.8']:
 c=next(r for r in cmp if r['nivel']==name);w=original[name];dd=[r for r in deals if r['nivel']==name]
 assert len(dd)==2;entry=next(r for r in dd if r['entry']=='0');exit=next(r for r in dd if r['entry']=='1')
 assert D(entry['volume'])==D(exit['volume'])==1 and entry['position']==exit['position'] and int(entry['time_msc'])<int(exit['time_msc'])
 assert exit['reason']=='5' and w['Motivo']=='ALVO' and not w['Ambíguo']
 initial=next(r for r in orders if r['ticket']==entry['position']);child=next(r for r in orders if r['comment'].startswith('tp ') and r['nivel']==name)
 assert initial['state']==child['state']=='4' and initial['type']=='3' and child['type']=='0'
 assert int(initial['setup_msc'])<int(initial['done_msc'])==int(entry['time_msc']) and child['done_msc']==exit['time_msc']
 assert D(initial['SL'])==D(c['SL_grade5']) and D(initial['TP'])==D(c['TP_grade5'])==D(child['price'])
 assert D(initial['price'])==D(c['entrada_grade5']) and D(c['entrada_media'])==D(entry['price']) and D(c['saida_media'])==D(exit['price'])
 assert c['estado']=='ENCERRADA' and c['ordens_pendentes']==c['posicoes_abertas']=='0'
 points=D(entry['price'])-D(exit['price']);assert points==D(c['pontos_EA_brutos'])
 with localcontext() as ctx:
  ctx.prec=40;wp=number(w['Entrada'])-number(w['Saída'])
  assert abs(wp-number(w['Pontos']))<D('0.000001')
  delta=points-wp
 assert datetime.fromtimestamp(int(entry['time_msc'])/1000,timezone.utc).strftime('%H:%M')==w['Hora entrada'][:5]
 assert datetime.fromtimestamp(int(exit['time_msc'])/1000,timezone.utc).strftime('%H:%M')==w['Hora saída'][:5]
 rows.append({'level':name,'entry_requested':c['entrada_grade5'],'SL_requested':c['SL_grade5'],'TP_requested':c['TP_grade5'],'entry_actual':entry['price'],'exit_actual':exit['price'],'EA_points':str(points),'Work_original_points_from_exported_prices':str(wp),'difference_to_Work_points':str(delta),'normalization_points':str(D(c['entrada_grade5'])-D(c['TP_grade5'])),'entry_execution_improvement':str(D(entry['price'])-D(c['entrada_grade5'])),'exit_execution_improvement':str(D(c['TP_grade5'])-D(exit['price'])),'accepted_strictly_before_fill':True,'Work_ambiguous':False,'risk_to_fixed_SL_from_actual_entry':str(D(c['SL_grade5'])-D(entry['price']))})
for name in ['S38.2','S50','S61.8']:
 c=next(r for r in cmp if r['nivel']==name);o=next(r for r in orders if r['nivel']==name)
 assert c['estado']=='SEM_EXECUCAO' and D(c['volume_in'])==D(c['volume_out'])==0
 assert c['pontos_EA_brutos']=='' and c['ordens_pendentes']==c['posicoes_abertas']=='0'
 assert o['state']=='2' and o['type']=='2' and int(o['done_msc'])==ms('2026.09.21 18:00')
 assert not any(r['nivel']==name for r in deals)
result={'date':'2026-09-21','server':'GenialInvestimentos-PRD','build':6295,'currency':'BRL','candles':563,'first_bar':on[0]['time'],'last_bar':on[-1]['time'],'internal_minute_gaps':0,'OHLC_fields_equal_per_comparison':2252,'comparisons':['OnTick vs original Work','CopyRates Tester vs original Work','OnTick vs CopyRates Tester'],'all_OHLC_exact':True,'real_volume_fields_equal':563,'native_real_volume_total':str(sum(D(r['real_volume']) for r in native)),'native_tick_volume_total':sum(int(r['tick_volume']) for r in native),'observed_classified_callbacks':1699111,'native_M1_spread_values':sorted({r['spread'] for r in native}),'closed_operations':2,'total_actual_points':str(sum(D(r['EA_points']) for r in rows)),'operations':rows,'historical_orders':7,'historical_deals':4,'support_pending_cancelled_at_18':3,'cutoff_open_position_close_exercised':False,'source_tick_sequence_exported':False,'tick_origin':'synthetic, explicitly confirmed by separately supplied Tester diary','raw_files_preserved_locally_only':True,'summary':summary,'sha256':{**{name:hashlib.sha256(content).hexdigest() for name,content in data.items()},a.zip.name:hashlib.sha256(a.zip.read_bytes()).hexdigest(),a.work_m1.name:hashlib.sha256(a.work_m1.read_bytes()).hexdigest(),a.work_ops.name:hashlib.sha256(a.work_ops.read_bytes()).hexdigest()}}
(a.out/'CONFERENCIA_COMPLETA.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
with (a.out/'CONFERENCIA_563_MINUTOS.csv').open('w',newline='') as f:
 writer=csv.DictWriter(f,fieldnames=checks[0].keys(),delimiter=';',lineterminator='\n');writer.writeheader();writer.writerows(checks)
print(json.dumps({k:v for k,v in result.items() if k not in ('sha256','summary')},ensure_ascii=False,indent=2))
