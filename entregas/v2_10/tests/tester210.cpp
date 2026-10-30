// Synthetic fixtures ONLY. This is not real historical data or a native Tester run.
int checks210=0,failures210=0;
void Check210(bool pass,string name){checks210++;if(!pass)failures210++;Print(pass?"PASS_210;":"FAIL_210;",name);}
long Begin210(){return MDCivilMidnight2026(20261030)+9*3600000;}
string Dataset210(){return "DataFonte=2026-10-29\nDataOperacional=2026-10-30\nFonte=BVBG.187.01\nStatus=OK\nQuantidadeContratos=1\nContrato.WINZ26.Ajuste=210000\nContrato.WINZ26.AjusteAnterior=210000\n";}
void WriteDataset210(string text){std::ofstream out(full(MDTesterB3Path210()));out<<text;}
void EmptyBook210(){
 mock_book=MDOpSnapshot{};mock_book.book.complete=true;mock_book.book.connected=true;mock_book.book.hedge=true;
 mock_book.book.account_key=MDAccount210();mock_book.book.server_key=MDServer210();mock_book.execution_prices_known=true;
}
void Reset210(){
 if(lock615!=INVALID_HANDLE)OnDeinit(1);
 fatal=false;owns615=false;report_error=false;stream_started615=false;stream_failed615=false;stream_reported615=-1;
 last_status="";stream_retries615=0;mock_tester210=true;ExecutarNoTester=true;mock_optimization210=false;
 DataTester=20261030;ContratoTester="WINZ26";FusoServidorTester=-10800;_Symbol="WINZ26";
 mock_login210=1;mock_server210="TEST";mock_hedge210=true;
 mock_connected=true;mock_unstable=false;mock_tick_error=false;mock_partial210=false;mock_stopped210=false;
 mock_price_error=false;mock_margin_ok=true;mock_free_margin=100000000;mock_calls=0;mock_send_calls210=0;
 mock_requests210.clear();mock_send210=nullptr;mock_rates.clear();EmptyBook210();
 mock_utc=Begin210()+10800000+45000;mock_mono=10000;opening208.symbol="";
 mock_ticks={{Begin210()+1000,210000,8}};mock_all_ticks=mock_ticks;
 long prior=MDCivilMidnight2026(20261029)/1000;
 mock_daily_rates210={{prior-86400,210000,211000,209000,210000},{prior,210000,211000,209000,210000},
 {MDCivilMidnight2026(20261030)/1000,210000,999999,1,888888}};
 for(int k=0;k<MDOP_LEVELS;k++)pending_trail_started[k]=false;
 for(int p=0;p<MDOP_POSITIONS;p++)position_trail_started[p]=false;
 WriteDataset210(Dataset210());
}
void Tick210(){OnTimer();advance(2000);}
void Bootstrap210(){Tick210();Tick210();Tick210();}
bool DiskPrepared210(const MqlTradeRequest &r){
 string text;MDOpState disk;
 if(!MDOpReadFile(ledger_path,text)||!MDOpReplay(text,operational.scope,Instancia,disk))return false;
 for(int k=0;k<disk.nlevels;k++){
  if(r.action==TRADE_ACTION_PENDING&&disk.levels[k].entry.phase==2&&MDOpComment(disk.levels[k])==r.comment)return true;
  if(r.action==TRADE_ACTION_REMOVE&&disk.levels[k].cancellation.phase==2&&disk.levels[k].order==(long)r.order)return true;
 }
 for(int p=0;p<disk.npositions;p++){
  if(r.action==TRADE_ACTION_SLTP&&disk.positions[p].protect.phase==2&&disk.positions[p].ticket==(long)r.position)return true;
  if(r.action==TRADE_ACTION_DEAL&&disk.positions[p].close.phase==2&&disk.positions[p].ticket==(long)r.position)return true;
 }
 return false;
}
void AcceptOrders210(bool &prepared){
 mock_send210=[&prepared](const MqlTradeRequest &r,MqlTradeResult &result){
  prepared=prepared&&DiskPrepared210(r);int k=mock_book.book.orders++;long ticket=1000+k;
  MDRawOrder69 order;order.order.ticket=ticket;order.order.magic=r.magic;order.order.symbol=r.symbol;
  order.order.buy=r.type==ORDER_TYPE_BUY_LIMIT;order.order.state=0;order.order.initial_volume=r.volume;
  order.order.remaining=r.volume;order.setup_msc=(long)TimeCurrent()*1000;order.entry_limit=true;
  mock_book.book.o[k]=order;mock_book.orders[k].price=r.price;mock_book.orders[k].sl=r.sl;mock_book.orders[k].tp=r.tp;
  mock_book.orders[k].position_id=0;mock_book.orders[k].comment=r.comment;result.retcode=10008;result.order=ticket;return true;
 };
}
void SeedPositions210(){
 MDOpState seed;MDOpFrame frame;OPFilled(seed,mock_book,frame);
 seed.scope=Scope615();mock_book.book.account_key=MDAccount210();mock_book.book.server_key=MDServer210();
 for(int k=0;k<seed.nlevels;k++){seed.levels[k].date=DataTester;seed.levels[k].key=(long)DataTester*10+k;
  seed.levels[k].cutoff_utc=MDCivilMidnight2026(DataTester)+75600000;}
 // Receipt in fixture has a two-contract pending remainder, as in the inherited tests.
 Check210(Commit(seed,"SYNTHETIC_POSITION_FIXTURE"),"fixture with proven origins committed");
 for(int i=0;i<3;i++){string why;MDOpClockRead(opclock,operational.watermark,why);}
}
int main(){
 std::filesystem::remove_all("/tmp/md615k_host");std::filesystem::create_directories("/tmp/md615k_host");
 Reset210();mock_tester210=false;Check210(OnInit()==INIT_PARAMETERS_INCORRECT&&mock_send_calls210==0,"live opt-in is rejected before any send");
 Reset210();mock_login210=0;mock_server210="";Check210(OnInit()==INIT_SUCCEEDED&&operational.scope==MDContext612(1,"STRATEGY_TESTER",Instancia),"virtual replay identity works without broker login or server");OnDeinit(1);
 Reset210();mock_hedge210=false;Check210(OnInit()==INIT_PARAMETERS_INCORRECT,"netting account cannot silently replace independent hedge positions");
 Reset210();ExecutarNoTester=false;Check210(OnInit()==INIT_PARAMETERS_INCORRECT,"Tester requires explicit opt-in");
 Reset210();mock_optimization210=true;Check210(OnInit()==INIT_PARAMETERS_INCORRECT,"optimization is rejected for first smoke release");
 Reset210();DataTester=20261029;Check210(OnInit()==INIT_PARAMETERS_INCORRECT,"unreviewed dataset date cannot be substituted");
 Reset210();FusoServidorTester=0;Check210(OnInit()==INIT_PARAMETERS_INCORRECT,"zero Tester GMT offset cannot silently authorize BRT");
 Reset210();_Symbol="WIN$N";Check210(OnInit()==INIT_PARAMETERS_INCORRECT,"continuous symbol cannot replace explicit historical contract");
 Reset210();std::filesystem::remove(full(MDTesterB3Path210()));Check210(OnInit()==INIT_PARAMETERS_INCORRECT,"missing B3 input blocks before any ledger/send");
 Reset210();string bad=Dataset210();StringReplace(bad,"2026-10-29","2026-10-28");WriteDataset210(bad);Check210(OnInit()==INIT_PARAMETERS_INCORRECT,"B3 source from wrong prior session rejected");
 Reset210();string native_path="ModeloD_OPERATIONAL_"+MDContext612(1,"TEST",Instancia)+".ledger";std::ofstream(full(native_path))<<"LIVE_SENTINEL";
 bool prepared=true;AcceptOrders210(prepared);
 Check210(OnInit()==INIT_SUCCEEDED,"actual EA starts pinned single-day Tester dataset");
 string first_prefix=tester_prefix210;Check210(ledger_path!=native_path&&StringFind(ledger_path,"MDT210_")==0,"Tester ledger uses independent run namespace");
 Bootstrap210();
 Check210(mock_send_calls210==5,"all five eligible pending levels sent in one planning cycle");
 Check210(prepared,"every OrderSend observed durable phase-2 attempt on disk first");
 Check210(operational.nlevels==5&&operational.levels[0].order>0,"receipts reconciled through same integrated core");
 bool correct=true;for(auto r:mock_requests210)correct=correct&&r.action==TRADE_ACTION_PENDING&&r.type_filling==ORDER_FILLING_RETURN&&r.sl>0&&r.tp>0&&r.volume==1;
 Check210(correct,"pending requests preserve fixed SLTP, volume and RETURN filling");
 string native_text;MDOpReadFile(native_path,native_text);Check210(native_text=="LIVE_SENTINEL","native observation ledger remains byte-identical");
 Check210(stream615.audit.count==0&&coverage_last209=="CONFERIDA","first partial minute uses exact first tick, without waiting for or inventing M1");
 Check210(!operational.levels[0].consumed&&!operational.levels[1].consumed,"opening does not fabricate crossing from zero to all supports");
 int before=mock_send_calls210;Tick210();Check210(mock_send_calls210==before,"repeated timer does not duplicate accepted pending orders");
 Check210(MDLogicalMillis210()==(long)TimeCurrent()*1000,"retry clock follows simulated time");
 long wall=mock_mono,logical=MDLogicalMillis210();mock_utc+=600000;
 Check210(mock_mono==wall&&MDLogicalMillis210()==logical+600000,"accelerated replay advances retries independently of CPU time");
 OnDeinit(1);Reset210();Check210(OnInit()==INIT_SUCCEEDED&&tester_prefix210!=first_prefix,"new run does not inherit or overwrite earlier Tester state");
 MDOpClock clock;MDOpClockInit(clock);string why;for(int i=0;i<3;i++)MDOpClockRead(clock,0,why);
 Check210(clock.ok&&clock.offset==-10800&&clock.utc==clock.server+10800000,"simulated UTC/BRT conversion explicit despite host clock");
 mock_utc-=1000;Check210(!MDOpClockRead(clock,0,why),"simulated clock regression refused");mock_utc+=1000;
 MDDailyRaw614 raw;opening208.symbol="";mock_partial210=true;
 Check210(!MDTesterReadDaily210(DataTester,raw,why)&&!opening208.confirmed,"partial tick return with 4403 never confirms opening");
 mock_partial210=false;advance(4000);Check210(MDTesterReadDaily210(DataTester,raw,why)&&raw.first_last==210000,"controlled retry recovers exact positive opening tick");
 MDDataEvidence evidence;Check210(MDDailyBuild614(raw,evidence,why),"actual daily validator accepts synthetic internally consistent input");
 double old_high=raw.h;mock_daily_rates210.back().high=777777;mock_daily_rates210.back().close=999999;
 Check210(MDTesterReadDaily210(DataTester,raw,why)&&raw.h==old_high,"future HLC of current D1 are not used in daily inputs");
 MDStream615 stream;MDStreamStart615(stream,evidence);MDCoverage209 cover;string details;
 mock_stopped210=true;Check210(!MDCurrentCoverage209(stream,Begin210()+45000,cover,why,details,true),"manual stop rejects current-tail publication");mock_stopped210=false;
 opening208.symbol="";mock_ticks.clear();long cursor=Begin210();
 Check210(!MDOpeningRead208("WINZ26",cursor,cursor+32400000,cursor+45000,raw.first_msc,raw.first_last,why,MDLogicalMillis210(),true)&&opening208.cursor==cursor,"empty unfinished opening window cannot advance cursor");
 OnDeinit(1);Reset210();Check210(OnInit()==INIT_SUCCEEDED,"failure fixture initialized");
 mock_send210=[](const MqlTradeRequest &,MqlTradeResult &r){r.retcode=10031;return false;};Bootstrap210();before=mock_send_calls210;Tick210();
 Check210(before==5&&mock_send_calls210==before&&operational.levels[0].entry.phase==2,"uncertain API responses remain pending with no automatic resend");
 OnDeinit(1);Reset210();OnInit();
 for(int i=0;i<3;i++){string q;MDOpClockRead(opclock,0,q);}
 Daily(); // Freeze/validate daily data before injecting a persistence fault.
 MDOpFrame f;BuildFrame(f,true);MDOpState intents;MDOpCycle(operational,mock_book,f,intents,why);Commit(intents,"FIXTURE_INTENTS");
 fail_write210=true;MDTesterDispatch210();
 Check210(fatal&&mock_send_calls210==0,"failed PREPARE write blocks all sends and preserves prior journal");
 OnDeinit(1);Reset210();OnInit();SeedPositions210();prepared=true;
 mock_send210=[&prepared](const MqlTradeRequest &r,MqlTradeResult &v){prepared=prepared&&DiskPrepared210(r);for(int p=0;p<mock_book.book.positions;p++)if(mock_book.book.p[p].ticket==(long)r.position){mock_book.sl[p]=r.sl;mock_book.tp[p]=r.tp;}v.retcode=10009;return true;};
 MDTesterDispatch210();int sltp_count=0;bool fixed=true;
 for(auto r:mock_requests210)if(r.action==TRADE_ACTION_SLTP){sltp_count++;fixed=fixed&&r.sl==operational.levels[0].prices.sl_tick&&r.tp==operational.levels[0].prices.tp_tick;}
 Check210(sltp_count==2&&fixed&&prepared,"two proven positions get independent durable fixed SLTP requests");
 Check210(operational.positions[0].protect.phase==6&&operational.positions[1].protect.phase==6,"SLTP effects confirmed only by new inventory reads");
 OnDeinit(1);Reset210();OnInit();SeedPositions210();
 MDOpState cut=operational;cut.levels[0].cancel=true;cut.levels[0].closing=true;Commit(cut,"SYNTHETIC_CUTOFF");prepared=true;
 mock_send210=[&prepared](const MqlTradeRequest &r,MqlTradeResult &v){
  prepared=prepared&&DiskPrepared210(r);
  if(r.action==TRADE_ACTION_REMOVE){for(int k=0;k<mock_book.book.orders;k++)if(mock_book.book.o[k].order.ticket==(long)r.order){mock_book.book.o[k].order.state=1;mock_book.book.o[k].order.remaining=0;}v.retcode=10009;return true;}
  if(r.action==TRADE_ACTION_DEAL){
   int p=pos_index((long)r.position);long id=mock_book.book.p[p].identifier;int k=mock_book.book.orders++;
   MDRawOrder69 o;o.order.ticket=2000+k;o.order.magic=r.magic;o.order.symbol=r.symbol;o.order.buy=false;o.order.state=2;
   o.order.initial_volume=r.volume;o.order.remaining=0;o.setup_msc=(long)TimeCurrent()*1000;o.entry_limit=false;mock_book.book.o[k]=o;
   mock_book.orders[k].price=r.price;mock_book.orders[k].sl=0;mock_book.orders[k].tp=0;mock_book.orders[k].position_id=id;mock_book.orders[k].comment=r.comment;
   OPDeal(mock_book,100+mock_book.book.deals,o.order.ticket,id,1,r.volume,(long)TimeCurrent()*1000);mock_book.deal_price[mock_book.book.deals-1]=r.price;
   for(int j=p;j+1<mock_book.book.positions;j++){mock_book.book.p[j]=mock_book.book.p[j+1];mock_book.sl[j]=mock_book.sl[j+1];mock_book.tp[j]=mock_book.tp[j+1];}
   mock_book.book.positions--;v.retcode=10009;v.order=o.order.ticket;return true;
  }return false;
 };
 MDTesterDispatch210();int closes=0,cancels=0;for(auto r:mock_requests210){closes+=r.action==TRADE_ACTION_DEAL;cancels+=r.action==TRADE_ACTION_REMOVE;}
 Check210(closes==2&&cancels==1&&prepared,"cutoff closes both exact tickets and cancels only proven pending remainder");
 Check210(operational.positions[0].volume==0&&operational.positions[1].volume==0&&operational.levels[0].cancellation.phase==6,"close and cancel effects reconciled from complete chains");
 before=mock_send_calls210;MDTesterDispatch210();Check210(mock_send_calls210==before,"completed close/cancel actions cannot duplicate");
 mock_tester210=false;MDTesterDispatch210();Check210(mock_send_calls210==before,"runtime loss of Tester flag blocks every transport path");mock_tester210=true;
 OnDeinit(1);Reset210();prepared=true;AcceptOrders210(prepared);mock_connected=false;OnInit();Bootstrap210();
 Check210(mock_send_calls210==5&&prepared,"offline broker connection does not block historical simulated transport");
 OnDeinit(1);Reset210();OnInit();mock_partial210=true;Bootstrap210();
 Check210(mock_send_calls210==0&&operational.nlevels==0,"partial opening history cannot create levels or intentions");
 mock_partial210=false;advance(4000);prepared=true;AcceptOrders210(prepared);Tick210();
 Check210(mock_send_calls210==5&&prepared,"later opening recovery plans once without resetting prior history state");
 OnDeinit(1);Reset210();OnInit();mock_send210=[](const MqlTradeRequest &,MqlTradeResult &r){r.retcode=10019;return true;};Bootstrap210();before=mock_send_calls210;Tick210();
 Check210(before==5&&mock_send_calls210==before&&operational.levels[0].entry.phase==5,"definitive rejection cannot become automatic new request");
 OnDeinit(1);Reset210();OnInit();for(int i=0;i<3;i++){string q;MDOpClockRead(opclock,0,q);}Daily();
 mock_unstable=true;MDTesterDispatch210();Check210(mock_send_calls210==0,"divergent inventory reads block Tester dispatch");mock_unstable=false;
 mock_stopped210=true;MDTesterDispatch210();Check210(mock_send_calls210==0,"manual interruption before dispatch cannot send");mock_stopped210=false;
 flip_guard210=true;MDTesterDispatch210();Check210(mock_send_calls210==0&&operational.levels[0].entry.phase==2,"loss of Tester flag during PREPARE cannot grant send permit");
 mock_tester210=true;OnDeinit(1);Reset210();OnInit();for(int i=0;i<3;i++){string q;MDOpClockRead(opclock,0,q);}Daily();
 delay_write210=true;MDTesterDispatch210();Check210(mock_send_calls210==0&&operational.levels[0].entry.phase==2,"slow durable write expires send permit instead of using stale snapshot");
 OnDeinit(1);Print("FOCUSED_210;Checks=",checks210,";Failures=",failures210,";API_MOCK_NOT_NATIVE_MQL5");return failures210?1:0;
}
