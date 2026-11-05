#ifndef MODELOD_OPERATIONAL_CASES
#define MODELOD_OPERATIONAL_CASES
#include "ModeloD_OperationalFile.mqh"
int op_checks=0,op_failures=0;string op_log="";
void OPCheck(bool pass,string name) {
 op_checks++;if(!pass)op_failures++;string line=(pass?"PASS: ":"FAIL: ")+name;op_log+=line+"\r\n";Print(line);
}
void OPBase(MDOpState &s,MDOpSnapshot &b,MDOpFrame &f) {
 MDOpInit(s,MDContext612(1,"TEST",1),1);
 MDInputs values;values.high_prev=210800;values.low_prev=207235;values.close_prev=208495;values.open_today=209500;values.adjustment=208485;
 MDDay day;MDCalculate(values,day);string why;
 MDOpAddDay(s,20261028,"WINZ26","FROZEN_INPUTS",day,100000,1000000,5,why);
 b.execution_prices_known=true;for(int i=0;i<4096;i++)b.deal_price[i]=0;
 b.book.complete=true;b.book.connected=true;b.book.hedge=true;b.book.account_key=1;b.book.server_key="TEST";
 b.book.orders=0;b.book.deals=0;b.book.positions=0;b.server_msc=200000;
 MDOpFrameReset(f,200000,200000,true,true);f.stable=true;
 for(int i=0;i<5;i++){f.entry_ready[i]=true;f.pending_history[i]=true;}
}
bool OPCycle(MDOpState &s,const MDOpSnapshot &b,const MDOpFrame &f) {
 MDOpState next;string why;bool ok=MDOpCycle(s,b,f,next,why);if(ok)s=next;return ok;
}
void OPOrder(MDOpState &s,MDOpSnapshot &b,int owner,long ticket,int state,double remaining) {
 int n=b.book.orders++;MDOpLevel l=s.levels[owner];MDRawOrder69 o;
 o.order.ticket=ticket;o.order.magic=MDMagic67(s.instance,l.level);o.order.symbol=l.symbol;o.order.buy=l.prices.buy;
 o.order.state=state;o.order.initial_volume=l.volume;o.order.remaining=remaining;o.setup_msc=150000;o.entry_limit=true;b.book.o[n]=o;
 b.orders[n].price=l.prices.entry_tick;b.orders[n].sl=0;b.orders[n].tp=0;b.orders[n].position_id=0;b.orders[n].comment=MDOpComment(l);
}
void OPDeal(MDOpSnapshot &b,long ticket,long order,long id,int entry,double volume,long msc) {
 MDDeal68 d;d.ticket=ticket;d.order=order;d.position=id;d.magic=entry==0?MDMagic67(1,0):0;d.symbol="WINZ26";
 d.buy=entry==0;d.entry=entry;d.volume=volume;d.msc=msc;b.deal_price[b.book.deals]=209000;b.book.d[b.book.deals++]=d;
}
void OPPosition(MDOpSnapshot &b,long ticket,long id,double volume,double sl=0,double tp=0) {
 int n=b.book.positions++;MDPosition68 v;v.ticket=ticket;v.identifier=id;v.magic=MDMagic67(1,0);v.symbol="WINZ26";v.buy=true;v.volume=volume;
 b.book.p[n]=v;b.sl[n]=sl;b.tp[n]=tp;
}
void OPFilled(MDOpState &s,MDOpSnapshot &b,MDOpFrame &f) {
 OPBase(s,b,f);OPCycle(s,b,f);MDOpBegin(s,0,-1,1,110000,true,true);
 MDOpResponse(s,0,-1,1,1,120000,true,10008,0,100);
 OPOrder(s,b,0,100,0,2);OPDeal(b,1,100,700,0,1,160000);OPDeal(b,2,100,701,0,2,161000);
 OPPosition(b,900,700,1);OPPosition(b,901,701,2);OPCycle(s,b,f);
}
void RunOperationalCases() {
 op_checks=0;op_failures=0;op_log="";
 MDOpState s,next,restored;MDOpSnapshot b;MDOpFrame f;string why;
 OPBase(s,b,f);OPCheck(OPCycle(s,b,f),"integrated empty snapshot processed");
 int eligible=0,intents=0;for(int i=0;i<5;i++){if(s.levels[i].prices.valid_open&&!s.levels[i].prices.geometry_blocked)eligible++;if(s.levels[i].entry.phase==1)intents++;}
 OPCheck(eligible>1&&intents==eligible,"all eligible entries planned in the same transaction");
 OPCheck(!MDOpTransportEnabled(),"transport physically absent");
 OPCheck(s.levels[0].entry.serial==0,"suppressed intentions do not invent attempts");
 OPCheck(OPCycle(s,b,f)&&s.levels[0].entry.serial==0,"repeated observation does not dispatch");
 OPCheck(!MDOpBegin(s,0,-1,1,100000,false,true),"clock evidence required before candidate attempt");
 OPCheck(!MDOpBegin(s,0,-1,1,100000,true,false),"reconciliation evidence required before candidate attempt");
 OPCheck(MDOpBegin(s,0,-1,1,110000,true,true),"attempt candidate marked uncertain before future transport");
 OPCheck(!MDOpBegin(s,0,-1,1,112000,true,true),"uncertain attempt cannot be duplicated");
 string text=MDOpEncode(s);OPCheck(MDOpDecode(text,s.scope,s.instance,restored),"full state round trip");
 OPCheck(restored.levels[0].entry.phase==2&&restored.levels[0].entry.serial==1,"restart retains uncertain attempt");
 OPCheck(OPCycle(restored,b,f)&&restored.levels[0].entry.phase==2,"empty server inventory does not prove absent uncertain request");
 OPCheck(!MDOpResponse(s,0,-1,1,2,120000,true,10008,0,100),"wrong response serial rejected");
 OPCheck(MDOpResponse(s,0,-1,1,1,120000,true,10008,0,100),"entry response recorded separately");
 OPCheck(s.levels[0].order==0&&s.levels[0].entry.phase==3,"accepted response is not an order receipt or fill");
 OPOrder(s,b,0,100,0,5);
 OPCheck(OPCycle(s,b,f)&&s.levels[0].order==100&&s.npositions==0,"receipt bound by request and full order properties");
 f.touched[0]=true;f.first_touch[0]=170000;
 OPCheck(OPCycle(s,b,f)&&s.levels[0].consumed&&!s.levels[0].cancel,"accepted-before-touch pending may remain");
 f.pending_boundary[0]=true;
 OPCheck(OPCycle(s,b,f)&&s.levels[0].cancellation.phase==1&&s.levels[0].closing,"theoretical boundary persists cancellation and concurrent-fill close cause");
 OPCheck(s.levels[0].cancellation.serial==0,"cancel intention is not a server cancellation");
 OPCheck(MDOpBegin(s,0,-1,3,200000,true,true),"cancel attempt prepared");
 OPDeal(b,1,100,700,0,5,180000);b.book.o[0].order.state=2;b.book.o[0].order.remaining=0;OPPosition(b,900,700,5);
 f.utc=210000;b.server_msc=210000;
 OPCheck(OPCycle(s,b,f)&&s.positions[0].close.phase==1&&s.levels[0].cancellation.phase==6,"fill during cancel produces close intention on identified position");
 OPCheck(s.positions[0].close.ticket==900&&s.positions[0].close.identifier==700,"close addresses ticket and stable identifier");
 OPFilled(s,b,f);
 OPCheck(s.npositions==2&&s.positions[0].protect.phase==1&&s.positions[1].protect.phase==1,"one chain with multiple independently managed positions");
 OPCheck(s.levels[0].consumed&&b.book.o[0].order.remaining==2,"partial fill consumes level but preserves same-order residual");
 OPCheck(s.positions[0].protect.serial==0,"missing SLTP creates intention only");
 OPCheck(MDOpBegin(s,0,0,2,200000,true,true),"first protection attempt immediate");
 OPCheck(!MDOpBegin(s,0,0,2,201000,true,true),"inflight protection not repeated");
 OPCheck(MDOpResponse(s,0,0,2,1,200100,true,10016,0,0),"protection rejection recorded");
 f.utc=201000;OPCycle(s,b,f);
 OPCheck(s.positions[0].protection.initial_completed==1&&s.positions[0].protect.phase==4,"completed first failure retains schedule");
 f.utc=202000;OPCycle(s,b,f);
 OPCheck(s.positions[0].protect.phase==1,"two-second initial spacing");
 for(int i=1;i<6;i++) {
  long now=200000+i*2000;f.utc=now;b.server_msc=now;OPCycle(s,b,f);
  OPCheck(MDOpBegin(s,0,0,2,now,true,true),"initial protection attempt "+IntegerToString(i+1));
  OPCheck(MDOpResponse(s,0,0,2,i+1,now+100,true,10016,0,0),"initial protection completion "+IntegerToString(i+1));
 }
 long sixth=s.positions[0].protection.sixth_completed_ms;
 OPCheck(s.positions[0].protection.initial_completed==6&&sixth==210100,"sixth COMPLETION anchors additional three-minute window");
 text=MDOpEncode(s);OPCheck(MDOpDecode(text,s.scope,s.instance,restored),"protection schedule persists with absolute UTC timestamps");
 f.utc=219999;OPCycle(restored,b,f);OPCheck(restored.positions[0].protect.phase!=1,"additional attempts wait ten seconds from start");
 f.utc=220000;OPCycle(restored,b,f);OPCheck(restored.positions[0].protect.phase==1,"additional protection attempt due at ten seconds");
 f.utc=sixth+179999;OPCycle(restored,b,f);OPCheck(!restored.positions[0].closing,"no early deadline before additional three minutes");
 f.utc=sixth+180000;OPCycle(restored,b,f);OPCheck(restored.positions[0].closing&&restored.positions[0].close.phase==1,"offline interval counts and missing SL triggers close at deadline");
 OPCheck(restored.positions[1].protection.initial_completed==0&&!restored.positions[1].closing,"another position has independent attempts and deadline");
 OPFilled(s,b,f);MDOpBegin(s,0,0,2,200000,true,true);MDOpResponse(s,0,0,2,1,200100,true,10009,0,0);
 OPCheck(s.positions[0].sl==0&&s.positions[0].protect.phase==3,"successful SLTP response does not fabricate applied protection");
 b.sl[0]=s.levels[0].prices.sl_tick;b.tp[0]=s.levels[0].prices.tp_tick;f.utc=201000;b.server_msc=201000;
 OPCheck(OPCycle(s,b,f)&&s.positions[0].protect.phase==6,"matching live SL AND TP confirm protection effect");
 // Ticket migration while action uncertain: no resend on the new ticket.
 OPFilled(s,b,f);MDOpBegin(s,0,0,2,200000,true,true);b.book.p[0].ticket=999;f.utc=201000;b.server_msc=201000;
 OPCheck(OPCycle(s,b,f)&&s.positions[0].ticket==999&&s.positions[0].identifier==700,"ticket migration reconciled by stable identifier");
 OPCheck(s.positions[0].protect.phase==2&&s.positions[0].protect.ticket==900,"migration preserves uncertain old-target attempt");
 b.sl[0]=s.levels[0].prices.sl_tick;b.tp[0]=s.levels[0].prices.tp_tick;f.utc=202000;
 OPCheck(OPCycle(s,b,f)&&s.positions[0].protect.phase==6,"same-identifier observed protection resolves old ticket attempt");
 // Outgoing deal must be present; disappearance alone cannot verify a close.
 OPFilled(s,b,f);f.position_boundary[0]=true;OPCycle(s,b,f);MDOpBegin(s,0,0,4,200000,true,true);
 MDOpResponse(s,0,0,4,1,200100,true,10009,0,300);
 MDOpState before=s;b.book.positions=1;b.book.p[0]=b.book.p[1];f.utc=201000;b.server_msc=201000;
 MDOpCycle(s,b,f,next,why);
 OPCheck(next.positions[0].volume==before.positions[0].volume&&next.positions[0].close.phase==3,"position disappearance without exit deals does not confirm close");
 OPDeal(b,3,300,700,1,1,190000);OPCheck(OPCycle(s,b,f)&&s.positions[0].volume==0&&s.positions[0].close.phase==6,"complete outgoing deal and zero residual confirm close");
 // Partial close, new server order terminal and residual independently reconciled.
 OPFilled(s,b,f);f.position_boundary[1]=true;OPCycle(s,b,f);MDOpBegin(s,0,1,4,200000,true,true);
 MDOpResponse(s,0,1,4,1,200100,true,10010,0,300);
 OPDeal(b,3,300,701,1,1,190000);b.book.p[1].volume=1;
 int q=b.book.orders++;b.book.o[q]=b.book.o[0];b.book.o[q].order.ticket=300;b.book.o[q].order.state=2;b.book.o[q].entry_limit=false;
 b.orders[q].price=0;b.orders[q].sl=0;b.orders[q].tp=0;b.orders[q].position_id=701;b.orders[q].comment="";
 f.utc=201000;b.server_msc=201000;
 OPCheck(OPCycle(s,b,f)&&s.positions[1].close.phase==1&&s.positions[1].close.volume==1,"confirmed partial close schedules only residual volume");
 OPCheck(s.positions[1].close.serial==1,"residual intention retains monotonic attempt counter");
 // Cutoff runs without data and connection, applying also to older sessions.
 OPFilled(s,b,f);f.utc=1000000;f.clock_ok=true;f.connected=false;f.stable=false;
 OPCheck(OPCycle(s,b,f)&&s.levels[0].cutoff&&s.levels[0].cancellation.phase==1&&s.positions[0].close.phase==1&&s.positions[1].close.phase==1,
 "timer cutoff persists cancellation and all closes while disconnected");
 text=MDOpEncode(s);OPCheck(MDOpDecode(text,s.scope,1,restored),"restart after cutoff retains shutdown intentions");
 f.utc=1001000;OPCycle(restored,b,f);OPCheck(restored.levels[0].entry.phase!=1,"restart after cutoff cannot plan a new entry");
 MDOpState backwards=restored;f.utc=restored.watermark-1;
 OPCheck(!MDOpCycle(restored,b,f,next,why),"clock regression blocks processing without shifting deadlines");
 OPFilled(s,b,f);f.clock_ok=false;f.utc=1100000;OPCycle(s,b,f);OPCheck(!s.levels[0].cutoff,"unknown clock does not fabricate certified cutoff");
 OPBase(s,b,f);OPCycle(s,b,f);MDOpBegin(s,0,-1,1,110000,true,true);
 MDOpResponse(s,0,-1,1,1,120000,true,10020,0,0);OPCycle(s,b,f);
 OPCheck(s.levels[0].entry.phase==1&&s.levels[0].entry.serial==1,"transient rejection may retry only with current untapped eligibility");
 f.touched[0]=true;f.first_touch[0]=130000;OPCycle(s,b,f);
 OPCheck(s.levels[0].consumed&&s.levels[0].entry.phase==7,"touch before retry consumes and supersedes unsent intention");
 OPBase(s,b,f);OPCycle(s,b,f);MDOpBegin(s,0,-1,1,110000,true,true);
 MDOpResponse(s,0,-1,1,1,120000,true,10015,0,0);OPCycle(s,b,f);
 OPCheck(s.levels[0].entry.phase==5,"definitive entry rejection is not retried or repriced");
 OPBase(s,b,f);OPCycle(s,b,f);OPOrder(s,b,0,100,0,5);MDOpCycle(s,b,f,next,why);
 OPCheck(why=="UNPROVEN_ORDER_ORIGIN"&&next.levels[0].order==0,"matching magic without persisted attempted origin is not adopted");
 OPBase(s,b,f);OPCycle(s,b,f);MDOpBegin(s,0,-1,1,110000,true,true);OPOrder(s,b,0,100,0,5);
 OPCheck(OPCycle(s,b,f)&&s.levels[0].order==100,"crash before callback recovers origin by unique attempt comment");
 OPFilled(s,b,f);b.book.server_key="WRONG";MDOpCycle(s,b,f,next,why);
 OPCheck(why=="SNAPSHOT_INVALID"&&MDOpEncode(s)==MDOpEncode(next),"cross-account snapshot cannot mutate persisted ownership");
 OPBase(s,b,f);s.levels[0].conflict=true;OPCycle(s,b,f);OPCheck(s.levels[0].entry.phase==0,"frozen data conflict blocks new intent");
 // Receipt acceptance at the same ms as first touch cannot establish precedence.
 OPBase(s,b,f);OPCycle(s,b,f);MDOpBegin(s,0,-1,1,110000,true,true);OPOrder(s,b,0,100,0,5);
 f.touched[0]=true;f.first_touch[0]=150000;OPCycle(s,b,f);
 OPCheck(s.levels[0].cancel,"acceptance at same ms as touch triggers cancellation");
 // TP absent after SL deadline must not close an otherwise protected position.
 OPFilled(s,b,f);s.positions[0].protection.initial_completed=6;s.positions[0].protection.started=true;
 s.positions[0].protection.last_started_ms=200000;s.positions[0].protection.sixth_completed_ms=200100;s.watermark=200100;
 b.sl[0]=s.levels[0].prices.sl_tick;f.utc=400000;b.server_msc=400000;OPCycle(s,b,f);
 OPCheck(!s.positions[0].closing&&s.positions[0].protect.phase==1,"SL present and TP missing retains position and retries TP beyond deadline");
 OPFilled(s,b,f);string receipts=s.levels[0].deal_receipts;b.book.d[0].ticket=55;
 MDOpCycle(s,b,f,next,why);OPCheck(why=="PREVIOUS_DEAL_RECEIPT_MISSING"&&next.levels[0].deal_receipts==receipts,"same totals with replaced deal ticket cannot rewrite persisted evidence");
 OPFilled(s,b,f);b.deal_price[0]+=5;MDOpCycle(s,b,f,next,why);
 OPCheck(why=="DEAL_RECEIPT_CHANGED","executed price mutation cannot silently change a persisted receipt");
 OPFilled(s,b,f);f.position_boundary[0]=true;OPCycle(s,b,f);
 for(int i=1;i<=8;i++) {
  long now=200000+i*2000;f.utc=now;b.server_msc=now;
  OPCheck(MDOpBegin(s,0,0,4,now,true,true),"close remains retryable beyond six initial protection attempts "+IntegerToString(i));
  MDOpResponse(s,0,0,4,i,now+100,true,10018,0,0);f.utc=now+200;OPCycle(s,b,f);
 }
 OPCheck(s.positions[0].close.serial==8&&s.positions[0].close.phase==1,"close retries have no six-attempt cap");
 // Five simultaneous independent chains, including both buy and sell sides.
 OPBase(s,b,f);OPCycle(s,b,f);
 for(int k=0;k<5;k++) {
  long at=110000+k*1000;
  OPCheck(MDOpBegin(s,k,-1,1,at,true,true),"entry attempt for independent level "+IntegerToString(k));
  MDOpResponse(s,k,-1,1,1,at+100,true,10008,0,100+k);
  OPOrder(s,b,k,100+k,0,4);
  MDDeal68 d;d.ticket=1+k;d.order=100+k;d.position=700+k;d.magic=MDMagic67(1,k);d.symbol="WINZ26";
  d.buy=k<3;d.entry=0;d.volume=1;d.msc=160000+k;b.deal_price[b.book.deals]=s.levels[k].prices.entry_tick+(k<3?-5:5);b.book.d[b.book.deals++]=d;
  MDPosition68 v;v.ticket=900+k;v.identifier=700+k;v.magic=d.magic;v.symbol=d.symbol;v.buy=d.buy;v.volume=1;
  int pi=b.book.positions++;b.book.p[pi]=v;b.sl[pi]=0;b.tp[pi]=0;
 }
 OPCheck(OPCycle(s,b,f)&&s.npositions==5,"five simultaneous partial chains reconcile into five independent positions");
 bool all=true;for(int k=0;k<5;k++)if(s.positions[k].protect.phase!=1||s.positions[k].owner!=k||!s.levels[k].consumed)all=false;
 OPCheck(all,"all five chains retain fixed protections and independent opportunity consumption");
 text=MDOpEncode(s);OPCheck(MDOpDecode(text,s.scope,1,restored)&&restored.npositions==5,"all five chains survive a single state serialization");
 MDOpState saved=s;MDOpSnapshot changed=b;changed.book.positions=0;MDOpCycle(s,changed,f,next,why);
 OPCheck(next.npositions==saved.npositions&&next.positions[4].volume==saved.positions[4].volume,"one invalid inventory does not partially commit any of the five chains");
 // Single ledger persistence and crash recovery using actual files in the selected runtime.
 OPFilled(s,b,f);MDOpInit(restored,s.scope,s.instance);
 string path="ModeloD_INTEGRATED_TEST_"+IntegerToString((long)TimeLocal())+"_"+IntegerToString((long)GetMicrosecondCount())+".ledger";
 int lock=FileOpen(path+".lock",FILE_READ|FILE_WRITE|FILE_BIN|FILE_COMMON);string ledger="";
 OPCheck(lock!=INVALID_HANDLE,"exclusive ledger test lock opened");
 OPCheck(MDOpCommitFile(path,lock,ledger,restored,s,"INTEGRATED_FIXTURE",why),"one commit stores receipt positions intents and attempts together");
 MDOpState reopened;string read;
 OPCheck(MDOpRecoverFile(path,s.scope,s.instance,read,reopened,why)&&MDOpEncode(reopened)==MDOpEncode(restored),"full integrated ledger reopens without clock-domain BENCH");
 MDOpState update=restored;update.levels[0].cancel=true;update.levels[0].consumed=true;update.revision++;
 string pending=MDOpRecord(ledger,update,"NEXT_COMMIT");
 OPCheck(MDOpWriteFile(path+".next",pending),"simulate crash after next ledger is durable before publication");
 OPCheck(MDOpRecoverFile(path,s.scope,s.instance,read,reopened,why)&&reopened.levels[0].cancel&&reopened.revision==update.revision,"valid next revision automatically recovered as one transaction");
 ledger=read;restored=reopened;OPCheck(MDOpWriteFile(path+".next","TORN"),"simulate torn staging file");
 OPCheck(MDOpRecoverFile(path,s.scope,s.instance,read,reopened,why)&&read==ledger,"torn candidate preserved and prior complete ledger recovered");
 string corrupt=ledger;int middle=StringLen(corrupt)/2;
 corrupt=StringSubstr(corrupt,0,middle)+"X"+StringSubstr(corrupt,middle+1);
 OPCheck(!MDOpReplay(corrupt,s.scope,1,next),"corrupted integrated ledger rejected");
 OPCheck(!MDOpReplay(StringSubstr(ledger,0,StringLen(ledger)-1),s.scope,1,next),"incomplete committed ledger rejected");
 OPCheck(!MDOpReplay(ledger,"OTHER_CONTEXT",1,next),"ledger cannot cross account context");
 OPCheck(!MDOpCommitFile(path,INVALID_HANDLE,ledger,restored,restored,"NO_LOCK",why),"commit without exclusive lock rejected");
 string stale=ledger;MDOpState stale_state=restored;
 OPCheck(MDOpCommitFile(path,lock,ledger,restored,restored,"NEXT_REVISION",why),"repeatable valid commit");
 OPCheck(!MDOpCommitFile(path,lock,stale,stale_state,stale_state,"STALE_WRITER",why),"stale writer cannot overwrite newer ledger");
 MDOpState regression=restored;regression.levels[0].consumed=false;
 OPCheck(!MDOpCommitFile(path,lock,ledger,restored,regression,"REGRESSED_STATE",why),"a later revision cannot reopen a consumed opportunity");
 FileClose(lock);
 Print("TESTE_OPERACIONAL_INTEGRADO;Checks=",op_checks,";Failures=",op_failures,";SEM_TRANSPORTE;EVENTOS_SINTETICOS;ARQUIVOS_REAIS");
}
#endif
