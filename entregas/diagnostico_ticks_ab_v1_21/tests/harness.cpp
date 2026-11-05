#include <string>
#include <vector>
#include <cmath>
#include <limits>
#include <iostream>
#include <algorithm>
#include <utility>
#include <sstream>
#include <iomanip>
using string=std::string;using ulong=unsigned long;using uint=unsigned int;
constexpr int NF=64,NMIN=60;
constexpr uint COPY_TICKS_ALL=0,COPY_TICKS_TRADE=1,COPY_TICKS_INFO=2;
constexpr uint TICK_FLAG_LAST=8,TICK_FLAG_VOLUME=16,TICK_FLAG_BUY=32,TICK_FLAG_SELL=64;
struct MqlTick {long time_msc;double bid,ask,last;ulong volume;double volume_real;uint flags;long time=1000;};
long InpFrom=1000,InpTo=1600;
uint g_mask=120;
std::vector<MqlTick> g_all_ticks,g_trade_ticks,g_info_ticks,reply;
bool resize_fail=false;
int api_error=0,last_error=0,n_override=-99;
void ResetLastError(){last_error=0;}int GetLastError(){return last_error;}
int CopyTicksRange(string,std::vector<MqlTick>&v,uint,ulong,ulong){v=reply;last_error=api_error;return n_override==-99?(int)v.size():n_override;}
string InpSymbol="WINZ26";
int InpMaxAttempts=10;
bool select_ok=true,timer_ok=true,g_have=false,g_done=false,finish_called=false,finish_stable=false;
int g_attempt=0;
long now=1602;
constexpr int INIT_PARAMETERS_INCORRECT=2,INIT_FAILED=1,INIT_SUCCEEDED=0;
bool SymbolSelect(string,bool){return select_ok;}
bool EventSetTimer(int){return timer_ok;}
long TimeCurrent(){return now;}
template<class...Args>void Print(Args&&...){}
template<class...Args>string StringFormat(const char*fmt,Args&&...){return fmt;}
void Say(string){}
constexpr int FILE_COMMON=1,FILE_WRITE=2,FILE_TXT=4,FILE_ANSI=8,INVALID_HANDLE=-1;
int file_writes=0,file_opens=0,write_fail_at=0;bool flush_fail=false,names_exhausted=false;
string file_content;
bool FileIsExist(string,int){return names_exhausted;}
int FileOpen(string,int){file_opens++;return 1;}
uint FileWriteString(int,string text){file_writes++;if(write_fail_at==file_writes)return 0;file_content+=text;return text.size();}
void FileClose(int){}
void FileFlush(int){if(flush_fail)last_error=8;}
void Finish(bool stable){g_done=true;finish_called=true;finish_stable=stable;}
int StringLen(const string &s){return s.size();}
unsigned short StringGetCharacter(const string &s,int i){return (unsigned char)s[i];}
string DoubleToString(double x,int n){std::ostringstream out;if(n<0)out<<std::scientific<<std::setprecision(-n)<<x;else out<<std::fixed<<std::setprecision(n)<<x;return out.str();}
template<class T>int ArrayResize(std::vector<T>&v,int n){if(resize_fail)return -1;v.resize(n);return n;}
string IntegerToString(long v){return std::to_string(v);}
double MathRound(double x){return std::round(x);}
bool MathIsValidNumber(double x){return std::isfinite(x);}
template<class T>int ArraySize(const std::vector<T>&v){return v.size();}
// MQL5 ArrayCopy enlarges a dynamic destination when necessary; it does not
// shrink an existing larger destination. Whole-array copy starts at index zero.
template<class T>int ArrayCopy(std::vector<T>&dst,const std::vector<T>&src){
 if(dst.size()<src.size())dst.resize(src.size());
 std::copy(src.begin(),src.end(),dst.begin());return src.size();
}
#include "extracted.hpp"
int checks=0,failures=0;
void check(bool ok,const char*name){checks++;if(!ok)failures++;std::cout<<(ok?"PASS ":"FAIL ")<<name<<std::endl;}
Res read(std::vector<MqlTick> v,int err=0,int count=-99){reply=v;api_error=err;n_override=count;Res r{};Collect(COPY_TICKS_ALL,r);return r;}
int main(int argc,char**argv){
 MqlTick quote{1000000,170910,170915,0,0,0,6};
 MqlTick trade{1001000,170910,170915,170910,250,250,56};
 if(argc>1&&string(argv[1])=="nan"){
  trade.last=std::numeric_limits<double>::quiet_NaN();
  Res r=read({trade});
  check(!r.valid&&r.tf_last_invalido==1,"nonfinite Last classified without invalid numeric conversion");
  return failures?1:0;
 }
 Res q=read({quote});check(q.valid&&q.tf_n==0&&q.ea_n==0,"quote-only stream remains distinct from trades");
 Res t=read({trade});check(t.valid&&t.tf_n==1&&t.ea_n==1&&t.tf_last_invalido==0,"valid flags+Last recognized");
 quote.last=170910;quote.volume=250;Res carried=read({quote});
 check(carried.tf_n==0&&carried.ea_n==0&&carried.carried_n==1,"carried Last and volume not counted as flagged trades");
 MqlTick zero=trade;zero.last=0;Res z=read({zero});check(z.tf_n==1&&z.ea_n==0&&z.tf_last_invalido==1,"flagged zero Last counted separately");
 read({quote});Res identical=read({quote});check(SameRes(identical,carried),"identical complete responses stable");
 quote.bid+=5;Res altered=read({quote});check(!SameRes(altered,carried),"changed quote-only Bid changes full signature");
 Res err=read({trade},4403);check(!err.valid&&err.why=="ERRO_4403","partial timeout invalidates response");
 Res mismatch=read({trade},0,2);check(!mismatch.valid&&mismatch.why.find("N_DIFERENTE")!=string::npos,"count/array mismatch explicitly invalidated");
 Res negative=read({},0,-1);check(!negative.valid,"negative API return invalidated");
 MqlTick before=trade;before.time_msc=999999;check(!read({before}).valid,"tick before requested window rejected");
 MqlTick after=trade;after.time_msc=1600000;check(!read({after}).valid,"tick at exclusive end rejected");
 MqlTick earlier=trade;earlier.time_msc=1000001;check(!read({trade,earlier}).valid,"time reversal rejected");
 Res duplicate=read({trade,trade});check(duplicate.valid&&duplicate.ea_n==2,"same-millisecond duplicates preserved");
 Res empty=read({});check(empty.valid&&empty.n==0&&empty.ea_n==0,"complete empty response structurally valid");
 check(!SameRes(err,err)&&!SameRes(mismatch,mismatch),"invalid responses never stable even if repeated");
 MqlTick minute=trade;minute.time_msc=1060000;Res minutes=read({trade,minute});
 check(minutes.per_min[0]==1&&minutes.per_min[1]==1,"per-minute assignment follows requested origin");
 quote.last=0;quote.volume=0;quote.volume_real=0.001;Res fraction_a=read({quote});
 quote.volume_real=0.002;Res fraction_b=read({quote});
 check(!SameRes(fraction_b,fraction_a),"different fractional volume_real must not be called identical");
 g_all_ticks.clear();Res large=read({trade,trade,trade});Res small=read({trade});
 check(small.n==1&&g_all_ticks.size()==1,"CSV buffer must contain exactly final successful response size");
 Res final_empty=read({});check(final_empty.n==0&&g_all_ticks.empty(),"final empty ALL must clear old CSV records");
 check(OnInit()==INIT_SUCCEEDED,"valid initialization selects symbol and starts timer");
 InpTo=InpFrom;check(OnInit()==INIT_PARAMETERS_INCORRECT,"invalid window rejected at initialization");InpTo=1600;
 InpMaxAttempts=1;check(OnInit()==INIT_PARAMETERS_INCORRECT,"insufficient attempts rejected");InpMaxAttempts=10;
 select_ok=false;check(OnInit()==INIT_FAILED,"symbol selection failure rejected");select_ok=true;
 timer_ok=false;check(OnInit()==INIT_FAILED,"timer initialization failure rejected");timer_ok=true;
 reply={trade};api_error=0;n_override=-99;now=InpTo+1;
 OnTimer();check(g_attempt==0&&!finish_called,"timer does not query an unfinished window");
 now=InpTo+2;OnTimer();check(g_attempt==1&&!finish_called,"first valid response cannot declare stability");
 OnTimer();check(g_attempt==2&&finish_called&&finish_stable,"second consecutive identical valid response finishes stable");
 int attempts=g_attempt;OnTimer();check(g_attempt==attempts,"finished run cannot query again");
 g_attempt=0;g_have=false;g_done=false;finish_called=false;api_error=4403;
 OnTimer();check(!g_have&&!finish_called,"timeout cannot establish stable baseline");
 api_error=0;OnTimer();check(!finish_called&&g_have,"first success after timeout is a new baseline");
 OnTimer();check(finish_called&&finish_stable&&g_attempt==3,"recovery requires two consecutive successful reads");
 g_attempt=0;g_have=false;g_done=false;finish_called=false;InpMaxAttempts=2;n_override=2;
 OnTimer();OnTimer();check(finish_called&&!finish_stable,"repeated malformed array reaches limit without false stable");
 resize_fail=true;Res allocation=read({trade});check(!allocation.valid&&allocation.why=="FALHA_COPIA_SNAPSHOT","snapshot allocation failure invalidates response");resize_fail=false;
 MqlTick inf=trade;inf.bid=std::numeric_limits<double>::infinity();
 check(!read({inf}).valid,"infinite Bid rejected before hashing");
 inf=trade;inf.ask=std::numeric_limits<double>::quiet_NaN();check(!read({inf}).valid,"NaN Ask rejected before hashing");
 inf=trade;inf.volume_real=std::numeric_limits<double>::infinity();check(!read({inf}).valid,"infinite volume_real rejected before hashing");
 g_a=read({trade,trade});file_writes=0;write_fail_at=0;file_content="";
 check(DumpCsv("test")&&file_writes==3,"CSV emits header and exactly ALL.n data rows");
 g_a=read({});file_writes=0;
 check(DumpCsv("test")&&file_writes==1,"empty final CSV emits header only");
 g_a=read({trade});g_all_ticks.clear();int opens=file_opens;
 check(!DumpCsv("test")&&file_opens==opens,"CSV refuses mismatched snapshot before opening file");
 g_a=read({trade});file_writes=0;write_fail_at=1;
 check(!DumpCsv("test"),"CSV header write failure reported");
 file_writes=0;write_fail_at=2;
 check(!DumpCsv("test"),"CSV row write failure reported");
 file_writes=0;write_fail_at=0;flush_fail=true;
 check(!DumpCsv("test"),"CSV flush failure reported");flush_fail=false;
 names_exhausted=true;opens=file_opens;
 check(!DumpCsv("test")&&file_opens==opens,"CSV cannot overwrite when all candidate filenames exist");names_exhausted=false;
 std::cout<<"CHECKS="<<checks<<";FAILURES="<<failures<<std::endl;
 return failures?1:0;
}
