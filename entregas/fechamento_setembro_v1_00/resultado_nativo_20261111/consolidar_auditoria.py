"""Audit completed collection separately from strict OHLC approval; no missing data imputed."""
import argparse,csv,json,hashlib,sys
from pathlib import Path
from decimal import Decimal as D
from collections import Counter,defaultdict
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'analise'))
from motor_precos import levels,calendar
p=argparse.ArgumentParser()
for n in ('coleta','resultado','diary','manifest','out'):p.add_argument('--'+n,type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
def read(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter=';'))
def write(name,rows):
 if not rows:return
 with (a.out/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter=';',lineterminator='\n');w.writeheader();w.writerows(rows)
refs=read(a.coleta/'REFERENCIAS.csv');assert len(refs)==14
blocks=read(a.coleta/'BLOCOS.csv');assert len(blocks)==798 and all(r['state']=='ESTAVEL' and r['attempts']=='2' and r['error']=='0' for r in blocks)
log=(a.coleta/'RESULTADO.txt').read_text(encoding='utf-8-sig');assert 'END;reason=CONCLUIDO;days=14;blocks=798;pending_blocks=0;io_failed=false' in log
external=a.diary.read_text(encoding='utf-8-sig');assert 'MES100;END;reason=CONCLUIDO;days=14;blocks=798;pending_blocks=0;io_failed=false' in external
rows=read(a.resultado/'TODOS_70_NIVEIS_QUATRO_CENARIOS.csv');assert len(rows)==280 and all(r['dia_com_abertura_e_corte']=='True' and r['estado']!='ABERTA' for r in rows)
base=Path(__file__).resolve().parents[1];native=read(base/'analise/TESTER_JA_AUDITADO.csv');assert len(native)==33
native={(r['data'].replace('-','.'),r['nivel']):r for r in native}
checks=read(a.resultado/'CANDLES_CONFERIDOS.csv');assert len(checks)==7875
px=[r for r in checks if r['OHLC_igual_Work']=='False'];qty=[r for r in checks if r['quantidade_igual_Work']=='False']
assert len(px)==24 and len(qty)==40
workbars=defaultdict(dict);tapebars=defaultdict(dict)
for c in checks:workbars[c['time'][:10]][c['time']]=tuple(map(D,c['Work_OHLC'].split('|')))
for ref in refs:
 date=ref['date'];mins=read(a.coleta/f"MINUTOS_{date.replace('.','')}.csv")
 for r in mins:
  if int(r['business_n'])>0:tapebars[date][r['time']]=tuple(D(r[k]) for k in ('open','high','low','close'))
 assert set(tapebars[date])==set(workbars[date])
refmap={r['date']:r for r in refs};critical=[];pxrows=[]
for c in px:
 date=c['time'][:10];ref=refmap[date];inside=c['time']<ref['cut_server'][:16];tp=tuple(map(D,c['ticks_OHLC'].split('|')));wp=tuple(map(D,c['Work_OHLC'].split('|')));changed=[]
 if inside:
  for l in levels(ref):
   for k in ('entry','sl','tp','entry5','sl5','tp5'):
    for i,field in enumerate('OHLC'):
     if ((tp[i]>l[k])-(tp[i]<l[k]))!=((wp[i]>l[k])-(wp[i]<l[k])):changed.append(l['name']+':'+k+':'+field)
 pxrows.append({'time':c['time'],'antes_corte':inside,'campos_diferentes':'|'.join(v for i,v in enumerate('OHLC') if tp[i]!=wp[i]),'ticks_OHLC':c['ticks_OHLC'],'Work_OHLC':c['Work_OHLC'],'muda_relacao_com_nivel':'|'.join(changed)})
 critical.extend(changed)
# Deterministic replay at candle resolution on each actual OHLC set, same frozen context.
def candle(ref,bars,grid):
 result={};cut=ref['cut_server'][:16]
 for l in levels(ref):
  if not l['eligible']:result[l['name']]=None;continue
  en=l['entry5' if grid else 'entry'];sl=l['sl5' if grid else 'sl'];tp=l['tp5' if grid else 'tp'];entry=None;reason=None;out=None;when=None
  for time,(o,h,lo,c) in sorted(bars.items()):
   if time>=cut:break
   if entry is None:
    if not (lo<=en if l['buy'] else h>=en):continue
    entry=time
   stop=lo<=sl if l['buy'] else h>=sl;target=h>=tp if l['buy'] else lo<=tp
   if stop or target:reason='STOP' if stop else 'ALVO';out=sl if stop else tp;when=time;break
  if entry is None:result[l['name']]=None;continue
  if reason is None:reason='CORTE_LAST';when=cut;out=bars[cut][0]
  points=((out-en) if l['buy'] else (en-out)).quantize(D('.000001'))
  result[l['name']]=(entry,when,reason,points)
 return result
