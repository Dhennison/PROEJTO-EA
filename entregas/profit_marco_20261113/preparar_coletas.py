"""Inventory March and prepare only unresolved Replay minutes."""
from pathlib import Path
from decimal import Decimal as D
import csv,json,datetime as dt,hashlib,zipfile
P=Path(__file__).parent
SOURCE=Path('/workspace/candles_originais_modelo_d/WINFUT_F_0_1min_01-01-2026_22-09-2026.csv')
MT=Path('/workspace/exportacao_winn_110/EXPORT110_1794241201_5300/M1_202603.csv')
def read(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter=';'))
def write(p,rs):
 with p.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rs[0]),delimiter=';',lineterminator='\n');w.writeheader();w.writerows(rs)
w={}
for r in csv.reader(SOURCE.read_bytes().decode('cp1252').splitlines(),delimiter=';'):
 if r[0]=='Ativo':continue
 t=dt.datetime.strptime(r[1]+' '+r[2],'%d/%m/%Y %H:%M:%S')
 if t.month==3:w[t]=tuple(D(x.replace('.','').replace(',','.')) for x in r[3:7])
m={dt.datetime.strptime(r['time'],'%Y.%m.%d %H:%M'):tuple(D(r[k]) for k in ('open','high','low','close')) for r in read(MT)}
common=set(w)&set(m);diff=[str(t) for t in sorted(common) if w[t]!=m[t]]
inv=dict(Work_M1_bars=len(w),MT5_M1_bars=len(m),dates=sorted({str(t.date()) for t in w}),common_timestamps=len(common),exclusive_Work=len(set(w)-set(m)),exclusive_MT5=len(set(m)-set(w)),OHLC_differences=len(diff),OHLC_difference_timestamps=diff,exclusive_MT5_timestamps=[str(t) for t in sorted(set(m)-set(w))],source_hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (SOURCE,MT)})
(P/'INVENTARIO_MARCO.json').write_text(json.dumps(inv,ensure_ascii=False,indent=2)+'\n')
ops=read(P/'OPERACOES_POSSIBILIDADES.csv');asks=read(P/'JANELAS_REPLAY.csv');refs=read(P/'REFERENCIAS_MARCO.csv');pending={(o['date'],o['level']) for o in ops if o['determined']=='False'}
contract=lambda d:'WINJ26'
rows=[]
for a in asks:
 if (a['date'],a['level']) not in pending:continue
 h,mi=map(int,a['minute'].split(':'));start=a['minute']+':00';end=f'{h+(mi+1)//60:02d}:{(mi+1)%60:02d}:00'
 same=next((r for r in rows if r['data']==a['date'] and r['inicio']==start),None)
 if same:same['niveis']+=','+a['level']
 else:rows.append(dict(data=a['date'],contrato=contract(a['date']),inicio=start,fim_exclusivo=end,niveis=a['level'],motivo='Ordem entrada/alvo/stop ambigua no M1'))
rows.sort(key=lambda r:(r['data'],r['inicio']))
extra=[o for o in ops if o['determined']=='True' and o['work_reason']!=('ALVO' if o['outcomes'].startswith('TP:') else 'STOP' if o['outcomes'].startswith('SL:') else 'ZERAGEM 18H')]
assert len(extra)==1 and extra[0]['date']=='2026-03-19' and extra[0]['level']=='S61.8',extra
for o in extra:
 minute=o['exit_candidates'].split('|')[0].split('@',1)[1][11:16];h,mi=map(int,minute.split(':'));rows.append(dict(data=o['date'],contrato=contract(o['date']),inicio=minute+':00',fim_exclusivo=f'{h+(mi+1)//60:02d}:{(mi+1)%60:02d}:00',niveis=o['level'],motivo='Controle do toque no stop normalizado grade5:desfecho difere Work'))
