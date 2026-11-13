"""Inventory April and prepare only unresolved Replay minutes."""
from pathlib import Path
from decimal import Decimal as D
import csv,json,datetime as dt,hashlib,zipfile
P=Path(__file__).parent
SOURCE=Path('/workspace/candles_originais_modelo_d/WINFUT_F_0_1min_01-01-2026_22-09-2026.csv')
MT=Path('/workspace/exportacao_winn_110/EXPORT110_1794241201_5300/M1_202604.csv')
def read(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter=';'))
def write(p,rs):
 with p.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rs[0]),delimiter=';',lineterminator='\n');w.writeheader();w.writerows(rs)
w={}
for r in csv.reader(SOURCE.read_bytes().decode('cp1252').splitlines(),delimiter=';'):
 if r[0]=='Ativo':continue
 t=dt.datetime.strptime(r[1]+' '+r[2],'%d/%m/%Y %H:%M:%S')
 if t.month==4:w[t]=tuple(D(x.replace('.','').replace(',','.')) for x in r[3:7])
m={dt.datetime.strptime(r['time'],'%Y.%m.%d %H:%M'):tuple(D(r[k]) for k in ('open','high','low','close')) for r in read(MT)}
common=set(w)&set(m);diff=[str(t) for t in sorted(common) if w[t]!=m[t]]
inv=dict(Work_M1_bars=len(w),MT5_M1_bars=len(m),dates=sorted({str(t.date()) for t in w}),common_timestamps=len(common),exclusive_Work=len(set(w)-set(m)),exclusive_MT5=len(set(m)-set(w)),OHLC_differences=len(diff),OHLC_difference_timestamps=diff,source_hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (SOURCE,MT)})
(P/'INVENTARIO_ABRIL.json').write_text(json.dumps(inv,ensure_ascii=False,indent=2)+'\n')
ops=read(P/'OPERACOES_POSSIBILIDADES.csv');asks=read(P/'JANELAS_REPLAY.csv');refs=read(P/'REFERENCIAS_ABRIL.csv');pending={(o['date'],o['level']) for o in ops if o['determined']=='False'}
contract=lambda d:'WINJ26' if d<'2026-04-15' else 'WINM26'
rows=[]
for a in asks:
 if (a['date'],a['level']) not in pending:continue
 h,mi=map(int,a['minute'].split(':'));start=a['minute']+':00';end=f'{h+(mi+1)//60:02d}:{(mi+1)%60:02d}:00'
 same=next((r for r in rows if r['data']==a['date'] and r['inicio']==start),None)
 if same:same['niveis']+=','+a['level']
 else:rows.append(dict(data=a['date'],contrato=contract(a['date']),inicio=start,fim_exclusivo=end,niveis=a['level'],motivo='Ordem entrada/alvo/stop ambigua no M1'))
rows.sort(key=lambda r:(r['data'],r['inicio']))
extra=[o for o in ops if o['determined']=='True' and o['work_reason']!=('ALVO' if o['outcomes'].startswith('TP:') else 'STOP' if o['outcomes'].startswith('SL:') else 'ZERAGEM 18H')]
assert not extra,extra
for r in refs:r['contrato_Replay']=contract(r['date'])
write(P/'REFERENCIAS_ABRIL.csv',refs);write(P/'COLETAS_REPLAY_PRIORITARIAS.csv',rows)
s=json.loads((P/'RESULTADO_PROVISORIO.json').read_text());s.update(contracts={'09abr':'WINJ26','17abr':'WINM26'},window_count=len(rows),window_dates=sorted({r['data'] for r in rows}),grade_controls=[],resultado_principal='AGUARDANDO_REPLAY',previous_context_first_day=refs[0]['previous'],source_context='M1 Profit e ajustes Work preservados;HLC de todo pregao anterior;sem gerar ticks.',coletas_apenas_ambiguidades=True)
(P/'RESULTADO_PROVISORIO.json').write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
assert len(rows)==3 and len(pending)==3 and len(ops)==36 and not s['work_missing'] and not s['work_extra']
assert len(w)==len(m)==len(common) and not diff
text=f'''ABRIL/2026 — MODELO D — ANALISE M1 AGUARDANDO REPLAY
Work:+6877,556998 pontos,36operacoes,20pregoes. Nosso principal:pendente.
33operacoes determinadas emM1;3pendentes em09abr e17abr.
09abr10:32–10:33WINJ26R61.8.
17abr09:47–09:48WINM26R61.8;17abr11:51–11:52WINM26S38.2.
Tres minutos,sem controles extras de grade nesta rodada.

ACERVO
{len(w)}M1Profit Work eMT5WIN$N,mesmoshorarios/OHLC,zero diferencas.
Ajustes20datas Work presentes. Contexto primeirodia01abr vem31marco
ja no acervo;HLC de todo pregao anterior,abertura atual eajusteoperacional.
36niveis matematicos entrada/SL/TP iguais Work,tolerancia0,00001.
Sem lacunas intradiarias fornecidas;nao certifica todosnegocios demercado.

METODO E COLETA
Mesmo criterio M1+Replay demaio/junho/julho,grade5,1contrato/nivel,
parametrosoriginais,corte18h. Nao escolher ordem de toques pelo resultado.
Ramos TP/SL/ABERTA,propagados ate corte. Pontos nos niveis,sem custos/fila/fills.
Nao apresentar subtotal dasdeterminadas nem envoltorio5720–7455 como
fechamento:extremos por operacao podem nao coexistir na fita diaria.
XLSX com3abas(09abr;17abr0947;17abr1151). Comecar algunssegundosantes,
terminardepois,sem saltar dentrojanela,sem filtro de lotes/corretoras/tipos.
Preservar negociosidenticos,verificarhorarios/limite200001/OHLC/quantidade.
Nenhum pedido adicional deOHLC/ajuste. Resultados fechados preservados.

CONTINUIDADE DEFINIDA PELO USUARIO
Expandir D original ate limite deReplayProfit,sem compra dehistorico.
Depois estudar alvo/stop por nivel e depois testar A/B/C nos mesmos meses.
Nao e otimo universal nem validacao independente escolher parametros na
mesma amostra. Preservar D original e identificar variantes/fontes/curvas.
Cedro ago-out:negocios brutos recebidos de todo periodo. Maio-julho:M1mais
janelas pontuais de negocios. Novos stops/alvos/modelos podem exigirnovas
janelas fora dascoletas ja feitas. Candles nao recuperam ordem de negocios.
Guardarbrutos,nao apenas reducao feita para os niveis D atuais. A validacao
nao se transfere automaticamente para novos parametros ou modelos.
'''
(P/'LEIA_ABRIL.txt').write_text(text)
with zipfile.ZipFile(P/'Abril_Modelo_D_Analise_e_Coletas.zip','w',zipfile.ZIP_DEFLATED) as z:
 for n in ['LEIA_ABRIL.txt','COLETAS_REPLAY_PRIORITARIAS.csv','REFERENCIAS_ABRIL.csv','DIARIO_PROVISORIO.csv','OPERACOES_POSSIBILIDADES.csv','INVENTARIO_ABRIL.json','RESULTADO_PROVISORIO.json']:z.write(P/n,n)
print(json.dumps({'inventory':inv,'coletas':rows},ensure_ascii=False,indent=2))
