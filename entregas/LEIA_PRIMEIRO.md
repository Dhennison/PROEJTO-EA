# Entrega Modelo D — v2.04 — 29/10/2026

Pacote atual: ModeloD_Integrado_Sem_Transporte_v2_04.zip. Extrair na pasta principal do projeto e copiar as subpastas de MQL5/Scripts e MQL5/Experts para as respectivas pastas da instalação MT5, preservando Common/Files. Compilar o script, executar duas vezes (631/0 + 104/0 em cada) e compilar o EA. Somente após aprovação nativa seguir com a observação de cerca de 15 minutos no WIN$N M5, negociação algorítmica desativada. Remover manualmente o EA ao terminar.

A v2.04 acrescenta diagnóstico de bloqueios e recuperação no relatório do EA e corrige inicialização explícita de áreas inativas de estruturas em memória antes de cópia/decodificação. A investigação foi local com sanitizadores; não é uma falha já comprovada no MT5. Como a correção afeta cabeçalhos compartilhados, esta revisão precisa atualizar Experts e Scripts e ser recompilada/testada nativamente. Regras, preços, consumo, prazos, formato do diário e transporte não foram alterados. Não apaga nem recria checkpoints.

Os quatro blocos e seus critérios de conclusão/impedimento estão em CRITERIOS_QUATRO_BLOCOS_20261029.md e no ZIP. Testes nativos anteriores não foram automaticamente atribuídos a esta revisão. Transporte permanece ausente. A main não foi alterada.
