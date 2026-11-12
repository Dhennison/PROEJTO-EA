"""Replay Cedro com motor anterior e conferencia independente em todos os negocios."""
from pathlib import Path
from decimal import Decimal as D
import csv, hashlib, importlib.util, io, json, subprocess, sys, zipfile
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('motor_fixo',ROOT/'entregas/fechamento_agosto_v1_11/analise/motor_precos.py')
motor=importlib.util.module_from_spec(spec);spec.loader.exec_module(motor)
def read(p):return list(csv.DictReader(p.open(encoding='utf-8-sig'),delimiter=';'))
def write(p,rows):
 if not rows:return
 with p.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter=';');w.writeheader();w.writerows(rows)
def config(path,symbol,date,ls,cut):
 bounds=motor.boundaries(ls)
 text=f'{symbol} {date.replace(".","-")} {motor.epoch(date+" 00:00:00")} {cut} {len(bounds)}\n'+ ' '.join(str(int(x)) for x in bounds)+'\n'
 for l in ls:text+=' '.join(str(int(x)) for x in [l['eligible'],l['buy'],l['entry5'],l['sl5'],l['tp5']])+'\n'
 path.write_text(text)
def events(path):return [{'ord':int(r['ordinal_ALL']),'msc':int(r['time_msc']),'p':D(r['last'])} for r in read(path)]
def direct_check(ls,states,path):
 direct=read(path);assert len(direct)==5
 for i,(l,r) in enumerate(zip(ls,direct)):
  s=states[l['name']];en=s['entry_event'];ex=s['exit_event']
  assert bool(int(r['eligible']))==l['eligible']
  assert bool(int(r['entered']))==bool(en) and bool(int(r['closed']))==bool(ex)
  if en:
   assert (int(r['entry_ord']),int(r['entry_ms']),D(r['entry_price']))==(en['ord'],en['msc'],en['p'])
  if ex:
   assert (int(r['exit_ord']),int(r['exit_ms']),D(r['exit_price']))==(ex['ord'],ex['msc'],ex['p'])
   assert D(r['theory_exit'])==s['exit_theory'] and D(r['points'])==s['points']
   assert {'STOP':1,'ALVO':2,'CORTE_LAST':3}[s['reason']]==int(r['reason'])
