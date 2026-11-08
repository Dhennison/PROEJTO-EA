# Diagnóstico focal Genial v1.02 — duas janelas de cinco minutos

Consulta somente de leitura, no **terminal da Genial**. Não envia ordens, não usa bibliotecas do EA, não altera ajustes ou diários operacionais. É um programa separado do diagnóstico de 877 pregões e não repete setembro inteiro.

## Janelas já configuradas

| Janela | Símbolo consultado | Início, horário do servidor | Final exclusivo |
|---|---|---|---|
| 1 | WINV26 | **01/09/2026 18:20:00** | **18:25:00** |
| 2 | WINV26 | **02/09/2026 16:10:00** | **16:15:00** |

A primeira representa a divergência recorrente depois do corte; a segunda representa divergência durante o período operacional. Os dados serão consultados em ALL, TRADE e M1. Estabilidade exige duas leituras consecutivas válidas iguais em todos os campos de cada fonte, incluindo volume e spread das barras. Não é necessário que o OHLC dos ticks coincida com o M1 para concluir a coleta: registrar essa diferença é o objetivo.

Não há conversão automática de fuso nem aprovação de identificação histórica/ajuste B3. `SymbolCustom`, modo de construção do gráfico, servidor e horários atuais serão registrados. Se o modo do símbolo for Bid, não interpretar a comparação Last/M1 como prova de erro da base de negócios. O foco é medir e exportar o que a API entrega.

## Instalar e compilar

1. Extraia o ZIP.
2. No **MT5 da Genial**, abra **Arquivo → Abrir Pasta de Dados**.
3. Cole nessa raiz a pasta **MQL5** recebida, mesclando as pastas. Não crie MQL5/MQL5. Os arquivos devem ficar em:

```text
MQL5/Experts/ModeloD_Diagnostico_Focal/Diagnostico_Focal_Ticks_M1.mq5
MQL5/Experts/ModeloD_Diagnostico_Focal/Focal_Core.mqh
MQL5/Experts/ModeloD_Diagnostico_Focal/HC_Core.mqh
```

4. Pressione **F4**, abra o `.mq5` acima e compile com **F7**.
5. Envie o resultado da compilação antes de iniciar a nova consulta. Não é preciso alterar o EA DEMO na XP nem os relatórios antigos.

## Executar depois de conferir a compilação

Use o gráfico separado no MT5 da Genial. Se o diagnóstico anterior já estiver concluído e ainda anexado, retire somente ele desse gráfico e coloque **Diagnostico_Focal_Ticks_M1**. O símbolo e o período do gráfico não determinam a consulta; pode ser WINZ26/M5.

Mantenha os parâmetros padrão:

- `InpSimbolo = WINV26`
- `InpInicio1 = 2026.09.01 18:20:00`
- `InpFim1 = 2026.09.01 18:25:00`
- `InpInicio2 = 2026.09.02 16:10:00`
- `InpFim2 = 2026.09.02 16:15:00`
- `InpIdentificador = GENIAL_FOCAL`
- `InpMaxTentativas = 6`

Clique OK. Não é necessário habilitar AlgoTrading, DLL ou WebRequest. Precisa de conexão com o servidor, mas não de pregão aberto ou cotações novas no gráfico. Uma chamada de histórico pode aguardar sincronização; o gráfico e o Experts mostram a fase antes de cada chamada. Os mesmos eventos também ficam em TENTATIVAS.csv, com retorno, erros e duração.

O programa processa as duas janelas automaticamente. Ao aparecer **FOCAL102_END**, as consultas terminaram e os arquivos foram fechados. Isso não significa que os snapshots foram estáveis ou que os dados estão aprovados: verificar os relatórios. Se as seis tentativas terminarem com snapshot válido mas instável, os arquivos são exportados como não estáveis; não podem provar ausência de negócios ou resultado definitivo. Se a última leitura for inválida, há relatório de erro e não são gerados CSVs aceitos dessa janela.

