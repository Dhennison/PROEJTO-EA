# EA Modelo D — critérios dos quatro blocos

Requisitos incorporados a partir das observações do usuário em 29/10/2026. Mantêm-se os quatro blocos; tarefas e ensaios internos não são novas etapas de instalação. Não reiniciar o projeto, não modificar a estratégia sem autorização e não habilitar negociação real. Entregas consolidadas; atualizar só Experts quando o script não for afetado.

## 1. Aceitação da integração sem transporte

Implementado: reutilização da matemática, cinco níveis, filtro de abertura, bloqueio geométrico, primeiro toque Last e normalização aprovados; diário único com consumo/intenções/tentativas/respostas e controladores por identificador; conciliação de ordens/deals/posições, parciais, migração de ticket, agendas de proteção, cancelamento e encerramento; retomada do diário. O transporte está ausente. A versão 2.04 acrescenta diagnóstico e inicialização explícita; a v2.05 corrige o marcador Unicode; a v2.06 recupera cache TRADE incompleto por ALL filtrado, aceitando apenas conferência integral com M1. A v2.07 separa falha da API de cálculo, valor inválido, margem indisponível e margem insuficiente, sem expor saldo e sem alterar a decisão.

Testado efetivamente: em 29/10/2026 o usuário confirmou o Script v2.04 nativo 0/0 e duas execuções 631+104 sem falhas. O EA v2.05 nativo 0/0 expôs histórico TRADE incompleto no minuto 10:38; o diagnóstico nativo posterior 0/0 mostrou 1.995 eventos adicionados, incluindo o LAST 173250. O EA v2.06 nativo 0/0 executou de 11:17 a 11:33, retomou o diário e reconstruiu 44 blocos/1.659.934 ticks até 11:33, sem divergência, retry ou bloqueio, com M1 consistente e encerramento correto. A recuperação ALL não foi necessária nessa execução porque o cache já estava completo. Conta vazia, sem toques, posições ou intenções. A v2.07 passou localmente pelo runtime 29/0 e bateria completa; ainda precisa de compilação nativa e execução curta para classificar a margem. Testes locais e nativos são categorias distintas.

Para concluir o registro deste bloco: confirmar o EA v2.07 no MetaEditor e capturar o motivo exato de margem. A execução v2.06 já comprovou retomada, reconstrução contínua, contrato, dados, relógio observado e duas coletas; a execução curta v2.07 não precisa repetir 15 minutos porque não muda lógica. Uma conta sem posições não exercita proteção/fechamento; essas evidências permanecem sintéticas até Tester/demo. A recuperação ALL tem prova local controlada, mas não foi acionada na execução nativa com cache completo.

Políticas atuais de falha (documentação do comportamento existente; não ampliadas pela revisão de logs):
- Dados diários ausentes/inválidos ou desconexão: releitura automática no timer; progresso depende de os dados/conexão tornarem-se válidos. Não estimar dados nem usar ajuste antigo.
- Inventários instáveis, leitura falha ou idade maior que 3 segundos: nova dupla coleta no timer, sem confirmar ações a partir de ausência.
- Relógio: nova avaliação no timer, exigindo âncora de TimeCurrent após início/reinício, continuidade e fuso compatível com o adaptador. Não reiniciar prazos. Salto/regressão não é certificado como hora válida.
- Divergência TICKS_DIVERGEM_M1: bloco reconsultado a cada 30 segundos, com janela total de 600 segundos; sem aprovar ou descartar silenciosamente o bloco.
- Outros erros de reconstrução: até três tentativas; depois o fluxo fica bloqueado na sessão e exige diagnóstico. Reanexação manual não é prova de recuperação automática.
- Conflito com dados congelados: novas entradas permanecem bloqueadas na sessão; não liberar apagando estado ou presumindo que reanexar resolve. Gestão das origens conhecidas continua sendo processada.
- Diário inválido, desaparecido, alterado ou gravação não confirmada: preservação dos arquivos; sem continuação normal nesta execução; retomada exige validação do diário/candidato. Não recriar checkpoints para contornar a falha.
- Resposta incerta/origem não provada: permanece pendente de evidência, sem duplicação por timeout. Se a evidência não chegar, não há promessa de desbloqueio automático.

