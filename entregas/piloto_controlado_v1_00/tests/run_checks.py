"""Tests extracted MQL algorithm bodies via C++ adaptation, not a native MT5 test."""
from pathlib import Path
import subprocess,tempfile,json,hashlib,sys,importlib.util,math,csv,io,os
root=Path(__file__).resolve().parents[1]
code=(root/'MQL5/Include/ModeloD_PilotoControlado/Piloto_Core.mqh').read_text()
def extract(sig):
 start=code.index(sig);brace=code.index('{',start);end=brace+1;depth=1
 while depth:
  depth+=(code[end]=='{')-(code[end]=='}');end+=1
 return code[start:end]
funcs='\n'.join(extract(s) for s in ['bool PHBusiness(','bool PHSameTick(','bool PHSame(','bool PHSubsequence(','bool PHUnsigned(','bool PHNumeric(','bool PHValidTicks(','int PHBatchEnd(','int PHBars('])
import re
for typ in ['MqlTick','MqlRates']:
 funcs=re.sub(r'const '+typ+r' &(\w+)\[\]',r'const std::vector<'+typ+r'> &\1',funcs)
 funcs=re.sub(typ+r' &(\w+)\[\]',r'std::vector<'+typ+r'> &\1',funcs)
cpp=r'''
#include <vector>
#include <string>
#include <cmath>
#include <cstring>
#include <iostream>
#include <limits>
#include <algorithm>
using string=std::string;using datetime=long;using ushort=unsigned short;
struct MqlTick {long time;long time_msc;double bid,ask,last;unsigned long volume;double volume_real;unsigned int flags;};
struct MqlRates {long time;double open,high,low,close;long tick_volume;int spread;long real_volume;};
int StringLen(const string&s){return s.size();}
ushort StringGetCharacter(const string&s,int i){return (unsigned char)s[i];}
string IntegerToString(long n){return std::to_string(n);}
bool MathIsValidNumber(double d){return std::isfinite(d);}
double MathMax(double a,double b){return std::max(a,b);}double MathMin(double a,double b){return std::min(a,b);}
template<class T>int ArraySize(const std::vector<T>&v){return v.size();}
template<class T>int ArrayResize(std::vector<T>&v,int n){v.resize(n);return n;}
template<class T>void ZeroMemory(T&v){std::memset(&v,0,sizeof(v));}
'''+funcs+r'''
int checks=0,failures=0;
void check(bool b,const char*n){checks++;if(!b){failures++;std::cout<<"FAIL "<<n<<"\n";}}
int main(){
 for(auto s:{"0","0002","4294967295"})check(PHUnsigned(s),"unsigned valid");
 for(auto s:{"","+2","-1","2x","1.0"," 3"})check(!PHUnsigned(s),"unsigned invalid");
 for(auto s:{"0","1.0",".5","-0.25","+1.2e+03","1e-8","1.","2E3"})check(PHNumeric(s),"numeric valid");
 for(auto s:{"",".","e2","1e","1e+","NaN","inf","1,25","1.2x"," 1","1 2"})check(!PHNumeric(s),"numeric invalid");
 MqlTick a{1000,1000000,100,105,100,2,2,1336};
 auto q=a;q.flags=6;check(!PHBusiness(q),"carried Last not trade");
 check(PHBusiness(a),"unknown flag bits preserve classification");
 auto generated=a;generated.flags=30;check(PHBusiness(generated),"generated flags can pass classifier; not authenticity");
 std::vector<MqlTick> s{a,a};auto b=a;b.last=105;s.push_back(b);
 check(PHSame(s,s),"self equality");check(!PHSame(s,{a,b}),"duplicate count matters");
 check(PHSubsequence(s,{a,b}),"coalesced sequence");check(PHSubsequence(s,{a,a,b}),"repeated ms preserved");
 check(!PHSubsequence(s,{a,a,a,b}),"cannot invent duplicate occurrence");
 check(!PHSubsequence(s,{b,a}),"order reversal detected");
 check(PHSubsequence(s,{}),"empty is subsequence but not equality");
 for(int k=0;k<8;k++){
  auto t=a;switch(k){case 0:t.time++;break;case 1:t.time_msc++;break;case 2:t.bid++;break;case 3:t.ask++;break;
  case 4:t.last++;break;case 5:t.volume++;break;case 6:t.volume_real++;break;case 7:t.flags^=1024;break;}
  check(!PHSameTick(a,t),"every field compared exactly");
 }
 check(PHBatchEnd(s,0,1)==3,"batch keeps repeated timestamp group");
 check(PHBatchEnd(s,0,2)==3,"batch ends at group boundary");
 check(PHBatchEnd(s,0,3)==3,"batch includes whole source");
 check(PHBatchEnd(s,2,1000)==3,"batch tail bounded");
 check(PHBatchEnd(s,3,1000)==3,"batch empty tail");
 check(PHBatchEnd(s,0,0)==0,"batch invalid requested size");
 std::vector<MqlTick> grouped;
 for(int i=0;i<10007;i++){auto x=a;x.time_msc=1000000+(i/13);x.time=x.time_msc/1000;grouped.push_back(x);}
 int cursor=0,total=0;
 while(cursor<(int)grouped.size()){
  int end=PHBatchEnd(grouped,cursor,1000);
  check(end>cursor&&end<=(int)grouped.size(),"batch progress and bounds");
  check(end==(int)grouped.size()||grouped[end-1].time_msc<grouped[end].time_msc,"batch no repeated-ms overlap");
  total+=end-cursor;cursor=end;
 }
 check(total==10007,"batches preserve every record exactly once");
 string why;check(PHValidTicks(s,1000000,1060000,why),"repeated timestamp valid");
 check(!PHValidTicks(s,1000001,1060000,why),"lower boundary enforced");
 check(!PHValidTicks(s,900000,1000000,why),"exclusive upper enforced");
 auto bad=a;bad.time++;check(!PHValidTicks({bad},1000000,1060000,why),"seconds mismatch");
 bad=a;bad.last=std::numeric_limits<double>::quiet_NaN();check(!PHValidTicks({bad},1000000,1060000,why),"nan rejected");
 bad=a;bad.last=0;check(!PHValidTicks({bad},1000000,1060000,why),"flagged zero last rejected");
 bad=a;bad.bid=110;check(PHValidTicks({bad},1000000,1060000,why),"inverted source quotes preserved, not repaired");
 auto next=a;next.time=1060;next.time_msc=1060000;next.last=95;
 check(!PHValidTicks({next,a},1000000,1120000,why),"retrograde timestamp rejected");
 std::vector<MqlRates> bars;
 check(PHBars({a,q,b,next},bars)==2,"minute aggregation only flagged trades");
 check(bars[0].open==100&&bars[0].high==105&&bars[0].low==100&&bars[0].close==105&&bars[0].tick_volume==2&&bars[0].real_volume==4,"OHLC and volume");
 check(bars[1].open==95&&bars[1].close==95,"second minute separate");
 std::cout<<"checks="<<checks<<" failures="<<failures<<"\n";return failures?1:0;
}
'''
with tempfile.TemporaryDirectory(prefix='mdd_pilot_') as td:
 p=Path(td);(p/'check.cpp').write_text(cpp)
 c=subprocess.run(['g++','-std=c++17','-O1','-g','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-omit-frame-pointer',str(p/'check.cpp'),'-o',str(p/'check')],capture_output=True,text=True)
 if c.returncode:raise RuntimeError(c.stderr)
 r=subprocess.run([str(p/'check')],capture_output=True,text=True,env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1'))
 if r.returncode:raise RuntimeError(r.stdout+r.stderr)
 native_algorithms=r.stdout.strip()
# Python postprocessor tests: independently supplied repeated-ms/changed-field cases.
spec=importlib.util.spec_from_file_location('pilot_check',root/'verificar_retorno.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
a=(1000,1000000,100.,105.,100.,2,2.,1336);b=(*a[:4],105.,*a[5:]);seq=[a,a,b]
assert mod.compare(seq,seq)['exact']
assert mod.compare(seq,[a,b])['ordered_subsequence'] and not mod.compare(seq,[a,b])['exact']
assert not mod.compare(seq,[b,a])['ordered_subsequence']
assert not mod.compare(seq,[a,a,a,b])['ordered_subsequence']
for k in range(8):
 t=list(a);t[k]+=1;assert not mod.compare([a],[tuple(t)])['exact']
# Bounded plan syntax and all three exact input names.
plan=list(csv.DictReader((root/'MQL5/Files/SONDA_PILOTO_9_JANELAS.csv').open(),delimiter=';'))
assert len(plan)==9 and len({r['de'][:4] for r in plan})==4
all_mql='\n'.join(p.read_text() for p in (root/'MQL5').rglob('*.mq*'))
for forbidden in ['OrderSend(', 'OrderSendAsync(', 'CTrade','CustomSymbolDelete(','CustomRatesReplace(']:assert forbidden not in all_mql
assert all_mql.count('CustomTicksReplace(')==1
# OnTick must stay cheap: storage only, no I/O/hash/queries/resizing.
ea=(root/'MQL5/Experts/ModeloD_PilotoControlado/Diagnostico_Piloto_OnTick.mq5').read_text()
event=ea[ea.index('void OnTick()'):ea.index('void PilotFinish(')]
for forbidden in ['FileWrite','PHHash','CopyTicksRange','ArrayResize','Sleep(']:assert forbidden not in event
result={'cpp_extracted_algorithms':native_algorithms,'sanitizers':'address,undefined','python_checks':'passed: equality, order, duplicate timestamps, every field, plan, mutation boundaries, buffered OnTick',
 'scope':'Algorithms adapted to C++; no native MQL compilation, no MT5 API/import/OnTick execution here.',
 'source_sha256':{p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'MQL5').rglob('*')) if p.is_file()}}
(root/'tests/RESULTADO.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