Esta etapa foi feita para o terminal. Se colocado no Tester, o programa recusa iniciar; o A/B Genial pendente continua sendo outra verificação com DiagTicksAB v1.21, conforme a configuração da XP.

## Encontrar e enviar os arquivos

Pressione **Windows + R**, cole e pressione Enter:

```text
%APPDATA%\MetaQuotes\Terminal\Common\Files\ModeloD_Historico_Focal
```

Dentro haverá uma pasta nova começando por **F102_GENIAL_FOCAL_...**. O caminho completo aparece no Experts em `FOCAL102_START`.

Após FOCAL102_END, compacte **essa pasta inteira** em um ZIP e envie. Não precisa escolher cada arquivo nem reenviar os relatórios do lote anterior. Cada execução usa uma pasta própria, sem substituir resultados anteriores; esta coleta curta não retoma uma janela interrompida, mas pode ser reexecutada com outra pasta de resultados preservada.

## O que será exportado

Para cada janela:

- `JANELA1_ALL.csv` / `JANELA2_ALL.csv`: todos os ticks da leitura final válida, na ordem original, com índice, time, time_msc, Bid, Ask, Last, volume, volume_real e flags completos.
- `..._TRADE.csv`: ticks retornados pelo canal TRADE.
- `..._M1.csv`: barras M1, inclusive tick_volume, real_volume e spread.
- `..._MINUTOS.csv`: OHLC dos ticks válidos de negócio em ALL e TRADE, OHLC M1, campos diferentes (O/H/L/C), diferenças numéricas e primeiro/último timestamp de negócio de cada minuto.
- `..._LEITURA1_MINUTOS.csv`, `..._LEITURA2_MINUTOS.csv` etc.: OHLC por minuto de cada tentativa válida. Permitem ver alterações de preço durante as releituras, sem repetir a exportação volumosa de todos os ticks a cada tentativa.
- `..._RELATORIO.txt`: estabilidade, validade, tamanhos dos arrays finais, janela, tentativas e códigos de erro.

Além disso, `META.txt` e `TENTATIVAS.csv` descrevem o ambiente e todas as chamadas. O END no log é um marcador do lote; não é uma terceira janela consultada.

Critério de negócio preservado: **flags & (LAST|VOLUME|BUY|SELL), Last positivo e finito**. Não se usa Bid/Ask para inventar negócios. Preços não são normalizados ao tick. Exportação em precisão de 17 algarismos significativos, sem hash arredondado para decidir estabilidade. Os índices preservam registros com mesmo milissegundo; não há deduplicação por timestamp.

O arquivo `BASELINE_2_JANELAS.csv` preserva as contagens dessas duas janelas na primeira coleta, em 06/11/2026. Ele não contém o OHLC original divergente, que a v1.00 não exportava. Uma eventual diferença entre essa coleta e a nova precisa ser interpretada à luz dessa limitação; não atribuir atualização ao servidor/cache sem evidência suficiente.

## Análise e validação local

`analisar_focal.py` recalcula o OHLC a partir dos CSVs brutos exportados, sem confiar nos deltas do CSV nativo, e conserva os estados não estáveis. Não é necessário executar Python no notebook: os arquivos podem ser enviados para análise aqui.

Validações realizadas: **24 verificações C++ do núcleo e da serialização extraídos do MQL, com tipos/APIs simulados e ASan/UBSan; seis testes Python do analisador; preflight de `input` global e ausência de transporte de ordens**. Todas passaram. O núcleo HC_Core foi preservado da v1.00.

**A v1.02 ainda precisa de compilação e execução nativas no MetaEditor/MT5**, indisponíveis neste ambiente. Não é um novo EA operacional nem um backtest nativo já realizado. A evidência coletada servirá para localizar a causa da diferença entre ticks e barras, sem flexibilizar regras ou apagar as pendências existentes.
