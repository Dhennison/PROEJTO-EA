#ifndef MODELOD_OPERATIONAL_CODEC
#define MODELOD_OPERATIONAL_CODEC
#include "ModeloD_Operational.mqh"
string MDOpN(long v){return IntegerToString(v)+"|";}
string MDOpD(double v){return DoubleToString(v,16)+"|";}
string MDOpEncodeAction(const MDOpAction &a) {
 return MDOpN(a.kind)+MDOpN(a.phase)+MDOpN(a.serial)+MDOpN(a.ticket)+MDOpN(a.identifier)+
 MDOpN(a.started)+MDOpN(a.completed)+MDOpN(a.retcode)+MDOpN(a.response_order)+MDOpD(a.volume)+MDOpD(a.baseline_exit);
}
string MDOpEncode(const MDOpState &s) {
 string t="MDOP1|"+s.scope+"|"+MDOpN(s.instance)+MDOpN(s.nlevels)+MDOpN(s.npositions)+MDOpN(s.revision)+MDOpN(s.watermark);
 for(int i=0;i<s.nlevels;i++) {
  MDOpLevel l=s.levels[i];MDLevel v=l.prices;
  t+=MDOpN(l.date)+MDOpN(l.level)+l.symbol+"|"+l.fingerprint+"|"+l.deal_receipts+"|"+
  MDOpN(l.key)+MDOpN(l.open_server)+MDOpN(l.cutoff_utc)+MDOpN(l.touch_server)+MDOpN(l.order)+MDOpN(l.accepted_server)+MDOpD(l.volume)+
  MDOpN(l.consumed?1:0)+MDOpN(l.cancel?1:0)+MDOpN(l.closing?1:0)+MDOpN(l.cutoff?1:0)+MDOpN(l.conflict?1:0)+
  MDOpN(v.id)+MDOpN(v.buy?1:0)+MDOpN(v.valid_open?1:0)+MDOpN(v.geometry_blocked?1:0)+
  MDOpD(v.entry)+MDOpD(v.sl)+MDOpD(v.tp)+MDOpD(v.entry_tick)+MDOpD(v.sl_tick)+MDOpD(v.tp_tick)+
  MDOpEncodeAction(l.entry)+MDOpEncodeAction(l.cancellation);
 }
 for(int i=0;i<s.npositions;i++) {
  MDOpPosition p=s.positions[i];MDProtection c=p.protection;
  t+=MDOpN(p.owner)+MDOpN(p.identifier)+MDOpN(p.ticket)+MDOpN(p.first_server)+MDOpD(p.entered)+MDOpD(p.exited)+MDOpD(p.volume)+
  MDOpD(p.sl)+MDOpD(p.tp)+MDOpN(p.closing?1:0)+MDOpN(c.initial_completed)+MDOpN(c.inflight?1:0)+MDOpN(c.started?1:0)+
  MDOpN(c.last_started_ms+1)+MDOpN(c.sixth_completed_ms+1)+MDOpEncodeAction(p.protect)+MDOpEncodeAction(p.close);
 }
 return t;
}
bool MDOpToken(string text,int &pos,string &v) {
 int n=StringFind(text,"|",pos);if(n<0)return false;v=StringSubstr(text,pos,n-pos);pos=n+1;return true;
}
bool MDOpReadN(string t,int &pos,long &v) {string token;return MDOpToken(t,pos,token)&&MDLong610(token,v);}
bool MDOpReadI(string t,int &pos,int &v) {long n;if(!MDOpReadN(t,pos,n)||n>2147483647)return false;v=(int)n;return true;}
bool MDOpReadB(string t,int &pos,bool &v) {long n;if(!MDOpReadN(t,pos,n)||n>1)return false;v=n==1;return true;}
bool MDOpReadD(string t,int &pos,double &v) {
 string token;if(!MDOpToken(t,pos,token)||StringLen(token)<1||StringLen(token)>30)return false;
 int dots=0;for(int i=0;i<StringLen(token);i++){int c=StringGetCharacter(token,i);if(c==46)dots++;else if(c<48||c>57)return false;}
 if(dots!=1)return false;
 v=StringToDouble(token);return MathIsValidNumber(v)&&v>=0&&DoubleToString(v,16)==token;
}
bool MDOpReadAction(string t,int &pos,int kind,MDOpAction &a) {
 if(!MDOpReadI(t,pos,a.kind)||a.kind!=kind||!MDOpReadI(t,pos,a.phase)||a.phase>7||!MDOpReadN(t,pos,a.serial)||a.serial>900000000||
 !MDOpReadN(t,pos,a.ticket)||!MDOpReadN(t,pos,a.identifier)||!MDOpReadN(t,pos,a.started)||!MDOpReadN(t,pos,a.completed)||
 !MDOpReadN(t,pos,a.retcode)||!MDOpReadN(t,pos,a.response_order)||!MDOpReadD(t,pos,a.volume)||!MDOpReadD(t,pos,a.baseline_exit))return false;
 if((a.phase==2||a.phase==3||a.phase==4||a.phase==5)&&(a.serial==0||a.started==0))return false;
 if(a.completed>0&&a.completed<a.started)return false;
 return true;
}
bool MDOpDecode(string t,string scope,int instance,MDOpState &out) {
 int at=0;string magic;MDOpState s;MDOpInit(s,scope,instance);
 if(!MDOpToken(t,at,magic)||magic!="MDOP1"||!MDOpToken(t,at,s.scope)||s.scope!=scope||!MDToken67(scope)||
 !MDOpReadI(t,at,s.instance)||s.instance!=instance||MDMagic67(instance,0)<0||!MDOpReadI(t,at,s.nlevels)||s.nlevels>MDOP_LEVELS||s.nlevels%5!=0||
 !MDOpReadI(t,at,s.npositions)||s.npositions>MDOP_POSITIONS||!MDOpReadN(t,at,s.revision)||!MDOpReadN(t,at,s.watermark))return false;
 for(int i=0;i<s.nlevels;i++) {
  MDOpLevel l;MDLevel v;
  if(!MDOpReadI(t,at,l.date)||!MDDateValid67(l.date)||!MDOpReadI(t,at,l.level)||l.level>4||
   !MDOpToken(t,at,l.symbol)||!MDToken67(l.symbol)||!MDOpToken(t,at,l.fingerprint)||!MDOpIdentityText(l.fingerprint)||!MDOpToken(t,at,l.deal_receipts)||StringLen(l.deal_receipts)>100000||StringFind(l.deal_receipts,"#")>=0||StringFind(l.deal_receipts,"\n")>=0||
   !MDOpReadN(t,at,l.key)||l.key!=(long)l.date*10+l.level||!MDOpReadN(t,at,l.open_server)||l.open_server==0||
   !MDOpReadN(t,at,l.cutoff_utc)||l.cutoff_utc==0||!MDOpReadN(t,at,l.touch_server)||!MDOpReadN(t,at,l.order)||
   !MDOpReadN(t,at,l.accepted_server)||(l.order>0)!=(l.accepted_server>0)||!MDOpReadD(t,at,l.volume)||l.volume<1||l.volume!=MathFloor(l.volume)||
   !MDOpReadB(t,at,l.consumed)||!MDOpReadB(t,at,l.cancel)||!MDOpReadB(t,at,l.closing)||!MDOpReadB(t,at,l.cutoff)||!MDOpReadB(t,at,l.conflict)||
   !MDOpReadI(t,at,v.id)||v.id!=l.level||!MDOpReadB(t,at,v.buy)||v.buy!=(l.level<3)||!MDOpReadB(t,at,v.valid_open)||!MDOpReadB(t,at,v.geometry_blocked)||
   !MDOpReadD(t,at,v.entry)||!MDOpReadD(t,at,v.sl)||!MDOpReadD(t,at,v.tp)||!MDOpReadD(t,at,v.entry_tick)||
   !MDOpReadD(t,at,v.sl_tick)||!MDOpReadD(t,at,v.tp_tick)||!MDOpReadAction(t,at,1,l.entry)||!MDOpReadAction(t,at,3,l.cancellation))return false;
  if(v.entry_tick!=MDRound5(v.entry)||v.sl_tick!=MDRound5(v.sl)||v.tp_tick!=MDRound5(v.tp))return false;
  if((l.touch_server>0||l.cutoff||l.cancel||l.closing)&&!l.consumed)return false;
  for(int j=0;j<i;j++)if(s.levels[j].key==l.key||(l.order>0&&s.levels[j].order==l.order))return false;
  l.prices=v;s.levels[i]=l;
 }
 for(int i=0;i<s.npositions;i++) {
  MDOpPosition p;MDProtection c;long last,sixth;
  if(!MDOpReadI(t,at,p.owner)||p.owner>=s.nlevels||!MDOpReadN(t,at,p.identifier)||p.identifier==0||!MDOpReadN(t,at,p.ticket)||
  !MDOpReadN(t,at,p.first_server)||p.first_server==0||!MDOpReadD(t,at,p.entered)||!MDOpReadD(t,at,p.exited)||!MDOpReadD(t,at,p.volume)||
  !MDEqual68(p.entered-p.exited,p.volume)||(p.volume>0&&p.ticket==0)||!MDOpReadD(t,at,p.sl)||!MDOpReadD(t,at,p.tp)||!MDOpReadB(t,at,p.closing)||
  !MDOpReadI(t,at,c.initial_completed)||c.initial_completed>6||!MDOpReadB(t,at,c.inflight)||!MDOpReadB(t,at,c.started)||
  !MDOpReadN(t,at,last)||!MDOpReadN(t,at,sixth)||!MDOpReadAction(t,at,2,p.protect)||!MDOpReadAction(t,at,4,p.close))return false;
  c.last_started_ms=last-1;c.sixth_completed_ms=sixth-1;
  if((c.inflight&&!c.started)||(!c.started&&(last!=0||c.initial_completed!=0))||
   (c.initial_completed<6&&sixth!=0)||(c.initial_completed==6&&sixth==0)||c.last_started_ms>s.watermark||c.sixth_completed_ms>s.watermark)return false;
  for(int j=0;j<i;j++)if(s.positions[j].identifier==p.identifier&&s.levels[s.positions[j].owner].symbol==s.levels[p.owner].symbol)return false;
  p.protection=c;s.positions[i]=p;
 }
 if(at!=StringLen(t)||MDOpEncode(s)!=t)return false;
 out=s;return true;
}
bool MDRepairEligibleState21303(const MDOpState &s,int k) {
 if(!MDRepairScope21303(s)||k<0||k>=s.nlevels)return false;
 MDOpLevel l=s.levels[k];long ticket=MDRepairTicket21303(l.level);
 if(ticket==0||l.date!=20261105||l.symbol!="WINZ26"||l.key!=(long)202611050+l.level||
    l.order!=ticket||l.accepted_server!=MDRepairAccepted21303(l.level)||l.volume!=1||
    !l.consumed||!l.cancel||l.closing||l.cutoff||l.conflict||l.touch_server!=0||l.deal_receipts!=""||
    l.entry.phase!=6||l.entry.serial!=1||l.entry.response_order!=ticket||l.entry.retcode!=10009||
    l.cancellation.phase!=6||l.cancellation.serial!=1||l.cancellation.retcode!=10009)return false;
 for(int p=0;p<s.npositions;p++)if(s.positions[p].owner==k)return false;
 return true;
}
// Identify the exact defective transition in the already verified journal:
// a response still unbound becomes a bound, cancelled, untouched origin in
// INTEGRATED_CYCLE. The complete old record is retained; never rewrite it.
bool MDRepairIncident21303(string text,int level,string scope,int instance) {
 int pos=0;bool have=false;MDOpState prior;
 while(pos<StringLen(text)) {
  int end=StringFind(text,"\n",pos);if(end<0)return false;
  string row=StringSubstr(text,pos,end-pos);int h=StringFind(row,"#");if(h<0)return false;
  string body=StringSubstr(row,0,h);int at=0;long rev,previous;string event;MDOpState s;
  if(!MDOpReadN(body,at,rev)||!MDOpReadN(body,at,previous)||!MDOpToken(body,at,event)||
     !MDOpDecode(StringSubstr(body,at),scope,instance,s))return false;
  int k=MDOpFindLevel(s,20261105,level),p=have?MDOpFindLevel(prior,20261105,level):-1;
  if(k>=0&&p>=0&&event=="INTEGRATED_CYCLE") {
   MDOpLevel a=prior.levels[p],b=s.levels[k];long ticket=MDRepairTicket21303(level);
   if(ticket>0&&a.order==0&&a.entry.phase==3&&a.entry.serial==1&&a.entry.response_order==ticket&&
      !a.consumed&&!a.cancel&&a.touch_server==0&&b.order==ticket&&b.accepted_server==MDRepairAccepted21303(level)&&
      b.entry.phase==6&&b.consumed&&b.cancel&&b.touch_server==0&&b.cancellation.phase==1)return true;
  }
  prior=s;have=true;pos=end+1;
 }
 return false;
}
void MDRepairClear21303(MDOpState &s,int k) {
 MDOpLevel l=s.levels[k];long cancel_serial=l.cancellation.serial;
 l.order=0;l.accepted_server=0;l.consumed=false;l.cancel=false;l.closing=false;
 MDOpActionReset(l.entry,1);l.entry.serial=2; // reserved audit generation; never sent
 MDOpActionReset(l.cancellation,3);l.cancellation.serial=cancel_serial;
 s.levels[k]=l;
}
// Ordinary commits remain strictly monotone. Only the explicit incident event
// can correct a false consumption, with a canonical one-level transformation.
bool MDOpForwardEvent21303(const MDOpState &old,const MDOpState &next,string event,string prefix) {
 if(MDOpForward(old,next))return true;
 if(!MDRepairScope21303(old)||next.scope!=old.scope||next.instance!=old.instance||
    next.watermark<old.watermark)return false;
 for(int k=0;k<old.nlevels;k++) {
  if(!MDRepairEligibleState21303(old,k))continue;
  MDOpLevel l=old.levels[k];
  if(event!="REPAIR21303_CANCEL_"+IntegerToString(l.order)||next.watermark>=l.cutoff_utc||
     !MDRepairIncident21303(prefix,l.level,old.scope,old.instance))continue;
  MDOpState canonical=old;MDRepairClear21303(canonical,k);
  canonical.revision=next.revision;canonical.watermark=next.watermark;
  if(MDOpEncode(canonical)==MDOpEncode(next))return true;
 }
 return false;
}
bool MDRepairEligible21304(const MDOpState &s) {
 if(!MDRepairScope21303(s))return false;
 int k=MDOpFindLevel(s,20261105,4);if(k<0)return false;
 MDOpLevel l=s.levels[k];
 if(l.symbol!="WINZ26"||l.order!=2585252290||l.accepted_server!=1793877148012||l.volume!=1||
    !l.consumed||!l.cancel||l.closing||l.cutoff||l.conflict||l.touch_server!=0||l.deal_receipts!=""||
    l.entry.phase!=6||l.entry.serial!=3||l.entry.response_order!=l.order||l.entry.retcode!=10009||
    l.cancellation.phase!=6||l.cancellation.serial!=2||l.cancellation.retcode!=10009)return false;
 for(int p=0;p<s.npositions;p++)if(s.positions[p].owner==k)return false;
 return true;
}
bool MDRepairIncident21304(string text,string scope,int instance) {
 int pos=0;bool have=false,recovered_origin=false;MDOpState prior;
 while(pos<StringLen(text)) {
  int end=StringFind(text,"\n",pos);if(end<0)return false;
  string row=StringSubstr(text,pos,end-pos);int h=StringFind(row,"#");if(h<0)return false;
  string body=StringSubstr(row,0,h);int at=0;long rev,previous;string event;MDOpState s;
  if(!MDOpReadN(body,at,rev)||!MDOpReadN(body,at,previous)||!MDOpToken(body,at,event)||
     !MDOpDecode(StringSubstr(body,at),scope,instance,s))return false;
  if(event=="REPAIR21303_CANCEL_2584909339")recovered_origin=true;
  int k=MDOpFindLevel(s,20261105,4),p=have?MDOpFindLevel(prior,20261105,4):-1;
  if(k>=0&&p>=0&&recovered_origin&&event=="INTEGRATED_CYCLE") {
   MDOpLevel a=prior.levels[p],b=s.levels[k];
   if(a.order==2585252290&&b.order==a.order&&a.accepted_server==1793877148012&&b.accepted_server==a.accepted_server&&
      a.entry.phase==6&&a.entry.serial==3&&b.entry.serial==3&&!a.consumed&&!a.cancel&&a.touch_server==0&&
      b.consumed&&b.cancel&&!b.closing&&!b.cutoff&&!b.conflict&&b.touch_server==0&&b.cancellation.phase==1)return true;
  }
  prior=s;have=true;pos=end+1;
 }
 return false;
}
void MDRepairClear21304(MDOpState &s) {
 int k=MDOpFindLevel(s,20261105,4);MDOpLevel l=s.levels[k];long serial=l.cancellation.serial;
 l.order=0;l.accepted_server=0;l.consumed=false;l.cancel=false;l.closing=false;
 MDOpActionReset(l.entry,1);l.entry.serial=4; // reserved migration generation
 MDOpActionReset(l.cancellation,3);l.cancellation.serial=serial;s.levels[k]=l;
}
bool MDOpForwardEvent21304(const MDOpState &old,const MDOpState &next,string event,string prefix) {
 if(MDOpForwardEvent21303(old,next,event,prefix))return true;
 if(event!="REPAIR21304_RESUME_2585252290"||!MDRepairEligible21304(old)||next.scope!=old.scope||
    next.instance!=old.instance||next.watermark<old.watermark)return false;
 int k=MDOpFindLevel(old,20261105,4);
 if(next.watermark>=old.levels[k].cutoff_utc||!MDRepairIncident21304(prefix,old.scope,old.instance))return false;
 MDOpState canonical=old;MDRepairClear21304(canonical);canonical.revision=next.revision;canonical.watermark=next.watermark;
 return MDOpEncode(canonical)==MDOpEncode(next);
}

