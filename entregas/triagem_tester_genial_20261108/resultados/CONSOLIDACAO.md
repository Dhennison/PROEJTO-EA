# Seis execuções concluídas — Genial, 08/11/2026

| Teste | Símbolo/data | ALL | TRADE: flags + Last | Diário |
|---|---|---:|---:|---|
|01|WINV26 01/09|5200|0|Ticks reais descartados|
|02|WINV26 02/09|15966|0|Ticks reais descartados|
|03|WINV26 02/10|29650|0|Ticks reais descartados|
|04|WINV26 09/10|30350|0|Ticks reais descartados|
|05|WINZ26 19/10|37831|0|Ticks reais descartados|
|06|WINZ26 29/10|36926|36926|Ticks reais ausentes; geração substituta|

Todos os relatórios estabilizaram em duas leituras sem erros. Os registros
brutos das seis execuções ainda não foram recebidos. Nenhum dia está aprovado
como alimentação de ticks reais para o backtest do Modelo D.

O teste 06 demonstra por que flags e Last são insuficientes para certificar
origem: a geração substituta pode produzir ambos, inclusive volume positivo.
Na rodada 02, Last era positivo sem flags de negócio. São comportamentos
distintos do fluxo gerado, sem prova da causa original dessas diferenças.

Preservar a tentativa com parâmetros 05 e período 29/10: ela retornou 162331
negócios de 19/10 anteriores à simulação, sem processar ticks/barras no motor.
É uma consulta histórica fora do período, não validação de alimentação OnTick.

Próximo: enviar TXT/CSV GTR_01 a GTR_06 (incluindo a segunda rodada tag 05,
sufixo 762592437) e coletar controle A de 29/10 no terminal, sem ordens,
mesmo símbolo/janela. Depois comparar procedência, cronologia, OHLC e volumes.
Não expandir os backtests para todo o período antes de aprovar uma alimentação.
Não alterar estratégia, apagar caches ou inventar Last para superar o problema.
