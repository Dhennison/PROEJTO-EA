# R38,2 — cancelamento esclarecido pelos ticks nativos

**Conclusão: o cancelamento após toque e alvo teórico está conforme a regra.**

| Evento | Horário civil do servidor | Registro |
|---|---|---|
| Pendente aceita | 09:01:00.342 | Ordem2586235149, SellLimit168805, SL169180, TP168440 |
| Primeiro toque matemático | 10:30:02.602 | Last168810; linha10909 do CSV; a linha anterior no mesmo ms registra168805 |
| Alvo teórico alcançado depois do toque | 10:30:02.618 | Last168440; linha11018, 16ms após o primeiro toque |
| Cancelamento planejado | 10:30:03 | INTEGRATED_CYCLE, revisão81 |
| Pedido e resposta do cancelamento | 10:30:04 | DEMO_REQUEST kind3 e retcode10009; revisão84 depois concilia cancel_phase6 |

Fonte exportada contém36895 eventos,35868 negócios válidos e ordenados. O alvo matemático é aproximadamente168440,045333, normalizado168440; portanto Last168440 atinge ambos. Nenhum stop foi encontrado após o toque neste recorte. A cotação atinge o alvo antes do cancelamento. Não é necessário inferir a sequência a partir do candle M1.

A ordem foi aceita antes do toque mas não teve preenchimento registrado. Pela regra9.3/Revisão1, ao atingir a fronteira teórica depois do toque, cancelar a pendente sem execução e manter o nível consumido. O saldo efetivamente executado segue somente R61,8: +150pontos/+30BRL na prévia; nenhum ganho hipotético da R38 deve ser adicionado.

O não preenchimento da venda na XP é distinto da decisão de cancelar. O CSV registra como última atualização anterior ao toque Bid168310 às10:30:02.395 e Ask168320 às10:30:02.041; não há atualização de cotação entre o toque e o alvo nas linhas examinadas. Isso não prova fila ou mecanismo interno de execução do simulador. Last tocar não equivale a fill garantido. Não atribuir causalidade definitiva a latência, corretora ou código sem evidência adicional.

Script conferir_ticks.py reproduz a sequência. CSV original preservado; nenhuma alteração no código do EA em função deste evento.
