from pathlib import Path
import json,hashlib,shutil,urllib.parse
P=Path(__file__).parent;R=P.parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  while b:=f.read(1024*1024):h.update(b)
 return h.hexdigest()
root='https://raw.githubusercontent.com/Dhennison/PROEJTO-EA/entrega-modelod-v2-10-20261030/'
assets=json.loads((P/'ASSETS_PLANEJADOS.json').read_text());files=[]
for a in assets:
 source=Path(a['path']);assert source.stat().st_size==a['bytes'] and sha(source)==a['sha256']
 if a['kind']=='DERIVED_ANALYTIC_STATE_ARCHIVE':
  parts=[]
  with source.open('rb') as f:
   index=1
   while chunk:=f.read(40*1024*1024):
    target=P/'caches'/f'{a["name"]}.part{index:03d}';target.parent.mkdir(exist_ok=True)
    if target.exists():assert target.read_bytes()==chunk
    else:target.write_bytes(chunk)
    rel=str(target.relative_to(R));item=dict(name=target.name,path=str(target),repository_path=rel,bytes=target.stat().st_size,sha256=sha(target),browser_download_url=root+urllib.parse.quote(rel,safe='/'));parts.append(item);files.append(item);index+=1
  a['storage_parts']=parts;a['browser_download_url']=None;a['repository_path']=None
 else:
  folder='brutos_cedro' if a['kind']=='ORIGINAL_CEDRO_ZIP' else 'anexos_replay';target=P/folder/a['name'];target.parent.mkdir(exist_ok=True)
  if target.exists():assert target.stat().st_size==a['bytes'] and sha(target)==a['sha256']
  else:shutil.copyfile(source,target)
  rel=str(target.relative_to(R));a['repository_path']=rel;a['browser_download_url']=root+urllib.parse.quote(rel,safe='/');files.append(dict(name=target.name,path=str(target),repository_path=rel,bytes=target.stat().st_size,sha256=sha(target),browser_download_url=a['browser_download_url']))
(P/'ASSETS_PLANEJADOS.json').write_text(json.dumps(assets,ensure_ascii=False,indent=2)+'\n');(P/'ARQUIVOS_FISICOS_NA_BRANCH.json').write_text(json.dumps(files,ensure_ascii=False,indent=2)+'\n')
assert len(files)==31 and sum(r['bytes'] for r in files)==630562860 and max(r['bytes'] for r in files)<50*1024*1024
print('31 arquivos fisicos, 28 artefatos logicos; nenhum arquivo acima de 40 MiB; total',sum(r['bytes'] for r in files))
