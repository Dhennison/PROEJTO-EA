"""Produce reviewable monthly workbooks and raw Replay tabs, preserving originals.
No formulas, monthly test totals, DD extension or fabricated Work references.
"""
from pathlib import Path
import csv,json,datetime as dt,zipfile,io,hashlib,collections
from decimal import Decimal as D
import openpyxl
from openpyxl.styles import Font,PatternFill,Alignment
from openpyxl.comments import Comment
P=Path(__file__).parent;R=P.parents[1];plans=P/'planilhas';plans.mkdir(exist_ok=True)
NAMES=['Janeiro','Fevereiro','Marco','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro','Novembro']
def read(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter=';'))
def write(p,rs,fields=None):
 fields=fields or (list(rs[0]) if rs else ['estado'])
 with p.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields,delimiter=';',lineterminator='\n');w.writeheader();w.writerows(rs)
def t(s):return dt.time.fromisoformat(s)
def style(sh):
 sh.freeze_panes='A2';sh.auto_filter.ref=sh.dimensions
 for c in sh[1]:c.fill=PatternFill('solid',fgColor='17405D');c.font=Font(color='FFFFFF',bold=True);c.alignment=Alignment(wrap_text=True,vertical='top')
 sh.row_dimensions[1].height=32
 for col in sh.columns:
  width=min(55,max(14,max(len(str(c.value or '')) for c in list(col)[:200])+2));sh.column_dimensions[col[0].column_letter].width=width
 for row in sh.iter_rows(min_row=2):
  for c in row:c.alignment=Alignment(vertical='top',wrap_text=True)
 sh.sheet_view.showGridLines=False

def table(wb,name,rs):
 sh=wb.create_sheet(name)
 if rs:
  fields=list(rs[0]);sh.append(fields)
  for r in rs:sh.append([r.get(k,'') for k in fields])
 else:sh.append(['Estado']);sh.append(['Nenhuma pendencia nesta categoria.'])
 style(sh);return sh
