# PROEJTO-EA

Estado geral atualizado em **12/11/2026**. Registro principal: **[RETOMADA_DO_TRABALHO.txt](entregas/v2_10/RETOMADA_DO_TRABALHO.txt)**. Esse TXT acompanha todas as etapas, o que foi concluído, pendências, evidências e próximo passo; será atualizado a cada avanço.

- **Setembro — resultado anterior preservado:** Work +3.839,31; nosso resultado principal +1.380,00; diferença −2.459,31 pontos. Critério: um contrato por nível, grade de cinco pontos, entrada por toque.
- **Trabalho ativo:** [agosto Cedro calculado sem MT5](entregas/cedro_modelod_agosto_2026/LEIA_RESULTADO.txt): Work −387,16; nosso principal **−2.275 pontos**, mesmas 20 datas e 43 operações. Dois PDFs salvos internamente. Próximo: reprocessar setembro pela Cedro; fonte anterior preservada.
- **Sequência aprovada:** D em setembro e outubro Cedro → A/B/C nos mesmos três meses → comparação dos quatro → estudo separado de alvos/stops. [Plano registrado](entregas/plano_comparacao_abcd_cedro_20261112/PLANO_E_CONTINUIDADE.txt).
- **Relatórios finais:** dois PDFs (técnico e enxuto Modelo D diário), atualizados internamente e entregues juntos no final. DD contínuo calculado em ordem cronológica, sem alterar resultados mensais já fechados.
- [Continuidade dos compilados e drawdown](entregas/compilado_work_modelod/LEIA_CONTINUIDADE.md)
- [Conteúdo recente da conversa e decisões](entregas/arquivo_conversa_20261111/CONTEXTO_E_CONTINUIDADE.md)
- [Trechos literais recentes — não é transcrição integral](entregas/arquivo_conversa_20261111/TRECHOS_LITERAIS_RECENTES.md)
- [Inventário dos originais disponíveis](entregas/arquivo_conversa_20261111/INVENTARIO_ORIGINAIS.csv)

## Histórico das entregas anteriores

Os estados “pendente” abaixo correspondem às datas originais. Para o estado corrente, prevalece o TXT principal acima.

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
- [Genial — piloto histórico concluído: 1559/1582 janelas conferidas; divergências localizadas e vínculos pendentes](entregas/diagnostico_cobertura_historica_v1_00/resultado_genial_piloto_20261106/VERIFICACAO_COMPLETA.md)
- [Genial focal v1.02 — compilado/executado: preços de M1/Work ausentes nos ticks recuperados em duas amostras](entregas/diagnostico_focal_genial_v1_02/resultado_genial_20261107/RESULTADO.md)
- [A/B Genial — Diário confirma descarte de ticks reais e geração substituta; CSVs originais pendentes](entregas/ab_genial_v1_21/resultado_20261108/RESULTADO_PRELIMINAR.md)
- [Comparativo principal Work × EA — um contrato, pontos, PDF e tratamento de ambiguidades/zeragem](entregas/historico_work_modelo_d_20261105/ESPECIFICACAO_COMPARATIVO_WORK_EA.md)
- [06/11 — XP DEMO: três pendentes canceladas no corte das 18h; fechamento de posição aberta ainda não exercitado](entregas/v2_13_05_demo/nativo_20261106_corte_18h/RESULTADO.md)

O cancelamento da pendente R61,8 no corte foi confirmado na XP DEMO; não havia posição aberta às 18h. Backtest multianual, confronto Work e conclusão da homologação permanecem em andamento. Conta real não liberada.

Revisão posterior do PDF de regras encontrou divergência expressa no item 9.7: a v2.13.04 mantém pendentes durante reconstrução/falha de histórico, enquanto o documento determina cancelamento com histórico incompleto. Código instalado preservado nesta auditoria; ver matriz antes de considerar conformidade integral.

A Revisão 1 substitui a redação anterior de 9.7: reconstrução não consome oportunidade; cancelamento confirmado sem toque/execução permite reenvio elegível. Documento atualizado; implementação geral no EA ainda pendente. A auditoria anterior permanece como registro da comparação com o PDF original.

A v2.13.05 implementa a Revisão 1, arquivamento de sessões encerradas, relatórios executados, freeze, auditoria de liquidez e tabela de horários revisados. 240 verificações locais ASan/UBSan passaram. Compilação e execução nativas desta versão pendentes; matemática e fonte B3 preservadas. O histórico Work e a liberação real continuam pendentes.

### Triagem do Tester na Genial — seis pregões (08/11/2026)

Pacote com o DiagTicksAB v1.21 inalterado, seis configurações B e seis A opcionais, roteiro e planilha de retorno. Execução nativa deste plano pendente; não é homologação do histórico nem de operações.

- [Guia e parâmetros](entregas/triagem_tester_genial_20261108/LEIA_PRIMEIRO.txt)
- [ZIP para o MT5](entregas/Triagem_Tester_Genial_6_Pregoes_20261108.zip)
- [Consolidação A/B XP e Genial com os quatro CSVs conferidos](entregas/resultado_ab_xp_genial_20261108/Resultados_AB_XP_e_Genial_2026-11-08.txt)

### Piloto de alimentação controlada v1.00 — 29/10/2026

Pacote preparado com importador em símbolo personalizado novo, auditoria de fonte/CopyTicksRange/OnTick, sonda amostral de datas antigas e revisão do ZIP fornecido pela outra IA. Sem alterações no EA da estratégia. Comparação exata, lotes sem dividir milissegundos e M1 derivado opcional/desligado. Compilação MetaEditor e execução nativa pendentes.

- [ZIP integrado](entregas/ModeloD_Piloto_Controlado_v1_00_Integrado.zip)
- [Instalação e roteiro](entregas/piloto_controlado_v1_00/LEIA_PRIMEIRO.txt)
- [Revisão e decisões de integração](entregas/piloto_controlado_v1_00/REVISAO_PACOTE_OUTRA_IA.md)
- [Verificações dos algoritmos](entregas/piloto_controlado_v1_00/tests/RESULTADO.json)
