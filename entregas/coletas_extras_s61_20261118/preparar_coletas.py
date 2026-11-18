from pathlib import Path
import csv,json,datetime as dt,hashlib
import openpyxl,fitz
from openpyxl.styles import Font,PatternFill,Alignment
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
P=Path(__file__).parent;R=P.parents[1];B=R/'entregas/coletas_s61_e_teste_50_250_20261118'
def read(p):
 with p.open(encoding='utf-8-sig') as f:return list(csv.DictReader(f,delimiter=';'))
def write(name,rs):
 with (P/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rs[0]),delimiter=';',lineterminator='\n');w.writeheader();w.writerows(rs)
extras=read(B/'JANELAS_EXTRAS_2_E_3_COLOCADOS.csv');primary=read(B/'20_JANELAS_PRIORITARIAS_E_COINCIDENCIAS.csv');fixed=read(B/'JANELAS_AGRUPADAS_50_250.csv');rows=[]
for r in extras:
 matches=[m for m in fixed if m['date']==r['date'] and m['minute']==r['start'][:5]]
 start=dt.datetime.fromisoformat(r['date']+'T'+r['start']);end=dt.datetime.fromisoformat(r['date']+'T'+r['end_exclusive'])
 rows.append(dict(date=r['date'],contract=r['contract'],start=r['start'],end_exclusive=r['end_exclusive'],copy_start=(start-dt.timedelta(seconds=3)).strftime('%H:%M:%S'),copy_end=(end+dt.timedelta(seconds=3)).strftime('%H:%M:%S'),variants='S61_48/S61_68' if r['variant']=='S61_48' else 'S61_60',also_helps_50_250=bool(matches),levels_50_250=','.join(m['levels'] for m in matches),return_tab=r['date'][8:]+'-'+r['date'][5:7]+'_'+r['start'][:5].replace(':','')))
rows.sort(key=lambda r:(r['date'],r['start']));assert len(rows)==9 and len({r['date'] for r in rows})==8
five=[dict(date=r['date'],contract=r['contract'],start=r['start'],end_exclusive=r['end_exclusive'],levels_50_250=r['levels_50_250'],where='JA_INCLUIDA_NAS20PRIORITARIAS_NAO_REPETIR') for r in primary if r['also_helps_50_250']=='True'];assert len(five)==5
assert sum(r['also_helps_50_250'] for r in rows)==4
assert {(r['date'],r['start']) for r in rows}.isdisjoint({(r['date'],r['start']) for r in primary})
write('8_DIAS_EXTRAS_9_JANELAS.csv',rows);write('5_DAS20_QUE_AJUDAM_50_250.csv',five)
allrows=[dict(date=r['date'],contract=r['contract'],start=r['start'],end_exclusive=r['end_exclusive'],group='20PRIORITARIAS') for r in primary]+[dict(date=r['date'],contract=r['contract'],start=r['start'],end_exclusive=r['end_exclusive'],group='8DIAS_EXTRAS') for r in rows];allrows.sort(key=lambda r:(r['date'],r['start']));assert len(allrows)==29 and len({r['date'] for r in allrows})==28
write('INDICE_29_JANELAS_SEM_DUPLICAR.csv',allrows)
lines=['REPLAY —8DIAS ADICIONAIS /9JANELAS —18/11/2026','Além das20janelas prioritárias doS61stop100. Não substitui as20.', 'Horário deSãoPaulo/fonte;fimexclusivo. Copiar3segundos antes/depois,ou mais se necessário para manter o minuto completo.','']
for r in rows:lines.append(f"{r['date']} | {r['start'][:5]}–{r['end_exclusive'][:5]} | {r['contract']} | {r['variants']} | ajuda50/250:{'SIM' if r['also_helps_50_250'] else 'NÃO'}")
lines+=['','AS5JANELAS50/250QUEJÁESTÃOENTREAS20PRIORITÁRIAS;NÃOCOPIARNOVAMENTE:']
for r in five:lines.append(f"{r['date']} | {r['start'][:5]}–{r['end_exclusive'][:5]} | {r['contract']}")
lines+=['','Entreosextras,mais4janelasajudam50/250:05/06/2024;22/04/2026;15/05/2026;19/10/2026.','Logo,20prioritárias+9extras=29janelas em28datas,dasquais9janelas também ajudam50/250.','Preservarpreços,quantidades,milissegundos,ordem e negócios idênticos. Não filtrar/ordenar/deduplicar.','Seabertura/leilão impediu negócios,informar seminventar linhas. ConfirmaremosOHLC/quantidade na volta.','Contratos esperados pelas referênciaspreservadas;conferir correspondência dospreços ao receber.']
(P/'LISTA_8_DIAS_EXTRAS.txt').write_text('\n'.join(lines)+'\n')
wb=openpyxl.Workbook();wb.remove(wb.active)
def table(name,rs):
 sh=wb.create_sheet(name);keys=list(rs[0]);sh.append(keys)
 for r in rs:sh.append([r[k] for k in keys])
 sh.freeze_panes='A2';sh.auto_filter.ref=sh.dimensions
 for c in sh[1]:c.fill=PatternFill('solid',fgColor='17354E');c.font=Font(color='FFFFFF',bold=True);c.alignment=Alignment(wrap_text=True)
 for col in sh.columns:sh.column_dimensions[col[0].column_letter].width=min(55,max(16,max(len(str(c.value or '')) for c in col)+2))
 return sh
