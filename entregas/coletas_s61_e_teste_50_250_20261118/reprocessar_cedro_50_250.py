from pathlib import Path
from decimal import Decimal as D
import csv,json,hashlib,zipfile,subprocess,sys,shutil,copy,itertools,collections
P=Path(__file__).parent;R=P.parents[1];E=R/'entregas';TMP=Path('/workspace/work/teste_50_250');STORE=Path('/workspace/dados_brutos_modelo_d/cedro');TMP.mkdir(exist_ok=True);STORE.mkdir(exist_ok=True)
sys.path.insert(0,str(E/'fechamento_agosto_v1_11/analise'));from motor_precos import replay,calendar
ids={'WIN_20260804_parte002.zip':'file_00000000065c820e8e92d1594bf03a5e','WIN_20260831_parte002.zip':'file_000000003d84820eb217940dc25a2d50','WIN_20260805_parte002.zip':'file_000000000518820e8899932c9c713800','WIN_20260804_parte001.zip':'file_000000001010820ea29000c4d02e0caa','WIN_20260813_parte002.zip':'file_00000000dba4820e9aaa35a50d9be644','WIN_20260805_parte001.zip':'file_000000006570820e87a845aaec4dd323','WIN_20260818_parte002.zip':'file_00000000c73c820eb030cf77dd804db5','WIN_20260813_parte001.zip':'file_00000000cf98820eaf374dfdeb0ed01a','WIN_20260819_parte002.zip':'file_000000008624820e9d488f16e2772aca','WIN_20260818_parte001.zip':'file_00000000d024820ebb9fe514f63858f0','WIN_20260821_parte002.zip':'file_0000000052a8820e968ff8b89e902ecb','WIN_20260819_parte001.zip':'file_00000000c4ac820eb79f5bbd7dc92ecf','WIN_20260821_parte001.zip':'file_0000000084b8820e92f053636aba8935','WIN_20260825_parte002.zip':'file_00000000ea60820eb82129ff0499f075','WIN_20260825_parte001.zip':'file_0000000043f4820e8e49d61fa38ae0c6','WIN_20260831_parte001.zip':'file_000000007c00820ebfd579b89a62d72a'}
def read(p):
 with p.open(encoding='utf-8-sig') as f:return list(csv.DictReader(f,delimiter=';'))
def write(p,rs):
 with p.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rs[0]),delimiter=';',lineterminator='\n');w.writeheader();w.writerows(rs)
parts=read(E/'estudo_saidas_niveis_20261117/CEDRO_PRIORITARIO_OITO_DATAS.csv');received=[]
for meta in parts:
 name=meta['arquivo'];dest=STORE/name
 if not dest.exists():
  matches=list(Path('/workspace/attachments').glob('*/'+name));assert len(matches)==1,(name,matches);shutil.copyfile(matches[0],dest)
 digest=hashlib.sha256(dest.read_bytes()).hexdigest();assert digest==meta['sha256'] and dest.stat().st_size==int(meta['bytes']),name
 with zipfile.ZipFile(dest) as z:assert len(z.namelist())==1 and z.testzip() is None
 received.append(dict(arquivo=name,bytes=dest.stat().st_size,sha256=digest,hash_match_previous_receipt=True,sediment_file_id=ids[name],preserved_path=str(dest)))
