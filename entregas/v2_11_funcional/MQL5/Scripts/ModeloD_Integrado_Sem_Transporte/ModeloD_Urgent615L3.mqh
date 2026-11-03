#ifndef MD_URGENT615L3
#define MD_URGENT615L3
#include "ModeloD_ManagementState615L2.mqh"
struct MDPair615L3 {long revision;MDState615L2 cancel_slot,close_slot;};
string MDPairKey615L3(const MDJournal610 &j,int level,long position_ticket)
{
 if(!j.valid||level<0||level>4||j.r[level].id<=0||position_ticket<=0)return "";
 MDRequest610 r=j.r[level];
 return j.scope+"|"+j.contract+"|"+IntegerToString(j.date)+"|"+IntegerToString(j.instance)+"|"+IntegerToString(level)+"|"+
 IntegerToString(r.id)+"|"+IntegerToString(r.prepared_msc)+"|"+IntegerToString(r.entry)+"|"+IntegerToString(r.sl)+"|"+IntegerToString(r.tp)+"|"+IntegerToString(position_ticket);
}
void MDPairInit615L3(MDPair615L3 &s,string key,string domain,long ticket)
{s.revision=1;MDInit615L2(s.cancel_slot,key+"|CANCEL",domain,ticket);MDInit615L2(s.close_slot,key+"|CLOSE",domain,ticket);}
bool MDPairValid615L3(const MDPair615L3 &s)
{
 if(s.revision<1||s.revision>1000000000||!MDValid615L2(s.cancel_slot)||!MDValid615L2(s.close_slot)||
 s.cancel_slot.clock_domain!=s.close_slot.clock_domain||s.cancel_slot.management.ticket!=s.close_slot.management.ticket||
 (s.cancel_slot.action!=0&&s.cancel_slot.action!=3)||(s.close_slot.action!=0&&s.close_slot.action!=4))return false;
 string k=s.cancel_slot.key;int n=StringLen(k);
 return n>7&&StringSubstr(k,n-7)=="|CANCEL"&&s.close_slot.key==StringSubstr(k,0,n-7)+"|CLOSE";
}
// Plano ja conciliado; gravacao de sua intencao precisa ser comprovada pelo chamador.
// Esta funcao cria reserva candidata; nao concede permissao de transporte.
bool MDPairPrepare615L3(const MDPair615L3 &s,const MDPlan615C &plan,int action,bool intent_durable,string scope,string contract,int date,int instance,int level,MDPair615L3 &next,MDCommand613 &command)
{
 if(!MDPairValid615L3(s)||!plan.valid||!intent_durable||s.revision>=1000000000||(action!=3&&action!=4))return false;
 MDJournal610 j;
 if(!MDReplay610(plan.journal,scope,contract,date,instance,j))return false;
 string expected=MDPairKey615L3(j,level,s.close_slot.management.ticket);
 if(expected==""||s.cancel_slot.key!=expected+"|CANCEL"||s.close_slot.key!=expected+"|CLOSE")return false;
 int index=-1;
 for(int i=0;i<plan.count;i++)if(plan.commands[i].action==action){if(index>=0)return false;index=i;}
 if(index<0)return false;
 MDCommand613 c=plan.commands[index];if(!c.valid||c.ticket<=0||c.level!=level||c.symbol!=contract||c.magic!=MDMagic67(instance,level))return false;
 if(action==3&&(!j.r[level].cancel||c.ticket!=j.r[level].ticket))return false;
 if(action==4&&!j.r[level].close)return false;
 if(action==4&&c.ticket!=s.close_slot.management.ticket)return false;
 MDState615L2 slot,candidate;if(action==3)slot=s.cancel_slot;else slot=s.close_slot;
 if(!MDPrepareAction615L2(slot,action,c.ticket,(long)c.volume,true,intent_durable,candidate)||c.volume!=(double)((long)c.volume))return false;
 next=s;if(action==3)next.cancel_slot=candidate;else next.close_slot=candidate;
 next.revision++;command=c;return true;
}
bool MDPairResolve615L3(const MDPair615L3 &s,int action,long attempt,long ticket,bool effect_confirmed,MDPair615L3 &next)
{
 if(!MDPairValid615L3(s)||s.revision>=1000000000||(action!=3&&action!=4))return false;
 MDState615L2 slot,candidate;if(action==3)slot=s.cancel_slot;else slot=s.close_slot;
 if(!MDResolveAction615L2(slot,attempt,action,ticket,effect_confirmed,candidate))return false;
 next=s;if(action==3)next.cancel_slot=candidate;else next.close_slot=candidate;next.revision++;return true;
}
string MDPairEncode615L3(const MDPair615L3 &s)
{
 if(!MDPairValid615L3(s))return "";
 string body="MD615L3\n"+IntegerToString(s.revision)+"\n"+MDEncode615L2(s.cancel_slot)+"\n@@CLOSE@@\n"+MDEncode615L2(s.close_slot);
 return body+"\n@@HASH@@\n"+IntegerToString(MDHash67(body));
}
bool MDPairDecode615L3(string text,string key,string domain,long min_revision,long now,MDPair615L3 &out)
{
 if(StringFind(text,"MD615L3\n")!=0)return false;
 int end=StringFind(text,"\n",8);if(end<0)return false;
 long rev;if(!MDLong610(StringSubstr(text,8,end-8),rev)||rev<min_revision)return false;
 string sep="\n@@CLOSE@@\n",hashsep="\n@@HASH@@\n";
 int mid=StringFind(text,sep,end+1),tail=StringFind(text,hashsep,end+1);
 if(mid<0||tail<=mid)return false;
 string body=StringSubstr(text,0,tail);long hash;
 if(!MDLong610(StringSubstr(text,tail+StringLen(hashsep)),hash)||hash!=MDHash67(body))return false;
 MDPair615L3 s;s.revision=rev;
 if(!MDDecode615L2(StringSubstr(text,end+1,mid-end-1),key+"|CANCEL",domain,1,now,s.cancel_slot)||
 !MDDecode615L2(StringSubstr(text,mid+StringLen(sep),tail-mid-StringLen(sep)),key+"|CLOSE",domain,1,now,s.close_slot)||!MDPairValid615L3(s))return false;
 out=s;return true;
}
#endif
