"""Fecha serie Cedro sem misturar a base Work com os meses completos entre modelos."""
from pathlib import Path
from decimal import Decimal as D
import csv,json,hashlib,shutil
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4,landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
import fitz
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent;OUT=HERE/'resultado';COMP=ROOT/'entregas/compilado_cedro_modelod';COMP.mkdir(exist_ok=True)
def read(p):return list(csv.DictReader(p.open(encoding='utf-8-sig'),delimiter=';'))
def write(p,rows):
 with p.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter=';');w.writeheader();w.writerows(rows)
s=json.loads((OUT/'RESULTADO.json').read_text());daily=read(OUT/'DIARIO_PRINCIPAL.csv');ops=read(OUT/'POR_OPERACAO.csv')
source=json.loads((ROOT/'entregas/compilado_work_modelod/MODELO_D_FONTE_PDF_VALIDADA.json').read_text());month=next(m for m in source['months'] if m['month']=='2026-09');assert [r['data'] for r in daily]==month['dates']
for r in daily:assert D(r['Work_pontos'])==D(source['daily'][r['data']]['value_exact6'])
base=read(ROOT/'entregas/fechamento_setembro_v1_00/analise/WORK_SETEMBRO.csv');main=[r for r in ops if r['escopo']=='WORK_ORIGINAL'];assert {(r['data'],r['nivel']) for r in main}=={(r['Data'],r['Nível']) for r in base}
prev=read(ROOT/'entregas/fechamento_setembro_v1_00/resultado_nativo_20261111/POR_OPERACAO.csv');prev=[r for r in prev if r['cenario']=='GRADE5_TOQUE'];look={(r['data'],r['nivel']):r for r in ops}
for r in prev:
 n=look[r['data'].replace('.','-'),r['nivel']];assert D(r['pontos_teoricos'])==D(n['pontos']) and r['motivo']==n['motivo']
assert len(prev)==33
s['conferencia_setembro_anterior']={'operacoes':33,'todos_mesmo_motivo_e_pontos':True,'total':'1380'}
sens=json.loads((OUT/'SENSIBILIDADE_ORDEM.json').read_text());assert sens['todos_mesmo_resultado'];s['sensibilidade_ordem']=sens
s['dados_quantidade_EOD']={'dias_com_diferencas':['2026-09-22','2026-09-24'],'precos_diarios_OHLC_iguais':True,'registros_todos_mantidos':True,'diferencas_nao_resolvidas_por_reordenacao':True,'arquivo':'auditoria/DIFERENCAS_EOD.csv'}
aug=ROOT/'entregas/cedro_modelod_agosto_2026/resultado';aug_summary=json.loads((aug/'RESULTADO.json').read_text())
full_aug=read(aug/'DIARIO_COMPLEMENTAR.csv')+read(aug/'DIARIO_PRINCIPAL.csv');full_aug.sort(key=lambda x:x['data']);full_sep=read(OUT/'DIARIO_MES_COMPLETO.csv')
assert len(full_aug)==len(full_sep)==21
full=full_aug+full_sep
balance=peak=maximum=D(0);curve=[];monthly={}
for r in full:
 date=r['data'];month=date[:7];balance+=D(r['nosso_pontos']);peak=max(peak,balance);dd=peak-balance;maximum=max(maximum,dd)
 curve.append({'data':date,'modelo':'D','pontos':r['nosso_pontos'],'saldo':str(balance),'pico':str(peak),'DD_atual':str(dd),'DD_max_acumulado':str(maximum),'escopo':'MESES_COMPLETOS_MODELOS_ABCD'})
 info=monthly.setdefault(month,{'mes':month,'modelo':'D','pregoes':0,'pontos':D(0),'operacoes':0,'DD_max_acumulado':D(0)})
 info['pregoes']+=1;info['pontos']+=D(r['nosso_pontos']);info['operacoes']+=int(r['operacoes_nossas']);info['DD_max_acumulado']=maximum
