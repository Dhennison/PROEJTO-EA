# Validação local v2.10

Todos os testes abaixo usam C++ e APIs MT5 simuladas. Não são compilação MQL5 nativa, execução do Strategy Tester ou prova de negociação real. Os fixtures numéricos do suporte são sintéticos, não o arquivo B3 para o pregão do usuário.

| Bateria | Resultado |
| --- | --- |
| Novos casos v2.10, adaptadores reais de Experts | 50 verificações, zero falhas |
| Compatibilidade dos casos v2.09 | 47 verificações, zero falhas |
| Regressão integrada herdada | 631 verificações, zero falhas |
| Coordenador operacional herdado | 104 verificações, zero falhas |
| Falhas de escrita/flush/publicação/readback | 10 verificações, zero falhas |
| Runtime do EA fora do Tester | 29 verificações, zero falhas |
| Repetição da regressão | Dois ciclos de 631 sem falhas; fixtures anteriores preservados |
| Reinício de processo | Prazos UTC preservados, sem duplicação e posições independentes |
| Inicialização | Slots inativos inicializados, estado ativo e formato MDOP1 preservados |

As baterias finais executaram com AddressSanitizer, UndefinedBehaviorSanitizer e LeakSanitizer ativos. A primeira tentativa de regressão dentro do sandbox esbarrou na incompatibilidade do LeakSanitizer com ptrace; a execução completa posterior ocorreu fora dessa restrição, mantendo os sanitizadores, e passou. Não foi desabilitada a detecção de vazamentos para obter aprovação.

Os 50 casos novos cobrem: bloqueio fora do Tester, opt-in, otimização recusada, símbolo/data/fuso, conta HEDGE, identidade virtual sem login de corretora, arquivo B3 ausente/incorreto, isolamento e repetição, cinco pendentes independentes, diário confirmado antes do envio, preços fixos, primeiro tick exato em janela parcial, rejeição de 4403, recuperação posterior, ausência de uso de HLC futuro do D1 atual, interrupção manual, respostas incertas, rejeição definitiva, falha de PREPARE, inventário instável, expiração do permit por gravação lenta, mudança do modo durante PREPARE, posições por ticket, SLTP conciliado e cancelamento/fechamento por corte. Um caso não equivale a execução física do respectivo cenário.

Comandos reproduzíveis, a partir da pasta de fontes que contém MQL5 e tests:

```sh
python tests/run_focused_v210.py --sanitize --report-dir /tmp/modelod210_focused
python tests/run_local.py --sanitize --report /tmp/modelod210_regressao.txt
```

Para os casos v2.09, copiar run_focused_v209.py/tests_v209.cpp do suporte anterior para uma pasta de relatório separada e executar run_focused_v209.py --root CAMINHO_DOS_FONTES --sanitize. O suporte v2.10 inclui cópia para reprodução. Executar baterias sequencialmente porque o harness herdado usa uma pasta de fixtures em /tmp.

O ZIP principal só contém MQL5/Experts. O suporte contém os três arquivos de teste novos/atualizados, relatórios, instruções e configuração. Para reproduzir a regressão completa, usar a árvore de fontes existente, mantendo host.cpp e os testes/Script herdados; sobrepor Experts v2.10 e os arquivos tests do suporte. Nenhum Script foi modificado ou reempacotado.

Preservação por SHA-256: núcleo matemático, modelo operacional, arquivo/codec do diário, proteção e todos os 76 arquivos do Script idênticos ao snapshot anterior. Relação em PRESERVACAO_SHA256.json e ARQUIVOS_ALTERADOS.txt. Mudanças em Experts: sete arquivos existentes e três novos.

Ainda pendente: compilação no MetaEditor, qualidade/realidade dos dados da instalação, execução nativa do pregão escolhido, relatório de efeitos/custos e aceitação por operação. Não há .ex5 gerado neste ambiente nem lucro/backtest aprovado. O histórico longo, confronto Work, demo e corte físico durante gravação continuam distintos desta entrega inicial.
