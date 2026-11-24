"""Restore verified release assets into a workspace; never overwrite different files."""
from pathlib import Path
import argparse,json,hashlib,urllib.request,zipfile,shutil
P=Path(__file__).parent
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  while b:=f.read(1024*1024):h.update(b)
 return h.hexdigest()
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--tipo',choices=['caches','cedro','anexos','tudo'],default='caches');parser.add_argument('--workspace',default='/workspace');parser.add_argument('--arquivo',action='append',help='Limit to exact asset name(s)');parser.add_argument('--verificar-somente',action='store_true');args=parser.parse_args();root=Path(args.workspace).resolve();meta=P/'ASSETS_PLANEJADOS.json';assets=json.loads(meta.read_text());count=0
 for a in assets:
  kind=a['kind'];wanted=args.tipo=='tudo' or (args.tipo=='cedro' and kind=='ORIGINAL_CEDRO_ZIP') or (args.tipo=='caches' and kind=='DERIVED_ANALYTIC_STATE_ARCHIVE') or (args.tipo=='anexos' and kind=='ORIGINAL_REPLAY_ATTACHMENTS_ARCHIVE')
  if not wanted or args.arquivo and a['name'] not in args.arquivo:continue
  local=Path(a['path']);cache=root/'backup_modelod_downloads'/a['name'];source=None
  for q in [local,cache]:
   if q.is_file() and q.stat().st_size==a['bytes'] and sha(q)==a['sha256']:source=q;break
  if source is None:
   if args.verificar_somente:raise RuntimeError('Arquivo nao acessivel para verificar: '+a['name'])
   cache.parent.mkdir(parents=True,exist_ok=True);partial=cache.with_suffix(cache.suffix+'.partial');request=urllib.request.Request(a['browser_download_url'],headers={'User-Agent':'ModeloD-backup-restore'})
   with urllib.request.urlopen(request) as inp,partial.open('wb') as out:shutil.copyfileobj(inp,out,1024*1024)
   if partial.stat().st_size!=a['bytes'] or sha(partial)!=a['sha256']:raise RuntimeError('Hash/tamanho diferente: '+a['name'])
   partial.replace(cache);source=cache
  if kind=='ORIGINAL_CEDRO_ZIP':
   target=root/'dados_brutos_modelo_d/cedro'/a['name']
   if target.exists():
    if sha(target)!=a['sha256']:raise RuntimeError('Nao sobrescrever bruto diferente: '+str(target))
   elif not args.verificar_somente:target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
  else:
   inventory='INVENTARIO_CACHES.json' if kind=='DERIVED_ANALYTIC_STATE_ARCHIVE' else 'INVENTARIO_ANEXOS.json'
   with zipfile.ZipFile(source) as z:
    for r in json.loads(z.read(inventory)):
     rel=Path(r['archive_path']);target=(root/rel).resolve()
     if rel.is_absolute() or root not in target.parents:raise RuntimeError('Caminho inseguro no arquivo')
     if target.exists():
      if target.stat().st_size!=r['bytes'] or sha(target)!=r['sha256']:raise RuntimeError('Nao sobrescrever arquivo diferente: '+str(target))
      continue
     if args.verificar_somente:continue
     target.parent.mkdir(parents=True,exist_ok=True)
     with z.open(r['archive_path']) as inp,target.open('xb') as out:shutil.copyfileobj(inp,out,1024*1024)
     if target.stat().st_size!=r['bytes'] or sha(target)!=r['sha256']:raise RuntimeError('Hash extraido diferente: '+str(target))
  count+=1;print('OK',a['name'],flush=True)
 print('Assets verificados/restaurados:',count)
if __name__=='__main__':main()
