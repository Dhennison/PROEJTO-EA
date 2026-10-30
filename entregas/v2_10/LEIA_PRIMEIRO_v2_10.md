# Modelo D v2.10 — primeiro pregão no Strategy Tester

Esta entrega implementa a integração inicial para **30/10/2026, WINZ26, um pregão**, usando o mesmo núcleo de níveis, consumo, diário, conciliação e proteção. Pode executar com o mercado fechado. Não é aprovação de backtest histórico, comparação Work, demo ou versão final do EA.

No gráfico, o padrão continua sem transporte. `ExecutarNoTester=true` fora do Strategy Tester é recusado no OnInit. Todos os caminhos de envio exigem MQL_TESTER, contexto isolado, diário confirmado e inventário conciliado. Não habilite negociação na conta conectada para executar este roteiro.

## 1. Preserve o ajuste usado no pregão

O ZIP não contém um ajuste B3 inventado ou obtido da conta do usuário. É necessário o arquivo real que a sua instalação usou em 30/10:

1. Localize `ajuste_b3.txt` na pasta compartilhada `Terminal\Common\Files`, a mesma origem usada pelo EA observacional.
2. Confira no arquivo: `DataOperacional=2026-10-30`, `DataFonte=2026-10-29`, `Fonte=BVBG.187.01`, `Status=OK` e o par Ajuste/AjusteAnterior do WINZ26.
3. **Copie**, sem mover ou editar o original. No MT5, use Arquivo → Abrir Pasta de Dados e coloque a cópia em `MQL5\Files\ModeloD_Tester_20261030_ajuste_b3.txt`.
4. Não troque datas ou preços para fazer passar. Se o arquivo atual já corresponde a outra sessão, use a cópia histórica correta; se ela não estiver disponível, envie o arquivo que você tem para identificarmos a fonte necessária. O log do EA não substitui o arquivo B3 original.

O nome fixo consta em `#property tester_file`; o MT5 transfere essa cópia para a pasta Files do agente. O adaptador lê o arquivo do agente, sem FILE_COMMON. Saída/ledger do ensaio usam Common/Files com prefixo próprio `MDT210_...`, sem abrir os arquivos operacionais do gráfico. O dado de entrada é carregado/validado no início e mantido fixo nesse ensaio.

## 2. Substituição e compilação

- Guarde a v2.09 já validada. Extraia o ZIP principal sobre a pasta de dados correta do MT5. Ele contém **somente MQL5\Experts**.
- Não altere o Script nem apague arquivos em Common/Files. O programa principal continua em `MQL5\Experts\ModeloD_Integrado_Sem_Transporte\EA_ModeloD_Fluxo_Sem_Ordens.mq5`; os cabeçalhos precisam estar na mesma pasta.
- Prepare o arquivo B3 do item anterior **antes** de compilar. Compile esse MQ5 no MetaEditor e envie o resultado. O teste local em C++ não é compilação MQL5; nenhum .ex5 nativo foi produzido neste ambiente.
- Não anexe esta configuração com `ExecutarNoTester=true` ao gráfico. No gráfico essa opção é bloqueada; o ensaio será iniciado pelo Strategy Tester.

## 3. Configuração do primeiro ensaio

Abra o Strategy Tester com Ctrl+R. Selecione teste único, sem otimização, agente local. Evite agentes remotos/cloud nesta primeira validação para facilitar coleta de arquivos e diagnóstico.

| Campo | Valor |
| --- | --- |
| Expert | ModeloD_Integrado_Sem_Transporte / EA_ModeloD_Fluxo_Sem_Ordens |
| Símbolo | **WINZ26**, contrato efetivo; não WIN$N |
| Período gráfico | M5 |
| Início | 30/10/2026 |
| Fim | 31/10/2026, para abranger integralmente o pregão de 30/10 |
| Modelagem | **Cada tick baseado em ticks reais** |
| Depósito inicial | 1.000.000 BRL, apenas no saldo simulado do Tester |
| Conta simulada | HEDGE; o núcleo recusa substituição silenciosa por netting |
| Atraso | Sem atraso artificial neste primeiro ensaio; registrar a opção usada |
| Visualização | Ativada para a primeira conferência |
| Otimização | Desativada |

Os ticks e D1 de WINZ26 precisam existir para o dia escolhido e os pregões anteriores necessários. O terminal pode baixar dados, por isso internet pode ser necessária mesmo com mercado fechado. Se o Tester informar substituição por ticks gerados/ausência de ticks reais, preserve o log e não classifique o ensaio como validado em ticks reais. O EA não certifica sozinho o modelo escolhido no painel.

Carregue o arquivo `ModeloD_Tester_20261030.set` nos parâmetros ou confira manualmente:

