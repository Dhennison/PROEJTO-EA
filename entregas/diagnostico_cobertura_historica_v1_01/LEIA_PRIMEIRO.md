# Diagnóstico de cobertura histórica Modelo D v1.01

Um único programa, um plano com os **877 pregões de 01/03/2023 a 21/09/2026**. Os parâmetros iniciais selecionam apenas **01 a 21/09/2026**, 14 pregões. Depois da conferência do piloto, o mesmo programa permite consultar o período inteiro, sem rodar manualmente dia por dia.

**Somente leitura de dados de mercado. Não contém transporte de ordens, bibliotecas do Modelo D, acesso ao diário do EA ou alteração de ajustes.** Grava seus próprios relatórios em uma pasta separada. `SymbolSelect` pode adicionar os candidatos à Observação do Mercado; não remove símbolos.

## Instalar e compilar na XP

1. Extraia o ZIP em uma pasta temporária.
2. No MT5 da XP, abra **Arquivo → Abrir Pasta de Dados**. Cole ali a pasta **MQL5** que veio no ZIP, mesclando as pastas. A pasta de destino é a raiz que contém MQL5, e não o interior dela. O resultado deve ser:

```text
MQL5/Experts/ModeloD_Historico_Diagnostico/Diagnostico_Cobertura_Historica.mq5
MQL5/Experts/ModeloD_Historico_Diagnostico/HC_Core.mqh
MQL5/Files/PLANO_HC100_877.csv
```

3. Abra o MetaEditor com **F4**, abra o `.mq5` acima e compile com **F7**. O plano CSV precisa estar em MQL5/Files também; ele foi declarado como arquivo de dados do Tester. Envie o resultado da compilação antes de considerar a versão validada nativamente.
4. Abra **um gráfico separado**, por exemplo outro WINZ26/M5, e coloque o `Diagnostico_Cobertura_Historica` nele. Ele consulta os símbolos do plano, não depende do símbolo ou tempo gráfico desse gráfico. Preserve o gráfico e a Instância do EA DEMO que já estão rodando.
5. Mantenha os parâmetros abaixo e clique OK. Não precisa mudar o AlgoTrading da DEMO, habilitar DLLs ou configurar WebRequest.

## Primeiro teste: setembro

| Parâmetro | Valor |
|---|---|
| InpDe | **2026.09.01 00:00:00** |
| InpAte | **2026.09.21 00:00:00** |
| InpIdentificador | **XP_PILOTO** |
| InpSimbolo | **vazio** |
| InpConsultarAlternativo | **false** |
| InpBlocoMinutos | **5** |
| InpTentativasPorBloco | **4** |
| InpReconsultarPendencias | **false** |

O primeiro candidato consultado nesse trecho é **WINV26**. O diagnóstico não o declara contrato histórico confirmado. A descrição atual do símbolo será registrada apenas como metadado atual, sem ser usada como prova de identificação passada.

O programa consulta uma janela por etapa, usando temporizador, sem esperar novos ticks no gráfico. Cada janela precisa de duas leituras consecutivas iguais em todos os campos; depois compara o OHLC dos negócios com as barras M1 do mesmo símbolo/minuto. Uma chamada da API pode demorar enquanto o terminal baixa dados; não há prazo fixo de conclusão e não se deve interpretar espera de rede como conclusão ou ausência de dados. A consulta usa memória por bloco, não acumula todos os ticks de vários anos. Os pedidos históricos consomem rede/recursos do terminal; o programa não garante impacto zero sobre outras consultas.

As consultas usam horários civis do servidor, **sem conversão automática de fuso**. A equivalência histórica com BRT permanece pendente no plano até ser conferida. Abertura posterior às 09h é permitida: o diagnóstico não exige negócio exatamente às 09h.

## Arquivos para enviar ao final

Espere aparecer **HC100_END** no Experts e **CONCLUÍDO** no gráfico. Isso significa que as consultas terminaram, não que todos os dados foram aprovados. Os arquivos são fechados ao concluir.

Os resultados ficam em:

```text
Terminal/Common/Files/ModeloD_Historico_Cobertura/
```

