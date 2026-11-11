"""Standalone PT report and PDF from the audited derived tables, not raw market data."""
from pathlib import Path
import csv,json
from decimal import Decimal as D
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.pagesizes import A4,landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
base=Path(__file__).resolve().parent
r=json.loads((base/'CONFERENCIA_COMPLETA_OBSERVADA.json').read_text())
def read(name):
 with (base/name).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter=';'))
ops=read('COMPARATIVO_COMPLETO_33_OPERACOES.csv');days=read('RESUMO_14_PREGOES.csv');same=read('ALVOS_MESMA_BARRA_WORK_12_CASOS.csv');diffs=read('DIFERENCAS_OHLC_E_LIMIARES.csv')
def pt(x,n=2):return f'{D(str(x)):,.{n}f}'.replace(',','@').replace('.',',').replace('@','.')
def short(s):return s[8:10]+'/'+s[5:7]
headline='''MODELO D — FECHAMENTO OBSERVADO DE SETEMBRO/2026
Período: 01/09 a 21/09/2026, 14 pregões — relatório de 11/11/2026
Um contrato por nível; pontos brutos, sem custos. Referências históricas auditadas do Work preservadas.

RESULTADO DO MÊS INTEIRO SOBRE OS NEGÓCIOS RECEBIDOS
Work original: +3839,308998 pontos (24 alvos e 9 stops).
Sequência dos negócios, níveis matemáticos, entrada por toque: +720,536666 pontos (19 alvos e 14 stops).
Sequência dos negócios, níveis matemáticos, entrada estrita: +720,536666 pontos (19 alvos e 14 stops).
Sequência dos negócios, grade5, entrada por toque: +1380 pontos (20 alvos e 13 stops).
Sequência dos negócios, grade5, entrada estrita: +730 pontos (19 alvos e 14 stops).
Deals do Tester com ticks gerados, já auditados: +1070 pontos (19 alvos e 14 stops).
Deals do Tester em 1 minuto OHLC, já auditados: +565 pontos (19 alvos e 14 stops).
Controle de candle inteiro com preços normalizados: +4490 pontos — continua sendo cenário por candle, não execução por negócios.

Os valores +720,54 e +1380 agora foram calculados varrendo os 14 pregões e todos os cinco níveis. Não são mais a substituição parcial dos seis desfechos mantendo as outras 27 operações do Work. O total matemático coincidir com a conta parcial anterior foi um resultado do processamento completo, não uma premissa.
O cenário principal para representar a grade de cinco pontos com toque inclusivo é GRADE5_TOQUE: +1380 pontos teóricos. Entrada estrita é sensibilidade ao toque, não simulação de fila. Não escolher o cenário pelo maior lucro e não tratar +730 a +1380 como intervalo garantido do resultado real.

COLETA COMPLETA, CORRESPONDÊNCIA INTEGRAL DE FEED NÃO APROVADA
Foram recebidos os 14 ZIPs e o log de Experts. Arquivos compartilhados repetidos nos ZIPs são idênticos, com extração reunida sem duplicar conteúdo.
Execução nativa GenialInvestimentos-PRD, build 6231, WINV26, entre 15:35:33 e 16:02:24 de 11/11/2026.
798 blocos, TODOS com duas leituras válidas idênticas, zero pendências e io_failed=false.
47.809.973 registros ALL observados, incluindo 37.191.079 negócios. A redução reteve 632.359 eventos relevantes aos níveis e aos primeiros negócios dos minutos; não são todos os ticks brutos.
Quatro variantes: 70 estados por variante (14 datas x 5 níveis), 33 operações encerradas por variante. Mesmas chaves data/nível das 33 operações Work; zero extras ou ausentes. Um nível inelegível e 36 sem toque antes do corte por variante.
Todas as aberturas e primeiros negócios no/depois do corte foram observados. Nenhuma posição das 33 permaneceu aberta ao final. Dia 03/09 foi conferido com dados e zero operações, não tratado como dia ausente.
A coleta termina em END;reason=CONCLUIDO;days=14;blocks=798;pending_blocks=0;io_failed=false.

A comparação de candles encontrou os mesmos 7875 horários do Work:
7851 candles com OHLC idêntico; 24 diferentes.
7835 candles com quantidade idêntica; 40 diferentes.
14 diferenças de OHLC estão às 18:24, depois do corte das 18h. As outras 10 estão antes do corte.
NENHUM dos 24 candles de preço divergente está entre a entrada e a saída das 33 operações nos cenários matemático/grade5 por toque.
A única diferença de quantidade dentro desses intervalos é 17/09 10:40, S61,8: ticks 139969 contra 139970 nas referências, já reproduzida no controle curto. Ela continua registrada como ressalva.
Os horários e as quantidades divergentes completos estão nos CSVs de auditoria; não se presume a causa. Não criar negócios para fechar volume e não tratar estabilidade como certificação independente do feed.

POR QUE O JSON INICIAL RECUSOU O RÓTULO DE MÊS APROVADO
O analisador original exige igualdade absoluta de OHLC em todos os 7875 candles para preencher pontos_mensais_teoricos como total aprovado. Ele corretamente deixou esse campo nulo e guardou os números em subtotal_nao_aprovado porque 24 candles não coincidem.
Isso não significa que faltam pregões, posições abertas ou blocos: todos foram processados. A validação estrita de igualdade integral da alimentação falhou; a soma observada dos negócios recebidos foi integralmente calculada.
A auditoria adicional não apagou essa recusa. Ela separou coleta completa, preço observado e equivalência do feed, e publica os números como TOTAIS CONDICIONAIS OBSERVADOS, sem homologá-los como lucro real ou feed idêntico.
Não há pedido de nova coleta para ocultar as diferenças.

EFEITO DAS 24 DIFERENÇAS SOBRE O CONTROLE POR CANDLES
Foi refeito o replay pela mesma convenção do Work sobre (a) seus candles originais e (b) os candles agregados dos negócios recebidos, mantendo o MESMO contexto por data.
Os 70 estados por grade coincidiram em entrada por minuto, saída por minuto, motivo e pontos.
Matemática por candle: +3839,308998 nas duas fontes.
Grade5 por candle: +4490 nas duas fontes.
Portanto, essas diferenças de OHLC não explicam a queda entre Work e sequência de negócios nesse controle. O efeito relevante observado foi a cronologia dentro dos candles.
A mudança de relação com um limiar encontrada em uma máxima de candle contra o SL da S50 não é condição de stop para a compra (que usa a mínima). O replay completo foi conferido em vez de presumir que qualquer diferença de preço alteraria o resultado.
Isso não prova que todos os negócios do servidor existem na amostra ou que a ordem de um negócio não recebido seja conhecida.

REFERÊNCIAS E FRONTEIRA DO TESTE
Abertura, H/L/C anterior, ajuste e corte usados foram os da referência auditada por data; o SHA-256 confere com o pacote. Resultados futuros do Work não foram usados para escolher entradas/saídas.
Não substituímos H/L/C anterior por um fechamento derivado dos ticks recebidos até 18:25. Há diferenças de fechamento às 18:24 e essa não seria uma comparação com os mesmos níveis do Work. O uso das referências congeladas isola cronologia/grade; não certifica outro algoritmo de formação diária ou o ajuste B3 em produção.
No motor de preços, o alvo/stop são testados em negócio posterior ao da entrada, como nas auditorias manuais. A redução guarda os primeiros dois registros de cada categoria para conservar o caso de gap além de entrada e proteção. No corte, usa-se o primeiro Last observado, sem preço inventado às 18h.
Não houve posição chegando ao corte neste conjunto. Isso não invalida o mês apurado; apenas significa que esta amostra não exercita a zeragem de posição aberta às 18h, que deve constar de outra amostra de homologação operacional.

DOZE ALVOS NA BARRA DE ENTRADA DO WORK
1 foi confirmado como alvo na mesma barra: S38,2 de 14/09.
6 foram alvos em barras posteriores: R61,8 de 01/09; S38,2, S50 e S61,8 de 11/09; S50 e S61,8 de 16/09.
5 tiveram stop primeiro nos dados recebidos: S38,2 e R61,8 de 10/09; S38,2 de 16/09; S38,2 e S61,8 de 17/09. A última conserva a ressalva quantitativa já descrita.
A S50 de 11/09 é um exemplo de concordância de motivo com horário diferente: Work atribui alvo às 09:30, os negócios mostram entrada às 09:30:01.632 e alvo às 09:40:23.334.
Os quatro controles fora dos seis iniciais também foram abrangidos e deram alvo em barra posterior. Isso confirma que concordância Work/Tester no motivo não certifica o minuto de saída.
A amostra não prova uma regra universal para a abertura além do alvo. Nenhuma regra do Modelo D foi substituída por STOP automático ou negação automática de alvo.

CASO QUE EXPLICA OS 650 PONTOS ENTRE TOQUE E ESTRITA
01/09, R38,2:
Linha matemática=180935,837333...; normalizada=180935.
Grade5 por toque: primeiro toque 09:47:50.034 em 180935; alvo 09:50:01.283 na linha 180660; +275 pontos teóricos.
Matemática: primeiro alcance 09:51:15.648 em 180940; stop 10:00:03.471 na linha matemática 181310,837333...; -375 pontos teóricos.
Grade5 estrita: entrada 09:51:15.648, stop 10:00:03.471 em 181310; -375 pontos.
É a ÚNICA mudança de pontos entre GRADE5_TOQUE e GRADE5_ESTRITA. Diferença=650. A igualdade ao nível pode disparar uma hipótese por toque sem comprovar execução na fila.
A diferença total entre grade5 por toque e matemática por toque é +659,463334: +650 por esse motivo/cronologia e +9,463334 de diferenças aritméticas nos demais casos.

SEPARANDO TRAJETÓRIA E PREENCHIMENTO SIMULADO
Grade5 por toque nos negócios recebidos: +1380.
Tester com ticks gerados: +1070.
32 operações têm o mesmo motivo entre esses dois cenários. A diferença aritmética de seus preços efetivos contra níveis exatos favoreceu o Tester em +465 pontos nesse subconjunto.
A única troca de motivo é S38,2 de 14/09: alvo teórico normalizado +440 contra stop simulado -335, parcela -775.
1380 - 775 + 465 = 1070.
Tester 1 minuto OHLC: +565. As outras 32 operações têm os preços nos níveis; em 14/09 o stop de -375 substitui o alvo de +440, parcela -815.
1380 - 815 = 565.
Essa decomposição é comparação aritmética de cenários, não estimativa de fila/slippage de bolsa real.

PREENCHIMENTO E RESULTADO REAL — SEM NOVA EXIGÊNCIA ESCONDIDA
Os deals do Tester JÁ mediram suas execuções simuladas e estão na tabela por operação. Não é necessário repetir aquelas duas rodadas.
Os cenários de negócios históricos assumem entrada/saída exatamente nos níveis matemáticos/normalizados. Não há spread, custos, parciais ou fila nesses pontos; o preço do primeiro negócio observado também consta em coluna separada e não é confundido com preenchimento garantido.
A fila e uma ordem que não foi colocada na bolsa naquele instante não podem ser comprovadas retroativamente. Não haverá outro teste histórico prometendo reconstruí-las para transformar estes pontos em lucro real.
A demo XP é evidência de execução em tempo corrente no ambiente demo, com seus limites; não foi alterada por esta coleta e não equivale a conta real.

VALIDAÇÃO INDEPENDENTE
O resultado do motor em fluxo foi confrontado com uma busca independente por nível sobre os eventos recebidos. Foram conferidos 280 estados, datas, eventos de entrada e saída, motivos, preços dos negócios e pontos, nas quatro variantes. Todos coincidiram.
A preservação do fluxo reduzido já havia sido confrontada com os CSVs completos recebidos, em 921 verificações e controles de igualdade/gap/timestamp/corte. A coleta nativa concluída e os seus metadados agora estão disponíveis; isso não transforma a validação em certificação independente do servidor.

CONCLUSÃO E CONTINUIDADE
A comparação de setembro sobre a alimentação recebida foi concluída: mesmos 33 pares data/nível em 14 pregões, zero extras/ausentes, nenhum saldo aberto. Há números integrais observados, dados excepcionais explicitados e comparação com os deals existentes, não uma conta híbrida de seis operações.
Para a regra de grade5 com toque inclusivo, o cenário apurado é +1380 pontos; para comparação na escala matemática original do Work, +720,536666. Work permanece +3839,308998; Tester gerado +1070 e Tester OHLC +565.
Não certificar esses valores como retorno real, equivalência integral de feeds ou desempenho de todo o histórico. A próxima ampliação usa o mesmo processo em lote, referências auditadas e amostra que exercite corte/abertura tardia/lacunas/ambiguidades, sem mais repetições manuais desta coleta de setembro.
A contagem de exposição de 1094/1877 operações no histórico longo continua sendo inventário, não número de erros demonstrados. Nenhuma alteração foi feita nos resultados originais, nas 32 ambiguidades históricas ou no núcleo do Modelo D.
'''
lines=[headline,'\nRESUMO POR PREGAO — PONTOS\nData;Operacoes;Work;Negocios_math;Negocios_grade5_toque;Grade5_estrita;Tester_ticks;Tester_OHLC\n']
for d in days:lines.append(';'.join([d['data'],d['operacoes'],d['Work_pontos'],d['sequencia_math'],d['sequencia_grade5'],d['sequencia_grade5_estrita'],d['Tester_ticks'],d['Tester_OHLC']])+'\n')
lines.append('\nCOMPARACAO DAS 33 OPERACOES\nData;Nivel;Work_motivo;Work_pontos;Negocios_math_motivo;Negocios_math_pontos;Grade5_motivo;Grade5_pontos;Grade5_estrita_pontos;Tester_ticks_pontos;Tester_OHLC_pontos;Entrada_grade5_servidor;Saida_grade5_servidor\n')
for o in ops:lines.append(';'.join(o[k] for k in ('data','nivel','Work_motivo','Work_pontos','sequencia_math_motivo','sequencia_math_pontos','sequencia_grade5_motivo','sequencia_grade5_pontos','grade5_estrita_pontos','Tester_ticks_pontos','Tester_OHLC_pontos','sequencia_grade5_entrada','sequencia_grade5_saida'))+'\n')
lines.append('''\nARQUIVOS DE AUDITORIA\nCOMPARATIVO_COMPLETO_33_OPERACOES.csv e RESUMO_14_PREGOES.csv: comparações principais.\nALVOS_MESMA_BARRA_WORK_12_CASOS.csv: cronologia dos doze casos.\nDIFERENCAS_OHLC_E_LIMIARES.csv: vinte e quatro diferenças de preço.\nCANDLES_CONFERIDOS.csv e RESSALVAS.csv: comparação de 7875 minutos e quarenta diferenças de quantidade.\nCONTROLE_DAS_24_DIFERENCAS.csv: confronto dos estados por candles nas duas fontes.\nCONFERENCIA_COMPLETA_OBSERVADA.json: contagens, totais condicionais, limites, SHA-256 dos arquivos e dos quatorze ZIPs.\nVALIDACAO_INDEPENDENTE.json: busca independente de eventos nos 280 estados.\nRESULTADO_MENSAL.json: saída original do validador estrito, preservada sem apagar sua recusa de igualdade integral.\nOs scripts permitem reproduzir a análise com os brutos locais. Os ZIPs originais e os eventos de mercado recebidos não integram a publicação.\n''')
(base/'RESULTADO_COMPLETO_SETEMBRO_WORK_NEGOCIOS_TESTER.txt').write_text(''.join(lines))
# PDF standalone; full event timestamps and source hashes remain in companion CSV/JSON.
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
pdfmetrics.registerFont(TTFont('DV',font));pdfmetrics.registerFont(TTFont('DVB',bold))
styles=getSampleStyleSheet();styles.add(ParagraphStyle(name='BodyPT',fontName='DV',fontSize=9,leading=12,spaceAfter=7));styles.add(ParagraphStyle(name='TitlePT',fontName='DVB',fontSize=17,leading=21,spaceAfter=12));styles.add(ParagraphStyle(name='HeadPT',fontName='DVB',fontSize=12,leading=15,spaceAfter=9));styles.add(ParagraphStyle(name='SmallPT',fontName='DV',fontSize=7.5,leading=10,spaceAfter=5))
story=[]
def para(s,style='BodyPT'):story.append(Paragraph(s,styles[style]))
def table(data,widths=None,size=8):
 data=[[Paragraph(str(c),styles['SmallPT']) for c in row] for row in data];t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dfe8ef')),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),.5,colors.HexColor('#768a9b')),('GRID',(0,1),(-1,-1),.2,colors.HexColor('#d4dbe1')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f4f7f9')]),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]));story.append(t);story.append(Spacer(1,10))
