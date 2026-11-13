"""Calcula somente datas completas recebidas. Nao publica parcial como mes fechado."""
from pathlib import Path
from decimal import Decimal as D
import csv,io,zipfile,subprocess,hashlib,json,importlib.util
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent;OUT=HERE/'resultado_restantes';OUT.mkdir(exist_ok=True)
spec=importlib.util.spec_from_file_location('anterior',ROOT/'entregas/cedro_modelod_setembro_2026/calcular.py');helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper);motor=helper.motor
read=helper.read
write=helper.write
state=json.loads((HERE/'recepcao/ESTADO.json').read_text());days=[d for d in state['datas_completas'] if d>'20261014']
assert len(days)==12
audit=json.loads((HERE/'auditoria_final/AUDITORIA.json').read_text());assert audit['datas']==12 and audit['ZIPs']==26
assert len(audit['regressoes'])==1 and audit['regressoes'][0]['data']=='20261028' # Conhecida/localizada;tratada sem excluir negocio
assert not (OUT/'PARCIAL.json').exists(),'Preservar resultado: use outra versao para reprocessar.'
manifest=read(ROOT/'entregas/cedro_extrator_win_v1_00/retorno_geral_20261112/ARQUIVOS.csv');inventory=read(ROOT/'entregas/cedro_extrator_win_v1_00/retorno_geral_20261112/CONTRATOS.csv')
eods={}
with zipfile.ZipFile('/workspace/retorno_cedro_20261112/GERAL_CEDRO_WIN.zip') as z:
 for name in z.namelist():
  if not name.endswith('_bmf.log'):continue
  tag=name.split('_')[1];eods[tag]={r['papel'].upper():r for r in csv.DictReader(io.StringIO(z.read(name).decode('utf-8-sig'))) if r['papel'].upper().startswith('WIN')}
