# A/B na Genial — controle igual ao realizado na XP

Pacote de instalação do **DiagTicksAB v1.21**, código byte a byte igual ao utilizado no A/B da XP. Sem bibliotecas do Modelo D, transporte de ordens ou alteração de histórico/cache/ajustes. A/B são as duas consultas de dados, não modelos de estratégia: a estratégia permanece Modelo D.

O pacote apenas organiza o fonte no caminho MQL5 para copiar. Nenhuma alteração de lógica foi feita para o servidor da Genial. O fonte já teve compilação/execução nativas na XP; a instalação e compilação nesta Genial ainda precisam ser conferidas.

## Etapa atual: instalar e compilar

1. Extraia o ZIP.
2. No **MT5 da Genial**, abra **Arquivo → Abrir Pasta de Dados**.
3. Cole nessa raiz a pasta **MQL5** recebida, mesclando as pastas. O arquivo deve ficar em:

```text
MQL5/Experts/ModeloD_Diagnostico_Ticks/DiagTicksAB.mq5
```

4. Pressione **F4**, abra o arquivo acima no MetaEditor e compile com **F7**.
5. Envie o resultado da compilação. A coleta A será o passo seguinte.

Não alterar o EA da XP, seus parâmetros/Instância ou os relatórios existentes da Genial. O diagnóstico focal v1.02 concluído pode permanecer removido do gráfico separado; preserve os arquivos gerados por ele.

## Etapa A — terminal Genial, após conferir a compilação

Use um gráfico separado **WINZ26/M5**, para reproduzir as condições efetivamente utilizadas na XP. Anexe DiagTicksAB e configure:

| Entrada | Valor |
|---|---|
| InpSymbol | **WINZ26** |
| InpFrom | **2026.10.30 09:00:00** |
| InpTo | **2026.10.30 09:10:00** |
| InpMaxAttempts | **10** |
| InpTag | **GENIAL_A** |
| InpDumpCsv | **true** |

Não exige AlgoTrading, DLL, WebRequest ou pregão aberto. O terminal precisa estar conectado. O programa consulta o histórico, compara duas leituras, grava os arquivos e remove apenas a si mesmo do gráfico. A remoção automática ao concluir é esperada.

O log informa o STATUS, contagens e caminho dos arquivos. ESTAVEL significa leituras iguais, não integridade total da fita nem que os ticks correspondem a todas as barras. Se a consulta não estabilizar, preservar os retornos e investigar, sem assumir ausência de negócios.

## Etapa B — Tester Genial, depois de conferir A

Abra **Ctrl+R** e use:

| Configuração | Valor |
|---|---|
| Expert | **ModeloD_Diagnostico_Ticks/DiagTicksAB.ex5** |
| Ativo | **WINZ26** |
| Tempo gráfico | **M5** |
| Data inicial | **2026.10.30** |
| Data final | **2026.10.31** |
| Modelagem | **Cada tick baseado em um tick real** |
| Otimização | **Desativada** |
| Para a frente | **Não** |
| Modo visual | **Desativado**, como no controle da XP |
| Latência | **Sem atrasos**, como no controle da XP |

Os parâmetros de entrada serão os mesmos de A, mudando apenas **InpTag=GENIAL_B**. Conferir **InpDumpCsv=true** também no Tester: ele tem parâmetros próprios, que não são herdados automaticamente do gráfico. Depósito/alavancagem não influenciam essa consulta sem ordens; manter a moeda/conta disponibilizada pelo ambiente, sem alterar a conta real para testar.

A janela consultada é [09:00:00,09:10:00), final exclusivo. No Tester, o programa espera o relógio simulado passar do fim da janela antes de consultar; o teste do dia inteiro dá essa oportunidade. Não usar apenas data final igual à data inicial.

Preservar o **Diário do Tester**, especialmente as mensagens de sincronização, divergência e uso/descarte de ticks reais. A opção “ticks reais” da interface não comprova o fluxo entregue; isso será confrontado com os CSVs.

## Arquivos de retorno

Pressione **Windows + R**, cole e pressione Enter:

```text
%APPDATA%\MetaQuotes\Terminal\Common\Files
```

Os arquivos ficam diretamente nessa pasta, não nas subpastas dos diagnósticos HC100 ou F102. Procurar:

- `DiagTicksAB_TERMINAL_GenialInvestimentos-PRD_WINZ26_..._GENIAL_A_....txt`
- O correspondente `..._ALL.csv`.
- Após B, `DiagTicksAB_TESTER_GenialInvestimentos-PRD_WINZ26_..._GENIAL_B_....txt`.
- O correspondente `..._ALL.csv`.

Nome do servidor é sanitizado, portanto pode variar no arquivo se o login usar outra identificação. Enviar os dois arquivos de A quando essa parte terminar; depois os de B e o Diário do Tester. Se houver sufixos numéricos por reexecução, não misturar rodadas.

## O que este controle responde

Na XP, terminal ALL=108005, negócios/TRADE=105342; Tester ALL=36571, negócios/TRADE=0, Last=0 e flags=6. O Diário confirmou descarte dos ticks reais e geração substituta. Este controle verificará se a Genial apresenta o mesmo comportamento **na mesma janela de outubro**, sem concluir antecipadamente que terá o mesmo resultado.

As diferenças encontradas no WINV26 de setembro são outro recorte. Depois deste A/B de controle, configuraremos a checagem no Tester dos trechos de setembro, preservando a comparação com os ticks e M1 já exportados. Não usar o resultado de outubro como prova automática do comportamento dos dois minutos de setembro.

Referência XP: `entregas/diagnostico_ticks_ab_v1_21/resultado_xp_20261105/RESULTADO.md` no repositório. O relatório inicial antigo menciona M1 em uma orientação; o registro nativo e os prints do A/B efetivamente executado confirmam **M5**, que é o período adotado neste controle.
