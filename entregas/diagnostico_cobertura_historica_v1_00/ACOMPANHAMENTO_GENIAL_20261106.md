# Primeiro lote nativo Genial — 06/11/2026

Evidência fornecida pelo usuário durante a execução, sem conexão desta sessão ao terminal.

- Compilação v1.00: zero erros, zero avisos, 1706 ms.
- Início 17:44:15.536, GENIAL_PILOTO, 14 tarefas. Prefixo `HC100_GENIAL_PILOTO_1389845132512126549`.
- D1 anterior de 31/08 para 01/09: n=1, erro=0, às 17:44:16.293. A linha não demonstra sozinha equivalência de OHLC com Work.
- Print inicial: tarefa 1/14, WINV26, 01/09 09:00, zero blocos finalizados. Sem mensagens por chamada na v1.00, o print não permitia distinguir qual consulta estava aguardando.
- Novo print com relógio 17:51:02: tarefa 2/14, WINV26, **02/09 16:10**, 86 blocos conferidos e zero pendentes no pregão corrente. Isso confirma avanço do diagnóstico; os contadores são reiniciados a cada pregão.
- Linha visível de 17:49:44.196: 01/09 concluído como **PENDENTE_OU_DIVERGENTE**, com `TICKS_M1_DIVERGENTES_OU_AUSENTES`, erro_ticks=0 e erro_m1=0. O restante da linha aparece truncado na tela. Não é possível identificar os minutos, contagens ou causa específica apenas pelo print.
- D1 anterior de 01/09 para 02/09: n=1, erro=0, às 17:49:44.448.

Decisão: manter a v1.00 em execução e recolher DIAS.csv, BLOCOS.csv e META.txt ao final. A instrumentação v1.01 foi preparada separadamente, com o mesmo núcleo e plano, mas não é necessária para interromper o lote que já está avançando. Não foram confirmados ainda contrato histórico, ajuste B3 por vencimento, cobertura integral ou execução do EA.
