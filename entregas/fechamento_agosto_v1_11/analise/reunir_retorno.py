"""Combine returned ZIPs, refusing conflicting duplicate files and unsafe paths."""
import argparse,zipfile,hashlib,json
from pathlib import Path,PurePosixPath

def gather(paths,out):
 assert not out.exists() or not any(out.iterdir()),'Usar pasta de destino vazia'
 out.mkdir(parents=True,exist_ok=True);files={};archives=[]
 for archive in paths:
  archives.append(dict(file=archive.name,sha256=hashlib.sha256(archive.read_bytes()).hexdigest()))
  with zipfile.ZipFile(archive) as z:
   for info in z.infolist():
    if info.is_dir():continue
    path=PurePosixPath(info.filename.replace('\\','/'));assert not path.is_absolute() and '..' not in path.parts
    name=path.name;assert ':' not in name and name.endswith(('.csv','.txt')),'Arquivo inesperado no retorno'
    content=z.read(info);digest=hashlib.sha256(content).hexdigest()
    if name in files:assert files[name]['sha256']==digest,'Duplicata conflitante: '+name
    else:(out/name).write_bytes(content);files[name]=dict(sha256=digest,bytes=len(content))
 manifest=dict(archives=archives,unique_files=files)
 (out.parent/(out.name+'_MANIFESTO_ZIPS.json')).write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');return manifest
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('zips',type=Path,nargs='+');a=p.parse_args();print('Arquivos reunidos:',len(gather(a.zips,a.out)['unique_files']))
