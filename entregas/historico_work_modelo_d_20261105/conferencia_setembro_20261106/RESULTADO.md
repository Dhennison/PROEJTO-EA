# Setembro de 2026 — contexto e cinco níveis do Modelo D

## O que foi procurado

Foram inventariados os 51 ZIPs disponíveis em `/workspace`, incluindo anexos, pacotes de entregas do projeto, cópias do histórico e suporte do Tester. A relação dos membros CSV/XLSX e eventuais subarquivos está em `resultados/INVENTARIO_ZIPS_DISPONIVEIS.json`. Também foram pesquisados os arquivos de dados já extraídos, a lista de arquivos das branches locais e as abas da planilha-mestre.

O pacote histórico recebido foi aberto: `Pacote_Modelo_D_Historico_20230301_20260921.zip`. Ele contém a planilha de auditoria, as operações de referência, ajustes e fontes auxiliares, mas **não contém o CSV M1 original usado pelo Work em setembro**. Os ZIPs de dados de ticks encontrados cobrem outubro/novembro de 2026, não setembro.

Não foi encontrado outro anexo identificado como ZIP completo do projeto com candles originais adicionais. Se o usuário se refere a um arquivo completo diferente dos pacotes disponíveis nesta sessão, será necessário disponibilizá-lo para concluir essa busca. A ausência nos arquivos acessíveis não demonstra ausência no acervo local do usuário.

## Conferência possível com os dados recebidos

`Book(3).xlsx/Planilha1` contém registros OHLC espaçados em 15 minutos, de 09:00 a 18:15, no recorte necessário. `Jan e Fev 2026.xlsx/Planilha1`, apesar do nome, também contém esse período. As 570 linhas de 31/08 a 21/09/2026 são iguais entre os dois arquivos, inclusive ajustes. Isso é uma concordância entre exportações, não evidência de duas fontes independentes.

Agregamos os registros sem usar preços das operações para reconstruir o contexto: primeira abertura cronológica, máxima das máximas, mínima das mínimas e último fechamento. Para cada data elegível de 01/09 a 21/09 foi utilizado o último pregão anterior presente na base; para 01/09, o contexto é 31/08. Os 15 pregões envolvidos possuem todos os 38 horários da grade M15 observada. Não foram criadas barras para feriados, fins de semana ou períodos ausentes.

Resultados:

- **14 pregões elegíveis**, incluindo **03/09 sem operações**.
- **14 ajustes por data operacional**; o valor repetido nos registros do XLSX coincide com o CSV de ajustes. Nenhum deslocamento para o dia seguinte.
- **70 níveis de entrada calculados**: S38,2, S50, S61,8, R38,2 e R61,8 em cada pregão. Stop e alvo matemáticos calculados junto, sem normalização ao tick.
- Nas **33 operações** presentes na referência D, foram confrontados abertura, linha, entrada, stop, alvo e elegibilidade pelos filtros de abertura/geometria: **zero divergências** à tolerância de 0,00000001 ponto.
- Maior diferença numérica entre cálculo Decimal e valores exportados da planilha: **0,00000000002 ponto**. Trata-se de representação dos números, não ajuste estratégico ou tolerância de preço de mercado.

`resultados/CONTEXTO_E_CINCO_NIVEIS_POR_PREGAO.csv` contém abertura, H/L/C anterior, ajuste, PP, extremos e cinco níveis para todas as 14 datas. `resultados/CONFERENCIA_70_NIVEIS.csv` contém entrada/stop/alvo, filtros e correspondência disponível com o Work.

Exemplo em **21/09/2026**, contexto anterior de **18/09**:

| Campo | Valor matemático |
|---|---:|
| Abertura | 187980 |
| Máxima anterior | 188730 |
| Mínima anterior | 185880 |
| Fechamento anterior | 187135 |
| Ajuste operacional | 186745 |
| S38,2 | 186084,776666… |
| S50 | 185880,833333… |
| S61,8 | 185676,89 |
| R38,2 | 188262,176666… |
| R61,8 | 189199,49 |

