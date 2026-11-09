"""Generate reviewed daily inputs and report-only Work results for the batch.
No native MT5 calls; no inferred adjustment or manufactured tick data.
"""
from pathlib import Path
import csv,io,json,hashlib
from datetime import datetime,timedelta
from decimal import Decimal as D,localcontext
root=Path(__file__).resolve().parent;repo=root.parents[1]
src=repo/'entregas/historico_work_modelo_d_20261105/replay_setembro_20261106/resultados'
context=src/'CONTEXTO_M1_E_CINCO_NIVEIS.csv';operations=src/'REFERENCIA_OPERACOES_SETEMBRO.csv'
candles=Path('/workspace/candles_originais_modelo_d/WINFUT_F_0_1min_01-01-2026_22-09-2026.csv')
refs=list(csv.DictReader(context.open(encoding='utf-8-sig'),delimiter=';'))
ops=list(csv.DictReader(operations.open(encoding='utf-8-sig'),delimiter=';'))
assert len(refs)==14 and len(ops)==33
levels=['S38.2','S50','S61.8','R38.2','R61.8'];by_date={r['Data']:r for r in refs}
assert list(by_date)==sorted(by_date) and len(by_date)==len(refs)
def num(s):return str(D(s.replace(',','.')))
def date(s):return s.replace('-','.')
def dt(s,time='00:00:00'):return "D'"+date(s)+' '+time+"'"
include=root/'MQL5/Include/ModeloD_PilotoWINN_Periodo';include.mkdir(parents=True,exist_ok=True)
code=['#ifndef PM_REFERENCE_110','#define PM_REFERENCE_110','#include "ModeloD_Core.mqh"',
 '#define PM_DAYS 14','#define PM_SLOTS 70',
 'const datetime PM_BEGIN='+dt(refs[0]['Data'])+';',
 'const datetime PM_END='+dt('2026-09-22')+';',
 'struct PMReference { datetime begin,first,cut,end,last_bar; string date,previous_date; MDInputs values; int expected_bars; };',
 'PMReference pm_ref[PM_DAYS];',
 'void PMInitReference()','{']
for i,r in enumerate(refs):
 assert r['LacunasInternas']=='0' and r['Corte']=='18:00:00'
 end=(datetime.fromisoformat(r['Data'])+timedelta(days=1)).strftime('%Y-%m-%d')
 code+=[' // Referencia Work '+r['Data']+'; nao e consulta de ajuste B3 live.',
 f' pm_ref[{i}].date="{r["Data"]}";pm_ref[{i}].previous_date="{r["PregaoAnterior"]}";',
 f' pm_ref[{i}].begin={dt(r["Data"])};pm_ref[{i}].end={dt(end)};',
 f' pm_ref[{i}].first={dt(r["Data"],r["PrimeiraBarra"])};pm_ref[{i}].cut={dt(r["Data"],r["Corte"])};pm_ref[{i}].last_bar={dt(r["Data"],r["UltimaBarra"])};',
 f' pm_ref[{i}].expected_bars={r["BarrasM1Hoje"]};',
 f' pm_ref[{i}].values.high_prev={num(r["MaximaAnterior"])};pm_ref[{i}].values.low_prev={num(r["MinimaAnterior"])};',
 f' pm_ref[{i}].values.close_prev={num(r["FechamentoAnterior"])};pm_ref[{i}].values.open_today={num(r["Abertura"])};pm_ref[{i}].values.adjustment={num(r["Ajuste"])};']
code+=['}', '#endif'];(include/'Periodo_Referencias.mqh').write_text('\n'.join(code)+'\n')
code=['#ifndef PM_WORK_REPORT_110','#define PM_WORK_REPORT_110',
 '// SOMENTE RELATORIO. Proibido usar resultado futuro para decidir ordens.',
 'struct PMWorkResult { bool exists,ambiguous; double points; string points_text,reason,entry_time,exit_time; };',
 'PMWorkResult pm_work[PM_SLOTS];','void PMInitWorkReport()','{',
 ' for(int s=0;s<PM_SLOTS;s++){pm_work[s].exists=false;pm_work[s].ambiguous=false;pm_work[s].points=0;pm_work[s].points_text="";pm_work[s].reason="SEM_OPERACAO";pm_work[s].entry_time="";pm_work[s].exit_time="";}']
