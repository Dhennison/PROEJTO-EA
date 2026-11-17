from pathlib import Path
from decimal import Decimal as D
import csv,json,pickle,hashlib,collections,textwrap
import numpy as np
import openpyxl,fitz
from openpyxl.styles import Font,PatternFill
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
P=Path(__file__).parent;BASE=P.parent;R=BASE.parents[1];E=R/'entregas';cache=Path('/workspace/work/cedro_recuperado/resultados_atualizados.pickle');data=pickle.loads(cache.read_bytes());days=data['data']['days'];levels=['R38.2','R61.8','S38.2','S50','S61.8'];cfg={c['id']:i for i,c in enumerate(data['cfg'])}
def read(p):
 with p.open(encoding='utf-8-sig') as f:return list(csv.DictReader(f,delimiter=';'))
def write(name,rs):
 with (P/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rs[0]),delimiter=';',lineterminator='\n');w.writeheader();w.writerows(rs)
def dd(a):
 b=np.cumsum(a);return float(np.max(np.maximum.accumulate(np.r_[0,b])[1:]-b))
# Historical receipts prove files were sent, independently of current availability.
proof=collections.defaultdict(list)
for p in E.rglob('PARTES_*.csv'):
 if 'cedro' not in str(p).lower():continue
 for r in read(p):
  name=r.get('arquivo','');sha=r.get('sha256','');ok=r.get('hash_OK',r.get('OK',''))
  if name.startswith('WIN_2026') and ok.lower()=='true':proof[name].append(dict(path=str(p.relative_to(R)),sha256=sha))
archive=read(E/'cedro_extrator_win_v1_00/retorno_geral_20261112/ARQUIVOS.csv');trace=[]
for r in archive:
 if r['tipo']!='WIN_ZIP':continue
 ev=[e for e in proof[r['arquivo']] if e['sha256']==r['sha256']]
 trace.append(dict(file=r['arquivo'],sha256=r['sha256'],historical_receipt_hash_confirmed=bool(ev),receipt_documents='|'.join(e['path'] for e in ev),current_session_raw_path_exists=any(p.exists() for p in [Path('/workspace/retorno_cedro_20261112/ticks')/r['arquivo'],Path('/workspace/dados_brutos_modelo_d/cedro')/r['arquivo']]),original_month_result_included=True))
write('RASTREAMENTO_RECEBIMENTO_CEDRO.csv',trace)
# All scenario yearly results, with year-only DD separated from global DD.
rows=[];lookup={}
for r in data['scenarios']+data['subsets']:
 id=r['id'];a,b=data['scenario_daily'][id]
 if id.startswith('EXC_'):
  use={levels.index(l):0 for l in r['levels'].split('|')};description=r['levels']+';saídas originais'
 elif r['family']=='SAME_RULE_ALL_LEVELS':use={i:cfg[id] for i in range(5)};description=r['rule']
 else:
  use={levels.index(l):cfg[v] for l,v in (x.split(':') for x in r['rule'].split('|')) if v!='OFF'};description=r['rule']
 for year in ['2024','2025','2026']:
  mask=np.array([day.startswith(year) for day in days]);aa=a[mask];bb=b[mask];n=sum(data['counts'][mask,i].sum() for i in use);u=sum(data['uncertain'][ci,mask,i].sum() for i,ci in use.items());lo=float(aa.sum());hi=float(bb.sum())
  assert lo==r['year'+year+('_JanOct' if year=='2026' else '')+'_lower']
  assert hi==r['year'+year+('_JanOct' if year=='2026' else '')+'_upper']
  rr=dict(scenario=id,year=year,scope='Janeiro a Outubro' if year=='2026' else 'Janeiro a Dezembro',configuration=description,points_lower=lo,points_upper=hi,DD_year_lower=dd(bb),DD_year_upper=dd(aa),operations=int(n),unresolved_operations=int(u),status='DETERMINADO_SOB_METODOLOGIA' if u==0 else 'FAIXA_NAO_FECHADA',points_cost5_lower=lo-5*n,points_cost5_upper=hi-5*n,points_cost10_lower=lo-10*n,points_cost10_upper=hi-10*n)
  rows.append(rr);lookup[(id,year)]=rr
