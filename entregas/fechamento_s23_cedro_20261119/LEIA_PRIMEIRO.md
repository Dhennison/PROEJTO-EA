# S23,6% stop200/alvo500 fechado — 19/11/2026

Recebidos novamente os dez ZIPs Cedro solicitados, cinco pregões de agosto/setembro. Todos os nomes, tamanhos, SHA256 e IDs Sediment de restauração estão em RESTAURACAO_FONTES.json. Bytes idênticos aos recibos históricos. Brutos preservados em /workspace/dados_brutos_modelo_d/cedro/. O usuário já havia enviado os 132 ZIPs dos três meses; esta etapa recuperou acesso a dez deles, não foi captura nova.

Agora existe índice unificado dos 26 ZIPs acessíveis em INDICE_26_ZIPS_RESTAURADOS.json, incluindo os 16 anteriores e os dez novos. Os demais brutos recebidos historicamente não foram declarados recuperados. Não pedir novamente arquivos presentes neste índice: restaurar pelos IDs quando necessário.

## Resultado fechado da configuração isolada

S23,6%, compra, stop fixo200 e alvo fixo500, mesmas 386 entradas (142/138/106 por ano), uma por nível/dia, sem reentrada, grade5 e corte no primeiro negócio/candle a partir de18h. Referências e elegibilidade preservadas.

2024: +8.935, DD anual1.600.
2025: +3.885, DD anual2.300.
2026 janeiro-outubro: +95, DD anual3.600.
Total: +12.915; DD diário CONTÍNUO:4.915; zero operações pendentes.

Os DDs anuais são diagnósticos separados. O DD contínuo considera todos os fechamentos diários em ordem cronológica, pico inicial zero, sem reinício mensal/anual. Não somar DDs anuais ou mensais.

Frequência:126 alvos,253 stops cheios,7 cortes; alvo a cada3,06349 entradas, stop a cada1,52569; maior sequência de12stops. Frequências empíricas, não periodicidade garantida ou probabilidade futura. Cortes são separados mesmo quando fecham em prejuízo/lucro.

Todos os resultados são brutos, com execução teórica nos níveis; sem custos, fila ou slippage. O ganho de apenas95em2026 antes dos custos indica forte enfraquecimento frente a2024/2025. Não confundir fechamento das dúvidas com validação futura independente. Nenhuma variante promovida ao resultado principal.

## Cinco casos finais

11/08/2026 WINQ26: SL-200; entrada09:03:07.381; saída09:03:18.058.
24/08/2026 WINV26: SL-200; entrada09:00:48.104; saída09:01:00.430.
04/09/2026 WINV26: SL-200; entrada09:30:03.288; saída09:30:05.824.
11/09/2026 WINV26: SL-200; entrada09:05:41.959; saída09:12:06.944.
25/09/2026 WINV26: SL-200; entrada09:03:47.703; saída09:05:00.999.
Total destas cinco:-1000. Ordinais e preços reais dos negócios estão no CSV.

Reprocessadas ambas as partes completas de cada dia, 26.558.920 registros dos contratos selecionados. Quantidade do fluxo conferida com inventário. Ordinais e milissegundos sem regressão. Motor C++ no fluxo integral e motor Python em eventos reduzidos preservando todas as barreiras conferem30estados (5originais+S23 em5dias). Os25estados originais permanecem iguais aos resultados salvos. Inversão de empates no mesmo milissegundo e verificação de grupos com barreiras opostas confirmam os cinco desfechos; não se deduziu a ordem apenas de candles.

Os primeiros dois registros de cada categoria de preço e as mudanças de categoria/minuto são preservados na redução para Python, com limites das seis configurações. O C++ calcula e confere estados em TODOS os registros independentemente dessa redução. Eventos reduzidos em /workspace/work/fechamento_s23_cedro_20261119/EVENTOS_*.csv podem ser regenerados dos brutos; hashes de cada arquivo constam na auditoria.

## Combinações anteriores

A contribuição S23N089 foi atualizada nos três conjuntos já destacados; os demais níveis/receitas não foram reapurados. As combinações continuam com16operações pendentes emR23,6/R50. Não apresentá-las como fechadas só porque S23 terminou. CSVs de totais e curvas diárias documentam as faixas restantes.

## Preservação e fontes

Modelo D original, resultados dos meses fechados, rankings e estudos anteriores intactos. Nenhuma alteração do controle dispensado de10/07. 50/250 dos cinco níveis continua emstand-by.

Fontes do período completo continuam M1MT5/Profit/Cedro auditado eReplaypontual onde validado, mais negócios Cedro disponíveis e provas documentadas. Não é auditoria integral tickatick dos34meses. Nota31/07sobreleilão preservada: retorno informado12:34:07; primeiro negócio da planilha12:34:07.958.

PDF, Excel, anual/mensal/diário,386operações e frequência finais nesta pasta. Cache atualizado /workspace/work/fechamento_s23_cedro_20261119/fechado.pickle. Os estudos futuros devem usar as janelas Novasdatas já validadas e as provas brutas daqui antes de marcar as mesmas dúvidas.

Ordem de reprodução: reprocessar.py; fechar.py; verificar.py. Dependem dos brutos e caches de referências/estudos anteriores; não é pacote autônomo sem o acervo. Fontes de novos uploads recuperáveis via IDs do manifesto.
