#ifndef MODELOD_OPERATIONAL
#define MODELOD_OPERATIONAL
#include "ModeloD_Core.mqh"
#include "ModeloD_Collect.mqh"
#include "ModeloD_Context.mqh"
#include "ModeloD_Protection.mqh"
#include "ModeloD_Execution.mqh"
// Integrated domain model. No transport and no dependency on TEST_ONLY stores.
#define MDOP_LEVELS 40
#define MDOP_POSITIONS 64
// phase: 0 absent, 1 durable intention, 2 attempted/uncertain,
// 3 response awaiting reconciliation, 4 retryable rejection, 5 definitive rejection,
// 6 effect verified, 7 superseded before attempt.
struct MDOpAction {
 int kind,phase;long serial,ticket,identifier,started,completed,retcode,response_order;
 double volume,baseline_exit;
};
struct MDOpLevel {
 int date,level;string symbol,fingerprint,deal_receipts;MDLevel prices;
 long key,open_server,cutoff_utc,touch_server,order,accepted_server;
 double volume;bool consumed,cancel,closing,cutoff,conflict;
 MDOpAction entry,cancellation;
};
struct MDOpPosition {
 int owner;long identifier,ticket,first_server;double entered,exited,volume,sl,tp;
 bool closing;MDProtection protection;MDOpAction protect,close;
};
struct MDOpState {
 string scope;int instance,nlevels,npositions;long revision,watermark;
 MDOpLevel levels[MDOP_LEVELS];MDOpPosition positions[MDOP_POSITIONS];
};
struct MDOpOrderExtra {double price,sl,tp;long position_id;string comment;};
struct MDOpSnapshot {
 MDSnapshot69 book;MDOpOrderExtra orders[256];double sl[64],tp[64],deal_price[4096];long server_msc;bool execution_prices_known;
};
struct MDOpFrame {
 long utc,server;bool clock_ok,connected,stable;
 bool entry_ready[MDOP_LEVELS],touched[MDOP_LEVELS],pending_history[MDOP_LEVELS],pending_boundary[MDOP_LEVELS];
 long first_touch[MDOP_LEVELS];
 bool position_history[MDOP_POSITIONS],position_boundary[MDOP_POSITIONS];
};
// Registry is rebuilt only from verified append-only journal events.
string retired_registry21305="";
bool MDRegistryRetired21305(const MDOpState &s,const MDOpSnapshot &snapshot,int index);
bool MDOpIdentityText(string s) {
 if(StringLen(s)<1||StringLen(s)>512)return false;
 for(int i=0;i<StringLen(s);i++){int c=StringGetCharacter(s,i);if(!((c>=48&&c<=57)||(c>=65&&c<=90)||(c>=97&&c<=122)||c==95||c==46||c==45))return false;}return true;
}
void MDOpActionReset(MDOpAction &a,int kind) {
 a.kind=kind;a.phase=0;a.serial=0;a.ticket=0;a.identifier=0;a.started=0;a.completed=0;
 a.retcode=0;a.response_order=0;a.volume=0;a.baseline_exit=0;
}
bool MDOpBusy(const MDOpAction &a){return a.phase==2||a.phase==3;}
void MDOpInit(MDOpState &s,string scope,int instance) {
 s.scope=scope;s.instance=instance;s.nlevels=0;s.npositions=0;s.revision=0;s.watermark=0;
 // Initialize every slot before whole-structure copies, including unused capacity.
 for(int i=0;i<MDOP_LEVELS;i++) {
  MDOpLevel l;l.date=0;l.level=0;l.symbol="";l.fingerprint="";l.deal_receipts="";
  MDLevel price;price.id=0;price.buy=false;price.valid_open=false;price.geometry_blocked=false;
  price.entry=0;price.sl=0;price.tp=0;price.entry_tick=0;price.sl_tick=0;price.tp_tick=0;l.prices=price;
  l.key=0;l.open_server=0;l.cutoff_utc=0;l.touch_server=0;l.order=0;l.accepted_server=0;l.volume=0;
  l.consumed=false;l.cancel=false;l.closing=false;l.cutoff=false;l.conflict=false;
  MDOpActionReset(l.entry,1);MDOpActionReset(l.cancellation,3);s.levels[i]=l;
 }
 for(int i=0;i<MDOP_POSITIONS;i++) {
  MDOpPosition v;v.owner=0;v.identifier=0;v.ticket=0;v.first_server=0;
  v.entered=0;v.exited=0;v.volume=0;v.sl=0;v.tp=0;v.closing=false;
  MDProtectionReset(v.protection);MDOpActionReset(v.protect,2);MDOpActionReset(v.close,4);s.positions[i]=v;
 }
}
void MDOpFrameReset(MDOpFrame &f,long utc,long server,bool clock,bool connected) {
 f.utc=utc;f.server=server;f.clock_ok=clock;f.connected=connected;f.stable=false;
 for(int i=0;i<MDOP_LEVELS;i++){
  f.entry_ready[i]=false;f.touched[i]=false;f.first_touch[i]=0;
  f.pending_history[i]=false;f.pending_boundary[i]=false;
 }
 for(int i=0;i<MDOP_POSITIONS;i++){f.position_history[i]=false;f.position_boundary[i]=false;}
}
int MDOpFindLevel(const MDOpState &s,int date,int level) {
 for(int i=0;i<s.nlevels;i++)if(s.levels[i].date==date&&s.levels[i].level==level)return i;
 return -1;
}
int MDOpFindPosition(const MDOpState &s,int owner,long identifier) {
 for(int i=0;i<s.npositions;i++)if(s.positions[i].owner==owner&&s.positions[i].identifier==identifier)return i;
 return -1;
}
bool MDOpAddDay(MDOpState &s,int date,string symbol,string fingerprint,const MDDay &day,
 long open_server,long cutoff_utc,double volume,string &why) {
 why="DAY_INVALID";
 if(!MDDateValid67(date)||!MDToken67(symbol)||!MDOpIdentityText(fingerprint)||open_server<=0||cutoff_utc<=0||
 !MDPositive(volume)||volume!=MathFloor(volume))return false;
 for(int i=0;i<5;i++) {
  int k=MDOpFindLevel(s,date,i);
  if(k>=0){
   if(s.levels[k].symbol!=symbol||s.levels[k].fingerprint!=fingerprint||s.levels[k].cutoff_utc!=cutoff_utc||s.levels[k].volume!=volume){
    for(int j=0;j<s.nlevels;j++)if(s.levels[j].date==date)s.levels[j].conflict=true;
    why="FROZEN_DATA_CHANGED";return false;
   }
  }
 }
 if(MDOpFindLevel(s,date,0)>=0){why="DAY_REUSED";return true;}
 if(s.nlevels+5>MDOP_LEVELS){why="CAPACITY_DAYS_NO_AUTOMATIC_PRUNING";return false;}
 for(int i=0;i<5;i++) {
  int k=s.nlevels++;MDOpLevel l;l.date=date;l.level=i;l.symbol=symbol;l.fingerprint=fingerprint;l.prices=day.levels[i];
  l.key=(long)date*10+i;l.open_server=open_server;l.cutoff_utc=cutoff_utc;l.volume=volume;
  l.deal_receipts="";l.touch_server=0;l.order=0;l.accepted_server=0;l.consumed=false;l.cancel=false;l.closing=false;l.cutoff=false;l.conflict=false;
  MDOpActionReset(l.entry,1);MDOpActionReset(l.cancellation,3);s.levels[k]=l;
 }
 why="DAY_FROZEN";return true;
}
string MDOpComment(const MDOpLevel &l){return "MD"+IntegerToString(l.key)+"A"+IntegerToString(l.entry.serial);}
bool MDOpTransient(long retcode) {
 return retcode==10004||retcode==10020||retcode==10021||retcode==10024||retcode==10018||retcode==10028||retcode==10029;
}
// Intention is separate from an attempt. Refreshing an intention never increments serial.
void MDOpIntent(MDOpAction &a,int kind,long ticket,long identifier,double volume,double exited) {
 if(MDOpBusy(a)||a.phase==5)return;
 if(a.phase==1&&a.ticket==ticket&&a.identifier==identifier&&a.volume==volume)return;
 if(a.phase==6&&a.ticket==ticket&&a.identifier==identifier&&kind==3)return;
 a.kind=kind;a.phase=1;a.ticket=ticket;a.identifier=identifier;a.volume=volume;a.baseline_exit=exited;
 a.started=0;a.completed=0;a.retcode=0;a.response_order=0;
}
// Candidate mutation only. Caller MUST commit/re-read the whole ledger before any future transport.
// The DEMO dispatcher calls it only after fresh reconciliation and before durable PREPARE.
bool MDOpBegin(MDOpState &s,int owner,int position,int kind,long utc,bool clock,bool reconciled) {
 if(!clock||!reconciled||utc<s.watermark||owner<0||owner>=s.nlevels)return false;
 MDOpAction a;
 if(kind==1)a=s.levels[owner].entry;
 else if(kind==3)a=s.levels[owner].cancellation;
 else {
  if(position<0||position>=s.npositions||s.positions[position].owner!=owner||s.positions[position].volume<=0)return false;
  if(kind==2)a=s.positions[position].protect;else if(kind==4)a=s.positions[position].close;else return false;
 }
 if(a.phase!=1||a.serial>=900000000||utc<=0)return false;
 MDOpLevel l=s.levels[owner];
 if(kind==1&&(l.consumed||l.cutoff||l.conflict||l.order!=0||utc>=l.cutoff_utc))return false;
 if(kind==2&&(!MDProtectionDue(s.positions[position].protection,utc)||s.positions[position].closing))return false;
 a.phase=2;a.serial++;a.started=utc;a.completed=0;a.retcode=0;a.response_order=0;
 if(kind==1)s.levels[owner].entry=a;
 if(kind==3)s.levels[owner].cancellation=a;
 if(kind==2){s.positions[position].protect=a;MDProtectionStarted(s.positions[position].protection,utc);}
 if(kind==4)s.positions[position].close=a;
 s.watermark=utc;return true;
}
// Transport response is recorded; it is never an execution/protection confirmation.
bool MDOpResponse(MDOpState &s,int owner,int position,int kind,long serial,long utc,
 bool api_ok,long retcode,long external,long order) {
 if(owner<0||owner>=s.nlevels||utc<s.watermark)return false;
 MDOpAction a;
 if(kind==1)a=s.levels[owner].entry;
 else if(kind==3)a=s.levels[owner].cancellation;
 else {
  if(position<0||position>=s.npositions||s.positions[position].owner!=owner)return false;
  if(kind==2)a=s.positions[position].protect;else if(kind==4)a=s.positions[position].close;else return false;
 }
 if(a.phase!=2||a.serial!=serial||utc<a.started)return false;
 int response=MDResponse613(api_ok,retcode,external);
 a.completed=utc;a.retcode=retcode;a.response_order=order;
 if(response==0)a.phase=2;
 else if(response==2)a.phase=(kind==1&&!MDOpTransient(retcode))?5:4;
 else a.phase=3;
 if(kind==1)s.levels[owner].entry=a;
 if(kind==3)s.levels[owner].cancellation=a;
 if(kind==2){s.positions[position].protect=a;if(response!=0)MDProtectionCompleted(s.positions[position].protection,utc);}
 if(kind==4)s.positions[position].close=a;
 s.watermark=utc;return true;
}
bool MDOpOrderMatch(const MDOpLevel &l,const MDRawOrder69 &o,const MDOpOrderExtra &x,int instance) {
 return o.entry_limit&&o.order.symbol==l.symbol&&o.order.magic==MDMagic67(instance,l.level)&&
 o.order.buy==l.prices.buy&&MDEqual68(o.order.initial_volume,l.volume)&&x.price==l.prices.entry_tick&&
 o.setup_msc>=l.open_server;
}
string MDOpDealReceipt(const MDDeal68 &d,bool price_known,double price) {
 return "D"+IntegerToString(d.ticket)+","+IntegerToString(d.order)+","+IntegerToString(d.position)+","+
 IntegerToString(d.magic)+","+IntegerToString(d.msc)+","+IntegerToString(d.entry)+","+IntegerToString(d.buy?1:0)+","+
 DoubleToString(d.volume,16)+","+IntegerToString(price_known?1:0)+","+DoubleToString(price_known?price:0,16)+";";
}
// Explicit incident manifest: only the four EA-cancelled XP DEMO orders from
// 2026-11-05. No general permission to retry a cancelled trading opportunity.
long MDRepairTicket21303(int level) {
 if(level==0)return 2584908719;
 if(level==1)return 2584909140;
 if(level==2)return 2584909261;
 if(level==4)return 2584909339;
 return 0;
}
long MDRepairAccepted21303(int level) {
 if(level==0)return 1793870593966;
 if(level==1)return 1793870596524;
 if(level==2)return 1793870598093;
 if(level==4)return 1793870600160;
 return 0;
}
bool MDRepairScope21303(const MDOpState &s) {
 return s.instance==1&&s.scope==MDContext612(52237148,"XPMT5-DEMO",1);
}
// These historical origins remain in every earlier immutable journal revision.
// Serial 2 is reserved by the explicit migration; a new request uses serial 3.
// Never exempt an active origin, a different receipt, or any origin with deals.
bool MDRepairRetired21303(const MDOpState &s,const MDOpSnapshot &snapshot,int j) {
 if(!MDRepairScope21303(s)||j<0||j>=snapshot.book.orders)return false;
 MDRawOrder69 o=snapshot.book.o[j];MDOpOrderExtra x=snapshot.orders[j];
 for(int k=0;k<s.nlevels;k++) {
  MDOpLevel l=s.levels[k];long ticket=MDRepairTicket21303(l.level);
  if(ticket==0||l.date!=20261105||l.symbol!="WINZ26"||l.entry.serial<2||l.order==ticket||o.order.ticket!=ticket)continue;
  if(!o.entry_limit||o.order.state!=1||o.order.symbol!=l.symbol||o.order.magic!=MDMagic67(s.instance,l.level)||
     o.order.buy!=l.prices.buy||o.order.initial_volume!=l.volume||o.setup_msc!=MDRepairAccepted21303(l.level)||
     x.comment!="MD"+IntegerToString(l.key)+"A1"||x.price!=l.prices.entry_tick||x.sl!=l.prices.sl_tick||x.tp!=l.prices.tp_tick||x.position_id!=0)return false;
  for(int d=0;d<snapshot.book.deals;d++)if(snapshot.book.d[d].order==ticket)return false;
  return true;
 }
 return false;
}
// Second incident: the repaired R61 pending was cancelled on resume while
// its already-valid raw tick trail was still catching up (no entry touch).
bool MDRepairRetired21304(const MDOpState &s,const MDOpSnapshot &snapshot,int j) {
 if(!MDRepairScope21303(s)||j<0||j>=snapshot.book.orders)return false;
 int k=MDOpFindLevel(s,20261105,4);if(k<0)return false;
 MDOpLevel l=s.levels[k];MDRawOrder69 o=snapshot.book.o[j];MDOpOrderExtra x=snapshot.orders[j];
 if(l.symbol!="WINZ26"||l.entry.serial<4||l.order==2585252290||o.order.ticket!=2585252290||
    !o.entry_limit||o.order.state!=1||o.order.symbol!=l.symbol||o.order.magic!=MDMagic67(1,4)||o.order.buy||
    o.order.initial_volume!=l.volume||o.setup_msc!=1793877148012||x.comment!="MD202611054A3"||
    x.price!=l.prices.entry_tick||x.sl!=l.prices.sl_tick||x.tp!=l.prices.tp_tick||x.position_id!=0)return false;
 for(int d=0;d<snapshot.book.deals;d++)if(snapshot.book.d[d].order==2585252290)return false;
 return true;
}
// Reconcile every chain by origin receipt, then every position by POSITION_IDENTIFIER.
// Absence alone never confirms an uncertain entry attempt.
bool MDOpReconcile(MDOpState &s,const MDOpSnapshot &snapshot,long utc,string &why) {
 why="SNAPSHOT_INVALID";
 if(MDContext612(snapshot.book.account_key,snapshot.book.server_key,s.instance)!=s.scope||!snapshot.book.complete||!snapshot.book.connected||!snapshot.book.hedge||!MDCounts69(snapshot.book)||snapshot.server_msc<=0||utc<s.watermark)return false;
 for(int k=0;k<s.nlevels;k++) {
  MDOpLevel l=s.levels[k];int found=-1;
  for(int j=0;j<snapshot.book.orders;j++) {
   if(!MDOpOrderMatch(l,snapshot.book.o[j],snapshot.orders[j],s.instance))continue;
   bool linked=l.order>0?snapshot.book.o[j].order.ticket==l.order:
    (l.entry.serial>0&&MDOpBusy(l.entry)&&
     (l.entry.response_order==snapshot.book.o[j].order.ticket||snapshot.orders[j].comment==MDOpComment(l)));
   if(!linked)continue;
   if(found>=0){why="AMBIGUOUS_ORIGIN";return false;}found=j;
  }
  if(l.order==0&&found>=0) {
   // A rejection is not superseded silently by adoption of a matching magic.
   l.order=snapshot.book.o[found].order.ticket;l.accepted_server=snapshot.book.o[found].setup_msc;l.entry.phase=6;
   s.levels[k]=l;
  }
  if(l.order==0)continue;
  if(found<0){why="BOUND_ORDER_MISSING_FROM_HISTORY";return false;}
  MDOrigin68 origin;origin.verified=true;origin.buy=l.prices.buy;origin.symbol=l.symbol;
  origin.instance=s.instance;origin.level=l.level;origin.date=l.date;origin.order_ticket=l.order;
  origin.magic=MDMagic67(s.instance,l.level);origin.accepted_msc=l.accepted_server;origin.initial_volume=l.volume;
  MDChainInput68 chain_input;MDChainResult68 chain;
  if(!MDBuild69(snapshot.book,origin,snapshot.server_msc,chain_input,why)||!MDReconcileChain68(chain_input,chain)){why="CHAIN_"+chain.reason;return false;}
  string observed_receipts="";
  for(int d=0;d<chain_input.deal_count;d++) {
   MDDeal68 deal=chain_input.deals[d];int source=-1;
   for(int z=0;z<snapshot.book.deals;z++)if(snapshot.book.d[z].ticket==deal.ticket){source=z;break;}
   double price=source<0?0:snapshot.deal_price[source];
   if(snapshot.execution_prices_known&&!MDPositive(price)){why="EXECUTION_PRICE_UNAVAILABLE";return false;}
   string receipt=MDOpDealReceipt(deal,snapshot.execution_prices_known,price);
   if(StringFind(observed_receipts,receipt)<0)observed_receipts+=receipt;
   string identity="D"+IntegerToString(deal.ticket)+",";
   if(StringFind(l.deal_receipts,identity)>=0&&StringFind(l.deal_receipts,receipt)<0){why="DEAL_RECEIPT_CHANGED";return false;}
   if(StringFind(l.deal_receipts,receipt)<0)l.deal_receipts+=receipt;
  }
  int receipt_at=0;
  while(receipt_at<StringLen(l.deal_receipts)) {
   int end=StringFind(l.deal_receipts,";",receipt_at);if(end<0){why="RECEIPT_FORMAT";return false;}
   string receipt=StringSubstr(l.deal_receipts,receipt_at,end-receipt_at+1);
   if(StringFind(observed_receipts,receipt)<0){why="PREVIOUS_DEAL_RECEIPT_MISSING";return false;}receipt_at=end+1;
  }
  if(chain.consumed)l.consumed=true;
  if(!chain.pending&&l.cancellation.phase!=0)l.cancellation.phase=6;
  if(!chain.pending)l.consumed=true; // an accepted order ending never creates a second opportunity
  for(int j=0;j<chain.position_count;j++) {
   MDChainPosition68 cp=chain.positions[j];int p=MDOpFindPosition(s,k,cp.identifier);
   if(p<0) {
    if(s.npositions>=MDOP_POSITIONS){why="POSITION_CAPACITY";return false;}
    p=s.npositions++;MDOpPosition v;v.owner=k;v.identifier=cp.identifier;v.ticket=cp.current_ticket;
    v.first_server=cp.first_entry_msc;v.entered=0;v.exited=0;v.volume=0;v.sl=0;v.tp=0;v.closing=false;
    MDProtectionReset(v.protection);MDOpActionReset(v.protect,2);MDOpActionReset(v.close,4);s.positions[p]=v;
   }
   MDOpPosition v=s.positions[p];
   if(cp.entered+0.00000001<v.entered||cp.exited+0.00000001<v.exited||cp.first_entry_msc!=v.first_server){why="DEAL_HISTORY_REGRESSED";return false;}
   v.ticket=cp.current_ticket;v.entered=cp.entered;v.exited=cp.exited;v.volume=cp.open_volume;v.sl=0;v.tp=0;
   for(int q=0;q<snapshot.book.positions;q++)if(snapshot.book.p[q].identifier==v.identifier&&snapshot.book.p[q].symbol==l.symbol){v.sl=snapshot.sl[q];v.tp=snapshot.tp[q];}
   bool matched=v.sl==l.prices.sl_tick&&v.tp==l.prices.tp_tick;
   if(v.volume==0) {
    if(v.close.phase!=0)v.close.phase=6;
    if(v.protect.phase!=0)v.protect.phase=6;
    if(v.protection.inflight)MDProtectionCompleted(v.protection,utc);
   } else if(matched&&v.protect.phase!=0) {
    v.protect.phase=6;if(v.protection.inflight)MDProtectionCompleted(v.protection,utc);
   } else if(v.protect.phase==3&&v.protect.completed>0&&utc>=v.protect.completed) {
    // Known completed modification plus a new stable read: still missing; same fixed SL/TP may be retried.
    v.protect.phase=6;
   }
   if(MDOpBusy(v.close)) {
    double done=v.exited-v.close.baseline_exit;
    bool outstanding=false,terminal=false;
    for(int q=0;q<snapshot.book.orders;q++)if(v.close.response_order>0&&snapshot.book.o[q].order.ticket==v.close.response_order){
     outstanding=snapshot.book.o[q].order.state==0;terminal=!outstanding;
    }
    if(!outstanding&&(done+0.00000001>=v.close.volume||(terminal&&done>0)))v.close.phase=6;
   }
   s.positions[p]=v;
  }
  // A previously known position may disappear only with a complete zero residual in its chain.
  for(int p=0;p<s.npositions;p++)if(s.positions[p].owner==k&&MDPosIndex68(chain,s.positions[p].identifier)<0){why="POSITION_HISTORY_MISSING";return false;}
  s.levels[k]=l;
 }
 // Any candidate owned by our magic but lacking origin/deal proof blocks new planning.
 // It is never adopted or acted on just because the account contains that magic.
 for(int j=0;j<snapshot.book.orders;j++) {
  int lv=MDLevelMagic67(snapshot.book.o[j].order.magic,s.instance);if(lv<0||!snapshot.book.o[j].entry_limit)continue;
  bool known=false;for(int k=0;k<s.nlevels;k++)if(s.levels[k].order==snapshot.book.o[j].order.ticket)known=true;
  if(!known&&!MDRepairRetired21303(s,snapshot,j)&&!MDRepairRetired21304(s,snapshot,j)&&!MDRegistryRetired21305(s,snapshot,j)){why="UNPROVEN_ORDER_ORIGIN";return false;}
 }
 for(int j=0;j<snapshot.book.positions;j++) {
  if(MDLevelMagic67(snapshot.book.p[j].magic,s.instance)<0)continue;
  bool known=false;for(int p=0;p<s.npositions;p++)if(s.positions[p].identifier==snapshot.book.p[j].identifier&&s.levels[s.positions[p].owner].symbol==snapshot.book.p[j].symbol)known=true;
  if(!known){why="UNPROVEN_POSITION_ORIGIN";return false;}
 }
 why="ALL_CHAINS_RECONCILED";return true;
}
// Reconciliation runs on a candidate copy. Failure cannot partially mutate the committed state.
bool MDOpCycle(const MDOpState &old,const MDOpSnapshot &snapshot,const MDOpFrame &f,MDOpState &next,string &why) {
 next=old;
 if(f.utc<=0||f.utc<old.watermark){why="CLOCK_REGRESSION";return false;}
 bool reconciled=false;
 if(f.stable&&f.connected) {
  MDOpState observed=next;
  reconciled=MDOpReconcile(observed,snapshot,f.utc,why);
  if(reconciled)next=observed;
 } else why="INVENTORY_UNAVAILABLE";
 for(int k=0;k<next.nlevels;k++) {
  MDOpLevel l=next.levels[k];
  if(f.clock_ok&&f.utc>=l.cutoff_utc){l.cutoff=true;l.consumed=true;l.cancel=true;l.closing=true;}
  if(f.touched[k]) {
   if(l.touch_server==0||f.first_touch[k]<l.touch_server)l.touch_server=f.first_touch[k];
   l.consumed=true;
  }
  if(f.pending_boundary[k]&&l.order>0){l.cancel=true;l.closing=true;l.consumed=true;}
  bool active=false;
  if(reconciled&&l.order>0)for(int j=0;j<snapshot.book.orders;j++)if(snapshot.book.o[j].order.ticket==l.order)active=snapshot.book.o[j].order.state==0;
  // Unknown/incomplete tick history is NOT proof of a trading boundary.
  // Existing orders remain server-protected while the adapter reconstructs.
  // New entries still require the independent complete-coverage entry_ready.
  if(active&&(f.pending_boundary[k]||(l.touch_server>0&&l.accepted_server>=l.touch_server))) {l.cancel=true;l.consumed=true;}
  if(l.cancel&&l.order>0&&(!reconciled||active))MDOpIntent(l.cancellation,3,l.order,0,0,0);
  if(l.entry.phase==1&&(l.consumed||l.cutoff||l.conflict||!f.entry_ready[k]))l.entry.phase=7;
  // All eligible levels are planned in this same cycle; no proximity ordering.
  if(reconciled&&f.clock_ok&&f.connected&&f.entry_ready[k]&&!l.consumed&&!l.cutoff&&!l.conflict&&l.order==0&&
    !l.prices.geometry_blocked&&l.prices.valid_open&&f.utc<l.cutoff_utc&&
    (l.entry.phase==0||l.entry.phase==4||l.entry.phase==7))MDOpIntent(l.entry,1,0,0,l.volume,0);
  next.levels[k]=l;
 }
 for(int p=0;p<next.npositions;p++) {
  MDOpPosition v=next.positions[p];MDOpLevel l=next.levels[v.owner];if(v.volume<=0)continue;
  bool sl=v.sl==l.prices.sl_tick,tp=v.tp==l.prices.tp_tick;
  // Missing history blocks new entries via entry_ready. It never fabricates a post-fill stop or a pending invalidation.
  if(l.closing||f.position_boundary[p]||(f.clock_ok&&MDProtectionCloseRequired(v.protection,f.utc,sl)))v.closing=true;
  if(v.closing) {
   // A mandatory risk exit must not leave the same opportunity's remainder
   // able to refill after the executed slice has been closed.
   next.levels[v.owner].cancel=true;next.levels[v.owner].consumed=true;next.levels[v.owner].closing=true;
   if(l.order>0)MDOpIntent(next.levels[v.owner].cancellation,3,l.order,0,0,0);
   if(v.protect.phase==1)v.protect.phase=7;
   MDOpIntent(v.close,4,v.ticket,v.identifier,v.volume,v.exited);
  } else if(reconciled&&(!sl||!tp)&&f.clock_ok&&MDProtectionDue(v.protection,f.utc))
   MDOpIntent(v.protect,2,v.ticket,v.identifier,v.volume,v.exited);
  if(sl&&tp&&v.protect.phase==1)v.protect.phase=7;
  next.positions[p]=v;
 }
 return true;
}
bool MDOpSamePrices(const MDLevel &a,const MDLevel &b) {
 return a.id==b.id&&a.buy==b.buy&&a.valid_open==b.valid_open&&a.geometry_blocked==b.geometry_blocked&&
 a.entry==b.entry&&a.sl==b.sl&&a.tp==b.tp&&a.entry_tick==b.entry_tick&&a.sl_tick==b.sl_tick&&a.tp_tick==b.tp_tick;
}
// Structural monotonicity is checked independently of the planner.
bool MDOpForward(const MDOpState &old,const MDOpState &next) {
 if(next.nlevels<old.nlevels||next.npositions<old.npositions||next.watermark<old.watermark)return false;
 for(int i=0;i<old.nlevels;i++) {
  MDOpLevel a=old.levels[i],b=next.levels[i];
  if(!MDOpSamePrices(a.prices,b.prices)||StringSubstr(b.deal_receipts,0,StringLen(a.deal_receipts))!=a.deal_receipts||a.key!=b.key||a.symbol!=b.symbol||a.fingerprint!=b.fingerprint||a.open_server!=b.open_server||a.cutoff_utc!=b.cutoff_utc||a.volume!=b.volume||
   (a.consumed&&!b.consumed)||(a.cutoff&&!b.cutoff)||(a.cancel&&!b.cancel)||(a.closing&&!b.closing)||(a.conflict&&!b.conflict)||
   (a.order>0&&(a.order!=b.order||a.accepted_server!=b.accepted_server))||
   (a.touch_server>0&&(b.touch_server==0||b.touch_server>a.touch_server))||a.entry.serial>b.entry.serial||a.cancellation.serial>b.cancellation.serial)return false;
 }
 for(int i=0;i<old.npositions;i++) {
  MDOpPosition a=old.positions[i],b=next.positions[i];
  if(a.owner!=b.owner||a.identifier!=b.identifier||a.first_server!=b.first_server||a.entered>b.entered+0.00000001||a.exited>b.exited+0.00000001||
   (a.closing&&!b.closing)||a.protect.serial>b.protect.serial||a.close.serial>b.close.serial||
   a.protection.initial_completed>b.protection.initial_completed||a.protection.last_started_ms>b.protection.last_started_ms||
   (a.protection.sixth_completed_ms>=0&&a.protection.sixth_completed_ms!=b.protection.sixth_completed_ms))return false;
 }
 return true;
}

// Legacy observation-only probe. Native sends use the separate account-bound DEMO gate.
bool MDOpTransportEnabled(){return false;}
#endif
