from pathlib import Path
import json,hashlib,zipfile,csv
P=Path(__file__).parent;R=P.parents[1];STORE=Path('/workspace/work/backup_continuidade_20261124');STORE.mkdir(exist_ok=True)
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  while b:=f.read(1024*1024):h.update(b)
 return h.hexdigest()
index=json.loads((R/'entregas/fechamento_s23_cedro_20261119/INDICE_26_ZIPS_RESTAURADOS.json').read_text())
assets=[]
for r in index:
 p=Path(r['preserved_path']);assert p.is_file() and p.stat().st_size==int(r['bytes']) and digest(p)==r['sha256'];assets.append(dict(name=p.name,path=str(p),bytes=p.stat().st_size,sha256=r['sha256'],kind='ORIGINAL_CEDRO_ZIP',sediment_file_id=r['sediment_file_id']))
# Every currently accessible non-Cedro uploaded original, names/bytes unchanged in UUID folders.
attachments=sorted(p for p in Path('/workspace/attachments').rglob('*') if p.is_file() and not p.name.startswith('WIN_2026'))
anexos=[];dest=STORE/'Anexos_Replay_Profit_20261124.zip'
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in attachments:
  arc=str(p.relative_to('/workspace'));z.write(p,arcname=arc);anexos.append(dict(path=str(p),archive_path=arc,bytes=p.stat().st_size,sha256=digest(p)))
 z.writestr('INVENTARIO_ANEXOS.json',json.dumps(anexos,ensure_ascii=False,indent=2)+'\n')
with zipfile.ZipFile(dest) as z:assert z.testzip() is None
assets.append(dict(name=dest.name,path=str(dest),bytes=dest.stat().st_size,sha256=digest(dest),kind='ORIGINAL_REPLAY_ATTACHMENTS_ARCHIVE',files=len(anexos)))
(P/'INVENTARIO_ANEXOS_REPLAY.json').write_text(json.dumps(anexos,ensure_ascii=False,indent=2)+'\n')
# Derived state to resume the saved scripts without needing lost local caches.
relative=[
'estudo_saidas/dados.pickle',
'estudo_s61/resultados.pickle',
'novos_niveis_20261119/resultados.pickle',
'fixos_tres_niveis_20261119/resultados.pickle',
'replay_s61_20261119/auditoria.pickle',
'replay_s23_20261119/auditoria.pickle',
'replay_s23_20261119/resultado_atualizado.pickle',
'fechamento_s23_cedro_20261119/resultados.pickle',
'fechamento_s23_cedro_20261119/fechado.pickle',
's23_espera_5min_20261122/resultados.pickle',
'modelod_espera_5min_20261122/resultados.pickle',
'combinacao_s23_s38_s61_20261122/resultados.pickle',
'combinacao_4_niveis_r61_venda_20261122/resultados.pickle',
'cedro_recuperado/resultados_atualizados.pickle']
cache=[];dest=STORE/'Caches_Analiticos_Modelo_D_20261124.zip'
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
 for rel in relative:
  p=Path('/workspace/work')/rel;assert p.is_file();row=dict(path=str(p),archive_path='work/'+rel,bytes=p.stat().st_size,sha256=digest(p));cache.append(row);z.write(p,arcname=row['archive_path'])
 z.writestr('INVENTARIO_CACHES.json',json.dumps(cache,ensure_ascii=False,indent=2)+'\n')
 z.writestr('LEIA_PRIMEIRO.txt','Caches derivados dos scripts locais. Fontes, resultados e configuracao oficial continuam nos CSVs/manifests da branch. Restaurar work/ sob /workspace/ e conferir SHA256 antes de carregar. Nao substituir fontes atuais por dados antigos de um cache sem conferir o contexto.\n')
with zipfile.ZipFile(dest) as z:assert z.testzip() is None
assets.append(dict(name=dest.name,path=str(dest),bytes=dest.stat().st_size,sha256=digest(dest),kind='DERIVED_ANALYTIC_STATE_ARCHIVE',files=len(cache)))
(P/'INVENTARIO_CACHES.json').write_text(json.dumps(cache,ensure_ascii=False,indent=2)+'\n')
# Exact historical receipt list: no claim that all 132 originals are locally available.
original={}
for f in (R/'entregas').rglob('*.csv'):
 if f.name not in ['PARTES_RECEBIDAS.csv','PARTES_CONFERIDAS.csv']:continue
 with f.open(encoding='utf-8-sig') as inp:
  for r in csv.DictReader(inp,delimiter=';'):
   name=r.get('arquivo','')
   if name.startswith(('WIN_202608','WIN_202609','WIN_202610')):original[name]=dict(arquivo=name,bytes=int(r['bytes']),sha256=r['sha256'],historical_receipt=str(f.relative_to(R)),accessible_now=name in {a['name'] for a in assets})
rows=[original[k] for k in sorted(original)];assert len(rows)==132 and sum(r['accessible_now'] for r in rows)==26
with (P/'INVENTARIO_CEDRO_132_RECEBIDOS_26_ACESSIVEIS.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter=';');w.writeheader();w.writerows(rows)
(P/'ASSETS_PLANEJADOS.json').write_text(json.dumps(assets,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(assets=len(assets),bytes=sum(r['bytes'] for r in assets),Cedro_ZIPs=26,original_attachments=len(anexos),cache_files=len(cache),cache_zip_bytes=assets[-1]['bytes']),indent=2))
