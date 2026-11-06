"""Preserve original illustrated pages; update 9.6/9.7 and append approved clarification."""
from pathlib import Path
import io,json,hashlib
import fitz
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
root=Path(__file__).resolve().parent
original=root.parent/'auditoria_regras_20261105/Regras_Modelo_D_Consolidadas_2026-11-05.pdf'
out=root/'Regras_Modelo_D_Consolidadas_2026-11-05_Revisao_1.pdf'
doc=fitz.open(original);assert len(doc)==21
page=doc[11]
partial=('Execução parcial: proteger o volume preenchido; o saldo permanece na MESMA ordem enquanto válido, antes das 18h e sem fronteira teórica de stop/alvo alcançada. Se o saldo preencher, proteger o adicional nos mesmos SL/TP fixos. Se stop/alvo ocorrer, cancelar o saldo e conferir o encerramento do executado. Às 18h, cancelar saldo e fechar exposição. Fill durante cancelamento também deve ser conciliado e encerrado quando devido. Não criar outra ordem para completar ou reentrar. Ver detalhamento na Revisão 1 ao final.')
resume=('Reconstruir ordens, posições, deals, diário e Last desde a abertura até o presente. Novas entradas exigem conferência completa e nível sem toque. Carregamento ou falha de consulta não consome a oportunidade nem cancela, por si só, pendente aceita. Cancelamento confirmado, sem execução nem toque, permite novo pedido após todas as validações; pedido anterior incerto/ativo impede duplicação. Primeiro toque bloqueia novos pedidos, mas não encerra posição válida nem impede o saldo da mesma ordem. Proteger posições conhecidas durante a reconstrução; fronteira após execução ou corte exige tratar fechamento. Após 18h, somente encerramento. Ver condições completas na Revisão 1 ao final.')
rects=[(fitz.Rect(49,179,548,253),partial),(fitz.Rect(49,290,548,410),resume)]
for rect,text in rects:page.add_redact_annot(rect,fill=(1,1,1))
page.apply_redactions(images=0,graphics=0)
used=[]
for rect,text in rects:
 for size in [10,9.7,9.5,9.2,9]:
  # Test layout on a temporary page, avoiding partial writes on failed layout.
  trial=fitz.open();test=trial.new_page(width=page.rect.width,height=page.rect.height)
  fit=test.insert_textbox(rect,text,fontname='helv',fontsize=size,lineheight=1.15)
  trial.close()
  if fit>=0:break
 else:raise ValueError('Text does not fit')
 assert page.insert_textbox(rect,text,fontname='helv',fontsize=size,lineheight=1.15,color=(0.08,0.13,0.17))>=0
 used.append(size)
