# Recuperação observada em 06/11/2026

Horários abaixo conforme os arquivos do terminal.

## Evidência do mesmo minuto 14:41

| Leitura | Negócios | O | H | L | C |
|---|---:|---:|---:|---:|---:|
| EA até 15:18:09.894 | 2106 | 170495 | 170520 | 170440 | 170520 |
| EA às 15:20:11.883 | 2226 | 170495 | 170520 | 170435 | 170520 |
| CSV enviado, minuto 14:41 | 2226 | 170495 | 170520 | 170435 | 170520 |
| M1 registrado antes e depois | — | 170495 | 170520 | 170435 | 170520 |

O CSV inteiro contém 31044 eventos, de 14:35:00.002 até 14:44:59.994. O minuto 14:41 contém 2412 eventos ALL, dos quais 2226 com Last positivo e flags de negócio (máscara LAST|VOLUME|BUY|SELL = 120). Exemplos da mínima 170435 às 14:41:35.197 e 14:41:35.198.

A consulta do EA passou a retornar mais 120 negócios, mudou a assinatura de 1284667619 para 1560499306 e passou a conferir com M1. Às 15:20:11.883 ocorreu TICKS_6_15_RECUPERADO, seguido de atualização dos blocos posteriores. Às 15:20:19.891 a cobertura atual foi CONFERIDA. O log enviado alcança 15:22:07.879.

Isso comprova uma mudança nos dados retornados para uma janela passada. Não identifica se a origem foi sincronização local, cache ou servidor. Não demonstra causalidade com a ausência de execução da R38,2 às 10:30. Nenhuma alteração de código, tolerância ou regra foi feita nesta análise.

## Horários e cobertura atual

No print XP: Observação do Mercado 15:24:46 versus PC 15:25:11, diferença exibida de 25 segundos. No print Genial: 15:25:25 versus PC 15:25:26, diferença exibida de 1 segundo. Os prints não são simultâneos. O horário da Observação do Mercado depende das cotações recebidas e não basta para medir o relógio interno utilizado pelo EA, nem para concluir atraso fixo da conexão.

A tela XP mostra cobertura CONFERIDA às 15:24:21.874 e JANELA_ATUAL_INVALIDA_OU_DEFASADA às 15:25:01.891. Portanto a recuperação histórica foi confirmada, mas a atualização da janela atual ainda apresenta intermitência. A frase CONFERIDOS ATE 15:24:00 é exclusiva e não certifica todos os segundos até 15:25:11 do PC.

## Limitação

O ZIP da gravação excede o limite de transferência de 32 MiB da ferramenta; o vídeo não foi aberto nem analisado. Conclusões baseadas nos CSV, log e prints fornecidos.
