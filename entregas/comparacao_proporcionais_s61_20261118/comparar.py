from pathlib import Path
import csv,json,hashlib,collections,re
import numpy as np
import openpyxl,fitz
from openpyxl.styles import Font,PatternFill
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4,landscape
P=Path(__file__).parent;R=P.parents[1];E=R/'entregas';S=E/'estudo_s61_saidas_20261117';B=E/'ranking_cenarios_20261118';sources=[]
def read(p):
 sources.append(dict(path=str(p.relative_to(R)),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
 with p.open(encoding='utf-8-sig') as f:return list(csv.DictReader(f,delimiter=';'))
def write(name,rows):
 with (P/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter=';',lineterminator='\n');w.writeheader();w.writerows(rows)
def dd(a):
 b=np.cumsum(a);return float(np.max(np.maximum.accumulate(np.r_[0,b])[1:]-b))
def n(v):return f'{float(v):,.0f}'.replace(',','.')
def ran(a,b):return n(a) if a==b else n(a)+' a '+n(b)
def score(r):return r['total_lower']/r['DD_upper']
IDs=['S61_48','S61_52','S61_56','S61_60','S61_64','S61_68','S61_72','S61_76','S61_80','S61_84'];raw={r['id']:r for r in read(S/'RESULTADO_S61_CENARIOS.csv')};params={r['id']:r for r in read(S/'PARAMETROS_CENARIOS.csv')};trade=read(S/'LIMITES_POR_OPERACAO.csv');days=sorted({r['date'] for r in read(E/'resultado_niveis_202401_202610_20261117/CURVAS_DIARIAS_POR_NIVEL.csv')});di={d:i for i,d in enumerate(days)};curves={};counts={}
for id in IDs+['S61_42']:
 lo=np.zeros(len(days));hi=np.zeros(len(days));ct=np.zeros(len(days),dtype=int)
 for r in trade:
  if r['variant']==id:lo[di[r['date']]]=float(r['lower']);hi[di[r['date']]]=float(r['upper']);ct[di[r['date']]]+=1
 assert ct.sum()==233
 orig=raw[id];assert lo.sum()==float(orig['points_lower']) and hi.sum()==float(orig['points_upper'])
 assert dd(lo)==float(orig['DD_upper']) and dd(hi)==float(orig['DD_lower'])
 curves[id]=(lo,hi);counts[id]=ct
# Prove duplicates from the exact distance and outcome of each original entry.
duplicates=[]
for a,b in [('S61_48','S61_68'),('S61_52','S61_72')]:
 aa={r['date']:r for r in trade if r['variant']==a};bb={r['date']:r for r in trade if r['variant']==b};assert aa.keys()==bb.keys()
 for day in aa:
  for k in ['stop_points','target_points','lower','upper']:assert float(aa[day][k])==float(bb[day][k])
 maxstop=max(float(r['stop_points']) for r in aa.values());assert maxstop<650
 duplicates.append(dict(a=a,b=b,entries_compared=233,all_distances_and_results_equal=True,max_stop_observed=maxstop,cap_bind_count=0))
write('EQUIVALENCIAS_CONFERIDAS.csv',duplicates)

def row(id,label=None):
 r=raw[id];return dict(id=id,label=label or id,total_lower=float(r['points_lower']),total_upper=float(r['points_upper']),DD_lower=float(r['DD_lower']),DD_upper=float(r['DD_upper']),pending=int(r['unresolved']),operations=233,**{f'year{y}_{side}':float(r[f'year{y}_{side}']) for y in [2024,2025,2026] for side in ['lower','upper']})
rank10=[row(id) for id in IDs]
rank10.sort(key=lambda r:(-score(r),r['id']))
last=None;dense=0
for r in rank10:
 sc=score(r)
 if last is None or sc!=last:dense+=1;last=sc
 r.update(rank=dense,conservative_points_per_DD=sc,positive_years_lower=sum(r[f'year{y}_lower']>0 for y in [2024,2025,2026]))
write('RANKING_10_CODIGOS.csv',rank10)
# Two distinct strategies, not two labels of the same recipe.
first=next(r for r in rank10 if r['id']=='S61_48').copy();first['label']='S61_48 = S61_68 (stop 0,5x alvo)'
second=next(r for r in rank10 if r['id']=='S61_60').copy();second['label']='S61_60 (stop 1,5x alvo, sem teto)'
confront=[first,second,row('S61_42','S61 stop 100, alvo original')]
previous=read(B/'RANKING_10_MAIS_PENDENTE.csv');prevcurves=read(B/'CURVAS_DIARIAS_10_CENARIOS.csv');origops=read(E/'resultado_niveis_202401_202610_20261117/OPERACOES_NORMALIZADAS.csv')
oldids=[]
for position,levels,label in [(1,['R61.8','S50','S61.8'],'Anterior 1: R61 + S50 + S61 originais'),(2,['R61.8','S61.8'],'Anterior 2: R61 novo + S61 alvo4x')]:
 orig=next(r for r in previous if int(r['rank'])==position);id='ANTERIOR_'+str(position);a=np.zeros(len(days));ct=np.zeros(len(days),dtype=int)
 for r in prevcurves:
  if int(r['rank'])==position:a[di[r['date']]]=float(r['points'])
 for r in origops:
  if r['level'] in levels:ct[di[r['date']]]+=1
 assert a.sum()==float(orig['total']) and dd(a)==float(orig['DD_continuous'])
 rr=dict(id=id,label=label,total_lower=float(a.sum()),total_upper=float(a.sum()),DD_lower=dd(a),DD_upper=dd(a),pending=0,operations=int(ct.sum()))
 for y in [2024,2025,2026]:v=float(a[np.array([day.startswith(str(y)) for day in days])].sum());rr[f'year{y}_lower']=rr[f'year{y}_upper']=v
 curves[id]=(a,a.copy());counts[id]=ct;confront.append(rr);oldids.append(id)
confront.sort(key=lambda r:(-score(r),r['id']))
for i,r in enumerate(confront,1):r.update(rank=i,conservative_points_per_DD=score(r),positive_years_lower=sum(r[f'year{y}_lower']>0 for y in [2024,2025,2026]))
# Normalize dictionary ordering for tabular exports.
keys=['rank','id','label','total_lower','total_upper','DD_lower','DD_upper','conservative_points_per_DD','pending','operations','positive_years_lower']+[f'year{y}_{s}' for y in [2024,2025,2026] for s in ['lower','upper']]
confront=[{k:r[k] for k in keys} for r in confront];write('CONFRONTO_5_OPCOES.csv',confront)
annual=[];sensitivity=[]
for r in confront:
 id=r['id'];lo,hi=curves[id];ct=counts[id]
 for y in [2024,2025,2026]:
  mask=np.array([day.startswith(str(y)) for day in days]);annual.append(dict(id=id,label=r['label'],year=y,scope='JanOut' if y==2026 else 'AnoCompleto',points_lower=float(lo[mask].sum()),points_upper=float(hi[mask].sum()),DD_year_lower=dd(hi[mask]),DD_year_upper=dd(lo[mask]),operations=int(ct[mask].sum())))
 for fee in [0,5,10]:
  aa=lo-fee*ct;bb=hi-fee*ct;floor=float(aa.sum());upperdd=dd(aa)
  sensitivity.append(dict(cost_points_per_complete_trade=fee,id=id,label=r['label'],points_lower=floor,points_upper=float(bb.sum()),DD_lower=dd(bb),DD_upper=upperdd,conservative_points_per_DD=floor/upperdd,operations=int(ct.sum())))
for fee in [0,5,10]:
 group=sorted([r for r in sensitivity if r['cost_points_per_complete_trade']==fee],key=lambda r:r['conservative_points_per_DD'],reverse=True)
 for i,r in enumerate(group,1):r['rank_within_cost_sensitivity']=i
write('ANUAIS_5_OPCOES.csv',annual);write('SENSIBILIDADE_CUSTOS_5_OPCOES.csv',sensitivity)
oldcriteria=sorted(confront,key=lambda r:(r['positive_years_lower'],score(r)),reverse=True)
write('CONFRONTO_CRITERIO_ANUAL_ANTERIOR.csv',[dict(rank=i+1,id=r['id'],positive_years_lower=r['positive_years_lower'],score=score(r)) for i,r in enumerate(oldcriteria)])
# Workbook complete, including the alternative criterion and hypothetical cost effects.
wb=openpyxl.Workbook();wb.remove(wb.active)
for name,rs in [('Ranking10',rank10),('Confronto5',confront),('Anuais5',annual),('Custos',sensitivity),('Equivalencias',duplicates),('Criterio_Anterior',read(P/'CONFRONTO_CRITERIO_ANUAL_ANTERIOR.csv'))]:
 sh=wb.create_sheet(name);ks=list(rs[0]);sh.append(ks)
 for r in rs:sh.append([r[k] for k in ks])
 sh.freeze_panes='A2';sh.auto_filter.ref=sh.dimensions
 for c in sh[1]:c.fill=PatternFill('solid',fgColor='17354E');c.font=Font(color='FFFFFF',bold=True)
 for col in sh.columns:sh.column_dimensions[col[0].column_letter].width=min(65,max(15,max(len(str(c.value or '')) for c in list(col)[:60])+2))
wb.save(P/'Ranking_Proporcionais_e_Confronto_5.xlsx')
# PDF on compact comparison pages, all intervals explicit.
c=canvas.Canvas(str(P/'Ranking_Proporcionais_e_Confronto_5.pdf'),pagesize=landscape(A4));W,H=landscape(A4);page=0;y=0

def new(title,subtitle='Pontos brutos | 2024/2025 completos | 2026: janeiro a outubro'):
 global page,y
 if page:c.showPage()
 page+=1;c.setFillColorRGB(.06,.16,.25);c.rect(0,H-72,W,72,fill=1,stroke=0);c.setFillColorRGB(1,1,1);c.setFont('Helvetica-Bold',17);c.drawString(28,H-29,title);c.setFont('Helvetica',10);c.drawString(28,H-51,subtitle);c.setFillColorRGB(.06,.16,.25);y=H-105;c.setFont('Helvetica',8);c.drawString(28,22,f'18/11/2026 | Critério quantitativo explícito, não aprovação para operar | Página {page}')
def line(t,bold=False):
 global y
 t=re.sub(r'(?<=[a-zà-ÿ])(?=\d)|(?<=\d)(?=[a-zà-ÿ])',' ',t)
 t=re.sub(r'(?<=DD)(?=\d)',' ',t)
 t=re.sub(r';(?=\S)','; ',t)
 t=re.sub(r',(?=[A-Za-zÀ-ÿ])',', ',t)
 import textwrap
 c.setFont('Helvetica-Bold' if bold else 'Helvetica',10)
 for ln in textwrap.wrap(t,130):c.drawString(28,y,ln);y-=15
 y-=6

def table(rows):
 global y
 xs=[28,70,354,481,586,675,779];c.setFont('Helvetica-Bold',9)
 for x,t in zip(xs,['#','Opção','Total em pontos','DD diário','Índice','Pend.','Operações']):(c.drawString if x in [28,70] else c.drawRightString)(x,y,t)
 y-=8
 for i,r in enumerate(rows):
  y-=29
  if i%2==0:c.setFillColorRGB(.94,.96,.98);c.rect(22,y-10,W-44,27,fill=1,stroke=0)
  c.setFillColorRGB(.06,.16,.25);c.setFont('Helvetica',9);c.drawString(xs[0],y,str(r['rank']));c.drawString(xs[1],y,r['label'])
  for x,t in zip(xs[2:],[ran(r['total_lower'],r['total_upper']),ran(r['DD_lower'],r['DD_upper']),f"{score(r):.3f}",str(r['pending']),str(r['operations'])]):c.drawRightString(x,y,t)
 y-=30
new('Ranking das10opções proporcionais')
table(rank10)
line('Índice = pontos totais no limite inferior / DD contínuo no limite superior. Maior é melhor para este critério.',True)
line('Não se usou máximo de pontos nem mínimo deDD para favorecer pendentes. Todas as10opções ainda têm pendências.')
line('Empates reais:48=68 e52=72 nas233entradas. Os tetos650 nunca alteraram essas receitas;maxstop390e580,respectivamente.')
line('Há oito estratégias distintas. No confronto usamos as duas melhores distintas:48/68e60,em vez de repetir a mesma receita.')
new('Confronto | Duas melhores distintas + anteriores + stop100')
table(confront)
line('Anterior1: R61,S50,S61 comsaídasoriginais;786operações. OutrosníveisOFF.')
line('Anterior2: R61alvo750/stop150 + S61stop650/alvo4x a distância original;488operações. OutrosOFF.')
line('Stop100:S61isolado,alvoS50original;233operações. Sua posição foi calculada,não reservada.',True)
line('As três primeiras neste critério estão pendentes. Liderança de índice não torna o resultado certificado.')
new('Comparação anual | Cinco opções')
for r in confront:
 line(str(r['rank'])+'º | '+r['label'],True)
 line('2024: '+ran(r['year2024_lower'],r['year2024_upper'])+' | 2025: '+ran(r['year2025_lower'],r['year2025_upper'])+' | 2026*: '+ran(r['year2026_lower'],r['year2026_upper']))
 y-=6
line('S61_60 tem os três pisos anuais positivos:1.175,2.410e960. Stop100pode ter2024negativo (-210).',True)
line('As48/68também têm pisos positivos,mas2024+240 e2026+280 são ganhos pequenos antes decustos.')
new('Custos, critério anterior e limites')
line('Esta ordem difere do ranking anterior:antes a prioridade era número deanos positivos e depois pontos/DD. Aqui o foco principal é o índice conservador pontos/DD,conforme solicitado.',True)
line('Se mantivermos a prioridade anual anterior,a ordem no confronto seria:48/68,60,Anterior1,Anterior2,Stop100. Nesse caso o100fica emúltimo por2024poder sernegativo,não porposiçãoreservada.')
line('Custo hipotético por operação completa:')
for fee in [5,10]:
 group=sorted([r for r in sensitivity if r['cost_points_per_complete_trade']==fee],key=lambda r:r['rank_within_cost_sensitivity'])
 line(str(fee)+' pontos: '+' > '.join(r['id'] for r in group))
line('Stop100:limiteinferior bruto2.075;comcusto5vira910;comcusto10vira-255. ODD também foi recalculado comcustos na planilha. São sensibilidades,não taxas reais.',True)
line('Faixas não são lucro realizado,previsão nem duas trajetórias comprovadas. Os limites podem ser conservadores; a sequência dos negócios pode estreitá-los. Nenhuma pendência foi arbitrada favoravelmente.')
line('Stops proporcionais variam por operação. O teto650éirrelevante nas48/68e52/72nestaamostra,mas altera osoutros pares. S61_60semteto pode passar650; não é igual à80.')
line('As entradas,referências,tamanho e resultados originais foram preservados. DDporfechamentosdiários,contínuo,sem reinício mensal. A comparação é histórica e exploratória.')
c.save();doc=fitz.open(P/'Ranking_Proporcionais_e_Confronto_5.pdf');assert len(doc)==4
manifest=dict(date='2026-11-18',ranking_metric='TOTAL_LOWER_DIVIDED_BY_DD_UPPER',earlier_ranking_had_different_priority=True,requested_options=10,distinct_options=8,duplicate_pairs=[['S61_48','S61_68'],['S61_52','S61_72']],comparison_count=5,stop100_not_manually_positioned=True,all_curves_scores_totals_and_DD_recomputed=True,main_ranking_gross=True,costs_hypothetical=True,original_results_unchanged=True,sources=sources)
(P/'MANIFESTO.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');(P/'.gitattributes').write_text('*.pdf binary\n*.xlsx binary\n');(P/'.gitignore').write_text('__pycache__/\n')
(P/'LEIA_PRIMEIRO.md').write_text('''# Proporcionais S61 — ranking e confronto

Critério principal: limite inferior de pontos totais dividido pelo limite superior doDD diário contínuo. Ranking bruto,maior índice primeiro. Diferente do ranking anterior,que priorizava número deanos positivos. A alternativa comcritérioanterior consta emCSV/planilha.

Dezcódigos representam oitoconfigurações distintas noacervo:48=68 e52=72,conferidos em233operações comstop,alvo e limites iguais. Usaram-se48/68e60como as duasmelhores distintas. Confronto inclui as duasprimeiras do ranking anterior eS61stop100/alvooriginal,semposiçãoreservada.

Confronto peloíndice:stop100;48/68;60;Anterior1R61+S50+S61originais;Anterior2R61alvo750/stop150+S61stop650/alvo4x. As trêsprimeiras são pendentes; não confundir liderança de índice comresultado fechado. Pelo critérioanual antigo:48/68,60,Anterior1,Anterior2,stop100.

Custos5/10pontos poroperação são sensibilidades e mudamranking;DD recalculado também.2026janeiro-outubro. PDF4páginas eXLSX incluemanuais,pendências,DD,pontos/risco e fontes. Dados originais preservados.
''')
print('RANKING10',[(r['rank'],r['id'],round(score(r),3)) for r in rank10]);print('CONFRONTO',[(r['rank'],r['id'],round(score(r),3)) for r in confront]);print('CUSTOS',[(r['cost_points_per_complete_trade'],r['rank_within_cost_sensitivity'],r['id']) for r in sensitivity])
