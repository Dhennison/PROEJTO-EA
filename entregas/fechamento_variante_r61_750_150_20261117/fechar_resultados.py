from pathlib import Path
from decimal import Decimal as D
import csv,json,pickle,hashlib,itertools
import numpy as np
import openpyxl,fitz
from openpyxl.styles import Font,PatternFill
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
P=Path(__file__).parent;R=P.parents[1];E=R/'entregas';BASE=E/'estudo_saidas_niveis_20261117';cache=pickle.loads(Path('/workspace/work/estudo_saidas/resultados.pickle').read_bytes());days=cache['data']['days'];di={d:i for i,d in enumerate(days)};names=['R38.2','R61.8','S38.2','S50','S61.8'];ci=next(i for i,c in enumerate(cache['cfg']) if c['id']=='V164');l=names.index('R61.8')
def read(p):
 with p.open(encoding='utf-8-sig') as f:return list(csv.DictReader(f,delimiter=';'))
def write(name,rows):
 with (P/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter=';',lineterminator='\n');w.writeheader();w.writerows(rows)
def dd(a):
 b=np.cumsum(a);return float(np.max(np.maximum.accumulate(np.r_[0,b])[1:]-b))
def fmt(v):return f'{float(v):,.0f}'.replace(',','.')
closed=read(P/'OITO_OPERACOES_REPROCESSADAS.csv');assert len(closed)==8
lo=cache['lo'][ci,:,l].copy();hi=cache['hi'][ci,:,l].copy();orig=cache['lo'][0];nops=cache['counts']
for r in closed:
 i=di[r['date']];v=float(r['variant_points']);assert lo[i]<=v<=hi[i];lo[i]=hi[i]=v
assert np.array_equal(lo,hi)
variant=lo+orig[:,4];original_pair=orig[:,1]+orig[:,4];original_d=orig.sum(1)
# Exact variants now have a single daily value; do not overwrite study envelopes.
daily=[];balance=peak=maxdd=0;peakdate='SALDO_ZERO';worst={}
for i,day in enumerate(days):
 balance+=variant[i]
 if balance>peak:peak=balance;peakdate=day
 if peak-balance>maxdd:maxdd=peak-balance;worst=dict(peak_date=peakdate,valley_date=day,peak=peak,valley=balance)
 daily.append(dict(date=day,variant_R61_points=lo[i],original_S61_points=orig[i,4],variant_pair_points=variant[i],original_pair_points=original_pair[i],original_D_points=original_d[i],variant_balance=balance,variant_peak=peak,variant_DD_current=peak-balance,variant_DD_max=maxdd))
write('CURVA_DIARIA_VARIANTE_FECHADA.csv',daily)
annual=[];monthly=[]
for yr in ['2024','2025','2026']:
 mask=np.array([day.startswith(yr) for day in days]);nn=int(nops[mask,1].sum()+nops[mask,4].sum());tot=float(variant[mask].sum())
 annual.append(dict(year=yr,scope='Janeiro a Outubro' if yr=='2026' else 'Ano completo',operations=nn,R61_target750_stop150_points=float(lo[mask].sum()),S61_original_points=float(orig[mask,4].sum()),variant_pair_points=tot,variant_year_DD=dd(variant[mask]),original_pair_points=float(original_pair[mask].sum()),original_pair_year_DD=dd(original_pair[mask]),original_D_points=float(original_d[mask].sum()),points_after_cost5=tot-5*nn,points_after_cost10=tot-10*nn,pending=0))
for m in sorted({day[:7] for day in days}):
 mask=np.array([day.startswith(m) for day in days]);monthly.append(dict(month=m,operations=int(nops[mask,1].sum()+nops[mask,4].sum()),variant_R61_points=float(lo[mask].sum()),original_S61_points=float(orig[mask,4].sum()),variant_pair_points=float(variant[mask].sum()),original_pair_points=float(original_pair[mask].sum()),variant_month_DD=dd(variant[mask]),variant_continuous_DD_end=daily[np.where(mask)[0][-1]]['variant_DD_max']))
