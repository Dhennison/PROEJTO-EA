"""Exercita o fonte do diagnóstico em host C++ com APIs simuladas.
Não compila MQL5, não reproduz o motor do Tester nem certifica o histórico.
"""
from pathlib import Path
import datetime
import re
import subprocess
import tempfile

root = Path(__file__).resolve().parent
source = root / "MQL5/Experts/ModeloD_Diagnostico_Agente/Diagnostico_Dados_WINZ26.mq5"
text = source.read_text()
if re.search(r"\b(OrderSend|OrderSendAsync|CTrade|FileDelete|FileMove)\b", text):
    raise SystemExit("API de negociação ou mutação de arquivos encontrada")
text = re.sub(r"^#property.*$", "", text, flags=re.M)
def date_literal(match):
    stamp = datetime.datetime.strptime(match[1], "%Y.%m.%d %H:%M:%S")
    return str(int(stamp.replace(tzinfo=datetime.timezone.utc).timestamp())) + "LL"
text = re.sub(r"D'([^']+)'", date_literal, text)
text = text.replace("MqlTick ticks[];", "std::vector<MqlTick> ticks;")
text = text.replace("MqlRates bars[];", "std::vector<MqlRates> bars;")
prelude = r'''
#include <algorithm>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
using string=std::string; using datetime=long long;
enum ENUM_SYMBOL_INFO_INTEGER { SYMBOL_CHART_MODE, SYMBOL_TRADE_CALC_MODE, SYMBOL_DIGITS };
enum ENUM_SYMBOL_INFO_DOUBLE { SYMBOL_TRADE_TICK_SIZE, SYMBOL_TRADE_TICK_VALUE, SYMBOL_POINT };
enum { MQL_TESTER=1,MQL_OPTIMIZATION,MQL_VISUAL_MODE,ACCOUNT_CURRENCY,ACCOUNT_MARGIN_MODE,
 TERMINAL_BUILD,SYMBOL_CURRENCY_PROFIT,SYMBOL_CURRENCY_MARGIN };
const int SYMBOL_CHART_MODE_BID=0,SYMBOL_CHART_MODE_LAST=1;
const int FILE_WRITE=1,FILE_TXT=2,FILE_ANSI=4,FILE_COMMON=8,FILE_SHARE_READ=16,CP_UTF8=65001;
const int INVALID_HANDLE=-1,INIT_SUCCEEDED=0,INIT_PARAMETERS_INCORRECT=2,INIT_FAILED=1;
const int TIME_DATE=1,TIME_SECONDS=2,PERIOD_M1=1;
const unsigned int COPY_TICKS_ALL=0,COPY_TICKS_TRADE=1;
const unsigned int TICK_FLAG_LAST=8,TICK_FLAG_VOLUME=16,TICK_FLAG_BUY=32,TICK_FLAG_SELL=64;
struct MqlTick{datetime time=0;double bid=0,ask=0,last=0;unsigned long volume=0;
 long time_msc=0;unsigned int flags=0;double volume_real=0;};
struct MqlRates{datetime time=0;double open=0,high=0,low=0,close=0;
 long tick_volume=0,real_volume=0;};
string _Symbol="WINZ26";bool tester=true,optimization=false,timer_ok=true,empty_trade=false;
bool partial_error=false;int api_error=0,removed=0,queries=0,checks=0;
datetime simulated=1793318400LL;string output;std::vector<MqlTick> fixture;
template<class...T>void Print(T...v){std::ostringstream s;(s<<...<<v);output+=s.str()+"\n";}
string IntegerToString(long long v){return std::to_string(v);}
string DoubleToString(double v,int n){std::ostringstream s;s<<std::fixed<<std::setprecision(n)<<v;return s.str();}
string TimeToString(datetime t,int){return std::to_string(t);}
bool MathIsValidNumber(double x){return std::isfinite(x);}
double MathMax(double a,double b){return std::max(a,b);}
double MathMin(double a,double b){return std::min(a,b);}
template<class T>int ArraySize(const std::vector<T>&a){return (int)a.size();}
long MQLInfoInteger(int p){if(p==MQL_TESTER)return tester;if(p==MQL_OPTIMIZATION)return optimization;return 1;}
long AccountInfoInteger(int){return 2;}long TerminalInfoInteger(int){return 6231;}
string AccountInfoString(int){return "USD";}string SymbolInfoString(string,int){return "BRL";}
bool SymbolInfoInteger(string,ENUM_SYMBOL_INFO_INTEGER p,long &v){v=p==SYMBOL_CHART_MODE?1:0;return true;}
bool SymbolInfoDouble(string,ENUM_SYMBOL_INFO_DOUBLE p,double &v){v=p==SYMBOL_TRADE_TICK_SIZE?5:1;return true;}
void ResetLastError(){api_error=0;}int GetLastError(){return api_error;}
datetime TimeCurrent(){return simulated;}datetime TimeTradeServer(){return simulated;}datetime TimeGMT(){return simulated;}
unsigned long GetMicrosecondCount(){return 100;}unsigned long GetTickCount64(){return 200;}
bool FileIsExist(string,int){return false;}int FileOpen(string,int,int,int){return 1;}
void FileWriteString(int,string){}void FileFlush(int){}void FileClose(int){}
bool EventSetTimer(int){return timer_ok;}void EventKillTimer(){}void ExpertRemove(){removed++;}
bool SymbolInfoTick(string,MqlTick&t){if(fixture.empty())return false;t=fixture.back();return true;}
int CopyRates(string,int,datetime,datetime,std::vector<MqlRates>&a){
 a={{1793350800LL,170910,171600,170900,171330,18948,78471}};return 1;}
int CopyTicksRange(string,std::vector<MqlTick>&a,unsigned int flags,unsigned long begin,unsigned long end){
 queries++;a.clear();if(flags==COPY_TICKS_TRADE&&empty_trade)return 0;
 for(auto t:fixture)if((unsigned long)t.time_msc>=begin&&(unsigned long)t.time_msc<=end&&
 (flags==COPY_TICKS_ALL||(t.flags&120)))a.push_back(t);
 if(partial_error)api_error=4403;return (int)a.size();}
void check(bool ok,string label){checks++;if(!ok)throw std::runtime_error(label);}
'''
main = r'''
int main(int argc,char**argv){try{
 if(argc!=2)return 2;std::ifstream f(argv[1]);check((bool)f,"input missing");
 string line;std::getline(f,line);
 while(std::getline(f,line)){
  if(!line.empty()&&line.back()=='\r')line.pop_back();
  std::istringstream row(line);std::vector<string> c;string field;
  while(std::getline(row,field,'\t'))c.push_back(field);
  if(c.size()!=7)throw std::runtime_error("invalid CSV");
  MqlTick t;int h=std::stoi(c[1].substr(0,2)),m=std::stoi(c[1].substr(3,2));
  int s=std::stoi(c[1].substr(6,2)),ms=std::stoi(c[1].substr(9,3));
  t.time=1793318400LL+h*3600+m*60+s;t.time_msc=(long)t.time*1000+ms;
  if(!c[2].empty())t.bid=std::stod(c[2]);if(!c[3].empty())t.ask=std::stod(c[3]);
  if(!c[4].empty())t.last=std::stod(c[4]);if(!c[5].empty())t.volume_real=std::stod(c[5]);
  t.volume=(unsigned long)t.volume_real;t.flags=(unsigned int)std::stoul(c[6]);fixture.push_back(t);
 }
 tester=false;check(OnInit()==INIT_PARAMETERS_INCORRECT,"terminal allowed");tester=true;
 optimization=true;check(OnInit()==INIT_PARAMETERS_INCORRECT,"optimization allowed");optimization=false;
 _Symbol="WIN$N";check(OnInit()==INIT_PARAMETERS_INCORRECT,"wrong symbol allowed");_Symbol="WINZ26";
 simulated=1793404800LL;check(OnInit()==INIT_PARAMETERS_INCORRECT,"wrong day allowed");simulated=1793318400LL;
 check(OnInit()==INIT_SUCCEEDED,"valid init refused");
 simulated=1793350919LL;OnTimer();check(queries==0&&removed==0,"queried before minute closed");
 simulated=1793350920LL;output.clear();OnTimer();
 check(queries==2&&removed==1&&diag_done,"probe did not stop");
 check(output.find("mode=ALL;from=1793350800000;to=1793350859999;returned=21566")!=string::npos,"ALL interval wrong");
 check(output.find("mode=TRADE;from=1793350800000;to=1793350859999;returned=10528")!=string::npos,"TRADE interval wrong");
 check(output.find("open=170910.00000000;high=171600.00000000;low=170900.00000000;close=171330.00000000;sum_volume=78471.00000000;sum_volume_real=78471.00000000")!=string::npos,"OHLC/volume differs from real CSV");
 check(output.find("flags_zero=7")!=string::npos,"zero flags not preserved");
 OnTimer();check(queries==2&&removed==1,"probe repeated");
 empty_trade=true;output.clear();DiagQuery("TRADE",COPY_TICKS_TRADE);
 check(output.find("returned=0;array=0;error=0")!=string::npos,"empty query hidden");
 empty_trade=false;partial_error=true;output.clear();DiagQuery("TRADE",COPY_TICKS_TRADE);
 check(output.find("error=4403")!=string::npos,"API error hidden");
 check(output.find("complete_without_api_error=0")!=string::npos,"partial timeout certified");
 partial_error=false;OnDeinit(1);check(diag_file==INVALID_HANDLE,"file not closed");
 std::cout<<"HOST_DIAGNOSTICO;Checks="<<checks<<";Failures=0;CPP_SIMULADO;NAO_E_COMPILACAO_MQL5\n";
 return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 1;}}
'''
csv_path = root.parent / "validacao_20261102_ensaio1/WINZ26_202610300900_202610300901.csv"
with tempfile.TemporaryDirectory(prefix="md_diag_host_") as tmp:
    folder = Path(tmp)
    (folder / "host.cpp").write_text(prelude + text + main)
    subprocess.run(["g++", "-std=c++17", "-O1", "-g", "-fsanitize=address,undefined",
                    "-fno-omit-frame-pointer", str(folder / "host.cpp"),
                    "-o", str(folder / "host")], check=True)
    subprocess.run([str(folder / "host"), str(csv_path)], check=True)
