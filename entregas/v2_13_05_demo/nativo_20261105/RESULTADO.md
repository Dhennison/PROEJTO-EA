# Conferência nativa inicial do relatório v2.13.05

Arquivos recebidos após inicialização às 23:10 de 05/11/2026, XP DEMO.
CSV com 30 colunas, cinco níveis e total. Chaves e colunas válidas.

| Nível | Entrada executada | Saída executada | Motivo nativo | Pontos | BRL DEMO |
|---|---:|---:|---|---:|---:|
| S50 | 169070 | 168695 | 4 = SL | -375 | -75 |
| S61,8 | 168935 | 169070 | 5 = TP | +135 | +27 |
| Total | | | | **-240** | **-48** |

Preços conferidos contra os quatro deals do relatório anterior, não apenas contra a soma do próprio CSV. Duas operações encerradas, uma positiva e uma negativa, acerto 50%, residual zero. Slippage de entrada em relação ao preço solicitado e saída em relação aos SL/TP normalizados: zero nos dois casos. Comissão, swap e fee reportados iguais a zero nesta amostra; não extrapolar custos futuros.

S38,2/R38,2: tocadas sem execução. R61,8: sem execução. Resultados teóricos Work corretamente vazios e identificados como pendentes; resultado observado não é reconstituição de todas as oportunidades teóricas do dia.

Diário reaberto na revisão 60, ALL_CHAINS_RECONCILED, sem intenções ou unresolved. CSV publicado. Bloqueio de relógio aguardando referência recente do broker; não comprova fuso incorreto. Nenhum novo pedido neste trecho.

**Confirmado nativamente:** compilação/inicialização, recuperação do diário e geração/conteúdo do CSV para operações já encerradas. **Não exercitado neste trecho:** reenvio geral, arquivamento na virada, novas parciais, sessão especial ou fechamento de posição aberta no corte.
