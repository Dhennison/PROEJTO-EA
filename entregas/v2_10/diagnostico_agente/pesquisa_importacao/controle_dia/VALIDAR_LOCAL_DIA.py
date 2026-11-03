"""Executa os dois novos fontes em host C++/APIs simuladas e CSV real completo.

Nao compila MQL5 nem executa importador/Tester. Sanitizadores ficam ativos.
"""
from pathlib import Path
import ast
import datetime
import re
import shutil
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parent
PREPARE = ROOT / "MQL5/Scripts/ModeloD_Pesquisa_Dados/Preparar_Pesquisa_Dia_WINZ26.mq5"
EXPERT = ROOT / "MQL5/Experts/ModeloD_Diagnostico_Pesquisa/Diagnostico_Dia_Importado_WINZ26.mq5"


def translate(path):
    text = path.read_text()
    if re.search(r"\b(OrderSend|OrderSendAsync|CTrade|CustomSymbolDelete|CustomSymbolSetString)\b", text):
        raise ValueError("API outside control scope")
    text = re.sub(r"^#property.*$", "", text, flags=re.M)
    text = re.sub(r"D'([^']+)'", lambda m: str(int(datetime.datetime.strptime(m[1], "%Y.%m.%d %H:%M:%S").replace(tzinfo=datetime.timezone.utc).timestamp())) + "LL", text)
    for typ, var in (("MqlRates", "prior"), ("MqlRates", "check"), ("MqlRates", "bars"), ("MqlTick", "ticks")):
        text = text.replace(typ + " " + var + "[];", "std::vector<" + typ + "> " + var + ";")
    return text


def build_run(folder, name, source, args=()):
    code = folder / (name + ".cpp")
    binary = folder / name
    code.write_text(source)
    subprocess.run(["g++", "-std=c++17", "-O1", "-g", "-fsanitize=address,undefined",
                    "-fno-omit-frame-pointer", str(code), "-o", str(binary)], check=True)
    subprocess.run([str(binary), *map(str, args)], check=True)


