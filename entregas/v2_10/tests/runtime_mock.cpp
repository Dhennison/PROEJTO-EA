// C++ adaptation with simulated MT5 APIs; NOT an MQL5 compiler or terminal.
#define main baseline_main
#include "host.cpp"
#undef main
#include <vector>
#include <ctime>
#include <functional>
#include "../MQL5/Scripts/ModeloD_Integrado_Sem_Transporte/ModeloD_OperationalCases.mqh"
#include "../MQL5/Experts/ModeloD_Integrado_Sem_Transporte/ModeloD_Observer.mqh"
#include "../MQL5/Experts/ModeloD_Integrado_Sem_Transporte/ModeloD_Stream.mqh"
#define MD_TERMINAL69
#define MD_DAILY_TERMINAL614
#define MODELOD_CHART_MQH
using datetime=long;
struct MqlDateTime{int year,mon,day;};
struct MqlTick{long time_msc;double last;uint flags;double bid=209995,ask=210000;};
struct MqlRates{long time;double open,high,low,close;long tick_volume=100,real_volume=100;};
template<class T>void ArraySetAsSeries(std::vector<T> &,bool){}
struct MqlTradeTransaction{};
struct MqlTradeRequest{int action=0,type=0,type_filling=0,type_time=0;ulong magic=0,order=0,position=0;string symbol,comment;double volume=0,price=0,sl=0,tp=0;};
struct MqlTradeResult{uint retcode=0;int retcode_external=0;ulong order=0,deal=0;};
template<class T>void ZeroMemory(T &v){v=T{};}
template<class T>int ArraySize(const std::vector<T> &v){return (int)v.size();}
const int MQL_TESTER=100,MQL_OPTIMIZATION=101,ACCOUNT_MARGIN_MODE=102,ACCOUNT_MARGIN_MODE_RETAIL_HEDGING=103,
 SYMBOL_EXPIRATION_TIME=104,SERIES_SYNCHRONIZED=105,PERIOD_D1=1440,SYMBOL_FILLING_MODE=106,SYMBOL_TRADE_EXEMODE=107,
 SYMBOL_FILLING_FOK=1,SYMBOL_FILLING_IOC=2,SYMBOL_TRADE_EXECUTION_MARKET=2,
 ORDER_TIME_GTC=0,ORDER_FILLING_RETURN=2,ORDER_FILLING_FOK=0,ORDER_FILLING_IOC=1,
 TRADE_ACTION_PENDING=5,TRADE_ACTION_REMOVE=8,TRADE_ACTION_SLTP=6,TRADE_ACTION_DEAL=1,
 ORDER_TYPE_BUY_LIMIT=2,ORDER_TYPE_SELL_LIMIT=3,DEAL_PROFIT=110,DEAL_COMMISSION=111,DEAL_SWAP=112,DEAL_FEE=113;
long mock_login210=1;string mock_server210="TEST";bool mock_hedge210=true;
bool mock_tester210=false,mock_optimization210=false;int mock_send_calls210=0;
std::vector<MqlTradeRequest> mock_requests210;std::vector<MqlRates> mock_daily_rates210;
std::function<bool(const MqlTradeRequest &,MqlTradeResult &)> mock_send210;
long MQLInfoInteger(int p){return p==MQL_TESTER?mock_tester210:mock_optimization210;}
bool OrderSend(const MqlTradeRequest &r,MqlTradeResult &v){mock_send_calls210++;mock_requests210.push_back(r);if(mock_send210)return mock_send210(r,v);v.retcode=10031;return false;}
bool SymbolSelect(string,bool){return true;}
bool SeriesInfoInteger(string,int,int,long &v){v=1;return true;}
bool FileIsEnding(int h){return handles.at(h)->f.peek()==std::char_traits<char>::eof();}
string FileReadString(int h){string line;std::getline(handles.at(h)->f,line);return line;}
int StringReplace(string &s,string from,string to){int n=0;size_t at=0;while((at=s.find(from,at))!=string::npos){s.replace(at,from.size(),to);at+=to.size();n++;}return n;}

