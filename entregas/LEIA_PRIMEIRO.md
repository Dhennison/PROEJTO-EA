# Entrega Modelo D — v2.05 — 29/10/2026

Pacote atual: ModeloD_Integrado_Sem_Transporte_v2_05.zip. Extraia na pasta principal do projeto e copie **somente** a subpasta `MQL5/Experts/ModeloD_Integrado_Sem_Transporte` para Experts da instalação MT5, preservando `Common/Files`. Compile o EA. Não é necessário substituir, recompilar ou executar o Script: na v2.04 ele já compilou com 0 erros/0 avisos e passou duas vezes por 631/0 + 104/0.

O EA v2.04 compilou nativamente com 0 erros/0 avisos, mas encerrou antes do timer com `LOCK_MARKER_WRITE_FAILED`. A v2.05 corrige a comparação entre bytes gravados pelo `FileWriteString` Unicode e caracteres de `StringLen`: agora confirma o marcador relendo seu conteúdo. O marcador e o ledger já criados são preservados e retomados. Não apague arquivos em `Common/Files`.

Depois da compilação, anexe o EA v2.05 ao `WIN$N` M5 com `Instancia=1`, `VolumePorNivel=1`, `IntervaloSegundos=2` e negociação algorítmica desativada. Observe por 15 minutos, remova manualmente e envie a compilação, as linhas de Experts e o novo `ModeloD_Integrado_*.txt`.

Regras, preços, consumo, prazos, Script, formato do diário e transporte não mudaram. A correção passou localmente por 24/0 no runtime direcionado e pela bateria sanitizada completa; isso não substitui compilação MQL5. Os critérios dos quatro blocos estão em `CRITERIOS_QUATRO_BLOCOS_20261029.md`.
