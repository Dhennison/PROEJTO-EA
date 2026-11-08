"""Exercises actual pilot source under C++ API mocks, not a native MT5 compiler."""
from pathlib import Path
import re,subprocess,tempfile,os
from datetime import datetime,timezone
root=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='winn100_') as d:
 out=Path(d)
 for source in (root/'MQL5').rglob('*'):
  if source.suffix not in ('.mqh','.mq5') or source.name in ('DiagTicksAB.mq5','Inspecionar_Ativo.mq5'):continue
  text=re.sub(r'^#property.*$', '', source.read_text(encoding='utf-8-sig'),flags=re.M)
  text=text.replace('MqlRates rates[]','std::vector<MqlRates> rates')
  text=re.sub(r"D'([^']+)'",lambda m:str(int(datetime.strptime(m[1],'%Y.%m.%d %H:%M:%S').replace(tzinfo=timezone.utc).timestamp())),text)
  dest=out/source.relative_to(root/'MQL5');dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(text)
 texts='\n'.join(p.read_text() for p in out.rglob('*') if p.is_file())+(root/'tests/host.cpp').read_text()
 constants=sorted(set(re.findall(r'\b(?:SYMBOL|ACCOUNT|MQL|TERMINAL|PERIOD|TIME|DEAL|POSITION|ORDER|TRADE|FILE|INIT|CP)_[A-Z0-9_]+\b',texts)))
 flags={'SYMBOL_ORDER_LIMIT':1,'SYMBOL_ORDER_SL':2,'SYMBOL_ORDER_TP':4,'SYMBOL_EXPIRATION_GTC':8,'SYMBOL_EXPIRATION_DAY':16,'SYMBOL_FILLING_FOK':32,'SYMBOL_FILLING_IOC':64}
 (out/'constants.h').write_text('enum { INVALID_HANDLE=-1, '+','.join(f'{n}={flags.get(n,1000+i)}' for i,n in enumerate(constants))+'};\n')
 (out/'host.cpp').write_text((root/'tests/host.cpp').read_text())
 binary=out/'pilot'
 p=subprocess.run(['c++','-std=c++17','-g','-O1','-Wall','-Wextra','-Wno-unused-parameter','-fsanitize=address,undefined','-fno-omit-frame-pointer','-I'+str(out/'Include'),'-I'+str(out/'Experts/ModeloD_PilotoWINN'),str(out/'host.cpp'),'-o',str(binary)],capture_output=True,text=True)
 (root/'tests/COMPILACAO_CPP.txt').write_text(p.stdout+p.stderr+'\nEXIT_STATUS='+str(p.returncode)+'\n')
 if p.returncode:print(p.stderr);raise SystemExit(p.returncode)
 env=os.environ.copy();env['ASAN_OPTIONS']='detect_leaks=0:halt_on_error=1';env['UBSAN_OPTIONS']='halt_on_error=1:print_stacktrace=1'
 p=subprocess.run([str(binary)],capture_output=True,text=True,env=env)
 (root/'tests/RESULTADO_CPP.txt').write_text(p.stdout+p.stderr+'\nEXIT_STATUS='+str(p.returncode)+'\n')
 print(p.stdout+p.stderr);raise SystemExit(p.returncode)