EXPERT_PRELUDE = r'''
#include <algorithm>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
using string=std::string;using datetime=long long;
enum ENUM_SYMBOL_INFO_INTEGER{SYMBOL_CUSTOM};
enum{MQL_TESTER,MQL_OPTIMIZATION,MQL_VISUAL_MODE,TERMINAL_BUILD,ACCOUNT_MARGIN_MODE,PERIOD_M1};
const int FILE_WRITE=1,FILE_TXT=2,FILE_ANSI=4,FILE_COMMON=8,FILE_SHARE_READ=16,CP_UTF8=65001;
const int INVALID_HANDLE=-1,INIT_SUCCEEDED=0,INIT_PARAMETERS_INCORRECT=2,INIT_FAILED=1,TIME_DATE=1,TIME_SECONDS=2;
const uint COPY_TICKS_ALL=0,COPY_TICKS_TRADE=1,TICK_FLAG_BID=2,TICK_FLAG_ASK=4,TICK_FLAG_LAST=8,TICK_FLAG_VOLUME=16,TICK_FLAG_BUY=32,TICK_FLAG_SELL=64;
struct MqlTick{datetime time=0;double bid=0,ask=0,last=0;ulong volume=0;long time_msc=0;uint flags=0;double volume_real=0;};
struct MqlRates{datetime time=0;double open=0,high=0,low=0,close=0;long tick_volume=0,real_volume=0;};
bool tester=true,optimization=false,is_custom=true,collision=false,file_ok=true;
int api_error=0,checks=0,queries=0,opened=0,closed=0;
datetime simulated=1793318400LL;string _Symbol="MD_PESQ_WINZ26_DIA1030",output,fault;
std::vector<MqlTick> fixture;std::vector<MqlRates> derived,published;
template<class...T>void Print(T...v){std::ostringstream s;(s<<...<<v);output+=s.str()+"\n";}
string IntegerToString(long long v){return std::to_string(v);}
string DoubleToString(double v,int n){std::ostringstream s;s<<std::fixed<<std::setprecision(n)<<v;return s.str();}
string TimeToString(datetime v,int){return std::to_string(v);}
bool MathIsValidNumber(double v){return std::isfinite(v);}
double MathMax(double a,double b){return std::max(a,b);}double MathMin(double a,double b){return std::min(a,b);}
template<class T>void ZeroMemory(T &v){v=T{};}
template<class T>int ArraySize(const std::vector<T>&v){return (int)v.size();}
template<class T>void ArrayFree(std::vector<T>&v){std::vector<T>().swap(v);}
long MQLInfoInteger(int p){return p==MQL_TESTER?tester:p==MQL_OPTIMIZATION?optimization:0;}
long TerminalInfoInteger(int){return 6295;}long AccountInfoInteger(int){return 2;}
bool SymbolInfoInteger(string,ENUM_SYMBOL_INFO_INTEGER,long &v){v=is_custom;return true;}
void ResetLastError(){api_error=0;}int GetLastError(){return api_error;}
datetime TimeCurrent(){return simulated;}ulong GetMicrosecondCount(){return 10;}ulong GetTickCount64(){return 20;}
bool FileIsExist(string,int){return collision;}int FileOpen(string,int,int,int){if(!file_ok)return INVALID_HANDLE;opened++;return 1;}
void FileWriteString(int,string){}void FileFlush(int){}void FileClose(int){closed++;}
bool SymbolInfoTick(string,MqlTick &v){v=fixture.back();if(fault=="early")v.time_msc--;return true;}
int CopyTicksRange(string symbol,std::vector<MqlTick>&a,uint mode,ulong from,ulong to){
 if(symbol!="MD_PESQ_WINZ26_DIA1030"||from!=1793318400000UL||to!=1793385084719UL)throw std::runtime_error("query escaped fixed scope");
 queries++;a.clear();a.reserve(mode==COPY_TICKS_ALL?fixture.size():3190938);
 for(const auto&t:fixture)if(mode==COPY_TICKS_ALL||(t.flags&120))a.push_back(t);
 if(fault=="reorder")std::swap(a[0],a[1]);
 if(fault=="quote_missing"&&mode==COPY_TICKS_ALL){auto it=std::find_if(a.begin(),a.end(),[](const auto&t){return !(t.flags&120);});a.erase(it);}
 if(fault=="volume_field")a[0].volume++;
 if(fault=="api_timeout")api_error=4403;
 if(fault=="outside"){auto t=fixture.back();t.time_msc++;a.push_back(t);}
 return (int)a.size();
}
int CopyRates(string symbol,int period,datetime from,datetime to,std::vector<MqlRates>&a){
 if(symbol!="MD_PESQ_WINZ26_DIA1030"||period!=PERIOD_M1||from!=1793318400LL||to!=1793385084LL)throw std::runtime_error("M1 escaped fixed scope");
 a=fault=="published_m1"?published:derived;return (int)a.size();
}
void check(bool ok,string why){checks++;if(!ok)throw std::runtime_error(why);}
'''