write('RESULTADO_ANUAL_VARIANTE_FECHADA.csv',annual);write('RESULTADO_MENSAL_VARIANTE_FECHADA.csv',monthly)
# Retain exact per-operation values for all488original entries in these levels.
allbounds=read(BASE/'LIMITES_POR_OPERACAO.csv');ops=[];rawindex={(r['date'],r['level']):r for r in closed}
for r in allbounds:
 if not (r['variant']=='V164' and r['level']=='R61.8' or r['variant']=='D_ORIGINAL' and r['level']=='S61.8'):continue
 key=(r['date'],r['level']);rr=rawindex.get(key)
 if rr:points=float(rr['variant_points']);source='FULL_CEDRO_RECOVERED_DIRECT_PLUS_INDEPENDENT_PYTHON'
 else:assert float(r['lower'])==float(r['upper']),r;points=float(r['lower']);source='FROZEN_ORIGINAL' if r['level']=='S61.8' else 'M1_PLUS_AVAILABLE_REPLAY_DETERMINED'
 ops.append(dict(date=r['date'],level=r['level'],target_points=r['target_points'],stop_points=r['stop_points'],points=points,source=source))
ops.sort(key=lambda r:(r['date'],r['level']));assert len(ops)==488
assert sum(r['points'] for r in ops)==variant.sum()
write('OPERACOES_488_VARIANTE_FECHADA.csv',ops)
for day in days:assert sum(r['points'] for r in ops if r['date']==day)==variant[di[day]]
# All16combinations now closed with R61new and other original levels either ON/OFF.
combinations=[]
for mask in range(16):
 others=[j for bit,j in enumerate([0,2,3,4]) if mask>>bit&1];a=lo+orig[:,others].sum(1) if others else lo.copy();nn=int(nops[:,[1]+others].sum());r=dict(id=f'R61_750_150_M{mask:02d}',levels='R61.8_NOVO'+'|'+'|'.join(names[j] for j in others),points=float(a.sum()),DD_continuous=dd(a),operations=nn)
 for yr in ['2024','2025','2026']:r['year'+yr]=float(a[np.array([d.startswith(yr) for d in days])].sum())
 r.update(points_cost5=r['points']-5*nn,points_cost10=r['points']-10*nn);combinations.append(r)
