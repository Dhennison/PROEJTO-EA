# Replay independente do Modelo D — setembro até 21/09/2026

## Resultado

Os candles originais chegaram no ZIP `Candles_Originais_Modelo_D_2023_2026.zip`, preservado em `originais/`. Os hashes dos cinco CSVs conferem com os hashes declarados no guia do pacote. A leitura dos cinco arquivos validou as datas reais, números, OHLC e ausência de timestamps duplicados dentro de cada arquivo.

| Fonte | Símbolo | Tempo gráfico | Registros | Primeiro registro | Último registro |
|---|---|---|---:|---|---|
| 2023 | WIN$N / MT5 | M5 | 22680 | 27/02/2023 15:10 | 28/12/2023 18:20 |
| 2024 | WINFUT / Profit | M5 | 27892 | 05/01/2024 15:55 | 30/12/2024 18:20 |
| 2025 | WINFUT / Profit | M5 | 28176 | 02/01/2025 09:00 | 30/12/2025 18:20 |
| Jan–fev/2026 | WINFUT / Profit | M5 | 4359 | 02/01/2026 09:00 | 27/02/2026 18:20 |
| Mar–set/2026 | WINFUT / Profit | M1 | 79437 | 27/02/2026 14:55 | 21/09/2026 18:24 |

Existem candles e a barra programada do corte para **todas as 877 datas elegíveis** nas fontes selecionadas. Isso confirma a presença dos dados por data, não certifica por si só o contexto anterior, a continuidade integral ou o replay dos demais pregões. Em particular, o começo parcial do M1 em 27/02 não deve substituir o M5 completo de fevereiro quando for expandido o contexto de março. Os períodos sobrepostos M1/M5 não foram concatenados.

## Contexto e níveis de setembro

- Recorte de operação: **01/09/2026 a 21/09/2026**, 14 pregões elegíveis. Contexto anterior inicial: **31/08/2026**.
- Fonte original agora identificada: **WINFUT, Profit, M1**.
- Abertura: OPEN da primeira barra original a partir das 09h; em setembro ela aparece às 09:02 ou 09:03. Não foi exigida barra exatamente às 09h e não foram criadas barras anteriores. A ausência dessas barras não é prova, por ticks, do horário do primeiro negócio.
- Nenhuma lacuna interna entre a primeira barra observada e a última barra das sessões usadas; última barra às 18:24 e barra do corte às 18:00 presente em todos os 14 dias. Os horários foram preservados como exportados; não foi aplicada conversão de fuso.
- H/L/C do pregão anterior foram agregados a partir do M1 original, incluindo todas as barras até o fim da fonte, sem usar o corte das operações para truncar o contexto diário.
- Ajuste do CSV por **data operacional**, sem deslocamento de data.
- Abertura, H/L/C anterior, ajuste e os cinco níveis nos 14 pregões conferiram com o contexto anteriormente agregado em M15. Foram preservados os 70 registros por nível, inclusive o dia sem operação e os níveis sem toque.

As tabelas estão em `resultados/CONTEXTO_M1_E_CINCO_NIVEIS.csv`, `resultados/CONTEXTO_M1_VERSUS_M15.csv` e `resultados/ESTADO_70_NIVEIS.csv`.

## Operações: nova rotina versus Work

A nova rotina recebe candles, ajustes e o calendário/universo elegível; não recebe os preços nem os desfechos das operações Work para gerar seus trades. A lista Work é lida apenas pelo comparador posterior.

| Métrica do recorte | Work | Replay independente |
|---|---:|---:|
| Pregões | 14 | 14 |
| Operações | 33 | 33 |
| Alvos | 24 | 24 |
| Stops | 9 | 9 |
| Zeragens por horário | 0 | 0 |
| Pontos por contrato | +3839,308998 | +3839,308998 |
| DD diário, saldo inicial zero no recorte | 1087,585333 | 1087,585333 |

**Zero operações ausentes, extras ou divergentes** na comparação por Data/Nível/Lado, abertura, linha, entrada, stop, alvo, horários, saída, motivo, pontos, marcador de ambiguidade e corte. Preços comparados à tolerância numérica de 0,000001 ponto; horários e motivos comparados exatamente. O total dos pontos, após arredondamento original a seis casas por operação, coincide exatamente.

