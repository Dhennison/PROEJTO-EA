#ifndef MD_MANAGEMENT615L
#define MD_MANAGEMENT615L
#include "ModeloD_Rehearsal.mqh"
// Coordenacao de planos de bancada. Transporte e evidencias reais ainda externos.
struct MDManagement615L {long ticket,last_ms;MDProtection protection;};
void MDManagementReset615L(MDManagement615L &m,long ticket)
{m.ticket=ticket;m.last_ms=-1;MDProtectionReset(m.protection);}
bool MDManagementClock615L(MDManagement615L &m,long now)
{if(now<0||now<m.last_ms)return false;m.last_ms=now;return true;}
bool MDManagementBegin615L(MDManagement615L &m,long now,long ticket,bool durable)
{
 if(!MDManagementClock615L(m,now)||ticket<=0||ticket!=m.ticket||!durable||!MDProtectionDue(m.protection,now))return false;
 MDProtectionStarted(m.protection,now);return true;
}
bool MDManagementComplete615L(MDManagement615L &m,long now,long ticket)
{
 if(!MDManagementClock615L(m,now)||ticket!=m.ticket||!m.protection.inflight)return false;
 MDProtectionCompleted(m.protection,now);return true;
}
bool MDManage615L(MDManagement615L &m,string text,string scope,string contract,int date,int instance,int level,
 const MDSnapshot69 &snapshot,long account,string server,long market_ms,long monotonic_ms,
 const MDRecoveryEvidence67 &market,bool cutoff,bool observed_sl_matches,bool observed_tp_matches,
 MDExecGate613 &gate,MDPlan615C &plan)
{
 MDClearPlan615C(plan);
 if(!MDManagementClock615L(m,monotonic_ms)||m.ticket<=0)return false;
 // Prazo sem SL e uma causa de fechamento, nao uma prova de toque/fill.
 MDRecoveryEvidence67 evidence=market;
 bool emergency=MDProtectionCloseRequired(m.protection,monotonic_ms,observed_sl_matches);
 MDPlan615C candidate;
 if(!MDTestRecoverPlan615C(text,scope,contract,date,instance,level,snapshot,account,server,market_ms,evidence,cutoff,gate,candidate))return false;
 MDJournal610 j;
 if(!MDReplay610(candidate.journal,scope,contract,date,instance,j))return false;
 bool found=false;
 for(int i=0;i<candidate.count;i++)if(candidate.commands[i].action==2&&candidate.commands[i].ticket==m.ticket)found=true;
 if(emergency&&found)
 {
  string next=candidate.journal;
  if(!MDTestIntent615C(next,j,level,5,market_ms))return false;
  candidate.journal=next;
  for(int i=0;i<candidate.count;i++)if(candidate.commands[i].action==2)
  {
   MDCommand613 c;
   if(!MDCommandBuild613(j,level,4,candidate.commands[i].ticket,candidate.commands[i].volume,gate,c))return false;
   candidate.commands[i]=c;
  }
 }
 // Confirma protecoes e agenda apenas para o ticket rastreado. Outros tickets exigem controlador proprio.
 MDPlan615C filtered=candidate;filtered.count=0;
 for(int i=0;i<candidate.count;i++)
 {
  MDCommand613 c=candidate.commands[i];
  if(c.action==2)
  {
   if(c.ticket!=m.ticket){MDClearPlan615C(plan);return false;}
   if(observed_sl_matches&&observed_tp_matches)continue;
   if(!MDProtectionDue(m.protection,monotonic_ms))continue;
  }
  filtered.commands[filtered.count++]=c;
 }
 plan=filtered;return true;
}
#endif
