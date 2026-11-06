# Estado após a implementação da v2.13.05

Código e ensaios locais concluídos nesta entrega; compilação e execução MQL5 da v2.13.05 ainda pendentes. Não confundir implementação com homologação no servidor.

| Item | Estado |
|---|---|
| 1. Retomada/R61 e política 9.7 | Recuperação específica já comprovada na v2.13.04. Política geral da Revisão 1 implementada na v2.13.05, incluindo reenvios sucessivos; falta prova nativa desta versão. |
| 2. Homologação XP DEMO | Parcial. Preservadas evidências do pregão de 05/11. Compilar/reanexar v2.13.05 no mesmo contexto e conferir diário, novas saídas e retomadas. |
| 3. Corte na DEMO | Cancelamento/bloqueio comprovados na v2.13.04; sem posição aberta no corte daquele dia. Não repetir teste sintético já concluído sem necessidade; fechamento nativo quando houver condição útil. |
| 4. Histórico Work | Ajustes/lista e universo auditados. Tabela por data/contrato preparada no adaptador DEMO, mas faltam calendário multianual, vínculos reais, OHLC/ticks e adaptador histórico principal com volume 5. |
| 5. Comparação Work | Aberta. CSV executado diário implementado; teórico independente e comparação 877 pregões não executados. |
| 6. A/B Genial | Pendente. |
| 7. Causa do descarte no Tester | Pendente. O mecanismo de geração/descarte foi identificado, sua causa upstream não foi demonstrada. |
| 8. Falha visual | Pendente de revisão com ocorrência reproduzível; camada visual não foi alterada nesta entrega. |
| 9. Operação contínua/Genial | Avançou com arquivamento de sessões, relatórios, freeze, liquidez e horários revisados. Ainda requer execução prolongada, cobertura de dados/calendário, desempenho e homologação da Genial; conta real bloqueada. |
| 10. GitHub | Consolidação anterior publicada; esta entrega acrescenta fontes, validações e ZIP, sem substituir evidências históricas. |

A guarda de leitura do diário em 128 MiB e os limites de snapshots/cadeias permanecem como mecanismos explícitos. O arquivamento remove a acumulação de dias/posições encerradas nos slots de trabalho, mas não declara capacidade ilimitada ou desempenho multianual homologado. Recibos e eventos permanecem no diário imutável.