const int TERMINAL_CONNECTED=1,ACCOUNT_LOGIN=2,ACCOUNT_SERVER=3,ACCOUNT_MARGIN_FREE=4,
 TIME_DATE=1,TIME_SECONDS=2,FILE_SHARE_READ=128,
 TICK_FLAG_LAST=8,TICK_FLAG_VOLUME=16,TICK_FLAG_BUY=32,TICK_FLAG_SELL=64,
 COPY_TICKS_TRADE=0,COPY_TICKS_ALL=-1,PERIOD_M1=1,ORDER_TYPE_BUY=0,ORDER_TYPE_SELL=1,
 SYMBOL_TRADE_TICK_SIZE=11,SYMBOL_VOLUME_MIN=12,SYMBOL_VOLUME_MAX=13,SYMBOL_VOLUME_STEP=14,
 SYMBOL_TRADE_MODE=15,SYMBOL_ORDER_MODE=16,SYMBOL_TRADE_STOPS_LEVEL=17,SYMBOL_TRADE_FREEZE_LEVEL=18,
 SYMBOL_POINT=19,SYMBOL_ASK=20,SYMBOL_BID=21,SYMBOL_ORDER_LIMIT=2,SYMBOL_ORDER_SL=4,SYMBOL_ORDER_TP=8,
 SYMBOL_TRADE_MODE_FULL=4,SYMBOL_TRADE_MODE_LONGONLY=1,SYMBOL_TRADE_MODE_SHORTONLY=2,
 ORDER_PRICE_OPEN=10,ORDER_SL=11,ORDER_TP=12,ORDER_POSITION_ID=13,ORDER_COMMENT=14,POSITION_SL=15,POSITION_TP=16,
 DEAL_PRICE=20,CHARTEVENT_CHART_CHANGE=1,INIT_PARAMETERS_INCORRECT=2,INIT_FAILED=1,INIT_SUCCEEDED=0;
