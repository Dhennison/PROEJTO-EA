# Padrão de versão visível — preferência do usuário

Solicitado após a compilação nativa da v2.13.05: mostrar claramente o número
completo da entrega nas propriedades do EA, sem depender de interpretar
2.135 como 2.13.05.

Nas próximas entregas:

- Exibir a versão completa no nome apresentado e/ou na descrição das
  propriedades, além de START, comentário do gráfico e documentação.
- Manter o formato numérico aceito pelo #property version do MQL5; não
  introduzir uma versão inválida com dois pontos só para imitar o nome.
- Conferir consistência entre versão de entrega, descrição, gráfico e logs.
- Preservar os caminhos/contextos de persistência. Mudança de identificação
  visual não pode trocar Instância, recriar diário ou rearmar níveis.
- O usuário pediu aplicação nas próximas atualizações; nenhuma nova troca
  de executável foi solicitada apenas por essa apresentação.
