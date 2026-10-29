# Entrega Modelo D — v2.07 — 29/10/2026

Pacote atual: ModeloD_Integrado_Sem_Transporte_v2_07.zip. Extraia na pasta principal do projeto e copie **somente** a subpasta `MQL5/Experts/ModeloD_Integrado_Sem_Transporte` para Experts da instalação MT5, preservando `Common/Files`. Compile o EA. Não é necessário substituir, recompilar ou executar o Script integrado.

O EA v2.06 compilou nativamente 0/0 e executou por 15 minutos sem divergência, retry ou bloqueio: 44 blocos, 1.659.934 ticks e M1 consistente até 11:33. O relatório agrupou falha de cálculo e margem insuficiente. A v2.07 apenas separa esses motivos, sem alterar a decisão nem registrar saldo. Não apague arquivos em `Common/Files`.

Depois da compilação, anexe o EA v2.07 ao `WIN$N` M5 com os parâmetros padrão e negociação algorítmica desativada. Basta aguardar aparecer o motivo exato `ENTRADA_0..4` e remover manualmente; a lógica v2.06 já foi observada por 15 minutos. Envie compilação, essas linhas e o novo TXT.

Regras, preços, consumo, prazos, Script, formato do diário e transporte não mudaram. A correção passou localmente por runtime 29/0 e bateria sanitizada completa 631/0 + 104/0 + falhas 10/0; isso não substitui compilação MQL5. Os critérios dos quatro blocos estão em `CRITERIOS_QUATRO_BLOCOS_20261029.md`.
