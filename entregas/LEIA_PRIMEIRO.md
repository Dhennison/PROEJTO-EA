# Entrega Modelo D — pacote v2.03

Baixe ModeloD_Integrado_Sem_Transporte_v2_03.zip e substitua a pasta Scripts completa em MQL5. Preserve todos os arquivos em Common/Files. Recompile Test_Integrado_Sem_Transporte.mq5 e execute duas vezes; cada execução deve ter TEST_RUN distinto e resultados 631/0 e 104/0.

Corrige o isolamento da bateria de regressão: o prefixo fixo anterior reutilizava estados e temporários das próprias fixtures. A reprodução local confirmou primeira execução 631/0 e segunda 556/85. A revisão reserva um namespace TEST_ONLY exclusivo por execução, preservando os arquivos anteriores. A reprodução corrigida passou duas vezes, 631/0 em ambas, sem limpar arquivos entre as execuções.

O EA permanece idêntico ao pacote v2.02, com transporte ausente. Esta revisão altera apenas o runner dos testes e empacotamento/documentação. Compilação nativa do runner corrigido e execução MT5 permanecem pendentes. A compilação do EA v2.02 sem avisos também aguarda confirmação do usuário.

Instruções, diagnósticos e evidências no ZIP. A main não foi alterada.
