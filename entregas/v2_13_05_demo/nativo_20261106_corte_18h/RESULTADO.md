# XP DEMO v2.13.05 — corte de 06/11/2026

Conferência do log enviado pelo usuário, gravação de 17,5 segundos e print da aba Negociação. Horários abaixo são os timestamps impressos no log do terminal; não são timestamps independentes do servidor para cada cancelamento.

## Resultado confirmado

O corte foi registrado em **18:00:01.966**, evento TIMER_DEADLINE, revisão 89. Em **18:00:02.099** houve diagnóstico HORARIO_DE_CORTE para ENTRADA_0 a ENTRADA_4. As únicas três solicitações de transporte do recorte foram cancelamentos `kind=3`, dos suportes S38,2/S50/S61,8. Cada uma recebeu `api_ok=1`, `retcode=10009` e teve o efeito conciliado posteriormente (`cancel_phase=6`). A conclusão não depende apenas do retorno 10009.

| Nível | Ordem | Solicitação no log | Resposta no log | Cancelamento conciliado no log |
|---|---:|---|---|---|
| S38,2 | 2586234621 | 18:00:02.188 | 18:00:02.352 | **18:00:02.438** |
| S50 | 2586234717 | 18:00:02.524 | 18:00:02.817 | **18:00:02.903** |
| S61,8 | 2586234914 | 18:00:02.999 | 18:00:03.175 | **18:00:03.272** |

Em **18:00:03.884**, revisão 99: ALL_CHAINS_RECONCILED, entry_intents=0, SLTP_intents=0, cancel_intents=0, close_intents=0 e unresolved=0. O print posterior da aba Negociação está vazio, sem posições ou pendentes visíveis, margem livre igual ao capital líquido e lucro flutuante zero.

O acionamento foi no ciclo do timer após o horário; os registros não mostram cancelamento instantâneo exatamente 18:00:00.000. O fluxo levou até cerca de 3,3 segundos após o horário para conciliar os três cancelamentos neste ambiente. Não foram observadas rejeições ou repetições desses pedidos no trecho enviado.

## Estado específico por nível

| Nível | Toque | Execução | Estado no encerramento |
|---|---|---|---|
| S38,2 | Sem toque observado no trecho conferido até 18h | Sem execução observada no material | Pendente cancelada por horário, conciliada 18:00:02.438 |
| S50 | Sem toque observado no trecho conferido até 18h | Sem execução observada no material | Pendente cancelada por horário, conciliada 18:00:02.903 |
| S61,8 | Sem toque observado no trecho conferido até 18h | Sem execução observada no material | Pendente cancelada por horário, conciliada 18:00:03.272 |
| R38,2 | Com toque, primeiro_msc=1793961002602 | Sem execução, conforme análise anterior | Cancelamento anterior ao corte, já conciliado; não houve novo pedido para essa ordem neste recorte |
| R61,8 | Com toque, primeiro_msc=1793964001579 | Uma entrada e uma saída, residual zero | Posição encerrada antes do corte; não houve fechamento de posição às 18h |

`consumed=1;cutoff=1` nos níveis sem toque representa bloqueio ao terminar o pregão. Isso não é prova de toque ou execução e não muda a classificação dos suportes para “tocados”. O coletor preserva explicitamente INTEGRIDADE_TOTAL_NAO_CERTIFICADA; os estados de toque são observacionais.

A R61,8 estava registrada com entered=1, exited=1, residual=0, ticket=0. SL_observed=0 e TP_observed=0 nesse registro de posição já encerrada não demonstram falta de proteção em posição aberta.

## Limites e pendências

**Confirmados neste corte:** cancelamento das três pendentes remanescentes, bloqueio das cinco entradas pelo horário, conciliação sem pendências e aba Negociação vazia no print posterior.

**Não exercitado:** fechamento de uma posição ainda aberta no corte, pois não havia tal posição. Essa parte da homologação continua pendente; não declarar a homologação integral concluída por este resultado.

Em 18:01:01.870 apareceu COBERTURA_ATUAL=JANELA_ATUAL_INVALIDA_OU_DEFASADA. Esse evento é posterior aos cancelamentos já conciliados e não os desfaz. O recorte não mostra novas solicitações de entrada após o corte. A causa/continuidade dessa janela atual defasada não pode ser determinada por uma única linha.

A gravação confirma a sequência visual em torno de 17:59:56, 18:00:04 e 18:00:12. Em um trecho, o texto do indicador de ajuste substitui o texto de status do EA e depois o status do EA reaparece; a pendência visual já conhecida permanece, sem evidência neste material de interferência nos cancelamentos.

O saldo no print é 999982,00 BRL. Esse saldo isolado não fornece o resultado diário por nível. A R61,8 +150 pontos/+30 BRL já tinha sido demonstrada pelos negócios recebidos anteriormente; para consolidar o fechamento financeiro deste dia, é necessário o CSV de pontos atualizado após o corte. Não somar o alvo teórico da R38,2 como resultado executado.

## Evidências preservadas

- `EXPERTS_1756_1801.txt`: texto original recebido.
- `GRAVACAO_CORTE_20261106.mp4`: gravação original recebida.
- Três frames extraídos para inspeção visual.
- `CONFERENCIA_CORTE.json`: pedidos, respostas, primeiras conciliações de cada suporte, estados finais e limites.
- `SHA256SUMS.json`: hashes dos arquivos preservados.

Nenhuma alteração foi feita no código ou no diário da DEMO. O diagnóstico de cobertura na Genial continua sendo outra frente, somente de leitura.
