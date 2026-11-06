# Modelo D: reprodução integral do Work e política de ambiguidades no MT5

Conferência realizada em 06/11/2026. Universo: **01/03/2023 a 21/09/2026**. Candles originais recebidos, ajustes associados pela data operacional, parâmetros congelados. Nenhum código, configuração ou diário da DEMO foi alterado.

## Resultado integral

| Período | Operações Work | Operações replay | Pontos Work | Pontos replay |
|---|---:|---:|---:|---:|
| 2023 | 469 | 469 | 36753,370672 | 36753,370672 |
| 2024 | 514 | 514 | 21544,596984 | 21544,596984 |
| 2025 | 510 | 510 | 38280,446339 | 38280,446339 |
| 2026 até 21/09 | 384 | 384 | 27759,344666 | 27759,344666 |
| Total | **1877** | **1877** | **124337,758661** | **124337,758661** |

- **877 pregões**, incluindo **112 sem operações**, com contexto anterior e cinco níveis por pregão: 4385 registros.
- **Zero operações ausentes, extras ou divergentes**: conferidos Data/Nível/Lado, abertura, linha, entrada, SL, TP, horários, preço de saída, motivo, pontos, ambiguidade e corte.
- Pontos conferidos **exatamente em cada uma das 1877 operações**, sem tolerância nessa verificação adicional; contagem e pontos também coincidem exatamente em cada dia.
- Soma, curva diária, pico e drawdown coincidem exatamente com a referência. **DD diário máximo: 4780,240329 pontos**, saldo inicial zero, confirmado por cálculo adicional usando todos os prefixos anteriores da curva.
- Desfechos: **1525 alvos, 319 stops, 7 zeragens às 17:45 e 26 zeragens às 18h**.
- Estados dos níveis: 1877 operações teóricas, 2360 sem toque antes do corte, 74 invalidados pela abertura e 74 bloqueados pela geometria. Esses estados são da reprodução por candles, não ordens ou fills nativos.

Este resultado é a nova reprodução independente do Work. O gerador recebe candles, ajustes e calendário/universo elegível, sem consultar as entradas ou os resultados das operações de referência. A lista original é usada somente depois, para comparação. Preços teóricos calculados com Decimal; pontos arredondados a seis casas por operação. Não há custos, slippage, normalização ao tick, fila ou contratos executados nessa camada.

## Transições e calendário conferidos

- 2023: WIN$N/MT5 M5; 2024/2025: WINFUT/Profit M5; janeiro/fevereiro de 2026: WINFUT M5; março a 21/09 de 2026: WINFUT M1. Arquivos sobrepostos não foram concatenados.
- **02/01/2026** usa H/L/C de **30/12/2025**, extraído do arquivo M5 de 2025.
- **02/03/2026** usa H/L/C de **27/02/2026**, extraído do M5 completo de janeiro/fevereiro. O M1 de 27/02 começa às 14:55 e não foi usado como se fornecesse o contexto completo desse dia.
- Corte **17:45 de 13/03 a 03/11/2023 inclusive**, e **18:00 nas demais datas**. Limites de vigência conferidos em 10/03, 13/03, 03/11 e 06/11/2023.
- Abertura pela primeira barra original a partir das 09h, preservando também sessões cujo primeiro registro é posterior. A cronologia dos arquivos foi ordenada, sem criar barras anteriores ou imputar preços.
- Último fechamento do contexto anterior calculado com todas as barras da fonte desse pregão, sem truncar o contexto no horário de zeragem da estratégia.

## Ambiguidades: duas camadas de resultado

A reprodução confirmou as **32 operações ambíguas em 26 pregões**, com as mesmas chaves do Work: uma em 2023, sete em 2024, doze em 2025 e doze em 2026. São 27 operações em M5 e cinco em M1. O Work e esta reprodução preservam **STOP FIRST** nesses casos para manter a referência original intacta.

**No futuro teste do EA com ticks reais, vale a cronologia observada.** Se o alvo ocorrer antes, o resultado cronológico será alvo; se o stop ocorrer antes, será stop. Não será imposto STOP FIRST para igualar o Work. O resultado da referência continua preservado em uma coluna separada e a diferença terá motivo explícito.

Há duas verificações distintas: primeiro preço teórico atingido na sequência dos ticks e saída efetivamente executada pela ordem no MT5. Um toque não garante fill, como observado na DEMO. Por isso a comparação conservará entrada aceita, execução, preços normalizados, SL/TP e comprovantes nativos, sem converter uma saída teórica em execução presumida.

Se não houver ticks reais suficientes, ou se a ordem dos registros não permitir separar os eventos, o estado será **indeterminado/pendente**, sem escolher gain ou stop arbitrariamente. Marcar a modelagem como “ticks reais” na interface não basta: o A/B anterior demonstrou substituição por ticks gerados. Antes de usar a cronologia para resolver ambiguidades, será necessário confirmar a fonte, a cobertura, os Last/flags e os avisos de descarte do Tester. Não serão fabricados Last a partir de OHLC.

