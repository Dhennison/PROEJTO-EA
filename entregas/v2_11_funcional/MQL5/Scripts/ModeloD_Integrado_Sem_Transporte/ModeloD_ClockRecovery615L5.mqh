#ifndef MD_CLOCK_RECOVERY615L5
#define MD_CLOCK_RECOVERY615L5
#include "ModeloD_StateStore615L4.mqh"
// Os intervalos UTC precisam ser certificados externamente. TimeLocal sozinho NAO basta.
// Tempo logico preserva a origem original dos prazos, mesmo apos mudar o contador bruto.
struct MDClock615L5 {string domain;long raw,lo,hi,utc_lo,utc_hi;bool utc_trusted;};
bool MDClockValid615L5(const MDClock615L5 &c)
{
 return c.domain!=""&&StringFind(c.domain,"\n")<0&&c.raw>=0&&c.lo>=0&&c.hi>=c.lo&&c.utc_lo>=0&&c.utc_hi>=c.utc_lo&&
 c.raw<=1000000000000000&&c.hi<=1000000000000000&&c.utc_hi<=1000000000000000;
}
bool MDClockAdvance615L5(const MDClock615L5 &old,string domain,long raw,MDClock615L5 &out)
{
 if(!MDClockValid615L5(old)||domain!=old.domain||raw<old.raw||raw>1000000000000000)return false;
 long delta=raw-old.raw;MDClock615L5 c=old;c.raw=raw;c.lo+=delta;c.hi+=delta;
 // A medicao UTC antiga nao e extrapolada como prova de sincronismo.
 if(delta>0)c.utc_trusted=false;
 if(!MDClockValid615L5(c))return false;
 out=c;return true;
}
bool MDClockRebase615L5(const MDClock615L5 &old,string new_domain,long new_raw,long utc_lo,long utc_hi,bool trusted,MDClock615L5 &out)
{
 if(!MDClockValid615L5(old)||!old.utc_trusted||!trusted||new_domain==old.domain||new_domain==""||new_raw<0||
 utc_lo<0||utc_hi<utc_lo||utc_hi<old.utc_lo||utc_hi>1000000000000000)return false;
 long elapsed_lo=utc_lo-old.utc_hi;if(elapsed_lo<0)elapsed_lo=0;
 long elapsed_hi=utc_hi-old.utc_lo;
 MDClock615L5 c;c.domain=new_domain;c.raw=new_raw;c.lo=old.lo+elapsed_lo;c.hi=old.hi+elapsed_hi;
 c.utc_lo=utc_lo;c.utc_hi=utc_hi;c.utc_trusted=true;
 if(!MDClockValid615L5(c))return false;
 out=c;return true;
}
// -1: evidencia temporal insuficiente; 0: ainda nao; 1: prazo comprovadamente atingido.
int MDThreshold615L5(const MDClock615L5 &c,long deadline)
{
 if(!MDClockValid615L5(c)||deadline<0)return -1;
 if(c.lo>=deadline)return 1;
 if(c.hi<deadline)return 0;
 return -1;
}
int MDProtectionDue615L5(const MDClock615L5 &c,const MDProtection &p)
{
 if(!MDClockValid615L5(c))return -1;
 if(p.inflight)return 0;
 if(!p.started)return 1;
 if(p.last_started_ms<0||p.last_started_ms>c.lo)return -1;
 return MDThreshold615L5(c,p.last_started_ms+(p.initial_completed<6?2000:10000));
}
int MDProtectionExpiry615L5(const MDClock615L5 &c,const MDProtection &p,bool sl_confirmed)
{
 if(!MDClockValid615L5(c))return -1;
 if(sl_confirmed||p.initial_completed<6)return 0;
 if(p.sixth_completed_ms<0)return -1;
 return MDThreshold615L5(c,p.sixth_completed_ms+180000);
}
string MDClockEncode615L5(const MDClock615L5 &c)
{
 if(!MDClockValid615L5(c))return "";
 string body="MD_CLOCK_L5\n"+c.domain+"\n";
 long v[6];v[0]=c.raw;v[1]=c.lo;v[2]=c.hi;v[3]=c.utc_lo;v[4]=c.utc_hi;v[5]=c.utc_trusted?1:0;
 for(int i=0;i<6;i++)body+=IntegerToString(v[i])+"\n";
 return body+IntegerToString(MDHash67(body));
}
bool MDClockDecode615L5(string text,MDClock615L5 &out)
{
 string f[9];int pos=0;
 for(int i=0;i<8;i++){int end=StringFind(text,"\n",pos);if(end<0)return false;f[i]=StringSubstr(text,pos,end-pos);pos=end+1;}
 long hash;if(f[0]!="MD_CLOCK_L5"||!MDLong610(StringSubstr(text,pos),hash)||hash!=MDHash67(StringSubstr(text,0,pos)))return false;
 long v[6];for(int i=0;i<6;i++)if(!MDLong610(f[i+2],v[i]))return false;
 if(v[5]>1)return false;
 MDClock615L5 c;c.domain=f[1];c.raw=v[0];c.lo=v[1];c.hi=v[2];c.utc_lo=v[3];c.utc_hi=v[4];c.utc_trusted=v[5]==1;
 if(!MDClockValid615L5(c))return false;
 out=c;return true;
}
// O par continua no dominio LOGICO original. Somente o mapa contador->logico muda.
string MDCheckpointEncode615L5(const MDPair615L3 &pair,const MDClock615L5 &clock)
{
 if(!MDPairValid615L3(pair)||!MDClockValid615L5(clock)||clock.lo<pair.cancel_slot.management.last_ms||clock.lo<pair.close_slot.management.last_ms)return "";
 string body=MDPairEncode615L3(pair)+"\n@@CLOCK_L5@@\n"+MDClockEncode615L5(clock);
 return body+"\n@@CHECK_L5@@\n"+IntegerToString(MDHash67(body));
}
bool MDCheckpointDecode615L5(string text,string key,string logical_domain,long min_revision,MDPair615L3 &pair,MDClock615L5 &clock)
{
 string sep="\n@@CLOCK_L5@@\n",tailsep="\n@@CHECK_L5@@\n";
 int mid=StringFind(text,sep),tail=StringFind(text,tailsep);if(mid<0||tail<=mid)return false;
 long hash;if(!MDLong610(StringSubstr(text,tail+StringLen(tailsep)),hash)||hash!=MDHash67(StringSubstr(text,0,tail)))return false;
 MDClock615L5 c;MDPair615L3 p;
 if(!MDClockDecode615L5(StringSubstr(text,mid+StringLen(sep),tail-mid-StringLen(sep)),c)||
 !MDPairDecode615L3(StringSubstr(text,0,mid),key,logical_domain,min_revision,c.lo,p))return false;
 pair=p;clock=c;return true;
}
#endif