para('Modelo D — comparação de setembro/2026','TitlePT');para('01/09 a 21/09/2026 • 14 pregões • 33 operações • relatório de 11/11/2026','BodyPT')
para('Totais observados: negócios históricos e deals do Tester','HeadPT')
table([['Camada / cenário','Pontos','Alvos / Stops'],['Work original','+3.839,31','24 / 9'],['Negócios recebidos — matemática, toque ou estrita','+720,54','19 / 14'],['Negócios recebidos — grade5 por toque','+1.380,00','20 / 13'],['Negócios recebidos — grade5 estrita','+730,00','19 / 14'],['Deals do Tester — ticks gerados','+1.070,00','19 / 14'],['Deals do Tester — 1 minuto OHLC','+565,00','19 / 14']],[480,125,110])
para('Um contrato por nível, pontos brutos. Os cenários da sequência assumem preenchimento nos níveis. São totais calculados para o período completo recebido, sem comprovação de fila, custos ou execução em conta real.')
para('Coleta completa; equivalência integral da alimentação não aprovada','HeadPT')
para('798 blocos com duas leituras idênticas, zero pendências e nenhum erro de gravação. Foram examinados 37.191.079 negócios e os 70 estados por variante. Abertura e corte observados nos 14 pregões; 33 operações encerradas em cada variante, sem extras ou ausentes.')
para('Dos 7.875 candles comparados, 24 divergem em OHLC e 40 em quantidade. Quatorze diferenças de preço ocorrem às 18:24. Nenhuma diferença de preço está entre a entrada e a saída das 33 operações. A ressalva de um contrato em 17/09 10:40 permanece na S61,8. Esses fatos não certificam a completude independente do feed.')
para('Os +720,54 agora resultam da varredura completa, e não da antiga substituição parcial de seis resultados. O cenário grade5 por toque representa o critério inclusivo na grade; a variante estrita mede sensibilidade ao toque, não simula fila.')
story.append(PageBreak());para('Resumo por pregão — pontos','TitlePT')
data=[['Data','Nº','Work','Negócios matemática','Grade5 toque','Grade5 estrita','Tester ticks','Tester OHLC']]
for d in days:data.append([short(d['data']),d['operacoes'],pt(d['Work_pontos']),pt(d['sequencia_math']),pt(d['sequencia_grade5']),pt(d['sequencia_grade5_estrita']),pt(d['Tester_ticks']),pt(d['Tester_OHLC'])])
data.append(['TOTAL','33','3.839,31','720,54','1.380,00','730,00','1.070,00','565,00']);table(data,[60,35,100,110,105,105,100,100])
para('03/09 tem dados conferidos e zero operações. Nenhuma das 33 posições chegou aberta ao corte; isso não exercita zeragem de uma posição aberta às 18h. As referências de abertura, H/L/C anterior, ajuste e corte são as mesmas do Work, com hash conferido.')
story.append(PageBreak());para('Comparação das 33 operações','TitlePT');para('A = alvo; S = stop. Valores em pontos. Horários completos, primeiros negócios e ressalvas por operação constam no CSV acompanhante.','SmallPT')
data=[['Data','Nível','Work motivo / pts','Negócios matemática','Grade5 toque','Grade5 estrita','Tester ticks','Tester OHLC']]
for o in ops:
 ab=lambda s:'A' if s=='ALVO' else 'S' if s=='STOP' else s
 data.append([short(o['data']),o['nivel'],ab(o['Work_motivo'])+' '+pt(o['Work_pontos']),ab(o['sequencia_math_motivo'])+' '+pt(o['sequencia_math_pontos']),ab(o['sequencia_grade5_motivo'])+' '+pt(o['sequencia_grade5_pontos']),pt(o['grade5_estrita_pontos']),pt(o['Tester_ticks_pontos']),pt(o['Tester_OHLC_pontos'])])