seen=set()
for r in ops:
 i=list(by_date).index(r['Data']);j=levels.index(r['Nível']);s=i*5+j;assert s not in seen;seen.add(s)
 amb=r['Ambíguo'].strip()!='';assert not amb
 code+=[f' pm_work[{s}].exists=true;pm_work[{s}].ambiguous={str(amb).lower()};pm_work[{s}].points={num(r["Pontos"])};pm_work[{s}].points_text="{num(r["Pontos"])}";',
 f' pm_work[{s}].reason="{r["Motivo"]}";pm_work[{s}].entry_time="{r["Hora entrada"]}";pm_work[{s}].exit_time="{r["Hora saída"]}";']
code+=['}','#endif'];(include/'Periodo_WorkRelatorio.mqh').write_text('\n'.join(code)+'\n')
reference_dir=root/'referencias';reference_dir.mkdir(exist_ok=True)
(reference_dir/'CONTEXTO_WORK_SETEMBRO.csv').write_bytes(context.read_bytes());(reference_dir/'OPERACOES_WORK_SETEMBRO.csv').write_bytes(operations.read_bytes())
def pn(s):return D(s.replace('.','').replace(',','.'))
actual={}
for r in csv.reader(io.StringIO(candles.read_bytes().decode('cp1252')),delimiter=';'):
 if len(r)>=9 and r[0]=='WINFUT':
  key=datetime.strptime(r[1],'%d/%m/%Y').strftime('%Y-%m-%d')
  if key in by_date or key in {v['PregaoAnterior'] for v in refs}:
   actual.setdefault(key,[]).append((r[2][:5],[pn(x) for x in r[3:7]],pn(r[8])))
bar_count=0
with (reference_dir/'WORK_M1_SETEMBRO.csv').open('w',newline='') as f:
 w=csv.writer(f,delimiter=';',lineterminator='\n');w.writerow(['time','open','high','low','close','quantity'])
 for r in refs:
  day=sorted(actual[r['Data']]);prev=sorted(actual[r['PregaoAnterior']]);assert len(day)==int(r['BarrasM1Hoje']) and len(prev)==int(r['BarrasM1Anterior'])
  assert day[0][0]==r['PrimeiraBarra'][:5] and day[-1][0]==r['UltimaBarra'][:5] and day[0][1][0]==D(r['Abertura'])
  assert max(v[1][1] for v in prev)==D(r['MaximaAnterior']) and min(v[1][2] for v in prev)==D(r['MinimaAnterior']) and prev[-1][1][3]==D(r['FechamentoAnterior'])
  for time,prices,volume in day:w.writerow([date(r['Data'])+' '+time,*prices,volume]);bar_count+=1
summary={'days':len(refs),'from':'2026-09-01','through':'2026-09-21','Tester_end_exclusive':'2026-09-22','Work_operations':len(ops),'Work_points_exported':str(sum(D(num(r['Pontos'])) for r in ops)),'Work_zero_operation_days':[r['Data'] for r in refs if not any(x['Data']==r['Data'] for x in ops)],'Work_ambiguous_operations':sum(bool(r['Ambíguo'].strip()) for r in ops),'Work_cutoff_exits':sum(r['Motivo'] not in ('STOP','ALVO') for r in ops),'expected_M1_bars':bar_count,'reference_only_adjustments':'Historical Work inputs; not certified native B3/live adjustment feed','source_SHA256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [context,operations,candles]}}
(reference_dir/'PROVENIENCIA.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');print(json.dumps(summary,ensure_ascii=False,indent=2))
