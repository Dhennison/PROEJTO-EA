# Recuperação XP — divergência no minuto 14:41 de 06/11

Fonte: mensagens do usuário de14:42:01.872 a15:02:05.908 e capturas comparando o horário mostrado na Observação do Mercado com o relógio do PC. Nenhuma mudança de parâmetros, diário, relógio ou código realizada nesta análise.

## Motivo demonstrado do bloqueio de dados

Minuto civil do servidor14:41:00–14:41:59.999 (1793976060000–1793976119999).

| Campo | Negócios TRADE / ALL filtrado | Barra M1 |
|---|---:|---:|
| Abertura |170495|170495|
| Máxima |170520|170520|
| Mínima |**170440**|**170435**|
| Fechamento |170520|170520|

TRADE retorna2106 negócios; ALL2286 eventos, dos quais2106 passam no critério de negócio. API erro0; assinaturas estáveis. As25 consultas mantêm a diferença de5pontos. Esse é o motivo explícito TICKS_DIVERGEM_M1, não uma demonstração de que houve erro de fuso.

Recuperação existente: reconsulta do mesmo bloco a cada30s durante os primeiros600s; depois sondagens de120s. Não aprova nem pula o bloco. Novas entradas e reenvios que dependem de cobertura atual ficam bloqueados. A rotina operacional de conciliação, gestão das origens e corte é separada dessa aquisição; execução concreta exige relógio, inventário, conexão e permissões válidos. Histórico incompleto por si só não cancela/consome as pendentes na política vigente.

## Observação de horários

XP: captura mostra Observação do Mercado14:54:11 e PC14:54:42 (~31s). Genial:14:55:10 e PC14:55:11 (~1s). Capturas não são simultâneas entre corretoras. O horário mostrado pode refletir atualização das cotações; não certifica atraso exato do feed, fuso, relógio do servidor ou o relógio usado internamente pelo corte. O trecho colado não contém diagnóstico RELOGIO.

A diferença de exibição é relevante para investigação, mas não comprova causa da mínima divergente, que permaneceu igual por mais de20min após a primeira consulta. Não relacionar retroativamente à falta de fill R38 como causa demonstrada.

## Próxima evidência necessária

Exportar no terminal XP os ticks nativos ALL e as barras M1 do WINZ26 de06/11/2026 14:40:00–14:43:00. Conferir se existe negócio válido Last170435 no minuto14:41; conferir flags, milissegundos, limites do minuto, extremos de Bid/Ask e modo de gráfico do símbolo quando necessário. Ausência de um negócio isolado não pode ser presumida apenas pela barra; a barra também pode ter origem/construção divergente.

Não alterar relógio/fuso, apagar cache, remover o EA ou aprovar o bloco por tolerância automática de5pontos. Primeiro comparar os dados recebidos. Não certificada ainda a causa da divergência nem a recuperação do bloco.
