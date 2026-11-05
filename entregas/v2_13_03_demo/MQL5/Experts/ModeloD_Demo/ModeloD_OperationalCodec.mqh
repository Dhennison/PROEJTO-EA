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
// Each committed revision contains the complete integrated state, with a hash chain.
// Receipt, intents, attempts, schedules and consumption therefore commit together.
string MDOpRecord(string previous,const MDOpState &s,string event) {
 if(!MDToken67(event))return "";
 string body=MDOpN(s.revision)+MDOpN(MDHash67(previous))+event+"|"+MDOpEncode(s);
 return previous+body+"#"+IntegerToString(MDHash67(body))+"\n";
}
bool MDOpReplay(string text,string scope,int instance,MDOpState &out) {
 if(text==""||StringLen(text)>134217728)return false;
 int pos=0;long sequence=0;string prefix="";MDOpState last;
 while(pos<StringLen(text)) {
  int end=StringFind(text,"\n",pos);if(end<0)return false;
  string row=StringSubstr(text,pos,end-pos);int hash_at=StringFind(row,"#");if(hash_at<0)return false;
  string body=StringSubstr(row,0,hash_at);long checksum;
  if(!MDLong610(StringSubstr(row,hash_at+1),checksum)||checksum!=MDHash67(body))return false;
  MDOpState prior;if(sequence>0)prior=last;
  int at=0;long revision,previous;string event;
  if(!MDOpReadN(body,at,revision)||revision!=sequence+1||!MDOpReadN(body,at,previous)||previous!=MDHash67(prefix)||
    !MDOpToken(body,at,event)||!MDToken67(event)||!MDOpDecode(StringSubstr(body,at),scope,instance,last)||last.revision!=revision)return false;
  if(sequence>0&&!MDOpForwardEvent21303(prior,last,event,prefix))return false;
  prefix+=row+"\n";sequence=revision;pos=end+1;
 }
 out=last;return sequence>0;
}
#endif