| Parâmetro | Valor |
| --- | --- |
| ExecutarNoTester | true |
| DataTester | 20261030 |
| ContratoTester | WINZ26 |
| FusoServidorTester | -10800 |
| Instancia | 1 |
| VolumePorNivel | 1 |
| IntervaloSegundos | 2 |

O fuso BRT está explicitamente fixado para este conjunto de dados já observado na instalação Genial em 30/10. Não aceitar zero porque TimeGMT e TimeTradeServer podem coincidir no ambiente simulado. Outro servidor/fuso, contrato ou período exige validação própria, sem editar esse valor para contornar erro. O backtest principal posterior com cinco contratos por nível continua distinto deste ensaio inicial com um.

## 4. O que o programa faz e registra

- Usa o relógio do replay para horários e retry, mantendo as durações de APIs medidas em tempo real de CPU/terminal. Não usa hora atual do PC para decidir o dia histórico.
- Busca o primeiro negócio exato desde 09:00. No Tester pode confirmar uma janela parcial positiva, sem M1 ou aproximação, rejeitando qualquer erro/4403 e sem pular janela parcial vazia. Isso permite avaliar o início do pregão sem esperar uma barra inteira. O caminho observacional padrão mantém a política anterior.
- Confere OHLC anterior no contrato explícito e ajuste B3 datado. Não usa H/L/C futuros do D1 corrente para decidir entradas. Reconstrução só consulta ticks até o tempo simulado atual; minutos completos exigem M1.
- Persiste intenção e tentativa antes de OrderSend. Grava resposta sem tratá-la como fill; só novas leituras de ordens/deals/posições confirmam efeitos. Resposta incerta não vira reenvio automático.
- Trabalha as cinco intenções elegíveis sem escolha por proximidade. Fecha pelo ticket correto, com identificador conciliado; SL/TP são os valores fixos aprovados. Cancelamento e proteção conservam as políticas do núcleo.
- Cada execução recebe prefixo novo `MDT210_...`, com identidade virtual explícita do replay. Não reaproveita consumo do gráfico, nem sobrescreve ledger de outro ensaio. Arquivos anteriores são preservados; colisão de nome bloqueia.
- Registra `TESTER_CONFIG`, `TESTER_REQUEST`, `TESTER_RESPONSE`, `TESTER_DEAL`, níveis, posições e `TESTER_END`. `TESTER_DEAL` inclui preços matemáticos/solicitados/executados, volume, identificadores e custos quando disponíveis. Dados não disponíveis são marcados pelo campo próprio. O relatório oficial do MT5 complementa motivos, resultados e qualidade do histórico.

O limite inicial é intencional: um pregão de 2026 revisado. Não ampliar a data, otimizar ou tentar histórico de 2023–2026 com esta configuração. Calendário, grade histórica, capacidade de oito sessões e retenção de inventário/diário precisam ser tratados antes da ampliação. O núcleo puro e o seu guard legado de transporte genérico continuam sem habilitar conta real; o envio novo está no adaptador exclusivo do Tester.

## 5. Ao terminar

Envie:

1. Resultado da compilação no MetaEditor.
2. Configuração efetivamente usada e relatório HTML do Strategy Tester, com histórico de ordens/deals.
3. Diário completo do Tester/agente, inclusive mensagens de dados e retcodes.
4. TXT indicado por `RELATORIO_ABERTO`, com prefixo `MDT210_...`, até o encerramento. Para diagnóstico de persistência, preserve também ledger e eventual .next/.torn do mesmo prefixo; não apague/restaure arquivos.
5. A cópia do ajuste B3 usada, ou seu conteúdo e SHA-256, para fixar a procedência do ensaio.

`TESTER_END` não é certificado de aprovação. Vamos verificar dados reais, aceitação e efeitos de ordens, consumo, preços, SL/TP, cancelamento, corte, resultado e ausência de duplicação. Saldo alto no Tester serve para não bloquear por margem nessa verificação; não é recomendação de capital ou aprovação de risco.

## Pendência de energia

Registrada para segunda, **02/11/2026**, em PENDENCIA_ENERGIA_20261102.md. Finados está marcado sem pregão no calendário B3 cadastrado. Bateria esgotada pode provocar hibernação/desligamento controlado; não garante corte abrupto. Não desativar proteções de energia para obter um PASS. As tentativas com STOP reason=9 ficaram aceitas apenas como retomada observada, e a simulação de escrita parcial permanece evidência local separada.

## Validação desta entrega

Ver RESULTADOS_TESTES.md e relatórios locais anexos. A compilação MQL5 nativa e a execução no Strategy Tester ainda precisam ocorrer na instalação do usuário. Nenhuma operação real foi habilitada ou enviada por este trabalho.
