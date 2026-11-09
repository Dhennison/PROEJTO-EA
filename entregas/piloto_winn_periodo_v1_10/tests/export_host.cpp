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
int mock_error=0,fixture_error=0;void ResetLastError(){mock_error=0;}int GetLastError(){return mock_error;}
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
int CopyRates(string,int,long from,long,std::vector<MqlRates> &out){out=fixture[from];mock_error=fixture_error;return out.size();}


struct MqlDateTime{int year=0,mon=0,day=0,hour=0,min=0,sec=0;};
bool TimeToStruct(long stamp,MqlDateTime &out){std::time_t t=stamp;auto p=std::gmtime(&t);if(!p)return false;out.year=p->tm_year+1900;out.mon=p->tm_mon+1;out.day=p->tm_mday;out.hour=p->tm_hour;out.min=p->tm_min;out.sec=p->tm_sec;return true;}
long StructToTime(MqlDateTime &p){std::tm t{};t.tm_year=p.year-1900;t.tm_mon=p.mon-1;t.tm_mday=p.day;t.tm_hour=p.hour;t.tm_min=p.min;t.tm_sec=p.sec;return timegm(&t);}
bool SymbolSelect(string,bool){return true;}bool removed=false;bool EventSetTimer(int){return true;}void EventKillTimer(){}void ExpertRemove(){removed=true;}
int ArraySize(const std::vector<MqlRates> &v){return v.size();}int ArrayResize(std::vector<MqlRates> &v,int n){v.resize(n);return n;}
int ArrayCopy(std::vector<MqlRates> &to,const std::vector<MqlRates> &from){if(to.size()<from.size())to.resize(from.size());std::copy(from.begin(),from.end(),to.begin());return from.size();}
#include "Exportar_M1_WINN_Sem_Ordens.mq5"
int checks=0;void require(bool v,const char *why){checks++;if(!v){std::cerr<<"FAIL "<<why<<"\n";std::exit(1);}}
long stamp(string text){std::tm t{};std::istringstream s(text);s>>std::get_time(&t,"%Y.%m.%d %H:%M:%S");return timegm(&t);}
string saved(string suffix){for(auto it=filenames.rbegin();it!=filenames.rend();++it)if(it->second.size()>=suffix.size()&&it->second.substr(it->second.size()-suffix.size())==suffix)return files[it->first];return "";}
void reset(){env_tester=false;env_opt=false;now=stamp("2026.11.09 10:00:00");send_count=0;fixture_error=0;mock_error=0;write_ok=true;fixture.clear();files.clear();filenames.clear();pe_previous.clear();pe_cursor=pe_end=0;pe_attempt=pe_months=pe_pending=0;pe_total_rows=0;pe_have=pe_done=pe_io_failed=false;pe_status=INVALID_HANDLE;removed=false;InpSymbol="WIN$N";InpInicio=stamp("2026.09.01 00:00:00");InpFim=stamp("2026.09.22 00:00:00");InpMaxTentativasPorMes=3;}
MqlRates rate(long t){MqlRates r;r.time=t;r.open=100;r.high=105;r.low=95;r.close=100;r.tick_volume=10;r.real_volume=20;r.spread=5;return r;}
int main(){
 reset();env_tester=true;require(OnInit()==INIT_PARAMETERS_INCORRECT,"Tester refused");
 reset();InpFim=now+86400;require(OnInit()==INIT_PARAMETERS_INCORRECT,"future range refused");
 reset();InpInicio++;require(OnInit()==INIT_PARAMETERS_INCORRECT,"non midnight refused");
 reset();InpMaxTentativasPorMes=1;require(OnInit()==INIT_PARAMETERS_INCORRECT,"need two reads");
 reset();write_ok=false;require(OnInit()==INIT_FAILED,"write failure refused");
 reset();require(OnInit()==INIT_SUCCEEDED,"terminal readonly init");fixture[InpInicio]={rate(InpInicio+9*3600),rate(InpInicio+9*3600+60)};
 OnTimer();require(pe_have&&pe_months==0&&saved("M1_202609.csv").empty(),"first read not exported");OnTimer();require(pe_months==1&&pe_total_rows==2&&saved("STATUS.csv").find("EXPORTADO_ESTAVEL")!=string::npos,"two equal valid reads exported");OnTimer();require(pe_done&&removed&&send_count==0,"readonly completed no order calls");
 reset();OnInit();fixture[InpInicio]={rate(InpInicio+9*3600)};OnTimer();fixture[InpInicio][0].high+=5;OnTimer();require(pe_months==0,"changed data not stable");OnTimer();require(pe_months==1,"new stable pair accepted");
 reset();OnInit();fixture[InpInicio]={rate(InpInicio+9*3600),rate(InpInicio+9*3600+60),rate(InpInicio+9*3600+120)};OnTimer();fixture[InpInicio].pop_back();OnTimer();require(pe_previous.size()==2,"previous buffer resized on shrinking read");OnTimer();require(pe_total_rows==2,"shrunk stable data exported correctly");
 reset();OnInit();OnTimer();OnTimer();require(saved("STATUS.csv").find("VAZIO_ESTAVEL_NAO_CERTIFICA_AUSENCIA_GLOBAL")!=string::npos&&pe_total_rows==0,"empty is scoped and explicit");
 reset();OnInit();fixture_error=4401;for(int i=0;i<3;i++)OnTimer();require(pe_pending==1&&saved("M1_202609.csv").empty(),"nonzero error never exported");
 reset();OnInit();auto r=rate(InpInicio+9*3600);r.high=99;fixture[InpInicio]={r};for(int i=0;i<3;i++)OnTimer();require(pe_pending==1,"invalid OHLC stays pending");
 reset();OnInit();r=rate(InpInicio+9*3600);fixture[InpInicio]={r,r};for(int i=0;i<3;i++)OnTimer();require(pe_pending==1,"duplicate times refused");
 reset();OnInit();fixture[InpInicio]={rate(InpInicio-60)};for(int i=0;i<3;i++)OnTimer();require(pe_pending==1,"out of range refused");
 reset();require(PENextMonth(stamp("2023.12.15 00:00:00"))==stamp("2024.01.01 00:00:00"),"year rollover");require(PENextMonth(stamp("2024.02.01 00:00:00"))==stamp("2024.03.01 00:00:00"),"leap February boundary");
 InpInicio=stamp("2023.03.01 00:00:00");OnInit();while(!pe_done)OnTimer();require(pe_months==43,"43 monthly windows cover March 2023 to September 2026");
 std::vector<MqlRates> x={rate(1000)},y=x;require(PESame(x,y),"same eight fields");y[0].spread++;require(!PESame(x,y),"spread changes stability");y=x;y[0].real_volume++;require(!PESame(x,y),"volume changes stability");
 std::cout<<"PASS readonly_export_checks="<<checks<<"; adapted MQL with API mocks; NOT native MT5 compilation/execution\n";
}
