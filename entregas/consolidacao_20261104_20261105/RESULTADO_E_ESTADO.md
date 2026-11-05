# Modelo D — consolidação de 04 e 05/11/2026

Atualizado após o corte de 05/11, horário de Brasília. Registro técnico dos resultados, decisões e pendências; não é uma transcrição integral do chat. Fontes originais recebidas e fontes de código mantidas no repositório. Conta real não liberada.

## Resultado nativo do corte em 05/11

Ambiente: XP XPMT5-DEMO, Hedge, BRL; EA v2.13.04 no gráfico WIN$N, contrato operacional WINZ26, Instância 1, volume 1. Compilação nativa comunicada pelo usuário: zero erros e zero avisos, 6.721 ms. EA inicializado às 14:09:02, diário validado na revisão 50; revisão final observada 60.

| Evento | Horário Experts | Evidência |
|---|---|---|
| Corte marcado nos cinco níveis | 18:00:00.609 | TIMER_DEADLINE, revisão 56, cutoff=1 |
| Preparação durável e pedido de cancelamento | 18:00:00.769 | DEMO_PREPARE_BEFORE_SEND, revisão 58; kind=3, order=2585837772, serial=3 |
| Resposta da corretora | 18:00:00.921 | api_ok=1, retcode=10009, error=0 |
| Cancelamento conciliado no histórico | 18:00:02.615 | revisão 60, R61 cancel_phase=6 |
| Conciliação final | 18:00:02.616 | ALL_CHAINS_RECONCILED; todas as intenções e unresolved=0 |

O print de Histórico fornecido pelo usuário mostra a ordem A5 cancelada às 18:00:01. São marcações de fontes/relógios diferentes; o pedido do EA foi emitido ainda no primeiro segundo após o corte. Não inferir latência exata da corretora a partir da diferença entre esses relógios.

A R61 permaneceu pendente entre sua recuperação e o corte; o relatório contém apenas um pedido de entrada A5 e um pedido de cancelamento dessa ordem. Nenhum pedido de entrada após 18h. Ambas as posições conhecidas terminaram com entered=exited=1 e residual=0. Os bloqueios CHAIN_ORIGEM_NAO_COMPROVADA no envio e BOUND_ORDER_MISSING_FROM_HISTORY no cancelamento foram transitórios; a coleta seguinte conciliou os recibos.

**Conclusão:** cancelamento nativo da pendente e bloqueio de entradas no corte aprovados nesta execução. Não havia posição aberta às 18h: o fechamento nativo de uma posição no corte não foi exercitado hoje. A cobertura de dados reportada como defasada às 18:01:02 ocorreu após a janela e após o cancelamento já conciliado; não desfaz a evidência de corte. Não representa homologação completa de todos os cenários nem autorização de conta real.

## Operações executadas em 05/11

| Nível | Posição de origem | Entrada | Saída | Pontos | Resultado DEMO BRL |
|---|---|---:|---:|---:|---:|
| S50 | 2585252213 | 169070 | 168695 | -375 | -75 |
| S61,8 | 2585252263 | 168935 | 169070 | +135 | +27 |
| Total | | | | **-240** | **-48** |

Deals de entrada/saída: 1874510005, 1874519661, 1874521782, 1874532574. Custos reportados nos quatro deals iguais a zero. O print de Histórico identifica as saídas como [sl 168695] e [tp 169070], compatíveis com os preços e os recibos. R61,8 sem execução; S38,2 e R38,2 mantidas consumidas por primeiro toque anterior. Este resultado é o do EA na DEMO, com as indisponibilidades e correções ocorridas durante o dia; não é uma reconstituição teórica integral de todas as oportunidades.

## Evolução e evidências de 04/11

- v2.11: correções de compilação, execução e pendentes/referência; fonte importada do pregão 30/10 permitiu duas operações, -370 e +515 pontos, saldo +145 pontos. Relatórios originais preservados em evidencias. Isso não é o saldo da DEMO de 05/11 nem comparação Work.
- v2.12: cenário sintético exclusivo do Tester exerceu corte com posição aberta e pendentes; fonte e resultados em ../v2_12_corte. Não confundir com execução nativa de corretora.
- XP DEMO Hedge instalada; indicador Ajuste_Oficial_B3_v2_20 compilado e ativo. Ajuste para 05/11: 169650, anterior 167551, fonte 04/11, status OK.
- Histórico nativo no Tester voltou a apresentar abertura sem negócios. v2.11.01 adicionou consulta diagnóstica TRADE/ALL; não foi autorizada substituição de Last por Ask nem relaxamento de primeiro negócio.
- DiagTicksAB v1.21 corrigiu buffer, precisão e validação de números no diagnóstico; compilação nativa 0/0. Fontes e validações em ../diagnostico_ticks_ab_v1_21.

## Evolução e correções de 05/11