summary=json.loads((P/'RESUMO_TODOS_MESES.json').read_text());allco=[];allcontrols=[];allissues=[];allflat=[];guide=[];manifest=[]
for s in summary:
 month=int(s['mes'][-2:]);out=next(x for x in P.iterdir() if x.is_dir() and x.name.startswith(f'{month:02d}_'))
 co=read(out/'COLETAS_REPLAY.csv');controls=read(out/'CONTROLES_COBERTURA.csv')
 if controls and 'mes' not in controls[0]:controls=[]
 # The 30Jul entry minute and its missing interval are one five-minute copy.
 for c in co:
  if c['data']=='2025-07-30' and c['inicio']=='15:42:00':c['fim_exclusivo']='15:47:00';c['tipo']='|'.join(dict.fromkeys((c['tipo']+'|COBERTURA_15:43_15:47').split('|')))
 for c in controls:
  if c['data']=='2025-07-30':c['acao']='JA_INCLUIDO na coleta30/07 15:42–15:47;nao repetir separadamente'
 # Merge adjacent windows on the same day/contract; preserve all affected levels.
 merged=[]
 for c in sorted(co,key=lambda x:(x['data'],x['inicio'])):
  if merged and merged[-1]['data']==c['data'] and merged[-1]['contrato']==c['contrato'] and t(c['inicio'])<=t(merged[-1]['fim_exclusivo']):
   g=merged[-1];g['fim_exclusivo']=max(g['fim_exclusivo'],c['fim_exclusivo']);g['niveis']=','.join(dict.fromkeys((g['niveis']+','+c['niveis']).split(',')));g['tipo']='|'.join(dict.fromkeys((g['tipo']+'|'+c['tipo']).split('|')))
  else:merged.append(dict(c))
 for c in merged:c['aba_retorno']=c['data'][8:]+'-'+c['data'][5:7]+'_'+c['inicio'][:5].replace(':','')
 write(out/'COLETAS_REPLAY.csv',merged);write(out/'CONTROLES_COBERTURA.csv',controls)
 s['janelas_replay']=len(merged);s['minutos_replay']=sum(int((dt.datetime.combine(dt.date.today(),t(c['fim_exclusivo']))-dt.datetime.combine(dt.date.today(),t(c['inicio']))).total_seconds()/60) for c in merged)
 s['intervalos_longos_exigem_primeiro_candles']=sum(c['tipo']=='COBERTURA_COMPARTILHADA_SEM_M5' for c in controls)
 s['controles_cobertura_ja_incluidos_no_replay']=sum('JA_INCLUIDO' in c['acao'] for c in controls)
 (out/'RESUMO.json').write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
 issues=read(out/'DATAS_E_DIVERGENCIAS.csv')
 issues=[r for r in issues if r.get('tipo')!='COMPLEMENTO_FORA_WORK']
 if issues and 'mes' not in issues[0]:issues=[]
 # Explicitly identify dates outside Work and the source of their actual adjustment.
 for day in s['datas_fora_Work']:
  issues.append(dict(mes=s['mes'],data=day,inicio='',fim='',tipo='COMPLEMENTO_FORA_WORK',detalhe='Candles e ajuste disponíveis na cobertura original;resultado complementar separado,Work indisponível',acao='Manter Work em branco;nao somar à comparação original',contexto=False))
 write(out/'DATAS_E_DIVERGENCIAS.csv',issues)
 ops=read(out/'OPERACOES_POSSIBILIDADES.csv');detail=read(out/'JANELAS_POR_OPERACAO.csv')
 grades={(x['data'],x['nivel']) for x in detail if x.get('tipo')=='CONTROLE_GRADE5'}
 ops_out=[]
 for o in ops:
  status='PENDENTE_COBERTURA' if o['coverage_pending']=='True' else 'PENDENTE_REPLAY' if o['determined']=='False' else 'PENDENTE_CONTROLE_GRADE' if (o['date'],o['level']) in grades else 'DETERMINADA_M1'
  ops_out.append(dict(data=o['date'],nivel=o['level'],contrato=o['contract'],estado=status,Work_motivo=o['work_reason'],Work_pontos=o['work_points'],teste_grade5=o['outcomes'],entrada=o['entry'],alvo=o['tp'],stop=o['sl'],minuto_entrada=o['entry_minute'],saidas_possiveis=o['exit_candidates'],fora_Work=o['date'] in s['datas_fora_Work']))
 write(out/'CONCRETO_E_PENDENTE_POR_OPERACAO.csv',ops_out)
 flat={k:s[k] for k in ['mes','nome','pregoes','operacoes','concretas_sem_ressalva_de_sequencia_cobertura_grade','pendentes_sequencia','controles_grade','operacoes_conhecidas_com_cobertura_pendente','janelas_replay','minutos_replay','intervalos_longos_exigem_primeiro_candles','Work_pontos','M1','M5','grupos_preco_divergente','grupos_quantidade_divergente']}
 flat['datas_fora_Work']=','.join(s['datas_fora_Work']);flat['principal']='PENDENTE';flat['DD_teste']='NAO_CALCULADO';allflat.append(flat)
 instructions=[
 ('Escopo',f'{s["nome"]}/2025: {s["pregoes"]}pregões, {s["operacoes"]}operações conhecidas. Sem fechamento mensal ou DD do teste.'),
 ('Concreto',f'{s["concretas_sem_ressalva_de_sequencia_cobertura_grade"]}operações determinadas sob os candles fornecidos, sem pendência de sequência/cobertura/grade. Quantidade divergente continua ressalvada.'),
 ('Replay',f'{len(merged)}janelas /{s["minutos_replay"]}minutos. Use as abas de retorno já preparadas. Fim do intervalo é exclusivo; horários de São Paulo.'),
 ('Como copiar','Reproduzir alguns segundos antes/depois,sem pular nem filtrar lotes/corretoras. Copiar dados completos do Times&Trades;preservar milissegundos,ordem e negócios idênticos. Não deduplicar.'),
 ('Abas de retorno','As abas com data/hora contêm só o cabeçalho padrão do Profit. Cole negócios nelas, mantendo os cabeçalhos. Se abertura for tardia, não invente negócios anteriores; informe a observação.'),
 ('Validação futura','Antes de resolver:OHLC/quantidade,minuto inteiro,limite200001 por cópia e empates de milissegundo. Preenchimento/ordens não certificados.'),
 ('Cobertura','A aba Controle_Cobertura informa lacunas. Nas lacunas longas, verificar existência de negócios no Replay e recuperar candles M1 primeiro; não é pedido de copiar toda a fita.'),
 ('30/07','A coleta15:42–15:47 já inclui os4minutos ausentes15:43–15:47. Não precisa enviar um segundo trecho igual.' if month==7 else 'Não aplicável neste mês.'),
 ('Datas fora do Work',', '.join(s['datas_fora_Work'])+'; ajustes no pacote original,complementos separados,Work em branco.' if s['datas_fora_Work'] else 'Nenhuma data complementar fora da seleção original.'),
 ('Preço20/05','M5fecha141500;M1fecha141510 no grupo18:20. Após corte18h,mas é contexto21/05. Preservar fechamentoWork141500;não trocar ajuste/níveis. Conferir a fonte como ressalva.' if month==5 else 'Ver aba Datas_A_Conferir.'),
 ('Parâmetros','D original,grade5,1contrato/nível,toque inclusivo,corte18h. Não variar alvos/stops,modelos ou ajustar referência pelo lucro.'),
 ('Fontes','M1 nativo MT5 WIN$N;M5 Profit usado pelo Work;ajustes Work. M1+janelas não são fita integral. Calendário sugere contrato;preços da cópia ainda precisam conferir.'),
 ('Acesso','Se contrato antigo indisponível,registrar data/contrato/alcance. TentarWINFUT só confirmando negócios individuais comms,correspondência e ajustes;sem compra.'),
 ('Preservação','Todos os meses fechados,brutos,referências e auditorias anteriores preservados. Controle10/07/2026 dispensado não reaberto;10/07/2025 é outra data.'),
 ]
 readme='\n\n'.join(f'{a}: {b}' for a,b in instructions)
 readme+='\n\nJANELAS PARA COPIAR\n'+'\n'.join(f'{c["data"]} {c["contrato"]} {c["inicio"]}–{c["fim_exclusivo"]} {c["niveis"]} [{c["tipo"]}]' for c in merged)
 if controls:readme+='\n\nCONTROLES DE COBERTURA\n'+'\n'.join(f'{c["data"]} {c["contrato"]} {c["inicio"]}–{c["fim_exclusivo"]}: {c["acao"]}' for c in controls)
 readme+='\n\nO QUE NÃO CASA\n'+'\n'.join(f'{c["data"]} {c["inicio"]} {c["tipo"]}: {c["detalhe"]}' for c in issues)
 (out/'LEIA_MES.txt').write_text(readme.rstrip()+'\n')
 wb=openpyxl.Workbook();wb.remove(wb.active)
 table(wb,'LEIA',[dict(topico=a,instrucao=b) for a,b in instructions]);table(wb,'Coletas',merged);table(wb,'Controle_Cobertura',controls);table(wb,'Datas_A_Conferir',issues);table(wb,'Concreto_Pendente',ops_out);table(wb,'Comparativo_Work_M5_M1',read(out/'COMPARATIVO_WORK_M5_M1.csv'));table(wb,'Acervo',read(out/'INVENTARIO_POR_DATA.csv'));table(wb,'Referencias',read(out/'REFERENCIAS.csv'))
 for c in merged:
  sh=wb.create_sheet(c['aba_retorno']);sh.append(['Data','Compradora','Valor','Quantidade','Vendedora','Agressor','Total (BRL)','Agente Agressor','Núm','Var']);style(sh)
  sh['A1'].comment=Comment(f'{c["data"]} {c["contrato"]} {c["inicio"]}–{c["fim_exclusivo"]},fimexclusivo. Cole aqui negócios do Profit,alguns segundos antes/depois. Não é candle.','PreparaçãoModeloD')
 wb.save(plans/f'2025_{month:02d}_{NAMES[month-1]}.xlsx')
 allco.extend(merged);allcontrols.extend(controls);allissues.extend(issues)
 guide.append(f'{s["nome"]}: {s["pregoes"]}pregões;{s["operacoes"]}operações conhecidas;{flat["concretas_sem_ressalva_de_sequencia_cobertura_grade"]}concretas;{len(merged)}janelas/{s["minutos_replay"]}minutos;{s["intervalos_longos_exigem_primeiro_candles"]}controles longos primeiro.')
