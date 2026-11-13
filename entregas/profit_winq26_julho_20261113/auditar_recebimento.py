from pathlib import Path
import csv,datetime as dt,collections,json,openpyxl,hashlib
out=Path('/workspace/PROEJTO-EA/entregas/profit_winq26_julho_20261113')
p=Path('/workspace/attachments/6340f23a-420a-4dcd-8f7d-09045a9bacd4/WINQ26_F_0_1min_17-06-2026_12-08-2026.csv')
num=lambda x:float(x.replace('.','').replace(',','.'))
bars={};dups=0
for r in csv.reader(p.read_bytes().decode('cp1252').splitlines(),delimiter=';'):
 t=dt.datetime.strptime(r[1]+' '+r[2],'%d/%m/%Y %H:%M:%S');dups+=t in bars;bars[t]=tuple(num(x) for x in r[3:7])
xp=Path('/workspace/attachments/538fea08-712a-4176-9493-e61afc15c395/JUN a AGO.xlsx')
w=openpyxl.load_workbook(xp,read_only=True,data_only=True);sheet=w.active
adj=collections.defaultdict(set);xb={};bad=0
for r in sheet.iter_rows(min_row=2,values_only=True):
 if not isinstance(r[0],dt.datetime):continue
 xb[r[0]]=tuple(r[1:5]);
 if r[5] is not None:adj[r[0].date()].add(r[5])
common=set(bars)&set(xb);diff=[t.isoformat() for t in sorted(common) if bars[t]!=xb[t]]
july=sorted(t for t in bars if t.month==7);days=sorted(set(t.date() for t in july))
mt={}
with open('/workspace/exportacao_winn_110/EXPORT110_1794241201_5300/M1_202607.csv',encoding='utf-8-sig') as f:
 for r in csv.DictReader(f,delimiter=';'):mt[dt.datetime.strptime(r['time'],'%Y.%m.%d %H:%M')]=tuple(float(r[k]) for k in ('open','high','low','close'))
jcommon=set(july)&set(mt);jdiff=[t.isoformat() for t in sorted(jcommon) if bars[t]!=mt[t]]
with (out/'AJUSTES_JULHO_PLANILHA.csv').open('w',newline='') as f:
 wr=csv.writer(f,delimiter=';');wr.writerow(['data','ajustes_distintos_exibidos','barras_csv','primeiro_horario','ultimo_horario'])
 for d in days:
  ts=[t for t in july if t.date()==d];wr.writerow([d.isoformat(),'|'.join(map(str,sorted(adj[d]))),len(ts),min(ts).strftime('%H:%M'),max(ts).strftime('%H:%M')])
res={'csv_barras':len(bars),'csv_duplicadas_timestamp':dups,'csv_inicio':min(bars).isoformat(),'csv_fim':max(bars).isoformat(),'xlsx_barras':len(xb),'comuns_csv_xlsx':len(common),'divergencias_ohlc_csv_xlsx':len(diff),'julho_dias':len(days),'julho_barras':len(july),'julho_comuns_mt5':len(jcommon),'julho_divergencias_ohlc_mt5':len(jdiff),'julho_exclusivas_profit':len(set(july)-set(mt)),'julho_exclusivas_mt5':len(set(mt)-set(july)),'julho_dias_ajuste_unico':sum(len(adj[d])==1 for d in days),'julho_dias_ajuste_ausente':sum(not adj[d] for d in days),'julho_dias_ajuste_variavel':{str(d):sorted(adj[d]) for d in days if len(adj[d])>1},'primeira_barra_18jun':min(t for t in bars if t.date()==dt.date(2026,6,18)).isoformat(),'print_18jun_0903_ohlc':bars.get(dt.datetime(2026,6,18,9,3)),'julho31_inicio':min(t for t in july if t.day==31).isoformat(),'sha256_csv':hashlib.sha256(p.read_bytes()).hexdigest(),'sha256_xlsx':hashlib.sha256(xp.read_bytes()).hexdigest()}
(out/'AUDITORIA.json').write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n');(out/'DIVERGENCIAS_OHLC_MT5.json').write_text(json.dumps(jdiff,indent=2)+'\n');print(json.dumps(res,ensure_ascii=False,indent=2))
