from pathlib import Path
import json,csv,hashlib,zipfile
P=Path(__file__).parent;R=P.parents[1]
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  while b:=f.read(1024*1024):h.update(b)
 return h.hexdigest()
assets=json.loads((P/'ASSETS_PLANEJADOS.json').read_text());remote=json.loads((P/'ARQUIVOS_GITHUB_VERIFICADOS.json').read_text());physical=json.loads((P/'ARQUIVOS_FISICOS_NA_BRANCH.json').read_text());by={r['repository_path']:r for r in remote['files']};members=0
assert len(by)==len(physical)==31
for r in physical:
 q=R/r['repository_path'];proof=by[r['repository_path']];assert q.stat().st_size==r['bytes'] and sha(q)==r['sha256'] and proof['bytes']==r['bytes'] and proof['sha256']==r['sha256'] and proof['remote_size_and_blob_match']
assert len(assets)==28
for a in assets:
 p=Path(a['path']);assert p.stat().st_size==a['bytes'] and sha(p)==a['sha256']
 if a.get('storage_parts'):
  h=hashlib.sha256();size=0
  for part in a['storage_parts']:
   with (R/part['repository_path']).open('rb') as f:
    while b:=f.read(1024*1024):h.update(b);size+=len(b)
  assert size==a['bytes'] and h.hexdigest()==a['sha256']
 else:
  q=R/a['repository_path'];assert q.stat().st_size==a['bytes'] and sha(q)==a['sha256']
 if a['kind']!='ORIGINAL_CEDRO_ZIP':
  internal='INVENTARIO_CACHES.json' if a['kind']=='DERIVED_ANALYTIC_STATE_ARCHIVE' else 'INVENTARIO_ANEXOS.json'
  with zipfile.ZipFile(p) as z:
   for m in json.loads(z.read(internal)):
    h=hashlib.sha256();size=0
    with z.open(m['archive_path']) as f:
     while b:=f.read(1024*1024):h.update(b);size+=len(b)
    assert size==m['bytes'] and h.hexdigest()==m['sha256'];members+=1
assert members==24
# No financial recalculation: verify saved final summary and gate settings.
q=R/'entregas/combinacao_4_niveis_r61_venda_20261122';rows=list(csv.DictReader((q/'RESUMO_EXTREMOS.csv').open(encoding='utf-8-sig'),delimiter=';'));assert [float(r['points']) for r in rows]==[25965,28470] and [float(r['DD_continuous']) for r in rows]==[7835,7705]
config=json.loads((q/'CONFIGURACAO_RESERVADA_4_NIVEIS.json').read_text());assert [(r['level'],r['wait_ms']) for r in config['levels']]==[('S23.6',0),('S38.2',300000),('S61.8',300000),('R61.8',0)]
proof=json.loads((q/'VERIFICACAO.json').read_text());assert proof['clock_choices_checked']==16384 and proof['exact_shared_pending_dates']==14
inv=list(csv.DictReader((P/'INVENTARIO_CEDRO_132_RECEBIDOS_26_ACESSIVEIS.csv').open(encoding='utf-8-sig'),delimiter=';'));assert len(inv)==132 and sum(r['accessible_now']=='True' for r in inv)==26
result=dict(verified_branch=remote['branch'],verified_commit=remote['verified_commit'],verified_physical_files=31,verified_logical_artifacts=28,verified_remote_bytes=sum(a['bytes'] for a in assets),original_Cedro_ZIPs=26,original_Replay_members=10,derived_cache_members=14,internal_members_SHA256_verified=24,Cedro_historical_receipts=132,historical_Cedro_bytes_not_accessible=106,saved_portfolio_extremes=[25965,28470],saved_DD_extremes=[7835,7705],financial_results_changed=False)
(P/'VERIFICACAO_BACKUP.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))