private=Path('/workspace/retorno_cedro_20261112/eventos_reduzidos_outubro');private.mkdir(exist_ok=True)
refs=[];allrows=[];daily=[];checks=[]
for day in days:
 assert day>'20261014'
 date=day[:4]+'.'+day[4:6]+'.'+day[6:];symbol='WINZ26';prev=max(k for k in eods if k<day and symbol in eods[k]);now=eods[day][symbol];old=eods[prev][symbol]
 first=next(r['primeiro_timestamp_na_ordem'] for r in inventory if r['dia']==day and r['ativo']==symbol)
 ref={'date':date,'symbol':symbol,'first_server':first[:16].replace('-','.')+':00','cut_server':date+' 18:00:00','open':now['open'],'high_prev':old['high'],'low_prev':old['low'],'close_prev':old['last_trade'],'adjustment':old['adjust'],'end_server':date+' 18:25:00','pregao_contexto':prev,'fonte':'EOD_CEDRO_MESMO_CONTRATO_FORA_WORK'};refs.append(ref)
 ls=motor.levels(ref);cut=motor.epoch(ref['cut_server']);cfg=OUT/(day+'.config');helper.config(cfg,symbol,date,ls,cut)
 reduced=private/('EVENTOS_'+day+'.csv');direct=OUT/('DIRETO_'+day+'.csv')
 print('CALCULANDO',day,flush=True)
 with reduced.open('wb') as f:
  sorter=None
  if day=='20261028':
   sorter=subprocess.Popen(['sort','--stable','-t','|','-k3,3','-k1,1n','-S','256M','-T','/workspace/retorno_cedro_20261112'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
   proc=subprocess.Popen(['/tmp/cedro-reduzir-setembro',str(cfg),str(direct),'time'],stdin=sorter.stdout,stdout=f,stderr=subprocess.PIPE)
   sorter.stdout.close();feed=sorter.stdin
  else:
   proc=subprocess.Popen(['/tmp/cedro-reduzir-setembro',str(cfg),str(direct)],stdin=subprocess.PIPE,stdout=f,stderr=subprocess.PIPE);feed=proc.stdin
  for r in sorted([r for r in manifest if r['tipo']=='WIN_ZIP' and r['arquivo'].startswith('WIN_'+day+'_')],key=lambda r:r['arquivo']):
   path=Path('/workspace/retorno_cedro_20261112/ticks')/r['arquivo'];assert hashlib.sha256(path.read_bytes()).hexdigest()==r['sha256']
   with zipfile.ZipFile(path) as z:
    with z.open(z.namelist()[0]) as source:
     while chunk:=source.read(1024*1024):feed.write(chunk)
  feed.close()
  if sorter:serr=sorter.stderr.read().decode();assert sorter.wait()==0,serr
  log=proc.stderr.read().decode();assert proc.wait()==0,log
 stats=dict(s.split('=') for s in log.strip().split(';'));assert int(stats['records'])==int(next(r['registros'] for r in inventory if r['dia']==day and r['ativo']==symbol))
 ev=helper.events(reduced);assert len(ev)==int(stats['reduced']) and ev[0]['p']==D(ref['open']);assert ev[0]['msc']//60000==motor.epoch(ref['first_server'])//60000
 exitcut=next(t for t in ev if t['msc']>=cut);assert exitcut['msc']<cut+60000
 result=motor.replay(ev,ls,cut,True,False);helper.direct_check(ls,result,direct)
 checks.append({'data':date,'estados':5,'fluxo_integral_vs_reduzido':True,'primeiro_negocio_corte':motor.calendar(exitcut['msc']),'negocios_referencia':int(stats['records']),'eventos_reduzidos':len(ev)})
 active=[]
 for l in ls:
  s=result[l['name']];assert s['status']!='ABERTA';en=s['entry_event'];ex=s['exit_event']
  r={'data':date.replace('.','-'),'contrato':symbol,'nivel':l['name'],'estado':s['status'],'entrada_teorica':str(s['entry_theory']) if en else '', 'stop_grade5':str(l['sl5']),'alvo_grade5':str(l['tp5']),'hora_entrada':motor.calendar(en['msc']) if en else '', 'ordinal_entrada':en['ord'] if en else '', 'negocio_entrada':str(en['p']) if en else '', 'hora_saida':motor.calendar(ex['msc']) if ex else '', 'ordinal_saida':ex['ord'] if ex else '', 'negocio_saida':str(ex['p']) if ex else '', 'saida_teorica':str(s['exit_theory']) if ex else '', 'motivo':s['reason'] or '', 'pontos':str(s['points']) if ex else ''};allrows.append(r)
  if en:active.append(r)
 points=sum((D(r['pontos']) for r in active),D(0));daily.append({'data':date.replace('.','-'),'pontos':str(points),'operacoes':len(active),'Work':'FORA_ESCOPO_WORK'})
 print('CONFERIDO',day,points,flush=True)
from collections import Counter
executed=[r for r in allrows if r['hora_entrada']];subtotal=sum((D(r['pontos']) for r in daily),D(0))
summary={'mes':'2026-10','status':'LOTE_12_PREGOES_RESTANTES_CALCULADO','datas_calculadas':[r['data'] for r in daily],'pregoes_calculados':12,'subtotal_pontos':str(subtotal),'operacoes':len(executed),'motivos':dict(Counter(r['motivo'] for r in executed)),'Work_comparavel':False,'dados_recebidos_ZIPs':48,'ZIPs_processados_datas_completas':26,'pregoes_restantes':0,'ZIPs_faltantes':0,'dia14_parcial_nao_calculado':False,'estados_validados':60,'criterio':'MODELO_D_ORIGINAL_1_CONTRATO_GRADE5_TOQUE','preenchimentos_reais_comprovados':False,'custos_inclusos':False,'todos_registros_preservados':True}
for name,rows in [('DIARIO_PARCIAL.csv',daily),('TODOS_NIVEIS.csv',allrows),('POR_OPERACAO.csv',executed),('REFERENCIAS.csv',refs),('VALIDACAO.csv',checks)]:write(OUT/name,rows)
(OUT/'PARCIAL.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');print(json.dumps(summary,ensure_ascii=False,indent=2),flush=True)
