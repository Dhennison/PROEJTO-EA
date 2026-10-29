# Diagnóstico do encerramento na inicialização — v2.04 para v2.05

Evidência nativa recebida em 29/10/2026, WIN$N M5:

```text
2026.10.29 10:20:09.518  RELATORIO_ABERTO;...ModeloD_Integrado_A155063S47656E69616C496E76657374696D656E746F732D505244I1_1793269209_778493734.txt
2026.10.29 10:20:09.520  LOCK_MARKER_WRITE_FAILED
2026.10.29 10:20:09.521  STOP;reason=8;transport=ABSENT
2026.10.29 10:20:09.521  RELATORIO_FECHADO;...ModeloD_Integrado_A155063S47656E69616C496E76657374696D656E746F732D505244I1_1793269209_778493734.txt
```

O TXT contém apenas RELATORIO_ABERTO e STOP;reason=8. O timer não iniciou e não houve ciclo de dados, reconstrução de ticks ou conciliação operacional.

## Causa

O lock foi aberto como arquivo binário no formato Unicode padrão do MQL5. FileWriteString retorna quantidade de bytes gravados; StringLen retorna quantidade de caracteres. A v2.04 exigia igualdade entre essas unidades. Assim, uma gravação Unicode completa podia ser classificada como falha.

## Correção v2.05

- exige seek e flush sem erro;
- exige retorno de gravação maior que zero;
- volta ao início, relê o arquivo e compara o conteúdo completo com o marcador esperado;
- aceita o marcador Unicode válido deixado pela v2.04;
- mantém bloqueio para arquivo vazio, ilegível ou com conteúdo diferente;
- preserva o ledger e todos os arquivos em Common\Files.

Não houve alteração de estratégia, formato do ledger, Script, transporte, cálculos, preços ou prazos. A validação local simula a contagem Unicode de bytes e verifica escrita, retomada e conteúdo; não substitui compilação e execução nativas no MetaEditor/MT5.
