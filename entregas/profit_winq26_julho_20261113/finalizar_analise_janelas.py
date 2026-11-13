from pathlib import Path
from decimal import Decimal as D
import csv,json,zipfile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import fitz
P=Path(__file__).parent
s=json.loads((P/'REPLAY_TODAS_ABAS_RESULTADO.json').read_text());daily=list(csv.DictReader((P/'DIARIO_APOS_JANELAS.csv').open(encoding='utf-8-sig'),delimiter=';'))
assert s['pending_operation_count']==0 and len(s['results'])==11
assert all(r['tie_invariant'] and not r['mixed_exit_barrier_ms'] for r in s['results'])
assert daily[-1]['date']=='2026-07-31' and daily[-1]['work_points']==''
assert sum(D(r['test_points']) for r in daily)==D(1100)
checks=list(csv.DictReader((P/'REPLAY_TODAS_ABAS_M1.csv').open(encoding='utf-8-sig'),delimiter=';'))
assert all(r['ohlc_match']=='True' and r['quantity_match']=='True' for r in checks if r['full_minute_from_bounds']=='True')
wb=wp=wd=tb=tp=td=D(0);curve=[]
for r in daily:
 tb+=D(r['test_points']);tp=max(tp,tb);td=max(td,tp-tb)
 if r['work_points']!='':wb+=D(r['work_points']);wp=max(wp,wb);wd=max(wd,wp-wb)
 curve.append(dict(date=r['date'],test_points=r['test_points'],test_balance=str(tb),test_current_dd=str(tp-tb),test_max_dd=str(td),work_points=r['work_points'],work_balance=str(wb) if r['work_points']!='' else '',work_max_dd=str(wd) if r['work_points']!='' else ''))
