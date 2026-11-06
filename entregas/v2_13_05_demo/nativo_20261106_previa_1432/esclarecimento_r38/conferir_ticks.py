"""Reconstruct observed Last touch and subsequent theoretical boundary; not a fill simulator."""
from pathlib import Path
from decimal import Decimal as D
from datetime import datetime,timezone
import csv,json,argparse
p=argparse.ArgumentParser();p.add_argument('csv',type=Path);p.add_argument('--saida',type=Path,required=True);a=p.parse_args()
with a.csv.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f,delimiter='\t'))
entry=D('168806.3106666666863021');adjustment=D('167848');r200=adjustment+(entry-adjustment)/D('.382')
target=adjustment+(r200-adjustment)*D('.236');stop=entry+D(375)
trades=[];quotes={}
for i,row in enumerate(rows,2):
 for field in ['<BID>','<ASK>']:
  if row[field]:quotes[field]={'preco':row[field],'horario':row['<TIME>'],'linha':i}
 if not (int(row['<FLAGS>'])&120) or not row['<LAST>']:continue
 price=D(row['<LAST>']);assert price.is_finite() and price>0
 ms=int(datetime.strptime(row['<DATE>']+' '+row['<TIME>'],'%Y.%m.%d %H:%M:%S.%f').replace(tzinfo=timezone.utc).timestamp()*1000)
 trades.append({'msc_civil_servidor':ms,'hora':row['<TIME>'],'last':str(price),'linha_csv':i,'flags':int(row['<FLAGS>']),'ultimas_cotacoes_precedentes':quotes.copy()})
assert all(x['msc_civil_servidor']<=y['msc_civil_servidor'] for x,y in zip(trades,trades[1:]))
first=next(i for i,t in enumerate(trades) if D(t['last'])>=entry)
assert first>0 and D(trades[first-1]['last'])<entry
post=trades[first:]
tp=next(t for t in post if D(t['last'])<=target);sl=next((t for t in post if D(t['last'])>=stop),None)
assert trades[first]['msc_civil_servidor']==1793961002602 and tp['msc_civil_servidor']==1793961002618
assert tp['msc_civil_servidor']<1793961004000 and sl is None
out={'linhas_dados':len(rows),'ticks_negocio_validos':len(trades),'horarios_civis_servidor_sem_converter_fuso':True,'entrada_matematica':str(entry),'alvo_matematico_derivado_aproximado':str(target),'SL_matematico':str(stop),'entrada_normalizada':'168805','alvo_normalizado':'168440','SL_normalizado':'169180','primeiro_toque':trades[first],'alvo_apos_toque':tp,'primeiro_stop_apos_toque':sl,'intervalo_toque_alvo_ms':tp['msc_civil_servidor']-trades[first]['msc_civil_servidor'],'cancelamento_reportado_no_log':'10:30:04','alvo_antes_cancelamento':True,'conclusao':'Cancelamento da pendente tocada e nao executada esta conforme regra de fronteira teorica.','limite':'Esta sequencia nao prova preenchimento nem a causa interna do nao preenchimento no simulador.'}
a.saida.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps(out,ensure_ascii=False,indent=2))