## 2. EA completo no Strategy Tester

Implementado até agora: núcleo integrado sem transporte, agendas e transições testadas de forma controlada. Transporte comercial não está implementado; ainda não houve execução desta versão no Strategy Tester.

Para concluir: implementar transporte inicialmente restrito ao Tester autorizado, mantendo o MESMO núcleo que seguirá para demo/final; correlacionar pedidos, respostas e efeitos com gravação anterior ao envio. Preparar período explícito, dados, ajustes, calendários e contratos reais; validar identificação/rolagem sem misturar contratos. A janela de horários atualmente revisada até 30/10/2026 e a capacidade de oito sessões precisam ser resolvidas antes de um teste longo. Revisar também limites globais de ordens/deals/posições, por cadeia e tamanho do diário, sem descartar provas necessárias à retomada. Não remover limites sem uma política testada de retenção/arquivamento.

Aceitação: evidências de entradas, parciais, SL/TP fixos, cancelamento por fronteira teórica, consumo, saídas e corte, com cenários de falha e reinício; histórico real validado para o intervalo e ausências explicitadas. Manter ensaios controlados para condições que o Tester não reproduz adequadamente, identificando-as como simuladas. Falta de dados, capacidade saturada ou transporte não validado impedem a conclusão. Não habilitar conta real.

## 3. Comparação com o Work

Não executado. O acervo possui regras, históricos e relatório agregado; na inspeção dos arquivos extraídos não foi localizada uma base tabular de operações do Work (os CSVs identificados são inventários/manifestações de integridade). Antes de solicitar novos dados, conferir os materiais disponíveis e pedir apenas a base/configuração específica ainda necessária ao confronto.

Aceitação: comparação por operação, com data operacional, contrato, nível, preços matemáticos/normalizados/solicitados/executados, horários, volumes, motivos de saída e pontos. Separar resultado teórico e executado; explicitar dados, gaps, sequência intrabar, tick/arredondamento, slippage e custos, sem valores inventados. Documentar divergências e suas causas sem ajustar regras para forçar igualdade. Entregar configurações, procedência/hashes dos dados, rotina e relatório reproduzível. Divergências relevantes sem explicação e datasets/configurações ausentes impedem a conclusão.

## 4. Conta demonstrativa e entrega final

Não executado. Não há comprovação de respostas/execuções reais do servidor para o transporte desta versão e nenhum .ex5 foi produzido neste ambiente.

Aceitação: ambiente demo autorizado e identificado, rejeições/retcodes reais, parciais quando disponíveis ou ensaio controlado explicitado, desconexão, reinício, resposta incerta e ausência de duplicação. Preservar gestão das posições de origem durante falha de dados e mudança do contrato candidato. Demonstrar proteção e corte por timer sem depender de tick no instante, respeitando impedimentos reais de mercado/servidor e sem prometer execução durante indisponibilidade.

Entrega: um .ex5 principal compilado em MetaEditor, fontes completos e instruções consolidadas; cabeçalhos são incorporados ao executável. Documentar coletor/ajuste B3, estado persistente, permissões, diretórios, parâmetros e relógio. Para outro MT5/conta, instalar o executável e dependências e inicializar a identidade correta; nunca copiar o diário de outra conta/servidor/instância como estado válido. Migração do MESMO contexto exige política explícita de transferência/retomada e exclusividade; não é equivalente a iniciar em conta diferente. Estas rotinas precisam ser testadas antes de chamar a entrega final de concluída.

## Registro obrigatório ao encerrar cada bloco

Informar: (1) implementação entregue e versão; (2) comandos/configurações realmente usados; (3) resultados e evidências, separando real, sintético e conta vazia; (4) falhas/limitações e requisitos ainda bloqueantes; (5) critério de aceitação atendido ou não atendido. Um bloco não passa por contagem de checks isolada. Nenhum critério aqui autoriza mudança estratégica ou operação real.
