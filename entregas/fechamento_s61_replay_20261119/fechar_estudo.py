from pathlib import Path
import csv,json,pickle,collections,ast,math,hashlib,itertools
import numpy as np
from openpyxl import Workbook
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4,landscape
P=Path(__file__).parent;R=P.parents[1];E=R/'entregas'
x=pickle.load(open('/workspace/work/estudo_s61/resultados.pickle','rb'));audit=pickle.load(open('/workspace/work/replay_s61_20261119/auditoria.pickle','rb'));data=x['data'];days=data['days'];di={d:i for i,d in enumerate(days)}
assert len(audit['audit'])==29
for key,es in audit['accepted'].items():data['replay'][key]=es
bars={d:[(int(b[0][:2])*60+int(b[0][3:]),*b[1:5]) for b in data['bars'][d]] for d in days}
ns=dict(data=data,math=math,collections=collections,bars=bars,replay=data['replay'],known_noquote={'2024-02-06','2024-06-07','2025-06-03','2025-07-30','2025-08-21'})
src=(E/'estudo_saidas_niveis_20261117/testar_cenarios.py').read_text()
for f in ast.parse(src).body:
 if isinstance(f,ast.FunctionDef) and f.name in ['tick_choices','evaluate']:exec(compile(ast.get_source_segment(src,f),'preserved_engine','exec'),ns)
base_tick=ns['tick_choices']
def checked_tick(es,e,tp,sl,sign,entering):
 a=base_tick(es,e,tp,sl,sign,entering)
 rev=[ev for _,g in itertools.groupby(es,key=lambda ev:ev[0]) for ev in reversed(list(g))]
 b=base_tick(rev,e,tp,sl,sign,entering)
 if a is None or b is None or a!=b:return None
 # A group containing both entry and target leaves intramillisecond entry order unresolved.
 if entering:
  active=False
  for _,g in itertools.groupby(es,key=lambda ev:ev[0]):
   pp=[sign*ev[1] for ev in g]
   if not active:
    if min(pp)<=e and max(pp)>=tp:return None
    if min(pp)<=e:active=True
 return a
ns['tick_choices']=checked_tick
ids=['S61_42','S61_48','S61_60'];ops={o['date']:o for o in x['ops']};trades=[];changes=[];baseline=[];pending=[]
for d in sorted({r['date'] for r in audit['audit']}):
 o=ops[d];a,b,_=ns['evaluate'](o,abs(o['tp']-o['entry']),650)
 baseline.append(dict(date=d,original=o['original'],lower=a,upper=b,compatible=a<=o['original']<=b));assert a<=o['original']<=b,(d,a,b,o)
for old in x['trade']:
 if old['variant'] not in ids:continue
 r=old.copy();d=r['date'];o=ops[d]
 if old['lower']!=old['upper']:
  a,b,pp=ns['evaluate'](o,r['target_points'],r['stop_points'])
  assert old['lower']<=a<=b<=old['upper'],(r,a,b)
  r.update(lower=a,upper=b,unresolved=a!=b,source='M1_PLUS_REPLAY_DATAS_XLSX_VALIDATED' if a==b else 'REPLAY_RECEIVED_STILL_UNRESOLVED')
  changes.append(dict(variant=r['variant'],date=d,contract=r['contract'],entry=r['entry'],target_points=r['target_points'],stop_points=r['stop_points'],previous_lower=old['lower'],previous_upper=old['upper'],new_lower=a,new_upper=b,resolved=a==b,result='TP' if a==b==r['target_points'] else 'SL' if a==b==-r['stop_points'] else 'CORTE' if a==b else 'PENDING'))
  if a!=b:
   for tm,why in pp:pending.append(dict(variant=r['variant'],date=d,contract=r['contract'],minute=tm,reason=why,lower=a,upper=b))
 trades.append(r)
def write(name,rs):
 if not rs:return
 with (P/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rs[0]),delimiter=';');w.writeheader();w.writerows(rs)