O caminho completo será impresso no Experts em **HC100_RELATORIOS**. Para o identificador XP_PILOTO haverá três arquivos com o mesmo prefixo `HC100_XP_PILOTO_<chave>`:

- **DIAS.csv**: resultado por data e símbolo consultado, contagens, contexto D1 anterior, comparação com Work e pendências separadas.
- **BLOCOS.csv**: janelas recuperadas, vazias, divergentes ou com erro; inclui limites em milissegundos, quantidade de leituras e códigos de erro. Mostra exatamente em que trecho a recuperação falhou.
- **META.txt**: ambiente, servidor, horários atuais, plano/configuração e limites de interpretação.

Compacte **esses três arquivos em um ZIP** e envie. Não é preciso enviar os diários operacionais da DEMO nem executar os scripts Python. `resumir_relatorios.py` é uma ferramenta adicional para analisar os retornos, caso desejado.

O diagnóstico registra contagens e conferências; **não exporta a fita integral de ticks**. Depois de identificar os dias/símbolos aproveitáveis, a exportação/importação dos ticks escolhidos será parte da preparação do backtest do EA.

## Como ler as três verificações separadas

### 1. Disponibilidade de dados

`TicksEstado=ESTAVEL_COM_NEGOCIOS_M1_COMPATIVEL` exige negócios com Last positivo/finito e flags de negócio, duas leituras iguais por janela, ausência de erros e compatibilidade por minuto com M1. Campos de Bid/Ask/Last/volume_real não finitos e retornos fora da janela ou de ordem são rejeitados. Last carregado sem flag de negócio não é contado como negócio. O teste não arredonda doubles para decidir igualdade. Não rejeita um tick apenas por Bid maior que Ask; essa anomalia não vira prova automática da causa de uma falha.

Se houver barras M1 com negócios mas sem ticks correspondentes, ticks sem barras, divergência de OHLC, erros de consulta ou ausência de estabilidade, o relatório conserva a pendência. Barras e ticks simultaneamente ausentes não provam que não houve negociação; **integridade total não é certificada**, mesmo que as janelas disponíveis confiram. Ausência de negócios observados não é classificada como ausência definitiva no servidor.

`ModoGrafico` deve ser Last para comparar diretamente os negócios com OHLC M1. Se o modo for Bid, a comparação de Last com M1 permanece pendente, em vez de afirmar uma divergência da base de negócios.

`CandidatoTecnicoSemVinculos=SIM_SUJEITO_A_VINCULOS` indica que as consultas conferiram e que abertura/HLC anterior coincidem com Work. É uma lista para selecionar o primeiro ensaio, **não aprovação de contrato/ajuste, cobertura integral ou execução do EA**. Contagens do resumo incluem somente janelas estáveis compatíveis; janelas pendentes ficam detalhadas em BLOCOS.csv. A primeira e a última marca em ms também se referem a esses negócios aceitos.

### 2. Identificação histórica do contrato

O plano contém **dois candidatos por data**, calculados por calendário nominal de vencimentos bimestrais. O segundo é o vencimento seguinte, para investigar rolagens. Esse calendário não certifica feriados/exceções nem a rolagem por liquidez. Não é usado para alterar o roteamento da DEMO. Consultar ambos ajuda a encontrar dados, mas não garante que um deles seja a associação histórica correta da série contínua.

`ContratoConfirmado` e `EvidenciaContrato` estão vazios. Nem ticks disponíveis, nem uma descrição atual de WIN$N, nem coincidência de OHLC substituem a prova histórica. Os relatórios permitirão identificar candidatos; o vínculo será revisado por data ou por intervalos de rolagem documentados, sem exigir que o usuário rode cada pregão separadamente.

### 3. Vínculo do ajuste

Os **877 ajustes do Work** estão incluídos por data operacional, sem deslocamento para o dia seguinte. Eles são referência, não certificação B3 por vencimento. `AjusteB3` e `EvidenciaB3` permanecem vazios. A consulta de mercado não baixa boletins B3 nem inventa DataFontePublicacao/AjusteAnterior.