write(COMP/'CURVA_MODELO_D_MESES_COMPLETOS.csv',curve);write(COMP/'MODELO_D_MESES_COMPLETOS.csv',list(monthly.values()))
s['serie_meses_completos']={'base_inicio':full[0]['data'],'base_fim':full[-1]['data'],'meses':json.loads(json.dumps(monthly,default=str)),'saldo':str(balance),'DD_max_acumulado':str(maximum),'metodo':'FECHAMENTOS_DIARIOS_ORDEM_CRESCENTE_SALDO_PICO_CONTINUOS','inclui03_agosto_e22a30_setembro':True,'separada_da_comparacao_Work':True,'provisorio':True}
(OUT/'RESULTADO.json').write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n')
pdfmetrics.registerFont(TTFont('DV','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'));pdfmetrics.registerFont(TTFont('DVB','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
def pt(x):return f'{D(x):,.2f}'.replace(',','@').replace('.',',').replace('@','.')
tech=OUT/'Comparativo_ModeloD_Cedro_Tecnico_Setembro.pdf';c=canvas.Canvas(str(tech),pagesize=landscape(A4))
def page(title,lines):
 c.setFillColor(colors.HexColor('#193b61'));c.setFont('DVB',19);c.drawString(36,550,title);y=510
 for text in lines:c.setFont('DV',10);c.drawString(36,y,text);y-=24
 c.showPage()
page('Setembro/2026 - comparacao original Work',[
 'Principal comparavel: Work '+pt(s['Work_pontos'])+' | Cedro '+pt(s['nosso_principal_pontos'])+' | Diferenca '+pt(s['diferenca'])+'.',
 'Base: 14 pregoes de01 a21/09; mesmas33operacoes,20alvos e13stops.',
 'As33operacoes repetem motivo e pontos da coleta anterior Genial. Sem trocar regras.',
 'Mes completo01 a30/09: '+pt(s['mes_completo']['pontos'])+' pontos,21pregoes,52operacoes.',
 'Complemento22 a30/09: '+pt(s['complemento_22_a_30_setembro']['pontos'])+' pontos; sem Work ficticio zero.',
 'Meses completos para comparar os modelos: agosto '+pt(monthly['2026-08']['pontos'])+' | setembro '+pt(monthly['2026-09']['pontos'])+'.',
 'Agosto comparavel ao Work continua -2275;03/08 (-100) entra somente no mes completo.',
 'Replay direto dos negocios: um contrato/nivel,grade5,toque,sem MT5 ou Tester.',
 'Saida so em registro posterior a entrada; corte no primeiro negocio do minuto18:00.',
 'Pontos condicionais nos niveis: sem custos,fila,spread ou garantia de preenchimento real.',
 'Novo estudo de stops/alvos fica para depois de comparar A/B/C/D originais.'
])
page('Dados, ordem dos registros e validacao',[
 '42ZIPs/21datas,121647412registrosWIN. Hashes,tamanhos,CRC,contagens e ordinais conferidos.',
 'Novo auditor C++ confere integralmente com auditor Python anterior nas8datas ja recebidas.',
 'M1Work igual durante horario operado nas14datas; diferencas apenas18:24 apos corte.',
 '14referencias originais Work preservadas.7extras derivam de EOD e contexto do pregao anterior.',
 'Tres registros com timestamp atrasado: um em22/09 e dois em24/09; originais preservados.',
 'Leitura cronologica estavel por timestamp,desempate por linha original; sem deduplicacao/filtros.',
 'Controle em ordem original tambem executado:10estados com mesmas entradas,saidas e pontos.',
 'OHLC diarios iguais aoEOD.22/24 possuem divergencias de quantidade/contagem,nao resolvidas.',
 'A invariancia de ordem no ModeloD nao prova fita completa nem valida futuras variantes A/B/C.',
 '105estados: Python anterior em eventos reduzidos x C++ em todos os negocios; todos conferidos.',
 '33operacoes e14somas diarias Work validadas contra arquivos anteriores/PDF original.',
 'DD calculado em ordem crescente,duas bases: comumWork e meses completos,sem misturar curvas.',
 'Fuso,condicoes e ordem oficial dos registros empatados ainda nao certificados independentemente.'
]);c.save()
(COMP/'diarios_principais').mkdir(exist_ok=True)
for month,path in [('2026_08',aug/'DIARIO_PRINCIPAL.csv'),('2026_09',OUT/'DIARIO_PRINCIPAL.csv')]:shutil.copyfile(path,COMP/'diarios_principais'/(month+'.csv'))
index=[]
for month,summary,report in [('2026-08',aug_summary,aug/'Comparativo_ModeloD_Cedro_Tecnico_Em_Andamento.pdf'),('2026-09',s,tech)]:
 r=read(aug/'DIARIO_PRINCIPAL.csv') if month=='2026-08' else daily
 index.append({'mes':month,'inicio_Work':r[0]['data'],'fim_Work':r[-1]['data'],'pregoes_Work':len(r),'operacoes_Work':summary['operacoes_Work'],'Work_pontos':summary['Work_pontos'],'nosso_resultado_principal':summary['nosso_principal_pontos'],'diferenca_nosso_menos_Work':summary['diferenca'],'estado':'CONCLUIDO_CEDRO','criterio_principal':'1 contrato;grade5;toque;condicional','pdf_preservado':str(report.relative_to(ROOT)),'pdf_sha256':hashlib.sha256(report.read_bytes()).hexdigest()})
write(COMP/'INDICE_MENSAL.csv',index)
(COMP/'MANIFESTO_COMPILADO.json').write_text(json.dumps({'serie':'CEDRO','modelos_incluidos':['D'],'meses_completos':s['serie_meses_completos'],'originais_anteriores_preservados':True},ensure_ascii=False,indent=2)+'\n')
gen=(ROOT/'entregas/compilado_work_modelod/gerar_dois_compilados.py').read_text()
gen=gen.replace("source=json.loads((root/'MODELO_D_FONTE_PDF_VALIDADA.json').read_text())","source=json.loads((root.parent/'compilado_work_modelod/MODELO_D_FONTE_PDF_VALIDADA.json').read_text())")
gen=gen.replace("(root/'Comparativo_Work_ModeloD_Compilado_Em_Andamento.pdf').write_bytes(tech.read_bytes())", "# Dois PDFs finais; sem terceira copia de compatibilidade nesta serie.")
gen=gen.replace("metadata.update({'entregas_finais_solicitadas'", "metadata.update({'entregas_finais_solicitadas'")
(COMP/'gerar_dois_compilados.py').write_text(gen)
import subprocess,sys
subprocess.run([sys.executable,str(HERE/'ajustar_apresentacao.py')],check=True)
(COMP/'LEIA_CONTINUIDADE.txt').write_text('''SERIE CEDRO — DUAS BASES EXPLICITAS
PDF enxuto e principal: compara somente datas originais do Work.
Agosto20datas -2275; setembro14datas +1380. Curva comum em ordem crescente.
Meses completos para comparar A/B/C/D: agosto21datas -2375; setembro21datas +2855.
Inclui03/08 e22–30/09. Curva propria, sem inventar Work zero nas datas adicionais.
Todas as curvas carregam saldo/pico entre meses; DD nao reinicia. Ainda provisorio
por faltarem meses anteriores e outubro. Dois PDFs guardados para entrega final.
PDFs anteriores e resultados da fonte Genial continuam preservados no acervo.
''')
print('Relatorio mensal e serie completa preparados',s['serie_meses_completos'])