write('RESULTADO_ANUAL_TODOS_CENARIOS.csv',rows)
ids=['D_ORIGINAL','EXC_19','EXC_18','EXC_26','EXC_16','EXC_02','MIX_0161'];labels={'D_ORIGINAL':'D completo original','EXC_19':'R38,2 + R61,8 + S61,8 originais','EXC_18':'R61,8 + S61,8 originais','EXC_26':'R61,8 + S50 + S61,8 originais','EXC_16':'Somente S61,8 original','EXC_02':'Somente R61,8 original','MIX_0161':'R61,8 alvo750/stop150 + S61,8 original'}
selected=[dict(label=labels[id],**lookup[(id,y)]) for y in ['2024','2025','2026'] for id in ids];write('RESULTADO_ANUAL_DESTAQUES.csv',selected)
wb=openpyxl.Workbook();wb.remove(wb.active)
for name,rs in [('Destaques',selected),('2024',[r for r in rows if r['year']=='2024']),('2025',[r for r in rows if r['year']=='2025']),('2026_Jan_Out',[r for r in rows if r['year']=='2026']),('Cedro_Recebido',trace)]:
 sh=wb.create_sheet(name);keys=list(rs[0]);sh.append(keys)
 for r in rs:sh.append([r[k] for k in keys])
 sh.freeze_panes='A2';sh.auto_filter.ref=sh.dimensions
 for c in sh[1]:c.fill=PatternFill('solid',fgColor='17354E');c.font=Font(color='FFFFFF',bold=True)
 for col in sh.columns:sh.column_dimensions[col[0].column_letter].width=min(65,max(15,max(len(str(c.value or '')) for c in list(col)[:70])+2))
wb.save(P/'Cenarios_Resultados_Anuais_2024_2025_2026.xlsx')
def n(v):return f'{v:,.0f}'.replace(',','.')
def range2(a,b):return n(a) if a==b else n(a)+' a '+n(b)
c=canvas.Canvas(str(P/'Cenarios_Resultados_Anuais_2024_2025_2026.pdf'),pagesize=A4);c.setTitle('Cenários — resultados anuais2024,2025 e2026jan-out')
for year in ['2024','2025','2026']:
 c.setFillColorRGB(.06,.16,.25);c.rect(0,758,595,84,fill=1,stroke=0);c.setFillColorRGB(1,1,1);c.setFont('Helvetica-Bold',22);c.drawString(32,806,year+' | Comparação anual');c.setFont('Helvetica',11);c.drawString(32,782,'Janeiro a outubro' if year=='2026' else 'Janeiro a dezembro');c.setFillColorRGB(.06,.16,.25);y=726
 for id in ids:
  r=lookup[(id,year)];c.setFont('Helvetica-Bold',11);c.drawString(32,y,labels[id]);y-=19;c.setFont('Helvetica',10)
  c.drawString(32,y,'Pontos: '+range2(r['points_lower'],r['points_upper'])+' | Operações: '+str(r['operations']));y-=17
  c.drawString(32,y,'DD isolado do ano: '+range2(r['DD_year_lower'],r['DD_year_upper'])+' | Pendentes: '+str(r['unresolved_operations']));y-=27
 c.setFont('Helvetica',9)
 for t in ['Pontos brutos. DD pelos fechamentos diários do próprio ano, começando em zero.','Este DD anual é diagnóstico adicional e não substitui o DD contínuo do período completo.','Faixa: resultado não fechado. Limites não são lucro realizado nem trajetória certificada.','2026 já inclui agosto, setembro e outubro Cedro nos cenários de saídas originais.','Variante750/150 fechada após recuperar os16ZIPs de oito datas Cedro deagosto.']:
  c.drawString(32,y,t);y-=15
 c.setFont('Helvetica',8);c.drawString(32,28,'17/11/2026 | Modelo D original preservado | Sem comparação com Work');c.showPage()