EXPERT_MAIN = r'''
void reset(){
 tester=true;optimization=false;is_custom=true;collision=false;file_ok=true;
 simulated=1793318400LL;_Symbol="MD_PESQ_WINZ26_DIA1030";fault.clear();output.clear();api_error=0;
 md_file=INVALID_HANDLE;md_done=false;md_observed=0;md_last_observed=-1;queries=opened=closed=0;
}
bool complete(){return output.find(";control_complete=1")!=string::npos;}
void run(){check(OnInit()==INIT_SUCCEEDED,"valid init failed");OnTick();OnTester();OnDeinit(0);check(queries==2&&opened==closed,"audit repeated or file leaked");}
std::vector<string> split(string line){if(!line.empty()&&line.back()=='\r')line.pop_back();std::vector<string> c;std::istringstream s(line);string v;while(std::getline(s,v,'\t'))c.push_back(v);return c;}
int main(int argc,char**argv){try{
 if(argc!=3)return 2;std::ifstream ticks(argv[1]);check((bool)ticks,"CSV missing");string line;std::getline(ticks,line);
 fixture.reserve(4319271);MqlTick state;long zeros=0,source_rows=0;std::map<datetime,MqlRates> cache;
 while(std::getline(ticks,line)){
  auto c=split(line);if(c.size()!=7)throw std::runtime_error("bad tick row");source_rows++;
  uint flags=(uint)std::stoul(c[6]);if(!flags){zeros++;continue;}
  long msc=1793318400000L+std::stol(c[1].substr(0,2))*3600000+std::stol(c[1].substr(3,2))*60000+std::stol(c[1].substr(6,2))*1000+std::stol(c[1].substr(9,3));
  if(flags&2)state.bid=std::stod(c[2]);if(flags&4)state.ask=std::stod(c[3]);if(flags&8)state.last=std::stod(c[4]);
  if(flags&16){state.volume_real=std::stod(c[5]);state.volume=(ulong)state.volume_real;}
  state.time_msc=msc;state.time=msc/1000;state.flags=flags;fixture.push_back(state);
  if(flags&120){datetime minute=state.time/60*60;auto &b=cache[minute];if(!b.tick_volume){b.time=minute;b.open=b.high=b.low=state.last;}
   b.tick_volume++;b.real_volume+=(long)state.volume_real;b.close=state.last;b.high=std::max(b.high,state.last);b.low=std::min(b.low,state.last);}
 }
 check(source_rows==4319285&&zeros==14&&fixture.size()==4319271,"unexpected fixture size");
 for(auto &item:cache)derived.push_back(item.second);check(derived.size()==566,"wrong derived minute count");
 std::ifstream bars(argv[2]);check((bool)bars,"M1 missing");std::getline(bars,line);
 while(std::getline(bars,line)){auto c=split(line);if(c.size()!=9)throw std::runtime_error("bad M1 row");
  datetime t=1793318400LL+std::stol(c[1].substr(0,2))*3600+std::stol(c[1].substr(3,2))*60;
  published.push_back({t,std::stod(c[2]),std::stod(c[3]),std::stod(c[4]),std::stod(c[5]),std::stol(c[6]),std::stol(c[7])});}
 reset();tester=false;check(OnInit()==INIT_PARAMETERS_INCORRECT,"terminal accepted");
 reset();optimization=true;check(OnInit()==INIT_PARAMETERS_INCORRECT,"optimization accepted");
 reset();_Symbol="WINZ26";check(OnInit()==INIT_PARAMETERS_INCORRECT,"real symbol accepted");
 reset();is_custom=false;check(OnInit()==INIT_PARAMETERS_INCORRECT,"noncustom accepted");
 reset();simulated=1793404800LL;check(OnInit()==INIT_PARAMETERS_INCORRECT,"wrong day accepted");
 reset();collision=true;check(OnInit()==INIT_FAILED,"report collision accepted");
 reset();file_ok=false;check(OnInit()==INIT_FAILED,"missing report accepted");
 reset();check(OnInit()==INIT_SUCCEEDED,"cancel init failed");OnDeinit(1);
 check(queries==0&&!md_done&&opened==closed&&output.find("AUDIT_NOT_RUN;")!=string::npos,"cancel started large audit or hid missing result");
 reset();run();check(complete(),"unaltered canonical source failed");
 check(output.find("canonical_all_match=1;canonical_trade_match=1;m1_matches_native_trades=1")!=string::npos,"source fingerprints differ");
 for(string f:{"reorder","quote_missing","volume_field","api_timeout","outside","early","published_m1"}){
  reset();fault=f;run();check(!complete(),"fault accepted: "+f);
  if(f=="quote_missing")check(output.find("canonical_trade_match=1")!=string::npos,"quote control invalidated trades");
  if(f=="early")check(output.find("canonical_all_match=1")!=string::npos,"early replay did not isolate end guard");
  if(f=="published_m1")check(output.find("canonical_all_match=1;canonical_trade_match=1;m1_matches_native_trades=0")!=string::npos,"M1 divergence not isolated");
 }
 std::cout<<"HOST_DIA;Checks="<<checks<<";Failures=0;SOURCE_ROWS="<<source_rows<<";CPP_SIMULADO;NAO_E_COMPILACAO_MQL5\n";
 return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 1;}}
'''


