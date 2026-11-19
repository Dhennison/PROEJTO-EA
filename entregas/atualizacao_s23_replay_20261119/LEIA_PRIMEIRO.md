# Atualização S23,6% stop200/alvo500 — 19/11/2026

Recebido `Novas datas.xlsx`, 10.448.531 bytes. Original preservado em `/workspace/dados_brutos_modelo_d/replay_profit/Novas_datas_S23_20261119.xlsx`. SHA256, ID Sediment e cópia local documentados no manifesto para restauração. Arquivo não foi regravado nem filtrado.

Cinco abas correspondem aos cinco minutos pedidos. OHLC e soma das quantidades conferem exatamente. Ordem original decrescente foi invertida integralmente, sem deduplicação. Só o S23,6% N089 stop200/alvo500 foi atualizado; os resultados e parâmetros originais, as outras receitas e os estudos anteriores permanecem preservados.

Resolução:
- 11/09/2025 WINV25: stop -200.
- 13/02/2026 WING26: stop -200.
- 17/03/2026 WINJ26: stop -200.
- 11/05/2026 WINM26: stop -200.
- 31/07/2026 WINQ26: stop -200.

Usuário informou leilão em 31/07 e retorno às 12h34min07s. Primeiro negócio registrado em 12:34:07.958, preço 177.470. A ausência anterior não foi considerada falha de captura, não foram inventados ticks ou candles. A validação exata OHLC/quantidade confirmou a janela.

Resultado atualizado: 2024 +8.935 fechado; 2025 +3.885 fechado; 2026 jan-out +95 a+3.595 com cinco operações pendentes. Total +12.915 a+16.415. DD diário contínuo de 4.915 em ambos os envelopes, sem reinício mensal/anual e com pico inicial zero. 386 operações. Pontos brutos sem custos/slippage. Faixas não são probabilidades nem lucro fechado. Nenhuma variante promovida.

As três combinações já publicadas foram recalculadas apenas substituindo a contribuição S23 N089 nos cinco dias. Os outros níveis/receitas não foram reapurados nem declarados fechados. Suas pendências, somadas às cinco restantes S23, continuam explicitadas. O estudo 50/250 dos cinco níveis permanece em stand-by.

Ainda faltam somente a restituição de acesso aos brutos Cedro já recebidos das cinco datas abaixo para fechar este S23:
- 11/08/2026 WINQ26 09:03–09:04: WIN_20260811_parte001.zip e WIN_20260811_parte002.zip.
- 24/08/2026 WINV26 09:00–09:01: WIN_20260824_parte001.zip e WIN_20260824_parte002.zip.
- 04/09/2026 WINV26 09:30–09:31: WIN_20260904_parte001.zip e WIN_20260904_parte002.zip.
- 11/09/2026 WINV26 09:05–09:06: WIN_20260911_parte001.zip e WIN_20260911_parte002.zip.
- 25/09/2026 WINV26 09:03–09:04: WIN_20260925_parte001.zip e WIN_20260925_parte002.zip.

Os 132 ZIPs agosto-outubro foram enviados e os recibos confirmam hashes. Não é falta de envio do usuário. Neste ambiente só 16 foram restaurados. Os dez acima, tamanhos, hashes e recibos constam no CSV copiado. O usuário pediu identificação exata para reenviar os arquivos existentes; não solicitar nova captura, extração ou compra de histórico.

Verificação independente: cinco operações em 20 execuções combinando trajetórias OHLC fora do Replay e reversão de empates no mesmo milissegundo. Todas confirmam os stops. Saídas posteriores ao minuto fornecido podem ser determinadas por M1; em PROVAS_SAIDAS.csv horários M1 têm apenas precisão de minuto e preços são referências da trajetória, não negócios reais identificados. Resultados diários e DD conferidos por somas escalares independentes.

Reprodução: conferir_janelas.py; atualizar.py; verificar.py; relatorio.py. Dependem dos caches/fontes das entregas anteriores; não é pacote autônomo sem o acervo. Cache novo dos cinco minutos: /workspace/work/replay_s23_20261119/auditoria.pickle; os próximos estudos devem incorporar estes minutos validados antes de marcar as mesmas ambiguidades. Não é auditoria integral tick a tick do período.