c.setFont('Helvetica-Bold',18);c.drawString(32,795,'Critérios e rastreamento Cedro');c.setFont('Helvetica',10);y=760
paragraphs=[
'Os cenários mostrados anteriormente eram destaques por critérios diferentes, não vencedores absolutos ou configurações comprovadamente melhores em todas as dimensões.',
'Maior total exato nas31exclusões: R38,2+R61,8+S61,8,6.055pontos. Melhor relação pontos/DD entre exclusões positivas: R61,8+S61,8,5.890pontos/DD5.505. MenorDD entre exclusões positivas: somenteR61,8,825pontos/DD2.545. Esses critérios não coincidem.',
'A variante750/150 foi fechada após recuperação dos16ZIPs:2024+6155,2025+6115,2026jan-out-4345,total7925,DDcontínuo7780. Isso não a torna estável ou aprovada para operar. A busca usou175receitas e1.279mistos; não abrange todos os parâmetros possíveis.',
f'Os logs Cedro foram enviados anteriormente: localizados{sum(r["historical_receipt_hash_confirmed"] for r in trace)}comprovantes de partes com hash correspondente ao manifesto. A expressão arquivos faltando foi imprecisa: 16ZIPs foram recuperados nesta sessão,fechando a variante750/150;isso não significa que os demais não tenham sido enviados.',
'Os resultados originais dos três meses Cedro são agosto-2.375,setembro+2.855,outubro+3.830, incluídos no resultado original de2026+8.940. Não é necessário recalcular ou excluir esses meses para entregar a comparação anual original.',
'Busca realizada nos arquivos locais, anexos atuais, downloads compartilhados, históricoGit e ReleaseGitHub consultada. Os16ZIPs prioritários foram recuperados e reprocessados;os116demais não estão disponíveis neste ambiente. Isso não impede o fechamento da variante750/150. A Release contém as planilhas Replay2024e2025. Não é possível reconstituir negócios individuais a partir de totais de auditoria.',
'As saídas750/150 das oito operações foram STOP-150,total-1200;nenhuma pendência nessa variante. Outras receitas mantêm limitações próprias. Não repetir automaticamente toda a coleta. RASTREAMENTO_RECEBIMENTO_CEDRO.csv discrimina prova de recebimento e disponibilidade atual.',
'Resultados anuais de todos os1.485cenários estão na planilha eCSV.2026 corresponde a janeiro-outubro. Todos os resultados originais e os relatórios anteriores permanecem preservados.'
]
import re
for p in paragraphs:
 p=re.sub(r'(?<=[a-zà-ÿ])(?=\d)|(?<=\d)(?=[a-zà-ÿ])',' ',p)
 for line in textwrap.wrap(p,96):c.drawString(32,y,line);y-=15
 y-=12
c.setFont('Helvetica',8);c.drawString(32,28,'17/11/2026 | Comparação anual | Sem alteração dos resultados fechados');c.save()
doc=fitz.open(P/'Cenarios_Resultados_Anuais_2024_2025_2026.pdf');assert len(doc)==4
summary=dict(years=['2024','2025','2026JanOct'],scenarios=len(data['scenarios'])+len(data['subsets']),annual_rows=len(rows),cedro_parts_previously_received_hash_proofs=sum(r['historical_receipt_hash_confirmed'] for r in trace),raw_parts_listed=len(trace),current_session_available_parts=sum(r['current_session_raw_path_exists'] for r in trace),original_2026_includes_full_Cedro_AugOct=True,changed_exits_2026_candidate_still_bounded=False,previous_user_delivery_not_in_question=True)
(P/'MANIFESTO_ANUAL.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
(P/'LEIA_PRIMEIRO.md').write_text('''# Comparação anual dos cenários

PDF com páginas separadas para2024,2025e2026janeiro-outubro;planilha eCSVcontêm todos os1.485cenários em cada ano. Pontos brutos,DD anual isolado,operações,pendências e sensibilidades de custo. DD anual isolado não substitui oDDcontínuo global.

Correção sobreCedro: os arquivos foram enviados e recebidos anteriormente,com comprovantes dehash. RASTREAMENTO_RECEBIMENTO_CEDRO.csv diferencia isso da disponibilidade dos brutos no ambiente atual. Os16ZIPs prioritários foram recuperados nesta sessão,verificados porhash e reprocessados. Os116demais continuam semcópia local. Ausência local não significa ausência de envio. Os resultados originais Cedro completos já estão incluídos em2026; a variante750/150agora está fechada;demais receitas mantêm limitações próprias.

Maior lucro exato,menorDD e melhorrelação pontos/DD dão rankings diferentes. As listas mostradas são destaques de uma grade finita de testes,não melhores configurações universais. A variante750/150soma6155em2024,6115em2025e-4345em2026jan-out;outroscenários comfaixas continuam pendentes.2026 não foi omitido.
''')
print(json.dumps(summary,ensure_ascii=False,indent=2))
for id in ids:print(id,[range2(lookup[(id,y)]['points_lower'],lookup[(id,y)]['points_upper']) for y in ['2024','2025','2026']])
