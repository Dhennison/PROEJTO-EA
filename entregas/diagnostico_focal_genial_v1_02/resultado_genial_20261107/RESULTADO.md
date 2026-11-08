# Genial — resultado da consulta focal de ticks e M1

Coleta nativa em **07/11/2026, 22:21:11–22:21:18**, servidor **GenialInvestimentos-PRD**, símbolo **WINV26**, ambiente **TERMINAL**, símbolo customizado=0, construção de barras por Last (modo=1).

Compilação v1.02 informada pelo usuário: **zero erros, zero avisos, 1702 ms**. Duas leituras válidas consecutivas e iguais por janela; chamadas ALL/TRADE/M1 sem erros no retorno registrado. O ZIP recebido foi preservado integralmente em `originais/`.

## Diferenças localizadas e recalculadas pelos ticks brutos

| Data e minuto do servidor | Campo | Ticks ALL filtrados e TRADE | M1 Genial | M1 original Work | Ticks − M1 |
|---|---|---:|---:|---:|---:|
| 01/09/2026 18:24 | Máxima | **182355** | **182390** | **182390** | −35 |
| 01/09/2026 18:24 | Fechamento | **182330** | **182390** | **182390** | −60 |
| 02/09/2026 16:13 | Máxima | **187930** | **187945** | **187945** | −15 |

Os demais campos desses dois minutos coincidem: em 01/09, O=182355 e L=182260; em 02/09, O=187855, L=187820, C=187865.

Das **10 barras M1** examinadas, **oito conferem integralmente com os negócios recuperados** e duas apresentam as diferenças acima. **As 10 barras M1 da Genial coincidem em OHLC com o arquivo M1 original do Work**, inclusive as duas divergentes dos ticks. Quantidade do Work também coincide com real_volume das 10 barras M1.

O analisador recalculou OHLC dos CSVs brutos em Decimal, sem usar os deltas produzidos pelo MQL. A ordem de registros com o mesmo milissegundo foi preservada. Os resultados são compatíveis com os CSVs MINUTOS gravados pelo programa. Os preços por minuto nas leituras 1 e 2 também permaneceram iguais; o marcador inicial NAO_ESTAVEL corresponde à ausência de uma leitura anterior para comparar, não a um erro de preço inicial.

## O filtro de negócio não explica os preços ausentes nestas amostras

| Janela | ALL completo | ALL com flags de negócio | TRADE |
|---|---:|---:|---:|
| 01/09, 18:20–18:25 | 2955 | 1907 | 1907 |
| 02/09, 16:10–16:15 | 17348 | 14210 | 14210 |

O ALL filtrado por `flags & 120` e o canal TRADE são **iguais registro a registro em todos os oito campos exportados**, desconsiderando apenas o índice da posição no respectivo array. Bits adicionais de flags foram preservados, sem removê-los ou recodificá-los.

Também foram examinados os registros ALL sem filtrar flags:

- No minuto 18:24 de 01/09, **182390 não aparece em Last, Bid ou Ask**. O Last bruto chega apenas a 182355; o último negócio filtrado é 182330, e o último registro ALL é de 18:24:59.780.
- No minuto 16:13 de 02/09, **187945 não aparece em Last, Bid ou Ask**. O Last bruto chega apenas a 187930; o último registro ALL é de 16:13:59.998.

Portanto, nessas duas amostras a diferença não é produzida apenas pela seleção de flags feita pelo EA ou pelo diagnóstico: os preços necessários não estão nem no Last bruto retornado para os minutos. Trocar COPY_TICKS_TRADE por ALL e remover o filtro não recuperaria esses valores nesses snapshots.

As contagens de ALL e TRADE das duas janelas coincidem com o lote v1.00 coletado no dia anterior. Isso confirma a repetição das contagens e da classificação pendente da janela, mas o primeiro lote não armazenou os OHLC divergentes nem uma fita completa desses blocos; não cabe afirmar igualdade integral entre os ticks de 06 e 07/11 somente pela contagem.

## O que está comprovado

