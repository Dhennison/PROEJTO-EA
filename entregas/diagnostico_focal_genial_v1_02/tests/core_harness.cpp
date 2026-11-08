#include <vector>
#include <string>
#include <cmath>
#include <iostream>
#include <sstream>
#include <iomanip>
#include <limits>
using string=std::string;using datetime=long;
struct MqlTick {long time=60000,time_msc=60000001;double bid=100,ask=105,last=100;unsigned long volume=1;double volume_real=1;unsigned int flags=56;};
struct MqlRates {long time=60000;double open=100,high=110,low=100,close=110;long tick_volume=2,real_volume=2;int spread=5;};
template<class T>int ArraySize(const std::vector<T>& v){return static_cast<int>(v.size());}
bool MathIsValidNumber(double value){return std::isfinite(value);}
int StringLen(const string& s){return static_cast<int>(s.size());}
string StringSubstr(const string& s,int pos,int length){return s.substr(pos,length);}
#include "focal_generated.hpp"
string IntegerToString(int n){return std::to_string(n);}string FInt(long n){return std::to_string(n);}
string FTime(long n){return std::to_string(n);}string FPrice(double n){std::ostringstream s;s<<std::scientific<<std::setprecision(16)<<n;return s.str();}
const int INVALID_HANDLE=-1;
std::vector<MqlTick> g_all,g_trade;std::vector<MqlRates> g_m1;datetime g_from[2]={60000,70000},g_to[2]={60120,70120};int g_window=0;
std::vector<string> writes;int closed_files=0,fail_at=-1;
int FOpen(const string&){return 1;}
bool FWrite(int,const string& s){if(static_cast<int>(writes.size())==fail_at)return false;writes.push_back(s);return true;}
bool FClose(int){closed_files++;return true;}
#include "format_generated.hpp"
int checks=0,failures=0;
void check(bool ok,const char*name){checks++;if(!ok)failures++;std::cout<<(ok?"PASS ":"FAIL ")<<name<<'\n';}
int columns(const string& s){int n=1;for(char c:s)if(c==';')n++;return n;}
int main(){
 const long lo=60000000,hi=60060000;MqlTick a,b,q;b.last=110;b.time_msc=a.time_msc;q.last=999;q.flags=6;
 FMinute m;FMinuteStats({a,b,q},lo,hi,m);
 check(m.total==3 && m.business==2,"carried Last excluded from business OHLC");
 check(m.o==100 && m.h==110 && m.l==100 && m.c==110,"OHLC and same millisecond sequence preserved");
 q.flags=1336;q.last=115;FMinuteStats({q},lo,hi,m);check(m.business==1 && m.o==115,"additional flag bits preserved");
 q.time_msc=hi;FMinuteStats({a,q},lo,hi,m);check(m.total==1 && m.c==100,"exclusive minute end");
 FMinuteStats({},lo,hi,m);check(m.business==0 && m.o==0 && m.last==0,"empty statistics reset");
 MqlRates r;string reason;
 check(FValidRates({r},1,0,lo,hi,reason),"valid M1 structurally accepted");
 check(!FValidRates({r},1,4403,lo,hi,reason),"partial M1 API error rejected");
 check(!FValidRates({r},2,0,lo,hi,reason),"count mismatch rejected");
 check(!FValidRates({r,r},2,0,lo,hi,reason),"duplicate M1 rejected");
 r.low=std::numeric_limits<double>::quiet_NaN();check(!FValidRates({r},1,0,lo,hi,reason),"NaN M1 rejected");
 r=MqlRates{};r.low=0;check(!FValidRates({r},1,0,lo,hi,reason),"zero M1 price rejected");
 r=MqlRates{};r.time+=60;check(!FValidRates({r},1,0,lo,hi,reason),"M1 exclusive end");
 r=MqlRates{};check(FSameRates({r},{r}),"M1 exact stability");MqlRates changed=r;changed.tick_volume++;
 check(!FSameRates({r},{changed}),"M1 volume change breaks stability");
 changed=r;changed.close+=0.0000000001;check(!FSameRates({r},{changed}),"M1 precision change breaks stability");
 FMinuteStats({a,b},lo,hi,m);r.high=115;r.close=105;
 check(FDiff(m,r)==10 && FFields(FDiff(m,r))=="H|C","reports exact divergent fields");
 FMinuteStats({},lo,hi,m);check(columns(FMinuteCells(m))==8,"empty minute CSV keeps all columns");
 FMinuteStats({a,b},lo,hi,m);check(columns(FMinuteCells(m))==8,"business minute CSV keeps all columns");
 g_all={a,b};g_trade={a,b};g_m1={MqlRates{}};writes.clear();
 check(FSaveMinutes("test.csv",true)&&writes.size()==3,"header and two minute rows exported");
 check(columns(writes[0])==33 && columns(writes[1])==33 && columns(writes[2])==33,"present and missing M1 export exactly 33 columns");
 check(writes[1].find("IGUAL;IGUAL")!=string::npos && writes[2].find("SEM_M1;SEM_M1")!=string::npos,"matching and missing M1 states distinct");
 g_all.clear();g_trade.clear();writes.clear();check(FSaveMinutes("test.csv",false)&&columns(writes[1])==33,"M1 without trades exported without invented zero-price OHLC");
 check(writes[1].find("SEM_NEGOCIO;SEM_NEGOCIO")!=string::npos,"absence not confused with price divergence");
 writes.clear();fail_at=1;int prior=closed_files;check(!FSaveMinutes("test.csv",true)&&closed_files==prior+1,"failed export does not claim success and closes file");
 std::cout<<"checks="<<checks<<" failures="<<failures<<'\n';return failures?1:0;
}
