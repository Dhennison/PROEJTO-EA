"""Rebuild Jan02text cache and audit without deduplicating or modifying main XLSX.
Requires preserved raw text,or explicit path supplied by user attachment.
"""
from pathlib import Path
import csv,pickle,json,hashlib,shutil,sys
P=Path(__file__).parent
SOURCE=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/workspace/dados_brutos_modelo_d/replay_profit/2025_01_02_Complemento_20261116.txt')
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()=='8e37c24e56587501b37fa8c1a14e7b2162bf887d860c2e58c64506bac1db00cc'
es=[]
with SOURCE.open(encoding='utf-8-sig',newline='') as f:
 for n,r in enumerate(csv.reader(f,delimiter='\t'),1):
  if n>1 and r and r[0]:es.append((r[0],int(r[2].replace('.','')),int(r[3].replace('.','')),n))
assert len(es)==56878 and all(a[0]>=b[0] for a,b in zip(es,es[1:]))
meta=next(m for m in json.loads((P/'INVENTARIO_ABAS.json').read_text()) if m['sheet']=='JAN 02-01-25')
old=pickle.loads(Path(meta['cache']).read_bytes());o=[r[:3] for r in old];new=[r[:3] for r in es]
found=next((i for i,x in enumerate(new) if x==o[0] and new[i:i+len(o)]==o),None);assert found is not None
cache=Path('/workspace/work/lote2025/cache/complemento02jan.pickle');cache.parent.mkdir(parents=True,exist_ok=True);cache.write_bytes(pickle.dumps(es,protocol=4))
dest=Path('/workspace/dados_brutos_modelo_d/replay_profit/2025_01_02_Complemento_20261116.txt');dest.parent.mkdir(parents=True,exist_ok=True)
if dest.resolve()!=SOURCE.resolve():shutil.copy2(SOURCE,dest)
audit=dict(date='2025-01-02',sheet='TXT_COMPLEMENTO02JAN',index='TXT02JAN',records=len(es),start=es[-1][0],end=es[0][0],at_limit_200001=False,cache=str(cache),source='USER_TEXT_COMPLEMENT',source_raw=str(dest),source_sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),main_original_records=len(old),main_original_temporal_price_quantity_sequence_contiguous_in_complement=True,main_original_slice_start=found,no_deduplication=True,use='Replace entire Jan02copy with complete text,retain original unchanged;do not concatenate/double count')
(P/'COMPLEMENTO_02JAN.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n');print(json.dumps(audit,indent=2))
