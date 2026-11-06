# Preparação do comparativo histórico — Modelo D

Inventário executado em 06/11/2026. A v2.13.05 DEMO continua separada deste trabalho.

## Resultado concreto

- 877 pregões elegíveis inventariados, incluindo 112 sem operações; 1877 operações canônicas preservadas.
- 877 ajustes disponíveis, com fonte e linha já identificadas no pacote original. Zero contratos reais identificados nos campos recebidos; não foram preenchidos por inferência.
- Espaçamento dos registros OHLC nas fontes de ajuste: 3600 segundos em 2023/2024; predominantemente 900 segundos em 2025/2026. Isso não equivale à base M5/M1 do Work.
- Piloto: semana completa 14–18/09/2026, escolhida por ser recente e pertencer à amostra M1. Cinco pregões, 14 operações Work, +2424,152333 pontos por contrato de referência. Esse número é o total do Work, não resultado de uma nova simulação.
- Volume planejado no futuro ensaio do EA: cinco contratos por nível. Comparar pontos por contrato sem multiplicar o total Work por cinco; volumes, pontos ponderados e custos terão colunas próprias na camada executada.
- Calendário de comparação preservado: 17:45 de 13/03 a 03/11/2023 inclusive; 18:00 nas demais datas. Não é uma certificação de sessões reais/especiais nem altera o corte da DEMO.

## Próximo insumo necessário

Enviar os candles M1 originais da MESMA série e fonte utilizada no Work, de **11/09/2026 a 18/09/2026**, com pregões completos, incluindo o fechamento. O dia 11 fornece o contexto anterior ao primeiro pregão do piloto, dia 14. Precisamos de Data/Hora, Abertura, Máxima, Mínima e Fechamento, identificando símbolo, plataforma/fonte e fuso. Não enviar somente a lista de operações ou as planilhas de ajuste: essas já foram recebidas.

Preservar o CSV bruto exportado e o cabeçalho; não arredondar nem fabricar barras ausentes. Se o arquivo original do Work já contiver esse período em M1, enviar esse arquivo é preferível a uma nova exportação de outra série. Exportação do Profit pode servir para comparação adicional, mas só substitui a base original depois de demonstrar equivalência.

Com esses candles, o próximo passo é implementar e conferir o replay teórico independente do piloto: OHLC anterior e abertura observados, níveis matemáticos, filtros e geometria, primeira entrada por nível, STOP FIRST em ambiguidade e saída no OPEN do candle do corte. Essa rotina ainda NÃO foi executada nem implementada neste pacote.

Em seguida, a camada de execução exige vínculo confirmado data/contrato/ajuste e ticks reais desse contrato, com contexto diário. Não vamos gerar Last a partir de candles nem usar os preços da lista de operações como negócios do MT5. O adaptador multianual do EA ainda precisa ser implementado/validado antes de ampliar o ensaio nativo. Backtest de candles e execução por ticks terão resultados e limitações próprios.

## Arquivos e uso das ferramentas

`dados/INVENTARIO_877_PREGOES.csv`: situação por data, fonte de ajuste, horários e espaçamentos observados; nenhuma data foi declarada pronta para backtest.

`dados/PILOTO_20260914_20260918.csv` e `dados/REFERENCIA_PILOTO_D.csv`: recorte do inventário e operações originais para conferir o piloto.

`comparar_teorico.py`: comparador pronto para receber uma rotina teórica independente. Compara chave Data/Nível/Lado, preços, horários, motivo e ambiguidade; detecta ausências, extras e diferenças. Reconcilia dias, meses, anos e total, com DD diário sobre as datas processadas. Em cobertura parcial, não declara DD integral. Tolerância numérica 0,000001 ponto, sem normalizar preços ao tick.

`dados/OPERACOES_NOVA_EXECUCAO_MODELO.csv` e `dados/COBERTURA_NOVA_EXECUCAO_MODELO.csv` contêm apenas cabeçalhos, porque ainda não há nova execução. A cobertura deve ter uma linha `Data;PROCESSADO` apenas após a rotina concluir o dia completo, mesmo se não houve operação. Datas sem cobertura continuam pendentes; nunca viram zero automaticamente. O comparador não aceita operações fora da cobertura, datas/níveis/lados inválidos, duplicatas ou números não finitos.

Os arquivos `sem_nova_execucao/` demonstram o estado atual real: **SEM_NOVA_EXECUCAO**, zero pregões comparados. Não são relatório de aprovação nem evidência de reprodução das 1877 operações.

Reproduzir inventário (Python 3 com openpyxl; argumento é a pasta extraída do ZIP original):

```sh
python preparar.py /caminho/pacote_extraido --saida dados
```

Comparar uma nova rotina teórica (diário e referência originais ficam na pasta superior no repositório):

```sh
python comparar_teorico.py --referencia ../Operacoes_Modelo_D_20230301_20260921_ORIGINAL.csv --operacoes dados/OPERACOES_NOVA_EXECUCAO_MODELO.csv --diario ../Referencia_D_diário.csv --cobertura dados/COBERTURA_NOVA_EXECUCAO_MODELO.csv --saida sem_nova_execucao
```

Validação das ferramentas: oito testes sintéticos do comparador passaram. Eles verificam tratamento de dados pendentes, dias sem operação, ausências/extras, duplicidade, diferenças, precisão e DD; não substituem execução do EA no MT5. Não usar a referência original como se fosse saída de uma rotina nova.

## Situação da R38,2 em 06/11

Toque às 10:30:02.602, alvo teórico observado às 10:30:02.618, sem execução nativa e cancelamento posterior conforme a regra. Movimento coincide com divulgação de notícias de alto impacto indicada pelo calendário enviado pelo usuário; isso não demonstra a causa da não execução no servidor XP DEMO. Esclarecimento adicional depende do Diário/registros da corretora. Essa investigação continua aberta, sem impedir a preparação histórica e sem mudar os parâmetros do Modelo D.