def prepare_harness():
    tree = ast.parse((ROOT.parent / "VALIDAR_CONTINUACAO.py").read_text())
    prelude = next(ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign)
                   and any(isinstance(target, ast.Name) and target.id == "prelude" for target in node.targets))
    prelude = prelude.replace('"MD_PESQ_WINZ26_1030"', '"MD_PESQ_WINZ26_DIA1030"')
    extra = r'''
int creates=0;bool create_ok=true;
bool CustomSymbolCreate(string s,string group,string origin){
 if(s!=target||group!="ModeloD_Pesquisa_Dia"||origin!="WINZ26"||exists)throw std::runtime_error("creation escaped scope");
 creates++;if(!create_ok)return false;exists=true;custom=true;return true;
}
'''
    main = r'''
void reset(){tester=false;exists=false;custom=false;source_custom=false;properties=true;property_api_ok=true;
 collision=false;file_ok=true;select_ok=true;target_selected=false;source_rows=565;source_fault=readback_fault=write_fault=0;
 creates=writes=opens=closes=api_error=0;create_ok=true;output.clear();stored.clear();md_research_file=INVALID_HANDLE;}
bool ready(){return output.find("READY_FOR_MANUAL_TICK_IMPORT;")!=string::npos;}
void no_create(){OnStart();check(creates==0&&writes==0&&!ready()&&opens==closes,"unsafe preparation");}
int main(){try{
 for(int i=0;i<565;i++)data.push_back({1793264400LL+i*60,170910,171600,170900,171330,18948,78471,5});
 reset();tester=true;no_create();reset();exists=true;no_create();reset();source_custom=true;no_create();
 reset();source_rows=499;no_create();for(int i=1;i<=5;i++){reset();source_fault=i;no_create();}
 reset();collision=true;no_create();reset();file_ok=false;no_create();
 reset();create_ok=false;OnStart();check(creates==1&&writes==0&&!ready()&&opens==closes,"create failure hidden");
 for(int i=1;i<=2;i++){reset();write_fault=i;OnStart();check(creates==1&&writes==1&&!ready()&&opens==closes,"write failure hidden");}
 for(int i=1;i<=5;i++){reset();readback_fault=i;OnStart();check(creates==1&&writes==1&&!ready()&&opens==closes,"readback failure hidden");}
 reset();select_ok=false;OnStart();check(creates==1&&writes==1&&!ready()&&opens==closes,"selection failure hidden");
 reset();OnStart();check(creates==1&&writes==1&&ready()&&stored.size()==565&&opens==closes,"valid creation failed");
 std::cout<<"HOST_PREPARAR_DIA;Checks="<<checks<<";Failures=0;CPP_SIMULADO;NAO_E_COMPILACAO_MQL5\n";return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 1;}}
'''
    return prelude + extra + translate(PREPARE) + main


def main():
    with tempfile.TemporaryDirectory(prefix="modelod_dia_host_") as tmp:
        folder = Path(tmp)
        build_run(folder, "prepare", prepare_harness())
        fixture = folder / "dia.csv"
        with zipfile.ZipFile(ROOT.parent / "coleta_dia_20261103/WINZ26_20261030_DIA_COMPLETO.zip") as archive:
            with archive.open("WINZ26_20261030_DIA_COMPLETO.csv") as source, fixture.open("wb") as destination:
                shutil.copyfileobj(source, destination)
        build_run(folder, "expert", EXPERT_PRELUDE + translate(EXPERT) + EXPERT_MAIN,
                  (fixture, ROOT.parent / "m1_atual_20261103/WINZ26_M1_20261030_SECUNDARIO_ATUAL.csv"))


if __name__ == "__main__":
    main()
