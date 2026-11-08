# Primeiro teste: WINV26, 01/09/2026, 18:20–18:25

Diário recebido e conferido. Consulta B estável em duas leituras, erro zero:
ALL=5200, INFO=5200, TRADE=0, Last positivo=0, flags=6 em todos os 5200 registros
segundo o relatório impresso no Diário. CSV e TXT nativos ainda não recebidos.
A coleta focal do terminal da mesma janela tinha ALL=2955 e TRADE=1907.

O Diário individualiza descarte de todos os ticks reais em **01/09 e 02/09**.
Informa 563 barras com mismatch em 01/09 e 562 em 02/09; o resumo registra
1125/1125 barras com descarte e divergência de volumes. Não somar contagens de
preços das linhas diárias para inferir total: o resumo de preços tem escopo
próprio. Há também indicação de uma barra M1 ausente com ticks presentes;
o trecho da mensagem não isola um minuto confiável para essa ausência.

A remoção automática em 50% do intervalo foi esperada: a consulta foi concluída
e chamou ExpertRemove. Não significa falha ou metade da janela consultada.
O horário da chamada do timer diverge do TimeCurrent impresso (18:31:24);
não usar essa diferença como prova de problema de fuso ou causa do descarte.

Este retorno estende a confirmação do descarte ao WINV26 em setembro;
a origem da incompatibilidade permanece desconhecida. A janela específica
de 02/09 16:10–16:15 ainda precisa do teste 02, embora o descarte diário
em 02/09 já esteja documentado nesta execução.

Próximo: carregar 02_20260902_WINV26_B.set, manter WINV26/M5/ticks reais,
configurar Tester 02/09 até 03/09 e consultar 16:10–16:15. Preservar Diários
por execução e reunir TXT/CSV GTR_01 e GTR_02 para auditoria bruta.
