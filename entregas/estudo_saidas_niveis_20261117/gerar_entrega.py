from pathlib import Path
import csv,json,pickle,hashlib,zipfile,textwrap,re
import numpy as np
import openpyxl,fitz
from openpyxl.styles import Font,PatternFill
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
P=Path(__file__).parent;R=P.parents[1];E=R/'entregas';CACHE=Path('/workspace/work/estudo_saidas');d=pickle.loads((CACHE/'resultados.pickle').read_bytes());data=d['data'];days=data['days'];levels=['R38.2','R61.8','S38.2','S50','S61.8'];configs={c['id']:c for c in d['cfg']}
def read(name):
 with (P/name).open(encoding='utf-8-sig') as f:return list(csv.DictReader(f,delimiter=';'))
def write(name,rows):
 with (P/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter=';',lineterminator='\n');w.writeheader();w.writerows(rows)
def num(x):return f'{float(x):,.0f}'.replace(',','.')
def ran(r):return num(r['points_lower']) if r['points_lower']==r['points_upper'] else num(r['points_lower'])+' a '+num(r['points_upper'])
def desc(c):
 if c['mode']=='ORIGINAL':return 'Saídas originais'
 if c['mode']=='FIXED_TARGET_AND_STOP_POINTS':return f"Alvo{c['tp_multiplier']} / stop{c['stop_parameter']} pontos"
 target=f"Alvo{c['tp_multiplier']}xoriginal"
 stop=f"stop{c['stop_parameter']}xoriginal" if c['mode']=='STOP_MULT_ORIGINAL' else f"stop{c['stop_parameter']}xnovoalvo" if c['mode']=='STOP_PROPORTIONAL_NEW_TARGET' else f"stop{c['stop_parameter']} pontos"
 return target+';'+stop
scenario={r['id']:r for r in d['scenarios']+d['subsets']};target='MIX_0161';cand=scenario[target]
assert cand['rule']=='R38.2:OFF|R61.8:V164|S38.2:OFF|S50:OFF|S61.8:D_ORIGINAL'
# Per-operation pending details only for candidate's modified level.
pp=[r for r in read('LIMITES_POR_OPERACAO.csv') if r['variant']=='V164' and r['level']=='R61.8' and r['uncertain']=='True'];assert len(pp)==8 and all(r['date'].startswith('2026-08') for r in pp)
for r in pp:
 op=next(o for o in data['ops'] if o['date']==r['date'] and o['level']==r['level']);r.update(contract=op['contract'],entry_minute=op['entry_minute'],need='RECUPERAR_CEDRO_ORIGINAL;NAO_COLETAR_FITA_INTEGRAL_REPLAY_SEM_TRIAGEM',status='SEM_FECHAMENTO')
write('CANDIDATA_R61_ALVO750_STOP150_PENDENCIAS.csv',pp)
raw=read('CEDRO_ARQUIVOS_BRUTOS_NAO_LOCALIZADOS.csv');datetags={r['date'].replace('-','') for r in pp};prioritized=[r for r in raw if r['arquivo'][4:12] in datetags];write('CEDRO_PRIORITARIO_OITO_DATAS.csv',prioritized)
# Neighbors quantify sensitivity around this recipe.
neighbors=[r for r in d['levelmetrics'] if r['level']=='R61.8' and configs[r['variant']]['mode']=='FIXED_TARGET_AND_STOP_POINTS' and configs[r['variant']]['tp_multiplier'] in [500,750,1000] and configs[r['variant']]['stop_parameter'] in [100,150,250]]
write('VIZINHANCA_R61_ALVO750_STOP150.csv',[dict(target=configs[r['variant']]['tp_multiplier'],stop=configs[r['variant']]['stop_parameter'],**r) for r in neighbors])
# Shortlisted M1 ambiguity requests are diagnostics, not a request for945windows.
sel=read('SELECAO_POR_NIVEL_TREINO_2024_2025.csv');byl={l:{r['variant'] for r in sel if r['level']==l and r['variant'] not in ['OFF','D_ORIGINAL']} for l in levels};short=[]
for w in d['windows']:
 selected=byl[w['level']]&set(w['variants'].split('|'))
 if not selected or w['reason']!='SEQUENCE_M1':continue
 if w['date']=='2026-07-10' and '09:55'<=w['minute']<='09:58':continue
 op=next(o for o in data['ops'] if o['date']==w['date'] and o['level']==w['level']);h,m=map(int,w['minute'].split(':'));finish=f'{(h*60+m+1)//60:02d}:{(h*60+m+1)%60:02d}'
 short.append(dict(date=w['date'],contract=op['contract'],start=w['minute'],end_exclusive=finish,level=w['level'],variants='|'.join(sorted(selected)),status='EXPLORATORIO_NAO_SOLICITADO_AUTOMATICAMENTE'))
