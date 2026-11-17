from pathlib import Path
from decimal import Decimal as D
import csv,json,zipfile,io,pickle,collections,sys,re
import numpy as np
P=Path(__file__).parent;R=P.parents[1];E=R/'entregas';CACHE=Path('/workspace/work/estudo_saidas');CACHE.mkdir(exist_ok=True)
sys.path.insert(0,str(E/'fechamento_agosto_v1_11/analise'));from motor_precos import levels
sources=[]
def read(p):
 sources.append(str(p.relative_to(R)))
 with p.open(encoding='utf-8-sig') as f:return list(csv.DictReader(f,delimiter=';'))
refs={};ops=[]
def collect(p,refpath,opfile='OPERACOES_FINAIS.csv'):
 for r in read(refpath):refs[r['date']]=r
 ops.extend(read(p/opfile))
for pre,val in [('preparacao_2024_20261117','validacao_replay_2024_20261117'),('preparacao_jan_nov_2025_20261115','validacao_lote_2025_20261116')]:
 for p in sorted((E/val).glob('[01][0-9]_*')):
  if not p.is_dir():continue
  refp=E/pre/p.name/'REFERENCIAS.csv';collect(p,refp)
for r in read(E/'preparacao_2024_20261117/complemento_ajustes_02a05jan/REFERENCIAS.csv'):refs[r['date']]=r
for folder,refname in [('profit_dezembro_2025_20261115','REFERENCIAS_DEZEMBRO.csv'),('profit_janeiro_20261115','REFERENCIAS_JANEIRO.csv'),('profit_fevereiro_20261114','REFERENCIAS_FEVEREIRO.csv'),('profit_marco_20261113','REFERENCIAS_MARCO.csv'),('profit_abril_20261113','REFERENCIAS_ABRIL.csv'),('profit_maio_20261113','REFERENCIAS_MAIO.csv'),('profit_junho_20261113','REFERENCIAS_JUNHO.csv')]:
 p=E/folder
 if not (p/refname).exists():refname=next(p.glob('REFERENCIAS*.csv')).name
 collect(p,p/refname)
p=E/'profit_winq26_julho_20261113';refs.update({r['date']:r for r in read(p/'REFERENCIAS_JULHO.csv')});resolved={(r['date'],r['level']):r for r in read(p/'REPLAY_OPERACOES_RESOLVIDAS.csv')}
for r in read(p/'OPERACOES_POSSIBILIDADES.csv'):
 rr=resolved.get((r['date'],r['level']));ops.append(dict(date=r['date'],level=r['level'],points=rr['points'] if rr else r['min_points'],entry=rr['entry_time'] if rr else r['entry_minute']+':00_CANDLE',contract='WINQ26'))
configs={}
for mo,folder,sub in [('08','agosto','resultado'),('09','setembro','resultado'),('10','outubro','resultado_mensal')]:
 p=E/f'cedro_modelod_{folder}_2026'/sub
 for r in read(p/'TODOS_NIVEIS.csv'):
  if r['estado']=='ENCERRADA':ops.append(dict(date=r['data'],level=r['nivel'],points=r['pontos'],entry=r['hora_entrada'][-12:],contract=r['contrato']))
 cfgs=(E/f'cedro_modelod_{folder}_2026').rglob('*.config')
 for cfg in cfgs:
  if cfg.stem.isdigit() and len(cfg.stem)==8:
   lines=cfg.read_text().splitlines();ls={}
   for n,line in zip(['S38.2','S50','S61.8','R38.2','R61.8'],lines[-5:]):
    eligible,buy,en,sl,tp=map(int,line.split());ls[n]=dict(eligible=bool(eligible),buy=bool(buy),entry5=en,sl5=sl,tp5=tp)
   date=cfg.stem[:4]+'-'+cfg.stem[4:6]+'-'+cfg.stem[6:];configs[date]=ls
base_daily=read(E/'resultado_niveis_202401_202610_20261117/CURVAS_DIARIAS_POR_NIVEL.csv');days=sorted({r['date'] for r in base_daily});assert len(days)==709
bars=collections.defaultdict(list);source={}
with zipfile.ZipFile(E/'arquivo_conversa_20261111/originais/ORIGINAIS_PARTE_005.zip') as z:blob=z.read(next(n for n in z.namelist() if n.endswith('/EXPORT110_1794243035_5791.zip')))
with zipfile.ZipFile(io.BytesIO(blob)) as z:
 for n in z.namelist():
  if re.search(r'M1_202[456]\d\d.csv$',n):
   for r in csv.DictReader(io.StringIO(z.read(n).decode('utf-8-sig')),delimiter=';'):
    day=r['time'][:10].replace('.','-')
    if day not in days:continue
    tm=r['time'][11:];bars[day].append((tm,*[int(D(r[k])) for k in ['open','high','low','close']],int(r['real_volume'])));source[day]='MT5_M1'
# Profit M1 original covers March through September2026; prefer it there.
with zipfile.ZipFile(E/'historico_work_modelo_d_20261105/replay_setembro_20261106/originais/Candles_Originais_Modelo_D_2023_2026.zip') as z:
 text=z.read('WINFUT_F_0_1min_01-01-2026_22-09-2026.csv').decode('cp1252')
 extra=collections.defaultdict(list)
 for r in csv.reader(io.StringIO(text),delimiter=';'):
  if r[0]=='Ativo':continue
  dd,mm,yy=r[1].split('/');day=f'{yy}-{mm}-{dd}'
  if day not in days or day<'2026-03-01':continue
  def br(x):return int(D(x.replace('.','').replace(',','.')))
  extra[day].append((r[2][:5],*[br(v) for v in r[3:7]],br(r[8])))
 for day,rr in extra.items():bars[day]=rr;source[day]='PROFIT_M1'