Mesmo que a disponibilidade de ticks esteja boa, o relatório mantém **DadosPrimeiroPiloto=PENDENTE** enquanto faltar identificação histórica, vínculo do ajuste ou confirmação do fuso/contexto. Após revisão documental, o plano pode receber os vínculos declarados e o diagnóstico poderá classificar um candidato ao piloto conforme essas declarações. Não preencha esses campos apenas para retirar o aviso. A suficiência dos comprovantes, o ajuste anterior/data fonte e o adaptador do EA ainda exigem conferência externa.

## Retomar após interrupção ou repetir falhas

- Mantendo os mesmos parâmetros e plano, o programa lê DIAS.csv e pula as tarefas já concluídas. **Um pregão interrompido é reconsultado desde o início.** O registro de conclusão tem checksum e só é escrito/flushado depois do pregão; os blocos antigos de uma rodada incompleta não se tornam cobertura aprovada.
- Se uma consulta terminou pendente, use **InpReconsultarPendencias=true** para tentar novamente. Serão reconsultadas tarefas sem ticks/M1 aprovados ou sem D1 anterior recuperado. Diferença persistente de série/ajuste não será resolvida por repetir indefinidamente.
- BLOCOS.csv pode conter várias rodadas do mesmo pregão. A coluna **Rodada** associa os blocos à linha de DIAS.csv. A última linha válida de cada Task é o resultado vigente.
- Se houver uma linha final incompleta/checksum inválido após queda abrupta durante escrita, o programa para e conserva o arquivo. Use outro InpIdentificador e envie o relatório anterior para revisão. Não apague os diários da DEMO. O checksum detecta corrupção acidental, não é assinatura de autoria.
- Mudar período, símbolos, tamanho do bloco, tentativas, opção de alternativo ou plano gera outro prefixo de arquivos; não mistura configurações. O nome do identificador deve usar letras/números, até 24 caracteres.

## Ampliar ao período inteiro, depois de conferir o piloto

No mesmo programa:

| Parâmetro | Valor para o lote completo |
|---|---|
| InpDe | **2023.03.01 00:00:00** |
| InpAte | **2026.09.21 00:00:00** |
| InpIdentificador | **XP_COMPLETO** |
| InpSimbolo | **vazio** |
| InpConsultarAlternativo | **true** |
| InpBlocoMinutos | **15**, depois de conferir o piloto com blocos de 5 |
| Demais | manter inicialmente |

Serão consultados os 877 pregões, com dois candidatos por data: até 1754 tarefas. Não há ação manual por dia. Pode demorar bastante e pode haver símbolos antigos não disponibilizados pela corretora. O relatório distingue isso de um erro estratégico. Também é possível dividir em intervalos anuais/mensais sem precisar de novo código; cada configuração tem seus próprios relatórios.

## Terminal e Tester

Comece no **terminal XP**. O mesmo diagnóstico identifica ambiente TERMINAL/TESTER nos metadados e mantém arquivos separados. Um teste no Tester será configurado depois para o mesmo símbolo/janela, conferindo o Diário por descarte/substituição dos ticks reais. A interface “ticks reais” não basta: a ocorrência anterior da XP exige comparar o que foi efetivamente entregue.

Este diagnóstico não envia ordens nem é o backtest do EA. O ensaio histórico do EA ainda precisará de adaptação, ticks exportados/importados e vínculos revisados. As 32 ambiguidades do Work permanecem como STOP FIRST na referência; no ensaio com ticks reais vale a cronologia observada e a execução nativa, com estado indeterminado quando os dados não resolverem a ordem.

## Referência preservada e validação desta entrega

`REFERENCIA_CONFERIDA_SETEMBRO/` preserva a tabela dos 14 pregões e as 33 operações do Work, conforme solicitado. A reprodução teórica integral já foi concluída separadamente, sem divergências nos 877 pregões.

Validação local: **27 verificações do núcleo extraído do MQL em C++ com tipos/APIs simulados, ASan/UBSan, e sete testes Python de plano/protocolo/checksum, todos aprovados**. Foram também conferidas as declarações globais `input` e a ausência de transporte de ordens. Esses testes não substituem a compilação nativa.

**MetaEditor/MT5 não estão disponíveis neste ambiente: a compilação e execução nativas desta v1.01 permanecem pendentes.** Por isso entregamos os fontes para compilar; não há EX5 pré-compilado nem alegação de teste nativo já realizado.
