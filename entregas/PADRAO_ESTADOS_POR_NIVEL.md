# Descrição específica dos estados por nível

Decisão do usuário após a conferência do CSV de 05/11/2026. Aplicar nas análises a partir de agora e na próxima evolução dos relatórios. Não implica atualização do executável já instalado.

Tratar separadamente e depois combinar:

1. **Toque Last:** observado (com horário), sem toque até o horizonte conferido, ou não conferido/reconstrução pendente. Sem execução não prova ausência de toque. Preenchimento em preço normalizado também não substitui a conferência do toque matemático Last.
2. **Execução:** nenhuma, parcial (quantidade preenchida e saldo), ou total, com horários e preços efetivos.
3. **Ordem:** ativa, cancelamento solicitado, cancelamento confirmado, rejeitada ou resposta incerta; preservar ticket e geração. Pedido enviado não equivale a efeito confirmado.
4. **Posição:** aberta, parcialmente encerrada ou encerrada, com residual e proteções conferidas. Nível consumido para novas entradas pode ter posição ainda em andamento.
5. **Motivo e tempo:** SL, TP, corte, outro motivo comprovado ou motivo indisponível. Distinguir horário do pedido do EA, marcação da corretora e confirmação conciliada. Não inventar horário/motivo.
6. **Oportunidade:** intacta/elegível, consumida por toque/execução ou impedida por filtro/dados/horário; ausência de toque não dispensa os outros gates.

Exemplos de linguagem:

- R61,8 em 05/11: sem toque no histórico conferido até 18h, sem execução, pendente cancelada no corte. Pedido 18:00:00.769; confirmação conciliada 18:00:02.615; Histórico da corretora exibiu 18:00:01.
- Nível com toque, sem execução; pendente previamente aceita ainda ativa, sujeita às fronteiras e ao corte.
- Parcial: 6 executados em posição, saldo 4 pendente na mesma ordem, sem duplicação.
- Posição encerrada por SL/TP; saldo cancelado quando devido; nível bloqueado para novas entradas.
- Histórico ainda não conferido até o presente: toque não confirmado; novas entradas aguardando.

O CSV v2.13.05 mantém sua estrutura publicada. Nas análises usar os campos do CSV em conjunto com o diário/relatório e a cobertura Last. Uma futura alteração de formato deverá trazer explicitamente essas dimensões e o horizonte, sem inferências apenas do rótulo SEM_EXECUCAO.

## Continuidade combinada para 06/11

Usuário deixará notebook/MT5 ativos para acompanhamento contínuo da v2.13.05 na XP DEMO, mantendo mesma conta/servidor/Instância e diário. Conferir relógio, arquivamento de 05/11, dados de 06/11, abertura real, ordens/posições e corte. Não provocar interrupções sem necessidade. Em paralelo, avançar no histórico Work: inventário de cobertura por data/contrato/ajustes/OHLC/ticks e preparação de lote pequeno; não tratar referência auditada como backtest EA executado.
