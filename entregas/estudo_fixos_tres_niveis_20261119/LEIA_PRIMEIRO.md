# Alvos/stops fixos em três níveis — 19/11/2026

Pedido: testar R61,8%, S38,2% e S61,8%, inclusive stop200/alvo500, preservando originais. Período janeiro/2024–outubro/2026. Mesmas 834 entradas: 255 R61,8%, 346 S38,2%, 233 S61,8%. Parâmetros de saída novos não mudam elegibilidade, referências, contrato ou primeiro toque. Uma entrada por nível/dia, sem reentrada. Grade de 5 pontos; corte na primeira cotação/candle a partir de 18h. Sem stop diário novo.

## Grade e resultados

90 receitas por nível, 270 testes. Stops 25/50/75/100/150/200/250/375/500/650; alvos 50/100/150/200/250/375/500/750/1000. Ambos fixos em pontos, independentemente das distâncias Fibonacci. Busca finita, não ótimo global.

Stop200/alvo500:
- R61,8%: 2024 +600 a1300; 2025 +140; 2026jan-out -1990 a110; total -1250 a1550; DD3700 a3970; 4 operações pendentes.
- S38,2%: -2840; +1575 a2275; -4100 a100; total -5365 a-465; DD7130 a8965; 7 pendentes.
- S61,8%: -2060 a-1360; -85 a615; -2715 a-2015; total -4860 a-2760; DD4000 a5760; 3 pendentes.

Destaques exploratórios:
- R61,8% stop75/alvo1000: +4760/+460/-1175; total+4045, DD2360, fechado. Melhor relação pontos/DD entre receitas desse nível.
- R61,8% stop375/alvo1000: +2315/+1705/+1705; total+5725, DD4865, fechado. Maior total conservador nesse nível.
- S38,2% stop200/alvo1000: -305/+3110/-1675; total+1130, DD6000, fechado. Maior total e relação pontos/DD nesse nível, sem retorno atraente frente ao DD.
- S61,8% stop25/alvo100: total1175 a8550, DD325 a550, 59 pendentes. A pequena distância exige muita confirmação de sequência; não promover com base na faixa favorável.
- S61,8% stop650/alvo100: total1470 a8765, DD2200 a3495, 11 pendentes. Maior total inferior nesse nível, mas relação entre stop/alvo desfavorável; não constitui recomendação.

Valores brutos sem custos/slippage/fila; seleção de destaques após observar período completo é exploratória e sujeita a sobreajuste. Também preservada seleção por 2024–2025. O período 2026 já era conhecido, não teste futuro independente. Nenhum modelo foi promovido ao resultado principal. Não interpretamos contagens absolutas de stops como vantagem sem considerar número de entradas, alvo médio, stop e frequência relativa.

DD por fechamentos diários em ordem cronológica, pico inicial zero, sem reinício mensal/anual. DD mensal e anual separados nos CSVs, sem somar DDs mensais para obter contínuo. Faixas mantidas nas dúvidas de sequência, sem tratá-las como probabilidades ou lucro realizado. Extremos de receitas simultâneas podem não ser conjuntamente atingíveis.

## Fontes e provas

Mesmo motor de conjuntos de desfechos do estudo dos níveis auxiliares: M1 MT5/Profit/Cedro auditado, Replay validado existente e provas monotônicas dos desfechos originais congelados. Stop original com stop novo menor e alvo novo não mais próximo implica stop novo; alvo original com stop novo não menor e alvo novo não mais distante implica alvo novo; corte com ambas as barreiras relaxadas permanece corte. As provas são registradas individualmente.

Reprocessados os 16 ZIPs Cedro acessíveis, 8 dias de agosto: 39.031.316 registros dos contratos, cinco estados originais por dia conferidos iguais. Examinadas 213 receitas/operações pendentes; 190 resolvidas com invariância de ordem nos milissegundos e rejeição de grupos com barreiras opostas. Os demais casos permaneceram incertos. Não é auditoria integral tick a tick do período completo.

## Correção da lista S23,6% 200/500

O usuário já enviou TODOS os logs Cedro de agosto, setembro e outubro. Recibos de 132 ZIPs confirmam recebimento e hashes. No ambiente atual, 16 ZIPs estão presentes; 116 não estão acessíveis. Foram conferidos filesystem, anexos atuais, arquivos ZIP do repositório, histórico relevante e lançamentos GitHub. Candles, recibos e resultados não substituem os negócios individuais para novas ambiguidades. Eventos reduzidos antigos não foram presumidos completos para novos níveis/barreiras.

Portanto os cinco dias Cedro NÃO são pedidos de nova captura. A classificação anterior foi corrigida sem alterar os estudos financeiros anteriores.

Replay a coletar (fim exclusivo, minuto inteiro e alguns segundos de margem):
- 11/09/2025 WINV25 09:30–09:31
- 13/02/2026 WING26 09:01–09:02
- 17/03/2026 WINJ26 09:00–09:01
- 11/05/2026 WINM26 09:01–09:02
- 31/07/2026 WINQ26 12:34–12:35

Pendências de recuperação de brutos já enviados, NÃO Replay novo:
- 11/08/2026 WINQ26 09:03–09:04: WIN_20260811_parte001.zip e WIN_20260811_parte002.zip.
- 24/08/2026 WINV26 09:00–09:01: WIN_20260824_parte001.zip e WIN_20260824_parte002.zip.
- 04/09/2026 WINV26 09:30–09:31: WIN_20260904_parte001.zip e WIN_20260904_parte002.zip.
- 11/09/2026 WINV26 09:05–09:06: WIN_20260911_parte001.zip e WIN_20260911_parte002.zip.
- 25/09/2026 WINV26 09:03–09:04: WIN_20260925_parte001.zip e WIN_20260925_parte002.zip.

Nomes, tamanhos, SHA256 e recibos exatos em S23_CEDRO_10_ZIPS_JA_RECEBIDOS_A_RESTAURAR.csv. Inventário dos 132 em ACERVO_CEDRO_RECEBIDO_E_ACESSO_ATUAL.csv. Não pedir recaptura, compra ou reextração desses períodos como se não tivessem sido enviados. Os cinco casos não foram fechados artificialmente nem removidos da incerteza do S23.

## Entrega e reprodução

PDF, Excel anual/mensal/frequências; ZIP com 75.060 operações/receitas, pendências e frequências totais/anuais. Modelo de retorno somente para as cinco datas de Replay. Scripts dependem dos acervos/caches locais anteriores. Ordem: testar.py; conferir_raw.py; testar.py; relatorio.py; verificar.py.

O estudo 50/250 dos CINCO níveis continua em stand-by. A nova grade dos TRÊS níveis, incluindo esse par, foi expressamente autorizada no pedido atual; não retomamos a coleta anterior dos cinco níveis. Nenhum resultado fechado nem controle dispensado de 10/07 foi reaberto.