with (P/'CURVA_JULHO_ISOLADA.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(curve[0]),delimiter=';',lineterminator='\n');w.writeheader();w.writerows(curve)
s['DD_julho_isolado']=str(td);s['DD_Work_julho_isolado']=str(wd);s['minutos_iguais_ohlc_quantidade']=sum(r['ohlc_match']=='True' and r['quantity_match']=='True' for r in checks);s['minutos_parciais_de_borda']=sum(r['ohlc_match']!='True' or r['quantity_match']!='True' for r in checks)
flips=[r for r in s['results'] if ('ALVO' if r['primary']['reason']=='TP' else 'STOP')!=next(x for x in csv.DictReader((P/'REPLAY_OPERACOES_RESOLVIDAS.csv').open(encoding='utf-8-sig'),delimiter=';') if x['date']==r['date'] and x['level']==r['level'])['work_reason']]
s['trocas_Work']=len(flips);s['datas_trocas']=[r['date']+' '+r['level'] for r in flips]
s['observacao_grade']='06julS38.2: alvo teorico176160.542 nao atingido apos entrada (SL);grade5alvo176160 atingido (TP+105). Principal continua grade5. Nao mudar regra para escolher resultado.'
(P/'REPLAY_TODAS_ABAS_RESULTADO.json').write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
progress=dict(status=s['status'],julho_operacoes=47,determinadas_por_candles_sem_coleta=36,resolvidas_Replay=11,pendentes_operacoes=0,resultado_principal='1100',work='5255.800668',diferenca='-4155.800668',controle_cobertura_pendente='10jul09:55–09:58,ausencia09:56',fonte='M1+Replay pontual,nao fita integral',DD_somente_julho=str(td),DD_Work_somente_julho=str(wd))
(P/'PROGRESSO_RESOLUCAO.json').write_text(json.dumps(progress,ensure_ascii=False,indent=2)+'\n')
text=f'''JULHO/2026 — RESULTADO PRINCIPAL APOS JANELAS REPLAY
Nosso: +1.100 pontos. Work: +5.255,800668. Diferenca: -4.155,800668.
47operacoes,22datas comparaveis Work;31jul extra sem entradas.
Fonte:36resultados determinados pelos candles M1 +11resolvidos por Replay
pontual. NAO apresentar como mes inteiro auditado tick a tick ou fills reais.
Parametros D originais,1contrato/nivel,grade5,toque inclusivo,corte18h.
Custos,fila e slippage nao incluidos.

COBERTURA RECEBIDA
9abas,824455registros,nenhuma alcanca limite observado200001.
13minutos reconstituem OHLC e quantidade exatos do CSV.12minutos de borda
parciais divergem como esperado,pelo inicio/fim da janela. Todos os minutos
de entrada das11operacoes pendentes conferem OHLC e quantidade.
Dia28duasabas tratadas separadamente.01jul repete coleta anterior.
Dois desempates entre registros do mesmo ms produzem mesmo motivo/pontos;
sem grupos com TP e SL opostos no mesmo ms dentro das posicoes investigadas.
Isso nao certifica sequencia oficial,completude absoluta ou fonte independente.

RESULTADOS
SeisALVO Work viraramSL:02julR38.2,06julS50,06julS61.8,16julS38.2,
28julR38.2,29julS38.2.14julR38.2 confirmaSTOP doWork. Demais quatro
pendencias confirmamALVO na grade5,incluindo01jul ja conferido antes.
Seis saidas estao nas copias;cinco sao determinadas pelos candles seguintes,
apos copia resolver ordem entrada/alvo. Horarios com sufixoCANDLE indicam
somente minuto,nao segundo exato. Nunca reutilizar maxima anterior a entrada.
Testes de regressao cobrem esse caso e barra de entrada incompleta.

EFEITO DA GRADE
06julS38.2:alvo matematico176160,542 nao atingido depois da entrada antes
SL;alvo normalizado176160 foi atingido,+105. Principal permanece grade5,
mesmo criterio de agosto/setembro/outubro. Nao selecionar regra pelo resultado.

CONTROLE AINDA NAO RECEBIDO
A planilha nao tem10jul09:55–09:58 para verificar ausencia de09:56. Duas
operacoes conhecidas desse dia ja encerradas09:12 e09:55;coleta e controle
de cobertura,nao uma das11ambiguidades. Nao interpolar. Resultado calculado
acima fica identificado com essa ressalva ate conferirmos a janela.

DRAWDOWN
Julho isolado,fechamentos diarios:teste{td};Work{wd}pontos.
NAO atualizar DD Cedro3meses usando julho como se fosse a mesma serie de
ticks integrais. Serie M1+Replay explicitamente separada;Cedro original intacto.
PDFs de julho guardados para compilacao final. Resultados originais preservados.
'''
(P/'LEIA_RESULTADO_APOS_JANELAS.txt').write_text(text)
def fmt(x):
 if x=='':return '-'
 v=D(x);return f'{v:,.2f}'.replace(',','X').replace('.',',').replace('X','.')
pdf=P/'Julho_2026_Comparativo_Diario_Em_Analise.pdf';c=canvas.Canvas(str(pdf),pagesize=A4);W,H=A4
c.setFont('Helvetica-Bold',16);c.drawString(35,H-42,'MODELO D - JULHO / 2026')
c.setFont('Helvetica',9);c.drawString(35,H-61,'M1 + janelas Replay | Grade 5 | Pontos brutos nos niveis')
c.drawString(35,H-76,'Controle de cobertura de 10/07 ainda pendente.')
y=H-107;c.setFont('Helvetica-Bold',9)
for x,t in [(35,'Data'),(205,'Work'),(320,'Nosso'),(445,'Diferenca')]:c.drawString(x,y,t)
y-=22
for r in daily:
 c.setFont('Helvetica',9);c.drawString(35,y,r['date'][8:]+'/07/2026')
 for x,k in [(270,'work_points'),(390,'test_points'),(555,'difference')]:c.drawRightString(x,y,fmt(r[k]))
 y-=19
c.setFont('Helvetica-Bold',11);y-=10;c.drawString(35,y,'TOTAL');c.drawRightString(270,y,fmt(s['work_points']));c.drawRightString(390,y,fmt(s['test_points']));c.drawRightString(555,y,fmt(s['difference']))
y-=28;c.setFont('Helvetica',9);c.drawString(35,y,f'DD julho isolado: Work {fmt(str(wd))} | Nosso {fmt(str(td))}')
y-=24
for line in ['36 operacoes determinadas em M1; 11 resolvidas com janelas Replay.','Seis alvos do Work passaram a stop. Sem custos, fila ou garantia de execucao.','31/07 fora da referencia Work; traco nao significa resultado zero.','Curva de julho separada da serie Cedro integral de agosto a outubro.']:
 c.drawString(35,y,line);y-=15
c.save()
with fitz.open(pdf) as doc:
 assert len(doc)==1 and '1.100,00' in doc[0].get_text() and '5.255,80' in doc[0].get_text()
tech=P/'Julho_2026_Analise_Tecnica_Em_Analise.pdf';c=canvas.Canvas(str(tech),pagesize=A4);y=H-40;c.setFont('Helvetica',9)
for line in text.splitlines():
 if y<40:c.showPage();c.setFont('Helvetica',9);y=H-40
 c.drawString(28,y,line);y-=14
c.save()
with zipfile.ZipFile(P/'Julho_Modelo_D_Apos_Janelas.zip','w',zipfile.ZIP_DEFLATED) as z:
 for n in ['LEIA_RESULTADO_APOS_JANELAS.txt','DIARIO_APOS_JANELAS.csv','REPLAY_OPERACOES_RESOLVIDAS.csv','REPLAY_TODAS_ABAS_AUDITORIA.csv','PROGRESSO_RESOLUCAO.json',pdf.name,tech.name]:z.write(P/n,n)
print(json.dumps(progress,indent=2))
