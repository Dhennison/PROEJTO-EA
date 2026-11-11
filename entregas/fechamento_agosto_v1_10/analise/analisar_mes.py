"""Audit August output, including both contract candidates, before publishing any total.
Price scenarios are conditional fills at the levels, not historical exchange fills.
"""
import argparse,csv,json,hashlib,re
from pathlib import Path
from decimal import Decimal as D
from collections import Counter
from motor_precos import levels,replay,epoch,calendar
ROOT=Path(__file__).resolve().parents[1]
def read(path):
 with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter=';'))
def write(path,rows):
 if not rows:return
 with path.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter=';',lineterminator='\n');w.writeheader();w.writerows(rows)
def ohlc(r):return tuple(D(r[k]) for k in ('open','high','low','close'))
def validate_inputs(folder):
 for actual,expected in [('REFERENCIAS.csv','MD_Agosto_2026_Referencias.csv'),('M1_WORK.csv','MD_Agosto_2026_M1_Work.csv')]:
  assert (folder/actual).read_bytes()==(ROOT/'MQL5/Files'/expected).read_bytes(),f'Fonte alterada: {actual}'
 refs=read(folder/'REFERENCIAS.csv');assert len(refs)==20
 return refs

def audit_contracts(folder,refs,work):
 rows=read(folder/'CONTRATOS.csv');resolved=read(folder/'REFERENCIAS_RESOLVIDAS.csv');pending=[];audit=[]
 assert len({(r['date'],r['candidate']) for r in rows})==len(rows),'Contrato duplicado'
 assert all(r['date'] in {x['date'] for x in refs} and r['candidate'] in ('WINQ26','WINV26') for r in rows)
 assert len({r['date'] for r in resolved})==len(resolved),'Referencia resolvida duplicada'
 assert all(r['date'] in {x['date'] for x in refs} for r in resolved)
 resolved_map={r['date']:r for r in resolved}
 for ref in refs:
  date=ref['date'];matches=[];stable=True;expected={k:ohlc(v) for k,v in work.items() if date+' 09:00'<=k<ref['cut_server'][:16]}
  for symbol in ('WINQ26','WINV26'):
   found=[r for r in rows if r['date']==date and r['candidate']==symbol]
   if found and found[0]['state']=='FORA_VIGENCIA':
    start,expiry=int(found[0]['start_time']),int(found[0]['expiration_time']);begin=epoch(date+' 09:00:00')//1000;finish=epoch(ref['end_server'])//1000
    assert int(found[0]['exact_before_cut'])==0 and ((expiry>0 and begin>expiry) or (start>0 and finish<=start)),'Vigencia nao exclui candidato'
    audit.append(dict(data=date,contrato=symbol,barras_antes_corte=0,diferencas='',OHLC_igual=False,estado='FORA_VIGENCIA'))
    continue
   if not found or found[0]['state']!='ESTAVEL':stable=False;continue
   r=found[0];assert int(r['attempts'])>=2 and int(r['error'])==0
   file=folder/f'M1_CONTRATO_{date.replace(".","")}_{symbol}.csv';bars=read(file)
   assert len(bars)==int(r['bars_n']) and len({b['time'] for b in bars})==len(bars)
   assert [b['time'] for b in bars]==sorted(b['time'] for b in bars)
   assert all(date+' 09:00'<=b['time']<ref['end_server'][:16] for b in bars)
   actual={b['time']:ohlc(b) for b in bars if b['time']<ref['cut_server'][:16]}
   diff=sum(expected.get(k)!=actual.get(k) for k in set(expected)|set(actual));exact=bool(expected) and diff==0
   assert int(r['source_bars_before_cut'])==len(expected) and int(r['candidate_bars_before_cut'])==len(actual)
   assert int(r['OHLC_differences_before_cut'])==diff and int(r['exact_before_cut'])==int(exact),'Declaracao de contrato nao confere'
   audit.append(dict(data=date,contrato=symbol,barras_antes_corte=len(actual),diferencas=diff,OHLC_igual=exact,estado='ESTAVEL'))
   if exact:matches.append(symbol)
  if not stable or len(matches)!=1:
   pending.append(dict(data=date,tipo='CONTRATO_NAO_UNICO_OU_NAO_ESTAVEL',detalhe='|'.join(matches)))
   assert date not in resolved_map,'Contrato sem prova unica foi usado'
   continue
  assert date in resolved_map,'Falta referencia resolvida';chosen=resolved_map[date]
  assert chosen['symbol']==matches[0]
  for k,v in ref.items():
   if k=='symbol':continue
   assert D(chosen[k])==D(v) if k in ('open','high_prev','low_prev','close_prev','adjustment') else chosen[k]==v
 return resolved_map,pending,audit

