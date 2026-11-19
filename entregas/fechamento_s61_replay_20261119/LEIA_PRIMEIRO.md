# Fechamento S61 — Replay recebido em 19/11/2026

Recebido `Datas.xlsx` no lançamento `dados-replay-2025-20261116`, asset 768928838. O bruto permanece no lançamento e em `/workspace/dados_brutos_modelo_d/replay_profit/Datas.xlsx`; URL, tamanho e SHA-256 constam no manifesto. Não foi regravado nem filtrado.

29 abas = 29 minutos em 28 datas. Todos conferem exatamente OHLC e soma das quantidades com M1. Os contratos são os esperados pelas referências: a planilha não contém uma coluna de ativo; a correspondência de preços e quantidade foi conferida, sem alegar identificação independente do código.

A cópia do Profit está em ordem decrescente. Para a análise foi invertida integralmente, mantendo negócios idênticos, quantidades e milissegundos. Conferida invariância ao inverter os negócios empatados no mesmo milissegundo. Grupos com barreiras opostas ou entrada/alvo cuja ordem possa mudar o resultado não são certificados.

## Resultados fechados, pontos brutos

| Opção | 2024 | 2025 | 2026 jan–out | Total | DD diário contínuo |
|---|---:|---:|---:|---:|---:|
| S61 stop 100, alvo original | -210 | +2.260 | +245 | +2.295 | 1.370 |
| S61_48 / S61_68 | +240 | +3.395 | +325 | +3.960 | 2.670 |
| S61_60 | +1.175 | +2.710 | +960 | +4.845 | 3.845 |

Todas usam as mesmas 233 entradas S61,8% originais, sem reentrada. O alvo é a distância original até S50%; stop 100 fixo no S61_42; 0,5x o alvo no S61_48/68; 1,5x no S61_60 sem teto. A equivalência 48/68 foi conferida nas 233 operações.

Resolvidas 61 operações entre três estratégias distintas: 20 do stop 100 (19 SL, 1 TP), 27 do 48/68 (25 SL, 2 TP) e 14 do 60 (13 SL, 1 TP). Isso não significa 61 operações independentes: estratégias compartilham datas e entradas.

O ranking por total/DD contínuo permanece: stop 100, 48/68, 60. O maior total isolado é do 60; o stop 100 tem o menor DD, mas 2024 negativo. Nenhuma variante foi promovida ao resultado principal. O confronto com as duas opções anteriores está no CSV `RANKING_ATUALIZADO_5.csv`.

## Método e verificação

DD principal por fechamentos diários em ordem cronológica, pico inicial zero, sem reinício mensal ou anual. DD mensal e anual constam separadamente nas tabelas; não são somados para formar o DD contínuo. Os 709 pregões do período são conservados, inclusive dias sem entrada S61.

M1 MT5 nas fontes iniciais, Profit nos meses correspondentes e M1 auditado Cedro em agosto–outubro/2026; Replay pontual somente nos minutos validados. Não é auditoria integral tick a tick. A sequência pode demonstrar que a operação permaneceu aberta após a janela; saídas posteriores seguem M1/Replay disponível. Não se considera máxima anterior à entrada como alvo posterior.

O verificador independente reproduz as 61 operações em 244 execuções (duas trajetórias OHLC fora do Replay e duas ordens dos empates no Replay), confrontando os resultados do motor preservado, e recalcula totais/DD por somas escalares. Horários de saída M1 têm precisão apenas de minuto; preços associados às trajetórias M1 não representam negócios individuais identificados. Conferida compatibilidade com todos os 28 resultados originais afetados, sem alterá-los.

Resultados brutos, execução teórica nos níveis da grade de 5 pontos, sem custos ou slippage. Os estudos, rankings e resultados originais anteriores permanecem intactos. **50/250 em stand-by por decisão expressa do usuário: nenhuma nova apuração desse teste nesta entrega.**

PDF de resumo, Excel anual/mensal/diário/operações e CSVs completos nesta pasta. Scripts dependem dos caches locais preservados dos estudos de origem; não representam um pacote autônomo sem essas fontes.