if short:write('REPLAY_TRIAGEM_VARIANTES_SELECIONADAS.csv',short)
# Exact one-day/one-operation conservation and independently recomputed exclusions.
base=d['lo'][0];assert np.array_equal(base,d['hi'][0]) and base.sum()==3950
for r in d['subsets']:
 ids=[levels.index(l) for l in r['levels'].split('|')];a=base[:,ids].sum(1);assert a.sum()==r['points_lower']==r['points_upper'];b=a.cumsum();dd=np.max(np.maximum.accumulate(np.r_[0,b])[1:]-b);assert dd==r['DD_upper']
# Source fingerprints, including original archive and exact immutable closed ledgers.
sources=set(data['sources']);sources.add('entregas/arquivo_conversa_20261111/originais/ORIGINAIS_PARTE_005.zip');sources.add('entregas/historico_work_modelo_d_20261105/replay_setembro_20261106/originais/Candles_Originais_Modelo_D_2023_2026.zip');sources.add('entregas/resultado_niveis_202401_202610_20261117/OPERACOES_NORMALIZADAS.csv')
manifest=dict(original_main='MODELO_D_ORIGINAL_GRADE5',period='2024-01 a2026-10',days=709,original_operations=1485,exit_rule_recipes=175,per_level_tests=875,exclusion_combinations=31,mixed_candidates=1279,source_closed_files=[dict(path=s,sha256=hashlib.sha256((R/s).read_bytes()).hexdigest()) for s in sorted(sources)],original_points=3950,original_DD_daily=14805,original_result_files_not_changed=True,tests=['frozen1485tradesconserved','31subsetresultsindependentlyrecomputed','originaldailyexactreproduced','preentryhighnotforcedTP','replaychronology','cut','sourcegaps','missingCedroAugustbounded'],missing_cedro_parts=len(raw),candidate_missing_parts=len(prioritized),no_variants_promoted=True,point_intervals_not_certified_trades=True)
(P/'MANIFESTO.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
# User workbook: all scenario/parameter/monthly results, not just winners.
wb=openpyxl.Workbook();wb.remove(wb.active)
for name,file in [('Exclusoes_Exatas','EXCLUSOES_31_COMBINACOES_EXATAS.csv'),('Cenarios_Saidas_Mistos','CENARIOS_SAIDAS_E_MISTOS.csv'),('Por_Nivel','VARIANTES_POR_NIVEL.csv'),('Parametros','PARAMETROS_VARIANTES.csv'),('Mensal_Todos','RESULTADO_MENSAL_TODOS_CENARIOS.csv'),('Selecao_Treino','SELECAO_POR_NIVEL_TREINO_2024_2025.csv'),('Pendencias_Candidata','CANDIDATA_R61_ALVO750_STOP150_PENDENCIAS.csv'),('Vizinhanca_R61','VIZINHANCA_R61_ALVO750_STOP150.csv'),('Cedro_Prioritario','CEDRO_PRIORITARIO_OITO_DATAS.csv')]:
 rows=read(file);sh=wb.create_sheet(name);keys=list(rows[0]);sh.append(keys)
 for r in rows:
  vals=[]
  for k in keys:
   v=r[k]
   if k not in ['month','id','variant','date','arquivo','sha256','entry_minute','contract']:
    try:v=float(v)
    except (ValueError,TypeError):pass
   vals.append(v)
  sh.append(vals)
 sh.freeze_panes='A2';sh.auto_filter.ref=sh.dimensions
 for c in sh[1]:c.font=Font(color='FFFFFF',bold=True);c.fill=PatternFill('solid',fgColor='17354E')
 for col in sh.columns:sh.column_dimensions[col[0].column_letter].width=min(55,max(15,max(len(str(c.value or '')) for c in list(col)[:70])+2))
wb.save(P/'Estudo_Stop_Alvo_Exclusoes_2024_2026.xlsx')
# PDF concise, explicit uncertainty and exact exclusions kept separate.
c=canvas.Canvas(str(P/'Estudo_Stop_Alvo_Exclusoes_2024_2026.pdf'),pagesize=A4);page=0
c.setTitle('Modelo D — estudo de saídas e exclusões — janeiro2024 a outubro2026')
def new(title,sub=''):
 global page,y
 if page:c.showPage()
 page+=1;y=760;c.setFillColorRGB(.06,.16,.25);c.rect(0,785,595,57,fill=1,stroke=0);c.setFillColorRGB(1,1,1);c.setFont('Helvetica-Bold',15);c.drawString(32,805,title);c.setFillColorRGB(.06,.16,.25);c.setFont('Helvetica',10)
 if sub:c.drawString(32,y,sub);y-=25
 c.setFont('Helvetica',8);c.drawString(32,24,f'17/11/2026 | Exploração, sem parâmetros aprovados | Página{page}');c.setFont('Helvetica',10)
def lines(t,bold=False):
 global y
 t=re.sub(r'(?<=[a-zà-ÿ])(?=\d)|(?<=\d)(?=[a-zà-ÿ])',' ',t)
 t=re.sub(r'(?<=DD)(?=\d)',' ',t)
 t=re.sub(r';(?=\S)','; ',t)
 t=re.sub(r',(?=[A-Za-zÀ-ÿ])',', ',t)
 t=re.sub(r'(?<=[a-zà-ÿ]),(?=\d)',', ',t)
 c.setFont('Helvetica-Bold' if bold else 'Helvetica',10)
 for paragraph in t.split('\n'):
  for line in textwrap.wrap(paragraph,98) or ['']:c.drawString(32,y,line);y-=15
 y-=6
new('Modelo D | Stops, alvos e exclusões','Janeiro/2024 a outubro/2026 | 709 pregões | 1.485 entradas originais')
lines('Resultado principal preservado: +3.950 pontos; DD diário contínuo14.805.',True)
lines('Foram calculadas175 receitas de saída,875 testes separados por nível,31 combinações de exclusão e1.279 modelos mistos. Receitas repetem distâncias em alguns níveis; não são caminhos independentes.')
lines('Conclusão verificável: excluir níveis melhora algumas métricas do conjunto fechado, mas há mudanças fortes entre anos. Não há configuração nova aprovada para operação.',True)
lines('Exemplo exato: R61.8+S61.8 originais soma5.890, DD5.505;488operações;2024: +2.680;2025: +4.325;2026jan-out: -1.115. Melhor agregado não garante estabilidade.')
lines('Candidata pendente: R61.8 alvo750/stop150; S61.8 original; outros OFF. Treino2024/25+12.270. No período completo, envoltória7.830 a19.145;DD limitado entre6.920 e7.875. Oito entradas deagosto2026 não podem ser encerradas com o acervo local atual. A faixa NÃO é lucro realizado nem previsão.',True)
lines('2026 foi separado na seleção, mas esse histórico já era conhecido. O teste não equivale a validação futura independente. Custos5/10/20 pontos por operação são sensibilidades hipotéticas.')
lines('Limitação material:132 partes Cedro não estão locais. Setembro/outubro têm M1 de auditoria; novas sequências ficam pendentes. Agosto não tem M1 auditado Cedro: novas saídas recebem limites amplos. Dados originais permanecem fechados.')
new('Exclusões | Resultados exatos','Saídas originais preservadas; DD por fechamentos diários, sem reinício mensal')
rank=sorted(d['subsets'],key=lambda r:r['points_lower']/max(1,r['DD_upper']),reverse=True)
for r in rank[:12]:
 lines(r['id']+' | '+r['levels'],True)
 lines(f"Pontos{num(r['points_lower'])} | DD{num(r['DD_upper'])} | {r['operations']}ops | Anos{num(r['year2024_lower'])}/{num(r['year2025_lower'])}/{num(r['year2026_JanOct_lower'])}")
# remaining exact combinations, all31 included.
for start in [12,24]:
 new('Exclusões | Demais combinações exatas','Ano2026 significa janeiro a outubro; valores em pontos')
 for r in rank[start:start+12]:
  lines(r['id']+' | '+r['levels'],True);lines(f"Pontos{num(r['points_lower'])} | DD{num(r['DD_upper'])} | {r['operations']}ops | Anos{num(r['year2024_lower'])}/{num(r['year2025_lower'])}/{num(r['year2026_JanOct_lower'])}")
new('Receitas de saídas | O que foi testado')
lines('Entradas e elegibilidade congeladas, um contrato por nível/dia e sem reentrada. As novas saídas percorrem preços posteriores à saída original até18h. Excluir um nível não redistribui contratos aos outros.')
lines('Alvos multiplicados por0,5;0,75;1;1,25;1,5;2;3 da distância original. Stops multiplicados por0,25;0,5;0,75;1;1,25;1,5;2. Stops proporcionais ao NOVO alvo em0,5;0,75;1;1,5;2;3. Stops fixos100/150/250/375/500/650. Alvos fixos100/150/250/375/500/750/1000 combinados com esses stops. Tudo arredondado à grade5, mínimo5.')
lines('Alvo/stop750/150 em R61.8 é uma receita de razão5:1, escolhida entre a grade exploratória, não validada por esse número. R50 não existe no D.')
lines('Cada nível seleciona, apenas por2024/25, original, OFF, duas melhores relações pontos/DD conservadoras e melhor total conservador. O produto das escolhas gera1.279 candidatos mistos; não foi feita busca de todas as175^5 configurações.')
lines('M1 pode conter máxima anterior à entrada. Não foi adotada ordem arbitrária favorável. Foram reutilizados106minutos completos deReplay após conferirOHLC e quantidade, preservando negócios idênticos. Fora desses minutos, todas as saídas compatíveis continuam no envelope.')
lines('Extremos de níveis diferentes podem exigir sequências incompatíveis no mesmo candle. Limites não são trajetórias certificadas. O DD de limite inferior/superior é calculado em curvas diárias inteiras, não por somarDDs de níveis.')
new('Por nível | Seleção apenas em2024/2025')
for l in levels:
 candidates=[r for r in d['levelmetrics'] if r['level']==l and r['variant']!='D_ORIGINAL'];r=max(candidates,key=lambda r:r['training_2024_25_lower']);c0=configs[r['variant']]
 lines(l+' | '+r['variant']+' | '+desc(c0),True)
 lines(f"Treino limite inferior{num(r['training_2024_25_lower'])};2026 {num(r['year2026_JanOct_lower'])} a{num(r['year2026_JanOct_upper'])};período {ran(r)};{r['uncertain_trades']} operações pendentes.")
lines('Esta tabela mostra a maior soma conservadora no treino por nível. Não presume que juntar esses cinco vencedores gere resultado estável; os mistos e o período2026 estão na planilha.')
new('Candidata R61.8 alvo750 / stop150','S61.8 original; R38.2, S38.2 e S50 excluídos | MIX_0161')
lines('2024+6.155;2025+6.115;2026jan-out-4.440 a+6.875. Total7.830 a19.145;488operações;DD6.920 a7.875. Há oito pendências, todas emagosto2026.',True)
lines('A faixa ampla vem da ausência da fonte Cedro deagosto; não indica probabilidade uniforme nem possibilidade de realizar o extremo superior. É necessário recuperar as partes originais destas datas antes de fechar a candidata:')
for r in pp:lines(f"{r['date']} | {r['contract']} | entrada original no minuto{r['entry_minute']}")
lines(f"Foram identificadas{len(prioritized)} partes originais dessas oito datas, listadas com nomes/hashes emCEDRO_PRIORITARIO_OITO_DATAS.csv. Não é pedido de repetir mês inteiro deReplay.")
new('Sensibilidade | Vizinhos do alvo750 / stop150','R61.8 isolado; treino2024+2025;2026 em faixa quando pendente')
for r in neighbors:
 c0=configs[r['variant']];lines(f"Alvo{c0['tp_multiplier']} / stop{c0['stop_parameter']} | treino{num(r['training_2024_25_lower'])} | 2026 {num(r['year2026_JanOct_lower'])} a{num(r['year2026_JanOct_upper'])}")
lines('Parâmetros vizinhos permitem detectar um pico isolado da busca. Nenhuma dessas configurações recebe aprovação automática por vencer o treino.')
new('Custos e estabilidade | Exclusões exatas')
for id in ['EXC_31','EXC_19','EXC_18','EXC_26','EXC_16']:
 r=scenario[id];lines(r['levels'],True)
 lines(f"Bruto{num(r['points_lower'])};custo5:{num(r['points_after_cost5_lower'])};custo10:{num(r['points_after_cost10_lower'])};custo20:{num(r['points_after_cost20_lower'])}.")
 lines(f"Meses positivos/negativos:{r['months_positive_lower']}/{r['months_negative_lower']};pior mês{num(r['worst_month_lower'])};cinco maiores dias = {100*r['top5_share_positive_days_lower']:.1f}% da soma dos dias positivos.")
lines('Valores de custo são pontos por operação completa, não taxas reais. Uma regra pode melhorar o bruto e continuar economicamente frágil.')
#34monthlyrows selected strategies: exact and pending clearly separated.
for start in [0,17]:
 new('Resultado mês a mês | Referências selecionadas','Original | R61+S61 originais | R61+S50+S61 originais | Candidata pendente')
 ids=['D_ORIGINAL','EXC_18','EXC_26',target];months=sorted({day[:7] for day in days})
 for m in months[start:start+17]:
  vals=[]
  for id in ids:
   a,b=d['scenario_daily'][id];mask=np.array([day.startswith(m) for day in days]);aa=a[mask].sum();bb=b[mask].sum();vals.append(num(aa) if aa==bb else num(aa)+' a '+num(bb))
  lines(m+' | '+' | '.join(vals))
new('Conclusões e pendências')
lines('1. As exclusões são resultados fechados sob a base original. A duplaR61.8+S61.8 reduzDD, mas perde em2026. O trioR61.8+S50+S61.8 é positivo nos três blocos anuais, porém2024 soma só140pontos e o total fica negativo no cenário de custo10pontos/operação.')
lines('2. Há melhorias de treino com novas saídas por nível, inclusive alvos fixos longos e stops curtos. Elas não devem ser confundidas com resultado certificado em todo o período. A candidata750/150 depende de oito entradas Cedro deagosto.')
lines('3. Recuperar primeiro os brutos já existentes dessas oito datas, usando o manifesto. Depois resolver apenas as janelas relevantes das candidatas selecionadas. A lista de945linhas reúne pendências de todas as receitas; não é uma solicitação de coletar tudo.')
lines('4. Preservar o D original como principal. Nenhuma variante substituiu resultados ou parâmetros. Não comprar histórico;2023 não foi aberto. O controle adicional dispensado de10/07/2026 não foi reaberto.')
lines('Planilha contém todos os resultados e parâmetros, por nível, por mês, anuais,DD, concentração e custos. CSVs de limites por operação permitem auditoria. Os arquivos originais têm hashes no manifesto.')
c.save();doc=fitz.open(P/'Estudo_Stop_Alvo_Exclusoes_2024_2026.pdf');assert len(doc)>=10
(P/'LEIA_PRIMEIRO.md').write_text('''# Estudo de saídas e exclusões — janeiro2024 a outubro2026

Leia primeiro Estudo_Stop_Alvo_Exclusoes_2024_2026.pdf. Planilha Estudo_Stop_Alvo_Exclusoes_2024_2026.xlsx reúne as175 receitas,875 testes por nível,31 exclusões exatas,1279 combinações mistas e34meses de cada cenário.

Modelo D original principal preservado:3950pontos,DD diário14805,1485operações em709pregões. Exclusões usam resultados originais exatos. Novas saídas são envoltórias condicionais quando a sequência não está disponível; não há resultado certificado escolhido pelo ramo favorável. Regras, seleção de2024/25, limites, custos e distinções de fontes em REGRAS_E_LIMITES.md.

Candidata para aprofundar: R61.8 alvo750/stop150 +S61.8original;outrosOFF. Treino2024/25:12270. Faixa completa7830a19145,DD6920a7875;8operações deagosto2026 aguardam fonteCedro. CEDRO_PRIORITARIO_OITO_DATAS.csv lista as partes já recebidas anteriormente,mas indisponíveis neste ambiente. Não há autorização implícita para comprar histórico nem pedido para coletar todas as945janelas de todas as receitas.

Nenhuma variante aprovada para operar. Mesmo a melhor seleção do treino é exploratória;2026 já era conhecido. Não foi alterado arquivo de resultado fechado. Curvas e fontes antigas seguem preservadas. O controle adicional de10/07/2026 dispensado não foi reaberto.
''')
(P/'.gitattributes').write_text('*.pdf binary\n*.xlsx binary\n*.zip binary\n');(P/'.gitignore').write_text('__pycache__/\n')
with zipfile.ZipFile(P/'Estudo_Stop_Alvo_Exclusoes_2024_2026.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(P.rglob('*')):
  if p.is_file() and p.suffix in ['.py','.csv','.json','.md','.xlsx','.pdf']:z.write(p,p.relative_to(P))
print(json.dumps(dict(pdf_pages=len(doc),candidate_pending=len(pp),candidate_missing_raw_parts=len(prioritized),shortlist_replay_windows=len(short),source_files=len(sources)),ensure_ascii=False))
