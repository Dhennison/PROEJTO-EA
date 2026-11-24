from pathlib import Path
import subprocess,json,hashlib
P=Path(__file__).parent;R=P.parents[1];BR='entrega-modelod-v2-10-20261030';REPO='Dhennison/PROEJTO-EA'
def run(args):return subprocess.run(args,cwd=R,capture_output=True,text=True,check=True).stdout.strip()
def main():
 assert run(['git','branch','--show-current'])==BR
 files=json.loads((P/'ARQUIVOS_FISICOS_NA_BRANCH.json').read_text());batches=[];batch=[];size=0
 for r in files:
  if batch and size+r['bytes']>90*1024*1024:batches.append(batch);batch=[];size=0
  batch.append(r);size+=r['bytes']
 if batch:batches.append(batch)
 for i,items in enumerate(batches,1):
  paths=[r['repository_path'] for r in items];run(['git','add','--',*paths]);changes=subprocess.run(['git','diff','--cached','--quiet'],cwd=R).returncode
  if changes:print(run(['git','commit','-m',f'Preserva brutos e caches da continuidade (lote {i}/{len(batches)})']),flush=True)
  print('PUSH_LOTE',i,len(batches),sum(r['bytes'] for r in items),flush=True)
  print(run(['git','-c','pack.window=0','-c','core.compression=1','push','origin',BR]),flush=True)
  print('PUBLISHED_LOTE',i,len(batches),flush=True)
 sha=run(['git','rev-parse','HEAD']);tree=json.loads(run(['gh','api',f'repos/{REPO}/git/trees/{sha}?recursive=1']));assert not tree.get('truncated');by={r['path']:r for r in tree['tree']};receipt=[]
 for r in files:
  q=by[r['repository_path']];localsha=run(['git','hash-object','--',r['repository_path']]);assert q['type']=='blob' and q['size']==r['bytes'] and q['sha']==localsha
  receipt.append(dict(repository_path=r['repository_path'],bytes=r['bytes'],sha256=r['sha256'],git_blob_sha=q['sha'],remote_size_and_blob_match=True,browser_download_url=r['browser_download_url']))
 (P/'ARQUIVOS_GITHUB_VERIFICADOS.json').write_text(json.dumps(dict(storage='GIT_BRANCH_BLOBS',repository=REPO,branch=BR,verified_commit=sha,verified_physical_files=len(receipt),verified_logical_artifacts=28,verified_bytes=sum(r['bytes'] for r in receipt),files=receipt),ensure_ascii=False,indent=2)+'\n')
 print('ALL_REMOTE_FILES_VERIFIED',len(receipt),sha,flush=True)
if __name__=='__main__':main()