# August audit bars use M1_CONTRACT_DATE naming in extractor receipt folders.
for fp in (E/'cedro_extrator_win_v1_00').rglob('retorno_agosto*/M1_WIN*.csv'):
 rr=read(fp)
 if not rr:continue
 day=rr[0]['time'][:10].replace('.','-')
 bars[day]=[(r['time'][11:],*[int(D(r[k])) for k in ['open','high','low','close']],int(D(r['soma_campo4']))) for r in rr];source[day]='CEDRO_AUDIT_M1'
# Cedro audit bars override MT5, preserving its source distinction.
for folder in ['setembro','outubro']:
 for p in (E/f'cedro_modelod_{folder}_2026').rglob('*_M1.csv'):
  rr=read(p)
  if not rr or 'time' not in rr[0]:continue
  day=rr[0]['time'][:10]
  if day not in days:continue
  bars[day]=[(r['time'][11:],*[int(D(r[k])) for k in ['open','high','low','close']],int(r['volume_real'])) for r in rr];source[day]='CEDRO_AUDIT_M1'
for day in bars:bars[day].sort()
assert set(days)<=set(bars),(set(days)-set(bars))
# Collect complete replay minutes only. Match OHLC and quantity before use.
replay={};candidate=collections.defaultdict(list)
for folder in ['validacao_replay_2024_20261117','validacao_lote_2025_20261116']:
 for meta in json.loads((E/folder/'INVENTARIO_FONTES_EM_USO.json').read_text()):
  path=Path(meta['cache'])
  if not path.exists():continue
  rr=pickle.loads(path.read_bytes());groups=collections.defaultdict(list)
  for tm,price,q,ordinal in reversed(rr):groups[tm[:5]].append((tm,price,q))
  for tm,es in groups.items():candidate[(meta['date'],tm)].append(es)
# Original 2026 replay attachments; dates are in each sheet name.
import openpyxl
for p in Path('/workspace/attachments').glob('*/*.xlsx'):
 month=1 if 'Janeiro' in p.name else 2 if 'Fevereiro' in p.name else 3 if 'Março' in p.name else 12 if 'Dezembro' in p.name else None
 if month is None:continue
 wb=openpyxl.load_workbook(p,read_only=True,data_only=True)
 for sh in wb:
  match=re.match(r'(\d\d)-(\d\d)',sh.title)
  if not match:continue
  day=f'{2025 if month==12 else 2026}-{month:02d}-{int(match[1]):02d}';groups=collections.defaultdict(list)
  for row in sh.iter_rows(min_row=2,values_only=True):
   if not row[0]:continue
   if not isinstance(row[0],str) or not re.fullmatch(r'\d\d:\d\d:\d\d\.\d\d\d',row[0]):continue
   def num(x):return int(D(x.replace('.','').replace(',','.'))) if isinstance(x,str) else int(x)
   groups[row[0][:5]].append((row[0],num(row[2]),num(row[3])))
  for tm,es in groups.items():candidate[(day,tm)].append(list(reversed(es)))
for (day,tm),copies in candidate.items():
 b=next((b for b in bars[day] if b[0]==tm),None)
 if b is None:continue
 for es in copies:
  if (es[0][1],max(x[1] for x in es),min(x[1] for x in es),es[-1][1])==b[1:5] and sum(x[2] for x in es)==b[5]:
   replay[(day,tm)]=es;break
normal=[]
for r in ops:
 day=r['date'];l=r['level'];lv=configs[day][l] if day in configs else next(x for x in levels(refs[day]) if x['name']==l)
 en=int(lv['entry5']);sl=int(lv['sl5']);tp=int(lv['tp5']);entry=r['entry'][:5]
 assert re.fullmatch(r'\d\d:\d\d',entry),(day,l,r['entry'])
 normal.append(dict(date=day,level=l,entry_minute=entry,entry=en,tp=tp,sl=sl,buy=lv['buy'],original=int(D(r['points'])),contract=r.get('contract',''),bar_source=source[day]))
assert len(normal)==1485 and len({(r['date'],r['level']) for r in normal})==1485
frozen=read(E/'resultado_niveis_202401_202610_20261117/OPERACOES_NORMALIZADAS.csv');assert sorted((r['date'],r['level'],int(D(r['points']))) for r in frozen)==sorted((r['date'],r['level'],r['original']) for r in normal)
data=dict(days=days,bars=dict(bars),source=source,replay=replay,ops=normal,sources=sorted(set(sources)))
(CACHE/'dados.pickle').write_bytes(pickle.dumps(data,protocol=4))
(P/'ACERVO_UTILIZADO.json').write_text(json.dumps(dict(days=len(days),ops=len(normal),sources=sorted(set(sources)),full_replay_minutes=len(replay),bar_sources=dict(collections.Counter(source.values())),limitation='Cedro audit M1 available AugustOctober;individual ticks used only where available;new ambiguous sequences remain pending'),ensure_ascii=False,indent=2)+'\n')
print('DATA',len(days),len(normal),'REPLAY',len(replay),collections.Counter(source.values()),flush=True)