Dia **03/09**: zero operações nas duas rotinas, mantido na curva. Nos 70 estados calculados: 33 operações teóricas, 36 níveis sem toque antes do corte e um invalidado pelo filtro de abertura. Esses são estados do replay por candles, não ordens ou fills de corretora.

Regras aplicadas: entrada teórica exata na primeira vela que alcança a linha, uma operação por nível/dia, níveis independentes, filtro de abertura e geometria antes da entrada, SL/TP originais fixos, teste de saída na vela da entrada, STOP FIRST quando ambos são alcançados na mesma vela, e saída no OPEN do candle do corte sem novas entradas nem teste do H/L desse candle. Não há ambiguidade marcada nas 33 operações deste recorte; o comportamento STOP FIRST foi exercitado também em cenário sintético.

`comparacao_setembro_completo/`: comparação **COMPLETA dentro do recorte de setembro**, com zero divergências.

`comparacao/`: comparação contra o universo de 877 datas; **PARCIAL**, porque apenas 14 datas foram processadas e as outras 863 continuam pendentes, sem serem tratadas como zero operações. O DD acima é do recorte, não o DD de todo o histórico 2023–2026.

## O que ainda falta para o EA

Este resultado é **reprodução teórica por candles**, sem tick de 5 pontos, custos, slippage, fila, execução parcial ou ordens nativas. Não é backtest executado pelo EA no MT5 nem homologação.

O ZIP novo não contém ticks reais nem identificação histórica do vencimento por data. Portanto permanecem pendentes:

1. **Contrato real de 01/09 a 21/09/2026**: WINV26 é o candidato anteriormente identificado em documentos de setembro, ainda sujeito à prova do vínculo diário com a série e com os ajustes B3. Não foi atribuído automaticamente pelo calendário.
2. **OHLC do contrato confirmado**, D1 ou M1 completo, **31/08 a 21/09/2026**, para confrontar com a série WINFUT e validar contexto e rolagem.
3. **Ticks reais do contrato confirmado**, **01/09 a 21/09/2026**, pregões completos, com tempo em ms, Bid/Ask/Last, volumes e flags. Os candles M1 recebidos não os substituem. A cobertura no servidor não foi consultada nesta sessão, que não tem conexão com o terminal do usuário.
4. Adaptador histórico do EA para esse recorte e para a expansão multianual, com cinco contratos por nível no ensaio principal e relatórios de execução separados da referência teórica.

Não é necessário reenviar os candles ou ajustes originais para repetir este recorte teórico. A matemática/replay de setembro está conferida. A cobertura dos demais pregões está inventariada; o próximo avanço do histórico é ampliar o replay e conferir as transições de fontes e o calendário histórico, mantendo os parâmetros congelados.

## Validação e reprodução

Sete testes sintéticos passaram: STOP FIRST na vela de entrada, prioridade do OPEN no corte, ausência de nova entrada no corte, rejeição de corte ausente, igualdade e abertura após 09h, alvos intermediários/stop S61,8 e importação Profit em ordem decrescente com milhares e duplicatas. Os cinco CSVs originais foram lidos sem OHLC inválido ou timestamps duplicados. A conferência dos 14 contextos M1/M15 e das 33 operações Work foi realizada com os dados reais do pacote.

Na pasta desta entrega (Python 3; o replay usa apenas a biblioteca padrão):

```sh
python replay.py originais/Candles_Originais_Modelo_D_2023_2026.zip .. --saida resultados
python -m unittest -v test_replay
python ../preparacao_20261106/comparar_teorico.py --referencia resultados/REFERENCIA_OPERACOES_SETEMBRO.csv --operacoes resultados/OPERACOES_REPLAY_D.csv --diario resultados/REFERENCIA_DIARIA_SETEMBRO.csv --cobertura resultados/COBERTURA_REPLAY.csv --saida comparacao_setembro_completo
```

Os arquivos de referência de setembro são recortes das listas canônicas originais, sem recalcular preços ou pontos. Os originais recebidos e as saídas possuem hashes no manifesto. Nenhum código ou diário da v2.13.05 DEMO foi alterado.
