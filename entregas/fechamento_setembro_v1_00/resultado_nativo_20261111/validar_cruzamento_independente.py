"""Independent per-level search over returned events, compared with stream state engine."""
import csv,json,sys,argparse
from decimal import Decimal as D
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'analise'))
from motor_precos import levels,epoch,calendar
p=argparse.ArgumentParser();p.add_argument('--coleta',type=Path,required=True);p.add_argument('--resultado',type=Path,required=True);a=p.parse_args()
def read(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter=';'))
expected={(r['data'],r['nivel'],r['cenario']):r for r in read(a.resultado/'TODOS_70_NIVEIS_QUATRO_CENARIOS.csv')};checks=0
for ref in read(a.coleta/'REFERENCIAS.csv'):
 date=ref['date'];cut=epoch(ref['cut_server']);raw=read(a.coleta/f"EVENTOS_{date.replace('.','')}.csv")
 events=[(int(r['time_msc']),D(r['last']),int(r['ordinal_ALL'])) for r in raw]
 for l in levels(ref):
  for grid in (False,True):
   for strict in (False,True):
    name=('GRADE5' if grid else 'MATEMATICA')+('_ESTRITA' if strict else '_TOQUE');e=expected[date,l['name'],name]
    en=l['entry5' if grid else 'entry'];sl=l['sl5' if grid else 'sl'];tp=l['tp5' if grid else 'tp'];reason='';points='';in_t=out_t='';entry=None;exit=None
    if not l['eligible']:assert e['estado']=='INELEGIVEL'
    else:
     candidates=(i for i,(ms,price,idx) in enumerate(events) if ms<cut and ((price<en if strict else price<=en) if l['buy'] else (price>en if strict else price>=en)))
     j=next(candidates,None)
     if j is not None:
      entry=events[j];in_t=calendar(entry[0])
      # Search first exit in ordered records AFTER entry, with cutoff precedence.
      for ms,price,idx in events[j+1:]:
       if ms>=cut:reason='CORTE_LAST';exit=(ms,price,idx);out=price;break
       stop=price<=sl if l['buy'] else price>=sl;target=price>=tp if l['buy'] else price<=tp
       if stop or target:reason='STOP' if stop else 'ALVO';out=sl if stop else tp;exit=(ms,price,idx);break
      assert exit is not None
      out_t=calendar(exit[0]);points=((out-en) if l['buy'] else (en-out)).quantize(D('.000001'))
     else:assert e['estado']=='SEM_TOQUE'
    assert e['hora_entrada']==in_t and e['hora_saida']==out_t and e['motivo']==reason
    assert (D(e['pontos_teoricos']) if e['pontos_teoricos'] else '')==points
    if entry:assert D(e['negocio_entrada'])==entry[1] and D(e['negocio_saida'])==exit[1]
    checks+=1
assert checks==280
(a.resultado/'VALIDACAO_INDEPENDENTE.json').write_text(json.dumps({'checks':checks,'dates':14,'variants':4,'all_five_levels_compared':True,'method':'Independent per-level first-entry/first-exit search vs streaming engine; exact timestamps, event prices, reasons and theoretical points.','passed':True,'certifies_exchange_fills':False},indent=2)+'\n')
print('PASS independent level searches',checks)
