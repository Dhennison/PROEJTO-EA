# Genial — verificação dos arquivos DIAS, BLOCOS e META

Execução original em 06/11/2026, servidor **GenialInvestimentos-PRD**, ambiente **TERMINAL**, diagnóstico v1.00, candidato consultado WINV26, período de 01 a 21/09/2026.

Os três arquivos originais estão preservados em `arquivos_recebidos/`. O código `analisar_retornos.py` reproduz os cruzamentos abaixo. A análise não consulta a corretora nem executa o Tester.

## Integridade dos relatórios e configuração

- Checksums das 14 linhas de conclusão diária válidos; nenhuma rodada incompleta foi contabilizada.
- Hash textual do plano nativo **677286351814178028**, igual ao plano local entregue. As 14 datas correspondem ao recorte Work.
- 1582 linhas de blocos, sem repetição de janela dentro da rodada. Cada dia tem 113 blocos contíguos de 09:00 a 18:25, com final exclusivo.
- Quantidades de janelas, ticks ALL e negócios nas janelas aprovadas reconciliadas entre DIAS.csv e BLOCOS.csv.
- Todos os retornos finais registrados em BLOCOS.csv têm ErroTicks=0 e ErroM1=0. Isso não informa erros eventualmente ocorridos durante as leituras de sincronização anteriores.

## Dados efetivamente recuperados

| Medida | Resultado |
|---|---:|
| Pregões consultados | 14 |
| Janelas de cinco minutos | 1582 |
| Janelas conferidas | **1559 (98,5461%)** |
| Janelas pendentes | **23** |
| Ticks ALL nas janelas conferidas | 47498317 |
| Ticks válidos de negócio nas janelas conferidas | **36951132** |
| Ticks ALL nas leituras finais das janelas pendentes | 311656 |
| Ticks de negócio nas leituras finais das janelas pendentes | 239947 |
| Minutos com M1 mas sem negócios correspondentes detectados | 0 |
| Minutos com negócios mas sem M1 correspondente detectados | 0 |
| Minutos com OHLC dos negócios diferente do M1 | **24** |

Portanto, **não houve falta generalizada de histórico ou ausência de ticks nos 14 dias**. A pendência registrada é diferença de OHLC em 24 minutos, distribuídos em 23 janelas. O diagnóstico exige que todas as janelas confiram para aprovar integralmente o dia; uma divergência já basta para PENDENTE_OU_DIVERGENTE.

As contagens são snapshots finais de cada janela disjunta, não soma de todas as releituras. Houve 1558 janelas encerradas na segunda leitura, uma na terceira e 23 na quarta. As janelas pendentes continuaram divergentes na leitura final registrada; os CSVs não guardam todos os snapshots intermediários.

Os negócios são registros classificados pelo critério Last positivo/finito e flags de negócio. Não são identificadores únicos de negócios da bolsa nem execuções da nossa conta. Ausência simultânea de ticks e barras em um minuto pode passar como ausência estrutural de registros; isso não certifica integridade total de mercado.

## Contexto diário e associação com o Work

Nos **14 pregões**, foram conferidos exatamente contra a referência original recebida:

1. Abertura pelos primeiros negócios nas janelas aceitas.
2. Máxima, mínima e fechamento D1 do pregão anterior.
3. Valor de AjusteWork carregado no plano.

Todos esses valores coincidem. ModoGrafico=1 (Last) nos 14 dias: a conferência dos negócios com M1 é apropriada para esse modo de construção.

Isso **corrobora empiricamente WINV26** como candidato associado ao trecho do Work; não é prova documental de rolagem ou identificação histórica da série em cada data. AjusteWork coincidir com o plano não certifica, por si só, o ajuste oficial B3 desse vencimento. Os campos de vínculo histórico/B3 continuam vazios e pendentes por desenho do plano, não por falha das consultas de ticks.

