import csv, json, math, hashlib, io, zipfile, argparse
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
FILES = {
 'GENIAL_A': Path('/workspace/attachments/bfffe30c-466c-4e74-b3b5-38c17b384d40/DiagTicksAB_TERMINAL_GenialInvestimentos-PRD_WINZ26_2026_10_30_09_00_2026_10_30_09_10_GENIAL_A_757381906_ALL.csv'),
 'GENIAL_B': Path('/workspace/attachments/b578ea40-d5a5-426f-a0ed-8bd88fc6f239/DiagTicksAB_TESTER_GenialInvestimentos-PRD_WINZ26_2026_10_30_09_00_2026_10_30_09_10_GENIAL_B_757688312_ALL.csv')
}
parser = argparse.ArgumentParser(description='Confere quatro CSVs A/B; XP é lido do ZIP preservado no projeto.')
parser.add_argument('--genial-a', type=Path, default=FILES['GENIAL_A'])
parser.add_argument('--genial-b', type=Path, default=FILES['GENIAL_B'])
args = parser.parse_args()
FILES.update(GENIAL_A=args.genial_a, GENIAL_B=args.genial_b)

def analyze(raw):
 rows = list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig')), delimiter=';'))
 flags = Counter(); mins=[0]*10; valid=[]; normalized=[]; inverted=0
 for r in rows:
  t=int(r['time_msc']); flag=int(r['flags']); last=float(r['last'])
  assert 1793350800000 <= t < 1793351400000
  flags[flag]+=1
  business=bool(flag & 120) and math.isfinite(last) and last>0
  if business:
   valid.append(r); mins[(t-1793350800000)//60000]+=1
  inverted+=float(r['bid'])>float(r['ask'])
  normalized.append((t,float(r['bid']),float(r['ask']),last,int(r['volume']),float(r['volume_real']),flag))
 ts=[r[0] for r in normalized]
 assert ts==sorted(ts)
 return {
  'rows':len(rows),'business_valid':len(valid),'per_minute':mins,'flags':dict(flags),
  'positive_last':sum(float(r['last'])>0 for r in rows),
  'positive_volume':sum(float(r['volume_real'])>0 for r in rows),
  'bid_greater_ask':inverted,
  'first_msc':ts[0], 'last_msc':ts[-1],
  'first_business_msc':int(valid[0]['time_msc']) if valid else None,
  'business_min':min((float(r['last']) for r in valid),default=None),
  'business_max':max((float(r['last']) for r in valid),default=None),
  'sha256':hashlib.sha256(raw).hexdigest()
 },normalized

results={}; records={}; sources={}
with zipfile.ZipFile(ROOT/'entregas/diagnostico_ticks_ab_v1_21/pacote_resultado_xp_20261105/Resultado_AB_XP_20261105.zip') as z:
 for tag in ['XP_A','XP_B']:
  name=next(n for n in z.namelist() if tag+'_' in n and n.endswith('_ALL.csv'))
  results[tag],records[tag]=analyze(z.read(name));sources[tag]=name
for tag,p in FILES.items():
 results[tag],records[tag]=analyze(p.read_bytes());sources[tag]=p.name
assert [results[t]['rows'] for t in ['XP_A','XP_B','GENIAL_A','GENIAL_B']]==[108005,36571,236855,36571]
assert [results[t]['business_valid'] for t in ['XP_A','XP_B','GENIAL_A','GENIAL_B']]==[105342,0,142865,0]
assert records['XP_B']==records['GENIAL_B']
assert results['XP_B']['sha256']==results['GENIAL_B']['sha256']
assert results['XP_A']['per_minute']==[8660,20683,15263,9445,8792,12129,6838,6168,9340,8024]
assert results['GENIAL_A']['per_minute']==[10528,26687,21451,12731,11849,17716,9325,8468,13070,11040]
(OUT/'CONFERENCIA_CSV.json').write_text(json.dumps({'results':results,'sources':sources,'XP_B_igual_GENIAL_B_campo_a_campo':True},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(results,ensure_ascii=False,indent=2))