candlecheck=[]
for ref in refs:
 for grid in (False,True):
  w=candle(ref,workbars[ref['date']],grid);t=candle(ref,tapebars[ref['date']],grid)
  for name in w:
   candlecheck.append({'data':ref['date'],'nivel':name,'grade5':grid,'resultado_por_candle_igual':w[name]==t[name],'operacao_Work_candles':str(w[name]),'operacao_ticks_candles':str(t[name])})
assert all(r['resultado_por_candle_igual'] for r in candlecheck)
candle_totals={}
for grid in (False,True):
 values=[v for ref in refs for v in candle(ref,workbars[ref['date']],grid).values() if v]
 candle_totals['GRADE5' if grid else 'MATEMATICA']=str(sum(v[3] for v in values))
assert candle_totals=={'MATEMATICA':'3839.308998','GRADE5':'4490.000000'}
scenarios=sorted({r['cenario'] for r in rows});ops={m:{(r['data'],r['nivel']):r for r in rows if r['cenario']==m and r['estado']=='ENCERRADA'} for m in scenarios}
assert all(len(v)==33 and set(v)==set(native) for v in ops.values())
totals={m:sum(D(r['pontos_teoricos']) for r in rr.values()) for m,rr in ops.items()}
assert totals=={'GRADE5_ESTRITA':D(730),'GRADE5_TOQUE':D(1380),'MATEMATICA_ESTRITA':D('720.536666'),'MATEMATICA_TOQUE':D('720.536666')}
comparison=[];samebar=[];days=[];tape_grade=ops['GRADE5_TOQUE'];tape_math=ops['MATEMATICA_TOQUE'];tape_strict=ops['GRADE5_ESTRITA']
for key,g in tape_grade.items():
 m=tape_math[key];s=tape_strict[key];n=native[key]
 active_price=[c['time'] for c in px if c['time'][:10]==key[0] and min(m['hora_entrada'][:16],g['hora_entrada'][:16])<=c['time']<=max(m['hora_saida'][:16],g['hora_saida'][:16])]
 active_qty=[c['time'] for c in qty if c['time'][:10]==key[0] and min(m['hora_entrada'][:16],g['hora_entrada'][:16])<=c['time']<=max(m['hora_saida'][:16],g['hora_saida'][:16])]
 comparison.append({'data':key[0],'nivel':key[1],'Work_motivo':m['Work_motivo'],'Work_pontos':m['Work_pontos'].replace(',','.'),'sequencia_math_motivo':m['motivo'],'sequencia_math_pontos':m['pontos_teoricos'],'sequencia_grade5_motivo':g['motivo'],'sequencia_grade5_pontos':g['pontos_teoricos'],'grade5_estrita_motivo':s['motivo'],'grade5_estrita_pontos':s['pontos_teoricos'],'Tester_ticks_motivo':n['Ticks_motivo'],'Tester_ticks_pontos':n['Ticks_pontos'],'Tester_OHLC_motivo':n['OHLC_motivo'],'Tester_OHLC_pontos':n['OHLC_pontos'],'Work_entrada':m['Work_entrada'],'Work_saida':m['Work_saida'],'sequencia_math_entrada':m['hora_entrada'],'sequencia_math_saida':m['hora_saida'],'sequencia_grade5_entrada':g['hora_entrada'],'sequencia_grade5_saida':g['hora_saida'],'primeiro_negocio_entrada_grade5':g['negocio_entrada'],'entrada_teorica_grade5':g['entrada_teorica'],'primeiro_negocio_saida_grade5':g['negocio_saida'],'saida_teorica_grade5':g['saida_teorica'],'candles_preco_divergente_entre_entrada_saida':'|'.join(active_price),'candles_volume_divergente_entre_entrada_saida':'|'.join(active_qty)})
 if m['Work_motivo']=='ALVO' and m['Work_entrada']==m['Work_saida']:
  samebar.append({'data':key[0],'nivel':key[1],'Work_entrada_saida':m['Work_entrada'],'sequencia_entrada':m['hora_entrada'],'sequencia_saida':m['hora_saida'],'sequencia_motivo':m['motivo'],'resultado_cronologia':'STOP_PRIMEIRO' if m['motivo']=='STOP' else 'ALVO_MESMA_BARRA' if m['hora_entrada'][:16]==m['hora_saida'][:16] else 'ALVO_EM_BARRA_POSTERIOR'})
