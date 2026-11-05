"""Audit only Modelo D reference; no EA execution or reconstructed price returns."""
import argparse,csv,json,hashlib
from decimal import Decimal
from collections import Counter,defaultdict
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('dados',type=Path);p.add_argument('--saida',type=Path,required=True);a=p.parse_args()
def rows(name):
 with (a.dados/name).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter=';'))
def num(s):return Decimal(s.replace(',','.'))
ops=rows('Operacoes_Modelo_D_20230301_20260921_ORIGINAL.csv');daily=rows('Referencia_D_diário.csv');monthly=rows('Referencia_D_mensal.csv');annual=rows('Referencia_D_anual.csv');adj=rows('Ajustes_Diarios_Modelo_D_20230301_20260921.csv');dd=rows('Referencia_D_drawdown.csv');controls=[r for r in rows('Referencia_D_controles.csv') if r['Modelo']=='D']
checks={}
checks['1877_operacoes']=len(ops)==1877
checks['877_pregoes_unicos']=len(daily)==len({r['Data'] for r in daily})==877
checks['csv_duplicado_nao_concatenado']=(a.dados/'Referencia_D_operacoes.csv').read_bytes()==(a.dados/'Operacoes_Modelo_D_20230301_20260921_ORIGINAL.csv').read_bytes()
checks['chave_data_nivel_lado_unica']=len({(r['Data'],r['Nível'],r['Lado']) for r in ops})==len(ops)
checks['cinco_niveis']=set(r['Nível'] for r in ops)=={'S38.2','S50','S61.8','R38.2','R61.8'}
checks['datas_operacoes_elegiveis']={r['Data'] for r in ops}<={r['Data'] for r in daily}
checks['ajuste_unico_e_mesmas_877_datas']=len(adj)==len({r['DataOperacional'] for r in adj})==877 and {r['DataOperacional'] for r in adj}=={r['Data'] for r in daily}
byday=defaultdict(lambda:Decimal(0));counts=Counter();byyear=defaultdict(lambda:Decimal(0));yearcounts=Counter()
for r in ops:byday[r['Data']]+=num(r['Pontos']);counts[r['Data']]+=1;byyear[r['Data'][:4]]+=num(r['Pontos']);yearcounts[r['Data'][:4]]+=1
checks['operacoes_conferem_cada_dia']=all(byday[r['Data']]==num(r['Pontos']) and counts[r['Data']]==int(r['Operações']) for r in daily)
checks['ajustes_contagem_operacoes_por_dia']=all(int(r['OperacoesD'])==counts[r['DataOperacional']] for r in adj)
bymonth=defaultdict(lambda:Decimal(0));monthcounts=Counter()
for r in ops:bymonth[r['Data'][:7]]+=num(r['Pontos']);monthcounts[r['Data'][:7]]+=1
checks['operacoes_conferem_cada_mes']=all(bymonth[r['Mês']]==num(r['Pontos']) and monthcounts[r['Mês']]==int(r['Operações']) for r in monthly)
checks['operacoes_conferem_cada_ano']=all(byyear[r['Período']]==num(r['Pontos']) and yearcounts[r['Período']]==int(r['Operações']) for r in annual if r['Período']!='Total' and r['Modelo']=='D')
total=sum((num(r['Pontos']) for r in ops),Decimal(0))
checks['soma_124337_758661']=total==Decimal('124337.758661')==sum((num(r['Pontos']) for r in daily),Decimal(0))==sum((num(r['Pontos']) for r in monthly),Decimal(0))
checks['linha_total_nao_somada_duas_vezes']=sum((num(r['Pontos']) for r in annual if r['Modelo']=='D' and r['Período']!='Total'),Decimal(0))==total
balance=peak=maxdd=Decimal(0);daily_curve=True
for r in daily:
 balance+=num(r['Pontos']);peak=max(peak,balance);draw=peak-balance;maxdd=max(maxdd,draw)
 daily_curve &= balance==num(r['Acumulado']) and peak==num(r['Pico acumulado']) and draw==num(r['Drawdown'])
checks['curva_diaria_saldo_zero']=bool(daily_curve)
# Independent quadratic prefix scan, suitable for this small daily dataset.
prefix=[Decimal(0)]
for r in daily:prefix.append(prefix[-1]+num(r['Pontos']))
independent=max(max(prefix[:j+1])-value for j,value in enumerate(prefix))
checks['dd_duas_rotinas_4780_240329']=maxdd==independent==Decimal('4780.240329')
checks['dd_apenas_colunas_D']=len(dd)==877 and all(r['Data']==d['Data'] and num(r['DD D'])==num(d['Drawdown']) and num(r['Acumulado D'])==num(d['Acumulado']) for r,d in zip(dd,daily))
checks['controles_filtrados_D']=len(controls)==5 and all(num(r['Diferença micropontos'])==0 for r in controls)
checks['contrato_publicacao_anterior_nao_inventados']=all(not r[k] for r in adj for k in ['ContratoReal','DataFontePublicacao','AjusteAnterior'])
checks['cutoff_historico_operacoes']=all(r['Zeragem']==('17:45:00' if '2023-03-13'<=r['Data']<='2023-11-03' else '18:00:00') for r in ops)
checks['cutoff_historico_ajustes']=all(r['ZeragemComparacaoWork']==('17:45:00' if '2023-03-13'<=r['DataOperacional']<='2023-11-03' else '18:00:00') for r in adj)
out={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'periodo':[daily[0]['Data'],daily[-1]['Data']],'operacoes':len(ops),'pregoes':len(daily),'pregoes_sem_operacao':sum(int(r['Operações'])==0 for r in daily),'pontos':str(total),'dd_diario':str(maxdd),'por_ano':{y:{'operacoes':yearcounts[y],'pontos':str(byyear[y])} for y in sorted(byyear)},'motivos':dict(Counter(r['Motivo'] for r in ops)),'zeragens_efetivas':dict(Counter(r['Hora saída'] for r in ops if r['Motivo'].startswith('ZERAGEM'))),'marcadores_ambiguidade':dict(Counter(r['Ambíguo'] for r in ops)),'hashes_csv':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(a.dados.glob('*.csv'))},'limite':'Auditoria da referencia D; nao executa EA nem certifica candles, ticks ou contratos.'}
a.saida.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='hashes_csv'},ensure_ascii=False,indent=2));raise SystemExit(0 if all(checks.values()) else 1)
