from pathlib import Path
import re,tempfile,subprocess,os,json,hashlib
root=Path(__file__).resolve().parents[1]
source=(root/'MQL5/Experts/ModeloD_PilotoControlado/Diagnostico_Piloto_Consultas.mq5').read_text()
core=(root/'MQL5/Include/ModeloD_PilotoControlado/Piloto_Core.mqh').read_text()
def extract(text,sig):
 a=text.index(sig);b=text.index('{',a)+1;n=1
 while n:n+=(text[b]=='{')-(text[b]=='}');b+=1
 return text[a:b]
f='\n'.join([extract(core,'bool PHSameTick('),extract(core,'bool PHSame('),extract(core,'bool PHValidTicks('),extract(source,'bool QueryRead(')])
f=re.sub(r'const MqlTick &(\w+)\[\]',r'const std::vector<MqlTick>&\1',f)
f=re.sub(r'MqlTick &(\w+)\[\]',r'std::vector<MqlTick>&\1',f)
f=re.sub(r'MqlTick (\w+)\[\],(\w+)\[\];',r'std::vector<MqlTick> \1,\2;',f)
f=re.sub(r'\(string\)\(int\)(\w+)',r'std::to_string((int)\1)',f)
f=re.sub(r'\(string\)(\w+)',r'std::to_string(\1)',f)
cpp=r'''
#include <string>
#include <vector>
#include <algorithm>
#include <cmath>
#include <iostream>
using string=std::string;using ulong=unsigned long;using uint=unsigned int;using datetime=long;
bool MathIsValidNumber(double n){return std::isfinite(n);}
string IntegerToString(long n){return std::to_string(n);}
struct MqlTick{long time,time_msc;double bid,ask,last;ulong volume;double volume_real;uint flags;};
struct Reply{std::vector<MqlTick> rows;int n,error;};
std::vector<Reply> replies;int calls=0,last_error=0,exports=0;uint seen_mode=999;bool resize_fail=false;
string pilot_folder="test",query_audit="";std::vector<MqlTick> exported;
template<class...A>void Print(A...){ }
void ResetLastError(){last_error=0;}int GetLastError(){return last_error;}
template<class T>int ArraySize(const std::vector<T>&a){return a.size();}
template<class T>int ArrayResize(std::vector<T>&a,int n){if(resize_fail)return -1;a.resize(n);return n;}
int ArrayCopy(std::vector<MqlTick>&dst,const std::vector<MqlTick>&src){dst=src;return src.size();}
int CopyTicksRange(string,std::vector<MqlTick>&dst,uint mode,ulong,ulong){seen_mode=mode;auto r=replies.at(calls++);dst=r.rows;last_error=r.error;return r.n;}
string _Symbol="MDDP29_TEST";
string PHStats(const std::vector<MqlTick>&){return "stats";}string PHFlagHistogram(const std::vector<MqlTick>&){return "flags";}
bool PHExport(string,const std::vector<MqlTick>&a){exports++;exported=a;return true;}
'''+f+r'''
int count=0,fail=0;void check(bool b,const char*s){count++;if(!b){fail++;std::cout<<"FAIL "<<s<<"\n";}}
void reset(Reply a,Reply b){replies={a,b};calls=0;exports=0;exported.clear();query_audit="";resize_fail=false;}
int main(){
 MqlTick t{100,100001,10,15,10,1,1,56};std::vector<MqlTick> out;Reply a{{t,t},2,0};
 reset(a,a);check(QueryRead("TRADE",1,100000,101000,out),"valid equal replies stable");check(seen_mode==1,"mode forwarded");check(out.size()==2&&out[0].time_msc==out[1].time_msc,"repeated timestamp preserved");check(exports==1&&exported.size()==2,"snapshot exported");
 auto altered=a;altered.rows[1].flags=6;reset(a,altered);check(!QueryRead("ALL",0,100000,101000,out),"same count different flags not stable");
 reset({{},-1,4401},a);check(!QueryRead("ALL",0,100000,101000,out),"invalid first reply not stable");check(out.size()==2&&exports==1,"valid diagnostic final exported but marked unstable");
 reset(a,{{t},1,4403});check(!QueryRead("ALL",0,100000,101000,out),"partial error rejected");check(exports==0&&out.empty(),"invalid output not exported");
 reset(a,{{t},2,0});check(!QueryRead("ALL",0,100000,101000,out),"count array mismatch rejected");
 reset(a,a);resize_fail=true;check(!QueryRead("ALL",0,100000,101000,out),"destination allocation failure rejected");
 reset({{},0,0},{{},0,0});check(QueryRead("INFO",2,100000,101000,out),"two valid empty snapshots stable without source approval");check(out.empty(),"empty snapshot stays empty");
 std::cout<<"checks="<<count<<" failures="<<fail<<"\n";return fail?1:0;
}
'''
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp);(p/'test.cpp').write_text(cpp)
 r=subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',str(p/'test.cpp'),'-o',str(p/'test')],capture_output=True,text=True)
 if r.returncode:raise RuntimeError(r.stderr)
 r=subprocess.run([str(p/'test')],capture_output=True,text=True,env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1'))
 if r.returncode:raise RuntimeError(r.stdout+r.stderr)
 log=r.stdout.strip()
assert 'ZeroMemory(tick);' in source
for mode in ['COPY_TICKS_ALL','COPY_TICKS_TRADE','COPY_TICKS_INFO']:assert mode in source
for word in ['CustomTicksReplace(','CustomRatesUpdate(','OrderSend(']:assert word not in source
assert 'if(TimeCurrent()<D\'2026.10.29' in source
r={'checks':log,'scope':'Adapted QueryRead/PHSame C++ with simulated APIs; not native MetaEditor or MT5.','native_compile':'PENDING','source_sha256':hashlib.sha256(source.encode()).hexdigest(),'core_sha256':hashlib.sha256(core.encode()).hexdigest()}
(root/'tests/RESULTADO.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps(r,indent=2))
