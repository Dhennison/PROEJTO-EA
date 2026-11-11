"""Exercise actual collector source with C++ API mocks, not a native MQL compiler."""
import re,subprocess,tempfile,os,sys,json
from pathlib import Path
from datetime import datetime,timezone
root=Path(__file__).resolve().parents[1]
fixture=Path('/workspace/PROEJTO-EA/entregas/piloto_winn_periodo_v1_10/referencias/WORK_M1_SETEMBRO.csv')
with tempfile.TemporaryDirectory(prefix='mes100_') as d:
 d=Path(d);source=root/'MQL5/Experts/ModeloD_Fechamento_Setembro'
 for p in source.iterdir():
  if p.suffix not in ('.mqh','.mq5'):continue
  s=p.read_text(encoding='utf-8-sig');s=re.sub(r'^#property.*$','',s,flags=re.M).replace('input ','')
  s=s.replace('Ref refs[];','std::vector<Ref> refs;')
  s=s.replace('MqlTick before[],now[];','std::vector<MqlTick> before,now;')
  s=re.sub(r'const MqlTick &(\w+)\[\]',r'const std::vector<MqlTick> &\1',s)
  s=s.replace('uchar data[],key[],digest[];','std::vector<uchar> data,key,digest;')
  s=re.sub(r"D'([^']+)'",lambda m:str(int(datetime.strptime(m[1],'%Y.%m.%d %H:%M:%S' if len(m[1])>10 else '%Y.%m.%d').replace(tzinfo=timezone.utc).timestamp())),s)
  (d/p.name).write_text(s)
 (d/'host.cpp').write_text((root/'testes/host.cpp').read_text())
 binary=d/'collector'
 compile=subprocess.run(['c++','-std=c++17','-O1','-g','-Wall','-Wextra','-Wno-unused-parameter','-Wno-sign-compare','-fsanitize=address,undefined','-fno-omit-frame-pointer',str(d/'host.cpp'),'-lcrypto','-o',str(binary)],text=True,capture_output=True)
 (root/'testes/COMPILACAO_CPP.txt').write_text(compile.stdout+compile.stderr+'\nEXIT_STATUS='+str(compile.returncode)+'\n')
 if compile.returncode:print(compile.stderr);raise SystemExit(compile.returncode)
 env=os.environ.copy();env['ASAN_OPTIONS']='detect_leaks=0:halt_on_error=1';env['UBSAN_OPTIONS']='halt_on_error=1'
 out=d/'resultado_sintetico'
 run=subprocess.run([str(binary),str(root/'MQL5/Files/MD_Setembro_2026_Referencias.csv'),str(fixture),str(out)],capture_output=True,text=True,env=env)
 (root/'testes/RESULTADO_CPP.txt').write_text(run.stdout+run.stderr+'\nEXIT_STATUS='+str(run.returncode)+'\n');print(run.stdout+run.stderr)
 if run.returncode:raise SystemExit(run.returncode)
 # End-to-end consumer on labelled synthetic transport; do not publish its PnL as real.
 analyze=subprocess.run([sys.executable,str(root/'analise/analisar_mes.py'),'--coleta',str(out),'--work-m1','/workspace/candles_originais_modelo_d/WINFUT_F_0_1min_01-01-2026_22-09-2026.csv','--out',str(d/'audit')],text=True,capture_output=True)
 pipeline_result=json.loads(analyze.stdout) if analyze.returncode==0 else {}
 (root/'testes/RESULTADO_PIPELINE_SINTETICO.txt').write_text('SYNTHETIC FOUR-POINT PATH — API/PIPELINE TEST ONLY, NOT HISTORICAL TICKS OR PERFORMANCE\n'+json.dumps({k:v for k,v in pipeline_result.items() if k in ('complete_price_replay','minute_checks','price_differences','quantity_differences')},indent=2)+'\nEXIT_STATUS='+str(analyze.returncode)+'\n'+analyze.stderr)
 print('Pipeline synthetic exit',analyze.returncode)
 if analyze.returncode:print(analyze.stderr)
 if analyze.returncode:raise SystemExit(analyze.returncode)
 # Refuse a monthly result on pending chunks or a price mismatch.
 base_args=[sys.executable,str(root/'analise/analisar_mes.py'),'--coleta',str(out),'--work-m1','/workspace/candles_originais_modelo_d/WINFUT_F_0_1min_01-01-2026_22-09-2026.csv']
 status_file=out/'BLOCOS.csv';status_original=status_file.read_text()
 status_file.write_text(status_original.replace(';ESTAVEL;',';PENDENTE;',1))
 refused=subprocess.run(base_args+['--out',str(d/'refused_pending')],text=True,capture_output=True)
 assert refused.returncode!=0 and not (d/'refused_pending/RESULTADO_MENSAL.json').exists()
 status_file.write_text(status_original)
 minute=out/'MINUTOS_20260901.csv';original_minute=minute.read_text();lines=original_minute.splitlines();columns=lines[0].split(';');hi=columns.index('high')
 for i in range(1,len(lines)):
  row=lines[i].split(';')
  if int(row[1])>0:
   row[hi]=str(float(row[hi])+5);lines[i]=';'.join(row);break
 minute.write_text('\n'.join(lines)+'\n')
 price=subprocess.run(base_args+['--out',str(d/'refused_price')],text=True,capture_output=True)
 assert price.returncode==0,price.stderr
 result=json.loads((d/'refused_price/RESULTADO_MENSAL.json').read_text())
 assert not result['complete_price_replay'] and all(r['pontos_mensais_teoricos'] is None for r in result['new_price_scenarios'])
 (root/'testes/RESULTADO_RECUSAS.txt').write_text('PASS pending chunks refuse month; price mismatch suppresses all four monthly totals. Synthetic API transport only.\n')
 print('PASS pending/price failure controls')
