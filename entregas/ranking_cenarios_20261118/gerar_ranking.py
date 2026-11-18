from pathlib import Path
import csv,json,hashlib
import numpy as np
import openpyxl,fitz
from openpyxl.styles import Font,PatternFill
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4,landscape
P=Path(__file__).parent;R=P.parents[1];E=R/'entregas';pool=json.loads((P/'UNIVERSO_CONSOLIDADO.json').read_text());sources=[]
def read(p):
 sources.append(dict(path=str(p.relative_to(R)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
 with p.open(encoding='utf-8-sig') as f:return list(csv.DictReader(f,delimiter=';'))
def write(name,rows):
 with (P/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter=';',lineterminator='\n');w.writeheader();w.writerows(rows)
def dd(a):
 balance=np.cumsum(a);return float(np.max(np.maximum.accumulate(np.r_[0,balance])[1:]-balance))
def n(v):return f'{float(v):,.0f}'.replace(',','.')
def span(a,b):return n(a) if a==b else n(a)+' a '+n(b)
# Explicit ranking: exact positive totals only, annual sign then total/DD.
closed=[r for r in pool if r['pending']==0 and r['lo']==r['hi'] and r['lo']>0]
assert len(closed)==42
for r in closed:r['positive_years']=sum(v>0 for v in r['years']);r['points_per_DD']=r['lo']/max(1,r['ddhi'])
closed.sort(key=lambda r:(r['positive_years'],r['points_per_DD'],min(r['years']),r['lo'],r['id']),reverse=True)
selected=closed[:10]
pending=next(r for r in pool if r['recipe']=={'S61.8':['fixed',100.0,'factor',1.0]});assert pending['pending']==20 and pending['lo']==2075 and pending['hi']==7300
# Recalculate chosen closed curves independently from the financial source rows.
base=read(E/'resultado_niveis_202401_202610_20261117/CURVAS_DIARIAS_POR_NIVEL.csv');days=sorted({r['date'] for r in base});daily_by_level={l:np.array([float(next(r['points'] for r in base if r['date']==d and r['level']==l)) for d in days]) for l in ['R38.2','R61.8','S38.2','S50','S61.8']}
raw=read(E/'fechamento_variante_r61_750_150_20261117/CURVA_DIARIA_VARIANTE_FECHADA.csv');assert [r['date'] for r in raw]==days
r61new=np.array([float(r['variant_R61_points']) for r in raw]);focused=read(E/'estudo_s61_saidas_20261117/LIMITES_POR_OPERACAO.csv');di={d:i for i,d in enumerate(days)}
s61x4=np.zeros(len(days));opcounts={l:np.zeros(len(days),dtype=int) for l in daily_by_level}
for r in read(E/'resultado_niveis_202401_202610_20261117/OPERACOES_NORMALIZADAS.csv'):opcounts[r['level']][di[r['date']]]+=1
for r in focused:
 if r['variant']=='S61_05':assert r['lower']==r['upper'];s61x4[di[r['date']]]=float(r['lower'])
labels={'R38.2':'R38','R61.8':'R61','S38.2':'S38','S50':'S50','S61.8':'S61'}
def describe(recipe):
 parts=[]
 for l in ['R38.2','R61.8','S38.2','S50','S61.8']:
  if l not in recipe:continue
  rule=recipe[l];label=labels[l]
  if rule==['ORIGINAL']:pass
  elif l=='R61.8' and rule==['fixed',150.0,'fixed',750.0]:label+=' novo'
  elif l=='S61.8' and rule==['fixed',650.0,'factor',4.0]:label+=' alvo4x'
  elif l=='S61.8' and rule==['fixed',100.0,'factor',1.0]:label+=' stop100 (pendente)'
  else:label+=' '+json.dumps(rule,ensure_ascii=False)
  parts.append(label)
 return ' + '.join(parts)
rank=[];curves=[]
for i,r in enumerate(selected,1):
 a=np.zeros(len(days));counts=np.zeros(len(days),dtype=int)
 for l,rule in r['recipe'].items():
  if rule==['ORIGINAL']:a+=daily_by_level[l]
  elif l=='R61.8' and rule==['fixed',150.0,'fixed',750.0]:a+=r61new
  elif l=='S61.8' and rule==['fixed',650.0,'factor',4.0]:a+=s61x4
  else:raise AssertionError((r['id'],l,rule))
  counts+=opcounts[l]
 assert a.sum()==r['lo']==r['hi'] and dd(a)==r['ddhi']==r['ddlo'],r
 annual=[float(a[np.array([d.startswith(str(y)) for d in days])].sum()) for y in [2024,2025,2026]];assert annual==r['years']
 row=dict(rank=i,scenario_id=r['id'],configuration=describe(r['recipe']),year2024=annual[0],year2025=annual[1],year2026_JanOct=annual[2],total=r['lo'],DD_continuous=r['ddhi'],positive_years=r['positive_years'],points_per_DD=r['points_per_DD'],operations=int(counts.sum()),status='FECHADO_SOB_METODOLOGIA',pending_operations=0,ranking_origin='ALGORITMO_ANOS_POSITIVOS_DEPOIS_PONTOS_DD')
 rank.append(row)
 for j,day in enumerate(days):curves.append(dict(rank=i,date=day,points=a[j]))
row11=dict(rank=11,scenario_id=pending['id'],configuration=describe(pending['recipe']),year2024=span(pending['years'][0],pending['yearshi'][0]),year2025=span(pending['years'][1],pending['yearshi'][1]),year2026_JanOct=span(pending['years'][2],pending['yearshi'][2]),total=span(pending['lo'],pending['hi']),DD_continuous=span(pending['ddlo'],pending['ddhi']),positive_years='PENDENTE',points_per_DD='PENDENTE',operations=233,status='PENDENTE_INCLUSAO_MANUAL_SOLICITADA',pending_operations=20,ranking_origin='POSICAO11_RESERVADA_PELO_USUARIO')
rank.append(row11);write('RANKING_10_MAIS_PENDENTE.csv',rank);write('CURVAS_DIARIAS_10_CENARIOS.csv',curves)
# Full eligible universe retained for checking alternative risk preferences.
eligible=[dict(position=i+1,scenario_id=r['id'],configuration=describe(r['recipe']),year2024=r['years'][0],year2025=r['years'][1],year2026_JanOct=r['years'][2],total=r['lo'],DD=r['ddhi'],positive_years=r['positive_years'],points_per_DD=r['points_per_DD']) for i,r in enumerate(closed)];write('42_OPCOES_FECHADAS_POSITIVAS.csv',eligible)
wb=openpyxl.Workbook();wb.remove(wb.active)
for name,rows in [('Ranking_11',rank),('42_Elegiveis',eligible),('Curvas_10',curves)]:
 sh=wb.create_sheet(name);keys=list(rows[0]);sh.append(keys)
 for r in rows:sh.append([r[k] for k in keys])
 sh.freeze_panes='A2';sh.auto_filter.ref=sh.dimensions
 for c in sh[1]:c.fill=PatternFill('solid',fgColor='17354E');c.font=Font(color='FFFFFF',bold=True)
 for col in sh.columns:sh.column_dimensions[col[0].column_letter].width=min(65,max(14,max(len(str(c.value or '')) for c in list(col)[:60])+2))
wb.save(P/'Ranking_10_Opcoes_e_Stop100_Pendente.xlsx')
# PDF table and rule definitions, enough to review ranking without code.
c=canvas.Canvas(str(P/'Ranking_10_Opcoes_e_Stop100_Pendente.pdf'),pagesize=landscape(A4));W,H=landscape(A4);c.setTitle('Ranking de cenários — pontos anuais e drawdown')
c.setFillColorRGB(.06,.16,.25);c.rect(0,H-78,W,78,fill=1,stroke=0);c.setFillColorRGB(1,1,1);c.setFont('Helvetica-Bold',19);c.drawString(28,H-31,'Ranking | Pontos anuais e DD contínuo');c.setFont('Helvetica',10);c.drawString(28,H-54,'2024/2025 completos | 2026: janeiro a outubro | resultados brutos, sem custos');c.setFillColorRGB(.06,.16,.25)
xs=[28,64,382,475,570,673,795];y=H-108;c.setFont('Helvetica-Bold',9)
for x,t in zip(xs,['#','Configuração','2024','2025','2026*','Total','DD']):(c.drawString if x in [28,64] else c.drawRightString)(x,y,t)
for j,r in enumerate(rank):
 y-=29
 if j%2==0:c.setFillColorRGB(.94,.96,.98);c.rect(22,y-10,W-44,27,fill=1,stroke=0)
 c.setFillColorRGB(.06,.16,.25);c.setFont('Helvetica-Bold' if r['rank']==11 else 'Helvetica',8)
 c.drawString(xs[0],y,str(r['rank']));c.drawString(xs[1],y,r['configuration'])
 for x,k in zip(xs[2:],['year2024','year2025','year2026_JanOct','total','DD_continuous']):c.drawRightString(x,y,n(r[k]) if isinstance(r[k],(float,int)) else r[k])
y-=29;c.setFont('Helvetica',9)
notes=['Ordem: mais anos positivos primeiro; dentro do grupo, maior total/DD. Apenas resultados sem pendências nas10primeiras.','R61 novo: alvo750/stop150. S61 alvo4x: stop650;alvo=entrada+4vezes a distância original atéS50,arredondado à grade5.','Níveis sem indicação usam parâmetros originais. Níveis não citados estão excluídos.','11ªposição:inclusão solicitada,não posição calculada;S61isolado,stop100,alvoS50original,20operações pendentes.','DD por fechamentos diários contínuos desdejaneiro2024,sem reinício mensal. Custos podem inverter pequenos ganhos anuais.']
for note in notes:c.drawString(28,y,note);y-=16
c.setFont('Helvetica',8);c.drawString(28,22,'18/11/2026 | Ranking descritivo de grade finita; não é aprovação de variante ou validação futura independente.');c.showPage()
c.setFont('Helvetica-Bold',18);c.drawString(30,H-40,'Critério, regras e limites');c.setFont('Helvetica',11);y=H-78
for t in ['Universo:1711configuraçõesconsolidadas;42comresultado fechado ebruto total positivo. Mesmasreceitasrepetidas foram consolidadas.',
'A classificaçãoprioriza não ter ano negativo. Só depois usa a eficiência total/DD. Essa preferência pode mudar o ranking emrelação amaior lucro puro.',
'Por isso o#1 tem2024apenas+140pontos e o#5 tem2026apenas+15. São ganhos frágeis:os custos podem tornar esses anos negativos.',
'Não são as dezmaiores somas brutas. É uma ordem explícita de consistência anual e DD. A planilha contém as42elegíveis paraoutraordenação.',
'R61original:stop450 ealvooriginal doModeloD. R61novo:stop150 ealvo750pontos,comasmesmasentradas originais.',
'S61original:stop650 ealvoS50original. S61alvo4x:stop650 ealvoquatrovezes a distância original daentrada atéS50.',
'R38,S38eS50 na tabela mantêm parâmetros originais. Umcontrato/nível,sem redistribuição de tamanho,corte18h,semreentrada.',
'A opção11não participou da classificação. Os intervalos refletem a sequênciaaindaambígua;os limites não são lucro realizado ou probabilidade.',
'As dezcurvas foram recalculadas dia a dia e conferidas com pontosanuais eDD dosarquivos deorigem. Os resultados fechados originais não foram alterados.',
'O histórico inteiro já eraconhecido. Selecionar resultados nestebanco não comprova estabilidade futura. Sem custos/slippage,fila ougarantia defills.']:
 import textwrap,re
 t=re.sub(r'(?<=[a-zà-ÿ])(?=\d)|(?<=\d)(?=[a-zà-ÿ])',' ',t)
 for line in textwrap.wrap(t,125):c.drawString(30,y,line);y-=15
 y-=12
c.setFont('Helvetica',8);c.drawString(30,22,'18/11/2026 | D original preservado | 11ªopção é pendente e não foi promovida a resultado fechado.');c.save()
doc=fitz.open(P/'Ranking_10_Opcoes_e_Stop100_Pendente.pdf');assert len(doc)==2
manifest=dict(date='2026-11-18',scope='ALL_PRIOR_TESTED_PORTFOLIOS_AND_FOCUSED_S61',consolidated_recipes=len(pool),eligible_closed_positive=len(closed),ranking_rule=['positive_years_desc','total_points_divided_by_continuous_daily_DD_desc','worst_year_points_desc','total_desc','id_desc'],gross_only=True,year2026_scope='JanOct',rank11_manually_reserved=True,rank11_pending_operations=20,all10_daily_curves_independently_recomputed=True,source_files=sources)
(P/'MANIFESTO.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');(P/'.gitattributes').write_text('*.pdf binary\n*.xlsx binary\n');(P/'.gitignore').write_text('__pycache__/\n')
(P/'LEIA_PRIMEIRO.md').write_text('''# Ranking de consistência anual e DD — 18/11/2026

Todos os estudos prévios foram considerados:exclusões,receitasmistas,fechamentoR61750/150 e88receitasS61 comcombinaçõesR61. Configurações iguais consolidadas,priorizando fonte maisatual. Universo1711receitas,42fechadas comtotalpositivo. As10primeiras são classificadas primeiro pelo número deanos positivos, depois por pontos totais/DD diário contínuo. Empates usam piorano,total eID. É critério definido paraesta tabela,não ranking universal ou maior lucro puro.

A11ªposição foi reservada pelo usuário aoS61isolado,stop100,alvoS50original;20operações pendentes. Ela não participou da disputa nem deve ser interpretada como resultado fechado. Nenhuma outra opção pendente entra nas10primeiras.

2024/2025completos;2026janeiro-outubro. Valoresbrutos,sem custos. #1tem2024+140 e#5tem2026+15,ganhos frágeis antes decustos. A classificação nãoaprova variantes. Níveis não citadosOFF;semredistribuição decontratos. R61novo:alvo750/stop150;S61alvo4x:stop650 ealvo=entrada+4distâncias atéS50original. Demaisreferências originaiscongeladas.

Curvas dos10recalculadas dia a dia e conferidas comanual,total eDD. Arquivosoriginais intactos. Planilha contémranking,42elegíveis ecurvas. Manifesto trazfontes/hashes;origem de cada receita emUNIVERSO_CONSOLIDADO.json.
''')
print(json.dumps(rank,ensure_ascii=False,indent=2))
