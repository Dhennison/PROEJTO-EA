"""Auditoria integral Cedro, sem ordenar ou deduplicar negocios."""
from pathlib import Path
from decimal import Decimal as D
import csv,io,zipfile,subprocess,hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent;OUT=HERE/'auditoria_final';OUT.mkdir(exist_ok=True)
STORE=Path('/workspace/retorno_cedro_20261112/ticks');STORE.mkdir(exist_ok=True)
def read(p):return list(csv.DictReader(p.open(encoding='utf-8-sig'),delimiter=';'))
def write(p,rows):
 if not rows:p.write_text('');return
 with p.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter=';');w.writeheader();w.writerows(rows)
manifest=read(ROOT/'entregas/cedro_extrator_win_v1_00/retorno_geral_20261112/ARQUIVOS.csv')
inv=read(ROOT/'entregas/cedro_extrator_win_v1_00/retorno_geral_20261112/CONTRATOS.csv')
work=[] # Outubro fora da referencia Work
old=[] # Motor auditor C++ ja conferido com Python em setembro
complete=['20261015', '20261016', '20261019', '20261020', '20261021', '20261022', '20261023', '20261026', '20261027', '20261028', '20261029', '20261030']
assert len({r['time'] for r in work})==len(work)
parts=[];coverage=[];diffs=[];eod_diffs=[];summaries=[];regress=[];python_checks=0
with zipfile.ZipFile('/workspace/retorno_cedro_20261112/GERAL_CEDRO_WIN.zip') as general:
 for day in complete:
  print('AUDITANDO',day,flush=True)
  prefix=OUT/day;files=[]
  for meta in sorted([r for r in manifest if r['tipo']=='WIN_ZIP' and r['arquivo'].startswith('WIN_'+day+'_')],key=lambda r:r['arquivo']):
   dest=STORE/meta['arquivo']
   if not dest.exists():
    matches=list(Path('/workspace/attachments').glob('*/'+meta['arquivo']));assert len(matches)==1,(meta['arquivo'],len(matches));shutil.copyfile(matches[0],dest)
   digest=hashlib.sha256(dest.read_bytes()).hexdigest();assert digest==meta['sha256'] and dest.stat().st_size==int(meta['bytes'])
   parts.append({'arquivo':dest.name,'bytes':dest.stat().st_size,'sha256':digest,'OK':True});files.append(dest)
  assert len(files) in (2,3)
  proc=subprocess.Popen(['/tmp/cedro-auditar',day[:4]+'-'+day[4:6]+'-'+day[6:],'WINZ26',str(prefix)],stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
  for path in files:
   with zipfile.ZipFile(path) as z:
    assert len(z.namelist())==1
    with z.open(z.namelist()[0]) as source:
     while chunk:=source.read(1024*1024):proc.stdin.write(chunk)
  proc.stdin.close();message=proc.stderr.read().decode();assert proc.wait()==0,message
  stats=read(Path(str(prefix)+'_CONTRATOS.csv'));bars=read(Path(str(prefix)+'_M1.csv'))
  assert {r['ativo'] for r in stats}=={r['ativo'] for r in inv if r['dia']==day}
  for r in stats:
   expected=next(x for x in inv if x['dia']==day and x['ativo']==r['ativo'])
   for a,b in [('registros','registros'),('regressoes','regressoes_timestamp'),('empates','empates_consecutivos')]:assert int(r[a])==int(expected[b])
   assert r['primeiro']==expected['primeiro_timestamp_na_ordem'] and r['ultimo']==expected['ultimo_timestamp_na_ordem']
  oldday=next((r for r in old if r['dia']==day),None)
  if oldday:
   for r in stats:
    py=oldday['contratos'][r['ativo']]
    for a,b in [('registros','registros'),('regressoes','regressoes'),('empates','empates'),('quantidade','soma_campo4'),('open','open'),('high','high'),('low','low'),('close','close')]:assert D(r[a])==D(str(py[b]))
   prev=read(ROOT/f'entregas/cedro_extrator_win_v1_00/retorno_setembro_lote1_20261112/M1_WINV26_{day}.csv')
   assert len(prev)==len(bars)
   for a,b in zip(prev,bars):
    assert a['time']==b['time'].replace('-','.')
    for x,y in [('open','open'),('high','high'),('low','low'),('close','close'),('soma_campo4','volume_real'),('registros','registros')]:assert D(a[x])==D(b[y])
   python_checks+=1
  actual={r['time'].replace('-','.'):r for r in bars}
  selected=[r for r in work if r['time'].replace('.','').startswith(day)];pd=qd=missing=0
  for w in selected:
   got=actual.get(w['time'])
   if got is None:missing+=1;diffs.append({'dia':day,'minuto':w['time'],'campo':'SEM_TICK','Work':'','Cedro':''});continue
   pd+=any(D(w[k])!=D(got[k]) for k in ['open','high','low','close']);qd+=D(w['volume_real'])!=D(got['volume_real'])
   for k in ['open','high','low','close','volume_real']:
    if D(w[k])!=D(got[k]):diffs.append({'dia':day,'minuto':w['time'],'campo':k,'Work':w[k],'Cedro':got[k]})
  eod_name=next(n for n in general.namelist() if n.endswith(day+'_bmf.log'))
  eod=list(csv.DictReader(io.StringIO(general.read(eod_name).decode('utf-8-sig'))))
  for r in stats:
   match=next((e for e in eod if e['papel'].upper()==r['ativo']),None)
   if match:
    for a,b in [('open','open'),('high','high'),('low','low'),('close','last_trade'),('quantidade','volume_amount'),('registros','quantitytrades')]:
     if D(r[a])!=D(match[b]):eod_diffs.append({'dia':day,'ativo':r['ativo'],'campo':a,'ticks':r[a],'EOD':match[b]})
  anomalies=read(Path(str(prefix)+'_REGRESSOES.csv'))
  for a in anomalies:
   prev=a['linha_anterior'].split('|');now=a['linha_atual'].split('|')
   regress.append({'data':day,'ativo':a['ativo'],'ordinal_anterior':prev[0],'timestamp_anterior':prev[2],'preco_anterior':prev[3],'ordinal_atual':now[0],'timestamp_atual':now[2],'preco_atual':now[3],'quantidade_atual':now[4],'campo7':now[7],'campo8':now[8]})
  coverage.append({'data':day,'barras_Work':len(selected),'Work_sem_tick':missing,'M1_preco_diferente':pd,'M1_quantidade_diferente':qd,'M1_Cedro':len(bars),'regressoes':sum(int(r['regressoes']) for r in stats)})
  summaries.append({'data':day,'registros_WIN':sum(int(r['registros']) for r in stats),'registros_V':int(next(r['registros'] for r in stats if r['ativo']=='WINZ26'))})
  print('CONFERIDO',day,'Work=',len(selected),'diferencas_preco=',pd,'regressoes=',len(anomalies),flush=True)
write(OUT/'PARTES_CONFERIDAS.csv',parts);write(OUT/'COBERTURA.csv',coverage);write(OUT/'DIFERENCAS_M1.csv',diffs);write(OUT/'DIFERENCAS_EOD.csv',eod_diffs);write(OUT/'REGRESSOES_LOCALIZADAS.csv',regress);write(OUT/'CONTAGENS.csv',summaries)
result={'ZIPs':len(parts),'datas':len(coverage),'registros_WIN':sum(r['registros_WIN'] for r in summaries),'datas_Cpp_vs_Python_independentes':python_checks,'regressoes':regress,'EOD_diferencas':len(eod_diffs),'novos_resultados_estrategia':False,'mes_completo':False}
(OUT/'AUDITORIA.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
