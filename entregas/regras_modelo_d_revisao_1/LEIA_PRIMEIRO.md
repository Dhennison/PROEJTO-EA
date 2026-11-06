# Regras Modelo D — Revisão 1

Revisão aprovada na conversa após a auditoria do consolidado de 05/11/2026. O original permanece em ../auditoria_regras_20261105; esta edição passa a ser a referência para retomada, parciais e reenvio.

## Alterações aprovadas

- Envio de pendente não consome oportunidade. Primeiro toque consome para novos pedidos, sem fechar posição válida por esse motivo isolado.
- Reconstruir e conferir histórico até o presente antes de novas entradas; carregamento/falha de consulta não equivale a toque e não é, por si só, motivo de cancelamento. Sem dados suficientes, novas entradas aguardam.
- Ordem comprovadamente cancelada, sem execução inclusive parcial e sem toque pode receber novo pedido após reconciliação e validação atual. Não duplicar ordem ativa ou requisição incerta; manter recibos e gerações anteriores.
- Parcial é saldo da mesma ordem: proteger preenchido; não criar outra ordem para completar. Fronteira de stop/alvo ou corte determina cancelamento do saldo e gestão de fechamento. Fill durante cancelamento também deve ser conciliado.
- Posições conhecidas continuam geridas durante a reconstrução; SL/TP fixos, regras B3/contrato/filtros e corte continuam obrigatórios.

## Artefato e validação

PDF revisado: Regras_Modelo_D_Consolidadas_2026-11-05_Revisao_1.pdf, 23 páginas. Capa e página 12 atualizadas; duas páginas finais detalham as decisões. As outras 19 páginas tiveram texto e renderização conferidos como idênticos ao original. Páginas 12 e 23 inspecionadas visualmente. Original preservado com SHA-256. Script gerar_pdf.py permite reproduzir a edição (PyMuPDF e ReportLab).

## Próximo item

**Implementar a Revisão 1 no EA e validar reenvio genérico após cancelamento sem toque/execução.** A v2.13.04 já mantém pendentes durante a reconstrução, mas suas migrações de recuperação são específicas dos incidentes de 05/11. O núcleo ainda consome uma origem aceita que termina e precisa separar término de ordem, primeiro toque e execução, preservando o diário. Não apagar consumo verdadeiro nem ignorar fills parciais. Aprovado no documento não significa implementado/instalado.

Após essa implementação e validação, retomar o item 4: preparar o backtest do período Work. Nenhuma alteração de fonte do EA nesta entrega documental.
