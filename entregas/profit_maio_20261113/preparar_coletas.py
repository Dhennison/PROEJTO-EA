"""Verify May coverage and request only unresolved local chronology."""
from pathlib import Path
from decimal import Decimal as D
import csv,json,datetime as dt,hashlib,zipfile
P=Path(__file__).parent
SOURCE=Path('/workspace/candles_originais_modelo_d/WINFUT_F_0_1min_01-01-2026_22-09-2026.csv')
MT=Path('/workspace/exportacao_winn_110/EXPORT110_1794241201_5300/M1_202605.csv')
def read(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter=';'))
def write(p,rs):
 with p.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rs[0]),delimiter=';',lineterminator='\n');w.writeheader();w.writerows(rs)
w={}
for r in csv.reader(SOURCE.read_bytes().decode('cp1252').splitlines(),delimiter=';'):
 if r[0]=='Ativo':continue
 t=dt.datetime.strptime(r[1]+' '+r[2],'%d/%m/%Y %H:%M:%S')
 if t.month==5:w[t]=tuple(D(x.replace('.','').replace(',','.')) for x in r[3:7])
m={dt.datetime.strptime(r['time'],'%Y.%m.%d %H:%M'):tuple(D(r[k]) for k in ('open','high','low','close')) for r in read(MT)}
common=set(w)&set(m);diff=[str(t) for t in sorted(common) if w[t]!=m[t]]
inv=dict(Work_M1_bars=len(w),MT5_M1_bars=len(m),dates=sorted({str(t.date()) for t in w}),common_timestamps=len(common),exclusive_Work=len(set(w)-set(m)),exclusive_MT5=len(set(m)-set(w)),OHLC_differences=len(diff),OHLC_difference_timestamps=diff,source_hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (SOURCE,MT)})
(P/'INVENTARIO_MAIO.json').write_text(json.dumps(inv,ensure_ascii=False,indent=2)+'\n')
ops=read(P/'OPERACOES_POSSIBILIDADES.csv');asks=read(P/'JANELAS_REPLAY.csv');refs=read(P/'REFERENCIAS_MAIO.csv');pending={(o['date'],o['level']) for o in ops if o['determined']=='False'}
rows=[]
for a in asks:
 if (a['date'],a['level']) not in pending:continue
 h,mi=map(int,a['minute'].split(':'));start=a['minute']+':00';end=f'{h+(mi+1)//60:02d}:{(mi+1)%60:02d}:00'
 same=next((r for r in rows if r['data']==a['date'] and r['inicio']==start),None)
 if same:same['niveis']+=','+a['level']
 else:rows.append(dict(data=a['date'],contrato='WINM26',inicio=start,fim_exclusivo=end,niveis=a['level'],motivo='Ordem entrada/alvo/stop ambigua no M1'))
extra=[o for o in ops if o['determined']=='True' and o['work_reason']!=('ALVO' if o['outcomes'].startswith('TP:') else 'STOP' if o['outcomes'].startswith('SL:') else 'ZERAGEM 18H')]
assert not extra,extra
for r in refs:r['contrato_Replay']='WINM26'
write(P/'REFERENCIAS_MAIO.csv',refs);write(P/'COLETAS_REPLAY_PRIORITARIAS.csv',rows)
s=json.loads((P/'RESULTADO_PROVISORIO.json').read_text());s.update(contract='WINM26',window_count=len(rows),window_dates=sorted({r['data'] for r in rows}),grade_controls=[],resultado_principal='AGUARDANDO_REPLAY',previous_context_first_day=refs[0]['previous'],source_context='M1 Profit e ajustes Work preservados;HLC de todo pregao anterior;sem gerar ticks.',coletas_apenas_ambiguidades=True)
(P/'RESULTADO_PROVISORIO.json').write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
assert len(rows)==4 and len(pending)==5 and len(ops)==45 and not s['work_missing'] and not s['work_extra']
assert len(w)==len(m)==len(common) and not diff
text=f'''MAIO/2026 — MODELO D — ANALISE M1 AGUARDANDO REPLAY
Work:+2032,313668 pontos,45operacoes,20pregoes. Nosso principal:pendente.
40operacoes determinadas pelos candles;5pendentes em15/19/26/27maio.
Quatro minutos de coleta,WINM26 em todos. Dia19resolveS38.2 eS50 juntos.
Nao solicitar outrosdias ou controles extras sem evidencia nova.

ACERVO E REFERENCIAS
{len(w)}barrasM1Profit Work eMT5WIN$N,mesmoshorarios eOHLC;zero diferencas.
Ajustes20datas presentes no Work. Contexto primeirodia04maio usa30abril
ja existente;HLC do pregao anterior completo,aberturaatual eajusteoperacional.
Todos45conjuntos matematicos entrada/SL/TP iguais Work,tolerancia0,00001.
Mesmo criterio grade5,1contrato/nivel,toqueinclusivo,corte18h,parametrosoriginais.
Sem lacunas intradiarias nos candles fornecidos;nao certifica negocios reais.
Nenhum desfecho determinado difere Work nesta rodada;sem controlegradeextra.

COLETA
15maio09:02–09:03S61.8;19maio09:03–09:04S38.2/S50;
26maio10:05–10:06S38.2;27maio09:22–09:23R61.8.
TodasWINM26. Iniciar algunssegundos antes e terminar depois do minuto
completo,reproduzir sem saltar dentrojanela,copiarsem filtro/corretora/lote.
Preservar negocios identicos. Copiaranteslimite observado200001;verificar
horario inicial/final,OHLC/quantidade e desempatesms na analise. XLSX com
abas pordia como mesesanteriores;nao pedir pregõesinteiros ou novoOHLC.

METODO
Ramos TP/SL/ABERTA propagados pelos M1,sem inventar trajeto. Mesmo
classificador de junho/julho. Pontos brutos nos niveis,sem custos/fila/fills.
Envoltorio externo tecnico-780a2540,nao fechamento nem faixa de resultado
realizavel garantida;extremos individuais podem ser incompativeis no dia.
Nao somar subtotal das determinadas nem incorporar maio ao DD antesde
resolver os5casos. Resultados fechadosjunho3405/julho1100 preservados.
Cedro agosto/setembro/outubro ecurva propria intactos;nao misturar fontes.
'''
(P/'LEIA_MAIO.txt').write_text(text)
with zipfile.ZipFile(P/'Maio_Modelo_D_Analise_e_Coletas.zip','w',zipfile.ZIP_DEFLATED) as z:
 for n in ['LEIA_MAIO.txt','COLETAS_REPLAY_PRIORITARIAS.csv','REFERENCIAS_MAIO.csv','DIARIO_PROVISORIO.csv','OPERACOES_POSSIBILIDADES.csv','INVENTARIO_MAIO.json','RESULTADO_PROVISORIO.json']:z.write(P/n,n)
print(json.dumps({'inventory':inv,'coletas':rows},ensure_ascii=False,indent=2))
