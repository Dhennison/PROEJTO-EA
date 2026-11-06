int checks213=0,failures213=0;
void Check213(bool ok,string text){checks213++;if(!ok)failures213++;Print(ok?"PASS_213;":"FAIL_213;",text);}
long Day213(){return MDCivilMidnight2026(20261104);}
long Begin213(){return Day213()+9*3600000;}
void WriteB3213(string text){std::ofstream out(full("ajuste_b3.txt"));out<<text;}
string B3213(){return "DataFonte=2026-11-03\nDataOperacional=2026-11-04\nFonte=BVBG.187.01\nStatus=OK\nQuantidadeContratos=1\nContrato.WINZ26.Ajuste=210000\nContrato.WINZ26.AjusteAnterior=210000\n";}
void EmptyBook213(){
 mock_book=MDOpSnapshot{};mock_book.book.complete=true;mock_book.book.connected=true;mock_book.book.hedge=true;
 mock_book.book.account_key=MDAccount213();mock_book.book.server_key=MDServer213();mock_book.execution_prices_known=true;
}
void Reset213(){
 if(lock615!=INVALID_HANDLE)OnDeinit(1);
 // A test fixture starts with a clean account journal; production code never removes these files.
 std::filesystem::remove_all("/tmp/md615k_host");std::filesystem::create_directories("/tmp/md615k_host");
 fatal=false;owns615=false;report_error=false;stream_started615=false;stream_failed615=false;stream_reported615=-1;last_status="";stream_retries615=0;
 mock_freeze21305=0;mock_terminal_state21305=-1;mock_profit21305.clear();mock_reason21305.clear();mock_cost_error21305=false;
 mock_tester210=false;mock_optimization210=false;mock_mode213=ACCOUNT_TRADE_MODE_DEMO;mock_login210=444;mock_server210="BROKER-DEMO";
 mock_hedge210=true;mock_currency211="BRL";mock_connected=true;mock_terminal_algo213=true;mock_ea_algo213=true;mock_account_trade213=true;mock_account_ea213=true;
 mock_unstable=false;mock_tick_error=false;mock_partial210=false;mock_stopped210=false;mock_price_error=false;mock_margin_ok=true;mock_free_margin=100000000;
 mock_custom213=false;mock_flip_on_symbol213=false;mock_description_failure213=false;mock_description213="IBOVESPA MINI(WINZ26)";
 mock_session_begin213=9*3600;mock_session_end213=18*3600+55*60;mock_session_available213=true;
 mock_calls=0;mock_send_calls210=0;mock_send210=nullptr;mock_requests210.clear();mock_expiration_modes211=SYMBOL_EXPIRATION_DAY;
 ExecutarNaDemo=true;Instancia=1;VolumePorNivel=1;IntervaloSegundos=2;
 demo_bound_account213=0;demo_bound_server213="";
 mock_utc=Begin213()+10800000+45000;mock_mono=10000;opening208.symbol="";mock_broker_fresh=true;
 mock_ticks={{Begin213()+1000,210000,8}};mock_all_ticks=mock_ticks;mock_rates.clear();
 long prior=MDCivilMidnight2026(20261103)/1000;
 mock_daily_rates210={{MDCivilMidnight2026(20261030)/1000,210000,211000,209000,210000},
  {prior,210000,211000,209000,210000},{Day213()/1000,210000,999999,1,888888}};
 for(int k=0;k<MDOP_LEVELS;k++)pending_trail_started[k]=false;
 for(int p=0;p<MDOP_POSITIONS;p++)position_trail_started[p]=false;
 EmptyBook213();WriteB3213(B3213());
}
void Timer213(){OnTimer();advance(2000);}
void Bootstrap213(){Timer213();Timer213();Timer213();}
bool Prepared213(const MqlTradeRequest &r){
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
void Accept213(bool &prepared){
 mock_send210=[&prepared](const MqlTradeRequest &r,MqlTradeResult &v){
  prepared=prepared&&Prepared213(r);int k=mock_book.book.orders++;long ticket=1000+k;
  MDRawOrder69 o;o.order.ticket=ticket;o.order.magic=r.magic;o.order.symbol=r.symbol;o.order.buy=r.type==ORDER_TYPE_BUY_LIMIT;
  o.order.state=0;o.order.initial_volume=r.volume;o.order.remaining=r.volume;o.setup_msc=(long)TimeCurrent()*1000;o.entry_limit=true;
  mock_book.book.o[k]=o;mock_book.orders[k].price=r.price;mock_book.orders[k].sl=r.sl;mock_book.orders[k].tp=r.tp;
  mock_book.orders[k].position_id=0;mock_book.orders[k].comment=r.comment;v.retcode=10008;v.order=ticket;return true;
 };
}
void Seed213(){
 MDOpState seed;MDOpFrame f;OPFilled(seed,mock_book,f);seed.scope=Scope615();
 mock_book.book.account_key=MDAccount213();mock_book.book.server_key=MDServer213();
 long shift=Begin213()-100000;
 for(int k=0;k<seed.nlevels;k++){
  seed.levels[k].date=20261104;seed.levels[k].key=202611040+k;seed.levels[k].cutoff_utc=Day213()+75600000;
  seed.levels[k].open_server+=shift;if(seed.levels[k].accepted_server>0)seed.levels[k].accepted_server+=shift;
  if(seed.levels[k].touch_server>0)seed.levels[k].touch_server+=shift;
  if(seed.levels[k].entry.started>0)seed.levels[k].entry.started+=shift+10800000;
  if(seed.levels[k].entry.completed>0)seed.levels[k].entry.completed+=shift+10800000;
 }
 for(int p=0;p<seed.npositions;p++)seed.positions[p].first_server+=shift;
 for(int o=0;o<mock_book.book.orders;o++)mock_book.book.o[o].setup_msc+=shift;
 mock_book.orders[0].comment=MDOpComment(seed.levels[0]);
 for(int d=0;d<mock_book.book.deals;d++){mock_book.book.d[d].msc+=shift;mock_book.deal_price[d]=seed.levels[0].prices.entry_tick;}
 for(int k=0;k<seed.nlevels;k++){
  seed.levels[k].deal_receipts="";
  for(int d=0;d<mock_book.book.deals;d++)if(mock_book.book.d[d].order==seed.levels[k].order)
   seed.levels[k].deal_receipts+=MDOpDealReceipt(mock_book.book.d[d],true,mock_book.deal_price[d]);
 }
 long now=Begin213()+62000;mock_mono+=now-(long)TimeCurrent()*1000;mock_utc=now+10800000;
 mock_book.server_msc=now;seed.watermark=now+10800000-1000;
 mock_ticks={{Begin213(),209500,8},{Begin213()+60000,207375,8},{Begin213()+61000,207400,8}};
 for(auto &q:mock_ticks){q.bid=q.last-5;q.ask=q.last;}
 mock_all_ticks=mock_ticks;
 Check213(Commit(seed,"SYNTHETIC_OWNED_POSITIONS"),"proven two-position fixture committed to demo ledger");
 mock_description_failure213=true;
 for(int i=0;i<3;i++){string why;MDOpClockRead(opclock,operational.watermark,why);advance(2000);}
}
int regression213(){
 std::cout.setf(std::ios::unitbuf);
 Reset213();mock_mode213=ACCOUNT_TRADE_MODE_REAL;Check213(OnInit()==INIT_PARAMETERS_INCORRECT&&mock_send_calls210==0,"real account refused before ledger and any API send");
 Reset213();mock_mode213=ACCOUNT_TRADE_MODE_CONTEST;Check213(OnInit()==INIT_PARAMETERS_INCORRECT,"contest account cannot masquerade as demo");
 Reset213();mock_tester210=true;Check213(OnInit()==INIT_PARAMETERS_INCORRECT,"demo package refuses Tester context");
 Reset213();mock_login210=0;Check213(OnInit()==INIT_PARAMETERS_INCORRECT,"unidentified login cannot count as demo");
 Reset213();mock_hedge210=false;Check213(OnInit()==INIT_PARAMETERS_INCORRECT,"netting is refused");
 Reset213();mock_currency211="USD";Check213(OnInit()==INIT_PARAMETERS_INCORRECT,"unsupported account currency refused without rewriting broker properties");
 Reset213();IntervaloSegundos=30;Check213(OnInit()==INIT_PARAMETERS_INCORRECT,"operational demo pins two-second management timer");
 Reset213();mock_custom213=true;Check213(OnInit()==INIT_PARAMETERS_INCORRECT,"custom chart cannot enter operational demo");
 Reset213();ExecutarNaDemo=false;Check213(OnInit()==INIT_SUCCEEDED,"demo observation mode can initialize");Bootstrap213();Check213(mock_send_calls210==0,"default observation cannot send any request");
 Reset213();bool prepared=true;Accept213(prepared);Check213(OnInit()==INIT_SUCCEEDED,"current-day demo initializes outside Tester");Bootstrap213();
 Check213(!MDIsTester210()&&mock_send_calls210==5&&prepared,"five native-demo limit requests pass durable prepare and real account identity");
 if(mock_requests210.size()!=5){Print("DEMO_213;EARLY_FAILURE;missing expected native demo requests");return 1;}
 bool exact=true;for(auto q:mock_requests210)exact=exact&&q.symbol=="WINZ26"&&q.type_time==ORDER_TIME_DAY&&q.sl>0&&q.tp>0&&q.volume==1;
 Check213(demo_sent213==5&&demo_native_called213,"send metrics count actual native API invocations");
 Check213(exact,"actual contract and fixed SLTP are preserved with supported expiration");
 Check213(operational.scope==MDContext612(444,"BROKER-DEMO",1)&&operational.levels[0].order>0,"broker receipts reconcile under real demo login and server, not virtual Tester scope");
 Check213(obs615.data.date==20261104&&obs615.data.previous_date==20261103&&obs615.data.session.normal_end==18*3600+55*60,"live daily reader accepts current B3 cycle and current broker session beyond old October pin");
 int second_lock=FileOpen(demo_prefix213+"ModeloD_OPERATIONAL_"+Scope615()+".lock",FILE_READ|FILE_WRITE|FILE_BIN|FILE_COMMON);
 Check213(second_lock==INVALID_HANDLE,"same account server and instance cannot acquire a second exclusive lock");if(second_lock!=INVALID_HANDLE)FileClose(second_lock);
 int before=mock_send_calls210;Timer213();Check213(mock_send_calls210==before&&!operational.levels[0].cancel,"waiting pending cannot be cancelled merely beyond its TP");
 string persistent=ledger_path;OnDeinit(1);Check213(OnInit()==INIT_SUCCEEDED&&ledger_path==persistent,"restart recovers same stable demo journal");Bootstrap213();Check213(mock_send_calls210==before&&operational.levels[0].order>0,"restart cannot duplicate previously accepted pending orders");
 MqlTradeRequest bad{};MqlTradeResult answer{};bad.action=TRADE_ACTION_DEAL;bad.symbol="WINZ26";bad.volume=1;
 Check213(!MDDemoOrderSend213(bad,answer)&&mock_send_calls210==before,"unowned market entry cannot reach native API");
 bad=mock_requests210[0];bad.order=987654;bad.action=TRADE_ACTION_REMOVE;Check213(!MDDemoOrderSend213(bad,answer),"foreign pending ticket cannot be cancelled");
 bad=mock_requests210[0];bad.symbol="WDOZ26";Check213(!MDDemoOrderSend213(bad,answer),"foreign contract rejected by owned-action proof");
 Reset213();mock_terminal_algo213=false;OnInit();Bootstrap213();Check213(mock_send_calls210==0,"terminal Algo Trading disabled blocks sends");
 Reset213();mock_ea_algo213=false;OnInit();Bootstrap213();Check213(mock_send_calls210==0,"EA algorithm permission disabled blocks sends");
 Reset213();mock_account_ea213=false;OnInit();Bootstrap213();Check213(mock_send_calls210==0,"broker expert permission blocks sends");
 Reset213();mock_account_trade213=false;OnInit();Bootstrap213();Check213(mock_send_calls210==0,"broker trading permission blocks sends");
 Reset213();mock_connected=false;OnInit();Bootstrap213();Check213(mock_send_calls210==0,"disconnection cannot send");
 Reset213();mock_session_available213=false;OnInit();Bootstrap213();Check213(mock_send_calls210==0,"missing current trade session blocks November entries rather than extrapolating October snapshot");
 Reset213();mock_session_end213=17*3600;OnInit();Bootstrap213();Check213(mock_send_calls210==0,"session shorter than model cutoff is refused");
 Reset213();WriteB3213("DataFonte=2026-10-29\nDataOperacional=2026-10-30\nFonte=BVBG.187.01\nStatus=OK\nQuantidadeContratos=1\nContrato.WINZ26.Ajuste=210000\nContrato.WINZ26.AjusteAnterior=210000\n");OnInit();Bootstrap213();Check213(mock_send_calls210==0,"stale B3 cycle cannot create orders");
 Reset213();OnInit();mock_send210=[](const MqlTradeRequest &,MqlTradeResult &r){r.retcode=10031;return false;};Bootstrap213();before=mock_send_calls210;Timer213();Check213(before==5&&mock_send_calls210==before&&operational.levels[0].entry.phase==2,"uncertain broker response persists without automatic resend");
 Reset213();OnInit();flip_guard210=true;Bootstrap213();Check213(mock_send_calls210==0,"account mode flip to real during PREPARE revokes the final send permit");
 Reset213();OnInit();fail_write210=true;Bootstrap213();Check213(mock_send_calls210==0,"failed durable write prevents all API calls");
 Reset213();OnInit();mock_login210++;Timer213();Check213(fatal&&mock_send_calls210==0,"account switch invalidates running instance");
 // Missing daily source does not disable management of known, proven positions.
 Reset213();OnInit();Seed213();prepared=true;
 mock_send210=[&prepared](const MqlTradeRequest &r,MqlTradeResult &v){prepared=prepared&&Prepared213(r);for(int p=0;p<mock_book.book.positions;p++)if(mock_book.book.p[p].ticket==(long)r.position){mock_book.sl[p]=r.sl;mock_book.tp[p]=r.tp;}v.retcode=10009;return true;};
 MDDemoDispatch213();int protection=0;for(auto q:mock_requests210)protection+=q.action==TRADE_ACTION_SLTP;
 Check213(protection==2&&prepared&&operational.positions[0].protect.phase==6&&operational.positions[1].protect.phase==6,"two owned hedge tickets get fixed protection and observed confirmation with daily source unavailable");
 string resume_path=ledger_path;OnDeinit(1);Check213(OnInit()==INIT_SUCCEEDED&&ledger_path==resume_path&&operational.npositions==2,"restart recovers exposure and protection state without resetting provenance");
 before=mock_send_calls210;for(int i=0;i<3;i++){Timer213();}Check213(mock_send_calls210==before,"already observed protection is not sent again after restart");
 // Force only the observed clock to the real model cutoff; no direct close intention is seeded.
 long target=Day213()+18*3600000,delta=target-(long)TimeCurrent()*1000;mock_utc+=delta;mock_mono+=delta;
 mock_send210=[&prepared](const MqlTradeRequest &r,MqlTradeResult &v){
  prepared=prepared&&Prepared213(r);
  if(r.action==TRADE_ACTION_REMOVE){for(int k=0;k<mock_book.book.orders;k++)if(mock_book.book.o[k].order.ticket==(long)r.order){mock_book.book.o[k].order.state=1;mock_book.book.o[k].order.remaining=0;}v.retcode=10009;return true;}
  if(r.action==TRADE_ACTION_DEAL){int p=pos_index(r.position);if(p<0)return false;long id=mock_book.book.p[p].identifier;int k=mock_book.book.orders++;
   MDRawOrder69 o;o.order.ticket=2000+k;o.order.magic=r.magic;o.order.symbol=r.symbol;o.order.buy=false;o.order.state=2;o.order.initial_volume=r.volume;o.order.remaining=0;o.setup_msc=(long)TimeCurrent()*1000;o.entry_limit=false;mock_book.book.o[k]=o;
   mock_book.orders[k].price=r.price;mock_book.orders[k].sl=0;mock_book.orders[k].tp=0;mock_book.orders[k].position_id=id;mock_book.orders[k].comment=r.comment;
   OPDeal(mock_book,100+mock_book.book.deals,o.order.ticket,id,1,r.volume,(long)TimeCurrent()*1000);mock_book.deal_price[mock_book.book.deals-1]=r.price;
   for(int j=p;j+1<mock_book.book.positions;j++){mock_book.book.p[j]=mock_book.book.p[j+1];mock_book.sl[j]=mock_book.sl[j+1];mock_book.tp[j]=mock_book.tp[j+1];}mock_book.book.positions--;
   v.retcode=10009;v.order=o.order.ticket;return true;
  }return false;
 };
 Timer213();int closes=0,cancels=0;for(auto q:mock_requests210){closes+=q.action==TRADE_ACTION_DEAL;cancels+=q.action==TRADE_ACTION_REMOVE;}
 Check213(closes==2&&cancels==1&&prepared,"native-demo adapter closes two exact tickets and cancels proven pending at cutoff through normal timer");
 Check213(operational.positions[0].volume==0&&operational.positions[1].volume==0&&operational.positions[0].close.phase==6,"exit receipts confirm flat exposure");
 before=mock_send_calls210;Timer213();Check213(mock_send_calls210==before,"subsequent cutoff timer does not duplicate completed actions");
 // Revoke permission inside the actual native wrapper even when a valid action remains in flight.
 Reset213();OnInit();Seed213();MDOpState inflight=operational;inflight.positions[0].closing=true;MDOpIntent(inflight.positions[0].close,4,inflight.positions[0].ticket,inflight.positions[0].identifier,inflight.positions[0].volume,0);
 Check213(MDOpBegin(inflight,0,0,4,opclock.utc,true,true)&&Commit(inflight,"VALID_INFLIGHT_WRAPPER_FIXTURE"),"valid in-flight owned close fixture is durable");
 MqlTradeRequest r;string reason;Check213(MDDemoRequest213(operational,0,0,4,r,reason)&&MDDemoOwnedRequest213(r),"owned-request proof accepts actual bound close before revocation");
 mock_flip_on_symbol213=true;before=mock_send_calls210;
 Check213(!MDDemoOrderSend213(r,answer)&&!demo_native_called213&&mock_send_calls210==before&&mock_mode213==ACCOUNT_TRADE_MODE_REAL,"account changing to real during symbol metadata read is refused immediately before OrderSend");
 mock_mode213=ACCOUNT_TRADE_MODE_DEMO;mock_custom213=true;
 Check213(!MDDemoOrderSend213(r,answer)&&mock_send_calls210==before,"custom symbol cannot reach native API even with in-flight owned action");mock_custom213=false;
 MqlTradeRequest wrong=r;wrong.position=999999;
 Check213(!MDDemoOrderSend213(wrong,answer)&&mock_send_calls210==before,"foreign position ticket cannot reach native close API");
 wrong=r;wrong.volume+=1;Check213(!MDDemoOrderSend213(wrong,answer)&&mock_send_calls210==before,"close volume cannot exceed observed owned position");
 mock_mode213=ACCOUNT_TRADE_MODE_REAL;before=mock_send_calls210;Check213(!MDDemoOrderSend213(r,answer)&&mock_send_calls210==before,"real-mode revocation is enforced at final native API boundary");
 mock_mode213=ACCOUNT_TRADE_MODE_DEMO;mock_ea_algo213=false;Check213(!MDDemoOrderSend213(r,answer)&&mock_send_calls210==before,"permission revocation is enforced at final native API boundary");
 OnDeinit(1);
 Reset213();OnInit();persistent=ledger_path;OnDeinit(1);std::filesystem::remove(full(persistent));
 Check213(OnInit()==INIT_FAILED&&mock_send_calls210==0,"existing lock marker forbids initializing a fresh state over a missing ledger");
 if(lock615!=INVALID_HANDLE)OnDeinit(1);
 Reset213();MDSessionRule expiry_rule;mock_utc=MDCivilMidnight2026(20261216)+12*3600000;
 Check213(!MDDemoSession213(20261216,"WINZ26",expiry_rule),"expiry date cannot use an ordinary weekly broker session without reviewed special schedule");
 Print("DEMO_213;Checks=",checks213,";Failures=",failures213,";API_MOCK_NOT_NATIVE_MT5");return failures213?1:0;
}

// Reproduction of the exact XP metadata received on 2026-11-05.
void ResetXP21301(){
 Reset213();mock_session_begin213=0;mock_session_end213=86400;
 long day=MDCivilMidnight2026(20261105),prior=MDCivilMidnight2026(20261104);
 mock_utc=day+12*3600000+5*60000+45000;
 mock_ticks={{day+8*3600000+55*60000,199000,8},{day+9*3600000+5*60000+1000,210000,56}};
 mock_all_ticks=mock_ticks;opening208.symbol="";
 mock_daily_rates210={{MDCivilMidnight2026(20261103)/1000,210000,211000,209000,210000},
  {prior/1000,210000,211000,209000,210000},{day/1000,210000,999999,1,888888}};
 WriteB3213("DataFonte=2026-11-04\nDataOperacional=2026-11-05\nFonte=BVBG.187.01\nStatus=OK\nQuantidadeContratos=1\nContrato.WINZ26.Ajuste=210000\nContrato.WINZ26.AjusteAnterior=210000\n");
}
int regression21301(){
 if(regression213())return 1;
 ResetXP21301();MDSessionRule rule;
 Check213(MDDemoSession213(20261105,"WINZ26",rule)&&rule.scheduled_open==32400&&rule.cutoff==64800&&rule.normal_end==64800,
  "21301 XP raw 0..86400 becomes model-only 09..18 window, not 24-hour trading");
 Check213(StringFind(rule.source,"NOT_B3_EXCHANGE_SCHEDULE")>=0,
  "21301 provenance explicitly distinguishes generic demo availability from exchange schedule");
 Check213(MDSessionEvaluate(rule,20261105,8*3600+59*60,true,true)==MD_BEFORE_OPEN,
  "21301 broker 24h metadata cannot authorize a pre09 model entry");
 Check213(MDSessionEvaluate(rule,20261105,9*3600+5*60,true,false)==MD_WAIT_REAL_OPEN,
  "21301 passing 09h without a confirmed business still waits for real opening");
 Check213(MDSessionEvaluate(rule,20261105,64800,true,true)==MD_CUTOFF,
  "21301 model cutoff remains exactly18h even though broker advertises24h");
 Check213(!MDDemoSession213(20261104,"WINZ26",rule),"21301 current generic session cannot certify another date");
 mock_mode213=ACCOUNT_TRADE_MODE_REAL;
 Check213(!MDDemoSession213(20261105,"WINZ26",rule),"21301 full-day exception cannot apply to REAL account");mock_mode213=ACCOUNT_TRADE_MODE_DEMO;
 mock_custom213=true;Check213(!MDDemoSession213(20261105,"WINZ26",rule),"21301 custom symbols still refused");mock_custom213=false;
 mock_session_end213=0;Check213(!MDDemoSession213(20261105,"WINZ26",rule),"21301 0..0 is not confused with 0..86400");
 mock_session_begin213=0;mock_session_end213=64800;
 Check213(!MDDemoSession213(20261105,"WINZ26",rule),"21301 arbitrary midnight-to18 session is not silently generalized");
 mock_session_begin213=32400;mock_session_end213=64799;
 Check213(!MDDemoSession213(20261105,"WINZ26",rule),"21301 explicit broker session ending before cutoff refused");
 ResetXP21301();mock_utc=MDCivilMidnight2026(20261216)+12*3600000;
 Check213(!MDDemoSession213(20261216,"WINZ26",rule),"21301 expiry-day exception stays blocked even with24h metadata");
 ResetXP21301();bool prepared=true;Accept213(prepared);
 Check213(OnInit()==INIT_SUCCEEDED,"21301 exact XP current-day fixture initializes");
 for(int k=0;k<12;k++)Timer213();
 Check213(obs615.frozen&&obs615.data.date==20261105&&obs615.data.open_msc==MDCivilMidnight2026(20261105)+9*3600000+5*60000+1000,
  "21301 real opening at09:05:01 recognized; pre09 flagged event excluded");
 Check213(mock_send_calls210==5&&prepared,"21301 five eligible demo orders still require durable preparation after delayed opening");
 string path=ledger_path;OnDeinit(1);
 Check213(OnInit()==INIT_SUCCEEDED&&ledger_path==path,"21301 restart preserves the same account journal and namespace");
 int before=mock_send_calls210;for(int k=0;k<4;k++)Timer213();
 Check213(mock_send_calls210==before,"21301 restart cannot resend accepted levels");OnDeinit(1);
 ResetXP21301();mock_utc=MDCivilMidnight2026(20261105)+11*3600000+55*60000;
 mock_ticks={{MDCivilMidnight2026(20261105)+8*3600000+55*60000,210000,56}};mock_all_ticks=mock_ticks;
 OnInit();for(int k=0;k<4;k++)Timer213();
 Check213(mock_send_calls210==0&&!obs615.frozen,"21301 pre09 business cannot freeze opening or send orders");OnDeinit(1);
 Print("DEMO_21301;Checks=",checks213,";Failures=",failures213,";API_MOCK_NOT_NATIVE_MT5");return failures213?1:0;
}

int regression21302(){
 if(regression21301())return 1;
 ResetXP21301();bool prepared=true;Accept213(prepared);
 auto base_send=mock_send210;
 mock_send210=[&](const MqlTradeRequest &r,MqlTradeResult &v){
  bool ok=base_send(r,v);
  if(ok&&r.action==TRADE_ACTION_PENDING)mock_book.book.o[mock_book.book.orders-1].setup_msc+=966;
  return ok;
 };
 Check213(OnInit()==INIT_SUCCEEDED,"21302 asynchronous broker-receipt fixture initializes");
 for(int k=0;k<12;k++)Timer213();
 int entries=0,cancels=0;for(auto q:mock_requests210){entries+=q.action==TRADE_ACTION_PENDING;cancels+=q.action==TRADE_ACTION_REMOVE;}
 Check213(entries>0&&prepared,"21302 async receipt entries remain durably prepared");
 Check213(cancels==0,"21302 newly bound pending cannot be cancelled by a frame built before its origin existed");
 bool bound=false;for(int k=0;k<operational.nlevels;k++)if(operational.levels[k].order>0)bound=true;
 Check213(bound,"21302 delayed broker order receipt eventually binds actual origin");
 bool kept=true;for(int k=0;k<operational.nlevels;k++)if(operational.levels[k].order>0)
  kept=kept&&!operational.levels[k].cancel&&!operational.levels[k].consumed&&operational.levels[k].cancellation.phase==0;
 Check213(kept,"21302 newly accepted untouched pending retains opportunity and has no cancel intention");
 string journal=ledger_path;OnDeinit(1);
 Check213(OnInit()==INIT_SUCCEEDED&&ledger_path==journal,"21302 delayed receipt recovery uses the same durable journal after restart");
 int sent=mock_send_calls210;for(int k=0;k<3;k++)Timer213();
 Check213(mock_send_calls210==sent,"21302 restarting delayed-receipt state does not duplicate entry or cancel");
 OnDeinit(1);
 Print("DEMO_21302;Checks=",checks213,";Failures=",failures213,";API_MOCK_NOT_NATIVE_MT5");return failures213?1:0;
}

MDOpFrame RepairFixture21303(bool native_prices=false){
 ResetXP21301();mock_login210=52237148;mock_server210="XPMT5-DEMO";EmptyBook213();ExecutarNaDemo=false;
 if(native_prices){
  long day=MDCivilMidnight2026(20261105),prior=MDCivilMidnight2026(20261104);
  mock_ticks={{day+9*3600000+46475,170000,56}};mock_all_ticks=mock_ticks;
  mock_daily_rates210={{MDCivilMidnight2026(20261103)/1000,170000,171000,168000,169000},
   {prior/1000,169500,170090,168390,169530},{day/1000,170000,999999,1,888888}};
  WriteB3213("DataFonte=2026-11-04\nDataOperacional=2026-11-05\nFonte=BVBG.187.01\nStatus=OK\nQuantidadeContratos=1\nContrato.WINZ26.Ajuste=169650\nContrato.WINZ26.AjusteAnterior=167551\n");
 }
 if(OnInit()!=INIT_SUCCEEDED)throw std::runtime_error("fixture init");
 for(int n=0;n<12;n++)Timer213();
 if(operational.nlevels!=5)throw std::runtime_error("fixture missing levels");
 long now=MDCivilMidnight2026(20261105)+9*3600000+30*60000;
 mock_utc=now+10800000;mock_mono+=2000000;MDOpClockRead(opclock,operational.watermark,last_status);
 MDOpState response=operational;response.watermark=now+10800000;
 for(int k=0;k<5;k++){
  MDOpLevel l=response.levels[k];long ticket=MDRepairTicket21303(k);
  if(ticket>0){l.entry.phase=3;l.entry.serial=1;l.entry.started=MDRepairAccepted21303(k)+10800000-966;
   l.entry.completed=l.entry.started;l.entry.retcode=10009;l.entry.response_order=ticket;}
  else{l.consumed=true;l.touch_server=MDCivilMidnight2026(20261105)+9*3600000+6*60000+9846;}
  response.levels[k]=l;
 }
 if(!Commit(response,"DEMO_RESPONSE_NOT_EXECUTION_PROOF"))throw std::runtime_error("response fixture commit");
 MDOpState broken=operational;
 for(int k=0;k<5;k++)if(MDRepairTicket21303(k)>0){
  broken.levels[k].order=MDRepairTicket21303(k);broken.levels[k].accepted_server=MDRepairAccepted21303(k);
  broken.levels[k].entry.phase=6;broken.levels[k].consumed=true;broken.levels[k].cancel=true;
  MDOpIntent(broken.levels[k].cancellation,3,broken.levels[k].order,0,0,0);
 }
 if(!Commit(broken,"INTEGRATED_CYCLE"))throw std::runtime_error("broken fixture commit");
 MDOpState terminal=operational;EmptyBook213();mock_book.server_msc=now;
 for(int k=0;k<5;k++)if(MDRepairTicket21303(k)>0){
  MDOpLevel l=terminal.levels[k];l.cancellation.phase=6;l.cancellation.serial=1;
  l.cancellation.started=l.accepted_server+10800000+2000;l.cancellation.completed=l.cancellation.started+100;
  l.cancellation.retcode=10009;l.cancellation.response_order=l.order;terminal.levels[k]=l;
  int j=mock_book.book.orders++;MDRawOrder69 o;
  o.order.ticket=l.order;o.order.magic=MDMagic67(1,k);o.order.symbol=l.symbol;o.order.buy=l.prices.buy;
  o.order.state=1;o.order.initial_volume=1;o.order.remaining=1;o.setup_msc=l.accepted_server;o.entry_limit=true;
  mock_book.book.o[j]=o;mock_book.orders[j].price=l.prices.entry_tick;mock_book.orders[j].sl=l.prices.sl_tick;
  mock_book.orders[j].tp=l.prices.tp_tick;mock_book.orders[j].position_id=0;mock_book.orders[j].comment=MDOpComment(l);
 }
 if(!Commit(terminal,"DEMO_RECEIPT_RECONCILIATION"))throw std::runtime_error("terminal fixture commit");
 MDOpFrame f;MDOpFrameReset(f,now+10800000,now,true,true);f.stable=true;
 for(int k=0;k<5;k++)f.entry_ready[k]=true;
 f.touched[3]=true;f.first_touch[3]=terminal.levels[3].touch_server;
 return f;
}
int regression21303(){
 if(regression21302())return 1;
 MDOpFrame f=RepairFixture21303();MDOpState next;string why;
 Check213(MDRepairIncident21303(ledger,0,operational.scope,1),"21303 defective timer transition is proven in preserved journal");
 Check213(MDRepairCandidate21303(operational,mock_book,f,0,ledger,next,why),"21303 untouched exact incident order qualifies with cancelled/no-deal broker proof");
 Check213(!MDOpForward(operational,next),"21303 ordinary monotonic policy still forbids clearing consumed state");
 Check213(MDOpForwardEvent21303(operational,next,"REPAIR21303_CANCEL_2584908719",ledger),"21303 only explicit audited incident event authorizes canonical repair");
 Check213(!MDOpForwardEvent21303(operational,next,"MANUAL_RESET",ledger),"21303 arbitrary reset event cannot authorize repair");
 MDOpState altered=next;altered.levels[0].prices.sl_tick-=5;
 Check213(!MDOpForwardEvent21303(operational,altered,"REPAIR21303_CANCEL_2584908719",ledger),"21303 recovery cannot change mathematical prices or stops");
 auto guard=[&](MDOpState st,MDOpSnapshot b,MDOpFrame frame,string journal){MDOpState out;string r;return MDRepairCandidate21303(st,b,frame,0,journal,out,r);};
 MDOpFrame touched=f;touched.touched[0]=true;touched.first_touch[0]=f.server-1000;
 Check213(!guard(operational,mock_book,touched,ledger),"21303 level touched after faulty cancellation is never rearmed");
 MDOpFrame incomplete=f;incomplete.entry_ready[0]=false;
 Check213(!guard(operational,mock_book,incomplete,ledger),"21303 missing reconstruction/current-tail proof prevents recovery");
 MDOpFrame unstable=f;unstable.stable=false;Check213(!guard(operational,mock_book,unstable,ledger),"21303 unstable inventory prevents recovery");
 MDOpFrame cut=f;cut.utc=operational.levels[0].cutoff_utc;Check213(!guard(operational,mock_book,cut,ledger),"21303 recovery cannot rearm at cutoff");
 MDOpSnapshot active=mock_book;active.book.o[0].order.state=0;
 Check213(!guard(operational,active,f,ledger),"21303 active old order cannot be restored into a second order");
 MDOpSnapshot wrong=mock_book;wrong.orders[0].comment="FOREIGN";
 Check213(!guard(operational,wrong,f,ledger),"21303 wrong comment cannot qualify as the incident origin");
 MDOpSnapshot dealt=mock_book;dealt.book.deals=1;dealt.book.d[0].order=operational.levels[0].order;
 Check213(!guard(operational,dealt,f,ledger),"21303 any linked deal prevents restoring that order");
 Check213(!guard(operational,mock_book,f,""),"21303 broker absence alone cannot replace journal proof");
 MDOpState other=operational;other.scope=MDContext612(123,"XPMT5-DEMO",1);
 Check213(!guard(other,mock_book,f,ledger),"21303 incident manifest cannot act on another account");
 MDOpState other_ticket=operational;other_ticket.levels[0].order++;
 Check213(!guard(other_ticket,mock_book,f,ledger),"21303 arbitrary cancelled order cannot be rearmed");
 MDOpState ignored;Check213(!MDRepairCandidate21303(operational,mock_book,f,3,ledger,ignored,why),"21303 legitimate R38 first touch is excluded from incident manifest");
 string prefix=ledger;MDOpLevel r38=operational.levels[3];
 Check213(MDRepairCandidate21303(operational,mock_book,f,0,ledger,next,why)&&Commit(next,"REPAIR21303_CANCEL_2584908719"),"21303 recovery publishes through normal durable readback protocol");
 Check213(StringSubstr(ledger,0,StringLen(prefix))==prefix,"21303 original journal revisions remain byte-identical prefix");
 Check213(operational.levels[3].touch_server==r38.touch_server&&operational.levels[3].consumed,"21303 R38 stays consumed and its touch timestamp is preserved");
 MDOpState replay;Check213(MDOpReplay(ledger,operational.scope,1,replay)&&replay.levels[0].order==0&&replay.levels[0].entry.serial==2,"21303 repaired journal replays with reserved audit generation");
 Check213(!MDRepairCandidate21303(operational,mock_book,f,0,ledger,next,why),"21303 recovery is idempotent for the same incident order");
 MDOpState reconciled=operational;
 Check213(MDOpReconcile(reconciled,mock_book,f.utc,why),"21303 old cancelled origin remains accounted for after explicit migration");
 MDOpSnapshot bad_old=mock_book;bad_old.book.o[0].order.state=0;
 Check213(!MDRepairRetired21303(operational,bad_old,0),"21303 retired-origin exemption never hides a live old pending");
 bad_old=mock_book;bad_old.orders[0].sl+=5;
 Check213(!MDRepairRetired21303(operational,bad_old,0),"21303 changed historical old-order properties are not silently ignored");
 MDOpState attempt=operational;MDOpIntent(attempt.levels[0].entry,1,0,0,1,0);
 Check213(MDOpBegin(attempt,0,0,1,f.utc+1,true,true)&&attempt.levels[0].entry.serial==3&&MDOpComment(attempt.levels[0])!="MD202611050A1", "21303 next request has unique new serial and comment");
 attempt.levels[0].entry.phase=3;attempt.levels[0].entry.response_order=9000001;
 MDOpSnapshot fresh=mock_book;int j=fresh.book.orders++;fresh.book.o[j]=fresh.book.o[0];fresh.book.o[j].order.ticket=9000001;
 fresh.book.o[j].order.state=0;fresh.book.o[j].setup_msc=f.server+1000;fresh.orders[j]=fresh.orders[0];fresh.orders[j].comment=MDOpComment(attempt.levels[0]);fresh.server_msc=f.server+2000;
 Check213(MDOpReconcile(attempt,fresh,f.utc+2000,why)&&attempt.levels[0].order==9000001,"21303 new origin reconciles while the historical cancelled order remains in snapshot");
 string journal_path=ledger_path;OnDeinit(1);
 Check213(OnInit()==INIT_SUCCEEDED&&ledger_path==journal_path&&operational.levels[0].entry.serial==2,"21303 restart recovers repaired state from the same existing journal");
 OnDeinit(1);
 f=RepairFixture21303();ExecutarNaDemo=true;
 f.touched[1]=true;f.first_touch[1]=f.server-500; // an additional level touched during the repair delay
 string before_repair=ledger;
 Check213(MDRepairRun21303(f,mock_book),"21303 automatic recovery commits first untouched target without manual state edits");
 Check213(MDRepairRun21303(f,mock_book)&&MDRepairRun21303(f,mock_book),"21303 remaining untouched levels recover while newly touched S50 stays blocked");
 Check213(!MDRepairRun21303(f,mock_book),"21303 automatic recovery stops after eligible targets are done");
 Check213(!operational.levels[0].consumed&&operational.levels[1].consumed&&!operational.levels[2].consumed&&operational.levels[3].consumed&&!operational.levels[4].consumed,
  "21303 only untouched levels0/2/4 recover; touched S50 and R38 remain consumed");
 string backup;Check213(MDOpReadFile(ledger_path+".pre21303",backup)&&backup==before_repair,"21303 original complete journal saved once as verified backup");
 Check213(mock_send_calls210==0,"21303 migration itself cannot send broker requests");
 MDOpFrame crossing=f;crossing.touched[0]=true;crossing.first_touch[0]=f.server+1;crossing.utc++;crossing.server++;
 MDOpState no_late_entry;
 Check213(MDOpCycle(operational,mock_book,crossing,no_late_entry,why)&&no_late_entry.levels[0].consumed&&no_late_entry.levels[0].entry.phase!=1,
  "21303 a touch after recovery but before send still blocks the new entry");
 Check213(!MDRepairBackup21303("missing_dir/journal",ledger,operational.scope,1),"21303 backup creation failure cannot grant recovery");
 string stored_path=ledger_path;OnDeinit(1);
 Check213(OnInit()==INIT_SUCCEEDED&&ledger_path==stored_path&&!operational.levels[0].consumed&&operational.levels[3].consumed,
  "21303 restarting automatic multi-level migration preserves decisions and legitimate consumption");OnDeinit(1);
 Print("DEMO_21303;Checks=",checks213,";Failures=",failures213,";API_MOCK_NOT_NATIVE_MT5");return failures213?1:0;
}

int regression_initial21304(){
 if(regression21303())return 1;
 Reset213();bool prepared=true;Accept213(prepared);OnInit();Bootstrap213();
 MDOpFrame f;MDOpFrameReset(f,opclock.utc+2000,opclock.server+2000,true,true);f.stable=true;
 for(int k=0;k<5;k++)f.entry_ready[k]=true; // pending trails still catching up
 mock_book.server_msc=f.server;
 MDOpState next;string why;
 Check213(MDOpCycle(operational,mock_book,f,next,why)&&why=="ALL_CHAINS_RECONCILED","21304 stable receipts reconcile while pending histories are incomplete");
 bool kept=true;for(int k=0;k<next.nlevels;k++)kept=kept&&!next.levels[k].cancel&&!next.levels[k].consumed&&next.levels[k].cancellation.phase==0;
 Check213(kept,"21304 incomplete history is not evidence to cancel or consume untouched pending orders");
 OnDeinit(1);Print("DEMO_21304;Checks=",checks213,";Failures=",failures213,";API_MOCK_NOT_NATIVE_MT5");return failures213?1:0;
}

MDOpFrame ResumeFixture21304(){
 MDOpFrame f=RepairFixture21303(true);MDOpState out;string why;
 for(int k=1;k<5;k++)if(k!=3){
  long ticket=operational.levels[k].order;
  if(!MDRepairCandidate21303(operational,mock_book,f,k,ledger,out,why)||!Commit(out,"REPAIR21303_CANCEL_"+IntegerToString(ticket)))
   throw std::runtime_error("initial migration "+why);
 }
 long now=MDCivilMidnight2026(20261105)+13*3600000+20*60000;mock_utc=now+10800000;mock_mono+=15000000;
 MDOpClockInit(opclock);
 for(int sample=0;sample<3;sample++)MDOpClockRead(opclock,operational.watermark,last_status);
 if(!opclock.ok)throw std::runtime_error("resume fixture clock "+last_status);
 mock_book.server_msc=now;
 MDOpState response=operational;
 long tickets[5]={0,2585252213,2585252263,0,2585252290};
 for(int k=1;k<5;k++)if(k!=3){
  response.levels[k].entry.phase=3;response.levels[k].entry.serial=3;
  response.levels[k].entry.started=1793877147000+10800000;response.levels[k].entry.completed=response.levels[k].entry.started;
  response.levels[k].entry.retcode=10009;response.levels[k].entry.response_order=tickets[k];
  int j=mock_book.book.orders++;MDRawOrder69 o;
  o.order.ticket=tickets[k];o.order.magic=MDMagic67(1,k);o.order.symbol="WINZ26";o.order.buy=k<3;
  o.order.state=0;o.order.initial_volume=1;o.order.remaining=1;o.setup_msc=k==4?1793877148012:1793877144000+k*1000;o.entry_limit=true;
  mock_book.book.o[j]=o;mock_book.orders[j].price=response.levels[k].prices.entry_tick;mock_book.orders[j].sl=response.levels[k].prices.sl_tick;
  mock_book.orders[j].tp=response.levels[k].prices.tp_tick;mock_book.orders[j].position_id=0;mock_book.orders[j].comment=MDOpComment(response.levels[k]);
 }
 if(!Commit(response,"DEMO_RESPONSE_NOT_EXECUTION_PROOF"))throw std::runtime_error("new response");
 MDOpState bound=operational;if(!MDOpReconcile(bound,mock_book,opclock.utc,why)||!Commit(bound,"DEMO_TIMER_RECEIPT_RECONCILIATION"))throw std::runtime_error("new origins "+why);
 for(int k=1;k<=2;k++){
  int j=-1;for(int x=0;x<mock_book.book.orders;x++)if(mock_book.book.o[x].order.ticket==tickets[k])j=x;
  mock_book.book.o[j].order.state=2;mock_book.book.o[j].order.remaining=0;mock_book.orders[j].position_id=tickets[k];
  long ms_in=k==1?1793881194403:1793881371206,ms_out=k==1?1793881631418:1793881387552;
  OPDeal(mock_book,8000+k,tickets[k],tickets[k],0,1,ms_in);mock_book.book.d[mock_book.book.deals-1].magic=MDMagic67(1,k);
  mock_book.deal_price[mock_book.book.deals-1]=operational.levels[k].prices.entry_tick;
  int e=mock_book.book.orders++;MDRawOrder69 exit;
  exit.order.ticket=9100+k;exit.order.magic=0;exit.order.symbol="WINZ26";exit.order.buy=false;exit.order.state=2;
  exit.order.initial_volume=1;exit.order.remaining=0;exit.setup_msc=ms_out;exit.entry_limit=false;
  mock_book.book.o[e]=exit;mock_book.orders[e].position_id=tickets[k];mock_book.orders[e].price=k==1?168695:169070;
  mock_book.orders[e].sl=0;mock_book.orders[e].tp=0;mock_book.orders[e].comment="";
  OPDeal(mock_book,8200+k,9100+k,tickets[k],1,1,ms_out);mock_book.deal_price[mock_book.book.deals-1]=k==1?168695:169070;
 }
 MDOpState closed=operational;if(!MDOpReconcile(closed,mock_book,opclock.utc,why)||!Commit(closed,"DEMO_TIMER_RECEIPT_RECONCILIATION"))throw std::runtime_error("closed chains "+why);
 MDOpState broken=operational;broken.levels[4].cancel=true;broken.levels[4].consumed=true;
 MDOpIntent(broken.levels[4].cancellation,3,2585252290,0,0,0);
 if(!Commit(broken,"INTEGRATED_CYCLE"))throw std::runtime_error("resume defect");
 MDOpState terminal=operational;terminal.levels[4].cancellation.phase=6;terminal.levels[4].cancellation.serial=2;
 terminal.levels[4].cancellation.started=1793884357000+10800000;terminal.levels[4].cancellation.completed=terminal.levels[4].cancellation.started+100;
 terminal.levels[4].cancellation.retcode=10009;terminal.levels[4].cancellation.response_order=2585252290;
 for(int j=0;j<mock_book.book.orders;j++)if(mock_book.book.o[j].order.ticket==2585252290)mock_book.book.o[j].order.state=1;
 if(!Commit(terminal,"DEMO_RECEIPT_RECONCILIATION"))throw std::runtime_error("resume cancelled");
 MDOpFrameReset(f,opclock.utc,now,true,true);f.stable=true;for(int k=0;k<5;k++)f.entry_ready[k]=true;
 f.touched[0]=f.touched[1]=f.touched[2]=f.touched[3]=true;
 f.first_touch[0]=1793871401375;f.first_touch[1]=1793881194320;f.first_touch[2]=1793881370451;f.first_touch[3]=1793869569846;
 return f;
}
int regression21304(){
 if(regression_initial21304())return 1;
 // Actual bounded trail reader: ten minutes of history cannot be consumed as
 // one failed/invalid opportunity merely because one minute was read per call.
 Reset213();bool durable=true;Accept213(durable);OnInit();Bootstrap213();
 MDOpState before=operational;long origin=before.levels[4].accepted_server;long horizon=origin+600000;
 mock_ticks.clear();for(long t=origin-1000;t<horizon;t+=20000)mock_ticks.push_back(MqlTick{t,210000,56});mock_all_ticks=mock_ticks;
 MDOpTrail trail;MDOpTrailInit(trail,"WINZ26",origin,before.levels[4].prices,true);string why;
 bool full=MDOpTrailRead(trail,horizon,why);
 Check213(!full&&trail.cursor<horizon&&!trail.failed&&StringFind(why,"TRAIL_RECONSTRUINDO")==0,"21304 bounded valid trail is explicitly reconstruction-in-progress");
 MDOpSnapshot snapshot=mock_book;snapshot.server_msc=horizon;MDOpFrame f;MDOpFrameReset(f,horizon+10800000,horizon,true,true);f.stable=true;
 for(int k=0;k<5;k++){f.pending_history[k]=true;}
 f.pending_history[4]=full;MDOpState next;
 Check213(MDOpCycle(before,snapshot,f,next,why)&&!next.levels[4].cancel&&!next.levels[4].consumed,"21304 real partial-reader result keeps accepted R61 active");
 for(int i=0;i<12&&!full;i++)full=MDOpTrailRead(trail,horizon,why);
 Check213(full&&trail.cursor==horizon&&!trail.boundary,"21304 repeated bounded reads eventually catch up without inventing a boundary");
 MDOpTrailInit(trail,"WINZ26",origin,before.levels[4].prices,true);mock_partial210=true;long cursor=trail.cursor;
 Check213(!MDOpTrailRead(trail,horizon,why)&&trail.cursor==cursor&&StringFind(why,"4403")>=0,"21304 timeout preserves trail cursor and cannot prove invalidation");mock_partial210=false;
 f.pending_history[4]=false;MDOpCycle(before,snapshot,f,next,why);
 Check213(!next.levels[4].cancel&&!next.levels[4].consumed,"21304 timeout cannot cancel or consume an untouched existing pending");
 f.pending_boundary[4]=true;MDOpCycle(before,snapshot,f,next,why);
 Check213(next.levels[4].cancel&&next.levels[4].consumed&&next.levels[4].cancellation.phase==1,"21304 proven boundary still cancels immediately even before all later history catches up");
 f.pending_boundary[4]=false;f.touched[4]=true;f.first_touch[4]=origin+1000;MDOpCycle(before,snapshot,f,next,why);
 Check213(next.levels[4].consumed&&!next.levels[4].cancel,"21304 first touch after acceptance consumes entry opportunity without falsely cancelling an unfilled valid pending");
 f.first_touch[4]=origin;MDOpCycle(before,snapshot,f,next,why);
 Check213(next.levels[4].cancel,"21304 acceptance without strict precedence over first touch remains invalid");
 f.touched[4]=false;f.utc=before.levels[4].cutoff_utc;f.server=f.utc-10800000;MDOpCycle(before,snapshot,f,next,why);
 Check213(next.levels[4].cutoff&&next.levels[4].cancel&&next.levels[4].cancellation.phase==1,"21304 cutoff cancels independently of incomplete tick history");
 OnDeinit(1);
 f=ResumeFixture21304();MDOpState candidate;
 Check213(operational.npositions==2&&operational.positions[0].volume==0&&operational.positions[1].volume==0,"21304 fixture includes both closed support operations, not just a flat empty account");
 Check213(operational.levels[1].prices.entry_tick==169070&&operational.levels[1].prices.sl_tick==168695&&operational.levels[2].prices.entry_tick==168935&&operational.levels[2].prices.tp_tick==169070,"21304 replay fixture uses actual day's support entry and exit prices");
 Check213(MDRepairIncident21304(ledger,operational.scope,1),"21304 resume cancellation transition is proven after the earlier audited recovery");
 Check213(MDRepairCandidate21304(operational,mock_book,f,ledger,candidate,why),"21304 exact cancelled untouched R61 qualifies with current history and broker proof");
 Check213(!MDOpForward(operational,candidate)&&!MDOpForwardEvent21304(operational,candidate,"RESET",ledger),"21304 ordinary rollback and arbitrary reset event stay forbidden");
 Check213(MDOpForwardEvent21304(operational,candidate,"REPAIR21304_RESUME_2585252290",ledger),"21304 only canonical one-level recovery event can clear the false consumption");
 MDOpState corrupt=candidate;corrupt.positions[0].entered=0;
 Check213(!MDOpForwardEvent21304(operational,corrupt,"REPAIR21304_RESUME_2585252290",ledger),"21304 repair cannot alter closed position receipts or volume totals");
 MDOpFrame touched=f;touched.touched[4]=true;touched.first_touch[4]=f.server-1;
 Check213(!MDRepairCandidate21304(operational,mock_book,touched,ledger,candidate,why),"21304 R61 touched after cancellation cannot be rearmed");
 touched=f;touched.entry_ready[4]=false;
 Check213(!MDRepairCandidate21304(operational,mock_book,touched,ledger,candidate,why),"21304 unverified reconstruction/current tail blocks recovery");
 touched=f;touched.stable=false;
 Check213(!MDRepairCandidate21304(operational,mock_book,touched,ledger,candidate,why),"21304 unstable inventory blocks recovery");
 touched=f;touched.utc=operational.levels[4].cutoff_utc;
 Check213(!MDRepairCandidate21304(operational,mock_book,touched,ledger,candidate,why),"21304 no recovery at or after cutoff");
 MDOpSnapshot changed=mock_book;for(int j=0;j<changed.book.orders;j++)if(changed.book.o[j].order.ticket==2585252290)changed.book.o[j].order.state=0;
 Check213(!MDRepairCandidate21304(operational,changed,f,ledger,candidate,why),"21304 an old R61 still active cannot generate a second order");
 changed=mock_book;OPDeal(changed,99999,2585252290,2585252290,0,1,f.server-1);
 Check213(!MDRepairCandidate21304(operational,changed,f,ledger,candidate,why),"21304 any execution linked to cancelled R61 blocks recovery");
 Check213(!MDRepairCandidate21304(operational,mock_book,f,"",candidate,why),"21304 missing journal proof cannot be replaced by broker absence");
 string prefix=ledger;MDOpState saved=operational;ExecutarNaDemo=true;
 Check213(MDRepairRun21304(f,mock_book),"21304 automatic recovery publishes with verified backup");
 Check213(StringSubstr(ledger,0,StringLen(prefix))==prefix,"21304 entire prior journal remains byte-identical prefix");
 Check213(operational.levels[4].order==0&&operational.levels[4].entry.serial==4&&!operational.levels[4].consumed,"21304 only the false R61 consumption is cleared and a new generation reserved");
 bool supports=true;for(int p=0;p<saved.npositions;p++)supports=supports&&operational.positions[p].entered==saved.positions[p].entered&&operational.positions[p].exited==saved.positions[p].exited&&operational.positions[p].volume==0;
 supports=supports&&operational.levels[1].deal_receipts==saved.levels[1].deal_receipts&&operational.levels[2].deal_receipts==saved.levels[2].deal_receipts;
 Check213(supports,"21304 S50 and S618 executions, exits, zero residuals and price receipts preserved");
 Check213(operational.levels[0].consumed&&operational.levels[3].consumed,"21304 real S38 and R38 first touches remain consumed");
 Check213(!MDRepairRun21304(f,mock_book),"21304 resume repair cannot repeat on next timer");
 MDOpState replay;Check213(MDOpReplay(ledger,operational.scope,1,replay)&&replay.levels[4].entry.serial==4,"21304 journal replays both generations of audited migrations");
 MDOpState binding=operational;MDOpIntent(binding.levels[4].entry,1,0,0,1,0);MDOpBegin(binding,4,0,1,f.utc+1,true,true);
 Check213(binding.levels[4].entry.serial==5&&MDOpComment(binding.levels[4])=="MD202611054A5","21304 new R61 request cannot reuse either earlier broker comment");
 binding.levels[4].entry.phase=3;binding.levels[4].entry.response_order=9200001;
 changed=mock_book;int j=changed.book.orders++;int original=-1;for(int n=0;n<mock_book.book.orders;n++)if(mock_book.book.o[n].order.ticket==2585252290)original=n;
 changed.book.o[j]=changed.book.o[original];changed.book.o[j].order.ticket=9200001;changed.book.o[j].order.state=0;changed.book.o[j].setup_msc=f.server+1000;
 changed.orders[j]=changed.orders[original];changed.orders[j].comment=MDOpComment(binding.levels[4]);changed.server_msc=f.server+2000;
 Check213(MDOpReconcile(binding,changed,f.utc+2000,why)&&binding.levels[4].order==9200001,"21304 both old cancelled R61 generations coexist with a correctly bound new pending");
 MDOpFrame gap;MDOpFrameReset(gap,f.utc+4000,f.server+4000,true,true);gap.stable=true;
 Check213(MDOpCycle(binding,changed,gap,next,why)&&!next.levels[4].cancel,"21304 another incomplete-history interval cannot cancel the newly recovered R61");
 string path=ledger_path;OnDeinit(1);Check213(OnInit()==INIT_SUCCEEDED&&ledger_path==path&&operational.npositions==2&&operational.levels[4].entry.serial==4,"21304 restart preserves repaired state and both closed operations");OnDeinit(1);
 Print("DEMO_21304;Checks=",checks213,";Failures=",failures213,";API_MOCK_NOT_NATIVE_MT5");return failures213?1:0;
}

MDOpFrame CancelledFixture21305(){
 Reset213();if(OnInit()!=INIT_SUCCEEDED)throw std::runtime_error("21305 init");
 MDOpState s;MDOpFrame f;OPBase(s,mock_book,f);s.scope=Scope615();
 mock_book.book.account_key=MDAccount213();mock_book.book.server_key=MDServer213();
 long now=Begin213()+120000;mock_utc=now+10800000;mock_mono+=120000;
 MDOpClockInit(opclock);for(int i=0;i<3;i++)MDOpClockRead(opclock,0,last_status);
 for(int k=0;k<s.nlevels;k++){
  s.levels[k].date=20261104;s.levels[k].key=202611040+k;s.levels[k].open_server=Begin213()+1000;
  s.levels[k].cutoff_utc=Day213()+18*3600000+10800000;s.levels[k].volume=10;
 }
 MDOpLevel l=s.levels[0];l.order=70001;l.accepted_server=Begin213()+30000;l.entry.phase=6;l.entry.serial=1;
 l.entry.started=l.accepted_server+10800000;l.entry.completed=l.entry.started;l.entry.retcode=10009;l.entry.response_order=l.order;l.consumed=true;s.levels[0]=l;
 OPOrder(s,mock_book,0,70001,1,10);mock_book.book.o[0].setup_msc=l.accepted_server;
 mock_book.orders[0].sl=l.prices.sl_tick;mock_book.orders[0].tp=l.prices.tp_tick;mock_book.orders[0].comment=MDOpComment(l);
 mock_book.server_msc=now;s.watermark=now+10800000;
 if(!Commit(s,"SYNTHETIC_CANCELLED_NO_FILL"))throw std::runtime_error("21305 seed");
 MDOpFrameReset(f,s.watermark,now,true,true);f.stable=true;f.entry_ready[0]=true;return f;
}
int main(){
 if(regression21304())return 1;
 string why;MDOpState candidate,verified;MDOpFrame f=CancelledFixture21305();MDOpState before=operational;
 Check213(MDRearmCandidate21305(operational,mock_book,f,0,candidate,why),"21305 general account and unrelated cancelled ticket can rearm only with complete untouched proof");
 Check213(!MDOpForward(operational,candidate)&&!MDOpForwardEvent21305(operational,candidate,"RESET",ledger),"21305 ordinary regression and arbitrary reset remain forbidden");
 Check213(!MDOpForwardEvent21305(operational,operational,"REARM21305_202611040_70001",ledger),"21305 reserved event cannot poison retired registry with a monotone no-op");
 Check213(MDOpForwardEvent21305(operational,candidate,"REARM21305_202611040_70001",ledger),"21305 canonical audited transition permits the approved rearm");
 MDOpState altered=candidate;altered.levels[1].prices.tp_tick+=5;
 Check213(!MDOpForwardEvent21305(operational,altered,"REARM21305_202611040_70001",ledger),"21305 rearm cannot change any other level or fixed price");
 MDOpFrame blocked=f;blocked.entry_ready[0]=false;
 Check213(!MDRearmCandidate21305(operational,mock_book,blocked,0,candidate,why),"21305 incomplete reconstruction/current tail cannot rearm");
 blocked=f;blocked.touched[0]=true;blocked.first_touch[0]=f.server-1;
 Check213(!MDRearmCandidate21305(operational,mock_book,blocked,0,candidate,why),"21305 historical first touch blocks rearm even with cancelled order");
 blocked=f;blocked.pending_boundary[0]=true;
 Check213(!MDRearmCandidate21305(operational,mock_book,blocked,0,candidate,why),"21305 proven theoretical boundary blocks rearm");
 blocked=f;blocked.stable=false;
 Check213(!MDRearmCandidate21305(operational,mock_book,blocked,0,candidate,why),"21305 unstable inventory cannot prove cancellation");
 blocked=f;blocked.utc=operational.levels[0].cutoff_utc;
 Check213(!MDRearmCandidate21305(operational,mock_book,blocked,0,candidate,why),"21305 cutoff never rearms");
 MDOpSnapshot changed=mock_book;changed.book.orders=0;
 Check213(!MDRearmCandidate21305(operational,changed,f,0,candidate,why),"21305 absence of old order is not cancellation proof");
 changed=mock_book;changed.book.o[0].order.state=0;
 Check213(!MDRearmCandidate21305(operational,changed,f,0,candidate,why),"21305 active order cannot generate duplicate pending");
 changed=mock_book;OPDeal(changed,90001,70001,80001,0,6,f.server-1000);
 Check213(!MDRearmCandidate21305(operational,changed,f,0,candidate,why),"21305 any partial execution blocks a new order to complete volume");
 altered=operational;altered.levels[0].entry.phase=2;
 Check213(!MDRearmCandidate21305(altered,mock_book,f,0,candidate,why),"21305 uncertain request cannot be reset");
 altered=operational;altered.levels[0].touch_server=f.server-1000;
 Check213(!MDRearmCandidate21305(altered,mock_book,f,0,candidate,why),"21305 durable prior touch cannot be forgotten");
 changed=mock_book;changed.orders[0].comment="FOREIGN";
 Check213(!MDRearmCandidate21305(operational,changed,f,0,candidate,why),"21305 changed comment or ownership blocks rearm");

 changed=mock_book;OPOrder(operational,changed,0,70099,0,10);changed.book.o[1].setup_msc=f.server-1;
 Check213(!MDRearmCandidate21305(operational,changed,f,0,candidate,why),"21305 another unbound active order for same level blocks a second pending");
 string prefix=ledger;
 mock_terminal_state21305=ORDER_STATE_EXPIRED;
 Check213(!MDRetomadaRun21305(f,mock_book)&&ledger==prefix,"21305 expired native state is not silently treated as an authorized cancellation");
 mock_terminal_state21305=-1;
 Check213(MDRetomadaRun21305(f,mock_book),"21305 runtime confirms native cancellation, backs up and publishes general rearm");
 Check213(StringSubstr(ledger,0,StringLen(prefix))==prefix&&FileIsExist(ledger_path+".pre21305",FILE_COMMON),"21305 previous ledger bytes and verified backup retained");
 Check213(operational.levels[0].order==0&&!operational.levels[0].consumed&&operational.levels[0].entry.serial==2,"21305 rearm reserves a new generation without consuming untouched level");
 Check213(!MDRetomadaRun21305(f,mock_book),"21305 next timer cannot repeat same recovery");
 Check213(MDOpReplay(ledger,operational.scope,1,verified)&&MDOpEncode(verified)==MDOpEncode(operational),"21305 replay reconstructs general rearm and retired origin proof");
 Check213(MDOpReconcile(verified,mock_book,f.utc,why),"21305 retired cancelled origin remains recognized from verified ledger");
 changed=mock_book;changed.orders[0].sl+=5;
 Check213(!MDOpReconcile(verified,changed,f.utc,why),"21305 changed retired broker receipt blocks reconciliation");
 changed=mock_book;OPDeal(changed,90001,70001,80001,0,1,f.server-1);OPPosition(changed,80001,80001,1);
 Check213(!MDOpReconcile(verified,changed,f.utc,why),"21305 delayed fill of retired origin is detected rather than ignored");
 MDOpState sent=operational;MDOpIntent(sent.levels[0].entry,1,0,0,10,0);MDOpBegin(sent,0,-1,1,f.utc+1000,true,true);
 sent.levels[0].entry.phase=3;sent.levels[0].entry.response_order=70002;sent.levels[0].entry.retcode=10009;
 changed=mock_book;OPOrder(sent,changed,0,70002,0,10);changed.book.o[1].setup_msc=f.server+1000;changed.server_msc=f.server+2000;
 changed.orders[1].sl=sent.levels[0].prices.sl_tick;changed.orders[1].tp=sent.levels[0].prices.tp_tick;
 Check213(sent.levels[0].entry.serial==3&&MDOpComment(sent.levels[0])=="MD202611040A3"&&MDOpReconcile(sent,changed,f.utc+2000,why),"21305 new request gets A3 and binds alongside cancelled A1 without duplication");
 Check213(Commit(sent,"SYNTHETIC_NEW_ORIGIN")&&MDOpReplay(ledger,operational.scope,1,verified),"21305 new origin and old retired proof survive persistence");
 string path=ledger_path;OnDeinit(1);Check213(OnInit()==INIT_SUCCEEDED&&ledger_path==path&&operational.levels[0].order==70002,"21305 restart recovers current origin without resending cancelled predecessor");
 mock_book=changed;mock_book.book.o[1].order.state=1;mock_book.server_msc=f.server+4000;mock_utc=f.utc+4000;
 MDOpClockInit(opclock);for(int sample=0;sample<3;sample++)MDOpClockRead(opclock,operational.watermark,why);
 verified=operational;bool repeated=MDOpReconcile(verified,mock_book,opclock.utc,why)&&Commit(verified,"SYNTHETIC_SECOND_CANCEL");
 MDOpFrame again;MDOpFrameReset(again,opclock.utc,mock_book.server_msc,true,true);again.stable=true;again.entry_ready[0]=true;
 Check213(repeated&&MDRetomadaRun21305(again,mock_book)&&operational.levels[0].entry.serial==4,"21305 a second confirmed cancellation without touch can rearm again under the same rule");
 MDOpState third=operational;MDOpIntent(third.levels[0].entry,1,0,0,10,0);MDOpBegin(third,0,-1,1,again.utc+1000,true,true);
 Check213(third.levels[0].entry.serial==5&&MDOpComment(third.levels[0])=="MD202611040A5"&&MDOpReplay(ledger,operational.scope,1,verified)&&MDOpReconcile(verified,mock_book,again.utc,why),"21305 third possible request has unique A5 and both earlier cancelled generations remain audited");OnDeinit(1);
 // User's exact partial example: 6 filled, 4 in the SAME pending order.
 f=CancelledFixture21305();changed=mock_book;changed.book.o[0].order.state=0;changed.book.o[0].order.remaining=4;
 OPDeal(changed,90001,70001,80001,0,6,f.server-1000);OPPosition(changed,80001,80001,6,operational.levels[0].prices.sl_tick,operational.levels[0].prices.tp_tick);
 changed.orders[0].position_id=80001;MDOpState partial=operational;
 Check213(MDOpReconcile(partial,changed,f.utc,why)&&partial.npositions==1&&partial.positions[0].volume==6,"21305 six fills plus four pending reconcile as one opportunity");
 Check213(!MDRearmCandidate21305(partial,changed,f,0,candidate,why),"21305 partial cannot rearm even if a frame mistakenly says no touch");
 f.touched[0]=true;f.first_touch[0]=f.server-1001;
 Check213(MDOpCycle(partial,changed,f,candidate,why)&&candidate.levels[0].consumed&&!candidate.levels[0].cancel&&!candidate.positions[0].closing,"21305 first touch keeps protected six and valid remainder four alive");



 MDOpState cancelling=partial;cancelling.levels[0].cancel=true;cancelling.levels[0].closing=true;
 cancelling.levels[0].cancellation.phase=3;cancelling.levels[0].cancellation.serial=1;cancelling.levels[0].cancellation.started=f.utc-1000;cancelling.levels[0].cancellation.response_order=70001;
 cancelling.positions[0].closing=true;MDOpIntent(cancelling.positions[0].close,4,80001,80001,6,0);
 cancelling.positions[0].close.phase=2;cancelling.positions[0].close.serial=1;cancelling.positions[0].close.started=f.utc-500;
 MDOpSnapshot fill_race=changed;fill_race.book.o[0].order.state=2;fill_race.book.o[0].order.remaining=0;
 OPDeal(fill_race,90004,70001,80001,0,4,f.server-200);fill_race.book.p[0].volume=10;
 MDOpFrame race_frame=f;race_frame.pending_boundary[0]=true;
 Check213(MDOpCycle(cancelling,fill_race,race_frame,candidate,why)&&candidate.positions[0].volume==10&&candidate.positions[0].close.phase==2&&candidate.positions[0].close.volume==6&&candidate.levels[0].entry.phase==6,"21305 four fill during cancellation is reconciled without duplicating in-flight close of six or creating new entry");
 MDOpState after_fill=candidate;after_fill.positions[0].close.phase=3;after_fill.positions[0].close.response_order=90006;
 OPDeal(fill_race,90005,90006,80001,1,6,f.server-100);fill_race.book.p[0].volume=4;
 int close_order=fill_race.book.orders++;fill_race.book.o[close_order]=fill_race.book.o[0];fill_race.book.o[close_order].order.ticket=90006;fill_race.book.o[close_order].entry_limit=false;
 Check213(MDOpCycle(after_fill,fill_race,race_frame,candidate,why)&&candidate.positions[0].volume==4&&candidate.positions[0].close.phase==1&&candidate.positions[0].close.volume==4,"21305 confirmed close of six leaves one new close intention for raced four-contract residual");
 MDOpState risk_partial=partial;risk_partial.positions[0].protection.started=true;risk_partial.positions[0].protection.initial_completed=6;
 risk_partial.positions[0].protection.last_started_ms=f.utc-181000;risk_partial.positions[0].protection.sixth_completed_ms=f.utc-180000;
 MDOpSnapshot no_sl=changed;no_sl.sl[0]=0;
 Check213(MDOpCycle(risk_partial,no_sl,f,candidate,why)&&candidate.positions[0].closing&&candidate.levels[0].cancel&&candidate.levels[0].cancellation.phase==1,"21305 mandatory missing-SL risk close also cancels the same order's unfilled four contracts");
 MDOpSnapshot no_tp=changed;no_tp.tp[0]=0;
 Check213(MDOpCycle(risk_partial,no_tp,f,candidate,why)&&!candidate.positions[0].closing&&!candidate.levels[0].cancel&&candidate.positions[0].protect.phase==1,"21305 SL-present TP-only failure keeps position and remainder valid while TP retry continues");
 MDOpSnapshot stopped_partial=changed;stopped_partial.book.positions=0;
 OPDeal(stopped_partial,90002,90003,80001,1,6,f.server-500);
 Check213(!MDBrokerExitBoundary21305(partial,stopped_partial,0),"21305 matching stop price alone without native reason is not claimed as broker SL receipt");
 mock_reason21305[90002]=DEAL_REASON_SL;
 Check213(MDBrokerExitBoundary21305(partial,stopped_partial,0),"21305 native SL exit of six confirms boundary while four remain pending");
 MDOpFrame broker_stop=f;broker_stop.pending_boundary[0]=MDBrokerExitBoundary21305(partial,stopped_partial,0);
 Check213(MDOpCycle(partial,stopped_partial,broker_stop,candidate,why)&&candidate.levels[0].cancel&&candidate.positions[0].volume==0,"21305 broker-confirmed partial exit cancels four without waiting for Last reconstruction");
 f.pending_boundary[0]=true;
 Check213(MDOpCycle(partial,changed,f,candidate,why)&&candidate.levels[0].cancel&&candidate.positions[0].closing,"21305 theoretical boundary cancels four and closes persistent executed six");
 f.pending_boundary[0]=false;f.utc=partial.levels[0].cutoff_utc;
 Check213(MDOpCycle(partial,changed,f,candidate,why)&&candidate.levels[0].cutoff&&candidate.levels[0].cancel&&candidate.positions[0].closing,"21305 cutoff cancels partial remainder and closes residual position");
 OnDeinit(1);
 // Closed sessions release bounded working slots, while every old revision remains.
 f=CancelledFixture21305();MDOpState closed=operational;
 for(int k=0;k<closed.nlevels;k++){closed.levels[k].cutoff=true;closed.levels[k].consumed=true;}
 long tomorrow=MDCivilMidnight2026(20261105)+10*3600000;mock_utc=tomorrow+10800000;mock_book.server_msc=tomorrow;
 closed.watermark=mock_utc;Check213(Commit(closed,"SYNTHETIC_PAST_CUTOFF"),"21305 complete closed past-session fixture persists");
 MDOpFrameReset(f,mock_utc,tomorrow,true,true);f.stable=true;
 Check213(MDArchiveCandidate21305(operational,mock_book,f,20261104,candidate,why),"21305 only past flat terminal session qualifies for archival");
 Check213(!MDArchiveCandidate21305(operational,mock_book,f,20261105,candidate,why),"21305 current session cannot be archived");
 altered=operational;altered.levels[0].entry.phase=2;
 Check213(!MDArchiveCandidate21305(altered,mock_book,f,20261104,candidate,why),"21305 uncertain origin prevents archival");
 changed=mock_book;changed.book.o[0].order.state=0;
 Check213(!MDArchiveCandidate21305(operational,changed,f,20261104,candidate,why),"21305 active pending prevents archival");
 prefix=ledger;
 Check213(MDRetomadaRun21305(f,mock_book)&&operational.nlevels==0&&operational.npositions==0,"21305 runtime releases closed working slots");
 Check213(StringSubstr(ledger,0,StringLen(prefix))==prefix&&MDOpReplay(ledger,operational.scope,1,verified),"21305 archive preserves immutable ledger prefix and full replay");
 Check213(MDOpReconcile(verified,mock_book,f.utc,why),"21305 archived origin still present in broker history remains verifiable");
 changed=mock_book;changed.book.o[0].order.state=0;
 Check213(!MDOpReconcile(verified,changed,f.utc,why),"21305 archived origin becoming active is not hidden");
 int dates[20]={20261106,20261109,20261110,20261111,20261112,20261113,20261116,20261117,20261118,20261119,20261123,20261124,20261125,20261126,20261127,20261130,20261201,20261202,20261203,20261204};
 bool rolling=true;MDInputs inputs;inputs.high_prev=211000;inputs.low_prev=209000;inputs.close_prev=210000;inputs.open_today=210000;inputs.adjustment=210000;MDDay day;MDCalculate(inputs,day);
 for(int i=0;i<20&&rolling;i++){
  int date=dates[i];long midnight=MDCivilMidnight2026(date);MDOpState add=operational;
  rolling=MDOpAddDay(add,date,"WINZ26","SYNTHETIC_ROLLING",day,midnight+32400000,midnight+75600000,1,why)&&Commit(add,"SYNTHETIC_ROLLING_ADD");
  for(int k=0;k<add.nlevels;k++){add.levels[k].cutoff=true;add.levels[k].consumed=true;}
  add.watermark=midnight+86400000+10800000;rolling=rolling&&Commit(add,"SYNTHETIC_ROLLING_CLOSE");
  MDOpFrameReset(f,add.watermark,midnight+86400000,true,true);f.stable=true;mock_book.server_msc=f.server;
  rolling=rolling&&MDArchiveCandidate21305(operational,mock_book,f,date,candidate,why)&&Commit(candidate,"ARCHIVE21305_"+IntegerToString(date));
 }
 Check213(rolling&&operational.nlevels==0&&MDOpReplay(ledger,operational.scope,1,verified),"21305 twenty closed sessions reuse working slots with every historical revision retained");
 OnDeinit(1);
 Check213(MDFreezeDistance21305(11,10,1)&&!MDFreezeDistance21305(10,10,1)&&!MDFreezeDistance21305(9,10,1),"21305 freeze boundary is strict and measured in symbol points");
 Check213(MDFreezeDistance21305(-100,0,1)&&!MDFreezeDistance21305(100,-1,1)&&!MDFreezeDistance21305(100,1,0),"21305 zero freeze does not invent restriction and invalid metadata is rejected");
 Check213(MDResponse613(false,10016,0)==2&&MDResponse613(false,10029,0)==2,"21305 explicit stop/freeze rejection is recognized even when native API returns false");
 Check213(MDResponse613(false,10031,0)==0&&MDResponse613(false,10012,0)==0&&MDResponse613(false,0,0)==0,"21305 disconnect timeout unknown responses remain uncertain and never auto-resend");
 MDProtection schedule;MDProtectionReset(schedule);long clock=100000;
 for(int i=0;i<6;i++){if(!MDProtectionDue(schedule,clock))throw std::runtime_error("protection schedule");MDProtectionStarted(schedule,clock);MDProtectionCompleted(schedule,clock+100);clock+=2000;}
 Check213(!MDProtectionCloseRequired(schedule,schedule.sixth_completed_ms+179999,false)&&MDProtectionCloseRequired(schedule,schedule.sixth_completed_ms+180000,false)&&!MDProtectionCloseRequired(schedule,schedule.sixth_completed_ms+180000,true),"21305 six completed attempts preserve additional three-minute window and SL-present TP-only management");

 f=ResumeFixture21304();mock_reason21305[8201]=4;mock_reason21305[8202]=5;mock_profit21305[8201]=-75;mock_profit21305[8202]=27;
 string csv=MDReportBody21305(operational,mock_book,20261105);
 std::vector<std::vector<string>> csvrows;std::stringstream csvstream(csv);string csvline;
 while(std::getline(csvstream,csvline)){std::stringstream fields(csvline);string field;std::vector<string> row;while(std::getline(fields,field,';'))row.push_back(field);csvrows.push_back(row);}
 bool columns=csvrows.size()==7;for(auto &row:csvrows)columns=columns&&row.size()==30;
 Check213(columns,"21305 CSV has five levels plus total, each matching all 30 header columns");
 Check213(columns&&csvrows[2][13]=="-375.00000000"&&csvrows[3][13]=="135.00000000"&&csvrows[6][13]=="-240.00000000","21305 report reproduces native support prices as minus375 plus135 and total minus240 points");
 Check213(columns&&csvrows[6][18]=="-48.00000000"&&csvrows[6][23]=="2"&&csvrows[6][24]=="1"&&csvrows[6][25]=="1"&&csvrows[6][27]=="50.00000000","21305 report sums broker costs and per-level closed-operation win statistics");
 Check213(columns&&csvrows[2][17]=="4"&&csvrows[3][17]=="5","21305 broker SL and TP reason codes are recorded rather than inferred from price");
 Check213(StringFind(csv,"PENDENTE_BACKTEST_TEORICO_INDEPENDENTE")>=0&&csvrows[6][28]=="","21305 executed results are never mislabelled as independent Work theoretical results");
 MDOpSnapshot slipped=mock_book;for(int d=0;d<slipped.book.deals;d++)if(slipped.book.d[d].ticket==8201)slipped.deal_price[d]-=5;
 Check213(StringFind(MDReportBody21305(operational,slipped,20261105),";-380.00000000;-380.00000000;0.00000000;5.00000000;4;")>=0,"21305 SL exit slippage is measured against fixed normalized stop with adverse sign");
 Check213(MDReportPoints21305(mock_book),"21305 daily points report publishes with readback before any archive");
 string points_path="MDD21305_PONTOS_"+operational.scope+"_20261105.csv",saved_csv;
 Check213(MDOpReadFile(points_path,saved_csv)&&saved_csv==csv,"21305 published report matches verified broker snapshot");
 mock_cost_error21305=true;string unknown=MDReportBody21305(operational,mock_book,20261105);
 Check213(StringFind(unknown,";NAO_DISPONIVEL;")<0&&unknown!=csv,"21305 unavailable costs are blank with availability flag, not fabricated zero values");mock_cost_error21305=false;
 // The weighted result is per filled contract; contract-points remain a separate column.
 MDOpState one=operational;MDOpSnapshot weighted=mock_book;
 for(int d=0;d<weighted.book.deals;d++)if(weighted.book.d[d].position==2585252213)weighted.book.d[d].volume*=6;
 one.levels[1].volume=6;for(int j=0;j<weighted.book.orders;j++)if(weighted.book.o[j].order.ticket==2585252213)weighted.book.o[j].order.initial_volume=6;
 string weighted_csv=MDReportBody21305(one,weighted,20261105);
 Check213(StringFind(weighted_csv,"-375.00000000;-2250.00000000;")>=0,"21305 six filled contracts keep minus375 per-contract points and separate minus2250 contract-points");
 // Verify actual freeze decisions using symbol metadata, preserving close/protection priority.
 mock_freeze21305=10;MDOpLevel frozen=operational.levels[1];frozen.prices.entry_tick=209990;
 Check213(!MDDemoFreeze21305(frozen,3,why),"21305 a buy pending at exact freeze distance defers cancellation without altering its price");
 frozen.prices.entry_tick=209985;Check213(MDDemoFreeze21305(frozen,3,why),"21305 cancellation becomes available outside freeze zone");
 frozen.prices.sl_tick=209980;frozen.prices.tp_tick=210005;
 Check213(MDDemoFreeze21305(frozen,2,why)&&MDDemoFreeze21305(frozen,4,why),"21305 freeze never silently suppresses a protective SLTP attempt or emergency market close");mock_freeze21305=0;
 MDOpState closed_supports=operational;for(int k=0;k<closed_supports.nlevels;k++){closed_supports.levels[k].cutoff=true;closed_supports.levels[k].consumed=true;}
 long next_day=MDCivilMidnight2026(20261106)+10*3600000;mock_utc=next_day+10800000;mock_book.server_msc=next_day;closed_supports.watermark=mock_utc;
 Check213(Commit(closed_supports,"SYNTHETIC_SUPPORT_CUTOFF"),"21305 actual-price two-closed-position fixture reaches audited past cutoff");
 MDOpFrameReset(f,mock_utc,next_day,true,true);f.stable=true;prefix=ledger;

 MDOpState mixed=operational;MDOpSnapshot mixed_book=mock_book;MDDay mixed_day;MDCalculate(inputs,mixed_day);
 Check213(MDOpAddDay(mixed,20261106,"WINZ26","SIMULATED_CURRENT_DAY",mixed_day,MDCivilMidnight2026(20261106)+32400000,MDCivilMidnight2026(20261106)+75600000,1,why),"21305 mixed retention fixture adds a current session alongside closed previous session");
 MDOpLevel new_level=mixed.levels[6];new_level.order=777008;new_level.accepted_server=MDCivilMidnight2026(20261106)+32700000;
 new_level.entry.phase=6;new_level.entry.serial=1;new_level.entry.response_order=777008;new_level.consumed=true;mixed.levels[6]=new_level;
 OPOrder(mixed,mixed_book,6,777008,2,0);int new_order=mixed_book.book.orders-1;
 mixed_book.book.o[new_order].setup_msc=new_level.accepted_server;mixed_book.orders[new_order].sl=new_level.prices.sl_tick;mixed_book.orders[new_order].tp=new_level.prices.tp_tick;mixed_book.orders[new_order].position_id=777008;
 OPDeal(mixed_book,777009,777008,777008,0,1,new_level.accepted_server+1);mixed_book.book.d[mixed_book.book.deals-1].magic=MDMagic67(1,1);
 OPPosition(mixed_book,777010,777008,1,new_level.prices.sl_tick,new_level.prices.tp_tick);mixed_book.book.p[mixed_book.book.positions-1].magic=MDMagic67(1,1);
 Check213(MDOpReconcile(mixed,mixed_book,f.utc,why)&&MDArchiveCandidate21305(mixed,mixed_book,f,20261105,candidate,why)&&candidate.nlevels==5&&candidate.npositions==1&&candidate.positions[0].owner==1&&candidate.positions[0].identifier==777008&&candidate.positions[0].volume==1&&candidate.levels[1].order==777008,"21305 archiving old closed positions remaps current open-position ownership without touching ticket volume or prices");
 Check213(MDArchiveCandidate21305(operational,mock_book,f,20261105,candidate,why)&&candidate.npositions==0&&Commit(candidate,"ARCHIVE21305_20261105"),"21305 archive releases closed position slots as well as level slots");
 Check213(StringSubstr(ledger,0,StringLen(prefix))==prefix&&MDOpReplay(ledger,operational.scope,1,verified)&&MDOpReconcile(verified,mock_book,f.utc,why),"21305 archived filled orders and exact entry/exit receipts remain verifiable");
 changed=mock_book;changed.deal_price[changed.book.deals-1]+=5;
 Check213(!MDOpReconcile(verified,changed,f.utc,why),"21305 altered archived exit price is not hidden by retention policy");
 Check213(MDOpReadFile(points_path,saved_csv)&&saved_csv==csv,"21305 archived session retains its final detailed points report");
 string unchanged_state=MDOpEncode(operational);int sends_before=mock_send_calls210;
 MDLiquidityAudit21305(20261106,"IBOVESPA MINI(WINZ26)");
 Check213(MDOpEncode(operational)==unchanged_state&&mock_send_calls210==sends_before,"21305 liquidity audit records observations without changing strategy or sending orders");OnDeinit(1);

 Reset213();Check213(OnInit()==INIT_SUCCEEDED,"21305 session-file test starts same demo runtime");MDSessionRule special;
 Check213(MDDemoSession213(20261104,"WINZ26",special)&&special.cutoff==64800,"21305 no override retains verified regular demo cutoff");
 auto timetable=[](string text){std::ofstream f(full("ModeloD_Sessoes_Verificadas.csv"));f<<text;};
 string schema="Data;Contrato;Abertura;Fim;Zeragem;Verificado;Fonte\n";
 timetable(schema+"20261104;WINZ26;10:00:00;18:25:00;17:45:00;SIM;FONTE_SIMULADA_LOCAL\n");
 Check213(MDDemoSession213(20261104,"WINZ26",special)&&special.scheduled_open==36000&&special.cutoff==63900,"21305 explicit exact-date contract timetable supports nonregular opening and earlier cutoff");
 Check213(MDSessionEvaluate(special,20261104,35999,true,true)==MD_BEFORE_OPEN&&MDSessionEvaluate(special,20261104,63900,true,true)==MD_CUTOFF,"21305 reviewed special opening and cutoff control the actual session evaluator");
 mock_session_end213=17*3600;Check213(!MDDemoSession213(20261104,"WINZ26",special),"21305 broker session that cannot contain reviewed timetable is refused");mock_session_end213=18*3600+55*60;
 timetable(schema+"20261104;WINZ26;10:00:00;18:25:00;17:45:00;NAO;SEM_REVISAO\n");
 Check213(!MDDemoSession213(20261104,"WINZ26",special)&&!MDSession614(20261104,"WINZ26",special),"21305 unreviewed row cannot silently fall back to regular hours");
 timetable(schema+"20261104;WINZ26;10:00:00;18:25:00;17:45:00;SIM;LOCAL\n20261104;WINZ26;10:00:00;18:25:00;17:45:00;SIM;LOCAL\n");
 Check213(MDSessionConfig21305(20261104,"WINZ26",special)<0,"21305 duplicate exact-date contract rows are rejected");
 timetable(schema+"20261104;WINZ26;24:00:00;18:25:00;17:45:00;SIM;LOCAL\n");
 Check213(MDSessionConfig21305(20261104,"WINZ26",special)<0,"21305 invalid clock and cutoff order are rejected");
 timetable(schema);mock_utc=MDCivilMidnight2026(20260218)+14*3600000+10800000;
 Check213(!MDDemoSession213(20260218,"WINJ26",special),"21305 known Ash Wednesday without reviewed timetable cannot inherit regular09h session");
 timetable(schema+"20260218;WINJ26;13:00:00;18:25:00;18:00:00;SIM;FONTE_SIMULADA_LOCAL\n");
 Check213(MDDemoSession213(20260218,"WINJ26",special)&&special.scheduled_open==46800,"21305 exact reviewed special session can be used with compatible broker metadata");
 std::filesystem::remove(full("ModeloD_Sessoes_Verificadas.csv"));OnDeinit(1);
 Print("DEMO_21305;Checks=",checks213,";Failures=",failures213,";API_MOCK_NOT_NATIVE_MT5");return failures213?1:0;
}
