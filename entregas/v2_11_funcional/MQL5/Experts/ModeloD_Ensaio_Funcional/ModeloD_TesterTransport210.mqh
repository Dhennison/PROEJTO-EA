#ifndef MD_TESTER_TRANSPORT210
#define MD_TESTER_TRANSPORT210
// Application adapter: SAME integrated planner/ledger. No live-account transport.
long tester_prepared210=0,tester_sent210=0,tester_responses210=0;
string tester_deals210=";",tester_blocks210[256];
void MDTesterBlocked210(int slot,string why)
{
 if(slot<0||slot>=256)return;
 if(tester_blocks210[slot]!=why){tester_blocks210[slot]=why;Report615("TESTER_TRANSPORT_BLOCKED;slot="+IntegerToString(slot)+";reason="+why);}
}
bool MDTesterFresh210(MDOpFrame &frame,string &why)
{
 if(!MDTesterGate210()||fatal||!owns615||lock615==INVALID_HANDLE||Scope615()!=operational.scope||IsStopped())
 {why="TESTER_CONTEXT_OR_LOCK_INVALID";return false;}
 if(!MDOpClockRead(opclock,operational.watermark,why)||MDDateValue614((datetime)(opclock.server/1000))!=DataTester)return false;
 long began=(long)GetTickCount64();
 datetime start=(datetime)(MDCivilMidnight2026(DataTester)/1000-86400);
 if(!MDOpCollect(start,inventory_a,why)||!MDOpCollect(start,inventory_b,why))return false;
 bool stable=MDOpSameSnapshot(inventory_a,inventory_b)&&((long)GetTickCount64()-began<=3000);
 // Bind newly observed receipts BEFORE building origin-specific tick trails.
 // Otherwise a new pending could be cancelled using a frame built while its order was still unknown.
 if(stable){
  MDOpState observed=operational;
  if(!MDOpReconcile(observed,inventory_b,opclock.utc,why)||!Commit(observed,"TESTER_RECEIPT_RECONCILIATION"))return false;
 }
 BuildFrame(frame,stable);
 if((long)GetTickCount64()-began>3000||Scope615()!=operational.scope||!MDTesterGate210())frame.stable=false;
 MDOpState reconciled;
 if(!MDOpCycle(operational,inventory_b,frame,reconciled,why))return false;
 if(!Commit(reconciled,"TESTER_FRESH_RECONCILIATION"))return false;
 return frame.stable&&frame.connected&&frame.clock_ok&&why=="ALL_CHAINS_RECONCILED";
}
bool MDTesterRequest210(const MDOpState &s,int owner,int position,int kind,MqlTradeRequest &r,string &why)
{
 ZeroMemory(r);
 if(!MDTesterGate210()||owner<0||owner>=s.nlevels){why="TESTER_REQUEST_CONTEXT";return false;}
 MDOpLevel l=s.levels[owner];
 if(l.date!=DataTester||l.symbol!=ContratoTester){why="TESTER_REQUEST_IDENTITY";return false;}
 r.symbol=l.symbol;r.magic=(ulong)MDMagic67(s.instance,l.level);r.comment=MDOpComment(l);
 r.type_time=ORDER_TIME_GTC;r.type_filling=ORDER_FILLING_RETURN;
 if(kind==1){
  r.action=TRADE_ACTION_PENDING;r.type=l.prices.buy?ORDER_TYPE_BUY_LIMIT:ORDER_TYPE_SELL_LIMIT;
  r.volume=l.volume;r.price=l.prices.entry_tick;r.sl=l.prices.sl_tick;r.tp=l.prices.tp_tick;
 }else if(kind==3){
  if(l.order<=0){why="TESTER_CANCEL_WITHOUT_BOUND_ORIGIN";return false;}
  r.action=TRADE_ACTION_REMOVE;r.order=(ulong)l.order;
 }else{
  if(position<0||position>=s.npositions||s.positions[position].owner!=owner){why="TESTER_POSITION_OWNER";return false;}
  MDOpPosition v=s.positions[position];
  if(v.ticket<=0||v.identifier<=0||v.volume<=0){why="TESTER_POSITION_UNAVAILABLE";return false;}
  r.position=(ulong)v.ticket;
  if(kind==2){r.action=TRADE_ACTION_SLTP;r.sl=l.prices.sl_tick;r.tp=l.prices.tp_tick;}
  else if(kind==4){
   MqlTick quote;long filling=0,execution=0;
   if(!MDSymbolInfoTick211(l.symbol,quote)||!MDSymbolInfoInteger211(l.symbol,SYMBOL_FILLING_MODE,filling)||
      !MDSymbolInfoInteger211(l.symbol,SYMBOL_TRADE_EXEMODE,execution)){why="TESTER_CLOSE_PROPERTIES";return false;}
   r.action=TRADE_ACTION_DEAL;r.type=l.prices.buy?ORDER_TYPE_SELL:ORDER_TYPE_BUY;
   r.volume=v.volume;r.price=l.prices.buy?quote.bid:quote.ask;
   if(!MDPositive(r.price)){why="TESTER_CLOSE_QUOTE_INVALID";return false;}
   if((filling&SYMBOL_FILLING_FOK)!=0)r.type_filling=ORDER_FILLING_FOK;
   else if((filling&SYMBOL_FILLING_IOC)!=0)r.type_filling=ORDER_FILLING_IOC;
   else if(execution==SYMBOL_TRADE_EXECUTION_MARKET){why="TESTER_CLOSE_NO_ALLOWED_FILLING";return false;}
  }else{why="TESTER_ACTION_INVALID";return false;}
 }
 if(kind==1||kind==4){
  MDExecGate613 volume;volume.volume_min=0;volume.volume_max=0;volume.volume_step=0;
  if(!MDSymbolInfoDouble211(l.symbol,SYMBOL_VOLUME_MIN,volume.volume_min)||
     !MDSymbolInfoDouble211(l.symbol,SYMBOL_VOLUME_MAX,volume.volume_max)||
     !MDSymbolInfoDouble211(l.symbol,SYMBOL_VOLUME_STEP,volume.volume_step)||!MDVolume613(r.volume,volume))
  {why="TESTER_VOLUME_INVALID";return false;}
 }
 why="TESTER_REQUEST_BUILT";return true;
}
void MDTesterReportDeals210()
{
 if(!MDTesterGate210())return;
 for(int i=0;i<inventory_b.book.deals;i++){
  MDDeal68 d=inventory_b.book.d[i];string id=";"+IntegerToString(d.ticket)+";";
  if(StringFind(tester_deals210,id)>=0)continue;
  int owner=-1;
  for(int k=0;k<operational.nlevels;k++)if(operational.levels[k].order==d.order){owner=k;break;}
  if(owner<0)for(int p=0;p<operational.npositions;p++)if(operational.positions[p].identifier==d.position){owner=operational.positions[p].owner;break;}
  if(owner<0)continue;
  MDOpLevel l=operational.levels[owner];double profit=0,commission=0,swap=0,fee=0;
  bool costs=DD69((ulong)d.ticket,DEAL_PROFIT,profit)&&DD69((ulong)d.ticket,DEAL_COMMISSION,commission)&&
   DD69((ulong)d.ticket,DEAL_SWAP,swap)&&DD69((ulong)d.ticket,DEAL_FEE,fee)&&
   MathIsValidNumber(profit)&&MathIsValidNumber(commission)&&MathIsValidNumber(swap)&&MathIsValidNumber(fee);
  Report615("TESTER_DEAL;ticket="+IntegerToString(d.ticket)+";order="+IntegerToString(d.order)+";position_id="+IntegerToString(d.position)+
   ";date="+IntegerToString(l.date)+";contract="+l.symbol+";level="+IntegerToString(l.level)+";msc="+IntegerToString(d.msc)+
   ";entry_kind="+IntegerToString(d.entry)+";buy="+IntegerToString(d.buy?1:0)+";volume="+DoubleToString(d.volume,8)+
   ";executed="+DoubleToString(inventory_b.deal_price[i],8)+";entry_math="+DoubleToString(l.prices.entry,8)+
   ";entry_requested="+DoubleToString(l.prices.entry_tick,8)+";SL_fixed="+DoubleToString(l.prices.sl_tick,8)+";TP_fixed="+DoubleToString(l.prices.tp_tick,8)+
   ";costs_available="+IntegerToString(costs?1:0)+";profit="+DoubleToString(profit,8)+";commission="+DoubleToString(commission,8)+
   ";swap="+DoubleToString(swap,8)+";fee="+DoubleToString(fee,8)+";SIMULATED_EXECUTION_NOT_WORK_COMPARISON");
  tester_deals210+=IntegerToString(d.ticket)+";";
 }
}
void MDTesterDispatch210()
{
 if(!MDTesterGate210()||fatal||!owns615||IsStopped())return;
 bool entry_sent[MDOP_LEVELS],cancel_sent[MDOP_LEVELS],protect_sent[MDOP_POSITIONS],close_sent[MDOP_POSITIONS];
 for(int k=0;k<MDOP_LEVELS;k++){entry_sent[k]=false;cancel_sent[k]=false;}
 for(int p=0;p<MDOP_POSITIONS;p++){protect_sent[p]=false;close_sent[p]=false;}
 // Each action/origin is considered at most once per timer. No tight retry loop.
 for(int iteration=0;iteration<2*MDOP_LEVELS+2*MDOP_POSITIONS;iteration++){
  MDOpFrame frame;string why;
  if(!MDTesterFresh210(frame,why)){MDTesterBlocked210(255,why);return;}
  MDTesterReportDeals210();
  int owner=-1,position=-1,kind=0,slot=0;
  for(int p=0;p<operational.npositions&&kind==0;p++)if(!close_sent[p]&&operational.positions[p].close.phase==1){position=p;owner=operational.positions[p].owner;kind=4;slot=192+p;}
  for(int k=0;k<operational.nlevels&&kind==0;k++)if(!cancel_sent[k]&&operational.levels[k].cancellation.phase==1){owner=k;kind=3;slot=64+k;}
  for(int p=0;p<operational.npositions&&kind==0;p++)if(!protect_sent[p]&&operational.positions[p].protect.phase==1){position=p;owner=operational.positions[p].owner;kind=2;slot=128+p;}
  for(int k=0;k<operational.nlevels&&kind==0;k++)if(!entry_sent[k]&&operational.levels[k].entry.phase==1){owner=k;kind=1;slot=k;}
  if(kind==0)return;
  if(kind==1)entry_sent[owner]=true;
  if(kind==3)cancel_sent[owner]=true;
  if(kind==2)protect_sent[position]=true;
  if(kind==4)close_sent[position]=true;
  if(kind==1&&!frame.entry_ready[owner]){MDTesterBlocked210(slot,"ENTRY_NO_LONGER_ELIGIBLE");continue;}
  MDOpState attempted=operational;
  if(!MDOpBegin(attempted,owner,position,kind,frame.utc,frame.clock_ok,true)){MDTesterBlocked210(slot,"BEGIN_REFUSED");continue;}
  MqlTradeRequest request;
  if(!MDTesterRequest210(attempted,owner,position,kind,request,why)){MDTesterBlocked210(slot,why);continue;}
  long began=(long)GetTickCount64();
  if(!Commit(attempted,"TESTER_PREPARE_BEFORE_SEND"))return;
  tester_prepared210++;
  // A permit exists ONLY in this call stack after confirmed publication/readback.
  bool permit=MDTesterGate210()&&!fatal&&owns615&&lock615!=INVALID_HANDLE&&Scope615()==operational.scope&&
   !IsStopped()&&(long)GetTickCount64()-began<=3000;
  if(!MDClaimOnce613(permit)){MDTesterBlocked210(slot,"PREPARED_BUT_NOT_SENT_RECONCILE_NO_AUTOMATIC_RESEND");return;}
  if(!MDTesterGate210()){MDTesterBlocked210(slot,"TESTER_GATE_CHANGED");return;}
  MDOpAction action;
  if(kind==1)action=operational.levels[owner].entry;else if(kind==3)action=operational.levels[owner].cancellation;
  else if(kind==2)action=operational.positions[position].protect;else action=operational.positions[position].close;
  Report615("TESTER_REQUEST;kind="+IntegerToString(kind)+";key="+IntegerToString(operational.levels[owner].key)+
   ";serial="+IntegerToString(action.serial)+";revision="+IntegerToString(operational.revision)+";order="+IntegerToString((long)request.order)+
   ";position="+IntegerToString((long)request.position)+";volume="+DoubleToString(request.volume,8)+";price="+DoubleToString(request.price,8)+
   ";sl="+DoubleToString(request.sl,8)+";tp="+DoubleToString(request.tp,8)+";SIMULATED_ONLY");
  MqlTradeResult result;ZeroMemory(result);ResetLastError();
  if(!MDTesterGate210()||fatal||!owns615||lock615==INVALID_HANDLE||Scope615()!=operational.scope||IsStopped()||
     (long)GetTickCount64()-began>3000){MDTesterBlocked210(slot,"PERMIT_EXPIRED_BEFORE_SEND_RECONCILE");return;}
  // The only send site in this release. Every path here requires native MQL_TESTER.
  bool api_ok=MDOrderSend211(request,result);int error=GetLastError();tester_sent210++;
  long completed=(long)TimeCurrent()*1000-(long)FusoServidorTester*1000;
  MDOpState response=operational;
  if(!MDOpResponse(response,owner,position,kind,action.serial,completed,api_ok,(long)result.retcode,(long)result.retcode_external,(long)result.order)){
   fatal=true;Report615("TESTER_RESPONSE_BLOCKED;RECONCILE_PRESERVE_FILES");return;
  }
  if(!Commit(response,"TESTER_RESPONSE_NOT_EXECUTION_PROOF"))return;
  tester_responses210++;
  Report615("TESTER_RESPONSE;kind="+IntegerToString(kind)+";serial="+IntegerToString(action.serial)+";api_ok="+IntegerToString(api_ok?1:0)+
   ";retcode="+IntegerToString((long)result.retcode)+";external="+IntegerToString((long)result.retcode_external)+
   ";order="+IntegerToString((long)result.order)+";deal="+IntegerToString((long)result.deal)+";error="+IntegerToString(error)+";EFFECT_REQUIRES_RECONCILIATION");
 }
}
#endif
