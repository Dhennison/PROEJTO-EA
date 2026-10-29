# Análise da observação nativa v2.05 — 29/10/2026

## Evidência confirmada

- EA v2.05 compilado no MetaEditor: 0 erros, 0 avisos.
- Execução no WIN$N M5 de 10:38:40 a 10:53:21, encerrada manualmente com `STOP;reason=1` e relatório fechado.
- Marcador e diário v2.04 retomados: `DIARIO_REABERTO_VALIDADO`, revisão inicial 1.
- Relógio passou pela amostragem; dados diários foram confirmados para 29/10/2026 e contrato WINZ26.
- Diário recebeu `DAILY_DATA`, revisão 2, com cinco níveis persistidos.
- Duas leituras do inventário conferiram; conciliação informou `ALL_CHAINS_RECONCILED`.
- Conta observada sem ordens ou posições vinculadas: zero intenções e zero pendências. Esta execução não comprova proteção, parcial ou fechamento reais.
- Reconstrução aprovou 19 blocos de cinco minutos, 983.178 ticks, da abertura até 10:35 exclusivo, sempre com registros nos cinco minutos e OHLC M1 correspondente.

## Bloqueio preservado

No bloco 10:35–10:40, o minuto 10:38 divergiu:

- `COPY_TICKS_TRADE`: O=172895, H=173240, L=172845, C=173165, 11.660 ticks;
- M1: O=172895, H=173250, L=172845, C=173165.

A diferença ficou restrita à máxima, 10 pontos. O EA reconsultou o mesmo bloco 19 vezes, aproximadamente a cada 30 segundos, sem mudança. Após dez minutos, recusou o bloco e bloqueou novas tentativas na sessão. Não aprovou checkpoint nem inventou tick. Esse comportamento confirma a política de recuperação, mas a origem da divergência ainda é desconhecida.

## Diagnóstico posterior

Às 11:01, o diagnóstico nativo encontrou 13.655 eventos TRADE no minuto, exatamente o `tick_volume` do M1. Entre os 1.995 eventos que não haviam sido fornecidos ao EA estava o negócio LAST de 173250 às 10:38:48.427. TRADE, ALL filtrado e M1 passaram a ter OHLC idêntico. As duas rodadas diagnósticas retornaram a mesma quantidade e sequência, sem erros, rejeições, regressões ou registros fora da janela.

Isso comprova alteração/complementação posterior do histórico TRADE disponível no terminal. Não comprova a causa interna do atraso no terminal ou servidor. O cálculo OHLC e o filtro de negociação do EA não produziram a diferença.

## Tratamento v2.06

Em divergência TRADE/M1, o EA consulta ALL na mesma janela e preserva somente registros com as mesmas flags de negociação. Só avança se o candidato filtrado passar integralmente pelas validações e pelo M1. Se ALL também divergir, descarta o candidato e mantém cursor/bloqueio. A estratégia Last, a ordem e a multiplicidade não mudam.

A Etapa 1 permanece parcialmente aceita: compilação, inicialização, retomada, dados diários, contrato, inventário, conciliação vazia, persistência, política de bloqueio e encerramento foram comprovados. A v2.06 ainda precisa de compilação e observação nativas. Gestão com posições continua sem comprovação.

## Observação nativa v2.06

A v2.06 compilou com 0 erros/0 avisos e executou no WIN$N M5 de 11:17:15 a 11:33:05. Retomou o diário na revisão 2, confirmou dados de 29/10/WINZ26 e duas leituras do inventário, reconstruiu 44 blocos e 1.659.934 ticks até 11:33 exclusivo, sempre com M1 consistente. Não houve divergência, retry, bloqueio, toque, ordem, posição ou intenção. O relatório encerrou com `STOP;reason=1` e `RELATORIO_FECHADO`.

A recuperação ALL não foi acionada porque o cache TRADE já estava completo. Sua execução nativa permanece sem ocorrência; os casos positivo/negativo foram controlados localmente.

As cinco entradas alternaram entre cobertura do minuto corrente ainda não fechada e `CALCULO_OU_DISPONIBILIDADE_DE_MARGEM`. A v2.07 separa a causa da margem sem alterar a decisão e sem registrar saldo. Uma execução curta deve identificar se houve falha de `OrderCalcMargin` ou margem livre insuficiente.
