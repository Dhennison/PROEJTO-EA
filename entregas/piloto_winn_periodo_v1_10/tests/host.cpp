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
bool env_tester=true,env_opt=false,send_ok=true,check_ok=true;int send_count=0,check_count=0,env_mode=0;long now=0;string env_currency="BRL";bool auto_pending=false,auto_remove=false,auto_close=false,write_ok=true,history_ok=true;
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
long TerminalInfoInteger(int){return 6295;}long AccountInfoInteger(int){return env_mode;}
string AccountInfoString(int p){return p==ACCOUNT_CURRENCY?env_currency:"GenialInvestimentos-PRD";}datetime TimeCurrent(){return now;}datetime TimeLocal(){return now;}long GetMicrosecondCount(){static long n=100;return n++;}
string TimeToString(long stamp,int flags){std::time_t value=stamp;auto t=*std::gmtime(&value);std::ostringstream out;if(flags&TIME_DATE)out<<std::put_time(&t,"%Y.%m.%d");if((flags&TIME_DATE)&&(flags&(TIME_MINUTES|TIME_SECONDS)))out<<" ";if(flags&TIME_SECONDS)out<<std::put_time(&t,"%H:%M:%S");else if(flags&TIME_MINUTES)out<<std::put_time(&t,"%H:%M");return out.str();}
long SymbolInfoInteger(string,int p){return sym_i[p];}bool SymbolInfoInteger(string s,int p,long &v){v=SymbolInfoInteger(s,p);return true;}
double SymbolInfoDouble(string,int p){return sym_d[p];}bool SymbolInfoDouble(string s,int p,double &v){v=SymbolInfoDouble(s,p);return true;}
bool SymbolInfoString(string,int,string &v){v="MOCK";return true;}bool SymbolInfoTick(string,MqlTick &t){t=quote;return true;}
bool FolderCreate(string,int){return true;}int FileOpen(string name,int,int,int){int h=nextfile++;filenames[h]=name;return h;}uint FileWriteString(int h,string s){if(!write_ok)return 0;files[h]+=s;return s.size();}void FileFlush(int){}void FileClose(int){}
bool OrderCheck(MqlTradeRequest &,MqlTradeCheckResult &r){check_count++;r.retcode=check_ok?TRADE_RETCODE_DONE:987;return check_ok;}
bool OrderSend(MqlTradeRequest &r,MqlTradeResult &v){send_count++;requests.push_back(r);v.retcode=send_ok?TRADE_RETCODE_DONE:999;v.order=send_count;if(send_ok&&auto_pending&&r.action==TRADE_ACTION_PENDING)orders.push_back({{-100,send_count},{ORDER_MAGIC,(long)r.magic}});if(send_ok&&auto_remove&&r.action==TRADE_ACTION_REMOVE){orders.erase(std::remove_if(orders.begin(),orders.end(),[&](auto &o){return (ulong)o[-100]==r.order;}),orders.end());}if(send_ok&&auto_close&&r.action==TRADE_ACTION_DEAL){positions.erase(std::remove_if(positions.begin(),positions.end(),[&](auto &p){return (ulong)p[-100]==r.position;}),positions.end());}return send_ok;}
int OrdersTotal(){return orders.size();}ulong OrderGetTicket(int i){selected_order=i;return orders[i].count(-100)?orders[i][-100]:i+1;}
string OrderGetString(int){return _Symbol;}long OrderGetInteger(int p){return orders.at(selected_order)[p];}
int PositionsTotal(){return positions.size();}ulong PositionGetTicket(int i){selected_position=i;return positions[i].count(-100)?positions[i][-100]:i+1;}
string PositionGetString(int){return _Symbol;}long PositionGetInteger(int p){return positions.at(selected_position)[p];}
double PositionGetDouble(int){return 1;}bool PositionSelectByTicket(ulong t){for(int i=0;i<(int)positions.size();i++)if((positions[i].count(-100)?positions[i][-100]:i+1)==(long)t){selected_position=i;return true;}return false;}
bool HistorySelect(long,long){return history_ok;}bool HistoryDealSelect(ulong t){selected_deal=t-1;return t>0&&t<=deals_i.size();}
int HistoryOrdersTotal(){return 0;}ulong HistoryOrderGetTicket(int){return 0;}string HistoryOrderGetString(ulong,int){return "";}long HistoryOrderGetInteger(ulong,int){return 0;}double HistoryOrderGetDouble(ulong,int){return 0;}
int HistoryDealsTotal(){return deals_i.size();}ulong HistoryDealGetTicket(int i){return i+1;}
string HistoryDealGetString(ulong,int p){return p==DEAL_SYMBOL?_Symbol:"MOCK";}
long HistoryDealGetInteger(ulong t,int p){return deals_i.at(t-1)[p];}
double HistoryDealGetDouble(ulong t,int p){return deals_d.at(t-1)[p];}
std::map<long,std::vector<MqlRates>> fixture;
int CopyRates(string,int,long from,long,std::vector<MqlRates> &out){out=fixture[from];return out.size();}

