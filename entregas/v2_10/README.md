# Modelo D v2.10 — integração inicial no Strategy Tester

O primeiro ensaio é um único pregão auditável: **30/10/2026, WINZ26, ticks reais, volume 1 por nível, sem otimização**. O transporte novo é exclusivo do Strategy Tester; no gráfico permanece ausente. Compilação nativa e execução no Tester ainda pendentes do usuário.

- [ZIP somente MQL5/Experts](../ModeloD_Integrado_Tester_v2_10.zip)
- [Instruções completas, preparação do ajuste B3 e parâmetros](LEIA_PRIMEIRO_v2_10.md)
- [Configuração .set](ModeloD_Tester_20261030.set)
- [Resultados locais e reprodução](RESULTADOS_TESTES.md)
- [Arquivos alterados](ARQUIVOS_ALTERADOS.txt)
- [Patch de Experts sobre v2.09](PATCH_EXPERTS_v2_09_para_v2_10.diff)
- [Suporte de documentação e testes](ModeloD_v2_10_Documentacao_e_Testes.zip)
- [SHA-256 dos pacotes](SHA256SUMS.txt)
- [Pendência de energia para segunda, 02/11](PENDENCIA_ENERGIA_20261102.md)

É necessário preservar o arquivo B3 real de DataFonte=2026-10-29 e DataOperacional=2026-10-30, copiando-o para MQL5/Files com o nome indicado nas instruções. Nenhum dado de mercado foi fabricado ou embutido no ZIP. Se esse arquivo histórico não estiver disponível, identificar a fonte antes de tentar o ensaio; não alterar datas/preços para contornar o bloqueio.

Testes locais finais com sanitizadores: 50 novos/0, compatibilidade v2.09 47/0, regressão 631/0, operacional 104/0, falhas 10/0 e runtime 29/0; repetição, reinício e inicialização aprovados. São APIs simuladas, não provas nativas ou resultado financeiro. Script e núcleo preservados por SHA-256. Histórico longo, confronto Work, demo e gravação interrompida real continuam distintos desta entrega.