`resultados/FILA_32_AMBIGUIDADES_PARA_MT5.csv` já contém data, nível, entrada, SL, TP, símbolo de referência, tempo gráfico original e a janela da vela ambígua. As colunas de contrato confirmado, primeiro evento por ticks e saída nativa estão vazias/pendentes. Os recortes sugeridos servem para diagnóstico; executar o EA requer a sessão completa, o contexto diário e a associação correta dos ajustes ao contrato real.

Exemplo inicial da fila: **06/10/2023, S38,2**, vela **09:30–09:35**, referência WIN$N/M5, resultado Work STOP. O contrato real e a sequência de ticks desse caso ainda não foram fornecidos.

## Intervalos sem barras na fonte original

Foram detectados três intervalos únicos em três sessões; o CSV tem seis linhas porque cada intervalo também aparece quando o pregão seguinte o usa como contexto anterior:

| Sessão da fonte | Última barra antes do intervalo | Primeira barra depois | Passo esperado | Contexto do pregão seguinte |
|---|---|---|---|---|
| 03/06/2025, WINFUT M5 | 09:00 | 09:55 | 5 min | 04/06/2025 |
| 21/08/2025, WINFUT M5 | 09:15 | 10:25 | 5 min | 22/08/2025 |
| 10/07/2026, WINFUT M1 | 09:55 | 09:57 | 1 min | 13/07/2026 |

Não há prova aqui para distinguir ausência de negócios, leilão/interrupção ou falta na exportação. Nenhuma barra foi preenchida e nenhum desses pregões foi retirado do Work. **Reproduzir o Work não certifica a integridade integral do mercado histórico.** Ao conferir os ticks/contrato real, essas sessões e seus contextos terão uma verificação específica. Se surgirem dados adicionais, manteremos a referência original e registraremos separadamente o efeito da diferença de cobertura.

## Estado do projeto após esta etapa

1. **Referência e reprodução teórica integral do Work: concluídas**, com zero divergências nos 877 pregões.
2. **Comparação do EA executado no MT5 com o Work: pendente.** Não foi executado um backtest nativo nesta etapa.
3. **Contrato real e ticks de setembro: pendentes.** WINV26 permanece candidato, sem identificação histórica certificada de cada data. Para o primeiro ensaio: contexto D1 ou M1 completo do contrato confirmado de 31/08 a 21/09/2026; ticks reais das sessões de 01 a 21/09/2026; vínculo data/contrato/ajuste B3 conferido. O WINFUT dos candles não fornece esse vínculo sozinho.
4. **Adaptação do ensaio histórico do EA:** ainda necessária para remover as amarras ao dia/contrato fixos da v2.11 de outubro e aplicar calendário, dados, normalização e relatórios com cinco contratos por nível. A v2.13.05 DEMO segue separada.
5. **Ambiguidades:** fila das 32 pronta; resolução por ticks e comparação nativa continuam pendentes de dados e cobertura. Setembro não contém operação marcada como ambígua, portanto o primeiro piloto de setembro não exercitará esse cenário.

Não é necessário reenviar candles e ajustes de referência para ampliar a comparação teórica: essa ampliação já foi concluída. Para avançar à execução nativa, precisamos conferir os dados do contrato real e a disponibilidade dos ticks no terminal.

## Arquivos e reprodução

- `resultados/CONTEXTO_E_4385_NIVEIS.csv`: abertura, H/L/C anterior, ajuste, cinco níveis, calendário e arquivo de cada lado da transição por pregão.
- `resultados/OPERACOES_REPLAY_D.csv`: as 1877 operações geradas pela nova rotina.
- `resultados/ESTADOS_4385_NIVEIS.csv`: estado de cada nível por data.
- `comparacao/`: resultados por operação, dia, mês, ano, total e resumo completo.
- `resultados/VALIDACAO_EXATA_E_DD_INDEPENDENTE.json`: 13 conferências adicionais aprovadas, incluindo pontos exatos e cálculo independente do DD.
- `resultados/LACUNAS_INTERNAS_OBSERVADAS.csv`: intervalos preservados, sem imputação.
- `resultados/FILA_32_AMBIGUIDADES_PARA_MT5.csv`: fila de investigação cronológica futura.

Três testes sintéticos novos de transição de fontes e limites do calendário passaram. O motor de candles é o mesmo validado na etapa de setembro, com sete testes de regras e importação. Nenhuma alteração foi necessária nesse motor para reproduzir os demais anos; a nova camada seleciona a fonte/contexto e o corte corretos por data.

Na pasta desta entrega, com Python 3 e a estrutura do repositório:

```sh
python replay_completo.py ../replay_setembro_20261106/originais/Candles_Originais_Modelo_D_2023_2026.zip .. --saida resultados
python ../preparacao_20261106/comparar_teorico.py --referencia ../Operacoes_Modelo_D_20230301_20260921_ORIGINAL.csv --operacoes resultados/OPERACOES_REPLAY_D.csv --diario ../Referencia_D_diário.csv --cobertura resultados/COBERTURA_REPLAY.csv --saida comparacao
python validar_e_preparar.py .. resultados
python -m unittest -v test_transicoes
```

Preços teóricos comparados com tolerância numérica de 0,000001 ponto para representação dos valores exportados; horários e motivos exatos. A verificação adicional de pontos por operação, dia, total e curva foi exata. Fontes originais preservadas e hashes registrados.
