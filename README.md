# PROEJTO-EA

Expert Advisor Modelo D para WIN no MT5. Estado consolidado em 05/11/2026, após o corte das 18h (Brasília).

- [Resultado dos dias 04–05/11, evidências e pendências](entregas/consolidacao_20261104_20261105/RESULTADO_E_ESTADO.md)
- [v2.13.05 DEMO — retomada, arquivamento, relatórios e horários revisados](entregas/v2_13_05_demo/LEIA_PRIMEIRO.txt)
- [Estado das pendências após a implementação](entregas/v2_13_05_demo/ESTADO_DAS_PENDENCIAS.md)
- [Regras vigentes — Revisão 1 aprovada](entregas/regras_modelo_d_revisao_1/LEIA_PRIMEIRO.md)
- [Auditoria das regras consolidadas contra v2.13.04](entregas/auditoria_regras_20261105/AUDITORIA_REGRAS_V21304.md)
- [v2.13.04 DEMO — fontes, ZIP e validação](entregas/v2_13_04_demo/LEIA_PRIMEIRO.txt)
- [A/B XP — Terminal versus Tester](entregas/diagnostico_ticks_ab_v1_21/resultado_xp_20261105/RESULTADO.md)
- [Referência histórica exclusivamente Modelo D — Work](entregas/historico_work_modelo_d_20261105/LEITURA_E_PREPARACAO.md)
- [06/11 — Replay teórico integral: 877 pregões, 1877 operações, zero divergências com Work; execução MT5 pendente](entregas/historico_work_modelo_d_20261105/replay_completo_20261106/RESULTADO.md)
- [Diagnóstico histórico v1.00 — lote de 877 pregões, somente leitura; compilação nativa pendente](entregas/diagnostico_cobertura_historica_v1_00/LEIA_PRIMEIRO.md)

O cancelamento da pendente R61,8 no corte foi confirmado na XP DEMO; não havia posição aberta às 18h. Backtest multianual, confronto Work e conclusão da homologação permanecem em andamento. Conta real não liberada.

Revisão posterior do PDF de regras encontrou divergência expressa no item 9.7: a v2.13.04 mantém pendentes durante reconstrução/falha de histórico, enquanto o documento determina cancelamento com histórico incompleto. Código instalado preservado nesta auditoria; ver matriz antes de considerar conformidade integral.

A Revisão 1 substitui a redação anterior de 9.7: reconstrução não consome oportunidade; cancelamento confirmado sem toque/execução permite reenvio elegível. Documento atualizado; implementação geral no EA ainda pendente. A auditoria anterior permanece como registro da comparação com o PDF original.

A v2.13.05 implementa a Revisão 1, arquivamento de sessões encerradas, relatórios executados, freeze, auditoria de liquidez e tabela de horários revisados. 240 verificações locais ASan/UBSan passaram. Compilação e execução nativas desta versão pendentes; matemática e fonte B3 preservadas. O histórico Work e a liberação real continuam pendentes.
