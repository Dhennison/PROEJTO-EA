"""Fecha outubro com21datas;parciais e regras originais permanecem preservadas."""
from pathlib import Path
from decimal import Decimal as D
from collections import Counter
import csv,json,hashlib
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent;OUT=HERE/'resultado_mensal';OUT.mkdir(exist_ok=True)
def read(p):return list(csv.DictReader(p.open(encoding='utf-8-sig'),delimiter=';'))
def write(p,rows):
 with p.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter=';',lineterminator='\n');w.writeheader();w.writerows(rows)
daily=[];ops=[];levels=[];checks=[];refs=[]
for folder in ['resultado_lote1','resultado_dia14','resultado_restantes']:
 p=HERE/folder;meta=json.loads((p/'PARCIAL.json').read_text());daily+=read(p/'DIARIO_PARCIAL.csv');levels+=read(p/'TODOS_NIVEIS.csv');checks+=read(p/'VALIDACAO.csv');refs+=read(p/'REFERENCIAS.csv')
 if (p/'POR_OPERACAO.csv').exists():ops+=read(p/'POR_OPERACAO.csv')
 else:assert meta['operacoes']==0 and all(not r['hora_entrada'] for r in read(p/'TODOS_NIVEIS.csv'))
daily.sort(key=lambda r:r['data']);refs.sort(key=lambda r:r['date']);checks.sort(key=lambda r:r['data']);assert len(daily)==len({r['data'] for r in daily})==21
assert len(levels)==len({(r['data'],r['nivel']) for r in levels})==105
assert len(ops)==len({(r['data'],r['nivel']) for r in ops})==31
assert not any(r['estado']=='ABERTA' for r in levels)
assert sum(D(r['pontos']) for r in daily)==sum(D(r['pontos']) for r in ops)==3830
old=read(HERE/'parcial_atual/DIARIO_PARCIAL.csv');current={r['data']:r for r in daily}
for r in old:assert r==current[r['data']]
control=json.loads((HERE/'resultado_restantes/SENSIBILIDADE_ORDEM.json').read_text());assert control['todos_mesmo_resultado']
# No dia27 o contrato teve diferenca de contagem EOD, mas TODOS os niveis de
# entrada ficam fora de[Low,High]diario,ja conferido contra EOD.
stats=read(HERE/'auditoria_final/20261027_CONTRATOS.csv');z=next(r for r in stats if r['ativo']=='WINZ26')
for l in [r for r in levels if r['data']=='2026-10-27']:
 assert not l['hora_entrada']
 cfg=(HERE/'resultado_restantes/20261027.config').read_text().splitlines();gridrows=cfg[-5:]
 for i,v in enumerate(gridrows):
  eligible,buy,en,sl,tp=map(int,v.split());assert (not eligible) or (en<D(z['low']) if buy else en>D(z['high']))
all_audits=[json.loads((HERE/p/'AUDITORIA.json').read_text()) for p in ['auditoria','auditoria14','auditoria_final']]
assert sum(r['datas'] for r in all_audits)==21 and sum(r['ZIPs'] for r in all_audits)==48
assert sum(r['registros_WIN'] for r in all_audits)==154385672
write(OUT/'DIARIO_MES_COMPLETO.csv',[{'data':r['data'],'Work_pontos':'','nosso_pontos':r['pontos'],'diferenca':'','operacoes_nossas':r['operacoes'],'escopo':'FORA_WORK_ORIGINAL'} for r in daily])
write(OUT/'POR_OPERACAO.csv',ops);write(OUT/'TODOS_NIVEIS.csv',levels);write(OUT/'VALIDACAO_POR_DIA.csv',checks)
# Referencias possuem campo extra na rolagem;normalizar cabecalho sem omitir origem.
keys=list(dict.fromkeys(k for r in refs for k in r));write(OUT/'REFERENCIAS.csv',[{k:r.get(k,'') for k in keys} for r in refs])
summary={'mes':'2026-10','status':'CONCLUIDO_SOBRE_ALIMENTACAO_RECEBIDA_COM_RESSALVAS','pregoes':21,'pontos_mes_completo':'3830','operacoes':31,'motivos':dict(Counter(r['motivo'] for r in ops)),'Work_comparavel':False,'Work_pontos':None,'ZIPs':48,'registros_WIN':154385672,'estados_conferidos':105,'parcial9dias_preservada':True,'sensibilidade28':control,'dias_ressalva_quantidade':['2026-10-27','2026-10-28'],'dia27_niveis_fora_extremos_diarios_EOD':True,'registros_reordenados_somente_por_timestamp_estavel':'2026-10-28','custos_inclusos':False,'preenchimentos_reais_comprovados':False,'criterio':'ModeloD original;1contrato/nivel;grade5;toque;saida em registro posterior;corte primeiro negocio18:00','rolagem':'V ate13;Z desde14;contexto14V13 conforme convencao historica Work','garantia_ordem_oficial_entre_empates':False}
(OUT/'RESULTADO.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');print(json.dumps(summary,ensure_ascii=False,indent=2))