// A known cancelled origin is not a consumed opportunity if Last never touched.
bool MDRearmEligible21305(const MDOpState &s,int k) {
 if(k<0||k>=s.nlevels)return false;MDOpLevel l=s.levels[k];
 if(l.order<=0||l.accepted_server<=0||l.touch_server!=0||l.cutoff||l.conflict||l.closing||
    !l.prices.valid_open||l.prices.geometry_blocked||l.deal_receipts!=""||l.entry.phase!=6||l.entry.serial>=899999998)return false;
 for(int p=0;p<s.npositions;p++)if(s.positions[p].owner==k)return false;
 return true;
}
void MDRearmClear21305(MDOpState &s,int k) {
 MDOpLevel l=s.levels[k];long serial=l.entry.serial,cancel_serial=l.cancellation.serial;
 l.order=0;l.accepted_server=0;l.consumed=false;l.cancel=false;l.closing=false;
 MDOpActionReset(l.entry,1);l.entry.serial=serial+1; // reserve an audit-only generation
 MDOpActionReset(l.cancellation,3);l.cancellation.serial=cancel_serial;s.levels[k]=l;
}
string MDRegistryLine21305(const MDOpState &s,int k) {
 MDOpLevel l=s.levels[k];
 return s.scope+"|"+MDOpN(s.instance)+MDOpN(l.date)+MDOpN(l.level)+l.symbol+"|"+
 MDOpN(l.order)+MDOpN(l.accepted_server)+MDOpD(l.volume)+MDOpD(l.prices.entry_tick)+MDOpD(l.prices.sl_tick)+MDOpD(l.prices.tp_tick)+
 MDOpComment(l)+"|"+l.deal_receipts+"|\n";
}
// Archive only complete past sessions. The immutable journal keeps all prices,
// identifiers, fills and decisions; active working slots can then be reused.
bool MDArchiveEligible21305(const MDOpState &s,int date) {
 int count=0;
 for(int k=0;k<s.nlevels;k++)if(s.levels[k].date==date){
  MDOpLevel l=s.levels[k];count++;
  if(!l.cutoff||!l.consumed||MDOpBusy(l.entry)||MDOpBusy(l.cancellation)||
    (l.order>0&&l.entry.phase!=6))return false;
  for(int p=0;p<s.npositions;p++)if(s.positions[p].owner==k&&
    (s.positions[p].volume>0||MDOpBusy(s.positions[p].protect)||MDOpBusy(s.positions[p].close)))return false;
 }
 return count==5;
}
void MDArchiveClear21305(MDOpState &s,int date) {
 int map[MDOP_LEVELS];for(int k=0;k<MDOP_LEVELS;k++)map[k]=-1;
 int levels=0;for(int k=0;k<s.nlevels;k++)if(s.levels[k].date!=date){map[k]=levels;s.levels[levels++]=s.levels[k];}
 int positions=0;for(int p=0;p<s.npositions;p++)if(map[s.positions[p].owner]>=0){
  MDOpPosition v=s.positions[p];v.owner=map[v.owner];s.positions[positions++]=v;
 }
 s.nlevels=levels;s.npositions=positions;
}
bool MDOpForwardEvent21305(const MDOpState &old,const MDOpState &next,string event,string prefix) {
 bool special=StringFind(event,"REARM21305_")==0||StringFind(event,"ARCHIVE21305_")==0;
 if(!special)return MDOpForwardEvent21304(old,next,event,prefix);
 if(next.scope!=old.scope||next.instance!=old.instance||next.watermark<old.watermark)return false;
 for(int k=0;k<old.nlevels;k++){
  MDOpLevel l=old.levels[k];MDOpState expected=old;
  if(event=="REARM21305_"+IntegerToString(l.key)+"_"+IntegerToString(l.order)){
   if(!MDRearmEligible21305(old,k)||next.watermark>=l.cutoff_utc)return false;
   MDRearmClear21305(expected,k);
  }else if(event=="ARCHIVE21305_"+IntegerToString(l.date)){
   if(!MDArchiveEligible21305(old,l.date)||next.watermark<l.cutoff_utc)return false;
   MDArchiveClear21305(expected,l.date);
  }else continue;
  expected.revision=next.revision;expected.watermark=next.watermark;
  return MDOpEncode(expected)==MDOpEncode(next);
 }
 return false;
}
bool MDRegistryRetired21305(const MDOpState &s,const MDOpSnapshot &snapshot,int index) {
 if(index<0||index>=snapshot.book.orders)return false;
 MDRawOrder69 o=snapshot.book.o[index];MDOpOrderExtra x=snapshot.orders[index];
 if(!o.entry_limit||o.order.state==0)return false;
 int cursor=0;
 while(cursor<StringLen(retired_registry21305)){
  int end=StringFind(retired_registry21305,"\n",cursor);if(end<0)return false;
  string record=StringSubstr(retired_registry21305,cursor,end-cursor);cursor=end+1;
  int at=0,instance,date,level;long ticket,accepted;string scope,symbol,comment,receipts;double volume,entry,sl,tp;
  if(!MDOpToken(record,at,scope)||!MDOpReadI(record,at,instance)||!MDOpReadI(record,at,date)||!MDOpReadI(record,at,level)||
     !MDOpToken(record,at,symbol)||!MDOpReadN(record,at,ticket)||!MDOpReadN(record,at,accepted)||
     !MDOpReadD(record,at,volume)||!MDOpReadD(record,at,entry)||!MDOpReadD(record,at,sl)||!MDOpReadD(record,at,tp)||
     !MDOpToken(record,at,comment)||!MDOpToken(record,at,receipts)||at!=StringLen(record))return false;
  if(scope!=s.scope||instance!=s.instance||ticket!=o.order.ticket)continue;
  if(o.order.symbol!=symbol||o.order.magic!=MDMagic67(instance,level)||o.order.buy!=(level<3)||
     o.setup_msc!=accepted||o.order.initial_volume!=volume||x.price!=entry||x.sl!=sl||x.tp!=tp||x.comment!=comment)return false;
  MDOrigin68 origin;origin.verified=true;origin.buy=level<3;origin.symbol=symbol;origin.instance=instance;origin.level=level;
  origin.date=date;origin.order_ticket=ticket;origin.magic=o.order.magic;origin.accepted_msc=accepted;origin.initial_volume=volume;
  MDChainInput68 chain_input21305;MDChainResult68 chain;string why;
  if(!MDBuild69(snapshot.book,origin,snapshot.server_msc,chain_input21305,why)||!MDReconcileChain68(chain_input21305,chain)||chain.pending||chain.open_volume>0)return false;
  string observed="";
  for(int d=0;d<chain_input21305.deal_count;d++){
   int z=-1;for(int j=0;j<snapshot.book.deals;j++)if(snapshot.book.d[j].ticket==chain_input21305.deals[d].ticket){z=j;break;}
   if(z<0)return false;
   string receipt=MDOpDealReceipt(chain_input21305.deals[d],snapshot.execution_prices_known,snapshot.deal_price[z]);
   if(StringFind(receipts,receipt)<0)return false;
   if(StringFind(observed,receipt)<0)observed+=receipt;
  }
  int from=0;while(from<StringLen(receipts)){
   int stop=StringFind(receipts,";",from);if(stop<0)return false;
   if(StringFind(observed,StringSubstr(receipts,from,stop-from+1))<0)return false;from=stop+1;
  }
  return true;
 }
 return false;
}
// Each committed revision contains the complete integrated state, with a hash chain.
// Receipt, intents, attempts, schedules and consumption therefore commit together.
string MDOpRecord(string previous,const MDOpState &s,string event) {
 if(!MDToken67(event))return "";
 string body=MDOpN(s.revision)+MDOpN(MDHash67(previous))+event+"|"+MDOpEncode(s);
 return previous+body+"#"+IntegerToString(MDHash67(body))+"\n";
}
bool MDOpReplay(string text,string scope,int instance,MDOpState &out) {
 if(text==""||StringLen(text)>134217728)return false;
 int pos=0;long sequence=0;string prefix="",registry="";MDOpState last;
 while(pos<StringLen(text)) {
  int end=StringFind(text,"\n",pos);if(end<0)return false;
  string row=StringSubstr(text,pos,end-pos);int hash_at=StringFind(row,"#");if(hash_at<0)return false;
  string body=StringSubstr(row,0,hash_at);long checksum;
  if(!MDLong610(StringSubstr(row,hash_at+1),checksum)||checksum!=MDHash67(body))return false;
  MDOpState prior;if(sequence>0)prior=last;
  int at=0;long revision,previous;string event;
  if(!MDOpReadN(body,at,revision)||revision!=sequence+1||!MDOpReadN(body,at,previous)||previous!=MDHash67(prefix)||
    !MDOpToken(body,at,event)||!MDToken67(event)||!MDOpDecode(StringSubstr(body,at),scope,instance,last)||last.revision!=revision)return false;
  if(sequence>0&&!MDOpForwardEvent21305(prior,last,event,prefix))return false;
  if(sequence>0){
   for(int k=0;k<prior.nlevels;k++){
    MDOpLevel l=prior.levels[k];
    int current=MDOpFindLevel(last,l.date,l.level);
    bool legacy=current>=0&&last.levels[current].order==0&&
      (event=="REPAIR21303_CANCEL_"+IntegerToString(l.order)||event=="REPAIR21304_RESUME_"+IntegerToString(l.order));
    if(l.order>0&&(legacy||event=="REARM21305_"+IntegerToString(l.key)+"_"+IntegerToString(l.order)||
       event=="ARCHIVE21305_"+IntegerToString(l.date)))registry+=MDRegistryLine21305(prior,k);
   }
  }
  prefix+=row+"\n";sequence=revision;pos=end+1;
 }
 if(sequence>0){retired_registry21305=registry;out=last;return true;}return false;
}
#endif
