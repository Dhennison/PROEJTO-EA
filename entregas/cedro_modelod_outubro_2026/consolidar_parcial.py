"""Une dias completos sem apresentar a parcial como fechamento de outubro."""
from pathlib import Path
from decimal import Decimal as D
from collections import Counter
import csv,json
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OUT=HERE/'parcial_atual';OUT.mkdir(exist_ok=True)
def read(p):return list(csv.DictReader(p.open(encoding='utf-8-sig'),delimiter=';'))
def write(p,rows):
 with p.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter=';',lineterminator='\n');w.writeheader();w.writerows(rows)
daily=[];ops=[]
for folder in ['resultado_lote1','resultado_dia14']:
 daily+=read(HERE/folder/'DIARIO_PARCIAL.csv')
 opfile=HERE/folder/'POR_OPERACAO.csv'
 if opfile.exists():ops+=read(opfile)
 else:
  meta=json.loads((HERE/folder/'PARCIAL.json').read_text());assert meta['operacoes']==0
  assert all(not r['hora_entrada'] for r in read(HERE/folder/'TODOS_NIVEIS.csv'))
daily.sort(key=lambda r:r['data']);assert len(daily)==len({r['data'] for r in daily})==9
assert len({(r['data'],r['nivel']) for r in ops})==len(ops)==13
points=sum((D(r['pontos']) for r in daily),D(0));assert points==1600
write(OUT/'DIARIO_PARCIAL.csv',daily);write(OUT/'POR_OPERACAO.csv',ops)
seed=read(ROOT/'entregas/compilado_cedro_modelod/CURVA_MODELO_D_MESES_COMPLETOS.csv')[-1]
balance=D(seed['saldo']);peak=D(seed['pico']);maximum=D(seed['DD_max_acumulado']);curve=[];local=localpeak=localdd=D(0)
for r in daily:
 p=D(r['pontos']);balance+=p;peak=max(peak,balance);dd=peak-balance;maximum=max(maximum,dd)
 local+=p;localpeak=max(localpeak,local);localdd=max(localdd,localpeak-local)
 curve.append({'data':r['data'],'pontos':r['pontos'],'saldo_desde03agosto':str(balance),'pico_desde03agosto':str(peak),'DD_atual':str(dd),'DD_max_acumulado':str(maximum),'status':'OUTUBRO_PARCIAL'})
write(OUT/'CURVA_PARCIAL_DRAWDOWN.csv',curve)
s={'mes':'2026-10','status':'PARCIAL_NAO_E_FECHAMENTO_MENSAL','data_inicio':daily[0]['data'],'data_fim':daily[-1]['data'],'pregoes_calculados':9,'subtotal_pontos':str(points),'operacoes':len(ops),'motivos':dict(Counter(r['motivo'] for r in ops)),'dia14':'COMPLETO_SEM_OPERACOES','estados_conferidos':45,'registros_WIN_auditados':69807252,'ZIPs_auditados':22,'faltam_pregoes':12,'faltam_ZIPs':26,'DD_continuo_desde03agosto':str(maximum),'DD_local_parcial':str(localdd),'saldo_periodo_completo_AgoSet_e_Out_parcial':str(balance),'Work':'SEM_REFERENCIA_NESTE_MES','criterio':'Modelo D original,1contrato/nível,grade5,toque,pontos condicionais,sem custos','referencias_rolagem':'14/10abertura/negociosZ,contextoHLC/ajusteV13,convencaohistoricaWork12/08preservada'}
(OUT/'RESULTADO_PARCIAL.json').write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n');print(json.dumps(s,ensure_ascii=False,indent=2))