table('Extras_9_Janelas',rows);table('5_Ja_Nas20_Nao_Repetir',five)
table('Instrucoes',[dict(item='Escopo',texto='8dias ADICIONAIS,9janelas.20pedidos anteriores continuam prioritários.27/03/2024tem2minutos separados.'),dict(item='Retorno',texto='Abas comdata_hora sócontêm cabeçalho vazioProfit. Cole todos osnegócios dajanela,sem filtros/ordenação/deduplicação.'),dict(item='Minuto completo',texto='copy_start/copy_end têm3segundos de margem. Conservar o minuto inteiro;se ultrapassar limite de cópia,dividir comsobreposição e informar.'),dict(item='Validação',texto='Milissegundos,ordem,preços equantidades precisam ser preservados. Faremos conferênciaOHLC/quantidade eempates antes defechar.'),dict(item='Observações',texto='Informar leilão ou ausência de cotações. Não inventar candles/negócios.'),dict(item='Parâmetros',texto='CopiarTime&Trades não requer operar nem alterar ordens:apenas contrato/data/horário.48/68e60serão calculados no projeto.')])
for r in rows:
 sh=wb.create_sheet(r['return_tab']);sh.append(['Data','Compradora','Valor','Quantidade','Vendedora','Agressor','Total (BRL)','Agente Agressor']);sh.freeze_panes='A2'
wb.save(P/'Coleta_8_Dias_Extras_9_Janelas.xlsx')
c=canvas.Canvas(str(P/'Coleta_8_Dias_Extras_9_Janelas.pdf'),pagesize=A4);W,H=A4;c.setTitle('Replay —8dias extras,9janelas')
c.setFont('Helvetica-Bold',18);c.drawString(30,H-40,'Replay | 8 dias extras, 9 janelas');c.setFont('Helvetica',10);c.drawString(30,H-64,'Além das20prioritárias;27/03/2024temdoisminutosseparados.');y=H-103
c.setFont('Helvetica-Bold',9)
for x,t in [(30,'Data'),(115,'Contrato'),(205,'Intervalo'),(325,'Opções'),(475,'Ajuda50/250')]:c.drawString(x,y,t)
c.setFont('Helvetica',9)
for r in rows:
 y-=26
 for x,t in [(30,r['date']),(115,r['contract']),(205,r['start'][:5]+'–'+r['end_exclusive'][:5]),(325,'48/68' if r['variants']=='S61_48/S61_68' else '60'),(490,'Sim' if r['also_helps_50_250'] else 'Não')]:c.drawString(x,y,t)
y-=35;c.setFont('Helvetica-Bold',11);c.drawString(30,y,'Estas cinco já estão nas20prioritárias — não repetir');c.setFont('Helvetica',9)
for r in five:y-=22;c.drawString(30,y,r['date']+' | '+r['contract']+' | '+r['start'][:5]+'–'+r['end_exclusive'][:5])
y-=35
for t in ['Os4extrasmarcados também ajudam50/250,totalizando9janelas compartilhadas.','Horário dafonte/SãoPaulo;fimexclusivo. Capturar alguns segundos antes/depois.','Manter minuto completo,ms,ordem e negócios idênticos. Não filtrar/deduplicar.','Total combinado:28datas/29janelas,contando os20pedidos anteriores.','Os resultados só serão fechados depois de validar os negócios enviados.']:
 c.drawString(30,y,t);y-=17
c.setFont('Helvetica',8);c.drawString(30,24,'18/11/2026 | Estudos anteriores preservados | Nenhum negócio executado');c.save();assert len(fitz.open(P/'Coleta_8_Dias_Extras_9_Janelas.pdf'))==1
manifest=dict(date='2026-11-18',extra_days=8,extra_windows=9,second_variant_extra_days=7,second_variant_extra_windows=8,third_variant_extra_days=1,third_variant_extra_windows=1,primary_days_remain20=True,five_shared_with_50_250_are_inside_primary20=True,additional_extra_shared_windows_with_50_250=4,total_shared_with_50_250=9,total_days_including_primary=28,total_windows_including_primary=29,source_files=[dict(path=str((B/f).relative_to(R)),sha256=hashlib.sha256((B/f).read_bytes()).hexdigest()) for f in ['JANELAS_EXTRAS_2_E_3_COLOCADOS.csv','20_JANELAS_PRIORITARIAS_E_COINCIDENCIAS.csv','JANELAS_AGRUPADAS_50_250.csv']],results_changed=False)
(P/'MANIFESTO.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');(P/'.gitattributes').write_text('*.pdf binary\n*.xlsx binary\n');(P/'.gitignore').write_text('__pycache__/\n')
(P/'LEIA_PRIMEIRO.md').write_text('''# Oito dias extras, nove janelas

Complementam os20pedidos S61stop100. Não são os únicosdias ainda pendentes: os20anteriores continuam. S61_48/68tem7diasextras/8janelas;S61_60tem1diaextra/1janela.27/03/2024tem10:07e10:13,separadamente. Totalconjunto28dias/29janelas.

As5janelas queajudam50/250 já estão nas20prioritárias,não são5dias adicionais. Cruzamento refinado também encontrou4janelas extrasque ajudam50/250:05/06/2024,22/04/2026,15/05/2026,19/10/2026. Logo9janelas compartilhadasentreos29pedidos eeste teste.

XLSXcom9abasderetorno,PDF/TXT/CSVcomdatas,horários econtratos. HorárioSãoPaulo/fonte,fimexclusivo,minuto completo e segundos demargem. Não filtrar/ordenar/deduplicar. Não executar negócios;somente coletaTime&Trades. Contratos/preçosserãoconferidosnavolta,antes defechar resultados.

Resultados e estudos anteriores preservados. Nenhuma hipótese foi transformada em resultado fechado nesta preparação.
''')
print(json.dumps(manifest,ensure_ascii=False,indent=2))