write(P/'ARQUIVOS_RECUPERADOS.csv',received)
(P/'RESTAURACAO_FONTES.json').write_text(json.dumps(received,ensure_ascii=False,indent=2)+'\n')
subprocess.run(['g++','-O3','-std=c++17',str(P/'reduzir_e_conferir_dez_estados.cpp'),'-o',str(TMP/'cedro_dez_estados')],check=True)
inventory=read(E/'cedro_extrator_win_v1_00/retorno_geral_20261112/CONTRATOS.csv');results=[];audits=[];names=['S38.2','S50','S61.8','R38.2','R61.8']
for tag in sorted({r['arquivo'][4:12] for r in parts}):
 cfg=E/'cedro_modelod_agosto_2026/resultado'/f'{tag}.config';lines=cfg.read_text().splitlines();head=lines[0].split();symbol,date=head[0:2];base,cut=int(head[2]),int(head[3]);original=[]
 for name,line in zip(names,lines[-5:]):
  eligible,buy,en,sl,tp=map(int,line.split());original.append(dict(name=name,eligible=bool(eligible),buy=bool(buy),entry5=D(en),sl5=D(sl),tp5=D(tp)))
 variant=copy.deepcopy(original)
 for lv in variant:
  sg=1 if lv['buy'] else -1;lv['tp5']=lv['entry5']+sg*250;lv['sl5']=lv['entry5']-sg*50
 bounds=sorted({int(l[k]) for l in original+variant for k in ['entry5','sl5','tp5']});config=P/f'{tag}.config';text=f'{symbol} {date} {base} {cut} {len(bounds)}\n'+' '.join(map(str,bounds))+'\n'
 for l in original+variant:text+=' '.join(str(int(x)) for x in [l['eligible'],l['buy'],l['entry5'],l['sl5'],l['tp5']])+'\n'
 config.write_text(text)
 direct=P/f'DIRETO_{tag}.csv';reduced=TMP/f'EVENTOS_{tag}.csv'
 with reduced.open('wb') as out:
  proc=subprocess.Popen([str(TMP/'cedro_dez_estados'),str(config),str(direct)],stdin=subprocess.PIPE,stdout=out,stderr=subprocess.PIPE)
  for part in sorted(r['arquivo'] for r in parts if r['arquivo'].startswith('WIN_'+tag+'_')):
   with zipfile.ZipFile(STORE/part) as z:
    with z.open(z.namelist()[0]) as f:
     while chunk:=f.read(1024*1024):proc.stdin.write(chunk)
  proc.stdin.close();message=proc.stderr.read().decode();assert proc.wait()==0,message
 stats=dict(x.split('=') for x in message.strip().split(';'));expected=next(r for r in inventory if r['dia']==tag and r['ativo']==symbol);assert int(stats['records'])==int(expected['registros'])
 old_direct=read(E/'cedro_modelod_agosto_2026/resultado'/f'DIRETO_{tag}.csv');current=read(direct)
 for a,b in zip(old_direct,current[:5]):assert a==b,(tag,'original changed',a,b)
 events=[dict(ord=int(r['ordinal_ALL']),msc=int(r['time_msc']),p=D(r['last'])) for r in read(reduced)];assert len(events)==int(stats['reduced'])
 py_orig=replay(events,original,cut,grid=True);py_variant=replay(events,variant,cut,grid=True)
 for states,rows in [(py_orig,current[:5]),(py_variant,current[5:])]:
  for l,row in zip(original,rows):
   st=states[l['name']];assert bool(int(row['entered']))==bool(st['entry_event']) and bool(int(row['closed']))==bool(st['exit_event'])
   if st['exit_event']:
    assert D(row['points'])==st['points'];assert int(row['entry_ord'])==st['entry_event']['ord'];assert int(row['exit_ord'])==st['exit_event']['ord']
 # Reverse only same-ms groups; keep chronological time. Baseline tie order
 # is not asserted as official; variant result must be invariant.
 alt=[ev for _,g in itertools.groupby(events,key=lambda e:e['msc']) for ev in reversed(list(g))];alt_state=replay(alt,variant,cut,grid=True)
 dayresults=[]
 for lv in variant:
  name=lv['name'];st=py_variant[name];tie=alt_state[name];orig=py_orig[name]
  assert bool(st['entry_event'])==bool(orig['entry_event'])
  if not st['entry_event']:continue
  assert st['status']=='ENCERRADA' and st['entry_event']==orig['entry_event']
  same=(st['reason'],st['points'])==(tie['reason'],tie['points']);mixed=[]
  for ms,g in itertools.groupby(events,key=lambda ev:ev['msc']):
   if not st['entry_event']['msc']<=ms<=st['exit_event']['msc']:continue
   ps=[ev['p'] for ev in g]
   if min(ps)<=min(lv['tp5'],lv['sl5']) and max(ps)>=max(lv['tp5'],lv['sl5']):mixed.append(ms)
  rr=dict(date=date,contract=symbol,level=name,reason=st['reason'],points=str(st['points']),original_points=str(orig['points']),entry_level=str(lv['entry5']),target_level=str(lv['tp5']),stop_level=str(lv['sl5']),entry_time=calendar(st['entry_event']['msc']),entry_ordinal=st['entry_event']['ord'],exit_time=calendar(st['exit_event']['msc']),exit_ordinal=st['exit_event']['ord'],exit_trade_price=str(st['exit_event']['p']),same_ms_reverse_result_invariant=same,mixed_barriers_same_ms='|'.join(map(str,mixed)),resolved=same and not mixed)
  results.append(rr);dayresults.append(rr)
 audits.append(dict(date=date,contract=symbol,full_stream_records=int(stats['records']),expected_records=int(expected['registros']),reduced_records=len(events),old_5_states_identical=True,python_vs_direct_all10_states=True,resolved_new_operations=sum(r['resolved'] for r in dayresults),new_operations=len(dayresults),reduced_events_sha256=hashlib.sha256(reduced.read_bytes()).hexdigest()))
 print(date,symbol,'OPS',len(dayresults),'POINTS',sum(D(r['points']) for r in dayresults),flush=True)
write(P/'CEDRO_50_250_OPERACOES_EXATAS.csv',results);(P/'AUDITORIA_CEDRO_50_250.json').write_text(json.dumps(audits,ensure_ascii=False,indent=2)+'\n')
print('CEDRO',len(results),'operacoes;saldo',sum(D(r['points']) for r in results),flush=True)
