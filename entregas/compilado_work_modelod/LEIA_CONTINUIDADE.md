# Dois compilados finais — Work × Modelo D

O usuário solicitou **dois PDFs finais**, atualizados a cada mês apurado:

1. **Técnico:** relatórios originais preservados, observações, dados, cenários secundários, limitações, operações e auditoria.
2. **Enxuto:** no estilo do PDF `relatorio_diario_win_modelos_abcd_2023_2026.pdf`, porém **somente Modelo D**, com data, dia da semana, Work, nosso resultado diário e diferença lado a lado. Um mês por página; somente meses apurados entram neste compilado em andamento, ordenados cronologicamente.

Preferência expressa: mostrar primeiro **Work, nosso resultado principal e diferença**. O principal usa **um contrato por nível, grade de cinco pontos e entrada por toque inclusivo**. Outros cenários ficam apenas na parte técnica.

## Resultados congelados e drawdown recalculável

Setembro/2026 (01 a 21) está concluído sobre a alimentação recebida, com ressalvas documentadas. Work: **+3.839,308998**; nosso principal: **+1.380**; diferença: **−2.459,308998** pontos. Os valores diários e mensais são preservados. Não reabrir as mesmas coletas para prometer preenchimento de bolsa retroativo.

**Instrução posterior do usuário sobre DD:** mesmo coletando setembro, agosto, julho, o cálculo percorre julho, agosto, setembro. Saldo, pico histórico e maior DD são carregados entre os meses. Ao inserir meses anteriores, recalcular a curva e o DD dos meses posteriores **sem alterar seus resultados diários ou mensais**. Saldos acumulados também incorporam os novos meses naturalmente.

A medida principal de risco é **DD máximo acumulado da curva contínua de fechamentos diários**, incluindo o pico inicial zero no começo da base, sem reset mensal. Não confundir com DD intradiário ou percentual. O DD local do PDF original do Work, que reiniciava a cada mês, fica como referência técnica separada.

Até completar os meses anteriores, o DD é **provisório**. Work e teste usam os mesmos dias já apurados, com início de base explicitado. Não comparar Work desde 2023 com teste começando em setembro sem indicar essa diferença; não preencher meses ausentes com zero nem concatenar períodos com lacunas como curva contínua.

Base comum atual: setembro/2026. DD Work **1.087,585333** e DD teste **1.575** pontos. Esses valores podem mudar com meses anteriores; nosso resultado mensal **+1.380** não muda. O teste de regressão usa valores sintéticos de agosto somente em diretório temporário, confirma a propagação do DD e recusa lacunas; não é apuração de agosto.

## Fonte e arquivos

Os 877 resultados diários Modelo D e os 43 totais, DD locais e acumulados foram conferidos contra o PDF enviado na precisão de exibição. Textos numéricos originais do Work são preservados; valores internos de seis casas vêm da referência já auditada. Os modelos A/B/C e o PDF bruto original não integram a publicação.

- `Comparativo_Work_ModeloD_Tecnico_Em_Andamento.pdf`: compilado técnico.
- `Comparativo_Diario_ModeloD_Enxuto_Em_Andamento.pdf`: compilado enxuto.
- `Comparativo_Work_ModeloD_Compilado_Em_Andamento.pdf`: alias mantido para o link técnico anterior.
- `originais_por_mes`: PDF original de setembro preservado byte a byte e com SHA-256.
- `diarios_principais`: dados principais mensais congelados; nunca incluir controles secundários como resultado principal.
- `INDICE_MENSAL.csv`: catálogo dos 43 meses; meses pendentes não entram no acumulado comparável.
- `CURVA_DIARIA_E_DRAWDOWN.csv`: resultados, saldo, pico, DD atual e DD máximo acumulado em ordem crescente.
- `DRAWDOWN_CRONOLOGICO_POR_MES.csv`: resumo por mês; métricas contínuas e referência local separadas.
- `gerar_dois_compilados.py`: atualiza ambos os PDFs e metadados; valida resultados mensais congelados e continuidade dos meses.

Próximo mês: **agosto/2026**, seleção do Work com 20 pregões de 04 a 31/08 e 43 operações. Work **−387,164995**; nosso resultado ainda não apurado. Há saídas às 18h em 06/08 S61,8 e 25/08 R61,8, e ambiguidade original em 18/08 S38,2. Validar contratos históricos por data na transição Q/V e fazer processamento em lote. Ver `PROXIMO_MES_AGOSTO_2026.json`.

## Entrega e continuidade — instrução mais recente

Não reenviar PDFs ou resultados a cada etapa: salvar e atualizar internamente; entregar os **dois PDFs juntos no final**. Comunicar apenas andamento e instruções necessárias de coleta. O usuário também pediu arquivamento dos arquivos disponíveis e decisões recentes no GitHub. Ver `entregas/arquivo_conversa_20261111/CONTEXTO_E_CONTINUIDADE.md`. Prosseguir com agosto sem reabrir setembro.
