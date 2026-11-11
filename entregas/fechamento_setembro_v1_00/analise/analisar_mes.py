"""Run after receiving MES100 output. Refuse a complete monthly total on missing chunks/prices."""
import argparse,csv,json,hashlib
from pathlib import Path
from decimal import Decimal as D
from collections import Counter,defaultdict
from motor_precos import levels,replay,epoch,calendar

def read(path):
 with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter=';'))
def write(path,rows):
 if not rows:return
 with path.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter=';',lineterminator='\n');w.writeheader();w.writerows(rows)
def main():
 p=argparse.ArgumentParser();p.add_argument('--coleta',type=Path,required=True);p.add_argument('--work-m1',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 expected=Path(__file__).resolve().parents[1]/'MQL5/Files/MD_Setembro_2026_Referencias.csv'
 actual=a.coleta/'REFERENCIAS.csv';assert actual.read_bytes()==expected.read_bytes(),'Referencias diferentes do pacote auditado'
 refs=read(actual);assert len(refs)==14
 status=read(a.coleta/'BLOCOS.csv');log=(a.coleta/'RESULTADO.txt').read_text(encoding='utf-8-sig')
 assert 'END;reason=CONCLUIDO;days=14;' in log and 'io_failed=false' in log,'Coleta interrompida ou erro de IO'
 assert all(r['state']=='ESTAVEL' and int(r['attempts'])>=2 for r in status),'Blocos pendentes; nao emitir total mensal'
 work={}
 with a.work_m1.open(encoding='cp1252',newline='') as f:
  for r in csv.reader(f,delimiter=';'):
   if len(r)<9 or r[0]!='WINFUT':continue
   d,m,y=r[1].split('/');k=f'{y}.{m}.{d} '+r[2][:5]
   if not '2026.09.01'<=k[:10]<='2026.09.21':continue
   work[k]=[D(x.replace('.','').replace(',','.')) for x in r[3:7]]+[D(r[8].replace('.','').replace(',','.'))]
 baseline=read(Path(__file__).with_name('WORK_SETEMBRO.csv'));assert len(baseline)==33
 original={(r['Data'].replace('-','.'),r['Nível']):r for r in baseline}
 tester=read(Path(__file__).with_name('TESTER_JA_AUDITADO.csv'));assert len(tester)==33
 native={(r['data'].replace('-','.'),r['nivel']):r for r in tester}
 allresults=[];states=[];checks=[];issues=[];price_ok=True;all_complete=True
 for ref in refs:
  date=ref['date'];tag=date.replace('.','');ls=levels(ref);cut=epoch(ref['cut_server'])
  blocks=[r for r in status if r['date']==date];assert blocks
  cursor=date+' 09:00'
  for b in blocks:
   assert b['from_inclusive']==cursor and b['from_inclusive']<b['to_exclusive'];cursor=b['to_exclusive']
  assert cursor==date+' 18:25','Faltam blocos do dia'
  minutes=read(a.coleta/f'MINUTOS_{tag}.csv');assert len(minutes)==565
  assert [r['time'] for r in minutes]==[calendar(epoch(date+' 09:00:00')+i*60000)[:16] for i in range(565)]
  assert sum(int(r['business_n']) for r in minutes)==sum(int(b['business_n']) for b in blocks)
  nonempty={r['time']:r for r in minutes if int(r['business_n'])>0};wk={k:v for k,v in work.items() if k.startswith(date)}
  if set(nonempty)!=set(wk):price_ok=False;issues.append({'data':date,'tipo':'HORARIOS_M1','detalhe':json.dumps({'faltantes':sorted(set(wk)-set(nonempty)),'extras':sorted(set(nonempty)-set(wk))})})
  for k in sorted(set(nonempty)&set(wk)):
   r=nonempty[k];px=[D(r[x]) for x in ('open','high','low','close')];same=px==wk[k][:4];qeq=D(r['volume_real'])==wk[k][4];price_ok&=same
   checks.append({'time':k,'OHLC_igual_Work':same,'quantidade_igual_Work':qeq,'quantidade_ticks':r['volume_real'],'quantidade_Work':str(wk[k][4]),'ticks_OHLC':'|'.join(map(str,px)),'Work_OHLC':'|'.join(map(str,wk[k][:4]))})
   if not qeq:issues.append({'data':date,'tipo':'QUANTIDADE','detalhe':k+';ticks='+r['volume_real']+';Work='+str(wk[k][4])})
  eventrows=read(a.coleta/f'EVENTOS_{tag}.csv');events=[{'ord':int(r['ordinal_ALL']),'msc':int(r['time_msc']),'p':D(r['last'])} for r in eventrows]
  assert events and all(x['ord']<y['ord'] and x['msc']<=y['msc'] for x,y in zip(events,events[1:]))
  assert all(epoch(date+' 09:00:00')<=t['msc']<epoch(ref['end_server']) for t in events)
  assert all(t['p'].is_finite() and t['p']>0 for t in events)
  # Source ordinal must refer to actual raw ALL rows, not generated or duplicate events.
  assert events[-1]['ord']<=sum(int(b['ALL_n']) for b in blocks)
  minute_first={}
  for t in events:minute_first.setdefault(calendar(t['msc'])[:16],t)
  assert set(minute_first)==set(nonempty),'Falta primeiro negocio de algum minuto'
  for k,r in nonempty.items():
   assert minute_first[k]['msc']==int(r['first_msc']) and minute_first[k]['p']==D(r['open'])
  opening_ok=events[0]['p']==D(ref['open']) and calendar(events[0]['msc'])[:16]==ref['first_server'][:16]
  day_complete=opening_ok and any(t['msc']>=cut for t in events)
  if not day_complete:all_complete=False;issues.append({'data':date,'tipo':'ABERTURA_OU_CORTE','detalhe':'Dia nao aprovado para total mensal'})
  for grid in (False,True):
   for strict in (False,True):
    model=('GRADE5' if grid else 'MATEMATICA')+('_ESTRITA' if strict else '_TOQUE');results=replay(events,ls,cut,grid,strict)
    for name,s in results.items():
     w=original.get((date,name));nt=native.get((date,name));entered=s['entry_event'];exited=s['exit_event']
     if s['status']=='ABERTA':all_complete=False
     row={'data':date,'nivel':name,'cenario':model,'estado':s['status'],'dia_com_abertura_e_corte':day_complete,'hora_entrada':calendar(entered['msc']) if entered else '', 'negocio_entrada':str(entered['p']) if entered else '', 'entrada_teorica':str(s['entry_theory']) if entered else '', 'hora_saida':calendar(exited['msc']) if exited else '', 'negocio_saida':str(exited['p']) if exited else '', 'saida_teorica':str(s['exit_theory']) if exited else '', 'motivo':s['reason'] or '', 'pontos_teoricos':str(s['points']) if s['points'] is not None else '', 'Work_motivo':w['Motivo'] if w else '', 'Work_pontos':w['Pontos'] if w else '', 'Ticks_gerados_pontos':nt['Ticks_pontos'] if nt else '', 'OHLC_tester_pontos':nt['OHLC_pontos'] if nt else '', 'Work_entrada':w['Hora entrada'] if w else '', 'Work_saida':w['Hora saída'] if w else '', 'comparacao_presenca':'AMBOS' if entered and w else 'EXTRA_NA_SEQUENCIA' if entered else 'AUSENTE_NA_SEQUENCIA' if w else 'SEM_OPERACAO_EM_AMBOS'}
     allresults.append(row)
     if entered:states.append(row)
 approved=price_ok and all_complete
 monthly=[]
 for model in sorted({r['cenario'] for r in allresults}):
  rows=[r for r in states if r['cenario']==model];subtotal=sum(D(r['pontos_teoricos']) for r in rows if r['pontos_teoricos'])
  monthly.append({'cenario':model,'operacoes':len(rows),'pontos_mensais_teoricos':str(subtotal) if approved else None,'subtotal_nao_aprovado':None if approved else str(subtotal),'motivos':dict(Counter(r['motivo'] for r in rows)),'status':'COM_RESSALVAS_QUANTITATIVAS' if approved and any(i['tipo']=='QUANTIDADE' for i in issues) else 'CONFERIDO_PRECOS_NAO_EXECUCAO_REAL' if approved else 'INCOMPLETO_NAO_PUBLICAR_COMO_MES_COMPLETO'})
 result={'month':['2026.09.01','2026.09.21'],'complete_price_replay':approved,'Work_reference_points':'3839.308998','Tester_generated_deals_points':'1070','Tester_1minute_OHLC_deals_points':'565','new_price_scenarios':monthly,'minute_checks':len(checks),'price_differences':sum(not c['OHLC_igual_Work'] for c in checks),'quantity_differences':sum(not c['quantidade_igual_Work'] for c in checks),'limitations':['Exact-level conditional points, not broker fills or real PnL.','All five levels and days scanned without Work outcomes steering entries or exits.','Reduced events preserve relevant threshold categories; full raw tick arrays compared twice before export.','Cutoff uses first observed Last at/after cutoff; no queue, spread or fees.','Entry/exit in same raw business record is resolved at next business by the predeclared manual-audit protocol; raw acceptance not certified.'],'sha256_inputs':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in a.coleta.iterdir() if p.is_file()}}
 write(a.out/'TODOS_70_NIVEIS_QUATRO_CENARIOS.csv',allresults);write(a.out/'POR_OPERACAO.csv',states);write(a.out/'CANDLES_CONFERIDOS.csv',checks);write(a.out/'RESSALVAS.csv',issues)
 (a.out/'RESULTADO_MENSAL.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='sha256_inputs'},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
