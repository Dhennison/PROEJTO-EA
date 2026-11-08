# Teste 06 — WINZ26, 29/10/2026, 09:00–09:10

Parâmetros e período simulado corretos. Duas leituras estáveis, sem erros.
ALL=36926, TRADE=36926, INFO=36922; Last e volume positivos em todos os ALL.
Flags 30 em 36922 registros e 24 em quatro. Flags 30 = BID|ASK|LAST|VOLUME;
flags 24 = LAST|VOLUME. Por isso INFO e TRADE se sobrepõem: não exigir
TRADE+INFO=ALL quando o mesmo registro traz bits dos dois grupos.

O Diário é explícito: ticks reais AUSENTES nas 565/565 barras M1 e geração
substituta usada. Não tratar os 36926 como negócios reais certificados.
O critério flags de negócio + Last válido é necessário para interpretar os
registros da estratégia, mas NÃO é certificado da procedência real do fluxo
no Tester. Não confundir ausência com o descarte dos testes 01–05.

TXT/CSV nativos não recebidos; autenticação com dados do terminal pendente.
O fato de esses registros satisfazerem o classificador não prova que o EA
completo liberaria todas as demais validações de abertura, cobertura e ajuste.
Não afirmar que o EA inteiro operaria nem que o dia está homologado.

Concluídas as seis EXECUÇÕES do plano. Nenhuma certificou alimentação real
para o backtest. Próximo: conferir CSVs das seis rodadas, preservar a tentativa
cruzada 762592437 e coletar controle A de 29/10 com 06_20261029_WINZ26_A.set.
