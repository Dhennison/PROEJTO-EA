from pathlib import Path
from datetime import datetime,timezone
import re,tempfile,subprocess,os,json,hashlib
root=Path(__file__).resolve().parents[1]
script=(root/'MQL5/Scripts/ModeloD_PilotoControlado/Preparar_Contexto_Piloto.mq5').read_text()
core=(root/'MQL5/Include/ModeloD_PilotoControlado/Piloto_Core.mqh').read_text()
def extract(code,signature):
 a=code.index(signature);b=code.index('{',a);n=1;b+=1
 while n:n+=(code[b]=='{')-(code[b]=='}');b+=1
 return code[a:b]
f='\n'.join([extract(core,'bool PHSameTick(')]+[extract(script,k) for k in ['bool CXSameRates(','bool CXSafeContext(','int CXGroupsM5(','bool CXMatchesObservedMapping(']])
for t in ('MqlTick','MqlRates'):f=re.sub(r'const '+t+r' &(\w+)\[\]',r'const std::vector<'+t+r'>&\1',f)
a=int(datetime(2026,10,27,tzinfo=timezone.utc).timestamp());b=int(datetime(2026,10,29,tzinfo=timezone.utc).timestamp())
cpp='''#include <vector>
#include <string>
#include <cmath>
#include <algorithm>
#include <iostream>
#include <limits>
using datetime=long;using string=std::string;
struct MqlTick{long time,time_msc;double bid,ask,last;unsigned long volume;double volume_real;unsigned int flags;};
struct MqlRates{long time;double open,high,low,close;long tick_volume;int spread;long real_volume;};
template<class T>int ArraySize(const std::vector<T>&v){return v.size();}
bool MathIsValidNumber(double n){return std::isfinite(n);}double MathMin(double a,double b){return std::min(a,b);}double MathMax(double a,double b){return std::max(a,b);}
'''+f'constexpr long CX_CONTEXT_FROM={a},CX_CONTEXT_TO={b};\n'+f+'''
int count=0,fail=0;void check(bool b,const char*s){count++;if(!b){fail++;std::cout<<"FAIL "<<s<<"\\n";}}
int main(){
 MqlRates a{CX_CONTEXT_FROM+9*3600,100,110,90,105,3,5,20};
 check(CXSafeContext({a}),"real previous minute allowed");
 auto t=a;t.time=CX_CONTEXT_TO;check(!CXSafeContext({t}),"target midnight excluded");
 t=a;t.time=CX_CONTEXT_TO+9*3600;check(!CXSafeContext({t}),"target window excluded");
 t=a;t.time=CX_CONTEXT_FROM-60;check(!CXSafeContext({t}),"outside context excluded");
 t=a;t.time++;check(!CXSafeContext({t}),"minute alignment enforced");
 check(!CXSafeContext({a,a}),"duplicate bar timestamp refused");
 t=a;t.time+=60;check(!CXSafeContext({t,a}),"time reversal refused");
 t=a;t.open=111;check(!CXSafeContext({t}),"invalid OHLC refused");
 t=a;t.close=std::numeric_limits<double>::quiet_NaN();check(!CXSafeContext({t}),"nonfinite refused");
 t=a;t.tick_volume=-1;check(!CXSafeContext({t}),"negative tick volume refused");
 t=a;t.real_volume=-1;check(!CXSafeContext({t}),"negative real volume refused");
 check(!CXSafeContext({}),"empty context refused");
 check(CXSameRates({a},{a}),"rates exact");check(!CXSameRates({a},{}),"rate length matters");
 for(int i=0;i<8;i++){t=a;switch(i){case 0:t.time++;break;case 1:t.open++;break;case 2:t.high++;break;case 3:t.low++;break;case 4:t.close++;break;case 5:t.tick_volume++;break;case 6:t.spread++;break;case 7:t.real_volume++;break;}check(!CXSameRates({a},{t}),"all rate fields compared");}
 std::vector<MqlRates> ctx;for(int i=0;i<1000;i++){t=a;t.time+=i*60;ctx.push_back(t);}
 check(CXGroupsM5(ctx)==200,"200 prior M5 groups counted");
 MqlTick raw{1793264458,1793264458034,0,0,173135,250,250,1336};auto stored=raw;stored.flags=56;
 check(CXMatchesObservedMapping({raw},{stored}),"known flag mapping accepted only as comparison view");
 stored.flags|=1024;check(!CXMatchesObservedMapping({raw},{stored}),"unexpected extra stored flag rejected");
 stored=raw;stored.flags=56;stored.last++;check(!CXMatchesObservedMapping({raw},{stored}),"price modification rejected");
 check(raw.flags==1336,"source remained unchanged");
 std::cout<<"checks="<<count<<" failures="<<fail<<"\\n";return fail?1:0;
}
'''
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp);(p/'test.cpp').write_text(cpp)
 r=subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-g',str(p/'test.cpp'),'-o',str(p/'test')],text=True,capture_output=True)
 if r.returncode:raise RuntimeError(r.stderr)
 r=subprocess.run([str(p/'test')],text=True,capture_output=True,env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1'))
 if r.returncode:raise RuntimeError(r.stdout+r.stderr)
 log=r.stdout.strip()
assert 'CustomSymbolDelete' not in script and 'OrderSend' not in script
assert 'CustomRatesUpdate(symbol,context)' in script
assert 'CustomRatesUpdate(InpCopiaOriginal' not in script and 'CustomTicksReplace(InpCopiaOriginal' not in script
assert 'CXSameRates(before_target,after_target)' in script and 'PHSame(before,after)' in script
assert (root/'MQL5/Include/ModeloD_PilotoControlado/Piloto_Core.mqh').read_bytes()==(root.parent/'piloto_controlado_v1_00/MQL5/Include/ModeloD_PilotoControlado/Piloto_Core.mqh').read_bytes()
result={'checks':log,'sanitizers':'address,undefined','scope':'Extracted pure functions adapted to C++, no native MQL compilation/API execution.',
 'core_identical_v100':True,'tester_EA_changed':False,'source_sha256':hashlib.sha256(script.encode()).hexdigest()}
(root/'tests/RESULTADO.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))
