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

## Próxima evidência necessária

O diagnóstico `ModeloD_Diagnostico_Ticks_20261029_1038_v1_00` consulta duas vezes a janela 10:35–10:40 e o minuto 10:38, comparando `COPY_TICKS_TRADE`, `COPY_TICKS_ALL`, flags LAST, Bid, Ask, OHLC M1, ordem e multiplicidade. Ele não altera EA, histórico ou estado. Somente depois dessa evidência será possível distinguir filtro/flags, alteração posterior do histórico ou inconsistência persistente do terminal/servidor.

A Etapa 1 permanece parcialmente aceita: compilação, inicialização, retomada, dados diários, contrato, inventário, conciliação vazia, persistência, política de bloqueio e encerramento foram comprovados. Reconstrução completa, recuperação bem-sucedida e gestão com posições continuam sem comprovação.
