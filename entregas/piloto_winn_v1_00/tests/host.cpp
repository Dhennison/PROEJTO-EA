#include <bits/stdc++.h>
using string=std::string;using datetime=long;using uint=unsigned int;
using ENUM_SYMBOL_INFO_INTEGER=int;using ENUM_SYMBOL_INFO_DOUBLE=int;using ENUM_SYMBOL_INFO_STRING=int;
#include "constants.h"
struct MqlTick{datetime time=0;double bid=0,ask=0,last=0;ulong volume=0;long time_msc=0;uint flags=0;double volume_real=0;};
struct MqlRates{datetime time=0;double open=0,high=0,low=0,close=0;long tick_volume=0;int spread=0;long real_volume=0;};
struct MqlTradeRequest{int action=0;ulong magic=0,order=0,position=0;string symbol,comment;double volume=0,price=0,sl=0,tp=0;int type=0,type_filling=0,type_time=0;ulong deviation=0;};
struct MqlTradeResult{uint retcode=0;ulong order=0,deal=0;double volume=0,price=0;string comment;};
struct MqlTradeCheckResult{uint retcode=0;string comment;};
struct MqlTradeTransaction{int type=0;ulong deal=0;};
bool env_tester=true,env_opt=false,send_ok=true,check_ok=true;int send_count=0,check_count=0,env_mode=0;long now=1789948800;
string _Symbol="WIN$N";int _Period=PERIOD_M5;MqlTick quote;std::map<int,long> sym_i;std::map<int,double> sym_d;
std::vector<MqlTradeRequest> requests;std::map<int,string> files,filenames;int nextfile=1;
std::vector<std::map<int,long>> orders,positions;int selected_order=-1,selected_position=-1;
std::vector<std::map<int,long>> deals_i;std::vector<std::map<int,double>> deals_d;int selected_deal=-1;
template<class T>void ZeroMemory(T &x){x=T{};}
template<class T,size_t N,class V>void ArrayInitialize(T (&a)[N],V v){std::fill(a,a+N,(T)v);}
void ArraySetAsSeries(std::vector<MqlRates>&,bool){}
string IntegerToString(long x){return std::to_string(x);}string DoubleToString(double x,int p){std::ostringstream s;s<<std::fixed<<std::setprecision(p)<<x;return s.str();}
bool MathIsValidNumber(double x){return std::isfinite(x);}double MathAbs(double x){return std::abs(x);}double MathFloor(double x){return std::floor(x);}double MathRound(double x){return std::round(x);}double MathMax(double x,double y){return std::max(x,y);}double MathMin(double x,double y){return std::min(x,y);}
template<class... T>void Print(T...){ }
void ResetLastError(){}int GetLastError(){return 0;}
long MQLInfoInteger(int p){return p==MQL_TESTER?env_tester:(p==MQL_OPTIMIZATION?env_opt:1);}
long TerminalInfoInteger(int){return 6231;}long AccountInfoInteger(int){return env_mode;}
string AccountInfoString(int){return "MOCK";}datetime TimeCurrent(){return now;}datetime TimeLocal(){return now;}long GetMicrosecondCount(){static long n=100;return n++;}
string TimeToString(long stamp,int){return std::to_string(stamp);}
long SymbolInfoInteger(string,int p){return sym_i[p];}bool SymbolInfoInteger(string s,int p,long &v){v=SymbolInfoInteger(s,p);return true;}
double SymbolInfoDouble(string,int p){return sym_d[p];}bool SymbolInfoDouble(string s,int p,double &v){v=SymbolInfoDouble(s,p);return true;}
bool SymbolInfoString(string,int,string &v){v="MOCK";return true;}bool SymbolInfoTick(string,MqlTick &t){t=quote;return true;}
bool FolderCreate(string,int){return true;}int FileOpen(string name,int,int,int){int h=nextfile++;filenames[h]=name;return h;}uint FileWriteString(int h,string s){files[h]+=s;return s.size();}void FileFlush(int){}void FileClose(int){}
bool OrderCheck(MqlTradeRequest &,MqlTradeCheckResult &r){check_count++;r.retcode=check_ok?TRADE_RETCODE_DONE:987;return check_ok;}
bool OrderSend(MqlTradeRequest &r,MqlTradeResult &v){send_count++;requests.push_back(r);v.retcode=send_ok?TRADE_RETCODE_DONE:999;v.order=send_count;return send_ok;}
int OrdersTotal(){return orders.size();}ulong OrderGetTicket(int i){selected_order=i;return i+1;}
string OrderGetString(int){return _Symbol;}long OrderGetInteger(int p){return orders.at(selected_order)[p];}
int PositionsTotal(){return positions.size();}ulong PositionGetTicket(int i){selected_position=i;return i+1;}
string PositionGetString(int){return _Symbol;}long PositionGetInteger(int p){return positions.at(selected_position)[p];}
double PositionGetDouble(int){return 1;}bool PositionSelectByTicket(ulong t){selected_position=t-1;return t>0&&t<=positions.size();}
bool HistorySelect(long,long){return true;}bool HistoryDealSelect(ulong t){selected_deal=t-1;return t>0&&t<=deals_i.size();}
int HistoryOrdersTotal(){return 0;}ulong HistoryOrderGetTicket(int){return 0;}string HistoryOrderGetString(ulong,int){return "";}long HistoryOrderGetInteger(ulong,int){return 0;}double HistoryOrderGetDouble(ulong,int){return 0;}
int HistoryDealsTotal(){return deals_i.size();}ulong HistoryDealGetTicket(int i){return i+1;}
string HistoryDealGetString(ulong,int p){return p==DEAL_SYMBOL?_Symbol:"MOCK";}
long HistoryDealGetInteger(ulong t,int p){return deals_i.at(t-1)[p];}
double HistoryDealGetDouble(ulong t,int p){return deals_d.at(t-1)[p];}
int CopyRates(string,int,long,long,std::vector<MqlRates>&){return 0;}
#include "EA_ModeloD_Piloto_WINN.mq5"
int checks=0;void require(bool value,const char* reason){checks++;if(!value){std::cerr<<"FAIL "<<reason<<"\n";std::exit(1);}}
void reset()
{
 env_tester=true;env_opt=false;send_ok=true;check_ok=true;send_count=0;check_count=0;env_mode=ACCOUNT_MARGIN_MODE_RETAIL_HEDGING;now=PW_DAY;_Symbol="WIN$N";_Period=PERIOD_M5;
 requests.clear();orders.clear();positions.clear();deals_i.clear();deals_d.clear();sym_i.clear();sym_d.clear();quote={};pw_day={};
 pw_started=false;pw_failed=false;pw_io_failed=false;pw_cut_seen=false;pw_reported=false;pw_initialized=false;pw_report=INVALID_HANDLE;
 pw_requests=0;pw_accepted=0;pw_first_msc=0;pw_last_msc=0;pw_ticks=0;pw_classified=0;
 for(int i=0;i<5;i++){pw_sent[i]=false;pw_ended[i]=false;pw_exit_seen[i]=false;pw_position[i]=0;pw_retry_cancel[i]=0;pw_retry_close[i]=0;pw_tape[i]={};}
 ArrayInitialize(pw_n,0);sym_i[SYMBOL_TRADE_MODE]=SYMBOL_TRADE_MODE_FULL;sym_i[SYMBOL_ORDER_MODE]=SYMBOL_ORDER_LIMIT|SYMBOL_ORDER_SL|SYMBOL_ORDER_TP;
 sym_i[SYMBOL_EXPIRATION_MODE]=SYMBOL_EXPIRATION_GTC;sym_i[SYMBOL_FILLING_MODE]=SYMBOL_FILLING_FOK;
 sym_d[SYMBOL_TRADE_TICK_SIZE]=5;sym_d[SYMBOL_VOLUME_MIN]=1;sym_d[SYMBOL_VOLUME_MAX]=100;sym_d[SYMBOL_VOLUME_STEP]=1;
}
void tick(long stamp,double last){quote={};quote.time_msc=stamp;quote.time=stamp/1000;quote.bid=last;quote.ask=last+5;quote.last=last;quote.flags=30;now=stamp/1000;OnTick();}
string saved(string suffix){for(auto it=filenames.rbegin();it!=filenames.rend();++it)if(it->second.size()>=suffix.size()&&it->second.substr(it->second.size()-suffix.size())==suffix)return files[it->first];return "";}
int main()
{
 reset();env_tester=false;require(OnInit()==INIT_PARAMETERS_INCORRECT,"terminal blocked");require(send_count==0,"no terminal sends");
 reset();env_opt=true;require(OnInit()==INIT_PARAMETERS_INCORRECT,"optimization blocked");
 reset();_Symbol="WINZ26";require(OnInit()==INIT_PARAMETERS_INCORRECT,"contract instead of WINN blocked");
 reset();_Period=99;require(OnInit()==INIT_PARAMETERS_INCORRECT,"wrong period blocked");
 reset();now=PW_FIRST;require(OnInit()==INIT_PARAMETERS_INCORRECT,"late init blocked");
 reset();env_mode=123;require(OnInit()==INIT_PARAMETERS_INCORRECT,"netting blocked");
 reset();sym_i[SYMBOL_TRADE_MODE]=0;require(OnInit()==INIT_PARAMETERS_INCORRECT,"disabled symbol blocked");
 reset();sym_d[SYMBOL_TRADE_TICK_SIZE]=1;require(OnInit()==INIT_PARAMETERS_INCORRECT,"wrong tick grid blocked");
 reset();sym_d[SYMBOL_VOLUME_MIN]=5;require(OnInit()==INIT_PARAMETERS_INCORRECT,"volume one unavailable blocked");
 reset();sym_i[SYMBOL_ORDER_MODE]=0;require(OnInit()==INIT_PARAMETERS_INCORRECT,"no limit/sl/tp blocked");
 reset();sym_i[SYMBOL_EXPIRATION_MODE]=0;require(OnInit()==INIT_PARAMETERS_INCORRECT,"no expiration supported blocked");
 reset();require(OnInit()==INIT_SUCCEEDED,"valid initial specification");tick((long)PW_FIRST*1000,187980);require(pw_started&&send_count==5&&pw_accepted==5,"five native pending requests");
 for(int i=0;i<5;i++){require(requests[i].volume==1,"one contract");require(requests[i].price==pw_day.levels[i].entry_tick,"entry preserved");require(requests[i].sl==pw_day.levels[i].sl_tick&&requests[i].tp==pw_day.levels[i].tp_tick,"fixed protection from theory");}
 require(pw_day.levels[3].entry_tick==188260&&pw_day.levels[3].tp_tick==187680,"R38 known fixture");
 require(pw_day.levels[4].entry_tick==189200&&pw_day.levels[4].tp_tick==188965,"R61 known fixture");
 tick((long)PW_FIRST*1000+1000,187980);require(send_count==5,"no repeated entries");
 reset();OnInit();tick((long)PW_FIRST*1000,187985);require(pw_failed&&send_count==0,"opening mismatch blocks all orders");
 reset();OnInit();check_ok=false;tick((long)PW_FIRST*1000,187980);require(pw_failed&&send_count==0&&pw_requests==1,"check failure no sends or next entries");
 reset();OnInit();send_ok=false;tick((long)PW_FIRST*1000,187980);require(pw_failed&&send_count==1&&pw_requests==1,"send rejection not bypassed");
 reset();OnInit();tick((long)PW_FIRST*1000,187980);env_tester=false;MqlTradeRequest req;MqlTradeResult res;require(!PWSend(req,"TEST",0,res)&&send_count==5,"transport guard rechecked");
 reset();OnInit();tick((long)PW_FIRST*1000,187980);int i=3;orders.push_back({{ORDER_MAGIC,(long)PW_MAGIC+i}});
 tick((long)PW_FIRST*1000+1000,188265);require(pw_tape[i].touched&&!pw_ended[i]&&send_count==5,"new touch no premature exit from pre-entry segment");
 tick((long)PW_FIRST*1000+2000,187680);require(pw_ended[i]&&send_count==6&&requests.back().action==TRADE_ACTION_REMOVE,"theoretical target cancels untouched-fill remainder");
 reset();OnInit();tick((long)PW_FIRST*1000,187980);orders.push_back({{ORDER_MAGIC,(long)PW_MAGIC}});positions.push_back({{POSITION_MAGIC,(long)PW_MAGIC+3},{POSITION_TYPE,POSITION_TYPE_SELL}});
 tick((long)PW_CUT*1000,188000);require(pw_cut_seen&&send_count==7,"cutoff cancels and closes");
 require(requests.back().action==TRADE_ACTION_DEAL&&requests.back().type==ORDER_TYPE_BUY&&requests.back().price==188005,"short cutoff uses ask native request");
 tick((long)PW_CUT*1000+500,188000);require(send_count==7,"cut retries throttled");
 reset();OnInit();tick((long)PW_FIRST*1000,187980);
 deals_i={{{DEAL_MAGIC,(long)PW_MAGIC+3},{DEAL_ENTRY,DEAL_ENTRY_IN},{DEAL_POSITION_ID,100},{DEAL_TIME_MSC,(long)PW_FIRST*1000+1000}},
          {{DEAL_MAGIC,0},{DEAL_ENTRY,DEAL_ENTRY_OUT},{DEAL_POSITION_ID,100},{DEAL_TIME_MSC,(long)PW_FIRST*1000+2000},{DEAL_REASON,DEAL_REASON_TP}},
          {{DEAL_MAGIC,(long)PW_MAGIC+4},{DEAL_ENTRY,DEAL_ENTRY_IN},{DEAL_POSITION_ID,200},{DEAL_TIME_MSC,(long)PW_FIRST*1000+3000}},
          {{DEAL_MAGIC,0},{DEAL_ENTRY,DEAL_ENTRY_OUT},{DEAL_POSITION_ID,200},{DEAL_TIME_MSC,(long)PW_FIRST*1000+4000},{DEAL_REASON,DEAL_REASON_TP}}};
 deals_d={{{DEAL_VOLUME,1},{DEAL_PRICE,188260}},{{DEAL_VOLUME,1},{DEAL_PRICE,187680}},{{DEAL_VOLUME,1},{DEAL_PRICE,189200}},{{DEAL_VOLUME,1},{DEAL_PRICE,188965}}};
 MqlTradeTransaction tx;tx.type=TRADE_TRANSACTION_DEAL_ADD;tx.deal=1;MqlTradeRequest request;MqlTradeResult result;
 OnTradeTransaction(tx,request,result);tx.deal=2;OnTradeTransaction(tx,request,result);require(pw_position[3]==100&&pw_exit_seen[3],"exit linked by position with different magic");
 PWFinish("TEST");string cmp=saved("COMPARATIVO.csv");require(cmp.find("580.0000000000")!=string::npos&&cmp.find("235.0000000000")!=string::npos,"actual report native deal points");
 require(cmp.find("579.863333333333")!=string::npos&&cmp.find("234.328333333333")!=string::npos,"Work points preserved separately");
 std::istringstream lines(cmp);string line;int width=-1,rows=0;while(std::getline(lines,line)){if(line.empty())continue;int count=std::count(line.begin(),line.end(),';');if(width<0)width=count;require(count==width,"CSV consistent columns");rows++;}require(rows==6,"five level rows plus header");
 auto filecount=files.size();PWFinish("TEST_AGAIN");require(files.size()==filecount,"final report emitted once");
 double points=0;require(PWClosedPoints(false,1,1,188260,187680,points)&&points==580,"short points");
 require(PWClosedPoints(true,1,1,100,90,points)&&points==-10,"cutoff negative points");
 require(PWClosedPoints(true,1,1,100,100,points)&&points==0,"cutoff flat points");
 require(!PWClosedPoints(true,1,.5,100,50,points),"partial exit not closed result");
 require(PWVolumeOne(1,100,1)&&!PWVolumeOne(5,100,1)&&!PWVolumeOne(.3,100,.3),"volume grid");
 require(PWExpectedDay((long)PW_DAY*1000)&&!PWExpectedDay((long)PW_END*1000),"day bounds");
 std::cout<<"PASS checks="<<checks<<"; MQL source adapted to C++; mocked APIs; NOT native MT5 compilation or execution\n";
}