write('COMBINACOES_16_R61_NOVO_OUTROS_ORIGINAIS.csv',combinations)
assert variant.sum()==7925 and [r['variant_pair_points'] for r in annual]==[6155,6115,-4345]
assert original_d.sum()==3950 and original_pair.sum()==5890
summary=dict(status='FECHADA_SOBRE_PRECOS_CONDICIONAIS_DO_MODELO',variant_id='R61_TARGET750_STOP150_S61_ORIGINAL',included_levels=['R61.8_NEW','S61.8_ORIGINAL'],excluded_levels=['R38.2','S38.2','S50'],period='2024-01-02 a2026-10-30',days=len(days),operations=len(ops),total_points=float(variant.sum()),DD_continuous=dd(variant),DD_peak_valley=worst,annual=annual,august_eight_original_points=float(sum(D(r['original_points']) for r in closed)),august_eight_new_points=float(sum(D(r['variant_points']) for r in closed)),pending_variant=0,pending_other_study_variants='NOT_AUTOMATICALLY_CLOSED_BY_THIS_BATCH',original_D_total_preserved=3950,original_D_DD_preserved=14805,original_pair_total_preserved=5890,costs_in_main=False,certified_fills=False,method='M1_AND_AVAILABLE_TARGETED_REPLAY_JAN2024_JUL2026;CEDRO_ORIGINAL_S61_AUGOCT;RECOVERED_CEDRO_R61_AUG;CEDRO_AUDIT_M1_R61_SEPOCT')
(P/'RESULTADO_VARIANTE_FECHADA.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
# Annual comparison preserves all originals and replaces only the candidate's interval.
prev=read(BASE/'comparacao_anual/RESULTADO_ANUAL_DESTAQUES.csv');compare=[]
for r in prev:
 if r['scenario']=='MIX_0161':
  new=next(a for a in annual if a['year']==r['year']);r.update(points_lower=new['variant_pair_points'],points_upper=new['variant_pair_points'],DD_year_lower=new['variant_year_DD'],DD_year_upper=new['variant_year_DD'],unresolved_operations=0,status='FECHADO_COM_CEDRO_RECUPERADO',points_cost5_lower=new['points_after_cost5'],points_cost5_upper=new['points_after_cost5'],points_cost10_lower=new['points_after_cost10'],points_cost10_upper=new['points_after_cost10'])
 compare.append(r)
write('COMPARACAO_ANUAL_ATUALIZADA.csv',compare)
wb=openpyxl.Workbook();wb.remove(wb.active)
for name,rows in [('Anual_Variante',annual),('Comparacao_Anual',compare),('Mensal',monthly),('Oito_Cedro',closed),('Operacoes_488',ops),('Curva_Diaria',daily),('Combinacoes_16',combinations),('Fontes_Recuperadas',read(P/'ARQUIVOS_RECUPERADOS.csv'))]:
 sh=wb.create_sheet(name);keys=list(rows[0]);sh.append(keys)
 for r in rows:sh.append([r[k] for k in keys])
 sh.freeze_panes='A2';sh.auto_filter.ref=sh.dimensions
 for c in sh[1]:c.font=Font(color='FFFFFF',bold=True);c.fill=PatternFill('solid',fgColor='17354E')
 for col in sh.columns:sh.column_dimensions[col[0].column_letter].width=min(65,max(16,max(len(str(c.value or '')) for c in list(col)[:80])+2))
wb.save(P/'Variante_R61_750_150_S61_Original_Fechada.xlsx')
c=canvas.Canvas(str(P/'Variante_R61_750_150_S61_Original_Fechada.pdf'),pagesize=A4);c.setTitle('Variante R61 alvo750 stop150 + S61 original — fechamento')
def header(title,sub=''):
 global y
 c.setFillColorRGB(.06,.16,.25);c.rect(0,758,595,84,fill=1,stroke=0);c.setFillColorRGB(1,1,1);c.setFont('Helvetica-Bold',17);c.drawString(32,806,title);c.setFont('Helvetica',10);c.drawString(32,782,sub);c.setFillColorRGB(.06,.16,.25);y=726
 c.setFont('Helvetica',8);c.drawString(32,27,'17/11/2026 | Variante separada; D original preservado | Preços condicionais, sem custos/fills')
def line(t,bold=False):
 global y
 c.setFont('Helvetica-Bold' if bold else 'Helvetica',10);c.drawString(32,y,t);y-=21
header('R61,8 alvo 750 / stop 150 + S61,8 original','Janeiro/2024 a outubro/2026 | 488 operações | R38,2, S38,2 e S50 excluídos')
line('Resultado fechado da variante: '+fmt(variant.sum())+' pontos',True);line('DD diário contínuo: '+fmt(dd(variant))+' pontos, sem reinício mensal.',True)
line('Os 16 ZIPs reenviados coincidem com os hashes do recebimento anterior.');line('As oito novas saídas R61,8 de agosto foram STOP de -150: soma -1.200.');line('Essas mesmas oito operações somavam +295 nas saídas originais.');y-=12
for a in annual:
 line(a['year']+(' (jan-out)' if a['year']=='2026' else '')+': '+fmt(a['variant_pair_points'])+' pontos | '+str(a['operations'])+' operações | DD anual '+fmt(a['variant_year_DD']),True)
y-=12;line('R61,8 + S61,8 com saídas originais:');line('2024 +2.680 | 2025 +4.325 | 2026 jan-out -1.115 | total +5.890.');line('D completo original: total +3.950 e DD 14.805.');y-=12
line('A variante melhora o agregado, mas piora 2026 frente à dupla original.',True)
line('Não é evidência de estabilidade ou aprovação para operar.');line('Custos hipotéticos de 5 pontos/operação: '+fmt(variant.sum()-5*488)+'.');line('Custos hipotéticos de 10 pontos/operação: '+fmt(variant.sum()-10*488)+'.');line('Custos são sensibilidades, não orçamento real de spread/corretagem.');line('DD anual isolado não substitui o DD contínuo do período completo.');c.showPage()
header('As oito operações de agosto/2026','Entrada original preservada | Novo alvo 750 / stop 150 | Sem pendências nesta variante')
for r in closed:
 line(r['date']+' | '+r['contract']+' | original '+fmt(r['original_points'])+' | novo '+fmt(r['variant_points']),True)
 line('Entrada '+r['entry_time'][-12:]+' | saída '+r['exit_time'][-12:]+' | STOP');y-=6
y-=10;line('Conferências de fonte e execução do cálculo:',True)
line('Contagens integrais conferem com o inventário histórico por contrato.');line('Os cinco estados originais por dia reproduzem ordinais, horários e pontos.');line('Motor C++ em todos os registros confere com motor Python independente.');line('Resultado invariável ao inverter negócios com o mesmo milissegundo.');line('Nenhum grupo relevante cruza simultaneamente alvo e stop da variante.');line('Não foi certificado preenchimento de ordens reais.');c.showPage()
for yr in ['2024','2025','2026']:
 header('Comparação anual | '+yr,'Janeiro a outubro' if yr=='2026' else 'Ano completo')
 for r in [r for r in compare if r['year']==yr]:
  line(r['label'],True);line('Pontos '+fmt(r['points_lower'])+' | DD anual '+fmt(r['DD_year_lower'])+' | Operações '+str(r['operations']));y-=13
 line('A candidata antes apresentada em faixa agora tem valor único.',True);line('Os demais cenários desta página mantêm seus resultados originais.');c.showPage()
for yr in ['2024','2025','2026']:
 header('Variante | Mensal '+yr,'R61,8 alvo750/stop150 + S61,8 original; demais níveis excluídos')
 for r in [r for r in monthly if r['month'].startswith(yr)]:line(r['month']+' | '+fmt(r['variant_pair_points'])+' pontos | DD no mês '+fmt(r['variant_month_DD'])+' | DD acum. '+fmt(r['variant_continuous_DD_end']))
 y-=20;line('Método: M1 com Replay pontual antes de agosto/2026.');line('S61,8 original Cedro preservado; R61,8 agosto reprocessado nos brutos.');line('R61,8 setembro/outubro determinado pelos candles de auditoria Cedro.');line('Não é auditoria integral tick a tick de todo o período.');line('O fechamento desta variante não fecha automaticamente todas as outras.');c.showPage()
c.save();doc=fitz.open(P/'Variante_R61_750_150_S61_Original_Fechada.pdf');assert len(doc)==8
(P/'.gitattributes').write_text('*.pdf binary\n*.xlsx binary\n');(P/'.gitignore').write_text('__pycache__/\n')
(P/'LEIA_PRIMEIRO.md').write_text('''# Fechamento da variante R61.8 alvo750/stop150 + S61.8 original

Recebidos novamente os16ZIPs necessários, com hashes idênticos aos comprovados anteriormente. Originais preservados em /workspace/dados_brutos_modelo_d/cedro/. Manifesto RESTAURACAO_FONTES.json contém também os IDs Sediment para recuperar novamente sem pedir novo envio se o ambiente for substituído. Os ZIPs brutos não foram duplicados no históricoGit.

Oito operações R61.8 deagosto2026: todas stop-150, total-1200,contra+295 original. Contagens integrais porcontrato conferidas; estados originais reproduzidos exatamente; motorC++em todosregistros confrontado comPython independente; ordem inversa nos empatesms não altera pontos/motivos. Entradas mantidas. Custos/fills não certificados.

Resultado da variante:2024+6155;2025+6115;2026jan-out-4345;total7925. Resultado principalDoriginal permanece3950,DD14805; duplaoriginalR61.8+S61.8 permanece5890. Arquivos anteriores comfaixas são checkpoints históricos, substituídos para ESTA variante pelos novos arquivos de fechamento.

Planilha ePDF incluem resultado anual,mensal,DD diário contínuo,488operações e comparação atualizada. A grade de outras175receitas ainda tem limitações próprias; não considerar todas fechadas porque estes16ZIPs foram recuperados. Nunca sobrescrever os resultados originais. Não houve comparação comWork.
''')
print(json.dumps(summary,ensure_ascii=False,indent=2))
