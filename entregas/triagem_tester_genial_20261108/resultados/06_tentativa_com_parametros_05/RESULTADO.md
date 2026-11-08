# Tentativa do teste 06 com entradas do teste 05

O Tester foi configurado para 29–30/10, mas InpFrom/To continuam em
19/10 09:00–09:10 e tag GTR_05_20261019_B. Não considerar teste 06 concluído.

Consulta à data anterior ao período da simulação: ALL=256971,
TRADE/negócios válidos=162331 e INFO=94640. Duas leituras estáveis, erro zero.
A mesma janela consultada DURANTE a simulação de 19/10 tinha retornado
ALL=37831 e TRADE=0 após descarte dos ticks reais. Nesta tentativa,
o motor processou ZERO ticks e ZERO barras antes de ExpertRemove.

É um achado relevante sobre a diferença entre consulta histórica anterior ao
período simulado e alimentação durante o próprio pregão simulado. Não prova
que os eventos OnTick de 19/10 seriam reais nem que o problema foi corrigido.
A origem dos registros precisa de conferência dos CSVs e controle A equivalente.

O Diário de 29/10 diz 'no real ticks within a day' e 'real ticks absent for
565 minutes of 565 total minute bars'; é AUSÊNCIA relatada pelo Tester,
diferente do descarte por incompatibilidade nas outras rodadas. Não inferir
que o terminal também não possui dados de 29/10. Como a consulta foi 19/10,
ainda não temos as contagens da janela alvo de 29/10 nesta execução.

Preservar ambos os retornos com tag 05, identificados pelo sufixo:
762382031 = simulação 19/10, consulta 19/10, fluxo sem negócios.
762592437 = simulação 29/10, consulta 19/10, negócios presentes fora do período.
Não misturar arquivos TXT/CSV entre essas rodadas.

Correção: manter Configuração WINZ26/M5, 29/10 até 30/10,
carregar 06_20261029_WINZ26_B.set e conferir janela 29/10 09:00–09:10,
tag GTR_06_20261029_B. Depois executar e preservar Diário/arquivos.
