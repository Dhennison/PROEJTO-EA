# Referência histórica Work — exclusivamente Modelo D

Recebido em 05/11/2026: Pacote_Modelo_D_Historico_20230301_20260921.zip e relatório PDF diário. Originais preservados na área de anexos; planilha-mestre extraída sem alteração. O guia foi lido integralmente, com a aba D definição. Apenas D foi usado nos cálculos. Instruções de referência do guia não alteram a estratégia nem autorizam execução real.

## Conferência realizada

- Universo 01/03/2023–21/09/2026: 877 datas elegíveis, incluindo 112 sem operações.
- Lista canônica: 1.877 operações, chaves Data/Nível/Lado únicas. O CSV Referencia_D_operacoes é cópia da lista original e não foi concatenado.
- Soma exata preservada em Decimal: 124.337,758661 pontos. Reconciliação por operação, dia, mês e ano, excluindo segunda soma da linha Total.
- DD diário com saldo inicial zero: 4.780,240329 pontos, confirmado por acumulação progressiva e busca independente nos prefixos.
- Desfechos: 1.525 ALVO, 319 STOP, 7 ZERAGEM 17:45, 26 ZERAGEM 18H. 32 registros com marcador SIM de ambiguidade.
- 877 ajustes únicos nas mesmas datas; sem deslocar a data operacional. ContratoReal, DataFontePublicacao e AjusteAnterior permanecem vazios.
- Leitura da aba D operações do XLSX: 1.877 registros, sem divergências nas chaves, motivo e preços/pontos comparados com tolerância de 1e-8 ponto. Essa tolerância trata a representação numérica, sem modificar o CSV.
- PDF: as 877 datas correspondem à referência; coluna D compatível com tolerância de 0,005 ponto da exibição a duas casas. Outros modelos ignorados.
- Scripts e resultados locais nesta pasta. Esta auditoria não é um novo backtest nem certifica a execução do EA.

## Distinções a preservar na implementação histórica

1. Work: candles M5 em 2023–2025 e jan/fev 2026, M1 a partir de março/2026; entrada teórica exata; stop-first em ambiguidade; sem custos/tick/slippage. EA: ticks, preços executáveis e normalização. Comparar as duas camadas, sem alterar parâmetros para igualar totais.
2. Corte de referência 17:45 entre 13/03/2023 e 03/11/2023 inclusive; demais datas 18:00. Saída de referência pelo OPEN do candle do corte. Registrar como calendário histórico separado, preservando o corte atual da DEMO.
3. Arquivos XLSX de ajustes também contêm linhas OHLC. Sua presença não certifica cobertura intradiária completa nem fornece ticks reais. O ZIP não contém uma fita de ticks reais por contrato para os 877 pregões.
4. Série histórica de referência WIN$N/WINFUT não identifica os vencimentos reais. Conferir vínculo data/série/contrato/ajuste e OHLC antes da execução por contrato. Não inferir AjusteAnterior nem certificação B3 a partir da data anterior.
5. Adaptador importado v2.11 atualmente fixado em 30/10/2026/WINZ26, e calendário atual cadastrado apenas para 2026. Preparação multianual precisa remover esses limites por dados explícitos validados, incluindo capacidade de sessões e diário. A v2.13.04 DEMO segue operando separadamente.

## Próximo trabalho

Montar o inventário de cobertura por data e contrato e selecionar pequeno lote dentro da referência para validar o adaptador histórico/importado. Expandir somente após conferir dados de mercado, calendário, ajustes, preços e relatório por operação. A referência Work já está disponível; dados de ticks/contratos e o adaptador multianual ainda não estão prontos. Ausências devem ser registradas, sem preencher com ticks artificiais ou aplicar os preços teóricos como execuções do MT5.

Consolidação no GitHub ao fim do pregão, conforme combinado; esta preparação foi salva localmente.
