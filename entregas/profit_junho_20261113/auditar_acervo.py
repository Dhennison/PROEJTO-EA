"""Inventory June price sources; do not infer trades from OHLC."""
from pathlib import Path
import csv,json,datetime as dt,collections,hashlib
from decimal import Decimal as D
import openpyxl
OUT=Path(__file__).parent
WORK=Path('/workspace/candles_originais_modelo_d/WINFUT_F_0_1min_01-01-2026_22-09-2026.csv')
MT=Path('/workspace/exportacao_winn_110/EXPORT110_1794241201_5300/M1_202606.csv')
NATIVE=Path('/workspace/attachments/6340f23a-420a-4dcd-8f7d-09045a9bacd4/WINQ26_F_0_1min_17-06-2026_12-08-2026.csv')
XLS=Path('/workspace/attachments/538fea08-712a-4176-9493-e61afc15c395/JUN a AGO.xlsx')
REF=Path('/workspace/historico_modelo_d_20230301_20260921')
def read(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter=';'))
def collect(p,thousands=False):
 raw=p.read_bytes().decode('cp1252').splitlines();out={}
 for r in csv.reader(raw,delimiter=';'):
  if r[0]=='Ativo':continue
  stamp=dt.datetime.strptime(r[1]+' '+r[2],'%d/%m/%Y %H:%M:%S')
  if stamp.month!=6:continue
  num=lambda x:D(x.replace('.','').replace(',','.')) if thousands else D(x.replace(',','.'))
  out[stamp]=tuple(num(x) for x in r[3:7])
 return out
w=collect(WORK,True);n=collect(NATIVE);m={dt.datetime.strptime(r['time'],'%Y.%m.%d %H:%M'):tuple(D(r[k]) for k in ('open','high','low','close')) for r in read(MT)}
adj=collections.defaultdict(set)
for row in openpyxl.load_workbook(XLS,read_only=True,data_only=True).active.iter_rows(min_row=2,values_only=True):
 if isinstance(row[0],dt.datetime) and row[0].month==6 and row[5] is not None:adj[str(row[0].date())].add(D(str(row[5])))
a=[r for r in read(REF/'Ajustes_Diarios_Modelo_D_20230301_20260921.csv') if r['DataOperacional'].startswith('2026-06')]
wa={r['DataOperacional']:D(r['Ajuste'].replace(',','.')) for r in a}
ops=[r for r in read(REF/'Operacoes_Modelo_D_20230301_20260921_ORIGINAL.csv') if r['Data'].startswith('2026-06')]
def comparison(a,b):
 common=set(a)&set(b);diff=[t for t in sorted(common) if a[t]!=b[t]]
 return dict(common=len(common),exclusive_first=len(set(a)-set(b)),exclusive_second=len(set(b)-set(a)),ohlc_differences=len(diff),differences=[str(t) for t in diff],differences_before_cut=[str(t) for t in diff if t.time()<dt.time(18)])
summary=dict(Work_M1_bars=len(w),Work_M1_dates=sorted({str(t.date()) for t in w}),MT5_M1_bars=len(m),WINQ26_new_bars=len(n),WINQ26_new_dates=sorted({str(t.date()) for t in n}),Work_vs_MT5=comparison(w,m),Work_vs_WINQ26_new=comparison(w,n),XLS_adjustment_dates={d:list(map(str,sorted(v))) for d,v in sorted(adj.items())},XLS_adjustment_mismatches=[d for d,v in adj.items() if d in wa and v!={wa[d]}],Work_adjustment_dates=sorted(wa),Work_operations=len(ops),Work_points=str(sum((D(r['Pontos'].replace(',','.')) for r in ops),D(0))),sources_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (WORK,MT,NATIVE,XLS)})
(OUT/'INVENTARIO_JUNHO.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');print(json.dumps(summary,ensure_ascii=False,indent=2))
