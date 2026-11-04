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
 UsarCenarioSinteticoNoTester=false;DataTester=20261030;ContratoTester="WINZ26";FusoServidorTester=-10800;_Symbol="WINZ26";
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

std::vector<MqlTick> complete_ticks212;
std::vector<MqlRates> complete_rates212;
void ResetCase212(){
 Reset210();UsarCenarioSinteticoNoTester=true;_Symbol=MD_FONTE211;VolumePorNivel=1;IntervaloSegundos=2;
 mock_expiration_modes211=SYMBOL_EXPIRATION_DAY;
 WriteDataset210("DataFonte=2026-10-29\nDataOperacional=2026-10-30\nFonte=BVBG.187.01\nStatus=OK\nQuantidadeContratos=1\nContrato.WINZ26.Ajuste=171499\nContrato.WINZ26.AjusteAnterior=173818\n");
 long prior=MDCivilMidnight2026(20261029)/1000;
 // Synthetic D1 fixture has the same pivot distances as the reviewed day.
 mock_daily_rates210={{prior-86400,170000,173030,170000,170275},{prior,170000,173030,170000,170275},
  {MDCivilMidnight2026(20261030)/1000,170910,170910,169800,169900}};
 complete_ticks212.clear();std::map<long,MqlRates> rates;
 for(int i=0;i<MD_CORTE212_COUNT;i++){
  MqlTick q;MDCorteTick212(i,q);complete_ticks212.push_back(q);long minute=q.time_msc/60000*60;
  if(!rates.count(minute))rates[minute]={minute,q.last,q.last,q.last,q.last,0,0};
  auto &bar=rates[minute];bar.high=std::max(bar.high,q.last);bar.low=std::min(bar.low,q.last);bar.close=q.last;bar.tick_volume++;bar.real_volume++;
 }
 complete_rates212.clear();for(auto &item:rates)complete_rates212.push_back(item.second);mock_rates=complete_rates212;
 mock_utc=MD_CORTE212_BEGIN+1000+10800000;mock_ticks={complete_ticks212[0],complete_ticks212[1]};mock_all_ticks=mock_ticks;
}
void SetTime212(long now){
 mock_utc=now+10800000;mock_mono+=2000;
 auto end=std::upper_bound(complete_ticks212.begin(),complete_ticks212.end(),now,[](long t,const MqlTick &q){return t<q.time_msc;});
 mock_ticks.assign(complete_ticks212.begin(),end);mock_all_ticks=mock_ticks;
}
int main(){
 std::filesystem::remove_all("/tmp/md615k_host");std::filesystem::create_directories("/tmp/md615k_host");
 ResetCase212();mock_tester210=false;Check210(OnInit()==INIT_PARAMETERS_INCORRECT&&mock_send_calls210==0,"cutoff EA refuses live chart");
 ResetCase212();UsarCenarioSinteticoNoTester=false;Check210(OnInit()==INIT_PARAMETERS_INCORRECT,"synthetic opt-in is mandatory");
 ResetCase212();_Symbol="WINZ26";Check210(OnInit()==INIT_PARAMETERS_INCORRECT,"original symbol cannot enter synthetic case");
 ResetCase212();mock_currency211="USD";Check210(OnInit()==INIT_PARAMETERS_INCORRECT,"USD refused before orders");
 ResetCase212();mock_hedge210=false;Check210(OnInit()==INIT_PARAMETERS_INCORRECT,"hedging remains mandatory");
 ResetCase212();VolumePorNivel=2;Check210(OnInit()==INIT_PARAMETERS_INCORRECT,"scenario requires exactly one contract");
 ResetCase212();IntervaloSegundos=1;Check210(OnInit()==INIT_PARAMETERS_INCORRECT,"scenario pins two-second timer");
 ResetCase212();mock_optimization210=true;Check210(OnInit()==INIT_PARAMETERS_INCORRECT,"optimization refused");
 ResetCase212();mock_daily_rates210[1].high+=30;OnInit();Bootstrap210();Check210(fatal&&mock_send_calls210==0,"incompatible geometry blocks without forcing frozen levels");OnDeinit(1);
 ResetCase212();Check210(complete_ticks212.size()==32957&&complete_rates212.size()==551,"recipe has 32957 ticks and 551 minutes");
 bool inside=true;for(auto q:complete_ticks212)if(q.time_msc>MD_CORTE212_FILL)inside=inside&&q.last>169425&&q.last<170125&&q.bid>169425&&q.ask<170125;
 Check210(inside&&complete_ticks212.back().time_msc>1793383200000,"post-fill bid ask and Last stay strictly inside protection beyond cutoff");
 mock_utc=MD_CORTE212_BEGIN/60000*60000+60000+10800000;
 Check210(MDReferenceMinute211(MD_CORTE212_BEGIN/60000*60000,complete_ticks212,complete_ticks212.size()),"closed synthetic opening minute verifies against recipe");
 auto damaged=complete_ticks212;damaged[2].ask+=5;
 Check210(!MDReferenceMinute211(MD_CORTE212_BEGIN/60000*60000,damaged,damaged.size()),"synthetic reference refuses changed quote");
 ResetCase212();bool prepared=true;AcceptOrders210(prepared);
 Check210(OnInit()==INIT_SUCCEEDED,"isolated cutoff EA initializes with recipe and reviewed B3 input");
 Bootstrap210();Check210(mock_send_calls210==5&&prepared,"same planner sends five DAY pending limits after durable records");
 bool requests=true;for(auto q:mock_requests210)requests=requests&&q.symbol==MD_FONTE211&&q.type_time==ORDER_TIME_DAY&&q.volume==1;
 Check210(requests&&operational.levels[0].prices.entry_tick==169800,"physical synthetic requests preserve model prices and logical identity");
 Check210(!CutFinal212(),"flat initialization cannot falsely certify a forced close");
 bool filled=false,early_action=false;
 mock_send210=[&prepared,&early_action](const MqlTradeRequest &q,MqlTradeResult &v){
  prepared=prepared&&DiskPrepared210(q);long now=(long)TimeCurrent()*1000;
  if(q.action==TRADE_ACTION_REMOVE){early_action=early_action||now<1793383200000;
   for(int k=0;k<mock_book.book.orders;k++)if(mock_book.book.o[k].order.ticket==(long)q.order){mock_book.book.o[k].order.state=1;mock_book.book.o[k].order.remaining=0;v.retcode=10009;return true;}
  }
  if(q.action==TRADE_ACTION_DEAL){early_action=early_action||now<1793383200000;
   int p=pos_index(q.position);if(p<0)return false;long id=mock_book.book.p[p].identifier;int k=mock_book.book.orders++;
   MDRawOrder69 o;o.order.ticket=2000+k;o.order.magic=q.magic;o.order.symbol=q.symbol;o.order.buy=false;o.order.state=2;o.order.initial_volume=q.volume;o.order.remaining=0;o.setup_msc=now;o.entry_limit=false;mock_book.book.o[k]=o;
   mock_book.orders[k].price=q.price;mock_book.orders[k].sl=0;mock_book.orders[k].tp=0;mock_book.orders[k].position_id=id;mock_book.orders[k].comment=q.comment;
   OPDeal(mock_book,100+mock_book.book.deals,o.order.ticket,id,1,q.volume,now);mock_book.deal_price[mock_book.book.deals-1]=q.price;
   for(int j=p;j+1<mock_book.book.positions;j++){mock_book.book.p[j]=mock_book.book.p[j+1];mock_book.sl[j]=mock_book.sl[j+1];mock_book.tp[j]=mock_book.tp[j+1];}
   mock_book.book.positions--;v.retcode=10009;v.order=o.order.ticket;return true;
  }
  return false;
 };
 for(long now=MD_CORTE212_BEGIN+7000;now<=MD_CORTE212_END+12000;now+=2000){
  SetTime212(now);
  if(!filled&&now>=MD_CORTE212_FILL){
   long order=operational.levels[0].order;int k=order_index(order);
   if(k>=0){
    mock_book.book.o[k].order.state=2;mock_book.book.o[k].order.remaining=0;mock_book.orders[k].position_id=8000;
    OPDeal(mock_book,10,order,8000,0,1,MD_CORTE212_FILL);mock_book.deal_price[mock_book.book.deals-1]=169800;
    OPPosition(mock_book,9000,8000,1,169425,170125);mock_book.book.p[0].symbol=MD_FONTE211;filled=true;
   }
  }
  OnTimer();
 }
 Check210(filled&&cut_pre_seen212&&cut_pre_ok212,"one protected position plus four pending remain immediately before real 18h cutoff");
 Check210(!early_action&&!cut_early_close212,"no forced close or pending cancellation before 18h");
 Check210(cut_close_sends212==1&&cut_close_first212>=1793383200000&&cut_close_first212<=1793383202000,"exactly one close is sent in first cutoff timer");
 int close_count=0,cancel_count=0,entry_count=0;bool addressed=false;
 for(auto q:mock_requests210){if(q.action==TRADE_ACTION_PENDING)entry_count++;if(q.action==TRADE_ACTION_REMOVE)cancel_count++;if(q.action==TRADE_ACTION_DEAL){close_count++;addressed=q.position==9000&&q.symbol==MD_FONTE211&&q.volume==1&&q.type==ORDER_TYPE_SELL;}}
 Check210(close_count==1&&addressed&&prepared,"close addresses exact owned ticket volume and physical source after durable prepare");
 Check210(cancel_count==4,"all four remaining pending limits are cancelled");
 Check210(mock_book.book.positions==0&&operational.positions[0].volume==0&&operational.positions[0].close.phase==6,"close effect is reconciled from receipt and exit deal, not response alone");
 Check210(entry_count==5&&!cut_late_entry212,"no duplicate or post-cutoff entries");
 Check210(cut_post_seen212&&CutFinal212(),"cutoff case passes only after pre-cut exposure and confirmed flat final inventory");
 bool old=cut_pre_ok212;cut_pre_ok212=false;Check210(!CutFinal212(),"missing pre-cut exposure invalidates acceptance");cut_pre_ok212=old;
 cut_close_sends212++;Check210(!CutFinal212(),"duplicate close invalidates acceptance");cut_close_sends212--;
 OnDeinit(1);
 Print("FOCUSED_212;Checks=",checks210,";Failures=",failures210,";API_MOCK_NOT_NATIVE_MQL5");return failures210?1:0;
}
