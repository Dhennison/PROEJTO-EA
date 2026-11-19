from pathlib import Path
import pickle,csv,json,zipfile,subprocess,hashlib,collections
P=Path(__file__).parent;R=P.parents[1];E=R/'entregas';C=Path('/workspace/work/novos_niveis_20261119');x=pickle.load(open(C/'resultados.pickle','rb'))
receipt=list(csv.DictReader((E/'coletas_s61_e_teste_50_250_20261118/ARQUIVOS_RECUPERADOS.csv').open(encoding='utf-8-sig'),delimiter=';'));inventory=list(csv.DictReader((E/'cedro_extrator_win_v1_00/retorno_geral_20261112/CONTRATOS.csv').open(encoding='utf-8-sig'),delimiter=';'))
subprocess.run(['g++','-O3','-std=c++17',str(P/'conferir_raw.cpp'),'-o',str(C/'conferir_raw')],check=True)
priorfile=P/'CEDRO_RESULTADOS_CONFIRMADOS.csv'
prior={(r['date'],r['level'],r['variant']) for r in csv.DictReader(priorfile.open(encoding='utf-8-sig'),delimiter=';')} if priorfile.exists() else set()
results=[];audits=[]
for tag in sorted({r['arquivo'][4:12] for r in receipt}):
 d=tag[:4]+'-'+tag[4:6]+'-'+tag[6:];trs=[r for r in x['trades'] if r['date']==d and (r['pending'] or (r['date'],r['level'],r['variant']) in prior)];cfg=(E/'cedro_modelod_agosto_2026/resultado'/f'{tag}.config').read_text().splitlines();sym,date=cfg[0].split()[:2]
 params=[tuple(map(int,l.split())) for l in cfg[-5:]]
 for r in trs:
  buy=r['level'].startswith('S');sign=1 if buy else -1;params.append((1,int(buy),r['entry'],r['entry']-sign*r['stop_points'],r['entry']+sign*r['target_points']))
 config=C/f'{tag}.config';config.write_text(f'{sym} {date} {18*3600000} {len(params)}\n'+'\n'.join(' '.join(map(str,a)) for a in params)+'\n');dest=P/f'RAW_DIRETO_{tag}.csv'
 with dest.open('wb') as f:
  proc=subprocess.Popen([str(C/'conferir_raw'),str(config)],stdin=subprocess.PIPE,stdout=f,stderr=subprocess.PIPE)
  for meta in sorted([r for r in receipt if tag in r['arquivo']],key=lambda r:r['arquivo']):
   path=Path(meta['preserved_path']);assert path.stat().st_size==int(meta['bytes']) and hashlib.sha256(path.read_bytes()).hexdigest()==meta['sha256']
   with zipfile.ZipFile(path) as z:
    with z.open(z.namelist()[0]) as raw:
     while chunk:=raw.read(1024*1024):proc.stdin.write(chunk)
  proc.stdin.close();log=proc.stderr.read().decode();assert proc.wait()==0,log
 records=int(log.strip());expected=next(int(r['registros']) for r in inventory if r['dia']==tag and r['ativo']==sym);assert records==expected
 rr=list(csv.DictReader(dest.open(),delimiter=';'));old=list(csv.DictReader((E/'cedro_modelod_agosto_2026/resultado'/f'DIRETO_{tag}.csv').open(encoding='utf-8-sig'),delimiter=';'))
 for a,b in zip(rr[:5],old):assert int(a['entered'])==int(b['entered']) and int(a['closed'])==int(b['closed']) and int(a['points'])==int(b['points']) and int(a['reason'])==int(b['reason']),(d,a,b)
 for tr,r in zip(trs,rr[5:]):
  assert int(r['entered']) and int(r['closed']);v=int(r['points']);reason={'1':'SL','2':'TP','3':'CUT'}[r['reason']];assert tr['lower']<=v<=tr['upper']
  results.append(dict(date=d,contract=sym,level=tr['level'],variant=tr['variant'],reason=reason,points=v,entry_ms=r['entry_ms'],exit_ms=r['exit_ms'],resolved=r['resolved']=='1'))
 audits.append(dict(date=d,contract=sym,full_records=records,expected_records=expected,original_5_states_match=True,new_pending_checked=len(trs),new_resolved=sum(r['resolved']=='1' for r in rr[5:])));print(d,records,len(trs),flush=True)
with (P/'CEDRO_RESULTADOS_CONFIRMADOS.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(results[0]),delimiter=';');w.writeheader();w.writerows(results)
(P/'AUDITORIA_CEDRO.json').write_text(json.dumps(audits,indent=2)+'\n');print('TOTAL',len(results),sum(r['resolved'] for r in results),flush=True)