write(P/'COLETAS_TODOS_MESES.csv',allco);write(P/'CONTROLES_COBERTURA_TODOS_MESES.csv',allcontrols);write(P/'DATAS_DIVERGENTES_TODOS_MESES.csv',allissues);write(P/'RESUMO_MENSAL.csv',allflat)
(P/'RESUMO_TODOS_MESES.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
wb=openpyxl.Workbook();wb.remove(wb.active);table(wb,'Resumo_Mensal',allflat);table(wb,'Coletas_Todos_Meses',allco);table(wb,'Controles_Cobertura',allcontrols);table(wb,'Datas_Divergentes',allissues)
wb.save(P/'Lista_Replay_Janeiro_a_Novembro_2025.xlsx')
text=f'''PREPARAÇÃO JANEIRO A NOVEMBRO/2025 — 15/11/2026
Nenhum mês foi fechado:resultado principal eDD do teste permanecem pendentes.
M1 de todos os11meses e M5Work disponíveis,com ressalvas individuais.
{sum(s['operacoes'] for s in summary)}operações conhecidas, incluindo complementos foraWork identificados.
{sum(s['concretas_sem_ressalva_de_sequencia_cobertura_grade'] for s in summary)}operações concretas sob os candles fornecidos,sem pendência de sequência/cobertura/grade;
{sum(s['pendentes_sequencia'] for s in summary)}operações com dúvida de sequência;{sum(s['controles_grade'] for s in summary)}controles adicionais de grade.
As categorias podem sobrepor cobertura;lacunas longas ainda podem esconder entradas extras.
São{len(allco)}janelas de negócios/{sum(s['minutos_replay'] for s in summary)}minutos,sendo4minutos de cobertura30jul já incluídos.
Além disso,verificar existência/recuperar candles nos intervalos longos03jun09:04–09:56
WINM25 e21ago09:17–10:26 WINV25. Não copiar52/69minutos de negócios agora.

'''+ '\n'.join(guide)+'''

ARQUIVOS
planilhas/:11XLSX,um por mês,com abas de instruções,coletas,cobertura,divergências,
operações concretas/pendentes,comparaçãoWork e abas vazias para colar negócios.
Lista_Replay_Janeiro_a_Novembro_2025.xlsx:lista consolidada para organizar a coleta.
Pastas01_... a11_...:CSVs completos,referências,comparações eLEIA_MES.txt.
DATAS_DIVERGENTES_TODOS_MESES.csv:divergências e datas foraWork.

RESSALVAS QUE NÃO DEVEM SER PERDIDAS
20/05 18:20:fechamentoM5 141500 versusM1 141510. Após corte,mas contexto21/05:
manter HLCWork141500 e ajustes originais;nenhuma alteração para aproximar lucro.
41grupos de quantidade diferentes no período,sem presumir fita perfeita.
02jan/10jul/11jul têm ajustes na cobertura original e candles conferidos,mas não
referência diáriaWork. Complementos separados,Work em branco,nunca zero fabricado.
10/07/2025 não é o controle10/07/2026 dispensado,que permanece encerrado.
Lacunas M1 e compartilhadas têm auditoria individual. Julho30 é5minutos incluindo
entrada15:42 e4minutos ausentes;sem pedido duplicado. Outras lacunas sem efeito
paraD atual não exigem negócios agora. Novasvariantes podem exigir outrasjanelas.
Calendário/convenção determina contratos sugeridos;conferir preços nas cópias.
M1+janelas não são histórico inteiro por negócios nem fills garantidos.
D original/grade5/1contrato/toque/corte18h preservados. Sem compras ou novosmodelos.

PRESERVAÇÃO
Dez2025+3135/Jan2026-1620/Fev-3545/Mar+350/Abr+5720/Mai-780/Jun+3405/Jul+1100
intactos. CedroAgo-2375/Set+2855/Out+3830 e comparáveis separados intactos.
Curvas/PDFs fechados não regravados;DDdez25-jul26 continua9365 eCedro3620.
Somente após resolver cada mês ampliarDD por fechamentos diários emordemcronológica,
sem reinício mensal,sem alterar dias fechados;PDFs técnico/enxuto continuarão diáriosWorkversusteste.
'''
(P/'LEIA_PRIMEIRO.txt').write_text(text)
# Read back EVERY workbook and check all requested raw tabs exist and are empty.
for f in list(plans.glob('*.xlsx'))+[P/'Lista_Replay_Janeiro_a_Novembro_2025.xlsx']:
 w=openpyxl.load_workbook(f,read_only=True,data_only=False)
 assert all(c.data_type!='f' for sh in w for row in sh.iter_rows() for c in row)
 if f.parent==plans:
  month=int(f.name[5:7]);out=next(x for x in P.iterdir() if x.is_dir() and x.name.startswith(f'{month:02d}_'))
  for c in read(out/'COLETAS_REPLAY.csv'):assert c['aba_retorno'] in w.sheetnames and w[c['aba_retorno']].max_row==1
 w.close()
for f in sorted(P.rglob('*')):
 if f.is_file() and f.suffix!='.zip' and f.name!='MANIFESTO_ENTREGA.json':manifest.append(dict(path=str(f.relative_to(P)),size=f.stat().st_size,sha256=hashlib.sha256(f.read_bytes()).hexdigest()))
(P/'MANIFESTO_ENTREGA.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
with zipfile.ZipFile(P/'Preparacao_Janeiro_a_Novembro_2025.zip','w',zipfile.ZIP_DEFLATED) as z:
 for f in sorted(P.rglob('*')):
  if f.is_file() and f.suffix!='.zip':z.write(f,f.relative_to(P))
print(text)