def calculate():
 out=HERE/'resultado';out.mkdir(exist_ok=True)
 assert not (out/'RESULTADO.json').exists(),'Resultado congelado: use nova versao/pasta para reprocessar.'
 reduced=Path('/workspace/retorno_cedro_20261112/eventos_reduzidos');reduced.mkdir(exist_ok=True)
 refs=read(ROOT/'entregas/fechamento_agosto_v1_11/MQL5/Files/MD_Agosto_2026_Referencias.csv')
 baseline=read(ROOT/'entregas/fechamento_agosto_v1_11/analise/WORK_AGOSTO.csv')
 original={(r['Data'],r['Nível']):r for r in baseline};assert len(original)==43
 assert sum(D(r['Pontos']) for r in baseline)==D('-387.164995')
 expected=read(ROOT/'entregas/cedro_extrator_win_v1_00/retorno_geral_20261112/ARQUIVOS.csv')
 inventory=read(ROOT/'entregas/cedro_extrator_win_v1_00/retorno_geral_20261112/CONTRATOS.csv')
 daily=[];rows=[];checks=[]
 for ref in refs:
  date=ref['date'];tag=date.replace('.','');iso=date.replace('.','-');symbol='WINQ26' if tag<'20260812' else 'WINV26';cut=motor.epoch(ref['cut_server']);ls=motor.levels(ref)
  cfg=out/(tag+'.config');config(cfg,symbol,date,ls,cut)
  dest=reduced/('EVENTOS_'+tag+'.csv');direct=out/('DIRETO_'+tag+'.csv')
  print('CALCULANDO',date,symbol,flush=True)
  with dest.open('wb') as f:
   proc=subprocess.Popen(['/tmp/cedro-reduzir',str(cfg),str(direct)],stdin=subprocess.PIPE,stdout=f,stderr=subprocess.PIPE)
   for part in sorted([r for r in expected if r['tipo']=='WIN_ZIP' and r['arquivo'].startswith('WIN_'+tag+'_')],key=lambda r:r['arquivo']):
    path=Path('/workspace/retorno_cedro_20261112/ticks')/part['arquivo']
    assert hashlib.sha256(path.read_bytes()).hexdigest()==part['sha256']
    with zipfile.ZipFile(path) as z:
     assert len(z.namelist())==1
     with z.open(z.namelist()[0]) as inp:
      while True:
       chunk=inp.read(1024*1024)
       if not chunk:break
       proc.stdin.write(chunk)
   proc.stdin.close();log=proc.stderr.read().decode();assert proc.wait()==0,log
  stats=dict(x.split('=') for x in log.strip().split(';'))
  expected_count=next(int(r['registros']) for r in inventory if r['dia']==tag and r['ativo']==symbol)
  assert int(stats['records'])==expected_count
  ev=events(dest);assert len(ev)==int(stats['reduced'])
  assert ev[0]['p']==D(ref['open'])
  assert ev[0]['msc']//60000==motor.epoch(ref['first_server'])//60000
  cutoff=next(t for t in ev if t['msc']>=cut);assert cutoff['msc']<cut+60000
  s=motor.replay(ev,ls,cut,grid=True,strict=False);direct_check(ls,s,direct)
  checks.append({'data':iso,'contrato':symbol,'negocios_referencia':expected_count,'eventos_reduzidos':len(ev),'estados_conferidos':5,'motor_antigo_vs_fluxo_integral_OK':True,'abertura_OK':True,'primeiro_negocio_corte':motor.calendar(cutoff['msc']),'eventos_sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
  dayrows=[]
  for l in ls:
   state=s[l['name']];en=state['entry_event'];ex=state['exit_event'];w=original.get((iso,l['name']))
   assert state['status']!='ABERTA',(date,l['name'])
   row={'data':iso,'escopo':'COMPLEMENTO_FORA_WORK' if tag=='20260803' else 'WORK_ORIGINAL','contrato':symbol,'nivel':l['name'],'estado':state['status'],'entrada_teorica':str(state['entry_theory']) if en else '', 'hora_entrada':motor.calendar(en['msc']) if en else '', 'ordinal_entrada':en['ord'] if en else '', 'negocio_entrada':str(en['p']) if en else '', 'stop_grade5':str(l['sl5']),'alvo_grade5':str(l['tp5']),'hora_saida':motor.calendar(ex['msc']) if ex else '', 'ordinal_saida':ex['ord'] if ex else '', 'negocio_saida':str(ex['p']) if ex else '', 'saida_teorica':str(state['exit_theory']) if ex else '', 'motivo':state['reason'] or '', 'pontos':str(state['points']) if ex else '', 'Work_pontos':w['Pontos'] if w else '', 'Work_motivo':w['Motivo'] if w else '', 'presenca':('COMPLEMENTO' if tag=='20260803' else 'AMBOS' if en and w else 'EXTRA_NOSSO' if en else 'AUSENTE_NOSSO' if w else 'SEM_OPERACAO_EM_AMBOS')}
   rows.append(row);dayrows.append(row)
  ours=sum((D(r['pontos']) for r in dayrows if r['pontos']),D(0));wp=sum((D(r['Work_pontos']) for r in dayrows if r['Work_pontos']),D(0))
  daily.append({'data':iso,'escopo':'COMPLEMENTO_FORA_WORK' if tag=='20260803' else 'WORK_ORIGINAL','contrato':symbol,'Work_pontos':str(wp) if tag!='20260803' else '', 'nosso_pontos':str(ours),'diferenca':str(ours-wp) if tag!='20260803' else '', 'operacoes_Work':sum(bool(r['Work_pontos']) for r in dayrows),'operacoes_nossas':sum(bool(r['hora_entrada']) for r in dayrows)})
  print('CONFERIDO',date,ours,'pontos',flush=True)
 main=[r for r in daily if r['escopo']=='WORK_ORIGINAL'];supp=[r for r in daily if r['escopo']!='WORK_ORIGINAL'];assert len(main)==20 and len(supp)==1
 ours=sum((D(r['nosso_pontos']) for r in main),D(0));work=sum((D(r['Work_pontos']) for r in main),D(0))
 executed=[r for r in rows if r['escopo']=='WORK_ORIGINAL' and r['hora_entrada']]
 from collections import Counter
 summary={'mes':'2026-08','fonte':'CEDRO_TICK_BMF','criterio':'GRADE5_TOQUE_1_CONTRATO_NIVEIS_CONDICIONAIS','status':'CONCLUIDO_SOBRE_ALIMENTACAO_RECEBIDA_COM_RESSALVAS','dias_Work':20,'dias_suplementares':1,'Work_pontos':str(work),'nosso_principal_pontos':str(ours),'diferenca':str(ours-work),'operacoes_Work':43,'operacoes_nossas':len(executed),'motivos':dict(Counter(r['motivo'] for r in executed)),'complemento_03_agosto':supp[0],'estados_conferidos_independentemente':len(checks)*5,'todos_conferidos':True,'preenchimentos_reais_comprovados':False,'custos_inclusos':False,'limites':['Sem fila, custos ou garantia de preenchimento; entrada e saida creditadas nos niveis.','Saida em registro posterior a entrada, inclusive quando mesmo milissegundo.','Corte no primeiro negocio do minuto18:00.','Condicoes preservadas sem filtro. Sem garantia independente da ordenacao dos negocios com timestamp empatado.','OHLC/quantidade M1 conferem com Work no horario operado; divergencias18:24 posteriores ao corte.','03/08 fora do Work original, nao somado ao principal.','Setembro anterior permanece arquivado; nova serie Cedro identificada separadamente.'],'sha256_motor_anterior':hashlib.sha256((ROOT/'entregas/fechamento_agosto_v1_11/analise/motor_precos.py').read_bytes()).hexdigest()}
 write(out/'TODOS_NIVEIS.csv',rows);write(out/'POR_OPERACAO.csv',[r for r in rows if r['hora_entrada']]);write(out/'DIARIO_PRINCIPAL.csv',main);write(out/'DIARIO_COMPLEMENTAR.csv',supp);write(out/'VALIDACAO_POR_DIA.csv',checks)
 (out/'RESULTADO.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');print(json.dumps(summary,ensure_ascii=False,indent=2),flush=True)
if __name__=='__main__':calculate()
