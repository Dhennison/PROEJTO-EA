"""Separa total do recorte Work de fechamento completo nos PDFs enxutos."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];p=ROOT/'entregas/compilado_cedro_modelod/gerar_dois_compilados.py';s=p.read_text()
s=s.replace('WIN  |  Modelo D  |  Work × nosso teste  |  pontos diários','WIN  |  Modelo D  |  Work × Cedro  |  pontos diários')
s=s.replace('DD provisório: será recalculado quando os meses anteriores forem acrescentados.','DD da base disponível; será recalculado se a cobertura histórica for ampliada.')
s=s.replace('Enquanto faltarem meses anteriores, o DD é provisório; não se atribui resultado zero a esses meses.','O DD refere-se à base disponível; períodos sem dados não recebem resultado zero.')
if "full_months=" not in s:s=s.replace("index=read(root/'INDICE_MENSAL.csv');", "full_months={r['mes']:r for r in read(root/'MODELO_D_MESES_COMPLETOS.csv')}\nindex=read(root/'INDICE_MENSAL.csv');")
s=s.replace("summaries=[('TOTAL DO MÊS',worktotal,testtotal,False),", "summaries=[('TOTAL COMPARÁVEL',worktotal,testtotal,False),('FECHAMENTO CEDRO',None,D(full_months[month]['pontos']),False),")
line=" for j,(label,wv,tv,risk) in enumerate(summaries):\n"
insert="""  if wv is None:
   c.setFont('DVB',8.5);c.setFillColor(navy);c.drawString(48,y,label)
   c.drawRightString(300,y,'—');c.setFillColor(red if tv<0 else green);c.drawRightString(424,y,pt(tv))
   c.setFillColor(gray);c.drawRightString(W-48,y,'—');y-=25;continue
"""
if insert not in s:s=s.replace(line,line+insert)
s=s.replace('Períodos concluídos — resultados mensais preservados','Resultados no recorte comparável ao Work')
s=s.replace("notes=[f'Acumulados", "notes=[f'Acumulados")
assert "'TOTAL DO MÊS'" not in s and "'TOTAL COMPARÁVEL'" in s and "'FECHAMENTO CEDRO'" in s
p.write_text(s)
