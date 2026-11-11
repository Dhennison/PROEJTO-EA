"""Regression: prepend a SYNTHETIC month; preserve September PnL, recalculate DD."""
from pathlib import Path
import tempfile,shutil,csv,json,subprocess,sys
from decimal import Decimal as D
root=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='dd_cronologico_') as tmp:
 repo=Path(tmp);copy=repo/'entregas/compilado_work_modelod';shutil.copytree(root,copy)
 def read(path):
  with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f,delimiter=';'))
 def write(path,rows):
  with path.open('w',encoding='utf-8-sig',newline='') as f:
   w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter=';',lineterminator='\n');w.writeheader();w.writerows(rows)
 source=json.loads((copy/'MODELO_D_FONTE_PDF_VALIDADA.json').read_text());index=read(copy/'INDICE_MENSAL.csv');sep=next(r for r in index if r['mes']=='2026-09');aug=next(r for r in index if r['mes']=='2026-08')
 before=read(copy/'diarios_principais/2026_09.csv');before_bytes=(copy/'diarios_principais/2026_09.csv').read_bytes()
 dates=next(r['dates'] for r in source['months'] if r['month']=='2026-08')
 synthetic=[{'data':d,'Work_pontos':source['daily'][d]['value_exact6'],'nosso_pontos':str(1000 if i==0 else -2000 if i==1 else 0)} for i,d in enumerate(dates)]
 write(copy/'diarios_principais/2026_08.csv',synthetic)
 aug.update(estado='CONCLUIDO_TESTE_SINTETICO_NAO_MERCADO',nosso_resultado_principal='-1000',pdf_preservado=sep['pdf_preservado'],pdf_sha256=sep['pdf_sha256'])
 write(copy/'INDICE_MENSAL.csv',index)
 run=subprocess.run([sys.executable,str(copy/'gerar_dois_compilados.py')],cwd=repo,text=True,capture_output=True);assert run.returncode==0,run.stderr
 after=read(copy/'DRAWDOWN_CRONOLOGICO_POR_MES.csv');m=next(r for r in after if r['mes']=='2026-09')
 assert D(m['teste_DD_max_acumulado'])==2750
 assert D(m['teste_DD_local_mensal_referencia'])==1575
 assert (copy/'diarios_principais/2026_09.csv').read_bytes()==before_bytes
 assert sum(D(r['nosso_pontos']) for r in read(copy/'diarios_principais/2026_09.csv'))==1380
 assert m['base_DD_inicio']=='2026-08-04' and m['DD_provisorio_por_meses_anteriores_pendentes']=='True'
 # A hole must not be silently filled with zero or concatenated as continuous history.
 july=next(r for r in index if r['mes']=='2026-07');july['estado']='CONCLUIDO_TESTE_SINTETICO_NAO_MERCADO';aug['estado']='PENDENTE';write(copy/'INDICE_MENSAL.csv',index)
 refused=subprocess.run([sys.executable,str(copy/'gerar_dois_compilados.py')],cwd=repo,text=True,capture_output=True)
 assert refused.returncode!=0 and 'Nao concatenar meses com lacuna' in refused.stderr
result={'passed':True,'scope':'Synthetic August prefix ONLY; not August market results.','checks':['Chronological ordering ignores reverse collection order','Monthly and daily September PnL unchanged','Historical accumulated DD propagates into September','Monthly-local DD remains a distinct reference','Matched Work/test coverage starts at the same date','Earlier missing months mark DD provisional','Gaps between completed months are refused, not zero-filled']}
(root/'VALIDACAO_DRAWDOWN.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print('PASS chronological drawdown; frozen September results; gap rejection. Synthetic test only.')