def dd(a):
 cum=np.cumsum(a);return float(np.max(np.maximum.accumulate(np.r_[0,cum])[1:]-cum))
def read(p):return list(csv.DictReader(p.open(encoding='utf-8-sig'),delimiter=';'))
annual=[];monthly=[];daily=[];summary=[];curves={}
for id in ids:
 rr=[r for r in trades if r['variant']==id];assert len(rr)==233
 lo=np.zeros(len(days));hi=lo.copy()
 for r in rr:lo[di[r['date']]]=r['lower'];hi[di[r['date']]]=r['upper']
 curves[id]=(lo,hi);row=dict(id=id,total_lower=float(lo.sum()),total_upper=float(hi.sum()),DD_lower=dd(hi),DD_upper=dd(lo),pending=sum(r['lower']!=r['upper'] for r in rr),operations=len(rr))
 row['points_per_DD']=row['total_lower']/row['DD_upper']
 for y in [2024,2025,2026]:
  mask=np.array([d.startswith(str(y)) for d in days]);a=float(lo[mask].sum());b=float(hi[mask].sum());row[f'year{y}_lower']=a;row[f'year{y}_upper']=b
  annual.append(dict(id=id,year=y,scope='Jan-Out' if y==2026 else 'Ano completo',operations=sum(r['date'].startswith(str(y)) for r in rr),lower=a,upper=b,DD_year_lower=dd(hi[mask]),DD_year_upper=dd(lo[mask])))
 for m in sorted({d[:7] for d in days}):
  mask=np.array([d.startswith(m) for d in days]);monthly.append(dict(id=id,month=m,operations=sum(r['date'].startswith(m) for r in rr),lower=float(lo[mask].sum()),upper=float(hi[mask].sum()),DD_month_lower=dd(hi[mask]),DD_month_upper=dd(lo[mask])))
 cumlo=np.cumsum(lo);cumhi=np.cumsum(hi);peaklo=np.maximum.accumulate(np.r_[0,cumlo])[1:];peakhi=np.maximum.accumulate(np.r_[0,cumhi])[1:]
 for i,d in enumerate(days):daily.append(dict(id=id,date=d,lower=lo[i],upper=hi[i],cumulative_lower=cumlo[i],cumulative_upper=cumhi[i],drawdown_lower=peakhi[i]-cumhi[i],drawdown_upper=peaklo[i]-cumlo[i]))
 summary.append(row)
summary.sort(key=lambda r:r['points_per_DD'],reverse=True)
for i,r in enumerate(summary,1):r['rank']=i
oldrank=read(E/'comparacao_proporcionais_s61_20261118/CONFRONTO_5_OPCOES.csv');confront=[r.copy() for r in summary]
for r in oldrank:
 if not r['id'].startswith('ANTERIOR'):continue
 rr={k:(float(r[k]) if k not in ['id'] else r[k]) for k in ['id','total_lower','total_upper','DD_lower','DD_upper','pending','operations','year2024_lower','year2024_upper','year2025_lower','year2025_upper','year2026_lower','year2026_upper']}
 rr['points_per_DD']=rr['total_lower']/rr['DD_upper'];confront.append(rr)
confront.sort(key=lambda r:r['points_per_DD'],reverse=True)
for i,r in enumerate(confront,1):r['rank']=i
write('RESULTADO_TRES_OPCOES.csv',summary);write('RESULTADO_ANUAL.csv',annual);write('RESULTADO_MENSAL.csv',monthly);write('CURVAS_DIARIAS.csv',daily);write('OPERACOES.csv',trades);write('RESOLUCAO_PENDENCIAS.csv',changes);write('CONFERENCIA_ORIGINAL.csv',baseline);write('PENDENCIAS_REMANESCENTES.csv',pending);write('RANKING_ATUALIZADO_5.csv',confront)
w=Workbook();w.remove(w.active)
for name,rows in [('Resumo',summary),('Anual',annual),('Mensal',monthly),('Diario',daily),('Operacoes',trades),('Resolvidas',changes),('Janelas',audit['audit']),('Ranking5',confront)]:
 s=w.create_sheet(name);keys=list(rows[0]);s.append(keys)
 for r in rows:s.append([r.get(k) for k in keys])
 s.freeze_panes='A2';s.auto_filter.ref=s.dimensions
 for col in s.columns:s.column_dimensions[col[0].column_letter].width=min(40,max(13,max(len(str(v.value or '')) for v in list(col)[:30])+2))
