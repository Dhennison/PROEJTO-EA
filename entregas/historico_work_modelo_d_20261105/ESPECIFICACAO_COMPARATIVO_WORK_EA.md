# Comparativo principal Work × EA — decisões vigentes

Decisões do usuário consolidadas para a continuidade em 08/11/2026. Elas substituem o planejamento anterior de usar cinco contratos no ensaio principal. Não alteram automaticamente parâmetros do EA instalado nem a referência original do Work.

## Duas etapas de execução

1. **Backtest principal comparativo: um contrato por nível.** Resultado principal em pontos brutos por contrato, a partir dos preços efetivamente executados. Custos financeiros registrados separadamente, sem serem descontados da pontuação de preços. O financeiro é secundário nesta etapa.
2. **Ensaio posterior de execução: cinco contratos por nível.** Validar preenchimentos/saídas parciais, proteção, cancelamento do saldo, fechamentos e conciliação. Não usar uma saída média de cinco contratos em diferentes momentos como substituto da comparação principal de um contrato com o Work.

Mesmo com um contrato, diferenças de série, cobertura, normalização ao tick, preço/fila de execução e slippage podem mudar o resultado. Registrar a causa e os comprovantes; não alterar parâmetros para forçar igualdade.

## PDF final solicitado

Work e resultado executado do EA lado a lado, por **ano, mês, dia e operação**. Chave por Data/Nível/Lado, com volumes, entrada, saída, motivo, pontos de cada lado, diferença e explicação. Totais por dia, mês, ano e período, com referência preservada.

Incluir dias sem operação; distinguir operação ausente, extra e trecho sem dados suficientes. Dados não processados ou insuficientes são pendentes, nunca zero pontos. O replay teórico já concluído dos 877 pregões não deve ser apresentado como se fosse execução do EA no MT5.

## Ambiguidades

- Work: preservar **STOP FIRST** como resultado original.
- EA/MT5: usar a cronologia observada em ticks reais e a saída efetivamente executada, podendo produzir alvo, stop ou zeragem por horário.
- No PDF, destacar a operação cuja vela era ambígua no Work e explicar qual sequência/resultado foi observado no EA.
- Se os ticks/provas não determinarem a ordem, marcar **indeterminado**, sem impor ganho ou perda.
- Distinguir preço teórico ter alcançado SL/TP de a ordem ter sido executada; manter os recibos nativos.

## Encerramento por horário

Calcular pelo preço efetivamente executado no encerramento: compra = saída − entrada; venda = entrada − saída. Resultado pode ser positivo, negativo ou zero; motivo permanece o efetivamente comprovado, e não uma inferência pela pontuação.

Preservar o calendário histórico da comparação: 17:45 entre 13/03 e 03/11/2023 inclusive; 18:00 nas demais datas da referência. O Work usa OPEN do candle do corte; o EA terá o preço da execução nativa, e a diferença deve ser explicada.

## Execução em lotes

Validar primeiro janelas curtas e um piloto operacional. Depois ampliar para setembro completo até 21/09/2026, meses agrupados e anos, até o universo de 01/03/2023–21/09/2026. Comparação automática por chave e revisão manual concentrada em divergências. A ampliação depende da cobertura e da entrega real dos ticks pelo Tester, sem rodadas manuais obrigatórias por pregão.

## Próxima etapa em andamento

A/B de controle na Genial com o mesmo DiagTicksAB v1.21 da XP: WINZ26/M5, 30/10/2026 09:00–09:10, A=terminal, B=Tester. Depois verificar os trechos de WINV26/setembro com diferenças já localizadas. Identificação histórica do contrato, vínculo do ajuste e adaptação do ensaio do EA continuam pendentes.