**Há inconsistência reproduzida entre as barras M1 e os ticks recuperados do terminal para o mesmo símbolo/minuto.** O coletor detectou uma diferença de dados observável, confirmada pelo recálculo independente. As barras M1 da Genial estão compatíveis com o Work nesses dez minutos; a fita recuperada não reproduz dois deles.

As somas de volume dos registros classificados como negócio também diferem do real_volume das barras nos dois minutos: 2275 versus 22171 em 01/09; 25506 versus 37688 em 02/09. É evidência adicional de diferença entre representações; sem identificadores únicos de negócio e sem confirmar a semântica de cada registro, não classificar a subtração como quantidade exata de contratos ausentes.

## O que ainda não está comprovado

- Não foi determinado se a origem é a captura/entrega do histórico pelo servidor, cache/sincronização local, um evento com timestamp fora da janela ou uma convenção de construção/correção das barras.
- Não foram consultados ticks além das janelas; uma hipótese de negócio de borda ou fechamento em 18:25 continua sem teste. Não chamar automaticamente o caso final de leilão ou preço oficial de encerramento.
- Concordância entre Work e M1 não equivale a uma fita independente da bolsa. Não é possível provar por esses arquivos qual representação contém todos os eventos reais.
- Essa coleta ocorreu no **terminal**, não no Strategy Tester. Não demonstra ainda como o Tester da Genial trata essas inconsistências, nem que ele descartou ticks como no A/B da XP.
- Não resolve por si só a identificação histórica da série/contrato em todo o intervalo ou o vínculo com boletins B3.

TimeCurrent em 06/11 18:24 e TimeTradeServer em 07/11 22:21 são os horários registrados em uma consulta histórica no fim de semana. A coleta não exigiu cotações novas. Os pedidos históricos foram feitos explicitamente para setembro; não se confundem com a data da última cotação atual.

## Encaminhamento

1. Preservar o critério de negócio, os parâmetros do Modelo D e a referência original Work. Não fabricar ticks/Last, trocar por Ask ou flexibilizar o teste de OHLC para esconder a diferença.
2. O próximo passo para avaliar a viabilidade do backtest é observar a **entrega efetiva de dados no Tester da Genial**. O A/B já pendente com a configuração da XP (WINZ26, 30/10/2026 09:00–09:10) continua sendo um controle separado. Para testar o efeito destas diferenças específicas de setembro será necessário reproduzir também estas janelas com WINV26 no Tester, sem confundir os dois experimentos.
3. Se for investigar a origem da divergência no terminal, a consulta seguinte deve cobrir as bordas dos minutos e a região de fechamento posterior a 18:25, ou uma fita independente do mesmo contrato, mantendo todos os registros e os horários. Esses dados não foram coletados nesta etapa.
4. Um símbolo personalizado com os ticks reais recuperados pode permitir controlar a alimentação do Tester, mas não recria preços que faltam na fita em relação ao Work. Barras reconstruídas desses ticks precisam de comparação e rastreabilidade próprias; não podem ser declaradas idênticas ao Work sem conferência.

Nenhuma mudança no EA operacional foi realizada. A reprodução matemática/teórica integral do Work permanece concluída; a execução histórica nativa e a resolução cronológica das ambiguidades continuam pendentes de dados e ensaio.

## Reprodução e arquivos

```sh
python conferir_evidencias.py
```

O script usa o ZIP nativo preservado e o ZIP dos candles originais já versionado no repositório, executa `analisar_focal.py`, compara os canais ALL/TRADE, as duas releituras e as 10 barras com o Work. Falha se contagens, índices, OHLC, timestamps ou as identidades esperadas não conferirem.

- `analise/OHLC_RECALCULADO.csv`: OHLC e deltas por minuto recalculados pelos ticks brutos.
- `analise/CONFRONTO_10_BARRAS_COM_WORK.csv`: confronto das barras M1 nativas com o Work.
- `analise/CONFERENCIA_ADICIONAL.json`: comprovações, preços, contagens e limites.
- `analise/RESUMO.json`: metadados e classificação dos snapshots recebidos.
- `SHA256SUMS.json`: hashes do ZIP, scripts e resultados preservados.