for ref in refs:
 date=ref['date'];keys=[k for k in tape_math if k[0]==date]
 days.append({'data':date,'operacoes':len(keys),'Work_pontos':str(sum(D(tape_math[k]['Work_pontos'].replace(',','.')) for k in keys)),'sequencia_math':str(sum(D(tape_math[k]['pontos_teoricos']) for k in keys)),'sequencia_grade5':str(sum(D(tape_grade[k]['pontos_teoricos']) for k in keys)),'sequencia_grade5_estrita':str(sum(D(tape_strict[k]['pontos_teoricos']) for k in keys)),'Tester_ticks':str(sum(D(native[k]['Ticks_pontos']) for k in keys)),'Tester_OHLC':str(sum(D(native[k]['OHLC_pontos']) for k in keys)),'candles_OHLC_diferentes':sum(c['time'].startswith(date) for c in px),'candles_volume_diferente':sum(c['time'].startswith(date) for c in qty)})
assert not any(r['candles_preco_divergente_entre_entrada_saida'] for r in comparison)
assert [(r['data'],r['nivel']) for r in comparison if r['candles_volume_divergente_entre_entrada_saida']]==[('2026.09.17','S61.8')]
assert sum(D(d['Work_pontos']) for d in days)==D('3839.308998')
assert sum(D(d['Tester_ticks']) for d in days)==1070 and sum(D(d['Tester_OHLC']) for d in days)==565
same_model=[k for k,g in tape_grade.items() if g['motivo']==native[k]['Ticks_motivo']];different_model=[k for k in tape_grade if k not in same_model]
assert different_model==[('2026.09.14','S38.2')]
fills_delta=sum(D(native[k]['Ticks_pontos'])-D(tape_grade[k]['pontos_teoricos']) for k in same_model)
assert fills_delta==465
assert Counter(s['resultado_cronologia'] for s in samebar)==Counter({'STOP_PRIMEIRO':5,'ALVO_EM_BARRA_POSTERIOR':6,'ALVO_MESMA_BARRA':1})
manifest=json.loads(a.manifest.read_text());assert len(manifest)==14
result={'collection_complete':True,'comparison_strict_ohlc_approved':False,'days':14,'blocks':798,'two_exact_reads_each_block':True,'blocks_pending':0,'ALL_records':sum(int(r['ALL_n']) for r in blocks),'business_records':sum(int(r['business_n']) for r in blocks),'retained_events':sum(sum(1 for _ in p.open())-1 for p in a.coleta.glob('EVENTOS_*.csv')),'states_per_variant':70,'closed_per_variant':33,'no_extra_or_missing_operations_any_variant':True,'no_open_positions_at_end':True,'all_openings_and_cutoffs_observed':True,'Work_points':'3839.308998','observed_conditional_price_totals':{m:str(v) for m,v in totals.items()},'Tester_generated_deals_points':'1070','Tester_OHLC_deals_points':'565','candle_replay_on_Work_and_received_tick_aggregates':{'identical_states_all_70_each_price_grid':True,'mathematical_total':candle_totals['MATEMATICA'],'grade5_total':candle_totals['GRADE5'],'scope':'Same full-candle Work convention. Does not prove tick completeness.'},'quality':{'Work_M1':7875,'same_timestamps':True,'OHLC_equal':7875-len(px),'OHLC_different':len(px),'OHLC_different_1824':sum(r['time'].endswith('18:24') for r in px),'OHLC_different_before_cut':sum(r['antes_corte'] for r in pxrows),'quantity_equal':7875-len(qty),'quantity_different':len(qty),'changed_relation_with_strategy_thresholds_at_intraday_different_bars':critical,'operations_with_price_different_bar_between_entry_and_exit':0,'operations_with_quantity_different_bar_between_entry_and_exit':[['2026.09.17','S61.8']]},'same_entry_bar_targets_Work':{'count':12,'actual_price_sequence_classification':dict(Counter(s['resultado_cronologia'] for s in samebar))},'grade_touch_vs_strict':{'only_changed_points_key':['2026.09.01','R38.2'],'difference_points':'650','grade_touch':'ALVO +275','grade_strict':'STOP -375'},'Tester_vs_grade_touch':{'same_motive':32,'different_motive':1,'different_key':['2026.09.14','S38.2'],'difference_on_changed_motive':'-775','arithmetic_price_fill_difference_on_other_32':str(fills_delta),'total_difference':'-310'},'cutoff_position_close_exercised':False,'conclusion':'Full-period observed conditional price totals computed. Strict source-price equality failed on 24 bars; do not certify as identical feed or real PnL. No new collection requested to conceal these exceptions.','sha256_data':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in a.coleta.iterdir() if p.is_file()},'zip_manifest':manifest}
write('COMPARATIVO_COMPLETO_33_OPERACOES.csv',comparison);write('RESUMO_14_PREGOES.csv',days);write('ALVOS_MESMA_BARRA_WORK_12_CASOS.csv',samebar);write('DIFERENCAS_OHLC_E_LIMIARES.csv',pxrows);write('CONTROLE_DAS_24_DIFERENCAS.csv',candlecheck)
(a.out/'CONFERENCIA_COMPLETA_OBSERVADA.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('sha256_data','zip_manifest')},ensure_ascii=False,indent=2))
