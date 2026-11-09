"""Read-only audit of original Work sources against consolidated MT5 M1 exports.
Usage: python analisar_cobertura.py --new DIRECTORY --previous DIRECTORY --work DIRECTORY --diary FILE --out DIRECTORY
Raw inputs remain local; outputs are derived comparisons.
"""
import argparse,csv,json,hashlib
from pathlib import Path
from collections import defaultdict,Counter
from datetime import datetime,timedelta
from decimal import Decimal as D
p=argparse.ArgumentParser()
for k in ('new','previous','work','diary','contexts','out'):p.add_argument('--'+k,type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
def read(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter=';'))
def write(name,rows):
 if not rows:return
 with (a.out/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter=';',lineterminator='\n');w.writeheader();w.writerows(rows)
def dt(s):return datetime.strptime(s,'%Y.%m.%d %H:%M')
def prices(r):return tuple(D(r[k]) for k in ('open','high','low','close'))
def pn(s):return D(s.replace('.','').replace(',','.'))
def aggregate(rows):
 rows=sorted(rows,key=lambda x:x['time'])
 return {'time':rows[0]['time'],'open':D(rows[0]['open']),'high':max(D(r['high']) for r in rows),'low':min(D(r['low']) for r in rows),'close':D(rows[-1]['close']),'quantity':sum(D(r.get('real_volume',r.get('quantity',0))) for r in rows),'records':len(rows)}
native={};coverage=[];overlap=0
newstatus=read(a.new/'STATUS.csv');assert len(newstatus)==37
assert all(r['state']=='EXPORTADO_ESTAVEL' and r['attempts']=='2' and r['error']=='0' for r in newstatus)
assert sum(int(r['rows']) for r in newstatus)==417800
last=None
for r in newstatus:
 assert not last or r['from_inclusive']==last
 last=r['to_exclusive']
assert newstatus[0]['from_inclusive']=='2023.02.27 00:00:00' and last=='2026.03.01 00:00:00'
for root,isnew in [(a.new,True),(a.previous,False)]:
 for f in sorted(root.glob('M1_*.csv')):
  rows=read(f);assert [r['time'] for r in rows]==sorted(r['time'] for r in rows)
  assert len({r['time'] for r in rows})==len(rows)
  for r in rows:
   v=prices(r);assert all(x.is_finite() and x>0 for x in v) and v[2]<=min(v[0],v[3])<=max(v[0],v[3])<=v[1]
   if r['time'] in native:
    assert native[r['time']]==r;overlap+=1
   else:native[r['time']]=r
  if isnew:assert len(rows)==int(next(r['rows'] for r in newstatus if r['file']==f.name))
  coverage.append({'coleta':'NOVA' if isnew else 'ANTERIOR','arquivo':f.name,'linhas':len(rows),'primeira':rows[0]['time'],'ultima':rows[-1]['time']})
assert len(native)==497028 and overlap==2307
assert 'END;months=37;pending_months=0;rows=417800;io_failed=false' in a.diary.read_text(encoding='utf-8-sig')
# Original sources differ in duration; never compare M5 directly with M1.
work={};sources={};workqty={}
for f in sorted(a.work.glob('*.csv')):
 if f.name.startswith('WIN$N'):
  with f.open(encoding='cp1252',newline='') as h:
   for r in csv.DictReader(h,delimiter='\t'):
    key=(r['<DATE>']+' '+r['<TIME>'])[:16]
    assert key not in work
    work[key]={'time':key,**dict(zip(('open','high','low','close'),map(D,[r['<OPEN>'],r['<HIGH>'],r['<LOW>'],r['<CLOSE>']]))),'quantity':D(r['<VOL>'])}
    sources[key]='2023_MT5_M5'
 else:
  m1='_1min_' in f.name
  with f.open(encoding='cp1252',newline='') as h:
   for r in csv.reader(h,delimiter=';'):
    if len(r)<9 or r[0]!='WINFUT':continue
    key=datetime.strptime(r[1]+' '+r[2],'%d/%m/%Y %H:%M:%S').strftime('%Y.%m.%d %H:%M')
    if m1 and key<'2026.03.01':continue
    assert key not in work
    work[key]={'time':key,**dict(zip(('open','high','low','close'),map(pn,r[3:7]))),'quantity':pn(r[8])}
    sources[key]=key[:4]+'_Profit_'+('M1' if m1 else 'M5')
