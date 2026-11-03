"""Executa o fluxo do Script em C++ com APIs simuladas; nao compila MQL5."""
from pathlib import Path
import datetime
import re
import subprocess
import tempfile

root = Path(__file__).resolve().parent
source = root / "MQL5/Scripts/ModeloD_Pesquisa_Dados/Continuar_Preparacao_WINZ26.mq5"
text = source.read_text()
if re.search(r"\b(OrderSend|OrderSendAsync|CTrade|CustomSymbolCreate|CustomSymbolDelete|CustomSymbolSetString|CustomTicksReplace|CustomTicksAdd)\b", text):
    raise SystemExit("API fora do escopo da continuacao")
text = re.sub(r"^#property.*$", "", text, flags=re.M)
text = re.sub(r"D'([^']+)'", lambda m: str(int(datetime.datetime.strptime(m[1], "%Y.%m.%d %H:%M:%S").replace(tzinfo=datetime.timezone.utc).timestamp())) + "LL", text)
text = text.replace("MqlRates prior[];", "std::vector<MqlRates> prior;").replace("MqlRates check[];", "std::vector<MqlRates> check;")
prelude = r'''
#include <cmath>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
using string=std::string;using datetime=long long;
enum ENUM_SYMBOL_INFO_INTEGER{SYMBOL_CHART_MODE,SYMBOL_DIGITS,SYMBOL_TRADE_CALC_MODE};
enum ENUM_SYMBOL_INFO_DOUBLE{SYMBOL_TRADE_TICK_SIZE,SYMBOL_POINT,SYMBOL_TRADE_CONTRACT_SIZE};
enum ENUM_SYMBOL_INFO_STRING{SYMBOL_CURRENCY_PROFIT,SYMBOL_CURRENCY_MARGIN};
enum {MQL_TESTER,TERMINAL_BUILD,PERIOD_M1,FILE_WRITE=4,FILE_TXT=8,FILE_ANSI=16,FILE_COMMON=32,FILE_SHARE_READ=64,CP_UTF8=65001};
const int INVALID_HANDLE=-1;
struct MqlRates{datetime time=0;double open=0,high=0,low=0,close=0;long tick_volume=0,real_volume=0;int spread=0;};
string output;bool tester=false,exists=true,custom=true,source_custom=false,properties=true,property_api_ok=true;
bool collision=false,file_ok=true,select_ok=true,target_selected=false;int source_rows=565,readback_fault=0,source_fault=0,write_fault=0;
int api_error=0,writes=0,opens=0,closes=0,checks=0;std::vector<MqlRates> data,stored;
const string target="MD_PESQ_WINZ26_1030";
template<class...T>void Print(T...v){std::ostringstream s;(s<<...<<v);output+=s.str()+"\n";}
void check(bool ok,string why){checks++;if(!ok)throw std::runtime_error(why);}
string IntegerToString(long long v){return std::to_string(v);}
bool MathIsValidNumber(double v){return std::isfinite(v);}
template<class T>int ArraySize(const std::vector<T>&a){return (int)a.size();}
long MQLInfoInteger(int){return tester;}long TerminalInfoInteger(int){return 6295;}
bool SymbolExist(string s,bool &c){if(s==target){c=custom;return exists;}c=source_custom;return s=="WINZ26";}
bool SymbolSelect(string s,bool){if(s==target){target_selected=select_ok;return select_ok;}return s=="WINZ26";}
bool SymbolInfoInteger(string s,ENUM_SYMBOL_INFO_INTEGER,long &v){v=(s==target&&!properties)?2:1;return property_api_ok&&(s!=target||target_selected);}
bool SymbolInfoDouble(string s,ENUM_SYMBOL_INFO_DOUBLE,double &v){v=5;return property_api_ok&&(s!=target||target_selected);}
bool SymbolInfoString(string s,ENUM_SYMBOL_INFO_STRING,string &v){v="BRL";return property_api_ok&&(s!=target||target_selected);}
void ResetLastError(){api_error=0;}int GetLastError(){return api_error;}
unsigned long GetMicrosecondCount(){return 10;}unsigned long GetTickCount64(){return 20;}
bool FileIsExist(string,int){return collision;}int FileOpen(string,int,int,int){if(!file_ok)return INVALID_HANDLE;opens++;return 1;}
void FileWriteString(int,string){}void FileFlush(int){}void FileClose(int){closes++;}
int CopyRates(string s,int period,datetime from,datetime to,std::vector<MqlRates>&a){
 if(period!=PERIOD_M1||from!=1793232000LL||to!=1793318399LL)throw std::runtime_error("read outside prior day");
 if(s=="WINZ26"){
  a=data;if(source_rows<565)a.resize(source_rows);
  if(source_fault==1)a[1].time=a[0].time;
  if(source_fault==2)a[1].low=0;
  if(source_fault==3)a[1].high=std::nan("");
  if(source_fault==4){api_error=4403;}
  if(source_fault==5)a[1].time=1793318400LL;
  return (int)a.size();
 }
 if(s!=target)throw std::runtime_error("unknown read target");
 a=stored;
 if(readback_fault==1)a[0].close+=1;
 if(readback_fault==2)a[0].spread+=1;
 if(readback_fault==3)a.pop_back();
 if(readback_fault==4)api_error=4403;
 if(readback_fault==5)a[0].real_volume+=1;
 return (int)a.size();
}
int CustomRatesReplace(string s,datetime from,datetime to,const std::vector<MqlRates>&a){
 if(s!=target||from!=1793232000LL||to!=1793318399LL)throw std::runtime_error("write escaped research/prior day");
 writes++;stored=a;
 if(write_fault==1)return (int)a.size()-1;
 if(write_fault==2)api_error=4403;
 return (int)a.size();
}
'''
main = r'''
void reset(){
 tester=false;exists=true;custom=true;source_custom=false;properties=true;property_api_ok=true;
 collision=false;file_ok=true;select_ok=true;target_selected=false;source_rows=565;source_fault=0;readback_fault=0;write_fault=0;
 api_error=0;writes=0;opens=0;closes=0;output.clear();stored.clear();md_research_file=INVALID_HANDLE;
}
bool ready(){return output.find("READY_FOR_MANUAL_TICK_IMPORT;")!=string::npos;}
void refused_without_write(){OnStart();check(writes==0&&!ready(),"unsafe write or false READY");check(opens==closes,"file leaked on refusal");}
int main(){try{
 for(int i=0;i<565;i++)data.push_back({1793264400LL+i*60,170910,171600,170900,171330,18948,78471,5});
 reset();tester=true;refused_without_write();
 reset();exists=false;refused_without_write();
 reset();custom=false;refused_without_write();
 reset();source_custom=true;refused_without_write();
 reset();properties=false;refused_without_write();
 reset();property_api_ok=false;refused_without_write();
 reset();source_rows=499;refused_without_write();
 for(int f=1;f<=5;f++){reset();source_fault=f;refused_without_write();}
 reset();collision=true;refused_without_write();
 reset();file_ok=false;refused_without_write();
 for(int f=1;f<=2;f++){reset();write_fault=f;OnStart();check(writes==1&&!ready()&&opens==closes,"copy failure hidden");}
 for(int f=1;f<=5;f++){reset();readback_fault=f;OnStart();check(writes==1&&!ready()&&opens==closes,"readback failure hidden");}
 reset();select_ok=false;refused_without_write();
 reset();OnStart();check(writes==1&&ready()&&stored.size()==565&&opens==closes,"valid continuation refused");
 check(output.find("PRIOR_READBACK;rows=565;same=1;error=0")!=string::npos,"readback success missing");
 std::cout<<"HOST_CONTINUACAO;Checks="<<checks<<";Failures=0;CPP_SIMULADO;NAO_E_COMPILACAO_MQL5\n";
 return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 1;}}
'''
with tempfile.TemporaryDirectory(prefix="md_continuacao_") as tmp:
    folder = Path(tmp)
    (folder / "host.cpp").write_text(prelude + text + main)
    subprocess.run(["g++", "-std=c++17", "-O1", "-g", "-fsanitize=address,undefined", "-fno-omit-frame-pointer", str(folder / "host.cpp"), "-o", str(folder / "host")], check=True)
    subprocess.run([str(folder / "host")], check=True)
