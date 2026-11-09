"""Independent audit of PM110 results. No native trading or history mutation."""
import argparse,csv,hashlib,io,json
from pathlib import Path
from zipfile import ZipFile
from collections import defaultdict,Counter
from decimal import Decimal as D,localcontext,ROUND_FLOOR,ROUND_HALF_EVEN
from datetime import datetime,timezone
p=argparse.ArgumentParser();p.add_argument('--zip',type=Path,required=True);p.add_argument('--diary',type=Path,required=True);p.add_argument('--work-m1',type=Path,required=True);p.add_argument('--context',type=Path,required=True);p.add_argument('--work-ops',type=Path,required=True);p.add_argument('--baseline-day',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
def read(path):return list(csv.DictReader(path.open(encoding='utf-8-sig'),delimiter=';'))
def fields(line):return dict(x.split('=',1) for x in line.split(';') if '=' in x)
def pn(text):return D(text.replace('.','').replace(',','.'))
def stamp(ms):return datetime.fromtimestamp(int(ms)/1000,timezone.utc).strftime('%H:%M:%S.%f')[:-3]
def to_ms(text):return int(datetime.strptime(text,'%Y.%m.%d %H:%M').replace(tzinfo=timezone.utc).timestamp()*1000)
def write(name,rows):
 if not rows:return
 with (a.out/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter=';',lineterminator='\n');w.writeheader();w.writerows(rows)
with ZipFile(a.zip) as z:
 names={Path(n).name:n for n in z.namelist() if not n.endswith('/')};expected={'COMPARATIVO.csv','DEALS.csv','DIAS.csv','ESPECIFICACAO.txt','M1_ONTICK.csv','M1_TESTER.csv','ORDERS.csv','REFERENCIA_USADA.csv','RESULTADO.txt'}
 assert set(names)==expected;data={name:z.read(path) for name,path in names.items()}
def raw(name):return list(csv.DictReader(io.StringIO(data[name].decode('utf-8-sig')),delimiter=';'))
context={r['Data']:r for r in read(a.context)};work_ops={(r['Data'],r['Nível']):r for r in read(a.work_ops)}
assert len(context)==14 and len(work_ops)==33
original=defaultdict(dict)
for r in csv.reader(io.StringIO(a.work_m1.read_bytes().decode('cp1252')),delimiter=';'):
 if len(r)>=9 and r[0]=='WINFUT':
  date=datetime.strptime(r[1],'%d/%m/%Y').strftime('%Y-%m-%d')
  if date in context or date in {r['PregaoAnterior'] for r in context.values()}:
   key=date.replace('-','.')+' '+r[2][:5];assert key not in original[date]
   original[date][key]={'time':key,'open':pn(r[3]),'high':pn(r[4]),'low':pn(r[5]),'close':pn(r[6]),'quantity':pn(r[8])}
work={key:r for date in context for key,r in original[date].items()}
on=raw('M1_ONTICK.csv');native=raw('M1_TESTER.csv');cmp=raw('COMPARATIVO.csv');days=raw('DIAS.csv');deals=raw('DEALS.csv');orders=raw('ORDERS.csv');used=raw('REFERENCIA_USADA.csv')
assert len(on)==len(native)==len(work)==7875
assert len({r['time'] for r in on})==len(on) and len({r['time'] for r in native})==len(native)
assert [r['time'] for r in on]==sorted(work)==[r['time'] for r in native]
bars_audit=[]
for x,y in zip(on,native):
 w=work[x['time']];xo=[D(x[k]) for k in ['O_OnTick','H_OnTick','L_OnTick','C_OnTick']];yo=[D(y[k]) for k in ['open','high','low','close']];wo=[w[k] for k in ['open','high','low','close']]
 assert xo==yo==wo and D(y['real_volume'])==w['quantity']
 bars_audit.append({'time':x['time'],'OHLC_OnTick_Work':'IGUAL_EXATO','OHLC_Tester_Work':'IGUAL_EXATO','volume_Tester_Work':'IGUAL_EXATO'})
assert len(cmp)==70 and len(days)==len(used)==14 and len(deals)==66 and len(orders)==102
assert len({r['ticket'] for r in deals})==len(deals) and len({r['ticket'] for r in orders})==len(orders)
for r in used:
 c=context[r['data']];assert r['pregao_anterior']==c['PregaoAnterior']
 for key,name in [('abertura_Work','Abertura'),('Hprev','MaximaAnterior'),('Lprev','MinimaAnterior'),('Cprev','FechamentoAnterior'),('ajuste_Work','Ajuste')]:assert D(r[key])==D(c[name])
 previous=sorted(original[c['PregaoAnterior']].values(),key=lambda r:r['time']);assert max(x['high'] for x in previous)==D(c['MaximaAnterior']) and min(x['low'] for x in previous)==D(c['MinimaAnterior']) and previous[-1]['close']==D(c['FechamentoAnterior'])
 assert r['primeira_barra']==c['PrimeiraBarra'][:5] and r['corte']==c['Corte'][:5]
levels=['S38.2','S50','S61.8','R38.2','R61.8'];stops=[D(375),D(375),D(650),D(375),D(450)]
def calculate(c):
 with localcontext() as ctx:
  ctx.prec=50;o,h,l,cl,adj=map(D,[c['Abertura'],c['MaximaAnterior'],c['MinimaAnterior'],c['FechamentoAnterior'],c['Ajuste']]);pp=(h+l+cl)/3;r2=o+2*abs(l-pp);s2=o-2*abs(h-pp)
  rr={p:adj+(r2-adj)*D(p) for p in ['.236','.382','.5','.618']};ss={p:adj+(s2-adj)*D(p) for p in ['.236','.382','.5','.618']}
  en=[ss['.382'],ss['.5'],ss['.618'],rr['.382'],rr['.618']];tp=[(ss['.382']+ss['.236'])/2,ss['.382'],ss['.5'],rr['.236'],(rr['.618']+rr['.5'])/2]
  return [{'entry':en[k],'sl':en[k]-stops[k] if k<3 else en[k]+stops[k],'tp':tp[k],'eligible':(o>=en[k] if k<3 else o<=en[k]) and not(adj<=s2 if k<3 else adj>=r2)} for k in range(5)]
def round5(v):return ((v/5+D('.5')).to_integral_value(rounding=ROUND_FLOOR))*5
def candle_replay(date,level,prices):
 if not prices['eligible']:return None
 buy=level.startswith('S');en,sl,tp=prices['entry'],prices['sl'],prices['tp'];entry_time=None
 for key in sorted(original[date]):
  bar=original[date][key];time=key[11:]
  if time>=context[date]['Corte'][:5]:break
  if entry_time is None:
   if not(bar['low']<=en if buy else bar['high']>=en):continue
   entry_time=time
  hit_sl=bar['low']<=sl if buy else bar['high']>=sl;hit_tp=bar['high']>=tp if buy else bar['low']<=tp
  if hit_sl or hit_tp:
   reason='STOP' if hit_sl else 'ALVO';exit_price=sl if hit_sl else tp
   return {'entry_minute':entry_time,'exit_minute':time,'reason':reason,'points':(exit_price-en)*(1 if buy else -1),'ambiguous':hit_sl and hit_tp}
 if entry_time is None:return None
 bar=original[date][date.replace('-','.')+' '+context[date]['Corte'][:5]]
 return {'entry_minute':entry_time,'exit_minute':context[date]['Corte'][:5],'reason':'HORARIO','points':(bar['open']-en)*(1 if buy else -1),'ambiguous':False}
calculated={date:calculate(c) for date,c in context.items()};eligible=0;operations=[];different=[];normalized_model=[];keys=set()
order_by_id={r['ticket']:r for r in orders};daily_stats=defaultdict(lambda:Counter())
for row in cmp:
 date,level=row['data'],row['nivel'];key=(date,level);assert key not in keys;keys.add(key);k=levels.index(level);expected=calculated[date][k];eligible+=expected['eligible']
 for column,field in [('entrada_math','entry'),('SL_math','sl'),('TP_math','tp')]:assert abs(D(row[column])-expected[field])<D('0.000000001')
 for column,field in [('entrada_grade5','entry'),('SL_grade5','sl'),('TP_grade5','tp')]:assert D(row[column])==round5(expected[field])
 theory=candle_replay(date,level,expected);normalized=candle_replay(date,level,{**expected,**{field:D(row[col]) for field,col in [('entry','entrada_grade5'),('sl','SL_grade5'),('tp','TP_grade5')]}})
 assert bool(theory)==(key in work_ops)
 initial=[r for r in orders if r['data']==date and r['nivel']==level and r['type'] in ['2','3']]
 assert len(initial)==int(expected['eligible'])
 if initial:
  initial=initial[0];assert initial['type']==('2' if k<3 else '3') and D(initial['volume_initial'])==1 and int(initial['setup_msc'])==to_ms(date.replace('-','.')+' '+context[date]['PrimeiraBarra'][:5])
  for col,field in [('price','entrada_grade5'),('SL','SL_grade5'),('TP','TP_grade5')]:assert D(initial[col])==D(row[field])
 assert row['ordens_pendentes']==row['posicoes_abertas']=='0'
 group=[r for r in deals if r['data']==date and r['nivel']==level]
 if key not in work_ops:
  assert not group and row['estado_operacao']=='SEM_EXECUCAO' and row['classificacao']=='SEM_OPERACAO_NOS_DOIS' and row['pontos_EA_brutos']==''
  if initial:assert initial['state']=='2' and int(initial['done_msc'])==to_ms(date.replace('-','.')+' '+context[date]['Corte'][:5])
  continue
 assert normalized is not None and theory is not None;w=work_ops[key];assert theory['reason']==w['Motivo'] and theory['entry_minute']==w['Hora entrada'][:5] and theory['exit_minute']==w['Hora saída'][:5] and abs(theory['points']-D(w['Pontos'].replace(',','.')))<D('.000001')
 assert bool(w['Ambíguo'].strip())==theory['ambiguous']==False
 assert len(group)==2;entry=next(r for r in group if r['entry']=='0');exit=next(r for r in group if r['entry']=='1')
 assert D(entry['volume'])==D(exit['volume'])==1 and entry['position']==exit['position']==initial['ticket'] and initial['state']=='4'
 assert int(initial['setup_msc'])<int(entry['time_msc'])==int(initial['done_msc'])<int(exit['time_msc'])
 assert exit['reason'] in ['4','5'];reason='STOP' if exit['reason']=='4' else 'ALVO';assert reason==row['motivo_EA']
 child=[r for r in orders if r['data']==date and r['nivel']==level and r['type'] in ['0','1']];assert len(child)==1;child=child[0]
 assert child['state']=='4' and child['type']==('1' if k<3 else '0') and child['done_msc']==exit['time_msc']
 assert D(child['price'])==D(row['SL_grade5'] if reason=='STOP' else row['TP_grade5'])
 ep,xp=D(entry['price']),D(exit['price']);points=(xp-ep)*(1 if k<3 else -1);assert points==D(row['pontos_EA_brutos']) and ep==D(row['entrada_media']) and xp==D(row['saida_media'])
 original_points=D(w['Pontos'].replace(',','.'));same=reason==w['Motivo'];assert row['classificacao']==('MESMO_MOTIVO_CONFERIR_PRECOS' if same else 'MOTIVOS_DIFERENTES')
 if same:
  norm=(D(row['TP_grade5'])-D(row['entrada_grade5']))*(1 if k<3 else -1) if reason=='ALVO' else (D(row['SL_grade5'])-D(row['entrada_grade5']))*(1 if k<3 else -1)
  assert norm==D(row['referencia_grade5_mesmo_motivo']) and points-norm==D(row['diferenca_execucao']) and norm-original_points==D(row['diferenca_normalizacao'])
 else:assert row['referencia_grade5_mesmo_motivo']==row['diferenca_normalizacao']==row['diferenca_execucao']==''
 actual_entry,actual_exit=stamp(entry['time_msc']),stamp(exit['time_msc']);entry_bar=original[date][date.replace('-','.')+' '+actual_entry[:5]]
 target_already_at_open=(entry_bar['open']>=expected['tp'] if k<3 else entry_bar['open']<=expected['tp'])
 work_samebar=w['Hora entrada'][:5]==w['Hora saída'][:5]
 cause='MESMO_MOTIVO_PRECOS_DIFERENTES'
 if not same:
  cause='GRADE5_MUDA_ENTRADA_E_MOTIVO_NO_REPLAY_CANDLE' if normalized['reason']!=w['Motivo'] else 'SEQUENCIA_ENTRADA_ALVO_NA_BARRA_NAO_DETERMINADA_PELO_OHLC'
 r={'data':date,'nivel':level,'Work_motivo':w['Motivo'],'Work_pontos':str(original_points),'Work_entrada_minuto':w['Hora entrada'][:5],'Work_saida_minuto':w['Hora saída'][:5],'EA_motivo':reason,'EA_pontos':str(points),'EA_entrada_hora':actual_entry,'EA_saida_hora':actual_exit,'entrada_math':row['entrada_math'],'entrada_grade5':row['entrada_grade5'],'entrada_efetiva':str(ep),'SL_grade5':row['SL_grade5'],'TP_math':row['TP_math'],'TP_grade5':row['TP_grade5'],'saida_efetiva':str(xp),'diferenca_EA_Work':str(points-original_points),'mesmo_motivo':str(same),'Work_ambiguo_original':'NAO','Work_alvo_na_barra_entrada':str(work_samebar and w['Motivo']=='ALVO'),'alvo_ja_alcancado_na_abertura_barra_entrada_EA':str(target_already_at_open),'entry_bar_open':str(entry_bar['open']),'entry_bar_high':str(entry_bar['high']),'entry_bar_low':str(entry_bar['low']),'entry_bar_close':str(entry_bar['close']),'hipotese_ou_controle':cause,'candle_grade5_entrada_minuto':normalized['entry_minute'],'candle_grade5_saida_minuto':normalized['exit_minute'],'candle_grade5_motivo':normalized['reason'],'candle_grade5_pontos':str(normalized['points'])}
 operations.append(r);normalized_model.append({'data':date,'nivel':level,**{k:str(v) for k,v in normalized.items()},'scope':'CONTROLE_TEORICO_OHLC_MESMA_REGRA_WORK_GRADE5_NAO_EA_NEM_MERCADO'})
 if not same:different.append(r)
 daily_stats[date]['closed']+=1;daily_stats[date]['points']+=points;daily_stats[date]['same_motive']+=same;daily_stats[date]['different_motive']+=not same
assert eligible==69 and len(operations)==33 and len(different)==7
assert set((r['data'],r['nivel']) for r in operations)==set(work_ops)
assert sum(int(r['n_classificados']) for r in on)==24120038
per_day=[]
for row in days:
 date=row['data'];original_day=sorted(original[date]);assert len(original_day)==int(context[date]['BarrasM1Hoje'])
 for x,y in zip(original_day,original_day[1:]):assert to_ms(y)-to_ms(x)==60000
 assert row['estado']=='CONCLUIDO_CONFERIR_WORK' and all(row[k]==v for k,v in {'started':'1','bloqueado':'0','cut_seen':'1','M1_differences':'0','residual':'0'}.items())
 assert int(row['observed_M1'])==int(row['native_M1'])==int(row['expected_M1'])==len(original_day)
 stat=daily_stats[date];wp=sum(D(r['Pontos'].replace(',','.')) for (d,l),r in work_ops.items() if d==date)
 assert stat['closed']==int(row['closed'])==int(row['operacoes_Work']) and stat['points']==D(row['pontos_EA_encerradas']) and wp==D(row['pontos_Work'])
 assert int(row['requests'])==int(row['accepted'])==sum(calculated[date][k]['eligible'] for k in range(5))
 per_day.append({'data':date,'barras_M1':len(original_day),'OHLC_Work':'IGUAL_EXATO','operacoes_Work':row['operacoes_Work'],'pontos_Work':str(wp),'operacoes_EA':row['closed'],'pontos_EA':str(stat['points']),'diferenca_EA_Work':str(stat['points']-wp),'mesmo_motivo':stat['same_motive'],'motivo_diferente':stat['different_motive'],'residual':0})
diary=a.diary.read_text(encoding='utf-8-sig');assert 'initial deposit 1000000.00 BRL' in diary and '2026.09.01 00:00 - 2026.09.22 00:00  no real ticks, every tick generation used' in diary and 'Test passed' in diary and 'BRLUSD10' not in diary
summary=fields(next(l.split(';RESUMO_PERIODO;',1)[1] for l in data['RESULTADO.txt'].decode('utf-8-sig').splitlines() if ';RESUMO_PERIODO;' in l))
assert summary['days_complete']=='14' and summary['closed']=='33' and summary['residual']=='0' and summary['global_block']==summary['io_failed']==summary['unknown_date_events']=='0'
assert D(summary['points_closed'])==sum(D(r['EA_pontos']) for r in operations)==1070
same=[r for r in cmp if r['classificacao']=='MESMO_MOTIVO_CONFERIR_PRECOS']
regression={}
if a.baseline_day:
 for name in ['M1_ONTICK.csv','M1_TESTER.csv']:
  old=read(a.baseline_day/name);new=[r for r in raw(name) if r['time'].startswith('2026.09.21 ')];assert old==new;regression[name]='IDENTICO_CAMPO_A_CAMPO_563_LINHAS'
result={'period':['2026-09-01','2026-09-21'],'date_count':14,'original_Work_M1_rows':7875,'exact_OHLC_fields_each_pair':31500,'OHLC_comparisons_all_exact':['OnTick vs original Work','CopyRates vs original Work','OnTick vs CopyRates'],'native_M1_real_volume_exact_rows':7875,'callbacks':24120038,'native_M1_tick_volume_sum':sum(int(r['tick_volume']) for r in native),'native_M1_real_volume_sum':sum(int(r['real_volume']) for r in native),'Work_operations':33,'EA_closed':33,'same_date_level_keys':True,'same_exit_motive':26,'different_exit_motive':7,'Work_target_to_EA_stop':6,'Work_stop_to_EA_target':1,'Work_original_ambiguous':0,'EA_exit_motives':dict(Counter(r['EA_motivo'] for r in operations)),'Work_exit_motives':dict(Counter(r['Work_motivo'] for r in operations)),'Work_points':str(sum(D(r['Work_pontos']) for r in operations)),'EA_points':str(sum(D(r['EA_pontos']) for r in operations)),'difference_EA_Work':str(sum(D(r['diferenca_EA_Work']) for r in operations)),'same_motive_subgroup':{'Work_points':str(sum(D(r['pontos_Work_original']) for r in same)),'same_motive_grade5_points':str(sum(D(r['referencia_grade5_mesmo_motivo']) for r in same)),'EA_points':str(sum(D(r['pontos_EA_brutos']) for r in same)),'normalization_arithmetic_difference':str(sum(D(r['diferenca_normalizacao']) for r in same)),'execution_arithmetic_difference':str(sum(D(r['diferenca_execucao']) for r in same))},'different_motive_subgroup':{'Work_points':str(sum(D(r['Work_pontos']) for r in different)),'EA_points':str(sum(D(r['EA_pontos']) for r in different))},'normalized_candle_counterfactual':{'points':str(sum(D(r['points']) for r in normalized_model)),'changed_entry_minutes':sum(r['entry_minute']!=work_ops[r['data'],r['nivel']]['Hora entrada'][:5] for r in normalized_model),'changed_exit_minutes':sum(r['exit_minute']!=work_ops[r['data'],r['nivel']]['Hora saída'][:5] for r in normalized_model),'changed_exit_motives_from_Work':sum(r['reason']!=work_ops[r['data'],r['nivel']]['Motivo'] for r in normalized_model),'scope':'Same OHLC convention as Work with grade5 prices, no Bid/Ask spread, queue or fill modelling. Analytical control, not EA backtest/performance.'},'initial_orders':69,'filled_entry_orders':33,'native_exit_market_orders':33,'cancelled_pending_orders_at_cutoff':36,'orders_total':102,'deals_total':66,'volume_per_deal':1,'residual':0,'native_cutoff_position_close_exercised':False,'zero_operation_day':'2026-09-03','native_single_day_regression':regression,'tick_origin':'SYNTHETIC_FALLBACK_EXPLICIT_IN_DIARY','summary':summary,'sha256':{**{name:hashlib.sha256(content).hexdigest() for name,content in data.items()},**{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [a.zip,a.diary,a.work_m1,a.context,a.work_ops]}}}
write('POR_DIA_CONFERIDO.csv',per_day);write('POR_OPERACAO_CONFERIDO.csv',operations);write('SETE_TROCAS_DE_MOTIVO.csv',different);write('CONTROLE_TEORICO_CANDLE_GRADE5.csv',normalized_model);write('CONFERENCIA_7875_MINUTOS.csv',bars_audit)
(a.out/'CONFERENCIA_COMPLETA.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['sha256','summary']},ensure_ascii=False,indent=2))
