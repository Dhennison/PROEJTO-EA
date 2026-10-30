// Appended to the unchanged runtime mock after adapting includes/arrays for C++.
// Tests exercise actual Experts headers; simulated MT5 API, NOT native MQL5.
int checks209=0;
void Check209(bool value,const char *label){
 if(!value){std::cerr<<"FAIL_209 "<<label<<'\n';std::exit(1);}
 checks209++;std::cout<<"PASS_209 "<<label<<'\n';
}
MDDataEvidence Data209(){
 MDDataEvidence d{};d.date=20261028;d.previous_date=20261027;d.adjustment_date=d.date;d.source_date=d.previous_date;d.expiry_date=20261216;
 d.contract="WINZ26";d.ohlc_contract=d.contract;d.opening_contract=d.contract;d.adjustment_contract=d.contract;d.source="BVBG.187.01";
 d.ohlc_verified=true;d.opening_verified=true;d.adjustment_verified=true;d.previous_adjustment=100;d.tick_size=5;
 d.values.high_prev=120;d.values.low_prev=80;d.values.close_prev=100;d.values.open_today=100;d.values.adjustment=100;
 MDSessionSet(d.date,32400,66300,64800,true,"FOCUSED_FIXTURE_209",d.session);
 d.open_msc=MDCivilMidnight2026(d.date)+32400000;return d;
}
void PrepareFrame209(MDDataEvidence data,long cursor){
 MDObserverStart615(obs615,Scope615());obs615.visible=true;obs615.frozen=true;obs615.data=data;
 stream615.data=data;stream615.cursor=cursor;stream615.ready=true;stream615.audit.valid=true;
 stream615.audit.count=10;stream615.audit.last_msc=cursor-1;stream615.audit.last_price=120;
 MDOpInit(operational,Scope615(),1);operational.nlevels=5;
 for(int i=0;i<5;i++){
  MDLevel p{};p.id=i;p.buy=true;p.valid_open=true;p.entry=100;p.sl=90;p.tp=110;p.entry_tick=100;p.sl_tick=90;p.tp_tick=110;
  stream615.control.day.levels[i]=p;stream615.audit.touches[i].tape.touched=false;
  auto &l=operational.levels[i];l.prices=p;l.date=data.date;l.level=i;l.symbol=data.contract;l.volume=1;l.cutoff_utc=cursor+10800000+3600000;
 }
 stream_started615=true;stream_failed615=false;stream_reported615=cursor;MDReset132(retry132);
 opclock.ok=true;opclock.offset=-10800;opclock.server=cursor+2000;opclock.utc=opclock.server+10800000;
 mock_connected=true;mock_tick_error=false;mock_partial209=false;mock_stop209=false;mock_drop209=false;mock_raw209=false;mock_stop_in_read209=false;
 report615=INVALID_HANDLE;coverage_last209="";
}
int main(){
 MDDataEvidence data=Data209();const long opening=data.open_msc,minute=opening+60000;string why,detail;
 PrepareFrame209(data,minute);
 mock_ticks={{minute-1,120,8},{minute+1,120,8}};MDCoverage209 coverage;
 Check209(MDCurrentCoverage209(stream615,minute+2000,coverage,why,detail),"coverage ignores prior-millisecond SLTP boundary of level zero");
 MDOpFrame frame;int before=mock_copy209;BuildFrame(frame,true);
 bool ready=true;for(int i=0;i<5;i++)ready=ready&&frame.entry_ready[i];
 Check209(ready&&mock_copy209==before+1,"actual BuildFrame verifies all five levels with ONE common tail query");
 stream615.control.day.levels[0].tp=130;BuildFrame(frame,true);ready=true;
 for(int i=0;i<5;i++)ready=ready&&frame.entry_ready[i];
 Check209(ready,"coverage stays valid when only level-zero SLTP changes");
 before=mock_copy209;Check209(MDCurrentCoverage209(stream615,minute,coverage,why,detail)&&mock_copy209==before,"zero-length tail needs no query");
 before=mock_copy209;Check209(!MDCurrentCoverage209(stream615,minute-1,coverage,why,detail)&&mock_copy209==before,"regressed target is rejected before query");
 Check209(!MDCurrentCoverage209(stream615,minute+60001,coverage,why,detail),"tail exceeding one minute is refused");
 for(int i=0;i<5;i++)stream615.control.day.levels[i].entry=100+i*5;
 mock_ticks={{minute+1,95,8}};
 Check209(MDCurrentCoverage209(stream615,minute+2000,coverage,why,detail)&&coverage.touched[0]&&coverage.touched[4]&&coverage.first[0]==minute+1,"gap across levels records earliest trade timestamp without inventing a trade on each line");
 mock_ticks={{minute+1,95,8},{minute+2,96,1}};
 Check209(!MDCurrentCoverage209(stream615,minute+2000,coverage,why,detail)&&!coverage.touched[0]&&why=="TICK_INVALIDO","later invalid tick discards entire candidate including prior touch");
 mock_ticks={{minute+1,0,8}};Check209(!MDCurrentCoverage209(stream615,minute+2000,coverage,why,detail),"nonpositive Last rejected");
 mock_ticks={{minute+1,std::nan(""),8}};Check209(!MDCurrentCoverage209(stream615,minute+2000,coverage,why,detail),"nonfinite Last rejected");
 mock_ticks={{minute+10,120,8},{minute+9,120,8}};Check209(!MDCurrentCoverage209(stream615,minute+2000,coverage,why,detail),"timestamp regression rejected");
 mock_ticks={{minute+1,120,8},{minute+1,120,8}};Check209(MDCurrentCoverage209(stream615,minute+2000,coverage,why,detail),"same-millisecond chronological events are retained without deduplication");
 mock_raw209=true;mock_ticks={{minute-1,120,8}};Check209(!MDCurrentCoverage209(stream615,minute+2000,coverage,why,detail),"out-of-window response rejected");mock_raw209=false;
 mock_ticks={{minute+1,95,8}};mock_partial209=true;
 Check209(!MDCurrentCoverage209(stream615,minute+2000,coverage,why,detail)&&why=="COPY_TICKS_ERRO_4403"&&!coverage.touched[0],"partial timeout cannot publish touch or coverage");
 BuildFrame(frame,true);bool blocked=true;for(int i=0;i<5;i++)blocked=blocked&&!frame.entry_ready[i];
 Check209(blocked&&StringFind(diagnostic_last[7],"causa=COPY_TICKS_ERRO_4403")>=0,"actual entry diagnostic preserves exact coverage failure cause");mock_partial209=false;
 mock_tick_error=true;Check209(!MDCurrentCoverage209(stream615,minute+2000,coverage,why,detail),"hard API error rejected");mock_tick_error=false;
 mock_connected=false;before=mock_copy209;Check209(!MDCurrentCoverage209(stream615,minute+2000,coverage,why,detail)&&mock_copy209==before,"disconnection before read blocks without query");mock_connected=true;
 mock_drop209=true;Check209(!MDCurrentCoverage209(stream615,minute+2000,coverage,why,detail)&&why=="DESCONECTADO_APOS_COLETA","disconnection during read cannot certify coverage");mock_drop209=false;mock_connected=true;
 mock_stop209=true;before=mock_copy209;Check209(!MDCurrentCoverage209(stream615,minute+2000,coverage,why,detail)&&mock_copy209==before,"manual interruption before read makes no query");mock_stop209=false;
 mock_stop_in_read209=true;Check209(!MDCurrentCoverage209(stream615,minute+2000,coverage,why,detail)&&why=="COLETA_INTERROMPIDA","manual interruption inside API cannot publish candidate");mock_stop_in_read209=false;mock_stop209=false;
 mock_ticks={{minute,120,8},{minute+1000,125,8},{minute+2000,115,8},{minute+3000,120,8}};
 mock_rates={{minute/1000,120,125,115,120}};
 Check209(MDCurrentCoverage209(stream615,minute+60000,coverage,why,detail),"complete minute requires and passes exact M1 consistency");
 mock_rates[0].high=130;Check209(!MDCurrentCoverage209(stream615,minute+60000,coverage,why,detail)&&why=="MINUTO_COMPLETO_NAO_CONFERE_M1","complete-minute M1 divergence is rejected");
 mock_rates.clear();Check209(!MDCurrentCoverage209(stream615,minute+60000,coverage,why,detail),"complete minute with missing M1 is rejected");
 MDOpTrail trail;MDLevel protect{};protect.buy=true;protect.entry=100;protect.sl=90;protect.tp=110;
 mock_ticks={{minute,90,8},{minute+1,100,8}};MDOpTrailInit(trail,"WINZ26",minute,protect);
 Check209(!MDOpTrailRead(trail,minute+2000,why)&&trail.ambiguous,"position-origin ambiguity protection remains unchanged");
 MDQuery209 first,second;MDQueryReset209(first,"TRADE",minute,minute+59999);MDQueryReset209(second,"TRADE",minute,minute+59999);
 MDQueryTick209(first,minute,100,8);MDQueryTick209(first,minute+1,120,8);
 MDQueryTick209(second,minute,100,8);MDQueryTick209(second,minute+1,120,8);
 Check209(first.tick_hash==second.tick_hash,"identical observed sequence yields identical diagnostic signature");
 MDQueryTick209(second,minute+1,120,8);Check209(first.tick_hash!=second.tick_hash&&second.accepted==3,"added same-millisecond event changes signature and count");
 MDQueryReset209(second,"TRADE",minute,minute+59999);MDQueryTick209(second,minute,100,16);MDQueryTick209(second,minute+1,120,8);
 Check209(first.tick_hash!=second.tick_hash,"flag change is visible in sequence signature");
 MDQueryBar209(first,0,minute,100,120,100,110);MDQueryBar209(second,0,minute,100,125,100,110);
 Check209(first.m1_hash!=second.m1_hash,"M1 change has independent diagnostic signature");
 MDRetry132 schedule;MDReset132(schedule);MDFail132(schedule,opening,opening+59999,1000);
 Check209(!MDDue132(schedule,30999)&&MDDue132(schedule,31000),"fast retry respects 30-second spacing");
 MDFail132(schedule,opening,opening+59999,301000);Check209(schedule.started==1000,"retry never restarts original acquisition age");
 Check209(!MDEnterSlow132(schedule,600999)&&MDEnterSlow132(schedule,601000)&&schedule.next==721000,"exact ten-minute transition schedules 120-second slow probe");
 Check209(!MDDue132(schedule,720999)&&MDDue132(schedule,721000),"slow phase is bounded by its own two-minute interval");
 Check209(MDCanCommit132(schedule,opening,opening+59999,901000),"late fully validated candidate remains eligible after ten minutes");
 Check209(!MDCanCommit132(schedule,opening+1,opening+59999,901000)&&!MDCanCommit132(schedule,opening,opening+59999,999),"late admission still rejects changed window or monotonic regression");
 // Actual coordinator: both feeds diverge; preserve candidate, enter slow mode, recover later.
 PrepareFrame209(data,minute);MDStreamStart615(stream615,data);obs615.data=data;obs615.scope=Scope615();owns615=true;
 mock_ticks={{opening,100,8},{opening+1000,110,8},{opening+60500,110,8}};mock_all_ticks=mock_ticks;
 mock_rates={{opening/1000,100,120,100,110}};mock_mono=1000;
 const long original_revision=operational.revision,original_cutoff=operational.levels[0].cutoff_utc;
 Pump615();const long incomplete_signature=query_trade209.tick_hash;
 Check209(retry132.active&&retry132.failures==1&&stream615.cursor==opening&&stream615.audit.count==0,"actual Pump rejects both divergent feeds without moving cursor or consuming ticks");
 Check209(query_trade209.returned==2&&query_all209.accepted==2&&query_trade209.h==110&&query_trade209.m1_h==120,"rejected query retains both feed counts and mismatching OHLC evidence");
 before=mock_copy209;mock_mono=601000;Pump615();
 Check209(retry132.slow&&!stream_failed615&&mock_copy209==before&&stream615.cursor==opening,"actual Pump enters slow monitoring instead of permanent failure");
 BuildFrame(frame,true);blocked=true;for(int i=0;i<5;i++)blocked=blocked&&!frame.entry_ready[i];
 Check209(blocked&&StringFind(diagnostic_last[7],"RECUPERACAO_EM_MONITORAMENTO_LENTO")>=0,"new entries remain blocked throughout slow monitoring");
 mock_mono=720999;Pump615();Check209(mock_copy209==before,"no repeated query during slow cooldown");
 mock_mono=721000;Pump615();Check209(retry132.active&&retry132.slow&&retry132.started==1000&&stream615.audit.count==0,"still-divergent slow probe preserves initial age and approved state");
 mock_ticks={{opening,100,8},{opening+700,120,8},{opening+1000,110,8},{opening+60500,110,8}};mock_all_ticks=mock_ticks;
 mock_mono=841000;Pump615();
 Check209(!retry132.active&&!stream_failed615&&stream615.cursor==opening+60000&&stream615.audit.count==3,"actual coordinator recovers consistent data after fourteen minutes without restart");
 Check209(query_trade209.returned==3&&query_trade209.h==120&&query_trade209.tick_hash!=incomplete_signature&&!query_all209.attempted,"successful TRADE query records changed count, restored high and new signature");
 Pump615();Check209(stream615.audit.count==3,"recovery and next timer cannot duplicate accepted ticks");
 Check209(operational.revision==original_revision&&operational.levels[0].cutoff_utc==original_cutoff,"acquisition recovery never rewrites journal revision or operational deadlines");
 MDOpState existing,next;MDOpSnapshot book;MDOpFrame deadline;OPFilled(existing,book,deadline);
 for(int k=0;k<existing.nlevels;k++)existing.levels[k].cutoff_utc=500000;
 MDOpFrameReset(deadline,600000,600000,true,false);MDFail132(retry132,opening,opening+59999,1000);retry132.slow=true;
 Check209(MDOpCycle(existing,book,deadline,next,why)&&next.levels[0].cutoff&&next.positions[0].close.phase==1,
  "cutoff planning continues without data coverage or connection while acquisition is degraded");
 std::cout<<"FOCUSED_209;Checks="<<checks209<<";Failures=0;API_SIMULADA;NAO_E_COMPILACAO_MQL5\n";
}
