from pathlib import Path
from decimal import Decimal as D
import csv,json,zipfile
P=Path(__file__).parent

def read(n):
 with (P/n).open(encoding='utf-8-sig') as f:return list(csv.DictReader(f,delimiter=';'))
ops=read('OPERACOES_POSSIBILIDADES.csv');bars=read('JANELAS_REPLAY.csv');refs=read('REFERENCIAS_JUNHO.csv')
contract=lambda d:'WINM26' if d<'2026-06-17' else 'WINQ26'
# Explicit calendar confirmed by user, independently of operation outcomes.
for r in refs:r['contrato_Replay']=contract(r['date'])
with (P/'REFERENCIAS_JUNHO.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(refs[0]),delimiter=';',lineterminator='\n');w.writeheader();w.writerows(refs)
pending={(o['date'],o['level']) for o in ops if o['determined']=='False'}
rows=[]
for r in bars:
 if (r['date'],r['level']) not in pending:continue
 minute=r['minute'];h,m=map(int,minute.split(':'));end=f'{h+(m+1)//60:02d}:{(m+1)%60:02d}:00'
 same=next((x for x in rows if x['data']==r['date'] and x['inicio']==minute+':00'),None)
 if same:same['niveis']+=','+r['level']
 else:rows.append(dict(data=r['date'],contrato=contract(r['date']),inicio=minute+':00',fim_exclusivo=end,niveis=r['level'],motivo='Ordem entrada/alvo/stop ambigua no M1'))
# Grade changes a determined result vs mathematical Work: request its actual touch.
extra=[]
for o in ops:
 if o['determined']!='True':continue
 reason=o['outcomes'].split(':',1)[0];expected='ALVO' if reason=='TP' else 'STOP' if reason=='SL' else 'ZERAGEM 18H'
 if expected!=o['work_reason']:
  cand=o['exit_candidates'].split('|')[0];stamp=cand.split('@',1)[1];minute=stamp[11:16];h,m=map(int,minute.split(':'))
  r=dict(data=o['date'],contrato=contract(o['date']),inicio=minute+':00',fim_exclusivo=f'{h+(m+1)//60:02d}:{(m+1)%60:02d}:00',niveis=o['level'],motivo='Controle de toque na grade5:desfecho difere Work')
  rows.append(r);extra.append(o)
rows.sort(key=lambda r:(r['data'],r['inicio']))
with (P/'COLETAS_REPLAY_PRIORITARIAS.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter=';',lineterminator='\n');w.writeheader();w.writerows(rows)
summary=json.loads((P/'RESULTADO_PROVISORIO.json').read_text());summary.update(contratos={'ate_2026_06_16':'WINM26','desde_2026_06_17':'WINQ26'},calendario_confirmado_usuario=True,grade_controls=[{'date':o['date'],'level':o['level'],'normalized_outcome':o['outcomes'],'Work_reason':o['work_reason'],'Work_points':o['work_points']} for o in extra],window_count=len(rows),window_dates=sorted({r['data'] for r in rows}),previous_context_first_day=refs[0]['previous'],resultado_principal='AGUARDANDO_REPLAY',previous_context_method='HLC do pregao anterior completo,abertura atual,ajuste operacional Work;sem trocar referencias para melhorar resultado.')
(P/'RESULTADO_PROVISORIO.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
text='''JUNHO/2026 — MODELO D — INVENTARIO E ANALISE M1
Resultado principal para comparar com Work: AGUARDANDO REPLAY.
Work: +7214,523331 pontos,43operacoes,21pregoes.
Fonte original WINFUT M1:11825barras. MT5 WIN$N:mesmos11825horarios/OHLC,
zero diferencas. CSV novo WINQ26:5628barras,10pregoes17–30jun;OHLC iguais.
Nao e necessario pedir novamente candles ou ajustes de junho.
Ajustes21datas presentes no Work. XLSX JUN a AGO so tem6datas de junho,
23/24/25/26/29/30;todas iguais Work. Nao alegar que XLSX cobre junho inteiro.
Contexto01jun vem29maio,candles ja no acervo. HLC pregao anterior completo,
sem truncar18h;abertura atual;ajuste operacional congelado Work.
Niveis matematicos entrada/SL/TP das43operacoes iguais Work,tol0,00001.

35operacoes com resultado determinado nos candles.8operacoes pendentes
em03/15/22/30jun. Controle adicional23junR38.2:Work encerra18h+55,092,
grade5 alcancaTP+495 no minuto17:00;conferir toque,nao alterar criterio.
Total6janelas de1minuto em03jun(3),15jun(1),22jun(1),23jun(1),30jun(1):
a contagem exata esta no CSV (7janelas:3+1+1+1+1).
Dia22um minuto resolve tres niveis. Pode mandar mesma planilha,abas por data;
dia03preferir3abas ou uma09:03–09:06 se nao atingir limite200001registros.
Comecar antes do inicio,reproduzir sem saltar dentrojanela,copiar ao final.
Todos negocios/corretoras/tipos,sem filtrar lotes,sem deduplicar negocios.
Conferir alcance,OHLC/quantidade e ordem antes de resolver.

CONTRATOS:WINM26ate16/06;WINQ26desde17/06. Confirmado pelo usuario com
calendario B3;nao confundir SerieWINFUT dos candles com contrato da fita.
Historico continuo Work preservado inclusive contexto na virada;operacoes
atualizadas com negocios do contrato indicado depois de verificar OHLC.

Metodo:mesmo classificador de julho,grade5,1contrato/nivel,parametros originais,
sem custos/fills/trajetoria sintetica. Ramos TP/SL/ABERTA,propagados ate corte18h.
Envoltorio tecnico2975–8070 e soma de extremos por operacao,nao fechamento
nem faixa de execucao real;extremos podem nao coexistir numa mesma fita.
Sem lacunas intradiarias nos M1 fornecidos;nao e certificado de todos negocios.
Nao adicionar junho aos resultados/DD fechados antes da resolucao. DDporserie
em ordem cronologica;nao misturar M1+Replay com Cedro integral sem identificar.
Julho encerrado+1100,controle10juldispensado expressamente;nao pedir novamente.
'''.replace('Total6janelas de1minuto em03jun(3),15jun(1),22jun(1),23jun(1),30jun(1):\na contagem exata esta no CSV (7janelas:3+1+1+1+1).','Total7janelas de1minuto em03jun(3),15jun(1),22jun(1),23jun(1),30jun(1).')
(P/'LEIA_JUNHO.txt').write_text(text)
with zipfile.ZipFile(P/'Junho_Modelo_D_Analise_e_Coletas.zip','w',zipfile.ZIP_DEFLATED) as z:
 for n in ['LEIA_JUNHO.txt','COLETAS_REPLAY_PRIORITARIAS.csv','REFERENCIAS_JUNHO.csv','DIARIO_PROVISORIO.csv','OPERACOES_POSSIBILIDADES.csv','INVENTARIO_JUNHO.json','RESULTADO_PROVISORIO.json']:z.write(P/n,n)
assert len(rows)==7 and len(pending)==8 and len(extra)==1
assert all(contract(r['data'])==r['contrato'] for r in rows)
print(json.dumps(rows,ensure_ascii=False,indent=2))