table(data,[53,55,115,120,110,95,85,82]);para('S61,8 de 17/09: stop observado com ressalva quantitativa no minuto de saída. Os resultados do Work e os deals do Tester foram preservados.','SmallPT')
story.append(PageBreak());para('O que mudou: cronologia e grade','TitlePT')
para('Dos 12 alvos que o Work creditou na barra da entrada, 1 ocorreu nessa barra, 6 vieram depois e 5 tiveram stop primeiro nos negócios recebidos. A concordância do motivo, sozinha, não confirma o horário da saída.')
data=[['Data / nível','Work: entrada e alvo','Entrada nos negócios','Saída nos negócios','Primeira saída']]
for x in same:data.append([short(x['data'])+' '+x['nivel'],x['Work_entrada_saida'],x['sequencia_entrada'][11:],x['sequencia_saida'][11:],x['sequencia_motivo']])
table(data,[125,145,145,145,155])
para('01/09 R38,2: grade5 por toque entra às 09:47:50.034 e atinge alvo às 09:50:01.283 (+275). Matemática e grade5 estrita entram às 09:51:15.648 e atingem stop às 10:00:03.471 (−375). Essa operação explica sozinha os 650 pontos entre grade5 por toque e estrita.')
para('Comparação com os deals: 1.380 − 775 (troca de motivo em 14/09 S38,2) + 465 (diferença aritmética de preenchimentos nas outras 32) = 1.070. No Tester OHLC: 1.380 − 815 (a mesma troca, com preços nos níveis) = 565.')
story.append(PageBreak());para('Qualidade dos dados e alcance','TitlePT')
data=[['Minuto','Campos OHLC diferentes','Antes das 18h?','Dentro de operação?']]
for x in diffs:data.append([x['time'],x['campos_diferentes'],'Sim' if x['antes_corte']=='True' else 'Não','Não'])
table(data,[210,200,140,165])
para('O replay por candle inteiro foi igual nas duas fontes para todos os 70 estados, tanto na matemática (+3.839,31) quanto na grade5 (+4.490). As diferenças de candles identificadas não alteraram esse controle; a divergência de cronologia permanece.')
para('A validação estrita original recusou equivalência integral de OHLC. Esta auditoria preserva essa recusa e publica totais condicionais sobre o fluxo recebido. Uma busca independente confirmou os 280 estados, eventos, motivos e pontos nas quatro variantes. Não há nova coleta solicitada para ocultar as exceções.')
para('Reprodução: TXT completo, tabelas por pregão e operação, diferenças de candles/volume, metadados e hashes dos 14 ZIPs estão nos arquivos acompanhantes. Os arquivos de eventos recebidos são reduzidos; não são ticks completos para alimentar outro Tester.')

def footer(canvas,doc):
 canvas.setFont('DV',7);canvas.drawString(35,18,'Modelo D • dados recebidos da Genial • pontos condicionais / deals simulados • não é comprovação de PnL real');canvas.drawRightString(805,18,str(doc.page))
SimpleDocTemplate(str(base/'Comparativo_Setembro_Work_Negocios_Tester.pdf'),pagesize=landscape(A4),rightMargin=35,leftMargin=35,topMargin=30,bottomMargin=32,title='Modelo D — Setembro 2026 — Work, negócios e Tester',author='Auditoria Modelo D').build(story,onFirstPage=footer,onLaterPages=footer)
print('Created TXT and PDF')
