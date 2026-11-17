# Conferência de 2024 — preparação do Replay

247 pregões preparados e 521 operações conhecidas. 483 operações determinadas pelos candles sem pendência de sequência, cobertura ou controle de grade. Permanecem 25 operações com dúvida de sequência, dez controles de grade e duas lacunas de cobertura que afetam posições. As categorias podem compartilhar operações/datas.

**Lista final: 32 datas, 33 intervalos, 35 minutos úteis**, mais alguns segundos antes/depois. Os intervalos contíguos foram unidos. Abril não tem janela necessária para o D original sob os dados disponíveis. A lista corresponde à necessidade de coleta: não comprova disponibilidade no servidor do Profit.

- `LISTA_REPLAY_POR_MES.txt`: leitura rápida de todas as datas, horários e contratos.
- `Replay_2024_Preparacao_e_Abas_Retorno.xlsx`: resumo por mês, pedidos e abas vazias para colar os negócios.
- `Conferencia_2024_Replay_por_Mes.pdf`: 12 páginas, uma por mês.
- `REPLAY_LISTA_FINAL.csv`: intervalos consolidados, com horários sugeridos de captura.
- Pastas mensais: operações concretas/pendentes, referências, comparação M1/M5 e auditorias.

M1 MT5 WIN$N disponível nos 12 meses, exportações estáveis em duas tentativas. Fonte Work: Profit WINFUT M5. Todos os grupos OHLC anteriores às 18h coincidem; os resultados possíveis em M1 refinam os de M5. As entradas, alvos e stops matemáticos reproduzem as operações Work existentes. Há 53 grupos com diferença de quantidade; isso permanece ressalva, não prova falta de negócios. Em 04/09 18:20, a mínima M1 é 137780 contra 137920 no M5, após o corte. Preservado HLC Work no contexto seguinte; não recalibrar referências para eliminar a diferença.

**Início do ano:** 02, 03, 04 e 05/01 têm M1, mas seus ajustes operacionais não constam nas duas tabelas de ajustes consultadas. Faltam os valores e a referência original desses quatro ajustes, não candles M1. Sem isso não se delimitam níveis nem se atribui zero. M5 começa em 05/01 parcial. 08/01 foi preparado como complemento separado, ajuste 133414 e contexto 05/01 M1 completo; referência Work começa em 09/01. Contexto de 02/01, quando houver ajuste, está disponível em M1 de 28/12/2023.

**Contratos:** WING24 até 13/02; WINJ24 de 14/02 a 16/04; WINM24 de 17/04 a 11/06; WINQ24 de 12/06 a 13/08; WINV24 de 14/08 a 15/10; WINZ24 de 16/10 a 17/12; WING25 a partir de 18/12. Convenção de rolagem no vencimento, preservada do projeto. Confirmar correspondência dos preços ao receber cópia do contrato real; continuidade/ajustes de WINFUT e WIN$N não são prova automática dessa correspondência. Disponibilidade no Profit ainda não verificada.

**Coleta:** horários de São Paulo; fim exclusivo. Capturar o minuto inteiro e alguns segundos antes/depois, sem filtros e sem deduplicação; manter negócios idênticos e milissegundos. Se não houver cotações ou o contrato não estiver disponível, informar exatamente a ocorrência. Na volta, conferir OHLC/quantidade, limites da cópia e ordem de negócios no mesmo milissegundo antes de resolver. Exportação de candles não substitui negócios individuais.

D original: S38.2, S50, S61.8, R38.2, R61.8; grade 5, um contrato por nível, toque inclusivo, corte 18h. Sem custos/fila/slippage ou fills certificados. M1 e Replay pontual não são auditoria integral tick a tick. Nenhum resultado mensal ou DD de 2024 está fechado nesta preparação. Parâmetros e todos os meses anteriormente fechados foram preservados.

A solicitação de 17/11 reabriu explicitamente a conferência de 2024 antes das variantes de saídas. 2023 permanece fora da expansão; não comprar histórico. Stop proporcional ao alvo segue registrado como hipótese futura, sem teste executado nesta entrega.
