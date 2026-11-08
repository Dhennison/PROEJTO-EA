# Tester com contexto — início em 29/10 confirmado

O Diário confirma início efetivo em 29/10 00:00, com 227 barras M5 de contexto.
O motor processou 204027 ticks. O diagnóstico registrou 204027 callbacks e
204027 observações dentro da janela, overflow zero, e exportou histórico/eventos.
Não há mensagens de descarte de ticks reais, ausência ou geração substituta
no Diário recebido. A mensagem normal “generating based on real ticks” e o
resumo “2 bars generated” não são aviso de fallback.

history_exact=false e ontick_exact=false são contra o CSV A bruto, cujos
bits extras já foram removidos no armazenamento do custom. Isso pode explicar
as diferenças, mas ainda não foi provado para os snapshots do Tester/OnTick.
Contagens iguais não comprovam ordem ou identidade de registros: faltam
RESULTADO.txt, ONTICK.csv, TESTER_COPYTICKS.csv e TESTER_M1.csv da pasta
TESTER_1793232000_422453 para análise independente.

A inicialização com contexto funcionou nesta rodada. Não concluir ainda
preservação integral dos eventos, homologação do EA ou backtest do Work.
