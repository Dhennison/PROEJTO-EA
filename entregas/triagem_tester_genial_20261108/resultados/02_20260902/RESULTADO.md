# Teste 02 — WINV26, 02/09/2026, 16:10–16:15

Parâmetros dos prints e Diário conferem. Consulta estável em duas leituras,
sem erro: ALL=15966, INFO=15966, TRADE=0, flags=6 em todos os registros,
volume positivo=0. Coleta focal anterior do terminal: ALL=17348 e TRADE=14210.
O Diário confirma descarte de todos os ticks reais nas 562/562 barras M1,
3.639.772 preços incompatíveis e divergência de volumes nas 562 barras.

Achado importante: **Last positivo em todos os 15966 registros**, apesar de
nenhum possuir flags de negócio. Primeiro Last=182390 (mesmo valor do fechamento
M1/Work de 01/09 às 18:24), com Bid=187725/Ask=187730 em 02/09 às 16:10.
É dado carregado sem indicação de novo negócio. O Diário não prova que Last
permaneceu constante em todas as linhas nem a origem desse valor; conferir CSV.
Last positivo sozinho aceitaria cotações geradas como negócios indevidamente.
Não trocar o critério por last>0 nem substituir por Bid/Ask.

TXT/CSV nativos da execução ainda não recebidos: resultados acima extraídos do
Diário. A origem do descarte continua desconhecida. A consulta usou dados já
sincronizados, o que não demonstra corrupção de cache.

Próximo teste: 03_20261002_WINV26_B.set; Configuração WINV26/M5,
02/10/2026 até 03/10/2026, ticks reais, janela 09:00–09:10,
tag GTR_03_20261002_B, CSV true. Símbolo candidato de calendário,
sem certificação do contrato original do Work.
