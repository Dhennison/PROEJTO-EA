# Diagnóstico v1.01 — mostrar a consulta e cada releitura

O print de 06/11 na Genial mostra tarefa 1/14, WINV26, 01/09 09:00, sem blocos finalizados. A v1.00 só mostra o resultado final de um bloco; uma chamada síncrona a CopyTicksRange ou CopyRates pode aguardar dados sem detalhar a etapa no gráfico. Isso não prova travamento, ausência de ticks ou erro de contrato. É uma limitação de visibilidade da v1.00.

A v1.01 mostra no gráfico a etapa **CONSULTANDO_TICKS_ALL**, **CONSULTANDO_M1** ou **CONSULTANDO_D1_ANTERIOR**, intervalo e número da leitura. No Experts, registra:

- `HC101_API_BEGIN`: início da chamada.
- `HC101_API_END`: retorno, quantidade, erro e duração em ms.
- `HC101_RELEITURA`: por que foi necessária outra leitura.
- `HC101_BLOCO`: bloco concluído ou pendente.

Essas mensagens permitem distinguir consulta em andamento de retorno vazio, erro de sincronização, ausência de estabilidade ou divergência M1. Uma mensagem BEGIN sem END informa qual chamada ainda não retornou; ela não estabelece sozinha uma causa no servidor.

## Instalar

**Atualização durante o acompanhamento:** o lote da v1.00 na Genial avançou para 02/09/2026, com 86 blocos conferidos até 16:10 no print seguinte. Não há indicação para interromper esse lote em andamento. A v1.01 fica preparada para uma consulta posterior que necessite de mais detalhes de progresso. O resultado pendente de 01/09 precisa ser analisado nos CSVs, sem atribuir causa ao servidor por esse print.

1. Extraia o ZIP novo e copie a pasta **MQL5** para a raiz da Pasta de Dados do **MT5 da Genial**, mesclando as pastas. São os mesmos caminhos da v1.00.
2. Reabra o arquivo atualizado `Diagnostico_Cobertura_Historica.mq5` no MetaEditor e compile com **F7**. A v1.00 já foi compilada na Genial com zero erros/avisos; a compilação nativa da v1.01 ainda precisa ser confirmada.
3. Recoloque **somente o diagnóstico** no gráfico separado, se necessário. Preserve o EA DEMO e seus arquivos. Se o terminal estiver aguardando uma chamada de histórico, a remoção/reinicialização do diagnóstico pode aguardar essa chamada retornar; não é necessário forçar o fechamento dos terminais.
4. Confira os mesmos parâmetros: **01 a 21/09/2026**, **GENIAL_PILOTO**, símbolo vazio, alternativo false, blocos de 5 minutos, quatro tentativas e reconsultar pendências false.
5. Envie as primeiras mensagens `HC101_API_BEGIN`, `HC101_API_END` e `HC101_RELEITURA` que aparecerem, ou eventual falha.

Núcleo de validação, plano dos 877 pregões, consultas solicitadas, limites de tentativas e critérios de aceite são os mesmos. Os prefixos `HC100_...`, o esquema de CSV e a chave da consulta foram preservados para retomar as tarefas já concluídas. O pregão interrompido continua sendo reconsultado desde o início. As novas mensagens detalhadas ficam no Experts; DIAS.csv/BLOCOS.csv/META.txt continuam sendo os três retornos do lote.

Esta atualização não resolve nem mascara indisponibilidade de dados. Não foi confirmado por que a primeira consulta está demorando. Ela permite obter essa evidência sem alterar regras ou enviar ordens.
