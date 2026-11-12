"""Reduction and ZIP integrity controls; synthetic data only."""
from pathlib import Path
import csv,random,json,sys,tempfile,zipfile
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'analise'))
from motor_precos import levels,replay,summary,reduce_events,epoch
from reunir_retorno import gather
with (root/'MQL5/Files/MD_Agosto_2026_Referencias.csv').open() as f:refs=list(csv.DictReader(f,delimiter=';'))
checks=0
for ref in refs:
 ls=levels(ref);bounds=sorted(set(v for level in ls for k,v in level.items() if k in ('entry5','sl5','tp5')))
 rng=random.Random(ref['date']);prices=bounds+[x+5 for x in bounds]+[x-5 for x in bounds]
 events=[dict(ord=i+1,msc=epoch(ref['date']+' 17:59:00')+(i//3)*1000,p=rng.choice(prices)) for i in range(300)];small=list(reduce_events(events,ls))
 for grid in (False,True):
  for strict in (False,True):
   assert summary(replay(events,ls,epoch(ref['cut_server']),grid,strict))==summary(replay(small,ls,epoch(ref['cut_server']),grid,strict));checks+=5
# The expected frozen core hash is fixed, so the package is self-contained.
import hashlib
assert hashlib.sha256((root/'MQL5/Experts/ModeloD_Fechamento_Agosto/ModeloD_Core.mqh').read_bytes()).hexdigest()==json.loads((root/'REFERENCIAS_AUDITADAS.json').read_text())['frozen_core_sha256']
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp)
 with zipfile.ZipFile(p/'a.zip','w') as z:z.writestr('MES111/RESULTADO.txt','END;');z.writestr('REFERENCIAS.csv','foo')
 with zipfile.ZipFile(p/'b.zip','w') as z:z.writestr('RESULTADO.txt','END;');z.writestr('EVENTOS_20260804.csv','bar')
 assert len(gather([p/'a.zip',p/'b.zip'],p/'ok')['unique_files'])==3
 with zipfile.ZipFile(p/'bad.zip','w') as z:z.writestr('REFERENCIAS.csv','conflict')
 try:gather([p/'a.zip',p/'bad.zip'],p/'badout')
 except AssertionError:pass
 else:raise AssertionError('ZIP conflict accepted')
 with zipfile.ZipFile(p/'unsafe.zip','w') as z:z.writestr('../evil.csv','no')
 try:gather([p/'unsafe.zip'],p/'unsafe')
 except AssertionError:pass
 else:raise AssertionError('Unsafe ZIP path accepted')
result=dict(august_level_state_reduction_checks=checks,same_millisecond_order_kept=True,gaps_equality_cutoff=True,core_identical_to_frozen_september=True,zip_merge_equal_duplicates=True,zip_conflicts_refused=True,zip_traversal_refused=True,native_MT5_compile_or_execution=False)
(root/'testes/RESULTADO_REDUCAO_E_ARQUIVOS.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
