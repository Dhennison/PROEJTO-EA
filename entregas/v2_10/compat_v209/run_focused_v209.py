from pathlib import Path
import argparse,re,subprocess,tempfile,os
parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=Path('/workspace/PROEJTO-EA/ModeloD_Integrado_Sem_Transporte'));parser.add_argument('--sanitize',action='store_true');args=parser.parse_args()
root=args.root.resolve();art=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='modelod_209_') as tmp:
 build=Path(tmp)
 for file in (root/'MQL5/Experts/ModeloD_Integrado_Sem_Transporte').iterdir():
  if file.suffix not in ('.mq5','.mqh'):continue
  content=re.sub(r'^#property.*$','',file.read_text(),flags=re.M)
  content=re.sub(r'^input ','',content,flags=re.M)
  content=re.sub(r'\b(MqlTick|MqlRates) (\w+)\[\];',r'std::vector<\1> \2;',content)
  (build/file.name).write_text(content)
 mock=(root/'tests/runtime_mock.cpp').read_text()
 mock=mock.replace('EA_ADAPTED_PATH',str(build/'EA_ModeloD_Fluxo_Sem_Ordens.mq5'))
 mock=mock.replace('#include "host.cpp"',f'#include "{root}/tests/host.cpp"').replace('#include "../MQL5/',f'#include "{root}/MQL5/')
 mock=mock.replace('int main(){','int inherited_runtime_main209(){',1)
 mock=mock.replace('out.push_back(v);return out.size();}', 'out.push_back(v);if(mock_stop_in_rates209)mock_stop209=true;return out.size();}')
 mock=mock.replace('bool EventSetTimer(int)', 'bool mock_stop209=false,mock_partial209=false,mock_raw209=false,mock_drop209=false,mock_stop_in_read209=false,mock_stop_in_rates209=false;int mock_copy209=0;\nbool EventSetTimer(int)')
 mock=mock.replace('bool IsStopped(){return false;}','bool IsStopped(){return mock_stop209;}')
 mock=mock.replace(' out.clear();if(mock_tick_error)', ' mock_copy209++;out.clear();if(mock_tick_error)')
 mock=mock.replace(' for(auto v:source)if(v.time_msc>=(long)from&&v.time_msc<=(long)until)out.push_back(v);', ' for(auto v:source)if(mock_raw209||(v.time_msc>=(long)from&&v.time_msc<=(long)until))out.push_back(v);\n if(mock_partial209)lastError=4403;\n if(mock_drop209)mock_connected=false;\n if(mock_stop_in_read209)mock_stop209=true;')
 (build/'focused.cpp').write_text(mock+'\n'+(art/'tests_v209.cpp').read_text())
 flags=['-std=c++17','-O0','-g','-Wall','-Wextra','-Wno-unused-parameter']
 if args.sanitize:flags+=['-fsanitize=address,undefined','-fno-omit-frame-pointer']
 env=os.environ.copy()
 if args.sanitize:env['ASAN_OPTIONS']='halt_on_error=1';env['UBSAN_OPTIONS']='halt_on_error=1:print_stacktrace=1'
 result=subprocess.run(['c++',*flags,str(build/'focused.cpp'),'-o',str(build/'focused')],text=True,capture_output=True)
 (art/'FOCUSED_COMPILACAO.txt').write_text(result.stdout+result.stderr+f'\nEXIT_STATUS={result.returncode}\n')
 if result.returncode:print(result.stderr[-6000:]);raise SystemExit(result.returncode)
 result=subprocess.run([str(build/'focused')],text=True,capture_output=True,env=env)
 (art/'VALIDACAO_FOCUSED_v2_09.txt').write_text(result.stdout+result.stderr+f'\nEXIT_STATUS={result.returncode}\n')
 print('\n'.join(l for l in result.stdout.splitlines() if l.startswith(('PASS_209','FAIL_209','FOCUSED_209'))))
 if result.stderr:print(result.stderr[-4000:])
 raise SystemExit(result.returncode)
