# Genial — piloto histórico de setembro concluído

Fonte: log Experts fornecido pelo usuário, execução nativa v1.00, GENIAL_PILOTO, WINV26 candidato, 14 pregões de 01 a 21/09/2026.

Início em **06/11/2026 17:44:15.536** e HC100_END em **18:09:55.699**, duração **25 minutos e 40,163 segundos**. As 14 tarefas foram concluídas. Não houve travamento definitivo do lote.

Todos os 14 contextos D1 anteriores tiveram retorno n=1 e erro=0. Isso demonstra recuperação de uma barra diária anterior em cada data; a igualdade com Work deve ser lida no DIAS.csv, não presumida apenas pela contagem.

Todos os 14 resumos diários ficaram como **PENDENTE_OU_DIVERGENTE**, motivo **TICKS_M1_DIVERGENTES_OU_AUSENTES**, com erro_ticks=0/erro_m1=0 na condição registrada. O resumo guarda a última pendência do dia; não comprova que todas as chamadas e tentativas anteriores tiveram erro zero.

O resultado não permite afirmar ausência de ticks na Genial, nem divergência durante todo o pregão, nem causa específica. Uma única janela não aprovada já impede aprovação integral do dia. Prints anteriores mostraram muitos blocos conferidos; é necessário distinguir essas janelas aproveitáveis das pendentes.

As pendências de IDENTIFICACAO_HISTORICA, VINCULO_AJUSTE_B3 e FUSO_HISTORICO são eixos separados, mantidos no plano com campos ainda não comprovados. Não são três falhas adicionais das consultas e não devem ser removidas por conveniência.

## Próxima ação antes de ampliar ou repetir

Receber os três arquivos com prefixo **HC100_GENIAL_PILOTO_1389845132512126549** em `Terminal/Common/Files/ModeloD_Historico_Cobertura/`:

- `_DIAS.csv`: quantidades conferidas/pendentes, negócios estáveis e comparação de contexto/abertura por data.
- `_BLOCOS.csv`: horários exatos e motivos das janelas aprovadas e pendentes.
- `_META.txt`: ambiente, servidor e configuração.

Não é necessário repetir o lote ou instalar a instrumentação v1.01 para analisar os dados já gerados. Não ampliar ainda aos 877 pregões. O A/B na Genial (30/10/2026 09:00–09:10 WINZ26, DiagTicksAB v1.21) continua pendente e é outro teste.