cover=doc[0];note=fitz.Rect(50,617,545,771)
assert cover.insert_textbox(note,'REVISÃO 1 — DECISÕES APROVADAS NESTA CONVERSA\n\nOs itens 9.6 (parciais) e 9.7 (retomada) foram atualizados na página 12. O detalhamento vigente está nas páginas 22 e 23.\n\nEnviar uma pendente não consome a oportunidade. Cancelamento comprovado, sem execução nem primeiro toque, permite novo pedido elegível. Reconstrução do histórico não é, por si só, motivo de consumo ou cancelamento.\n\nEsta revisão documenta regras aprovadas. A implementação geral de reenvio e sua validação no EA ainda estão pendentes.',fontname='helv',fontsize=10,lineheight=1.2,color=(0.04,0.22,0.3))>=0
styles=getSampleStyleSheet();styles.add(ParagraphStyle(name='RuleBody',fontName='Helvetica',fontSize=10.4,leading=14,spaceAfter=10,textColor=HexColor('#183348')))
styles.add(ParagraphStyle(name='RuleHead',fontName='Helvetica-Bold',fontSize=14,leading=18,spaceAfter=12,textColor=HexColor('#123047')))
styles.add(ParagraphStyle(name='RuleTitle',fontName='Helvetica-Bold',fontSize=21,leading=26,spaceAfter=15,textColor=HexColor('#123047')))
story=[]
def para(t,style='RuleBody'):story.append(Paragraph(t,styles[style]))
para('Modelo D — Revisão 1','RuleTitle')
para('Retomada, primeiro toque e pendentes canceladas','RuleHead')
para('Esta revisão substitui a redação anterior do item 9.7 e explicita os itens 9.3 e 9.6. Preserva matemática, filtros, SL/TP fixos, fonte B3, volume e corte. Decisões aprovadas pelo usuário após a leitura do consolidado de 05/11/2026.')
para('1. Uma oportunidade por nível','RuleHead')
para('O envio de uma ordem pendente não consome a oportunidade. O primeiro toque válido por Last — inclusive igualdade, cruzamento ou gap — consome o nível para novos pedidos de entrada. O toque não determina, sozinho, fechamento de uma posição válida e não cancela automaticamente o saldo ainda válido da mesma ordem.')
para('O nível já executado, mesmo parcialmente, não recebe uma nova ordem para completar ou reentrar. Após gain, stop ou zeragem, permanece bloqueado até o próximo pregão. Filtros de abertura, geometria, dados, contrato e horário continuam cumulativos: ausência de toque não dispensa essas condições.')
para('2. Reconstrução até o momento atual','RuleHead')
para('Ao retornar de interrupção, reconciliar ordens, posições, deals e histórico do servidor com o diário persistido e os identificadores do EA. Reconstruir os negócios desde a abertura real até o presente, incluindo a janela corrente disponível. Não basta atingir o último minuto fechado se ainda faltar conferir o trecho atual.')
para('Somente depois da conferência completa autorizar novas entradas nos níveis comprovadamente intactos e elegíveis. Revalidar antes de cada pedido. Se houve primeiro toque antes da aceitação, não enviar entrada atrasada. Leitura em andamento ou falha de consulta não comprova toque, não consome o nível e não provoca cancelamento por si só. Não criar prazo arbitrário para descartar a oportunidade apenas pela demora. Sem prova suficiente, aguardar/reconsultar e bloquear novas entradas.')
para('Proteção de posições conhecidas, conciliação e corte não devem ficar subordinados ao término de toda a reconstrução. Manter a gestão possível das origens comprovadas; conexão e permissões do servidor continuam necessárias para enviar ações.')
story.append(PageBreak())
para('3. Reenvio após cancelamento confirmado','RuleHead')
para('É permitido um novo pedido para o mesmo nível somente se: a ordem anterior estiver comprovadamente cancelada sem execução; não houver nenhum deal de entrada, inclusive parcial; o histórico desde a abertura até agora confirmar ausência de primeiro toque; não existir outra pendente ativa nem requisição com efeito incerto; e todas as demais condições de entrada estiverem válidas, antes do corte.')
para('Ausência na tela, desconexão ou pedido de cancelamento enviado não provam cancelamento. Preservar ticket, recibos e histórico da ordem anterior. Identificar o novo pedido com outra geração, sem apagar o diário nem reutilizar identificadores de forma ambígua. Não usar uma ordem com execução parcial como candidata a esse reenvio.')
para('4. Exemplo de execução parcial: 10 = 6 + 4','RuleHead')
para('Ordem de 10 contratos, dos quais 6 executados e 4 pendentes: proteger imediatamente o volume preenchido com os preços originais normalizados de SL/TP. Os 4 contratos são o saldo da mesma ordem, não quatro ordens novas. Permanecem válidos antes do corte enquanto não ocorrer condição de cancelamento por stop/alvo teórico.')
para('Se os 4 preencherem enquanto a operação continuar válida, reconciliar os preenchimentos e proteger o volume adicional com os mesmos preços fixos. A exposição pode chegar a 10 contratos. Não deslocar SL/TP em razão de preços de execução diferentes.')
para('Se a fronteira teórica de stop/alvo for alcançada, cancelar qualquer saldo pendente e conferir o encerramento do volume executado, mesmo que a saída dos 6 contratos também ocorra em parcelas. Às 18h, cancelar o saldo e fechar o residual. Se houver preenchimento durante o cancelamento, reconciliar a cronologia e encerrar o volume resultante quando devido. Não reabrir a oportunidade.')
para('5. Posição aberta e proteções','RuleHead')
para('Posição executada durante a interrupção pode continuar aberta na retomada, se ainda válida. Seu nível já está consumido para novas entradas. O simples toque não é motivo de fechamento. Se Last após a execução comprovar stop/alvo já alcançado e a posição persistir, conferir proteções e pedidos de fechamento, evitando duplicidade, e solicitar fechamento a mercado quando devido, conforme 9.5/9.6/9.8. SL/TP são vinculados à posição, não ordens opostas independentes.')
para('<b>Estado de implementação:</b> revisão normativa aprovada; não certifica execução. A v2.13.04 contém recuperação de incidentes específicos. O reenvio geral após cancelamento sem toque/execução ainda precisa ser implementado e validado. Preservar o diário e não tratar este PDF como prova de que a alteração já foi instalada.')
buffer=io.BytesIO();SimpleDocTemplate(buffer,pagesize=A4,leftMargin=50,rightMargin=50,topMargin=48,bottomMargin=43).build(story)
appendix=fitz.open(stream=buffer.getvalue(),filetype='pdf');assert len(appendix)==2,len(appendix)
for i,pg in enumerate(appendix):pg.insert_text((50,818),f'MODELO D | REVISÃO 1 | {22+i}/23',fontname='helv',fontsize=8,color=(.2,.3,.4))
doc.insert_pdf(appendix)
toc=doc.get_toc();toc+=[[1,'Revisão 1 — retomada e primeiro toque',22],[2,'Reenvio, parciais e proteção',23]];doc.set_toc(toc)
meta=doc.metadata;meta['title']='Regras Modelo D consolidadas — Revisão 1';meta['subject']='Atualização aprovada dos itens 9.6 e 9.7; implementação não certificada';doc.set_metadata(meta)
doc.save(out,garbage=4,deflate=True);doc.close();appendix.close()
check=fitz.open(out);old=fitz.open(original)
assert len(check)==23
text='\n'.join(p.get_text() for p in check)
assert 'se alcançados ou histórico incompleto, solicitar cancelamento' not in text
for i in range(21):
 if i in [0,11]:continue
 assert old[i].get_text()==check[i].get_text(),f'Unchanged page text differs {i+1}'
 assert old[i].get_pixmap().samples==check[i].get_pixmap().samples,f'Unchanged page pixels differ {i+1}'
for i in [0,11,21,22]:check[i].get_pixmap(matrix=fitz.Matrix(1.15,1.15)).save(f'/tmp/regras_rev1_p{i+1}.png')
(root/'TEXTO_REVISAO_EXTRAIDO.txt').write_text(text)
(root/'VALIDACAO.json').write_text(json.dumps({'paginas':len(check),'original_paginas':len(old),'paginas_originais_editadas':[1,12],'paginas_adicionadas':[22,23],'outras_19_paginas_texto_e_pixels_identicos':True,'tamanhos_fonte_substituicoes':used,'pdf_original_sha256':hashlib.sha256(original.read_bytes()).hexdigest(),'pdf_revisado_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'regra_cancelar_por_historico_incompleto_substituida':True,'codigo_EA_alterado':False},indent=2)+'\n')
print(out, out.stat().st_size)