rows.sort(key=lambda r:(r['data'],r['inicio']))
for r in refs:r['contrato_Replay']=contract(r['date'])
write(P/'REFERENCIAS_MARCO.csv',refs);write(P/'COLETAS_REPLAY_PRIORITARIAS.csv',rows)
s=json.loads((P/'RESULTADO_PROVISORIO.json').read_text());s.update(contracts={'marco':'WINJ26'},window_count=len(rows),window_dates=sorted({r['data'] for r in rows}),grade_controls=[{'date':o['date'],'level':o['level'],'normalized_outcome':o['outcomes'],'Work_reason':o['work_reason'],'Work_points':o['work_points']} for o in extra],resultado_principal='AGUARDANDO_REPLAY',previous_context_first_day=refs[0]['previous'],source_context='M1 Profit e ajustes Work preservados;HLC de todo pregao anterior;sem gerar ticks.',coletas_apenas_ambiguidades=True)
(P/'RESULTADO_PROVISORIO.json').write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
assert len(rows)==5 and len(pending)==4 and len(ops)==50 and not s['work_missing'] and not s['work_extra']
assert len(w)==len(common) and all(dt.datetime.fromisoformat(t).time()>=dt.time(18) for t in diff+inv['exclusive_MT5_timestamps'])
for day in inv['dates']:
 aa=sorted((t,v) for t,v in w.items() if str(t.date())==day);bb=sorted((t,v) for t,v in m.items() if str(t.date())==day)
 assert (aa[0][1][0],max(v[1] for t,v in aa),min(v[2] for t,v in aa),aa[-1][1][3])==(bb[0][1][0],max(v[1] for t,v in bb),min(v[2] for t,v in bb),bb[-1][1][3]),day
inv['daily_OHLC_matches_all_22_days']=True;inv['all_differences_after_cut']=True
(P/'INVENTARIO_MARCO.json').write_text(json.dumps(inv,ensure_ascii=False,indent=2)+'\n')
text=f'''MARCO/2026 — MODELO D — ANALISE M1 AGUARDANDO REPLAY
Work:+3451,037332 pontos,50operacoes,22pregoes. Nosso principal:pendente.
46operacoes determinadas nos candles;4pendentes em17mar/19mar.
Controle adicional19marS61.8:stopgrade177480 tocado09:31,mas stop matematico
177477,898 nao e atingido. WorkALVO574,935333 posterior10:17. Conferir toque
na grade5,nao alterar criterio conforme ganho. Total5minutos,sempreWINJ26.

ACERVO
{len(w)}M1ProfitWork eMT5WIN$N,horarios/OHLC conferidos em inventario.
10mar18:24diferente eMT5extra18:25:depoiscorte18h,OHLCdiariofinaligual
em todas22datas,semimpacto nasreferencias. Nao pedir nova coleta.
Ajustes22datas Work disponiveis. Niveis matematicos50entrada/SL/TP iguais
Work,tolerancia0,00001. Sem chaves faltantes/extra,sem lacunas intradiarias.
Contexto02mar usa27fevereiro M5 COMPLETO do Work(09h em diante),nao210M1
parciais sobrepostos que comecam14:55. HLC todo pregao anterior,sem truncar
18h;abertura atual;ajuste operacional congelado. Nao gerar ticks deM5/M1.
M5 so para contexto HLC,nao simular negocios ou definir trajetoria de marco.

COLETAS
17mar10:21–10:22 R61.8.
19mar09:03–09:04 S38.2.
19mar09:31–09:32 S61.8(controlestopgrade).
19mar16:01–16:02 R38.2 e16:02–16:03 R61.8,podem vir juntos16:01–16:03.
TodasWINJ26. XLSX porjanelas:17mar;19mar0903;19mar0931;19mar1601.
Comecar algunssegundos antes/terminardepois,reproduzir sem saltar dentro
janela,sem filtrar lotes/corretoras/tipos. Preservar negociosidenticos.
Verificar limite200001,alcance/OHLC/quantidade e desempatesms antes de decidir.
Nao pedir novos ajustes ou candles,acervo suficiente para esta classificacao.

CRITERIO
Mesmo protocoloD grade5,1contrato/nivel,parametrosoriginais,toqueinclusivo,
corte18h,sem custos/fila/fills. Um mero toque nao determina ordementrada/
alvo/stop;so descartar Replay se todosramos compativeis dao mesmoresultado.
Ramos TP/SL/ABERTA propagados ate corte. Envoltorioexterno-180a2220 e dado
tecnico,nao fechamento nem faixa de resultado realizavel garantida.
Nao somar subtotal de determinadas nem incorporar marco aoDD ate resolver.
Abril5720/Maio-780/Junho3405/Julho1100 eCedro fechados preservados.
Cada ampliacao recalculaDDcronologico porserie,sem mudar pontos fechados.
'''
(P/'LEIA_MARCO.txt').write_text(text)
with zipfile.ZipFile(P/'Marco_Modelo_D_Analise_e_Coletas.zip','w',zipfile.ZIP_DEFLATED) as z:
 for n in ['LEIA_MARCO.txt','COLETAS_REPLAY_PRIORITARIAS.csv','REFERENCIAS_MARCO.csv','DIARIO_PROVISORIO.csv','OPERACOES_POSSIBILIDADES.csv','INVENTARIO_MARCO.json','RESULTADO_PROVISORIO.json']:z.write(P/n,n)
print(json.dumps({'inventory':inv,'coletas':rows},ensure_ascii=False,indent=2))
