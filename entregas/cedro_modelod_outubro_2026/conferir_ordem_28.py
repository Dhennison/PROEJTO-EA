"""Leitura alternativa em ordem de arquivo; nao escolhe a variante por lucro."""
from pathlib import Path
from decimal import Decimal as D
import importlib.util,subprocess,zipfile,csv,json
HERE=Path(__file__).resolve().parent;spec=importlib.util.spec_from_file_location('c',HERE.parent/'cedro_modelod_setembro_2026/calcular.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
root=Path('/workspace/retorno_cedro_20261112');checks=[]
for day in ['20261028']:
 red=root/('ORDEM_ARQUIVO_'+day+'.csv');direct=HERE/'resultado_restantes'/('DIRETO_ORDEM_ARQUIVO_'+day+'.csv');cfg=HERE/'resultado_restantes'/(day+'.config')
 with red.open('wb') as f:
  proc=subprocess.Popen(['/tmp/cedro-reduzir-setembro',str(cfg),str(direct),'file'],stdin=subprocess.PIPE,stdout=f,stderr=subprocess.PIPE)
  for path in sorted((root/'ticks').glob('WIN_'+day+'_*.zip')):
   with zipfile.ZipFile(path) as z:
    with z.open(z.namelist()[0]) as inp:
     while chunk:=inp.read(1024*1024):proc.stdin.write(chunk)
  proc.stdin.close();log=proc.stderr.read().decode();assert proc.wait()==0,log
 old=c.read(direct);chron=c.read(HERE/'resultado_restantes'/('DIRETO_'+day+'.csv'));assert len(old)==len(chron)==5
 for a,b in zip(old,chron):
  keys=['eligible','entered','closed','entry_ord','entry_ms','entry_price','exit_ord','exit_ms','exit_price','theory_exit','reason','points']
  changes=[k for k in keys if a[k]!=b[k]]
  checks.append({'data':day,'nivel':a['nivel'],'arquivo_pontos':a['points'],'cronologico_pontos':b['points'],'campos_diferentes':'|'.join(changes),'mesmo_desfecho_e_pontos':a['points']==b['points'] and a['reason']==b['reason']})
 print('SENSIBILIDADE',day,log.strip(),flush=True)
c.write(HERE/'resultado_restantes/SENSIBILIDADE_ORDEM.csv',checks)
result={'registros_preservados':True,'ordenacao_principal':'timestamp e linha_original como desempate','alternativa':'ordem original do arquivo','estados':len(checks),'todos_mesmo_resultado':all(r['mesmo_desfecho_e_pontos'] for r in checks),'sem_filtro_ou_correcao_de_negocios':True,'nao_resolve_divergencias_de_conteudo_EOD':True}
(HERE/'resultado_restantes/SENSIBILIDADE_ORDEM.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
