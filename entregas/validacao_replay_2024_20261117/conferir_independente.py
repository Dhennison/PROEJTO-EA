from pathlib import Path
from decimal import Decimal as D
import json,pickle,hashlib
import openpyxl
P=Path(__file__).parent
src=Path('/workspace/dados_brutos_modelo_d/replay_profit/Janeiro_a_Dezembro_2024_Release.xlsx')
inv=json.loads((P/'INVENTARIO_ABAS.json').read_text());assert len(inv)==33 and sum(x['records'] for x in inv)==1313080
ss=json.loads((P/'RESULTADOS_TODOS_MESES.json').read_text());rs=[r for s in ss for r in s['results']]
assert len(rs)==35 and all(r['resolved'] and r['tie_invariant'] and not r['mixed_barrier_ms'] for r in rs)
assert len({(r['date'],r['level']) for r in rs})==35
prefix=[r for r in rs if r.get('partial_prefix_invariance_proof')];assert {(r['date'],r['level']) for r in prefix}=={('2024-01-18','S50'),('2024-08-29','S50')}
wb=openpyxl.load_workbook(src,read_only=True,data_only=True);out=[]
for name in ['JAN 18-01-24','JUN 07-06-24','AGO 29-08-24']:
 rr=[]
 for ordinal,row in enumerate(wb[name].iter_rows(min_row=2,values_only=True),2):
  if row[0] is None:continue
  def val(x):return int(D(str(x).replace('.','').replace(',','.'))) if isinstance(x,str) else int(x)
  rr.append((row[0],val(row[2]),val(row[3]),ordinal))
 meta=next(r for r in inv if r['sheet']==name);assert rr==pickle.loads(Path(meta['cache']).read_bytes())
 out.append(dict(sheet=name,rows=len(rr),all_time_price_quantity_ordinals_equal=True))
(P/'CONFERENCIA_EXTRACAO_INDEPENDENTE.json').write_text(json.dumps(dict(cases_validated=35,independent_reader='openpyxl',stream_reader='lxml',sheets=out,prefix_proofs=[dict(date=r['date'],level=r['level'],proof=r['partial_prefix_invariance_proof']) for r in prefix],unresolved=0),ensure_ascii=False,indent=2)+'\n')
print('35casos validados;3abas independentes idênticas;0pendências')
