"""Classify original entry candles; do not change any strategy rule or outcome."""
import argparse,csv,json,hashlib
from pathlib import Path
from collections import Counter,defaultdict
from decimal import Decimal as D
from datetime import datetime
p=argparse.ArgumentParser()
for n in ('candles','operations','contexts','sept','out'):p.add_argument('--'+n,type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
def read(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter=';'))
def pn(s):return D(s.replace('.','').replace(',','.'))
def write(n,r):
 with (a.out/n).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(r[0]),delimiter=';',lineterminator='\n');w.writeheader();w.writerows(r)
contexts={r['Data']:r for r in read(a.contexts)};operations=read(a.operations)
assert len(operations)==1877 and len(contexts)==877
bars={}
for path in a.candles.glob('*.csv'):
 group={}
 if path.name.startswith('WIN$N'):
  with path.open(encoding='cp1252',newline='') as f:
   for r in csv.DictReader(f,delimiter='\t'):
    k=r['<DATE>'].replace('.','-')+' '+r['<TIME>'];assert k not in group
    group[k]=tuple(D(r[x]) for x in ('<OPEN>','<HIGH>','<LOW>','<CLOSE>'))
 else:
  with path.open(encoding='cp1252',newline='') as f:
   for r in csv.reader(f,delimiter=';'):
    if len(r)<9 or r[0]!='WINFUT':continue
    k=datetime.strptime(r[1]+' '+r[2],'%d/%m/%Y %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S');assert k not in group
    group[k]=tuple(pn(x) for x in r[3:7])
 bars[path.name]=group
inventory=[]
for r in operations:
 source=contexts[r['Data']]['ArquivoAtual'];key=r['Data']+' '+r['Hora entrada'];o,h,l,c=bars[source][key]
 en,tp,sl=map(D,(r['Entrada'],r['Alvo'],r['Stop']));buy=r['Lado']=='COMPRA'
 assert tp>en>sl if buy else tp<en<sl
 touch=l<=en if buy else h>=en
 assert touch
 beyond=o>tp if buy else o<tp
 at=o==tp
 between=en<o<tp if buy else tp<o<en
 category='ALEM_DO_ALVO' if beyond else 'EXATAMENTE_NO_ALVO' if at else 'ENTRE_ENTRADA_E_ALVO' if between else 'NA_ENTRADA_OU_ALEM_DA_ENTRADA'
 target_inside=h>=tp if buy else l<=tp
 stop_inside=l<=sl if buy else h>=sl
 same=r['Hora entrada']==r['Hora saída'];same_target=same and r['Motivo']=='ALVO'
 if same_target:assert target_inside
 inventory.append({'data':r['Data'],'nivel':r['Nível'],'lado':r['Lado'],'fonte':source,'duracao_original':'M1' if '1min' in source else 'M5','hora_entrada':r['Hora entrada'],'hora_saida':r['Hora saída'],'motivo_Work':r['Motivo'],'pontos_Work_preservados':r['Pontos'],'ambiguo_original':r['Ambíguo'],'entrada':str(en),'alvo':str(tp),'stop':str(sl),'abertura_barra_entrada':str(o),'maxima_barra_entrada':str(h),'minima_barra_entrada':str(l),'fechamento_barra_entrada':str(c),'categoria_abertura':category,'alvo_presente_barra_entrada':target_inside,'stop_presente_barra_entrada':stop_inside,'entrada_saida_mesma_barra':same,'Work_credita_alvo_na_barra_entrada':same_target})
flag='Work_credita_alvo_na_barra_entrada'
assert len(inventory)==1877
summaries=[]
for scope,predicate in [('TOTAL',lambda r:True),*[(str(y),lambda r,y=y:r['data'].startswith(str(y))) for y in range(2023,2027)],('M5',lambda r:r['duracao_original']=='M5'),('M1',lambda r:r['duracao_original']=='M1')]:
 rows=[r for r in inventory if predicate(r)];targets=[r for r in rows if r[flag]]
 summaries.append({'escopo':scope,'operacoes':len(rows),'alvos_na_barra_entrada':len(targets),'percentual_operacoes':str((D(len(targets))*100/D(len(rows))).quantize(D('.01'))),'alem_alvo':sum(r['categoria_abertura']=='ALEM_DO_ALVO' for r in targets),'exatamente_alvo':sum(r['categoria_abertura']=='EXATAMENTE_NO_ALVO' for r in targets),'entre_entrada_alvo':sum(r['categoria_abertura']=='ENTRE_ENTRADA_E_ALVO' for r in targets),'na_entrada_ou_alem_entrada':sum(r['categoria_abertura']=='NA_ENTRADA_OU_ALEM_DA_ENTRADA' for r in targets),'pontos_originais_desses_alvos':str(sum(D(r['pontos_Work_preservados']) for r in targets)),'operacoes_com_alvo_presente_barra_entrada_independente_motivo':sum(r['alvo_presente_barra_entrada'] for r in rows)})
sept=read(a.sept);candidates=[]
for r in sept:
 if r['Work_alvo_na_barra_entrada']=='True' and r['mesmo_motivo']=='True' and r['alvo_ja_alcancado_na_abertura_barra_entrada_EA']=='True':
  original=next(x for x in inventory if x['data']==r['data'] and x['nivel']==r['nivel'])
  assert original[flag] and original['categoria_abertura'] in ('ALEM_DO_ALVO','EXATAMENTE_NO_ALVO')
  candidates.append({'data':r['data'],'nivel':r['nivel'],'hora_entrada_Work':r['Work_entrada_minuto'],'hora_saida_Work':r['Work_saida_minuto'],'motivo_Work':r['Work_motivo'],'motivo_Tester':r['EA_motivo'],'abertura_barra':r['entry_bar_open'],'entrada_math':r['entrada_math'],'alvo_math':r['TP_math'],'estado_ticks':'PENDENTE_CONFERENCIA_DA_SEQUENCIA'})
write('INVENTARIO_1877_OPERACOES.csv',inventory);write('RESUMO_EXPOSICAO.csv',summaries);write('CANDIDATOS_FORA_DOS_SEIS.csv',candidates)
result={'classification_only_no_rule_changes':True,'operations':1877,'dates':877,'summary':summaries,'candidates_September_agreement_same_bar_open_at_or_beyond_target':candidates,'limits':['Exposure counts do not prove the target happened before or after entry.','Current original Work outcome and original ambiguity markers are preserved.','This is not M1 replay of the whole history; M5/M1 follow original sources.','No candidate rule has been applied; totals listed are original accounting exposure, not estimated performance correction.','2023 reference is an earlier MT5 WIN$N export, not an independent Profit feed.'],'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [a.operations,a.contexts,a.sept,*sorted(a.candles.glob('*.csv'))]}}
(a.out/'CONFERENCIA.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='sha256'},ensure_ascii=False,indent=2))
