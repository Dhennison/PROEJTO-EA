# Diagnóstico da inicialização interrompida

Em 08/11/2026 às 14:07, o usuário executou o diagnóstico v1.00 sobre
`MDDP29_1794146086_769098390`, M5, período 29–30/10/2026.

O Diário informa duas barras M5 de 29/10 (09:00 e 09:05), deslocamento do início
para 30/10 para fornecer dados iniciais e recusa por `OnInit` nessa data.
O programa não chegou a registrar eventos OnTick. Não é descarte de ticks
comprovado nessa execução nem rejeição de uma ordem.

A proteção de data permanece inalterada. O complemento cria outra cópia,
preserva a base e acrescenta M1 nativo de 27–28/10, exclusivamente antes da
janela. Exige 200 grupos M5 prévios e compara ticks/barras-alvo antes e depois.
O efeito sobre a data real de início do Tester ainda exige confirmação nativa.
Os metadados M1 e flags já analisados do alvo não são corrigidos neste controle.
