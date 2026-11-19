# Novas entradas e frequência — 19/11/2026

Período: janeiro de 2024 a outubro de 2026, 709 pregões (34 meses). Cinco níveis originais preservados, 1.485 operações, +3.950 pontos brutos e DD diário contínuo de 14.805 pontos. Nenhuma variante foi promovida ao resultado principal.

## Novas hipóteses

R23,6% e R50% como vendas limitadas; S23,6% como compra limitada. Mesma matemática das oito linhas, referências e contratos do estudo original. Recalculados e confrontados os níveis de entrada de todas as 1.485 operações antigas: iguais. Filtros da abertura e bloqueio geométrico antes do arredondamento; grade de 5 pontos com o mesmo arredondamento; uma oportunidade por nível/dia, sem reentrada. Entradas somente antes das 18h. Posições independentes, sem fechar outras entradas ao atingir alvo. Corte na primeira cotação/candle disponível a partir de 18h. Não foi adicionado stop diário.

Novas entradas encontradas: R23,6% 386, R50% 299 e S23,6% 386. As frequências dependem da combinação de stop/alvo, e não só do nível. A contagem de oportunidades não soma dias como se todos os níveis operassem diariamente.

Testadas 168 receitas por nível (504 testes): alvos fixos 50/100/150/200/250/375/500/750; alvos 0,5/1/1,5/2 vezes a distância de referência; stops fixos 25/50/75/100/150/200/250/375/500/650 e stops proporcionais 0,5/1/1,5/2 vezes o alvo. Distâncias positivas com mínimo de 5 pontos. Referências novas: R23,6→Ajuste; R50→R38,2; S23,6→Ajuste. Isso define os testes; não é regra de entrada do Modelo D original.

## Seleção e combinações

Para cada novo nível, três escolhas usando somente 2024–2025: maior relação limite inferior/DD, maior total inferior e maior pior ano. Cada família foi cruzada com todos os 255 subconjuntos não vazios dos oito níveis: 765 avaliações, com duplicatas entre famílias. Os cinco antigos mantiveram seus stops/alvos originais. Não foi feita uma busca cartesiana de todas as 168 receitas entre si ou otimização adicional dos cinco antigos.

O candidato principal do estudo novo é o subconjunto de maior relação pontos/DD no treino. Os destaques de maior total e maior relação pontos/DD no período completo são posteriores à observação de 2026 e estão rotulados como exploratórios. Mesmo a divisão cronológica não constitui validação futura independente: todo esse período já era conhecido. Não afirmar que os destaques são um ótimo global ou um sistema viável antes de resolver pendências e considerar execução/custos.

O melhor candidato pelo treino conserva apenas S61,8% original e acrescenta os três novos: +22.940 a +35.855; DD 5.925 a 7.055; 26 operações pendentes.
O maior total entre as combinações testadas conserva R38,2/R61,8/S61,8 e acrescenta os três novos: +23.930 a +36.845; DD 10.580 a 11.435; 26 pendências.
A melhor relação pontos/DD no período completo conserva R61,8/S50 e acrescenta os três novos: +18.560 a +31.475; DD 3.595 a 3.850; 26 pendências.

As três usam R23,6 N154 (stop 25, alvo 2x distância até Ajuste), R50 N155 (stop 50, alvo 2x distância até R38,2) e S23,6 N089 (stop 200, alvo 500). S61,8 ORIGINAL significa stop 650 e alvo S50; não confundir com o stop 100 já estudado e fechado separadamente.

## Frequência

Frequência histórica: uma saída do tipo a cada N entradas = entradas/quantidade desse tipo. Não prevê periodicidade, ordem nem probabilidade da próxima operação. Alvo, stop cheio e saída por horário são separados. Não inferimos o motivo apenas pelo valor dos pontos: os rótulos originais foram recolhidos dos fechamentos/auditorias e confrontados com as distâncias dos stops/alvos. Os 1.485 rótulos estão preservados no CSV.

Nas receitas novas, contagens e frequências mostram garantidos e possíveis, incluindo as maiores sequências de stops/alvos em número de entradas, sem que dias sem operação interrompam a sequência. Uma saída por horário interrompe sequência de stop/alvo, mesmo se fechar com prejuízo/lucro. Limites distintos de eventos incertos não devem ser somados como se fossem simultâneos.

Há frequências totais e anuais para TODAS as receitas no ZIP, frequências dos cinco originais em CSV/Excel e mensais/anuais dos novos selecionados. Resultados mensais dos candidatos em CSV/Excel.

## Fontes, incertezas e confirmação

M1 MT5 nas fontes iniciais; Profit M1 nos meses correspondentes; M1 auditado Cedro de agosto a outubro/2026. Replay pontual prévio e 29 minutos de Datas.xlsx validados por OHLC e quantidade. As referências históricas são as mesmas do original, incluindo contextos originalmente documentados em M5. Não reabrimos os meses fechados.

Também reprocessados os 16 ZIPs Cedro já recuperados (8 dias de agosto, 39.031.316 registros dos contratos selecionados). Conferidos quantidade do fluxo e os cinco estados originais por dia; examinadas 965 operações/receitas novas pendentes nessas datas, 923 resolvidas com invariância à reversão dos grupos no mesmo milissegundo e sem grupos de barreiras opostas. As demais mantêm incerteza, sem atribuir ordem favorável. Arquivos brutos, recibos e hashes continuam preservados nas pastas anteriores; nenhuma alegação de que o usuário não os enviou.

Faixas não são lucros fechados. Limite inferior considera saídas desfavoráveis possíveis e o superior as favoráveis, sem presumir que todas possam ocorrer simultaneamente na mesma trajetória. DD por fechamentos diários em ordem cronológica, pico inicial zero, sem reinício mensal/anual. As faixas são envelopes conservadores, não estimativas probabilísticas. Não há auditoria integral tick a tick do período completo.

Execução teórica nos preços de stop/alvo, sem fila, custos ou slippage. Sensibilidade hipotética de 5 e 10 pontos por operação em CSV separado; não representa custo real informado. Stops muito pequenos e sequências longas merecem atenção particular.

A triagem de Replay dos novos selecionados tem 37 janelas em 32 datas. Não é solicitação automática para coletar todas. O 50/250 dos cinco níveis antigos continua em stand-by por decisão expressa do usuário; não foi retomado. A inclusão de pares numéricos iguais na grade dos NOVOS níveis não retoma aquele teste.

## Arquivos e reprodução

PDF de resumo; Excel com 504 receitas, 765 combinações, seleções, frequência original e nova, mensal e triagem de Replay. ZIP com tabelas completas de operações (179.928 linhas), pendências e frequência de todas as receitas. Demais CSVs legíveis e filtráveis na pasta.

Ordem de reprodução: estudar.py (varredura inicial); conferir_raw.py (fontes Cedro locais); estudar.py (aplica provas Cedro); frequencias_relatorio.py; verificar.py. Dependem das fontes e caches locais dos estudos anteriores. Não é um pacote autônomo sem os acervos. A fonte externa Datas.xlsx e os brutos Cedro estão documentados nos manifestos das entregas anteriores.
