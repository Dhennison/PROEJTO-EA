"""Separate per-level search validates chronological transitions, not an MT5 fill test."""
import argparse,csv,json
from pathlib import Path
from decimal import Decimal as D
from motor_precos import levels,epoch,calendar

def read(path):
 with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter=';'))
def validate(folder,audit):
 refs=read(folder/'REFERENCIAS.csv');observed=read(audit/'TODOS_NIVEIS_QUATRO_CENARIOS.csv');lookup={(r['data'],r['nivel'],r['cenario']):r for r in observed};assert len(lookup)==len(observed)
 count=0;cut_cases=0
 for ref in refs:
  tag=ref['date'].replace('.','');file=folder/f'EVENTOS_{tag}.csv'
  if not file.exists():continue
  events=[(int(r['ordinal_ALL']),int(r['time_msc']),D(r['last'])) for r in read(file)];cut=epoch(ref['cut_server'])
  for grid in (False,True):
   for strict in (False,True):
    scenario=('GRADE5' if grid else 'MATEMATICA')+('_ESTRITA' if strict else '_TOQUE')
    for level in levels(ref):
     key=(ref['date'],level['name'],scenario)
     if key not in lookup:continue
     actual=lookup[key];count+=1;en=level['entry5' if grid else 'entry'];tp=level['tp5' if grid else 'tp'];sl=level['sl5' if grid else 'sl'];buy=level['buy']
     if not level['eligible']:assert actual['estado']=='INELEGIVEL' and not actual['hora_entrada'];continue
     start=next((i for i,(_,ms,p) in enumerate(events) if ms<cut and ((p<en if strict else p<=en) if buy else (p>en if strict else p>=en))),None)
     if start is None:assert actual['estado']=='SEM_TOQUE' and not actual['hora_entrada'];continue
     order,ms,price=events[start];assert int(actual['ordinal_entrada'])==order and actual['hora_entrada']==calendar(ms) and D(actual['entrada_teorica'])==en and D(actual['negocio_entrada'])==price
     end=None
     for order,ms,price in events[start+1:]:
      if ms>=cut:end=(order,ms,price,price,'CORTE_LAST');break
      if price<=sl if buy else price>=sl:end=(order,ms,price,sl,'STOP');break
      if price>=tp if buy else price<=tp:end=(order,ms,price,tp,'ALVO');break
     if end is None:assert actual['estado']=='ABERTA' and not actual['hora_saida'];continue
     order,ms,price,exit_price,reason=end;points=((exit_price-en) if buy else (en-exit_price)).quantize(D('.000001'))
     assert actual['estado']=='ENCERRADA' and actual['motivo']==reason and D(actual['pontos'])==points and int(actual['ordinal_saida'])==order and actual['hora_saida']==calendar(ms) and D(actual['negocio_saida'])==price and D(actual['saida_teorica'])==exit_price
     cut_cases+=reason=='CORTE_LAST'
 result=dict(states_checked=count,cut_cases=cut_cases,passed=True,scope='Independent per-level chronological search. Conditional level fills; not queue or native MT5 execution.')
 (audit/'VALIDACAO_INDEPENDENTE.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--coleta',type=Path,required=True);p.add_argument('--analise',type=Path,required=True);a=p.parse_args();print(json.dumps(validate(a.coleta,a.analise),indent=2))
