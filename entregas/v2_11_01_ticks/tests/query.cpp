// Actual adapter and opening acquisition bodies; simulated MT5 API, not native MQL5.
#include <string>
#include <vector>
#include <cmath>
#include <iostream>
#include <cassert>
using string=std::string;using ulong=unsigned long;using uint=unsigned int;
struct MqlTick {long time_msc;double last;uint flags;double bid=100,ask=105;};
const uint COPY_TICKS_TRADE=1,COPY_TICKS_ALL=0,COPY_TICKS_INFO=2;
const int TICK_FLAG_LAST=8,TICK_FLAG_VOLUME=16,TICK_FLAG_BUY=32,TICK_FLAG_SELL=64;
bool tester=true,ExecutarNoTester=true,UsarFonteImportadaNoTester=false,stopped=false;
int last_error=0,trade_error=0,all_error=0,trade_calls=0,all_calls=0;
long mono=100;std::vector<MqlTick> reply_trade,reply_all;std::vector<string> logs;
bool MDIsTester210(){return tester;}bool IsStopped(){return stopped;}
ulong GetTickCount64(){return mono;}void ResetLastError(){last_error=0;}int GetLastError(){return last_error;}
string IntegerToString(long n){return std::to_string(n);}string DoubleToString(double x,int){return std::to_string(x);}
bool MathIsValidNumber(double x){return std::isfinite(x);}void Print(string){}
void Report615(string s){logs.push_back(s);}
template<class T>int ArraySize(const std::vector<T>&v){return v.size();}
template<class T>int ArrayResize(std::vector<T>&v,int n){v.resize(n);return n;}
int CopyTicksRange(string,std::vector<MqlTick>&v,uint flags,ulong,ulong){
 if(flags==COPY_TICKS_ALL){all_calls++;v=reply_all;last_error=all_error;}
 else{trade_calls++;v=reply_trade;last_error=trade_error;}
 return v.size();
}
#include "query_adapted.mqh"
int MDCopyTicksRange211(string s,std::vector<MqlTick>&v,uint f,ulong a,ulong b){return MDConsultaNativa21101(s,v,f,a,b);}
#include "opening_adapted.mqh"
int checks=0;void check(bool ok,const char*name){if(!ok){std::cerr<<"FAIL "<<name<<'\n';std::exit(1);}checks++;std::cout<<"PASS "<<name<<'\n';}
int main(){
 std::vector<MqlTick> out;long begin=100000,end=begin+180000;string why;long first=-1;double price=-1;
 auto read=[&](){return MDOpeningRead208("WINZ26",begin,end,end+1,first,price,why);};
 reply_all={{begin+1,999,2},{begin+2,100,8},{begin+2,100,32},{begin+3,105,16}};
 int n=MDConsultaNativa21101("WINZ26",out,COPY_TICKS_TRADE,begin,begin+59999);
 check(n==3&&out[0].time_msc==begin+2&&out[1].time_msc==begin+2,"ALL skips quote-only prefix and preserves duplicate order");
 check(logs[0].find("TRADE_n=0;TRADE_erro=0;ALL_n=4")!=string::npos,"paired diagnostic records actual query counts");
 check(read()&&first==begin+2&&price==100,"actual opening reader accepts first flagged trade despite empty TRADE");
 begin+=1000000;end=begin+180000;reply_all={{begin+1,100,2}};mono+=10000;
 check(!read()&&!opening208.confirmed&&opening208.cursor==begin+60000,"quote-only carried Last never creates opening");
 begin+=1000000;end=begin+180000;reply_all={{begin+1,100,8}};all_error=4403;mono+=10000;
 check(!read()&&!opening208.confirmed&&opening208.cursor==begin,"partial timeout cannot advance opening cursor");
 all_error=0;mono=opening208.next_due;
 check(read()&&price==100,"retry of same window succeeds after complete ALL result");
 reply_all={{begin-1,100,8}};
 check(MDConsultaNativa21101("WINZ26",out,COPY_TICKS_TRADE,begin,end)==-1,"out-of-window ALL rejected");
 reply_all={{begin+2,100,8},{begin+1,105,8}};
 check(MDConsultaNativa21101("WINZ26",out,COPY_TICKS_TRADE,begin,end)==-1,"unordered ALL rejected without sorting");
 reply_all={{begin+1,0,8}};
 check(MDConsultaNativa21101("WINZ26",out,COPY_TICKS_TRADE,begin,end)==-1,"flagged zero Last rejected");
 reply_all={{begin+1,NAN,8}};
 check(MDConsultaNativa21101("WINZ26",out,COPY_TICKS_TRADE,begin,end)==-1,"flagged NaN Last rejected");
 reply_all.clear();
 check(MDConsultaNativa21101("WINZ26",out,COPY_TICKS_TRADE,begin,end)==0&&out.empty(),"complete empty ALL remains empty");
 UsarConsultaAllFiltradaNoTester=false;reply_trade={{begin+4,110,64}};all_error=4403;
 check(MDConsultaNativa21101("WINZ26",out,COPY_TICKS_TRADE,begin,end)==1&&out[0].last==110&&GetLastError()==0,"TRADE baseline unaffected by auxiliary ALL error");
 trade_error=4403;all_error=0;reply_all={{begin+1,100,8}};
 check(MDConsultaNativa21101("WINZ26",out,COPY_TICKS_TRADE,begin,end)==-1,"baseline preserves TRADE timeout rejection");
 UsarConsultaAllFiltradaNoTester=true;
 check(MDConsultaNativa21101("WINZ26",out,COPY_TICKS_TRADE,begin,end)==1,"selected ALL can succeed independently of TRADE timeout");
 trade_error=0;md_comparacoes21101=32;int calls=trade_calls;size_t lines=logs.size();
 check(MDConsultaNativa21101("WINZ26",out,COPY_TICKS_TRADE,begin,end)==1&&trade_calls==calls&&logs.size()==lines,"comparisons stop at bounded limit while ALL continues");
 tester=false;calls=all_calls;
 check(MDConsultaNativa21101("WINZ26",out,COPY_TICKS_TRADE,begin,end)==1&&all_calls==calls&&out[0].last==110,"outside Tester forwards original query unchanged");
 tester=true;UsarFonteImportadaNoTester=true;calls=all_calls;
 check(MDConsultaNativa21101("WINZ26",out,COPY_TICKS_TRADE,begin,end)==1&&all_calls==calls,"imported path excluded from experiment");
 UsarFonteImportadaNoTester=false;calls=all_calls;
 check(MDConsultaNativa21101("WINZ26",out,COPY_TICKS_INFO,begin,end)==1&&all_calls==calls,"non-TRADE queries unchanged");
 std::cout<<"CHECKS="<<checks<<";FAILURES=0;SIMULATED_API\n";
}