# Derive time-aligned five-minute groups from native minute bars.
buckets=defaultdict(list)
for k,r in sorted(native.items()):
 t=dt(k);buckets[t.replace(minute=t.minute//5*5).strftime('%Y.%m.%d %H:%M')].append(r)
native5={k:{**aggregate(v),'time':k} for k,v in buckets.items()}
diffs=[];qtydiff=[];missing=[];extras=[];summary=[];dayrows=[];daydiff=[]
for source in sorted(set(sources.values())):
 w={k:r for k,r in work.items() if sources[k]==source};mn,mx=min(w),max(w)
 n={k:r for k,r in (native if source.endswith('M1') else native5).items() if mn<=k<=mx}
 common=set(w)&set(n);pd=qd=0
 for k in sorted(common):
  np,wp=prices(n[k]),prices(w[k]);q=D(n[k].get('real_volume',n[k].get('quantity',0)));wq=w[k]['quantity']
  if np!=wp:
   pd+=1;diffs.append({'fonte':source,'time':k,'MT5_OHLC':'|'.join(map(str,np)),'Work_OHLC':'|'.join(map(str,wp)),'campos':'|'.join(x for i,x in enumerate(('O','H','L','C')) if np[i]!=wp[i]),'antes_18h':k[11:]<'18:00','M1_no_grupo':n[k].get('records',1)})
  if q!=wq:qd+=1;qtydiff.append({'fonte':source,'time':k,'MT5_quantidade':str(q),'Work_quantidade':str(wq),'diferenca':str(q-wq)})
 for k in sorted(set(w)-set(n)):missing.append({'fonte':source,'time':k})
 for k in sorted(set(n)-set(w)):extras.append({'fonte':source,'time':k,'dia_presente_Work':any(x.startswith(k[:10]) for x in w)})
 nd=defaultdict(list);wd=defaultdict(list)
 for k,r in n.items():nd[k[:10]].append(r)
 for k,r in w.items():wd[k[:10]].append(r)
 dequal=ddiff=0
 for day in sorted(set(wd)|set(nd)):
  nn=nd.get(day,[]);ww=wd.get(day,[]);equal=bool(nn and ww and prices(aggregate(nn))==prices(aggregate(ww)))
  if nn and ww:
   dequal+=int(equal);ddiff+=int(not equal)
  row={'fonte':source,'data':day,'barras_MT5':len(nn),'barras_Work':len(ww),'primeira_MT5':min(r['time'] for r in nn) if nn else '', 'primeira_Work':min(r['time'] for r in ww) if ww else '', 'ultima_MT5':max(r['time'] for r in nn) if nn else '', 'ultima_Work':max(r['time'] for r in ww) if ww else '', 'OHLC_dia_igual':equal,'MT5_OHLC':'|'.join(map(str,prices(aggregate(nn)))) if nn else '', 'Work_OHLC':'|'.join(map(str,prices(aggregate(ww)))) if ww else ''}
  dayrows.append(row)
  if nn and ww and not equal:daydiff.append(row)
 summary.append({'fonte':source,'primeira_Work':mn,'ultima_Work':mx,'Work_barras':len(w),'MT5_barras_no_intervalo':len(n),'comuns':len(common),'OHLC_iguais':len(common)-pd,'OHLC_diferentes':pd,'quantidade_diferente':qd,'faltantes_MT5':len(set(w)-set(n)),'extras_MT5':len(set(n)-set(w)),'dias_comuns':len(set(wd)&set(nd)),'dias_OHLC_igual':dequal,'dias_OHLC_diferente':ddiff})
gaps=[]
nd=defaultdict(list)
for k in sorted(native):nd[k[:10]].append(k)
for day,keys in sorted(nd.items()):
 for before,after in zip(keys,keys[1:]):
  gap=int((dt(after)-dt(before)).total_seconds()/60)-1
  if gap:gaps.append({'data':day,'antes':before,'depois':after,'minutos_ausentes_entre_barras':gap})
# Compare the actual strategy inputs for all 877 eligible Work dates.
contexts=read(a.contexts);assert len(contexts)==877
context_rows=[]
for c in contexts:
 day=c['Data'].replace('-','.');prev=c['PregaoAnterior'].replace('-','.')
 now=aggregate([native[k] for k in nd[day]])
 prior=aggregate([native[k] for k in nd[prev]])
 expected=tuple(D(c[k]) for k in ('Abertura','MaximaAnterior','MinimaAnterior','FechamentoAnterior'))
 got=(now['open'],prior['high'],prior['low'],prior['close'])
 context_rows.append({'data':c['Data'],'pregao_anterior':c['PregaoAnterior'],'abertura_HLC_anterior_igual':got==expected,'MT5_valores':'|'.join(map(str,got)),'Work_valores':'|'.join(map(str,expected)),'ajuste_Work_preservado':c['Ajuste'],'corte_preservado':c['Corte']})
assert all(r['abertura_HLC_anterior_igual'] for r in context_rows)
write('CONTEXTO_877_DATAS.csv',context_rows)
result={'nova_coleta':{'janelas_estaveis':37,'janelas_pendentes':0,'linhas':417800,'primeiro_M1':min(k for k in native if k<'2026.03.01'),'ultimo_M1':max(k for k in native if k<'2026.03.01'),'erro_gravacao':False},'consolidacao':{'M1_distintos':len(native),'dias_observados':len(nd),'primeiro':min(native),'ultimo':max(native),'sobreposicao_com_coleta_anterior_exata_todos_campos':overlap},'comparacao':summary,'total_comparado':{k:sum(r[k] for r in summary) for k in ('Work_barras','comuns','OHLC_iguais','OHLC_diferentes','faltantes_MT5','extras_MT5','quantidade_diferente','dias_comuns','dias_OHLC_igual','dias_OHLC_diferente')},'contextos_877_abertura_e_HLC_anterior_iguais':sum(r['abertura_HLC_anterior_igual'] for r in context_rows),'ajuste':'Mantido da referencia Work; esta coleta de candles nao o valida contra a B3.','diferencas_pre_18h':sum(r['antes_18h'] for r in diffs),'limitacao':'Igualdade na duracao original M5 nao certifica os minutos internos nem trajetoria de ticks. Mes estavel nao prova sessao completa. Datas e barras extras nao sao incorporadas automaticamente ao Work. A coleta nao testa ordens ou resultado financeiro.','sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [*sorted(a.new.glob('*.*')),*sorted(a.work.glob('*.csv')),a.diary,a.contexts]}}
for name,rows in [('COBERTURA.csv',coverage),('RESUMO_POR_FONTE.csv',summary),('OHLC_DIVERGENTE.csv',diffs),('QUANTIDADE_DIVERGENTE.csv',qtydiff),('FALTANTES_MT5.csv',missing),('EXTRAS_MT5.csv',extras),('COMPARACAO_POR_DIA.csv',dayrows),('DIAS_OHLC_DIVERGENTE.csv',daydiff),('LACUNAS_M1.csv',gaps)]:write(name,rows)
(a.out/'CONFERENCIA.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='sha256'},ensure_ascii=False,indent=2))
print('DIFFERENCES FIRST',diffs[:15]);print('DAILY DIFFERENCES',daydiff[:15]);print('GAPS',gaps[:15])