META registra TimeTradeServer=06/11 17:44:15 e TimeGMT=20:44:15: diferença **−3 horas no instante da inicialização**, compatível com BRT. Isso não certifica retrospectivamente todos os timestamps históricos; não há evidência aqui para recomendar mudança no relógio/fuso do PC ou servidor.

## Onde estão as divergências

Em **todos os 14 dias**, a janela **18:20–18:25** tem divergência. Os CSVs v1.00 não informam qual dos cinco minutos nem quais valores O/H/L/C diferiram. Não podemos chamar automaticamente de divergência em 18:24 ou atribuir a ajuste/leilão/cache sem dados adicionais.

As outras nove janelas pendentes são anteriores ao corte das 18h:

| Data | Janelas pendentes antes das 18h, final exclusivo |
|---|---|
| 02/09 | 16:10–16:15 |
| 03/09 | 11:15–11:20; 11:20–11:25; 16:10–16:15 |
| 09/09 | 13:25–13:30 |
| 14/09 | 11:30–11:35 |
| 17/09 | 10:10–10:15; 13:05–13:10 |
| 18/09 | 12:40–12:45 |

Há **24 minutos divergentes nas 23 janelas pendentes**. Em 03/09 são cinco minutos nas quatro janelas, mas não é possível atribuir o minuto adicional a uma janela específica apenas com esses arquivos. Assim, tampouco podemos separar exatamente os 24 minutos entre antes/depois do corte: sabemos a contagem das janelas, não a de minutos divergentes em cada janela.

Antes das 18h, **1503 de 1512 janelas conferiram (99,4048%)**. Depois do corte, 56 de 70 conferiram. Essa separação ajuda a priorizar o ensaio, mas não autoriza apagar divergências após 18h: o fechamento diário compõe o contexto posterior e o Tester pode rejeitar ticks em função de inconsistências no restante da sessão.

## Candidatos a um primeiro ensaio

Sem janela pendente **antes das 18h**: **01, 04, 08, 10, 11, 15, 16 e 21/09/2026**. São oito candidatos técnicos para investigar primeiro; todos ainda têm a divergência final em 18:20–18:25 e vínculos documentais pendentes.

Com divergências também antes das 18h: **02, 03, 09, 14, 17 e 18/09/2026**. Esses seis dias exigem conferência focal das janelas listadas antes de considerá-los para um ensaio homogêneo.

**Nenhum dia está certificado para execução do EA/Tester por esta análise.** O teste foi no terminal; a entrega dos ticks pelo Tester ainda não foi comparada. O A/B pendente na Genial permanece outro teste: repetir a configuração da XP, DiagTicksAB v1.21, WINZ26 em 30/10/2026 09:00–09:10. Não chamar esta coleta de aprovação daquele A/B.

## Próximo passo recomendado

Não ampliar ainda aos 877 pregões e não repetir o lote inteiro de setembro. A próxima consulta deve registrar o OHLC dos ticks e o OHLC M1 **por minuto nas janelas já identificadas**, com releituras e exportação dos registros envolvidos. Começar por duas amostras cobre as duas classes observadas:

- **WINV26, 01/09/2026 18:20–18:25:** divergência recorrente após o corte.
- **WINV26, 02/09/2026 16:10–16:15:** divergência durante o período operacional.

Essa coleta focal permitirá distinguir diferença de preço, instante de borda, atualização posterior do histórico ou outra causa — hipóteses ainda não provadas. O arquivo `analise_completa/JANELAS_PENDENTES_PARA_CONSULTA_FOCAL.csv` lista todas as 23 janelas, com contagens e limites exatos. A v1.01 acrescenta visibilidade das chamadas, mas não grava por si só os OHLC divergentes de cada minuto; apenas trocar para v1.01 não é a solução demonstrada para essas diferenças.

Em paralelo, o vínculo contrato/ajuste deve ser revisado com evidências históricas, e o primeiro ensaio no Tester precisa comprovar entrega de ticks reais. A reprodução teórica do Work continua conferida; não houve mudança de parâmetros ou flexibilização de abertura/validação para esconder diferenças.
