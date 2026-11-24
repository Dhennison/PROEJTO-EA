from pathlib import Path
import json,csv,hashlib,zipfile
P=Path(__file__).parent;R=P.parents[1]
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  while b:=f.read(1024*1024):h.update(b)
 return h.hexdigest()
assets=json.loads((P/'ASSETS_PLANEJADOS.json').read_text());remote=json.loads((P/'ASSETS_GITHUB_VERIFICADOS.json').read_text());by={r['name']:r for r in remote['assets']};members=0
assert len(assets)==len(by)==28
for a in assets:
 p=Path(a['path']);assert p.stat().st_size==a['bytes'] and sha(p)==a['sha256']
 r=by[a['name']];assert r['bytes']==a['bytes'] and r['sha256']==a['sha256'] and r['github_digest']=='sha256:'+a['sha256'] and r['state']=='uploaded'
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
result=dict(verified_release_url=remote['release_url'],verified_remote_assets=28,verified_remote_bytes=sum(a['bytes'] for a in assets),original_Cedro_ZIPs=26,original_Replay_members=10,derived_cache_members=14,internal_members_SHA256_verified=24,Cedro_historical_receipts=132,historical_Cedro_bytes_not_accessible=106,saved_portfolio_extremes=[25965,28470],saved_DD_extremes=[7835,7705],financial_results_changed=False)
(P/'VERIFICACAO_BACKUP.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))