long mock_utc=11000000,mock_mono=10000;bool mock_broker_fresh=true;bool mock_connected=true,mock_unstable=false,mock_price_error=false,mock_tick_error=false,mock_margin_ok=true;
double mock_free_margin=100000000;
int mock_calls=0;long selected_order=0,selected_pos=0;string _Symbol="WIN$N";
MDOpSnapshot mock_book;std::vector<MqlTick> mock_ticks,mock_all_ticks;std::vector<MqlRates> mock_rates;
long TimeGMT(){return mock_utc/1000;}
long TimeTradeServer(){return (mock_utc-10800000)/1000;}
long TimeCurrent(){return mock_broker_fresh?TimeTradeServer():0;}
unsigned long GetTickCount64(){return mock_mono;}
long AccountInfoInteger(int p){return p==ACCOUNT_MARGIN_MODE?(mock_hedge210?ACCOUNT_MARGIN_MODE_RETAIL_HEDGING:0):mock_login210;}string AccountInfoString(int){return mock_server210;}
double AccountInfoDouble(int){return mock_free_margin;}
bool TerminalInfoInteger(int){return mock_connected;}
bool TimeToStruct(long stamp,MqlDateTime &out){std::time_t value=stamp;auto g=std::gmtime(&value);out.year=g->tm_year+1900;out.mon=g->tm_mon+1;out.day=g->tm_mday;return true;}
int MDDateValue614(long stamp){MqlDateTime v;TimeToStruct(stamp,v);return v.year*10000+v.mon*100+v.day;}
string TimeToString(long v,int){return IntegerToString(v);}
bool EventSetTimer(int){return true;}void EventKillTimer(){}bool IsStopped(){return false;}
template<class...T>void Comment(T...){ }
void MDVisualClear(long,uint){}
bool MDVisualSync(long,uint,const MDDay &,datetime,datetime,bool){return true;}
bool MDCollectDaily614(int,MDDailyRaw614 &,string &why){why="SIMULATED_DAILY_DATA_FAILURE";return false;}
bool SymbolInfoDouble(string,int prop,double &v){
 if(prop==SYMBOL_TRADE_TICK_SIZE)v=5;
 else if(prop==SYMBOL_VOLUME_MAX)v=100000;
 else if(prop==SYMBOL_ASK)v=210000;
 else if(prop==SYMBOL_BID)v=209995;
 else v=1;
 return true;
}
bool SymbolInfoInteger(string,int prop,long &v){if(prop==SYMBOL_TRADE_MODE)v=SYMBOL_TRADE_MODE_FULL;else if(prop==SYMBOL_ORDER_MODE)v=14;else if(prop==SYMBOL_EXPIRATION_TIME)v=MDCivilMidnight2026(20261216)/1000;else if(prop==SYMBOL_FILLING_MODE)v=SYMBOL_FILLING_FOK;else if(prop==SYMBOL_TRADE_EXEMODE)v=SYMBOL_TRADE_EXECUTION_MARKET;else v=0;return true;}
bool SymbolInfoTick(string,MqlTick &v){if(mock_ticks.empty())return false;v=mock_ticks.back();return true;}
bool OrderCalcMargin(int,string,double,double,double &v){v=100;if(!mock_margin_ok){lastError=77;return false;}return true;}
bool Collect69(datetime,datetime,MDSnapshot69 &s,string &why){
 s=mock_book.book;mock_calls++;
 if(mock_unstable&&mock_calls%2==0){if(s.orders>0)s.o[0].order.remaining-=1;else s.account_key+=1;}
 why="MOCK_INVENTORY";return mock_tester210||mock_connected;
}
bool OrderSelect(ulong id){selected_order=(long)id;return true;}
bool PositionSelectByTicket(ulong id){selected_pos=(long)id;return true;}
int order_index(long id){for(int i=0;i<mock_book.book.orders;i++)if(mock_book.book.o[i].order.ticket==id)return i;return -1;}
int pos_index(long id){for(int i=0;i<mock_book.book.positions;i++)if(mock_book.book.p[i].ticket==id)return i;return -1;}
bool OD69(int prop,double &v){int i=order_index(selected_order);if(i<0)return false;auto x=mock_book.orders[i];v=prop==ORDER_PRICE_OPEN?x.price:(prop==ORDER_SL?x.sl:x.tp);return true;}
bool OI69(int,long &v){int i=order_index(selected_order);if(i<0)return false;v=mock_book.orders[i].position_id;return true;}
bool OS69(int,string &v){int i=order_index(selected_order);if(i<0)return false;v=mock_book.orders[i].comment;return true;}
bool HD69(ulong id,int prop,double &v){selected_order=id;return OD69(prop,v);}
bool HI69(ulong id,int prop,long &v){selected_order=id;return OI69(prop,v);}
bool HS69(ulong id,int prop,string &v){selected_order=id;return OS69(prop,v);}
bool DD69(ulong id,int prop,double &v){if(prop!=DEAL_PRICE){v=0;return true;}for(int i=0;i<mock_book.book.deals;i++)if(mock_book.book.d[i].ticket==(long)id){v=mock_book.deal_price[i];return !mock_price_error;}return false;}
bool PD69(int prop,double &v){int i=pos_index(selected_pos);if(i<0)return false;v=prop==POSITION_SL?mock_book.sl[i]:mock_book.tp[i];return true;}
int CopyTicksRange(string,std::vector<MqlTick> &out,int flags,ulong from,ulong until){
 out.clear();if(mock_tick_error){lastError=1;return -1;}
 auto &source=flags==COPY_TICKS_ALL?mock_all_ticks:mock_ticks;
 for(auto v:source)if(v.time_msc>=(long)from&&v.time_msc<=(long)until)out.push_back(v);
 return out.size();
}
int CopyRates(string,int period,datetime from,std::time_t until,std::vector<MqlRates> &out){out.clear();auto &source=period==PERIOD_D1?mock_daily_rates210:mock_rates;for(auto v:source)if(v.time>=from&&v.time<=until)out.push_back(v);return out.size();}
int CopyRates(string,int,int from,int count,std::vector<MqlRates> &out){out=mock_daily_rates210;return out.size();}
// MT5's Unicode binary writer reports bytes while StringLen reports characters.
// Simulate that native behavior only for the lock marker.
uint RuntimeFileWriteString(int h,string value,int count=-1){
 uint written=FileWriteString(h,value,count);
 return handles.at(h)->path.find(".lock")!=string::npos?written*2:written;
}
#define FileWriteString RuntimeFileWriteString
#include "EA_ADAPTED_PATH"
#undef FileWriteString
string ReadMockReport(){std::ifstream file(full(report_path));return string(std::istreambuf_iterator<char>(file),std::istreambuf_iterator<char>());}
void advance(long delta){mock_utc+=delta;mock_mono+=delta;}
int main(){
 std::filesystem::remove_all("/tmp/md615k_host");std::filesystem::create_directories("/tmp/md615k_host");
 MDOpState seed;MDOpFrame f;OPFilled(seed,mock_book,f);
 for(int i=0;i<seed.nlevels;i++)seed.levels[i].cutoff_utc=12000000;
 string scope=seed.scope,path="ModeloD_OPERATIONAL_"+scope+".ledger",text,why;
 int h=FileOpen("ModeloD_OPERATIONAL_"+scope+".lock",FILE_READ|FILE_WRITE|FILE_BIN|FILE_COMMON);
 MDOpState empty;MDOpInit(empty,scope,1);OPCheck(MDOpCommitFile(path,h,text,empty,seed,"RUNTIME_SEED",why),"seed integrated ledger with proven synthetic positions");FileClose(h);
 OPCheck(OnInit()==INIT_SUCCEEDED,"actual EA OnInit reopens integrated ledger");
 string marker_why;
 OPCheck(LockMarkerMatches(lock615,"MDOP_LOCK_V1_"+scope,marker_why),"lock marker is confirmed by content when native write count is bytes, not characters");
 OnTimer();advance(2000);OnTimer();advance(2000);OnTimer();
 OPCheck(operational.npositions==2&&!fatal,"actual EA timer keeps both positions despite daily-data failure");
 OPCheck(opclock.ok&&opclock.offset==-10800,"runtime clock samples measured server timezone");
 OPCheck(operational.positions[0].protect.phase==1&&operational.positions[1].protect.phase==1,"actual timer persists missing SLTP intents");
 string diagnostic_report=ReadMockReport();
 OPCheck(StringFind(diagnostic_report,"componente=DADOS_DIARIOS;motivo=SIMULATED_DAILY_DATA_FAILURE")>=0,
  "daily failure cause is actually written to report, not only chart comment");
 OPCheck(StringFind(diagnostic_report,"recuperacao=RELEITURA_NO_TIMER;DEPENDE_DE_DADOS_VALIDOS")>=0,
  "daily report explicitly states conditional automatic re-evaluation");
 long revision=operational.revision;mock_unstable=true;advance(2000);OnTimer();
 OPCheck(operational.revision==revision,"unstable pair of real collector calls cannot commit reconciliation");
 OPCheck(StringFind(ReadMockReport(),"componente=INVENTARIO;motivo=DUAS_LEITURAS_DIVERGENTES")>=0,
  "unstable pair has exact report cause despite generic coordinator result");mock_unstable=false;
 mock_price_error=true;MDOpSnapshot rejected;
 OPCheck(!MDOpCollect(0,rejected,why)&&why=="DEAL_PRICE_READ_FAILED","terminal producer rejects unavailable execution price");mock_calls=0;advance(2000);OnTimer();
 OPCheck(StringFind(ReadMockReport(),"componente=INVENTARIO;motivo=PRIMEIRA_COLETA;DEAL_PRICE_READ_FAILED")>=0,
  "underlying property collection error survives the coordinator in the report");
 mock_price_error=false;
 mock_book.sl[0]=operational.levels[0].prices.sl_tick;mock_book.tp[0]=operational.levels[0].prices.tp_tick;
 advance(2000);OnTimer();
 OPCheck(operational.positions[0].sl==mock_book.sl[0]&&operational.positions[0].tp==mock_book.tp[0],"live SLTP properties feed the persisted integrated state");
 mock_book.book.p[0].ticket=999;advance(2000);OnTimer();
 OPCheck(operational.positions[0].ticket==999&&operational.positions[0].identifier==700,"actual EA reconciles migrated ticket without resetting identifier");
 mock_connected=false;advance(12000000-mock_utc);OnTimer();
 OPCheck(operational.levels[0].cutoff&&operational.positions[0].close.phase==1&&operational.positions[1].close.phase==1,"actual timer cutoff works without quote, daily data or connection");
 OPCheck(operational.positions[0].close.serial==0,"actual EA does not transport shutdown intentions");
 OnDeinit(1);fatal=false;report_error=false;stream_started615=false;mock_connected=true;mock_calls=0;
 for(int i=0;i<MDOP_LEVELS;i++)pending_trail_started[i]=false;
 for(int i=0;i<MDOP_POSITIONS;i++)position_trail_started[i]=false;
 OPCheck(OnInit()==INIT_SUCCEEDED&&operational.levels[0].cutoff&&operational.positions[0].close.phase==1,"EA reinitialization retains cutoff and untransported intentions");
 OnDeinit(1);
 // Reproduce the native incident: TRADE cache lacks the high while M1 is complete.
 MDDataEvidence evidence;evidence.date=20261028;evidence.previous_date=20261027;evidence.adjustment_date=20261028;evidence.source_date=20261027;evidence.expiry_date=20261216;
 evidence.contract="WINZ26";evidence.ohlc_contract=evidence.contract;evidence.opening_contract=evidence.contract;evidence.adjustment_contract=evidence.contract;evidence.source="BVBG.187.01";
 evidence.ohlc_verified=true;evidence.opening_verified=true;evidence.adjustment_verified=true;evidence.previous_adjustment=100;evidence.tick_size=5;
 evidence.values.high_prev=120;evidence.values.low_prev=80;evidence.values.close_prev=100;evidence.values.open_today=100;evidence.values.adjustment=100;
 MDSessionSet(evidence.date,9*3600,18*3600+25*60,18*3600,true,"RUNTIME_FIXTURE",evidence.session);
 long fallback_from=MDCivilMidnight2026(evidence.date)+(long)evidence.session.scheduled_open*1000;evidence.open_msc=fallback_from;
 MDStream615 fallback_stream;OPCheck(MDStreamStart615(fallback_stream,evidence),"fallback fixture starts with valid frozen daily data");
 mock_ticks={{fallback_from,100,8},{fallback_from+1000,110,8}};
 mock_all_ticks={{fallback_from,100,8},{fallback_from+500,100,1},{fallback_from+700,120,8},{fallback_from+1000,110,8}};
 mock_rates={{fallback_from/1000,100,120,100,110}};
 bool fallback_ok=MDStreamCollect615(fallback_stream,fallback_from+59999,why,true);string fallback_why=why;
 OPCheck(fallback_ok&&StringFind(fallback_why,"BLOCO_RECUPERADO_COPY_TICKS_ALL_FILTRADO")==0&&fallback_stream.audit.count==3&&fallback_stream.audit.minutes[0].h==120,
  "incomplete TRADE cache recovers only through trade-flagged ALL events that fully match M1; "+fallback_why);
 MDStream615 still_blocked;MDStreamStart615(still_blocked,evidence);mock_all_ticks=mock_ticks;
 bool blocked_ok=MDStreamCollect615(still_blocked,fallback_from+59999,why,true);
 OPCheck(!blocked_ok&&StringFind(why,"TICKS_DIVERGEM_M1;")==0&&still_blocked.cursor==fallback_from,
  "ALL fallback that also disagrees with M1 cannot advance the stream; "+why);
 string property_reason;mock_margin_ok=false;
 OPCheck(!EntryProperties(operational.levels[0],property_reason)&&property_reason=="CALCULO_DE_MARGEM_FALHOU;erro=77","margin API failure has an exact non-sensitive diagnostic");
 mock_margin_ok=true;mock_free_margin=50;
 OPCheck(!EntryProperties(operational.levels[0],property_reason)&&property_reason=="MARGEM_LIVRE_INSUFICIENTE","insufficient free margin is distinct from calculation failure without logging account balance");
 mock_free_margin=100000000;
 // Exercise the actual new trail producer using API mocks, including timestamp ambiguity.
 MDOpTrail trail;MDLevel price=seed.levels[0].prices;
 mock_ticks={{160000,price.sl,8},{160001,price.entry,8},{160002,price.tp+5,8}};
 MDOpTrailInit(trail,"WINZ26",160000,price);
 OPCheck(!MDOpTrailRead(trail,160010,why)&&trail.ambiguous&&trail.boundary,"same-ms stop remains ambiguous; later target is proven post-origin");
 mock_ticks={{160000,price.sl,8}};MDOpTrailInit(trail,"WINZ26",160000,price);
 OPCheck(!MDOpTrailRead(trail,160010,why)&&!trail.boundary,"pre/same-fill boundary is not converted into post-fill close evidence");
 mock_ticks={{160001,price.entry,8},{160002,price.sl-10,8}};MDOpTrailInit(trail,"WINZ26",160000,price);
 OPCheck(MDOpTrailRead(trail,160010,why)&&trail.boundary,"post-origin gap beyond mathematical stop creates boundary evidence");
 mock_tick_error=true;MDOpTrailInit(trail,"WINZ26",160000,price);
 OPCheck(!MDOpTrailRead(trail,160010,why)&&trail.cursor==160001,"failed tick query leaves trail cursor unchanged");mock_tick_error=false;
 MDOpClock c;MDOpClockInit(c);MDOpClockRead(c,0,why);advance(2000);MDOpClockRead(c,0,why);advance(2000);
 OPCheck(MDOpClockRead(c,0,why),"continuous clock established by successive samples");mock_utc+=10000;
 OPCheck(!MDOpClockRead(c,0,why)&&why=="WALL_CLOCK_DISCONTINUITY","wall-clock jump without monotonic progress is refused");
 MDOpClock unanchored;MDOpClockInit(unanchored);mock_broker_fresh=false;
 for(int i=0;i<3;i++){advance(2000);MDOpClockRead(unanchored,0,why);}
 OPCheck(!unanchored.ok&&why=="FRESH_BROKER_TIME_REQUIRED_AFTER_RESTART","startup cannot certify time from two estimates sharing the same PC clock");mock_broker_fresh=true;
 Print("RUNTIME_MOCK;Checks=",op_checks,";Failures=",op_failures,";API_MT5_SIMULADA;NAO_E_COMPILACAO_MQL5");return op_failures?1:0;
}
