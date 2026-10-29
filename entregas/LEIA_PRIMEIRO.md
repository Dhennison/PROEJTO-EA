# Entrega Modelo D — v2.06 — 29/10/2026

Pacote atual: ModeloD_Integrado_Sem_Transporte_v2_06.zip. Extraia na pasta principal do projeto e copie **somente** a subpasta `MQL5/Experts/ModeloD_Integrado_Sem_Transporte` para Experts da instalação MT5, preservando `Common/Files`. Compile o EA. Não é necessário substituir, recompilar ou executar o Script integrado.

O EA v2.05 compilou nativamente 0/0 e reconstruiu 983.178 ticks, mas TRADE estava incompleto no minuto 10:38 enquanto M1 já estava completo. O diagnóstico posterior mostrou 1.995 eventos adicionais, incluindo o LAST da máxima ausente. A v2.06 usa ALL somente como recuperação: filtra as mesmas flags de negociação e exige conferência integral com M1. Se continuar divergente, não avança. Não apague arquivos em `Common/Files`.

Depois da compilação, anexe o EA v2.06 ao `WIN$N` M5 com `Instancia=1`, `VolumePorNivel=1`, `IntervaloSegundos=2` e negociação algorítmica desativada. Observe por 15 minutos, remova manualmente e envie a compilação, as linhas de Experts e o novo `ModeloD_Integrado_*.txt`.

Regras, preços, consumo, prazos, Script, formato do diário e transporte não mudaram. A correção passou localmente por runtime 27/0 e pela bateria sanitizada completa 631/0 + 104/0 + falhas 10/0; isso não substitui compilação MQL5. Os critérios dos quatro blocos estão em `CRITERIOS_QUATRO_BLOCOS_20261029.md`.