def run(folder,out):
 out.mkdir(parents=True,exist_ok=True)
 assert not (out/'RESULTADO_MENSAL.json').exists(),'Use pasta nova: nao sobrescrever fechamento anterior'
 refs=validate_inputs(folder);work={r['time']:r for r in read(folder/'M1_WORK.csv')}
 baseline=read(ROOT/'analise/WORK_AGOSTO.csv');assert len(baseline)==43 and sum(D(r['Pontos']) for r in baseline)==D('-387.164995')
 original={(r['Data'].replace('-','.'),r['Nível']):r for r in baseline};assert len(original)==43
 log=(folder/'RESULTADO.txt').read_text(encoding='utf-8-sig')
 ends=re.findall(r'^END;[^\n]+',log,re.M);assert len(ends)==1,'Coleta interrompida ou mais de um END'
 end=dict(part.split('=',1) for part in ends[0].split(';')[1:] if '=' in part)
 assert end.get('io_failed')=='false' and end.get('days')=='20' and end.get('reason') in ('CONCLUIDO','CONCLUIDO_COM_PENDENCIAS')
 resolved,pending,contracts=audit_contracts(folder,refs,work)
 status=read(folder/'BLOCOS.csv');assert len(status)==int(end['blocks'])
 assert len({(r['date'],r['from_inclusive']) for r in status})==len(status)
 assert all(r['date'] in resolved for r in status)
 assert int(end['pending_blocks'])==sum(r['state']!='ESTAVEL' for r in status)
 assert all(r['state'] in ('ESTAVEL','PENDENTE','SEM_NEGOCIOS_ABERTURA') for r in status)
 states=[];checks=[];daily=[];allresults=[];issues=[];ranges=[]
 for ref in refs:
  date=ref['date'];tag=date.replace('.','');blocks=[b for b in status if b['date']==date]
  if date not in resolved:continue
  if not blocks or any(b['state']!='ESTAVEL' for b in blocks):
   pending.append(dict(data=date,tipo='BLOCOS_INCOMPLETOS',detalhe=';'.join(b['state'] for b in blocks if b['state']!='ESTAVEL')));continue
  cursor=date+' 09:00'
  for b in blocks:
   assert b['from_inclusive']==cursor and b['from_inclusive']<b['to_exclusive']<=ref['end_server'][:16]
   assert 1<=(epoch(b['to_exclusive']+':00')-epoch(cursor+':00'))//60000<=10 and int(b['attempts'])>=2 and int(b['error'])==0
   cursor=b['to_exclusive']
  assert cursor==ref['end_server'][:16],'Blocos incompletos sem marca de pendencia'
  minutes=read(folder/f'MINUTOS_{tag}.csv');begin=epoch(date+' 09:00:00');duration=(epoch(ref['end_server'])-begin)//60000
  assert [r['time'] for r in minutes]==[calendar(begin+i*60000)[:16] for i in range(duration)]
  assert sum(int(r['business_n']) for r in minutes)==sum(int(b['business_n']) for b in blocks)
  assert all(0<=int(b['business_n'])<=int(b['ALL_n']) for b in blocks)
  for b in blocks:
   assert sum(int(r['business_n']) for r in minutes if b['from_inclusive']<=r['time']<b['to_exclusive'])==int(b['business_n'])
  nonempty={r['time']:r for r in minutes if int(r['business_n'])>0};wk={k:v for k,v in work.items() if k.startswith(date)}
  if set(nonempty)!=set(wk):
   issues.append(dict(data=date,tipo='HORARIOS_M1',detalhe=json.dumps(dict(faltantes=sorted(set(wk)-set(nonempty)),extras=sorted(set(nonempty)-set(wk))))))
   pending.append(dict(data=date,tipo='COBERTURA_M1_DIVERGENTE',detalhe='Nao fechar o mes com minutos ausentes/extras sem avaliacao'))
  day_price_diffs=[]
  for k in sorted(set(nonempty)&set(wk)):
   r=nonempty[k];same=ohlc(r)==ohlc(wk[k]);qeq=D(r['volume_real'])==D(wk[k]['volume_real'])
   checks.append(dict(time=k,OHLC_igual_Work=same,quantidade_igual_Work=qeq,ticks_OHLC='|'.join(map(str,ohlc(r))),Work_OHLC='|'.join(map(str,ohlc(wk[k]))),quantidade_ticks=r['volume_real'],quantidade_Work=wk[k]['volume_real']))
   if not same:day_price_diffs.append(k);issues.append(dict(data=date,tipo='OHLC',detalhe=k))
   if not qeq:issues.append(dict(data=date,tipo='QUANTIDADE',detalhe=k+';ticks='+r['volume_real']+';Work='+wk[k]['volume_real']))
  eventrows=read(folder/f'EVENTOS_{tag}.csv')
  assert all(int(r['flags'])&120 and D(r['volume_real']).is_finite() and D(r['volume_real'])>=0 for r in eventrows)
  events=[dict(ord=int(r['ordinal_ALL']),msc=int(r['time_msc']),p=D(r['last'])) for r in eventrows]
  assert events and events[0]['ord']>=1 and all(x['ord']<y['ord'] and x['msc']<=y['msc'] for x,y in zip(events,events[1:]))
  assert all(begin<=t['msc']<epoch(ref['end_server']) and t['p'].is_finite() and t['p']>0 for t in events)
  assert events[-1]['ord']<=sum(int(b['ALL_n']) for b in blocks)
  minute_first={}
  for t in events:
   key=calendar(t['msc'])[:16];assert key in nonempty
   r=nonempty[key];assert D(r['low'])<=t['p']<=D(r['high']) and int(r['first_msc'])<=t['msc']<=int(r['last_msc'])
   minute_first.setdefault(key,t)
  assert set(minute_first)==set(nonempty),'Falta primeiro negocio do minuto'
  for k,r in nonempty.items():assert minute_first[k]['msc']==int(r['first_msc']) and minute_first[k]['p']==D(r['open'])
  cut=epoch(ref['cut_server']);opening_ok=events[0]['p']==D(ref['open']) and calendar(events[0]['msc'])[:16]==ref['first_server'][:16]
  cutoff=next((t for t in events if t['msc']>=cut),None)
  # Do not silently turn a long gap after the cutoff into a certified 18h close.
  cutoff_ok=cutoff is not None and cutoff['msc']<cut+60000
  if not opening_ok or not cutoff_ok:pending.append(dict(data=date,tipo='ABERTURA_OU_CORTE',detalhe='Primeiro negocio divergente ou sem negocio no minuto do corte'))
  ls=levels(ref);models={}
  for grid in (False,True):
   for strict in (False,True):
    model=('GRADE5' if grid else 'MATEMATICA')+('_ESTRITA' if strict else '_TOQUE');results=replay(events,ls,cut,grid,strict);models[model]=results
    for name,s in results.items():
     w=original.get((date,name));entered=s['entry_event'];exited=s['exit_event']
     if s['status']=='ABERTA':pending.append(dict(data=date,tipo='POSICAO_NAO_ENCERRADA',detalhe=model+';'+name))
     row=dict(data=date,nivel=name,cenario=model,estado=s['status'],contrato=resolved[date]['symbol'],hora_entrada=calendar(entered['msc']) if entered else '',ordinal_entrada=entered['ord'] if entered else '',negocio_entrada=str(entered['p']) if entered else '',entrada_teorica=str(s['entry_theory']) if entered else '',hora_saida=calendar(exited['msc']) if exited else '',ordinal_saida=exited['ord'] if exited else '',negocio_saida=str(exited['p']) if exited else '',saida_teorica=str(s['exit_theory']) if exited else '',motivo=s['reason'] or '',pontos=str(s['points']) if s['points'] is not None else '',Work_motivo=w['Motivo'] if w else '',Work_pontos=w['Pontos'] if w else '',Work_entrada=w['Hora entrada'] if w else '',Work_saida=w['Hora saída'] if w else '',Work_ambiguo=w['Ambíguo'] if w else '',presenca='AMBOS' if entered and w else 'EXTRA_NOSSO' if entered else 'AUSENTE_NOSSO' if w else 'SEM_OPERACAO_EM_AMBOS')
     allresults.append(row)
     if entered:
      states.append(row)
      if exited and model=='GRADE5_TOQUE':
       inside=[k for k in day_price_diffs if calendar(entered['msc'])[:16]<=k<=calendar(exited['msc'])[:16]]
       if inside:issues.append(dict(data=date,tipo='OHLC_DURANTE_OPERACAO_PRINCIPAL',detalhe=name+';'+'|'.join(inside)))
  primary=models['GRADE5_TOQUE'];rows=[s for s in primary.values() if s['entry_event']]
  ours=sum((s['points'] for s in rows if s['points'] is not None),D(0));wp=sum((D(w['Pontos']) for (d,n),w in original.items() if d==date),D(0))
  daily.append(dict(data=date.replace('.','-'),Work_pontos=str(wp),nosso_pontos=str(ours),diferenca=str(ours-wp),operacoes_Work=sum(d==date for d,n in original),operacoes_nossas=len(rows),contrato=resolved[date]['symbol'],corte_primeiro_negocio=calendar(cutoff['msc']) if cutoff else '',ressalvas_quantidade=sum(not c['quantidade_igual_Work'] for c in checks if c['time'].startswith(date))))
  ranges.append(dict(data=date,contrato=resolved[date]['symbol'],ALL_n=sum(int(b['ALL_n']) for b in blocks),negocios=sum(int(b['business_n']) for b in blocks),eventos_reduzidos=len(events),minutos_com_negocios=len(nonempty),abertura_ok=opening_ok,corte_no_minuto_ok=cutoff_ok))
 complete=not pending and len(daily)==20
 monthly=[]
 for model in ('GRADE5_TOQUE','MATEMATICA_TOQUE','GRADE5_ESTRITA','MATEMATICA_ESTRITA'):
  rows=[r for r in states if r['cenario']==model];points=sum((D(r['pontos']) for r in rows if r['pontos']),D(0))
  monthly.append(dict(cenario=model,operacoes=len(rows),pontos=str(points) if complete else None,subtotal_nao_fechado=str(points) if not complete else None,motivos=dict(Counter(r['motivo'] for r in rows))))
 principal=monthly[0];proof=dict(month='2026-08',status='CONCLUIDO_SOBRE_ALIMENTACAO_RECEBIDA_COM_RESSALVAS' if complete and issues else 'CONCLUIDO_SOBRE_ALIMENTACAO_RECEBIDA' if complete else 'PENDENTE_NAO_COMPARAR_TOTAL',complete=complete,Work_points='-387.164995',principal_points=principal['pontos'],difference=str(D(principal['pontos'])-D('-387.164995')) if complete else None,days_analyzed=len(daily),operations_Work=43,operations_ours=principal['operacoes'],price_differences=sum(not c['OHLC_igual_Work'] for c in checks),quantity_differences=sum(not c['quantidade_igual_Work'] for c in checks),new_price_scenarios=monthly,Tester_deals='NAO_MEDIDOS_EM_AGOSTO_NAO_SAO_O_RESULTADO_PRINCIPAL',limitations=['Pontos condicionais nos niveis, um contrato, sem custos/fila/spread ou garantia de execucao.','Escolha de contrato por correspondencia unica de M1, nunca por ganho.','Duas leituras identicas conferem estabilidade local, nao completude do servidor.','Grade5/toque e o principal; demais variantes sao controles.','Saida em negocio posterior a entrada; corte pelo primeiro Last no minuto do corte.','Todas as divergencias de OHLC/quantidade sao registradas, inclusive durante operacoes.','Nenhum saldo de setembro e alterado. DD so recalculado depois de congelar agosto.'],sha256_inputs={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.iterdir() if p.is_file()})
 for name,rows in [('CONTRATOS_CONFERIDOS.csv',contracts),('PENDENCIAS.csv',pending),('TODOS_NIVEIS_QUATRO_CENARIOS.csv',allresults),('POR_OPERACAO.csv',states),('CANDLES_CONFERIDOS.csv',checks),('RESSALVAS.csv',issues),('DIARIO_PRINCIPAL.csv',daily),('COBERTURA_POR_DIA.csv',ranges)]:write(out/name,rows)
 (out/'RESULTADO_MENSAL.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n')
 message='AGOSTO/2026 — '+proof['status']+'\n'
 if complete:message+='PRINCIPAL: Work -387,164995 pontos | nosso '+proof['principal_points']+' | diferenca '+proof['difference']+'\n'
 else:message+='Nenhum total mensal nosso liberado: ver PENDENCIAS.csv.\n'
 message+='Um contrato por nivel; grade 5; toque inclusivo; pontos condicionais, sem custos/fila.\n'
 (out/'RESULTADO_PRINCIPAL.txt').write_text(message)
 return proof

def main():
 p=argparse.ArgumentParser();p.add_argument('--coleta',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 result=run(a.coleta,a.out);print(json.dumps({k:v for k,v in result.items() if k!='sha256_inputs'},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
