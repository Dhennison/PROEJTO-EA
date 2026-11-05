#ifndef MODELOD_OPERATIONAL_TERMINAL
#define MODELOD_OPERATIONAL_TERMINAL
#include "ModeloD_OperationalFile.mqh"
#include "ModeloD_TickAudit.mqh"
#include "ModeloD_TerminalCollect.mqh"
#include "ModeloD_DailyTerminal.mqh"
#include "ModeloD_Context.mqh"
// The existing daily/stream adapter uses Brasilia civil timestamps directly.
// Measure the actual server offset, and refuse to reinterpret another timezone silently.
struct MDOpClock {long utc,server,last_utc,last_mono;int offset,samples;bool ok,broker_anchored;long last_broker;};
void MDOpClockInit(MDOpClock &c){c.utc=0;c.server=0;c.last_utc=0;c.last_mono=0;c.offset=0;c.samples=0;c.ok=false;c.broker_anchored=false;c.last_broker=0;}
bool MDOpClockRead(MDOpClock &c,long watermark,string &why) {
 long utc=(long)TimeGMT()*1000,server=(long)TimeTradeServer()*1000,mono=(long)GetTickCount64();
 c.ok=false;why="CLOCK_UNAVAILABLE";if(utc<=0||server<=0)return false;
 long difference=server-utc;
 int candidate=(int)(MathRound((double)difference/900000.0)*900);
 if(MathAbs((double)(difference-(long)candidate*1000))>2000||candidate< -43200||candidate>50400){why="SERVER_OFFSET_INCOHERENT";return false;}
 if(utc<watermark||(c.last_utc>0&&(utc<c.last_utc||mono<c.last_mono||
    MathAbs((double)((utc-c.last_utc)-(mono-c.last_mono)))>2000))){why="WALL_CLOCK_DISCONTINUITY";return false;}
 if(c.samples>0&&candidate!=c.offset){why="SERVER_OFFSET_CHANGED";c.samples=0;return false;}
 long broker=(long)TimeCurrent()*1000;
 if(c.last_broker>0&&broker<c.last_broker){why="BROKER_TIME_REGRESSED";return false;}
 if(broker>0&&MathAbs((double)(server-broker))<=3000)c.broker_anchored=true;
 if(broker>c.last_broker)c.last_broker=broker;
 c.offset=candidate;c.samples++;c.utc=utc;c.server=server;c.last_utc=utc;c.last_mono=mono;
 if(c.samples<3){why="CLOCK_SAMPLING";return false;}
 if(!c.broker_anchored){why="FRESH_BROKER_TIME_REQUIRED_AFTER_RESTART";return false;}
 c.ok=true;why="CLOCK_OBSERVED_NOT_INDEPENDENT_NTP_CERTIFICATION";return true;
}
bool MDOpCollect(datetime start,MDOpSnapshot &s,string &why) {
 datetime end=TimeTradeServer();if(!Collect69(start,end,s.book,why))return false;
 s.server_msc=(long)end*1000;s.execution_prices_known=true;
 for(int i=0;i<s.book.deals;i++)if(!DD69((ulong)s.book.d[i].ticket,DEAL_PRICE,s.deal_price[i])||!MDPositive(s.deal_price[i])){why="DEAL_PRICE_READ_FAILED";return false;}
 for(int i=0;i<s.book.orders;i++) {
  long ticket=s.book.o[i].order.ticket;bool active=OrderSelect((ulong)ticket);
  double price=0,sl=0,tp=0;long position=0;string comment="";
  bool ok;
  if(active)ok=OD69(ORDER_PRICE_OPEN,price)&&OD69(ORDER_SL,sl)&&OD69(ORDER_TP,tp)&&OI69(ORDER_POSITION_ID,position)&&OS69(ORDER_COMMENT,comment);
  else ok=HD69((ulong)ticket,ORDER_PRICE_OPEN,price)&&HD69((ulong)ticket,ORDER_SL,sl)&&HD69((ulong)ticket,ORDER_TP,tp)&&HI69((ulong)ticket,ORDER_POSITION_ID,position)&&HS69((ulong)ticket,ORDER_COMMENT,comment);
  if(!ok){why="ORDER_EXTRA_READ_FAILED";return false;}
  s.orders[i].price=price;s.orders[i].sl=sl;s.orders[i].tp=tp;s.orders[i].position_id=position;s.orders[i].comment=comment;
 }
 for(int i=0;i<s.book.positions;i++) {
  if(!PositionSelectByTicket((ulong)s.book.p[i].ticket)||!PD69(POSITION_SL,s.sl[i])||!PD69(POSITION_TP,s.tp[i])){why="SLTP_READ_FAILED";return false;}
 }
 return true;
}
bool MDOpSameSnapshot(const MDOpSnapshot &a,const MDOpSnapshot &b) {
 if(!MDSame69(a.book,b.book)||a.execution_prices_known!=b.execution_prices_known)return false;
 for(int i=0;i<a.book.deals;i++)if(a.deal_price[i]!=b.deal_price[i])return false;
 for(int i=0;i<a.book.orders;i++)if(a.orders[i].price!=b.orders[i].price||a.orders[i].sl!=b.orders[i].sl||a.orders[i].tp!=b.orders[i].tp||
   a.orders[i].position_id!=b.orders[i].position_id||a.orders[i].comment!=b.orders[i].comment)return false;
 for(int i=0;i<a.book.positions;i++)if(a.sl[i]!=b.sl[i]||a.tp[i]!=b.tp[i])return false;
 return true;
}
struct MDOpTrail {
 string symbol;long begin,cursor;bool boundary,ambiguous,failed;double entry,sl,tp;bool buy;
 bool pending,previous_known,entry_seen;double previous_price;
};
void MDOpTrailInit(MDOpTrail &t,string symbol,long begin,const MDLevel &price,bool pending=false) {
 t.symbol=symbol;t.begin=begin;t.cursor=begin+1;t.boundary=false;t.ambiguous=false;t.failed=false;
 t.entry=price.entry;t.sl=price.sl;t.tp=price.tp;t.buy=price.buy;
 t.pending=pending;t.previous_known=false;t.previous_price=0;t.entry_seen=false;
}
// Bounded per call, retained in memory and rebuilt from receipt/fill after restart.
// Same-millisecond boundary and fill have no demonstrated order; never claim post-fill evidence.
bool MDOpTrailRead(MDOpTrail &t,long until,string &why) {
 if(t.failed){why="TRAIL_PREVIOUS_FAILURE";return false;}
 if(until<t.cursor){why="TRAIL_BEFORE_ORIGIN";return false;}
 if(t.cursor==until)return !t.ambiguous;
 long end=t.cursor+59999;if(end>=until)end=until-1;
 MqlTick ticks[];ResetLastError();
 long lower=t.cursor==t.begin+1?t.begin:t.cursor;
 if(t.pending&&t.cursor==t.begin+1){lower=t.begin-60000;if(lower<0)lower=0;}
 int n=MDCopyTicksRange213(t.symbol,ticks,COPY_TICKS_TRADE,(ulong)lower,(ulong)end);
 int error=GetLastError();
 if(n<0||error!=0||n>500000){why="TRAIL_COPY_FAILED_"+IntegerToString(error);return false;}
 long previous=-1;bool boundary=t.boundary,ambiguous=t.ambiguous;
 bool known=t.previous_known,entered=t.entry_seen;double prior_price=t.previous_price;
 for(int i=0;i<n;i++) {
  long stamp=ticks[i].time_msc;double price=ticks[i].last;
  if(stamp<lower||stamp>end||stamp<previous||!MDPositive(price)||
    (ticks[i].flags&(TICK_FLAG_LAST|TICK_FLAG_VOLUME|TICK_FLAG_BUY|TICK_FLAG_SELL))==0){
   why="TRAIL_TICK_INVALID;index="+IntegerToString(i)+";msc="+IntegerToString(stamp)+";previous="+IntegerToString(previous);t.failed=true;return false;
  }
  if(t.pending&&stamp<t.begin){known=true;prior_price=price;previous=stamp;continue;}
  bool hit=t.buy?(price<=t.sl||price>=t.tp):(price>=t.sl||price<=t.tp);
  if(t.pending){
   if(stamp==t.begin){entered=entered||price==t.entry;hit=t.buy?price<=t.sl:price>=t.sl;}
   else{
    if(!known){why="TRAIL_PENDING_ANCHOR_MISSING";return false;}
    bool was_entered=entered;
    if(MDCrossed(prior_price,price,t.entry))entered=true;
    // The approach to a Limit necessarily passes its TP before its entry.
    // Only a missed entry touch can start the theoretical SL/TP path.
    hit=was_entered?(MDCrossed(prior_price,price,t.sl)||MDCrossed(prior_price,price,t.tp)):
        (entered&&(t.buy?price<=t.sl:price>=t.sl));
   }
   known=true;prior_price=price;
  }
  if(stamp==t.begin&&hit)ambiguous=true;
  if(stamp>t.begin&&hit)boundary=true;
  previous=stamp;
 }
 if(t.pending&&!known){why="TRAIL_PENDING_ANCHOR_MISSING";return false;}
 // Audit complete minutes in this exact block against M1; partial edges are labelled raw tail.
 long first=(t.cursor+59999)/60000*60000,last=(end+1)/60000*60000;
 for(long minute=first;minute<last;minute+=60000) {
  MDMinuteAudit m;m.count=0;m.o=0;m.h=0;m.l=0;m.c=0;
  for(int i=0;i<n;i++)if(ticks[i].time_msc>=minute&&ticks[i].time_msc<minute+60000) {
   double price=ticks[i].last;if(m.count==0){m.o=price;m.h=price;m.l=price;}else{if(price>m.h)m.h=price;if(price<m.l)m.l=price;}
   m.c=price;m.count++;
  }
  MqlRates bars[];ResetLastError();int count=MDCopyRates213(t.symbol,PERIOD_M1,(datetime)(minute/1000),(datetime)(minute/1000+59),bars);
  if(GetLastError()!=0||count!=1||(!MDAuditMinuteMatches(m,bars[0].open,bars[0].high,bars[0].low,bars[0].close)&&
    !MDReferenceMinute213(minute,ticks,n))){
   why="TRAIL_M1_NOT_CONFIRMED;minute="+IntegerToString(minute);return false;
  }
 }
 t.cursor=end+1;t.boundary=boundary;t.ambiguous=ambiguous;
 t.previous_known=known;t.previous_price=prior_price;t.entry_seen=entered;
 why=ambiguous?"BOUNDARY_SAME_MILLISECOND_UNKNOWN":
  (t.cursor<until?"TRAIL_RECONSTRUINDO;cursor_msc="+IntegerToString(t.cursor)+";ate_msc="+IntegerToString(until):"TRAIL_CONFERIDO_ATE_AGORA;BORDAS_PARCIAIS_RAW");
 return t.cursor==until&&!ambiguous;
}
#endif
