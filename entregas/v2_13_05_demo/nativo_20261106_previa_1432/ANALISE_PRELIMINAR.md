# Prévia nativa de 06/11 — relatório até 14:32:01

Não é fechamento do pregão. Arquivos originais recebidos e preservados.

- Arquivamento de 05/11 confirmado às 08:55:01, revisão 61. Primeira prova nativa desta função; não certifica retenção prolongada.
- Cinco pendentes enviadas/aceitas entre 09:00:54 e 09:01:02, todas volume 1 e com SL/TP fixos.
- R38,2: ordem 2586235149, aceitação servidor 09:01:00.342, preço solicitado 168805, SL169180, TP168440. Primeiro toque Last matemático às 10:30:02.602. Cancelamento planejado em INTEGRATED_CYCLE (revisão 81) às 10:30:03; pedido nativo kind3 às 10:30:04, retcode10009 e cancel_phase6 em revisão84. Nenhum deal do nível3 no relatório e volume executado zero no CSV. Ausência de setas corresponde à ausência de execução registrada.
- O cancelamento partiu do EA. Aceitação precede primeiro toque, cutoff=0 e nenhum deal/posição desse nível registrado. A lógica de MDOpCycle indica fronteira teórica como gatilho restante; o relatório não grava o tick e horário dessa fronteira. Não afirmar correção nem erro sem reconstruir a sequência. M1 10:30: O168560/H168870/L168200/C168285 permite passagem pelo alvo, mas não prova ordem temporal nem passagem anterior ao pedido das10:30:04. Solicitar ticks reais WINZ26 de10:29–10:31 para verificar.
- R61,8: ordem2586235453 aceita09:01:02.049; primeiro toque11:20:01.579; venda executada11:20:01.810 a169400 (deal1875522306); saída11:23:40.806 a169250 (deal1875541727), razão nativa5=TP. +150 pontos, +30BRL DEMO, residual0. Horário de impressão do deal não é seu timestamp de execução.
- S38,2/S50/S61,8: sem toque no trecho conferido até14:32, sem execuções e pendentes ativas no CSV.
- Saldo efetivamente executado desta prévia: +150 pontos/+30BRL, uma operação encerrada. Não incluir pontuação hipotética da R38 nem declarar fechamento do dia.

Próxima evidência necessária para a R38: exportação nativa Todos os ticks, WINZ26,06/11/2026 10:29:00–10:31:00. Last/Bid/Ask/flags permitem verificar a trajetória e investigar o cancelamento. Last tocar não prova preenchimento na fila/simulador; eventual causa de não preenchimento na corretora também não deve ser inventada.