Essa coincidência sustenta a compatibilidade do contexto agregado com os preços de referência. **Não comprova separadamente que cada H/L/C anterior é idêntico à base M1 original, nem valida a cronologia dos 70 níveis.** Nos níveis sem operação, o arquivo não oferece um preço de referência independente para confrontar. Em 03/09, tampouco há abertura registrada em uma operação D para confrontar. Preservamos esses limites na classificação dos CSVs.

## Comparação das operações

A conferência dos preços das 33 operações foi realizada. A nova reprodução intradiária de entradas, saídas, motivos e ambiguidades continua pendente do **M1 original**. Não usamos candles M15 para produzir operações que seriam comparadas como M1, nem copiamos os desfechos do Work como saída de um replay. O comparador preparado anteriormente fica disponível para a nova rotina independente.

## Verificação paralela do EA por contrato real

Nos dados recebidos não há contrato real comprovado por data nem exportações de ticks reais para setembro. Os campos ContratoReal, DataFontePublicacao e AjusteAnterior do pacote histórico estão vazios. Há registro histórico da descrição de WIN$N associada a **WINV26** nos documentos de setembro, mas isso não certifica a associação de cada pregão de 01/09 a 21/09. WINV26 é o candidato a conferir; WINZ26, dos testes de outubro/novembro, não pode ser atribuído ao trecho por conveniência.

Não há conexão desta sessão com o terminal MT5 do usuário para consultar diretamente disponibilidade dos ticks ou especificações históricas. A inexistência de uma exportação nos anexos significa **cobertura não verificada**, não zero ticks no servidor. O ensaio do EA depende ainda de validar o adaptador histórico multianual; não foi executado neste trabalho.

## Dados exatos que faltam

| Finalidade | Símbolo | Datas | Granularidade e conteúdo |
|---|---|---|---|
| Reproduzir o Work | Série WIN da exportação original do Work; identificar no cabeçalho se é WINFUT/Profit ou WIN$N/MT5 | **31/08/2026 a 21/09/2026**, pregões completos | **M1**, data/hora e OHLC, inclusive fechamento do pregão; preservar fuso e arquivo bruto |
| Identificar contrato do EA | **WINV26 como candidato**, sujeito à prova de associação por data | **01/09/2026 a 21/09/2026** | Descrição/identificador arquivado do contrato em cada data, ou outra evidência histórica da série e rolagem; especificação do contrato e vínculo com ajuste B3 |
| Contexto diário do contrato real | **Contrato confirmado acima** (inicialmente investigar WINV26) | **31/08/2026 a 21/09/2026** | **D1 e abertura diária**, ou M1 completo que permita conferir a agregação por sessão/fuso |
| Execução histórica do EA | **Contrato confirmado acima** | **01/09/2026 a 21/09/2026**, pregões completos | **Ticks reais**, preferencialmente exportação ALL com tempo em ms, Bid, Ask, Last, volumes e flags; não possui tempo gráfico M1/M5 |

Os símbolos originais não foram fixados por inferência: a documentação refere a série histórica como WIN$N/WINFUT, e o pacote não conserva o cabeçalho do CSV M1 de setembro. Se só for possível fornecer dados de outra série/fonte, primeiro será necessária a comparação de equivalência, sem tratar a substituição como automática.

O primeiro arquivo útil é o ZIP completo, caso ele contenha a base M1 original que não está nos anexos acessíveis. Se não contiver, o CSV M1 original acima destrava o replay teórico; a confirmação de contrato e os ticks destravam a camada executada em outra etapa. Não é necessário reenviar os 877 ajustes já recebidos.

## Reprodução e verificações

```sh
python conferir.py /workspace/historico_modelo_d_20230301_20260921 --saida resultados
python -m unittest -v test_conferir
```

Dois testes sintéticos passaram: preços de um contexto simétrico conhecido e agregação cronológica com detecção de lacuna na grade. São verificações da ferramenta de conferência, não execução nativa ou homologação. Origens e hashes preservados no JSON de resultados. Nenhum código da DEMO, regra de execução, fonte B3 ao vivo ou diário foi alterado.
