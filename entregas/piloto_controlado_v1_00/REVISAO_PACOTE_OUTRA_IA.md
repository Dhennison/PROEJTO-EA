# Revisão e integração do pacote recebido

Foi revisado `ModeloD_Piloto_Alimentacao_v1.zip`, fornecido pelo usuário em 08/11/2026. Os fontes foram lidos; não foram executados nem compilados no MT5. O arquivo recebido permanece localmente, sem republicação automática.

O pacote em desenvolvimento foi preservado. Ideias úteis incorporadas:

- Importação em lotes, ampliando o limite para não dividir registros do mesmo milissegundo. Nosso importador exige contagem e ausência de erro em cada lote e só escreve num símbolo recém-criado.
- Construção **opcional** de M1 derivado dos negócios da fonte. Padrão `false`; cada execução cria outro símbolo. O M1 automático é registrado antes; depois da construção há nova releitura dos ticks para detectar mudanças.
- Histograma de flags, exemplos dos primeiros registros diferentes e cobertura dos milissegundos observados em callbacks, além da comparação de quantidade, ordem e subsequência.

Decisões preservadas na versão integrada:

- **Comparação exata em oito campos**, sem tolerância de preço ou arredondamento para duas casas. O CSV original usa notação científica com 17 algarismos significativos, não duas casas. Hash é resumo; igualdade é campo a campo. O hash legado de sete campos é usado somente para validar a fonte conhecida; os novos hashes incluem também `time`.
- `OnTick` apenas lê o tick atual e copia para memória previamente alocada. Sem resize, hash ou escrita por callback. Buffer e falhas são monitorados. As observações são exportadas por padrão.
- Subsequência ordenada consome ocorrências: duas observações idênticas não reutilizam indefinidamente uma única linha da fonte. Um teste de correspondência com “alguma linha do mesmo ms” sozinho não verifica multiplicidade nem ordem dentro do grupo.
- Tester obrigatório, símbolo personalizado com prefixo do piloto e data fixa. O diagnóstico não fica registrando ticks ao vivo se anexado por engano no terminal.
- Fonte validada antes de criar o símbolo. O importador não reutiliza nem substitui dados de um símbolo personalizado preexistente.
- CSV estrito e números validados antes da conversão; campos extras ou truncados são recusados. `time` é derivado de `time_msc` na fonte, mas os retornos preservam o `time` efetivamente recebido.
- Releitura estável exige duas respostas válidas iguais, não apenas hash arredondado igual. Fonte/histórico e callbacks permanecem provas separadas.
- Finalização por `OnTester`, com fallback em `OnDeinit`, inclusive se o usuário interromper. Metadados distinguem esse encerramento de um fim normal. A inspeção do Diário segue obrigatória.

Perfil opcional de M1: OHLC pelos Last com flags de negócio; tick_volume = quantidade desses registros; real_volume = soma de seu volume inteiro. É escolha de construção declarada, não barra oficial nem prova de fita completa. Não importar barras nativas ou do Work por cima para ocultar incompatibilidades.

O código do EA Modelo D e seus relatórios operacionais não foram alterados. O diagnóstico não envia ordens. A sondagem amostral de datas antigas continua incluída no mesmo pacote, como tarefa independente.
