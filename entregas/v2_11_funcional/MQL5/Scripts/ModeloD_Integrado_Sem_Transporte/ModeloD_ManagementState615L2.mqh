#ifndef MD_MANAGEMENT_STATE615L2
#define MD_MANAGEMENT_STATE615L2
#include "ModeloD_Management615L.mqh"
// Estado isolado de bancada. clock_domain deve identificar a mesma origem monotona.
struct MDState615L2 {
 string key,clock_domain;MDManagement615L management;
 long revision,attempt,action_ticket,volume;int action,phase;
};
bool MDValid615L2(const MDState615L2 &s)
{
 if(s.key==""||s.clock_domain==""||StringFind(s.key,"\n")>=0||StringFind(s.clock_domain,"\n")>=0||
 s.revision<1||s.revision>1000000000||s.attempt<0||s.attempt>1000000000||s.management.ticket<=0||s.management.last_ms< -1)return false;
 MDProtection p=s.management.protection;
 if(p.initial_completed<0||p.initial_completed>6||p.last_started_ms< -1||p.sixth_completed_ms< -1||
 (p.inflight&&!p.started)||(!p.started&&(p.initial_completed!=0||p.last_started_ms!=-1))||
 (p.started&&(p.last_started_ms<0||p.last_started_ms>s.management.last_ms))||
 (p.initial_completed<6&&p.sixth_completed_ms!=-1)||(p.initial_completed==6&&(p.sixth_completed_ms<0||p.sixth_completed_ms>s.management.last_ms)))return false;
 if(s.action==0)return s.phase==0&&s.action_ticket==0&&s.volume==0&&s.attempt==0;
 return (s.action==3||s.action==4)&&s.attempt>0&&s.action_ticket>0&&s.volume>=0&&
 (s.action!=4||s.volume>0)&&(s.phase==1||s.phase==2);
}
void MDInit615L2(MDState615L2 &s,string key,string domain,long position_ticket)
{
 s.key=key;s.clock_domain=domain;MDManagementReset615L(s.management,position_ticket);
 s.revision=1;s.attempt=0;s.action=0;s.phase=0;s.action_ticket=0;s.volume=0;
}
string MDEncode615L2(const MDState615L2 &s)
{
 if(!MDValid615L2(s))return "";
 MDProtection p=s.management.protection;
 string body="MD615L2\n"+s.key+"\n"+s.clock_domain+"\n";
 long v[16];v[0]=s.revision;v[1]=s.management.ticket;v[2]=s.management.last_ms+1;v[3]=p.initial_completed;
 v[4]=p.inflight?1:0;v[5]=p.started?1:0;v[6]=p.last_started_ms+1;v[7]=p.sixth_completed_ms+1;
 v[8]=s.attempt;v[9]=s.action;v[10]=s.phase;v[11]=s.action_ticket;v[12]=s.volume;v[13]=0;v[14]=0;v[15]=0;
 for(int i=0;i<16;i++)body+=IntegerToString(v[i])+"\n";
 return body+IntegerToString(MDHash67(body));
}
bool MDDecode615L2(string text,string key,string domain,long minimum_revision,long now,MDState615L2 &out)
{
 string f[20];int pos=0;
 for(int i=0;i<19;i++){int end=StringFind(text,"\n",pos);if(end<0)return false;f[i]=StringSubstr(text,pos,end-pos);pos=end+1;}
 f[19]=StringSubstr(text,pos);long hash;
 if(f[0]!="MD615L2"||f[1]!=key||f[2]!=domain||!MDLong610(f[19],hash)||hash!=MDHash67(StringSubstr(text,0,pos)))return false;
 long v[16];for(int i=0;i<16;i++)if(!MDLong610(f[i+3],v[i]))return false;
 if(v[3]>6||v[4]>1||v[5]>1||v[9]>4||v[10]>2||v[13]!=0||v[14]!=0||v[15]!=0)return false;
 MDState615L2 s;s.key=key;s.clock_domain=domain;s.revision=v[0];s.management.ticket=v[1];s.management.last_ms=v[2]-1;
 s.management.protection.initial_completed=(int)v[3];s.management.protection.inflight=v[4]==1;s.management.protection.started=v[5]==1;
 s.management.protection.last_started_ms=v[6]-1;s.management.protection.sixth_completed_ms=v[7]-1;
 s.attempt=v[8];s.action=(int)v[9];s.phase=(int)v[10];s.action_ticket=v[11];s.volume=v[12];
 if(!MDValid615L2(s)||s.revision<minimum_revision||now<0||now<s.management.last_ms)return false;
 // Nenhuma permissao de transporte e serializada ou recriada.
 out=s;return true;
}
bool MDPrepareAction615L2(const MDState615L2 &s,int action,long ticket,long volume,bool reconciled,bool durable_intent,MDState615L2 &next)
{
 if(!MDValid615L2(s)||s.phase==1||!reconciled||!durable_intent||s.revision>=1000000000||s.attempt>=1000000000||
 (action!=3&&action!=4)||ticket<=0||volume<0||(action==4&&volume<=0))return false;
 // Encerrado para o mesmo alvo/acao: somente evidencia externa de nova necessidade autoriza outro controlador.
 if(s.phase==2&&s.action==action&&s.action_ticket==ticket)return false;
 next=s;next.revision++;next.attempt++;next.action=action;next.action_ticket=ticket;next.volume=volume;next.phase=1;return true;
}
bool MDResolveAction615L2(const MDState615L2 &s,long attempt,int action,long ticket,bool effect_confirmed,MDState615L2 &next)
{
 if(!MDValid615L2(s)||s.phase!=1||attempt!=s.attempt||action!=s.action||ticket!=s.action_ticket||!effect_confirmed||s.revision>=1000000000)return false;
 next=s;next.phase=2;next.revision++;return true;
}
#endif
