# A/B XP concluído — 05/11/2026

Mesmo DiagTicksAB1.21, servidor XPMT5-DEMO, build6295, WINZ26 nativo,
M5, janela histórica30/10/2026 09:00:00 inclusivo a09:10:00 exclusivo.
ParteA no terminal e parteB no Tester configurado com ticks reais.
Ambas estabilizaram em duas leituras completas, sem erro de consulta.

| Medida | TerminalA | TesterB |
|---|---:|---:|
| ALL |108005|36571|
| TRADE / negócios com Last válido |105342|0|
| Last positivo no ALL |108004|0|
| Volume positivo no ALL |108004|0|

Os CSVs foram lidos integralmente: contagens conferem com os relatórios.
No B, todos36571registros têm flags6 e Last/volume zero. Não houve negócio
ocultado pelo classificador do Modelo D nesse fluxo entregue pelo Tester.
O diagnóstico não usa as bibliotecas do Modelo D nem envia ordens.

## Evidência decisiva no Diário

`all the real ticks discarded within a day`

`real ticks discarded for 565 minutes of 565 total minute bars, every tick generation used`

O MT5 também informa preços incompatíveis em2299875ticks e divergência
de volumes nas565barrasM1. Embora a opção fosse ticks reais, o Tester
substituiu o fluxo após descartar os dados reais por inconsistência.

## Conclusão e limite

Está demonstrado o mecanismo imediato da ausência de negócios no ensaio
nativo: descarte de ticks reais e geração substituta que só entregou Bid/Ask.
Isso explica o bloqueio de abertura da v2.11 na XP nesse dia. Não é evidência
de30minutos de leilão, limitação de linhas do Diário nem motivo para trocar
Last por Ask. A origem da incompatibilidade entre os dados reais e as barras
M1 ainda não foi isolada; não prova cache corrompido, culpa da corretora ou
bug específico do MT5. Não apagar caches nem flexibilizar o modelo por isso.

A/B Genial ainda pendente, no próprio terminal/servidor da Genial, somente
com o diagnóstico sem ordens. Não concluir a partir da XP sobre execução
real ou DMA. Comparativo com o histórico Work também permanece pendente.

Os relatórios e o Diário completos acompanham este resultado; os CSVs
originais enviados pelo usuário são identificados por nome/tamanho/SHA256,
sem duplicar os arquivos grandes no repositório. O agregado por minuto está
em COMPARACAO_POR_MINUTO.csv.