1. Relógio voltou a avançar às 08:55; observação do usuário. EA aguardou validação de relógio e conexão.
2. Script de leitura da grade XP mostrou sessão genérica raw 0..86400. v2.13.01 aceitou essa disponibilidade mantendo a janela do Modelo D e primeiro negócio a partir das 09h. Não exigimos negócio exatamente às 09h.
3. Recibo de entrada ainda não vinculado antes de BuildFrame provocou cancelamentos indevidos. v2.13.02 corrigiu a ordem de conciliação; foi compilada, mas o usuário esperou a versão com recuperação para anexar.
4. v2.13.03 acrescentou recuperação específica, auditada e persistente dos cancelamentos originais. R38 já tocada não foi rearmada; após reconstrução, S50/S61/R61 receberam novos pedidos A3. S38 também já tocada permaneceu consumida.
5. As operações S50/S61 executaram e encerraram na corretora enquanto o notebook esteve suspenso.
6. Retomada às 13:12: leitura por blocos ainda incompleta foi interpretada como invalidação da pendente R61 A3, ticket 2585252290. Cancelamento indevido identificado e reproduzido.
7. v2.13.04 removeu essa inferência: histórico incompleto não prova motivo de cancelamento. Manteve invalidação comprovada, precedência estrita e corte. Acrescentou recuperação exata do incidente 2585252290, sem reset genérico.
8. Às 14:10:06, REPAIR21304_CONFIRMADO; novo pedido A5 2585837772 conciliado às 14:10:08. Resultados das duas operações preservados. Sem novo cancelamento até o corte.
9. Corte das 18h cumprido conforme a tabela acima. Fontes v2.13.04 e 151 verificações locais ASan/UBSan em ../v2_13_04_demo; APIs simuladas não substituem esta evidência nativa.

## Diagnóstico A/B XP concluído

Janela comum: 30/10/2026 09:00–09:10, WINZ26. A/B designa Terminal/Tester; a estratégia é Modelo D.

- A Terminal: ALL=108005, TRADE=105342; primeiro negócio 09:00:43.103, Last=170910.
- B Tester: ALL=36571, TRADE=0; todos flags=6 e Last=0.
- Diário: descartou ticks reais em 565/565 barras M1 e usou geração. Explica a ausência de negócios no Tester; a causa do descarte permanece não comprovada.
- Bid maior que Ask em algumas linhas, flags adicionais e cache são hipóteses; não causas demonstradas. Leilão prolongado e ausência de negócios na base do Terminal foram descartados pela evidência.
- Resultado, fontes, CSVs e ZIP: ../diagnostico_ticks_ab_v1_21/resultado_xp_20261105 e pacote_resultado_xp_20261105.
- Símbolo personalizado com fita real importada é o caminho já demonstrado para o ensaio histórico. Sem inventar ticks nem mudar regras para contornar geração do Tester.

## Referência Work recebida e conferida

../historico_work_modelo_d_20261105 contém o pacote e PDF originais, guia, extrações D e auditoria local. Só Modelo D utilizado. 01/03/2023–21/09/2026: 877 pregões (112 sem operação), 1877 operações, 124337,758661 pontos, DD diário 4780,240329 pontos. Ajustes presentes em todas as 877 datas. Somatórios e curva conferidos; CSV versus XLSX e PDF confrontados. Isso valida a referência, não é novo backtest do EA.

Work usa candles, preços teóricos e STOP FIRST; EA usa ticks e preços executáveis. Corte histórico 17:45 de 13/03 a 03/11/2023; demais datas 18h. Ajustes já associados à data operacional, sem deslocar um dia. Contratos reais e AjusteAnterior não informados na referência: não preencher por suposição.

## Pendências e próxima ação

1. **Prioridade atual: backtest histórico para Work.** Inventariar cobertura por data/contrato/ticks, validar associação com ajustes e OHLC, adaptar calendário multianual e ensaio atualmente fixo em 30/10/WINZ26; começar por lote pequeno e depois ampliar. Preservar universo de 877 dias, custos e camadas teórica/executada separados. Sem fita real não certificar cobertura nem substituir por ticks gerados.
2. Acompanhamento DEMO em pregão contínuo com a versão corrigida; comprovar preservação e eventual execução nativa com proteção. O dia de hoje inclui hibernações e migrações e não substitui um pregão contínuo da mesma versão. Não repetir artificialmente cenários já comprovados sem necessidade.
3. Fechamento nativo de posição aberta no corte: ainda não observado; cenário sintético já disponível. Aguardar condição útil na DEMO, sem criar operação alheia às regras para forçar o teste.
4. A/B Genial pendente antes de usar o ambiente real; diagnóstico de descarte upstream pode prosseguir sem bloquear a rota importada.
5. Revisão para produção: capacidade de sessões/posições/recibos, calendário além de 2026, vencimentos/rolagens/sessões especiais, persistência e pacote final. Falha visual só será retomada se reaparecer.
6. Conta real não homologada nem autorizada por este registro. A tecnologia DMA4 citada pelo usuário não prova compatibilidade de dados ou autorização operacional.

## Continuidade operacional

Manter mesma conta/servidor/Instância 1 e o diário existente; não apagar consumos. v2.13.04 aceita as migrações 2.13.03 e 2.13.04; versões anteriores não devem ser usadas para reabrir o diário migrado. Notebook/MT5/rede precisam estar ativos para a gestão pelo EA; stops/targets e pendentes aceitos permanecem sujeitos à corretora durante indisponibilidade.

## Revisão posterior: PDF consolidado de regras

Após este fechamento, o usuário forneceu Regras_Modelo_D_Consolidadas_2026-11-05.pdf. A [auditoria de 32 itens](../auditoria_regras_20261105/AUDITORIA_REGRAS_V21304.md) identificou conflito entre a manutenção de pendentes na v2.13.04 e o cancelamento por histórico incompleto exigido expressamente em 9.7. O êxito técnico do reenvio/corte permanece evidência do comportamento observado, mas não certifica conformidade dessa política com o PDF. Também foram identificadas lacunas de relatórios, retenção, calendário e freeze. Código do EA não alterado nesta revisão.