w.save(P/'S61_Resultados_Replay_20261119.xlsx')
def fmt(v):return f'{v:,.0f}'.replace(',','.')
def interval(a,b):return fmt(a) if a==b else fmt(a)+' a '+fmt(b)
c=canvas.Canvas(str(P/'S61_Resultados_Replay_20261119.pdf'),pagesize=landscape(A4));W,H=landscape(A4)
c.setFont('Helvetica-Bold',16);c.drawString(30,H-35,'S61 - Fechamento das janelas recebidas em Datas.xlsx')
c.setFont('Helvetica',10);y=H-65
for t in ['Periodo: janeiro/2024 a outubro/2026. Pontos brutos; sem custos ou slippage.','S61_42: stop 100; S61_48/68: stop 0,5x alvo; S61_60: stop 1,5x alvo, sem teto.','Alvo das tres opcoes: distancia original ate S50. Mesmas 233 entradas originais.','DD principal: fechamentos diarios em ordem cronologica, incluindo zero inicial, sem reiniciar por mes.','Fontes: M1 MT5/Profit/Cedro auditado + Replay pontual; nao e auditoria integral tick a tick.','50/250 em stand-by por decisao do usuario. Resultados originais preservados.']:
 c.drawString(30,y,t);y-=17
y-=15;c.setFont('Helvetica-Bold',10)
for xx,t in zip([30,115,230,345,460,580,695],['Opcao','2024','2025','2026 Jan-Out','Total','DD continuo','Pendentes']):c.drawString(xx,y,t)
y-=22;c.setFont('Helvetica',10)
for r in summary:
 values=[r['id'],interval(r['year2024_lower'],r['year2024_upper']),interval(r['year2025_lower'],r['year2025_upper']),interval(r['year2026_lower'],r['year2026_upper']),interval(r['total_lower'],r['total_upper']),interval(r['DD_lower'],r['DD_upper']),str(r['pending'])]
 for xx,t in zip([30,115,230,345,460,580,695],values):c.drawString(xx,y,t)
 y-=25
y-=20;c.drawString(30,y,f"Janelas aceitas: {len(audit['accepted'])}/29. Pendencias resolvidas: {sum(r['resolved'] for r in changes)}/{len(changes)}.")
c.showPage();c.save()
raw=Path('/workspace/dados_brutos_modelo_d/replay_profit/Datas.xlsx');manifest=dict(file='Datas.xlsx',path=str(raw),bytes=raw.stat().st_size,sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),url='https://github.com/Dhennison/PROEJTO-EA/releases/download/dados-replay-2025-20261116/Datas.xlsx',asset_id=768928838,expected_windows=29,accepted_windows=len(audit['accepted']),pending_operations_before=len(changes),pending_operations_after=sum(r['lower']!=r['upper'] for r in trades),original_compatible_days=len(baseline),original_not_modified=True,standby='50/250',contract_check='Contrato esperado das referencias; planilha nao possui campo ativo. Correspondencia OHLC e quantidade confirmada nos minutos aceitos.',tied_ms='Reversao de grupos no mesmo milissegundo e rejeicao de grupos com barreiras opostas ou entrada/alvo ambiguos.',summary=summary)
(P/'MANIFESTO.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(manifest,ensure_ascii=False,indent=2))
