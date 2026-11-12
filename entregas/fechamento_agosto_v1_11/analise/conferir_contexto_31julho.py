"""Report July31 M1 versus D1; never alter the frozen Work universe or references."""
import csv,json
from decimal import Decimal as D
from pathlib import Path

def inspect(folder,out):
 result={'date':'2026-07-31','symbol':'WIN$N','jul31_actual_session_open':'12:34:00','session_open_confirmed_by_user_and_chart':True,'aug03_collected_as_supplement_outside_original_Work_scope':True,'does_not_override_references':True}
 for frame in ('M1','D1'):
  p=folder/f'CONTEXTO_20260731_{frame}.csv'
  if not p.exists():result[frame]={'state':'ARQUIVO_NAO_RECEBIDO'};continue
  with p.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f,delimiter=';'))
  stable=[r for r in rows if r['state']=='ESTAVEL']
  if not stable:result[frame]={'state':rows[0]['state'] if rows else 'SEM_REGISTROS','rows':0};continue
  assert all(r['time'].startswith('2026.07.31') for r in stable)
  assert [r['time'] for r in stable]==sorted({r['time'] for r in stable})
  result[frame]={'state':'ESTAVEL','rows':len(stable),'first':stable[0]['time'],'last':stable[-1]['time'],'OHLC':[str(D(stable[0]['open'])),str(max(D(r['high']) for r in stable)),str(min(D(r['low']) for r in stable)),str(D(stable[-1]['close']))]}
 if all(result[x]['state']=='ESTAVEL' for x in ('M1','D1')):
  result['D1_equal_M1_aggregate']=result['D1']['OHLC']==result['M1']['OHLC']
  result['D1_OHLC_is_additional_source_not_certified_full_feed']=True
 result['interpretation']='A sessao de31/07 abriu realmente as12:34, confirmado pelo usuario/grafico. Nao classificar o inicio tardio como historico incompleto. H/L/C das351barras e contexto valido para03/08. A consultaD1 e conferencia adicional e nao bloqueia uso desse contexto. 03/08 e coletado como complemento, sem inventar resultado Work original.'
 (out/'CONTEXTO_31JUL.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');return result
