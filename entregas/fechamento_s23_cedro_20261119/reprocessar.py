from pathlib import Path
from decimal import Decimal as D
import pickle,csv,json,zipfile,subprocess,hashlib,sys,itertools
P=Path(__file__).parent;R=P.parents[1];E=R/'entregas';C=Path('/workspace/work/fechamento_s23_cedro_20261119');C.mkdir(exist_ok=True)
x=pickle.load(open('/workspace/work/replay_s23_20261119/resultado_atualizado.pickle','rb'))
sys.path.insert(0,str(E/'fechamento_agosto_v1_11/analise'));from motor_precos import replay,calendar
receipt=json.loads((P/'RESTAURACAO_FONTES.json').read_text());inventory=list(csv.DictReader((E/'cedro_extrator_win_v1_00/retorno_geral_20261112/CONTRATOS.csv').open(encoding='utf-8-sig'),delimiter=';'))
subprocess.run(['g++','-O3','-std=c++17',str(P/'reprocessar.cpp'),'-o',str(C/'motor')],check=True)
results=[];audits=[];names=['S38.2','S50','S61.8','R38.2','R61.8'];oldresults=x['trades']
for tag in sorted({r['arquivo'][4:12] for r in receipt}):
 d=tag[:4]+'-'+tag[4:6]+'-'+tag[6:];month='agosto' if tag[4:6]=='08' else 'setembro';folder=E/f'cedro_modelod_{month}_2026'/'resultado';cfg=(folder/f'{tag}.config').read_text().splitlines();sym,date,base=cfg[0].split()[:3];base=int(base)
 params=[tuple(map(int,l.split())) for l in cfg[-5:]];o=x['ops'][d];original=next(r for r in oldresults if r['date']==d);assert original['pending'] and original['lower']==-200 and original['upper']==500
 params.append((1,1,o['entry'],o['entry']-200,o['entry']+500));levels=[dict(name=name,eligible=bool(eligible),buy=bool(buy),entry5=D(en),sl5=D(sl),tp5=D(tp)) for name,(eligible,buy,en,sl,tp) in zip(names+['S23.6'],params)]
 config=C/f'{tag}.config';config.write_text(f'{sym} {date} {18*3600000} {len(params)}\n'+'\n'.join(' '.join(map(str,a)) for a in params)+'\n');dest=P/f'DIRETO_{tag}.csv';reduced=C/f'EVENTOS_{tag}.csv'
 with dest.open('wb') as f:
  proc=subprocess.Popen([str(C/'motor'),str(config),str(reduced)],stdin=subprocess.PIPE,stdout=f,stderr=subprocess.PIPE)
  for meta in sorted([r for r in receipt if tag in r['arquivo']],key=lambda r:r['arquivo']):
   path=Path(meta['preserved_path']);assert path.stat().st_size==meta['bytes'] and hashlib.sha256(path.read_bytes()).hexdigest()==meta['sha256']
   with zipfile.ZipFile(path) as z:
    with z.open(z.namelist()[0]) as raw:
     while chunk:=raw.read(1024*1024):proc.stdin.write(chunk)
  proc.stdin.close();log=proc.stderr.read().decode();assert proc.wait()==0,log
 records=int(log.strip());expected=next(int(r['registros']) for r in inventory if r['dia']==tag and r['ativo']==sym);assert records==expected
 rr=list(csv.DictReader(dest.open(),delimiter=';'));old=list(csv.DictReader((folder/f'DIRETO_{tag}.csv').open(encoding='utf-8-sig'),delimiter=';'))
 for a,b in zip(rr[:5],old):assert int(a['entered'])==int(b['entered']) and int(a['closed'])==int(b['closed']) and int(a['points'])==int(b['points']) and int(a['reason'])==int(b['reason']),(d,a,b)
 events=[dict(ord=int(r['ordinal']),msc=base+int(r['ms']),p=D(r['price'])) for r in csv.DictReader(reduced.open(),delimiter=';')]
 st=replay(events,levels,base+18*3600000,grid=True);alt=[ev for _,g in itertools.groupby(events,key=lambda ev:ev['msc']) for ev in reversed(list(g))];altst=replay(alt,[levels[-1]],base+18*3600000,grid=True)['S23.6']
 for lv,r in zip(levels,rr):
  py=st[lv['name']];assert bool(int(r['entered']))==bool(py['entry_event']) and bool(int(r['closed']))==bool(py['exit_event'])
  if py['exit_event']:assert int(r['points'])==int(py['points']) and int(r['reason'])=={'STOP':1,'ALVO':2,'CORTE_LAST':3}[py['reason']]
 py=st['S23.6'];assert py['status']=='ENCERRADA';direct=rr[-1];assert int(direct['resolved'])==1,(d,direct)
 assert (py['points'],py['reason'])==(altst['points'],altst['reason']);value=int(py['points']);assert original['lower']<=value<=original['upper']
 reason={'STOP':'SL','ALVO':'TP','CORTE_LAST':'CUT'}[py['reason']]
 results.append(dict(date=d,contract=sym,level='S23.6',entry=o['entry'],stop=o['entry']-200,target=o['entry']+500,entry_time=calendar(py['entry_event']['msc']),entry_ordinal=py['entry_event']['ord'],exit_time=calendar(py['exit_event']['msc']),exit_ordinal=py['exit_event']['ord'],exit_trade_price=int(py['exit_event']['p']),reason=reason,points=value,same_ms_order_invariant=True,full_direct_cpp_and_python_match=True,resolved=True))
 audits.append(dict(date=d,contract=sym,full_stream_records=records,expected_records=expected,reduced_events=len(events),original_5_states_match=True,python_all6_states_match=True,full_same_ms_invariant=True,reduced_file_sha256=hashlib.sha256(reduced.read_bytes()).hexdigest()))
 print(d,sym,reason,value,'entry',results[-1]['entry_time'],'exit',results[-1]['exit_time'],flush=True)
with (P/'CINCO_OPERACOES_RESOLVIDAS.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(results[0]),delimiter=';');w.writeheader();w.writerows(results)
(P/'AUDITORIA_REPROCESSAMENTO.json').write_text(json.dumps(audits,ensure_ascii=False,indent=2)+'\n');(C/'resultados.pickle').write_bytes(pickle.dumps(dict(results=results,audits=audits,prior=x)))
print('TOTAL',sum(r['points'] for r in results),'RECORDS',sum(r['full_stream_records'] for r in audits),flush=True)