#include "EA_ModeloD_WINN_Periodo.mq5"
int checks=0;void require(bool value,const char* why){checks++;if(!value){std::cerr<<"FAIL "<<why<<"\n";std::exit(1);}}
void reset()
{
 env_tester=true;env_opt=false;send_ok=true;check_ok=true;env_mode=ACCOUNT_MARGIN_MODE_RETAIL_HEDGING;env_currency="BRL";now=1788220800;
 auto_pending=false;auto_remove=false;auto_close=false;write_ok=true;history_ok=true;send_count=check_count=0;_Symbol="WIN$N";_Period=PERIOD_M5;
 requests.clear();orders.clear();positions.clear();deals_i.clear();deals_d.clear();sym_i.clear();sym_d.clear();files.clear();filenames.clear();quote={};
 pm_initialized=false;pm_global_failed=false;pm_io_failed=false;pm_reported=false;pm_last_global_msc=0;pm_unknown_events=0;pm_active_day=-1;pm_report=INVALID_HANDLE;
 for(int d=0;d<PM_DAYS;d++){pm_day[d]={};pm_ref[d]={};pm_started[d]=pm_failed[d]=pm_cut_seen[d]=false;pm_ticks[d]=pm_classified[d]=pm_first_msc[d]=pm_last_msc[d]=0;pm_requests[d]=pm_accepted[d]=0;}
 for(int s=0;s<PM_SLOTS;s++){pm_tape[s]={};pm_sent[s]=pm_ended[s]=pm_exit_seen[s]=pm_close_requested[s]=false;pm_position[s]=0;pm_retry_cancel[s]=pm_retry_close[s]=0;pm_work[s]={};}
 ArrayInitialize(pm_n,0);ArrayInitialize(pm_o,0);ArrayInitialize(pm_h,0);ArrayInitialize(pm_l,0);ArrayInitialize(pm_c,0);
 sym_i[SYMBOL_TRADE_MODE]=SYMBOL_TRADE_MODE_FULL;sym_i[SYMBOL_ORDER_MODE]=SYMBOL_ORDER_LIMIT|SYMBOL_ORDER_SL|SYMBOL_ORDER_TP;
 sym_i[SYMBOL_EXPIRATION_MODE]=SYMBOL_EXPIRATION_GTC;sym_i[SYMBOL_FILLING_MODE]=SYMBOL_FILLING_FOK;
 sym_d[SYMBOL_TRADE_TICK_SIZE]=5;sym_d[SYMBOL_VOLUME_MIN]=1;sym_d[SYMBOL_VOLUME_MAX]=100;sym_d[SYMBOL_VOLUME_STEP]=1;
}
void tick(long stamp,double price){quote={};quote.time_msc=stamp;quote.time=stamp/1000;quote.bid=price;quote.ask=price+5;quote.last=price;quote.flags=30;now=stamp/1000;OnTick();}
void first_tick(int d){tick((long)pm_ref[d].first*1000,pm_ref[d].values.open_today);}
string saved(string suffix){for(auto it=filenames.rbegin();it!=filenames.rend();++it)if(it->second.size()>=suffix.size()&&it->second.substr(it->second.size()-suffix.size())==suffix)return files[it->first];return "";}
void csv_shape(string text,int expected_rows){std::istringstream in(text);string line;int rows=0,width=-1;while(std::getline(in,line)){if(line.empty())continue;int count=std::count(line.begin(),line.end(),';');if(width<0)width=count;require(count==width,"consistent CSV columns");rows++;}require(rows==expected_rows,"CSV expected row count");}
long parse_stamp(string text){std::tm t{};std::istringstream in(text);in>>std::get_time(&t,"%Y.%m.%d %H:%M");return timegm(&t);}
void load_fixture(string path)
{
 std::ifstream in(path);string line;std::getline(in,line);while(std::getline(in,line)){std::vector<string> c;std::istringstream s(line);string v;while(std::getline(s,v,';'))c.push_back(v);MqlRates r;r.time=parse_stamp(c[0]);r.open=std::stod(c[1]);r.high=std::stod(c[2]);r.low=std::stod(c[3]);r.close=std::stod(c[4]);r.real_volume=std::stol(c[5]);r.tick_volume=4;r.spread=5;fixture[r.time/86400*86400].push_back(r);}
}
void run_bars(int day)
{
 for(auto r:fixture[pm_ref[day].begin]){tick(r.time*1000,r.open);tick(r.time*1000+100,r.high);tick(r.time*1000+200,r.low);tick(r.time*1000+300,r.close);}
}
int main(int argc,char **argv)
{
 require(argc==2,"fixture argument");load_fixture(argv[1]);
 reset();env_tester=false;require(OnInit()==INIT_PARAMETERS_INCORRECT&&send_count==0,"terminal blocked");
 reset();env_opt=true;require(OnInit()==INIT_PARAMETERS_INCORRECT,"optimization blocked");
 reset();_Symbol="WINZ26";require(OnInit()==INIT_PARAMETERS_INCORRECT,"wrong symbol blocked");
 reset();_Period=99;require(OnInit()==INIT_PARAMETERS_INCORRECT,"wrong timeframe blocked");
 reset();env_currency="USD";require(OnInit()==INIT_PARAMETERS_INCORRECT,"USD rejected before any order");
 reset();env_mode=999;require(OnInit()==INIT_PARAMETERS_INCORRECT,"netting blocked");
 reset();sym_i[SYMBOL_CUSTOM]=1;require(OnInit()==INIT_PARAMETERS_INCORRECT,"custom symbol blocked");
 reset();sym_i[SYMBOL_TRADE_MODE]=0;require(OnInit()==INIT_PARAMETERS_INCORRECT,"trade disabled blocked");
 reset();sym_d[SYMBOL_TRADE_TICK_SIZE]=1;require(OnInit()==INIT_PARAMETERS_INCORRECT,"wrong tick grid");
 reset();sym_d[SYMBOL_VOLUME_MIN]=5;require(OnInit()==INIT_PARAMETERS_INCORRECT,"one contract unavailable");
 reset();sym_i[SYMBOL_ORDER_MODE]=0;require(OnInit()==INIT_PARAMETERS_INCORRECT,"SL TP limit required");
 reset();write_ok=false;require(OnInit()==INIT_FAILED&&send_count==0,"report failure prevents orders");
 reset();require(OnInit()==INIT_SUCCEEDED,"valid batch initialized");
 for(int d=0;d<PM_DAYS;d++){require(pm_ref[d].begin<pm_ref[d].first&&pm_ref[d].first<pm_ref[d].cut,"daily timing");require(pm_ref[d].values.adjustment>0,"daily adjustment");for(int l=0;l<5;l++)require(pm_day[d].levels[l].entry_tick==MDRound5(pm_day[d].levels[l].entry),"core normalization retained");}
 PMInitWorkReport();int work_count=0;double work_points=0;for(int s=0;s<PM_SLOTS;s++){work_count+=pm_work[s].exists;work_points+=pm_work[s].points;}
 require(work_count==33&&std::abs(work_points-3839.308998)<1e-7,"33 Work reference operations preserved");
 require(PMFindDay(1788566400000)<0,"Saturday has no reference");
 reset();OnInit();first_tick(0);require(pm_started[0]&&pm_requests[0]==5&&pm_accepted[0]==5,"first day pending requests");
 for(int i=0;i<5;i++){require(requests[i].volume==1,"one contract each");require(requests[i].magic==PM_MAGIC+(ulong)i,"unique day level magic");require(requests[i].price==pm_day[0].levels[i].entry_tick&&requests[i].sl==pm_day[0].levels[i].sl_tick&&requests[i].tp==pm_day[0].levels[i].tp_tick,"requested prices from core");}
 tick((long)pm_ref[0].first*1000+1000,pm_ref[0].values.open_today);require(pm_requests[0]==5,"no duplicate entries");
 tick((long)pm_ref[0].cut*1000,pm_ref[0].values.open_today);first_tick(1);require(pm_requests[1]==5&&requests.back().magic==PM_MAGIC+9,"second day fresh state and magic");
 reset();OnInit();tick((long)pm_ref[0].first*1000,pm_ref[0].values.open_today+5);require(pm_failed[0]&&send_count==0,"opening mismatch no entries");first_tick(1);require(pm_started[1]&&!pm_global_failed&&send_count==5,"opening mismatch isolated to one day");
 reset();OnInit();check_ok=false;first_tick(0);require(pm_failed[0]&&send_count==0&&pm_requests[0]==1,"OrderCheck rejection blocks remaining daily entries");
 reset();OnInit();send_ok=false;first_tick(0);require(pm_failed[0]&&send_count==1,"OrderSend rejection not bypassed");
 reset();OnInit();first_tick(0);int before=send_count;env_tester=false;MqlTradeRequest req;MqlTradeResult result;require(!PMSend(req,"ENTRADA",0,result)&&send_count==before,"transport guard rechecked");
 reset();OnInit();tick(1788566400000+9*3600000,180000);require(pm_global_failed&&send_count==0,"unexpected date blocks new entries");
 reset();OnInit();auto_pending=true;auto_remove=true;first_tick(0);require(orders.size()==5,"mock pending book");tick((long)pm_ref[0].cut*1000,180000);require(orders.empty()&&pm_cut_seen[0],"all pending cancelled at own cutoff");first_tick(1);require(!pm_global_failed&&pm_requests[1]==5,"normal rollover allowed");
 reset();OnInit();auto_pending=true;first_tick(0);first_tick(1);require(pm_global_failed&&!pm_started[1]&&pm_requests[1]==0,"prior-day residual blocks next entries");require(pm_sent[0],"old consumed/request state retained");
 reset();OnInit();first_tick(13);int slot=68;orders.push_back({{-100,500},{ORDER_MAGIC,(long)PM_MAGIC+slot}});before=send_count;
 tick((long)pm_ref[13].first*1000+1000,188305);require(pm_tape[slot].touched&&!pm_ended[slot]&&send_count==before,"new touch not cancelled by pre-entry TP crossing");
 tick((long)pm_ref[13].first*1000+2000,187605);require(pm_ended[slot]&&requests.back().action==TRADE_ACTION_REMOVE,"post-touch theoretical exit cancels remainder");
 reset();OnInit();first_tick(0);positions.push_back({{-100,10},{POSITION_MAGIC,(long)PM_MAGIC},{POSITION_TYPE,POSITION_TYPE_BUY}});positions.push_back({{-100,20},{POSITION_MAGIC,(long)PM_MAGIC+3},{POSITION_TYPE,POSITION_TYPE_SELL}});before=send_count;
 tick((long)pm_ref[0].cut*1000,180000);require(send_count==before+2,"cutoff closes two independent positions");
 require(requests[before].type==ORDER_TYPE_BUY&&requests[before].price==180005,"short cutoff uses ask");require(requests[before+1].type==ORDER_TYPE_SELL&&requests[before+1].price==180000,"long cutoff uses bid");
 tick((long)pm_ref[0].cut*1000+500,180000);require(send_count==before+2,"cutoff retries throttled");
 pm_close_requested[0]=true;require(PMExitLabel(DEAL_REASON_EXPERT,0,(long)pm_ref[0].cut*1000,"PM110_CORTE")=="HORARIO","native cutoff label requires own close evidence");require(PMExitLabel(DEAL_REASON_EXPERT,0,(long)pm_ref[0].cut*1000,"end of test")!="HORARIO","forced test end not mislabeled cutoff");
 double points=0;require(PMClosedPoints(true,1,1,100,90,points)&&points==-10,"negative cutoff points");require(PMClosedPoints(true,1,1,100,100,points)&&points==0,"flat cutoff points");require(!PMClosedPoints(true,1,.5,100,50,points),"partial exit not closed");
 reset();OnInit();first_tick(0);PMFinish("TRUNCATED");auto cmp=saved("COMPARATIVO.csv");require(cmp.find("SEM_EVENTOS")!=string::npos&&saved("DIAS.csv").find("INCOMPLETO")!=string::npos,"truncated batch not called zero result");csv_shape(cmp,71);csv_shape(saved("DIAS.csv"),15);
 reset();OnInit();auto_pending=true;auto_remove=true;for(int d=0;d<PM_DAYS;d++)run_bars(d);require(!pm_global_failed&&orders.empty(),"whole batch chronological rollover");
 // Actual price fixture from audited 21/09 pilot; APIs remain mocks.
 deals_i={{{DEAL_MAGIC,(long)PM_MAGIC+68},{DEAL_ENTRY,DEAL_ENTRY_IN},{DEAL_POSITION_ID,5},{DEAL_TIME_MSC,1789981322993}},{{DEAL_MAGIC,0},{DEAL_ENTRY,DEAL_ENTRY_OUT},{DEAL_POSITION_ID,5},{DEAL_TIME_MSC,1789981382296},{DEAL_REASON,DEAL_REASON_TP}},{{DEAL_MAGIC,(long)PM_MAGIC+69},{DEAL_ENTRY,DEAL_ENTRY_IN},{DEAL_POSITION_ID,6},{DEAL_TIME_MSC,1789982341090}},{{DEAL_MAGIC,0},{DEAL_ENTRY,DEAL_ENTRY_OUT},{DEAL_POSITION_ID,6},{DEAL_TIME_MSC,1789982402374},{DEAL_REASON,DEAL_REASON_TP}}};
 deals_d={{{DEAL_PRICE,188305},{DEAL_VOLUME,1}},{{DEAL_PRICE,187605},{DEAL_VOLUME,1}},{{DEAL_PRICE,189200},{DEAL_VOLUME,1}},{{DEAL_PRICE,188970},{DEAL_VOLUME,1}}};
 MqlTradeTransaction tx;tx.type=TRADE_TRANSACTION_DEAL_ADD;tx.deal=1;OnTradeTransaction(tx,req,result);tx.deal=2;OnTradeTransaction(tx,req,result);require(pm_position[68]==5&&pm_exit_seen[68],"transaction mapped by position even magic zero on exit");
 PMFinish("FIXTURE");cmp=saved("COMPARATIVO.csv");require(cmp.find("700.0000000000")!=string::npos&&cmp.find("230.0000000000")!=string::npos,"audited execution prices yield 700 and 230");
 require(saved("RESULTADO.txt").find("days_complete=14")!=string::npos&&saved("RESULTADO.txt").find("points_closed=930.0000000000")!=string::npos,"all-day completeness and actual aggregate");
 require(cmp.find("580.0000000000")!=string::npos&&cmp.find("235.0000000000")!=string::npos,"normalized references separate");
 require(cmp.find("OPERACAO_WORK_SEM_EA")!=string::npos,"missing execution explicitly classified rather than copied from Work");
 csv_shape(cmp,71);csv_shape(saved("DIAS.csv"),15);csv_shape(saved("M1_ONTICK.csv"),7876);csv_shape(saved("M1_TESTER.csv"),7876);csv_shape(saved("DEALS.csv"),5);
 before=files.size();PMFinish("AGAIN");require((int)files.size()==before,"finish once");
 std::cout<<"PASS checks="<<checks<<"; actual MQL source adapted to C++; ASan/UBSan; mock trading APIs; NOT native MT5 compilation/execution\n";
}
