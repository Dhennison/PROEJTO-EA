# Consultas v1.02 — rodada 1, 08/11 às 17:26

Diário e configuração conferem. TRADE retornou **170544**, não os 128669
negócios da fonte. INFO retornou 75358. Isso não aprova TRADE como caminho
fiel; a composição exata dessas respostas exige os arquivos brutos.

Todas as 15 consultas adicionais declararam duas leituras iguais, erro zero.
O grupo de 09:02:28.680 retornou 3 em ALL e TRADE, contra 5 na fonte.
A janela 09:02 retornou 39425, contra 39427. A janela 09:00 retornou 2874,
contra 2875. A soma das dez consultas foi 204024, contra 204025 na consulta
ALL posterior às modalidades e 204027 na fonte. Não identificar o registro
adicional ausente nem atribuir causa sem alinhar os CSVs.

O motor processou 204027 ticks e o callback guardou 204027 eventos, overflow
zero. O Diário não informa descarte, ausência ou fallback na rodada.
A zeragem da estrutura foi executada pelo fonte v1.02; seu efeito nos flags
não aparece no resumo do Diário e depende de RESULTADO.txt/ONTICK.csv.

Próximo: preservar QUERIES102_1793232000_504466 e repetir UMA vez com os
mesmos parâmetros e símbolo. Depois confrontar os dois retornos e Diários,
sem novo programa e sem alteração de cache, ticks ou barras.
