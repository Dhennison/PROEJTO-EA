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
 mock_expiration_modes211=SYMBOL_EXPIRATION_GTC;mock_expiration_error211=false;mock_currency211="BRL";
 if(lock615!=INVALID_HANDLE)OnDeinit(1);
 fatal=false;owns615=false;report_error=false;stream_started615=false;stream_failed615=false;stream_reported615=-1;
 last_status="";stream_retries615=0;mock_tester210=true;ExecutarNoTester=true;mock_optimization210=false;
 UsarFonteImportadaNoTester=false;DataTester=20261030;ContratoTester="WINZ26";FusoServidorTester=-10800;_Symbol="WINZ26";
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
int baseline211(){
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
 string first_prefix=tester_prefix210;Check210(ledger_path!=native_path&&StringFind(ledger_path,"MDT211_FUNC_")==0,"Tester ledger uses independent run namespace");
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

void PhysicalBook211(){
 for(int i=0;i<mock_book.book.orders;i++)mock_book.book.o[i].order.symbol=MD_FONTE211;
 for(int i=0;i<mock_book.book.positions;i++)mock_book.book.p[i].symbol=MD_FONTE211;
 for(int i=0;i<mock_book.book.deals;i++)mock_book.book.d[i].symbol=MD_FONTE211;
}
int main(){
 int baseline=baseline211();if(baseline)return baseline;
 Reset210();UsarFonteImportadaNoTester=true;_Symbol=MD_FONTE211;
 bool prepared=true;AcceptOrders210(prepared);
 Check210(OnInit()==INIT_SUCCEEDED,"functional EA starts with existing imported WIN dataset");
 Bootstrap210();Check210(mock_send_calls210==5&&prepared,"functional bridge sends five eligible pending orders after durable prepare");
 bool physical=true;for(auto r:mock_requests210)physical=physical&&r.symbol==MD_FONTE211;
 Check210(physical,"broker receives only physical custom symbol in Tester");
 bool logical=operational.nlevels==5;for(int k=0;k<operational.nlevels;k++)logical=logical&&operational.levels[k].symbol=="WINZ26"&&operational.levels[k].order>0;
 Check210(logical,"core keeps WINZ26 identity and reconciles physical receipts");
 long expiry211=0;MDSymbolInfoInteger211("WINZ26",SYMBOL_EXPIRATION_TIME,expiry211);
 string description211;
 Check210(MDSymbolInfoString211("WINZ26",0,description211)&&description211=="BRL"&&mock_last_symbol211=="MD_PESQ_WINZ26_DIA1030","three-argument string property preserves output and physical route");
 mock_string_failure211=true;
 Check210(!MDSymbolInfoString211("WIN$N",0,description211)&&mock_last_symbol211=="WIN$N","three-argument string property preserves failure and unmapped identity");
 mock_string_failure211=false;
 MDSymbolInfoInteger211("WINZ26",SYMBOL_EXPIRATION_TIME,expiry211);
 Check210(mock_last_symbol211=="WINZ26"&&expiry211==MDCivilMidnight2026(20261216)/1000,"expiry belongs to real underlying contract, not internal custom name");
 std::vector<MqlRates> rates;CopyRates("WINZ26",PERIOD_D1,0,3,rates);
 Check210(mock_last_symbol211=="WINZ26","D1 remains original same-contract reference");
 MDCopyRates211("WINZ26",PERIOD_M1,(datetime)(Begin210()/1000),(datetime)(Begin210()/1000+59),rates);
 Check210(mock_last_symbol211==MD_FONTE211,"M1 uses imported execution tape");
 std::vector<MqlTick> ticks;MDCopyTicksRange211("WINZ26",ticks,COPY_TICKS_TRADE,(ulong)Begin210(),(ulong)Begin210()+59999);
 Check210(mock_last_symbol211==MD_FONTE211,"opening and touch ticks use physical source");
 double margin=0;MDOrderCalcMargin211(ORDER_TYPE_BUY,"WINZ26",1,210000,margin);
 Check210(mock_last_symbol211==MD_FONTE211,"margin calculated for actual simulated traded symbol");
 string value;MDOrderGetString211(ORDER_SYMBOL,value);Check210(value=="WINZ26","order identity normalized");
 MDHistoryOrderGetString211(1,ORDER_SYMBOL,value);Check210(value=="WINZ26","historical order identity normalized");
 MDHistoryDealGetString211(1,DEAL_SYMBOL,value);Check210(value=="WINZ26","deal identity normalized");
 MDPositionGetString211(POSITION_SYMBOL,value);Check210(value=="WINZ26","position identity normalized");
 MDOrderGetString211(ORDER_COMMENT,value);Check210(value==MD_FONTE211,"unrelated string properties not rewritten");
 MqlTradeRequest request;MqlTradeResult response;request.symbol="WDOZ26";int before=mock_send_calls210;
 Check210(!MDOrderSend211(request,response)&&mock_send_calls210==before,"bridge refuses foreign-contract request");
 mock_tester210=false;request.symbol="WINZ26";
 Check210(!MDOrderSend211(request,response)&&mock_send_calls210==before,"bridge cannot send to live connected account");
 mock_tester210=true;_Symbol="OUTRO";
 Check210(!MDOrderSend211(request,response)&&mock_send_calls210==before,"source context change revokes bridge");
 OnDeinit(1);Reset210();UsarFonteImportadaNoTester=true;_Symbol="WINZ26";
 Check210(OnInit()==INIT_PARAMETERS_INCORRECT,"import opt-in cannot silently run on original failing feed");
 OnDeinit(1);Reset210();UsarFonteImportadaNoTester=true;_Symbol=MD_FONTE211;OnInit();SeedPositions210();PhysicalBook211();prepared=true;
 mock_send210=[&prepared](const MqlTradeRequest &r,MqlTradeResult &v){prepared=prepared&&DiskPrepared210(r);for(int p=0;p<mock_book.book.positions;p++)if(mock_book.book.p[p].ticket==(long)r.position){mock_book.sl[p]=r.sl;mock_book.tp[p]=r.tp;}v.retcode=10009;return true;};
 MDTesterDispatch210();int sltp_count=0;bool fixed=true;
 for(auto r:mock_requests210)if(r.action==TRADE_ACTION_SLTP){sltp_count++;fixed=fixed&&r.sl==operational.levels[0].prices.sl_tick&&r.tp==operational.levels[0].prices.tp_tick;}
 Check210(sltp_count==2&&fixed&&prepared,"two proven positions get independent durable fixed SLTP requests");
 Check210(operational.positions[0].protect.phase==6&&operational.positions[1].protect.phase==6,"SLTP effects confirmed only by new inventory reads");
 OnDeinit(1);Reset210();UsarFonteImportadaNoTester=true;_Symbol=MD_FONTE211;OnInit();SeedPositions210();PhysicalBook211();
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
 bool routed_all=true;for(auto r:mock_requests210)routed_all=routed_all&&r.symbol==MD_FONTE211;
 Check210(routed_all,"SLTP close and cancellation preserve physical-symbol route and ticket ownership");
 OnDeinit(1);
 Reset210();UsarFonteImportadaNoTester=true;_Symbol=MD_FONTE211;mock_currency211="USD";
 Check210(OnInit()==INIT_PARAMETERS_INCORRECT&&mock_send_calls210==0,"USD functional run blocks before sends rather than requesting absent conversion");
 Reset210();UsarFonteImportadaNoTester=true;_Symbol=MD_FONTE211;mock_expiration_modes211=SYMBOL_EXPIRATION_DAY;
 prepared=true;AcceptOrders210(prepared);Check210(OnInit()==INIT_SUCCEEDED,"BRL day-only fixture initializes");Bootstrap210();
 bool day=mock_requests210.size()==5;for(auto r:mock_requests210)day=day&&r.type_time==ORDER_TIME_DAY&&r.expiration==0&&r.sl>0&&r.tp>0;
 Check210(day&&prepared,"day-only symbol receives five DAY pending requests with original SLTP and durable prepare");
 MqlTradeRequest validity;string why_validity;MDOpLevel level=operational.levels[0];
 mock_expiration_modes211=SYMBOL_EXPIRATION_GTC|SYMBOL_EXPIRATION_DAY;
 Check210(MDTesterExpiration211(level,validity,why_validity)&&validity.type_time==ORDER_TIME_GTC&&validity.expiration==0,"GTC used only when supported");
 mock_expiration_modes211=SYMBOL_EXPIRATION_SPECIFIED;
 Check210(MDTesterExpiration211(level,validity,why_validity)&&validity.type_time==ORDER_TIME_SPECIFIED&&validity.expiration==level.cutoff_utc/1000+FusoServidorTester,"specified expiry maps UTC model cutoff to server seconds");
 level.cutoff_utc=(long)TimeCurrent()*1000-(long)FusoServidorTester*1000;
 Check210(!MDTesterExpiration211(level,validity,why_validity)&&why_validity=="TESTER_EXPIRATION_CUTOFF_PASSED","specified expiry refuses elapsed cutoff");
 mock_expiration_modes211=8;
 Check210(!MDTesterExpiration211(level,validity,why_validity)&&why_validity=="TESTER_EXPIRATION_MODE_UNSUPPORTED","unsupported expiry blocks without guessing");
 mock_expiration_error211=true;
 Check210(!MDTesterExpiration211(level,validity,why_validity)&&why_validity=="TESTER_EXPIRATION_PROPERTIES_UNAVAILABLE","expiry property read failure blocks");
 OnDeinit(1);
 // Regression of the real cancellation incident: wait for entry, not merely a price beyond TP.
 Reset210();UsarFonteImportadaNoTester=true;_Symbol=MD_FONTE211;prepared=true;AcceptOrders210(prepared);OnInit();Bootstrap210();
 int accepted_count=mock_send_calls210;Tick210();Tick210();
 bool waiting=mock_send_calls210==accepted_count&&mock_book.book.orders==5;
 for(int k=0;k<operational.nlevels;k++)waiting=waiting&&!operational.levels[k].consumed&&!operational.levels[k].cancel;
 Check210(waiting,"accepted pending limits remain active before entry touch; next timers cannot cancel all five merely beyond TP");
 OnDeinit(1);Reset210();
 MDLevel pprice{};pprice.entry=100;pprice.sl=90;pprice.tp=110;pprice.buy=true;
 MDOpTrail path;string path_why;
 mock_ticks={{159999,150,8},{160001,149,8},{160002,148,8}};
 MDOpTrailInit(path,"WINZ26",160000,pprice,true);
 Check210(MDOpTrailRead(path,160003,path_why)&&!path.boundary&&!path.entry_seen,"buy pending beyond TP at acceptance is not a post-touch boundary");
 mock_ticks.push_back({160003,105,8});
 Check210(MDOpTrailRead(path,160004,path_why)&&!path.boundary&&!path.entry_seen,"crossing TP on approach to buy entry cannot consume an untouched limit");
 mock_ticks.push_back({160004,100,8});
 Check210(MDOpTrailRead(path,160005,path_why)&&path.entry_seen&&!path.boundary,"entry touch without fill leaves previously accepted pending valid");
 mock_ticks.push_back({160005,111,8});
 Check210(MDOpTrailRead(path,160006,path_why)&&path.boundary,"TP crossing after missed entry touch still cancels pending");
 pprice.buy=false;pprice.sl=110;pprice.tp=90;
 mock_ticks={{159999,50,8},{160001,95,8},{160002,100,8},{160003,89,8}};
 MDOpTrailInit(path,"WINZ26",160000,pprice,true);
 Check210(MDOpTrailRead(path,160002,path_why)&&!path.boundary&&!path.entry_seen,"sell approach across TP is not post-entry cancellation evidence");
 Check210(MDOpTrailRead(path,160004,path_why)&&path.entry_seen&&path.boundary,"sell target after missed entry touch remains cancellation evidence");
 pprice.buy=true;pprice.sl=90;pprice.tp=110;
 mock_ticks={{159999,150,8},{160001,80,8}};MDOpTrailInit(path,"WINZ26",160000,pprice,true);
 Check210(MDOpTrailRead(path,160002,path_why)&&path.entry_seen&&path.boundary,"gap across entry and stop cannot leave pending active");
 mock_ticks={{160001,99,8}};MDOpTrailInit(path,"WINZ26",160000,pprice,true);
 Check210(!MDOpTrailRead(path,160002,path_why)&&path_why=="TRAIL_PENDING_ANCHOR_MISSING"&&path.cursor==160001,"missing acceptance anchor blocks rather than assuming no crossing");
 mock_ticks={{160000,90,8},{160001,89,8}};MDOpTrailInit(path,"WINZ26",160000,pprice,true);
 Check210(!MDOpTrailRead(path,160002,path_why)&&path.ambiguous,"same-millisecond acceptance and boundary remain unproven");
 mock_ticks={{160001,80,8}};MDOpTrailInit(path,"WINZ26",160000,pprice);
 Check210(MDOpTrailRead(path,160002,path_why)&&path.boundary,"filled-position protection still detects a post-fill price beyond stop");
 mock_ticks={{160000,110,8},{160001,111,8}};MDOpTrailInit(path,"WINZ26",160000,pprice,true);
 Check210(MDOpTrailRead(path,160002,path_why)&&!path.boundary&&!path.ambiguous&&!path.entry_seen,"TP equality at acceptance without entry touch is not a post-entry boundary");
 // Exact original 09:01 sequence from CSV, including timestamp ties, not a synthetic replacement.
 Reset210();UsarFonteImportadaNoTester=true;_Symbol=MD_FONTE211;OnInit();Bootstrap210();
 mock_ticks={{Begin210()+45001,999999,0}};
 mock_all_ticks={{Begin210()+45001,171300,0},{Begin210()+45002,171305,2},{Begin210()+45003,171310,56}};
 std::vector<MqlTick> filtered;ResetLastError();
 Check210(MDCopyTicksRange211("WINZ26",filtered,COPY_TICKS_TRADE,Begin210()+45000,Begin210()+45999)==1&&filtered[0].last==171310&&filtered[0].flags==56,"imported trade query uses ALL and excludes carried Last and quote-only records");
 mock_partial210=true;ResetLastError();
 MDCopyTicksRange211("WINZ26",filtered,COPY_TICKS_TRADE,Begin210()+45000,Begin210()+45999);
 Check210(GetLastError()==4403,"filtered trade adapter preserves incomplete-query error");mock_partial210=false;
 MDDataEvidence original_evidence=obs615.data;
 std::ifstream original_minute("ORIGINAL_MINUTE_PATH");std::vector<MqlTick> original;long stamp;double price_value;uint flag_value;
 while(original_minute>>stamp>>price_value>>flag_value)original.push_back({stamp,price_value,flag_value});
 const long minute=1793350860000;
 mock_utc=minute+60000+10800000;
 Check210(original.size()==26687&&MDReferenceMinute211(minute,original,original.size()),"original CSV 09:01 passes count OHLC and both ordered timestamp-price-flag hashes");
 auto damaged=original;damaged.erase(damaged.begin()+20);
 Check210(!MDReferenceMinute211(minute,damaged,damaged.size()),"missing interior trade cannot pass frozen reference");
 damaged=original;damaged[20].last+=5;
 Check210(!MDReferenceMinute211(minute,damaged,damaged.size()),"modified interior trade cannot pass frozen reference");
 damaged=original;std::swap(damaged[0],damaged[1]);
 Check210(!MDReferenceMinute211(minute,damaged,damaged.size()),"reordered same-millisecond trades cannot pass frozen reference");
 UsarFonteImportadaNoTester=false;
 Check210(!MDReferenceMinute211(minute,original,original.size()),"frozen reference cannot override original symbol or live context");UsarFonteImportadaNoTester=true;
 mock_utc=minute+59999+10800000;
 Check210(!MDReferenceMinute211(minute,original,original.size()),"future minute cannot be certified from preloaded reference");mock_utc=minute+60000+10800000;
 original_evidence.open_msc=minute;original_evidence.values.open_today=171315;
 original_evidence.session.scheduled_open=9*3600+60;
 MDStream615 reference_stream;Check210(MDStreamStart615(reference_stream,original_evidence),"closed-minute integration fixture starts");
 mock_ticks=original;mock_all_ticks=original;mock_rates={{minute/1000,171330,171480,170730,171255}};
 MDStream615 source_stream=reference_stream;
 Check210(MDStreamCollect615(reference_stream,minute+59999,path_why)&&reference_stream.cursor==minute+60000&&reference_stream.audit.minutes[0].o==171315,"actual stream advances on exact original sequence despite mutated native M1 open");
 MDStream615 recovered;
 Check210(MDStreamRecoverAll615(source_stream,minute+59999,false,recovered,path_why)&&recovered.cursor==minute+60000,"ALL producer uses the same exact immutable-reference check");
 MDCoverage209 original_cover;string details;
 Check210(MDCurrentCoverage209(source_stream,minute+60000,original_cover,path_why,details,true),"current coverage accepts exact original minute without rewriting native M1");
 MDOpTrailInit(path,"WINZ26",minute-1,pprice);
 Check210(MDOpTrailRead(path,minute+60000,path_why)&&path.cursor==minute+60000,"position trail audits the same immutable original minute");
 mock_ticks=original;mock_ticks.erase(mock_ticks.begin()+20);mock_all_ticks=mock_ticks;
 MDStream615 refused=source_stream;
 Check210(!MDStreamCollect615(refused,minute+59999,path_why)&&refused.cursor==minute,"stream with missing trade and mismatching native M1 remains blocked");
 Check210(!MDCurrentCoverage209(source_stream,minute+60000,original_cover,path_why,details,true),"current coverage cannot bypass integrity with an incomplete original minute");
 OnDeinit(1);
 std::cout<<"FOCUSED_211;Checks="<<checks210<<";Failures="<<failures210<<";API_MOCK_NOT_NATIVE_MQL5\n";
 return failures210?1:0;
}
