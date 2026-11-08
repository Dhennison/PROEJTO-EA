# Genial A/B — descarte de ticks reais confirmado em 08/11/2026

Controle WINZ26/M5, 30/10/2026, janela [09:00,09:10), DiagTicksAB v1.21, servidor GenialInvestimentos-PRD, build 6231. Compilação na Genial informada pelo usuário: zero erros/avisos, 660 ms. Fonte idêntico ao controle da XP.

## Evidência recebida

- Parte A: log fornecido diretamente na conversa; relatórios TXT/CSV originais ainda não anexados.
- Parte B: Diário completo do Tester recebido e preservado como `DIARIO_TESTER_B.txt`, incluindo parâmetros, mensagens de descarte, resumo do diagnóstico e gravação dos arquivos.

| Medida reportada | A: terminal Genial | B: Tester Genial |
|---|---:|---:|
| Ticks ALL | 236855 | 36571 |
| Ticks de negócio válidos / TRADE | 142865 | 0 |
| INFO | 93990 | 36571 |
| Last positivo | 236855 no ALL | 0 |
| Estabilidade | Duas leituras iguais | Duas leituras iguais |

Na parte A, Last preenchido em ticks INFO é valor carregado, não prova de novo negócio; o diagnóstico contou negócios apenas pelos flags e Last válido. Na parte B, todos os 36571 ticks têm flags=6 (Bid/Ask), Last=0 e volume=0.

## O Diário comprova o mecanismo

```text
all the real ticks discarded within a day
4319114 tick prices mismatch for 565 minute bars
real ticks discarded for 565 minutes of 565 total minute bars, every tick generation used
real ticks discarded for 1 whole days
tick volumes not matched for 565 minute bars
```

Embora a modelagem estivesse configurada como “Cada tick baseado em um tick real”, o Tester **descartou os ticks reais do dia e usou geração substituta**. O fluxo efetivamente entregue na janela não tem negócios utilizáveis pelo critério do Modelo D. Esse ensaio não serve como backtest fiel de uma estratégia que exige Last/flags de negócio.

O padrão é o mesmo observado na XP. Inclusive o hash completo reportado do ALL no B, **12192812819959984030**, coincide com o B da XP, assim como n=36571 e flags=6. Isso não substitui comparar os CSVs completos nem prova igualdade de todos os dados de origem. O A da Genial possui contagens diferentes do A da XP, e os builds das instalações são diferentes (6231 na Genial; 6295 no controle XP). A comparação interna A/B da Genial foi feita no mesmo build.

A mensagem final “38029 ticks, 3 bars generated” descreve eventos processados pelo motor até o diagnóstico se remover; não é a contagem da consulta exata [09:00,09:10), que é 36571. A remoção do próprio diagnóstico é prevista pelo programa. O saldo virtual inalterado não é resultado operacional do Modelo D: nenhuma ordem foi enviada.

## Limites

Está confirmado o **descarte e a substituição na amostra**, não a causa inicial da incompatibilidade. Não atribuir a cache corrompido, modo de execução DMA, VPS ou erro da estratégia. Tamanhos pequenos de sincronização, como “43 bytes”, não demonstram corrupção por si sós.

Não extrapolar esse resultado automaticamente a todos os pregões ou aos dois minutos de WINV26/setembro. As inconsistências terminais nesses minutos foram documentadas separadamente. Uma repetição correspondente no Tester seria outro experimento.

Não fabricar Last nem trocar por Ask para forçar abertura da estratégia. Antes de ampliar o backtest principal com um contrato ao período inteiro, é necessário controlar/validar a alimentação do Tester. Importar ticks reais em símbolo personalizado permanece uma alternativa a validar, preservando as limitações da fita e sem inventar eventos que faltam em relação às barras do Work.

## Próxima coleta necessária

Receber os quatro arquivos de Common/Files, sem repetir o teste:

```text
DiagTicksAB_TERMINAL_GenialInvestimentos-PRD_WINZ26_2026_10_30_09_00_2026_10_30_09_10_GENIAL_A_757381906.txt
DiagTicksAB_TERMINAL_GenialInvestimentos-PRD_WINZ26_2026_10_30_09_00_2026_10_30_09_10_GENIAL_A_757381906_ALL.csv
DiagTicksAB_TESTER_GenialInvestimentos-PRD_WINZ26_2026_10_30_09_00_2026_10_30_09_10_GENIAL_B_757688312.txt
DiagTicksAB_TESTER_GenialInvestimentos-PRD_WINZ26_2026_10_30_09_00_2026_10_30_09_10_GENIAL_B_757688312_ALL.csv
```

Esses arquivos permitirão conferir contagens, campos, estabilidade reportada e o fluxo bruto. Não foram produzidos neste registro resultados fictícios de CSV que ainda não foi recebido. Nenhum código do diagnóstico, EA, cache ou configuração foi alterado nesta análise.
