#include <string>
#include <vector>
#include <cmath>
#include <iostream>
#include <cassert>
using string=std::string;using ulong=unsigned long;
struct MqlTick {long time_msc;double last;unsigned flags;};
const int COPY_TICKS_TRADE=0,TICK_FLAG_LAST=8,TICK_FLAG_VOLUME=16,TICK_FLAG_BUY=32,TICK_FLAG_SELL=64;
long mono=0;bool stopped=false,stop_in_call=false;int err=0,reply_error=0,calls=0,count=0;long from_seen=0,to_seen=0;
std::vector<MqlTick> reply;
bool IsStopped(){return stopped;}ulong GetTickCount64(){return mono;}
string IntegerToString(long n){return std::to_string(n);}bool MathIsValidNumber(double x){return std::isfinite(x);}
void Print(string s){std::cout<<s<<"\n";}
void ResetLastError(){err=0;}int GetLastError(){return err;}
template<class T>int ArraySize(const std::vector<T>&a){return a.size();}
int CopyTicksRange(string,std::vector<MqlTick>&out,int,ulong from,ulong to){calls++;from_seen=from;to_seen=to;out=reply;err=reply_error;mono+=45000;if(stop_in_call)stopped=true;return count;}
#include "opening_adapted.mqh"
int checks=0;void check(bool yes,const char *name){if(!yes){std::cerr<<"FAIL "<<name<<'\n';std::exit(1);}checks++;std::cout<<"PASS "<<name<<'\n';}
int main(){
 string why;long first=-7;double price=-7;long begin=100000,end=begin+180000,now=end+1;
 auto read=[&](){return MDOpeningRead208("WINZ26",begin,end,now,first,price,why);};
 count=1;reply={{begin+1,100,8}};reply_error=4403;
 check(!read()&&!opening208.confirmed&&first==-7,"partial timeout rejected without publishing opening");
 check(from_seen==begin&&to_seen==begin+59999,"nonzero bounded one-minute session query");
 check(opening208.cursor==begin&&opening208.next_due==mono+2000,"timeout preserves search cursor; backoff measured after call");
 int before=calls;check(!read()&&calls==before,"no query during backoff");
 mono=opening208.next_due;count=-1;check(!read()&&opening208.next_due==mono+4000,"repeated timeout increases backoff");
 mono=opening208.next_due;reply_error=0;count=0;reply.clear();check(!read()&&opening208.cursor==begin+60000,"only complete empty window advances search");
 mono=opening208.next_due;count=1;reply={{begin+60001,105,8}};
 check(read()&&first==begin+60001&&price==105,"later recovery confirms real first trade after proven empty prefix");
 before=calls;check(read()&&calls==before,"confirmed opening retained without repeated history synchronization");
 stopped=true;check(!read()&&calls==before,"manual interruption before query has no side effect");
 stopped=false;begin+=1000000;end=begin+180000;now=end+1;reply={{begin,100,8}};stop_in_call=true;reply_error=4022;count=-1;
 check(!read()&&!opening208.confirmed&&opening208.cursor==begin&&opening208.next_due==0,"manual removal during call does not commit error result or advance retry");
 stopped=false;stop_in_call=false;reply_error=0;mono+=100000;count=1;reply={{begin-1,100,8}};
 check(!read()&&!opening208.confirmed,"out-of-window result rejected");
 mono=opening208.next_due;reply={{begin,100,1}};check(!read(),"quote-only event rejected");
 mono=opening208.next_due;reply={{begin,100,8}};check(read(),"valid subsequent trade recovers invalid result");
 begin+=1000000;end=begin+180000;now=begin+1000;before=calls;
 check(!read()&&calls==before,"unfinished first minute cannot certify empty history");
 std::cout<<"OPENING_TICKS_208;Checks="<<checks<<";Failures=0;SIMULATED_API\n";
}
