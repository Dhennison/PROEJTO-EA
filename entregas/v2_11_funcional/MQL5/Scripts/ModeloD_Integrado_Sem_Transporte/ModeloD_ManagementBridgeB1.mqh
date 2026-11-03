#ifndef MD_BRIDGE_B1
#define MD_BRIDGE_B1
#include "ModeloD_ResponseStore615Q.mqh"
#include "ModeloD_ConsolidatedStore615L7.mqh"
// Fonte de protecoes e respostas certificadas externa; neste pacote sao fixtures.
// Diario Q e estado L7 tem locks distintos. Intencoes Q sao gravadas primeiro;
// falha posterior nao expoe comando e conserva intencao para reconciliar.
bool MDBeginManagedB1(MDResponseStore615Q &source,MDStore615L7 &store,int level,
 const MDSnapshot69 &snapshot,long account,string server,long market_now,string raw_domain,long raw_now,
 const MDRecoveryEvidence67 &market,bool cutoff,bool sl,bool tp,MDExecGate613 &gate,int action,
 MDCommand613 &command,string &reason)
{
 command.valid=false;reason="GESTAO_BLOQUEADA";
 if(action<2||action>4||!source.IdentityB1(account,server))return false;
 MDPair615L3 pair;MDClock615L5 clock,timecandidate;
 MDResponseState615Q before;if(!source.Load(before)||!store.Load(pair,clock)||!MDClockAdvance615L5(clock,raw_domain,raw_now,timecandidate))return false;
 // Intervalo temporal incerto nao pode ser usado como instante pontual.
 if(timecandidate.lo!=timecandidate.hi){reason="INTERVALO_TEMPORAL_INDETERMINADO";return false;}
 MDJournal610 j;
 if(!source.JournalB1(j)||level<0||level>4||pair.cancel_slot.key!=MDPairKey615L3(j,level,pair.close_slot.management.ticket)+"|CANCEL")return false;
 MDManagement615L managed=pair.close_slot.management;MDPlan615C plan;
 if(!source.ManageB1(before.revision,managed,snapshot,market_now,timecandidate.lo,market,cutoff,sl,tp,gate,plan))return false;
 MDPair615L3 next=pair;next.close_slot.management=managed;
 MDCommand613 candidate;candidate.valid=false;
 if(action==2)
 {
  int found=-1;for(int i=0;i<plan.count;i++)if(plan.commands[i].action==2){if(found>=0)return false;found=i;}
  if(found<0||!MDManagementBegin615L(next.close_slot.management,timecandidate.lo,next.close_slot.management.ticket,true))return false;
  candidate=plan.commands[found];next.revision++;
 }
 else
 {
  MDPair615L3 staged;
  if(!MDPairPrepare615L3(next,plan,action,true,j.scope,j.contract,j.date,j.instance,level,staged,candidate))return false;
  next=staged;
 }
 if(!store.Commit(pair,clock,next,timecandidate)){reason="RESERVA_NAO_PERSISTIDA";return false;}
 command=candidate;reason="RESERVADO_EM_DISCO_SEM_TRANSPORTE";return true;
}
// Confirmacao de conclusao da chamada, inclusive rejeicao conhecida, deve vir
// de produtor verificado. Nao confundir conclusao da chamada com SL/TP aplicados.
bool MDCompleteProtectionB1(MDStore615L7 &store,long started_tag,string domain,long raw_now,bool verified_response)
{
 MDPair615L3 old,next;MDClock615L5 clock,timecandidate;
 if(!verified_response||!store.Load(old,clock)||old.close_slot.management.protection.last_started_ms!=started_tag||
   !MDClockAdvance615L5(clock,domain,raw_now,timecandidate)||timecandidate.lo!=timecandidate.hi)return false;
 next=old;
 if(!MDManagementComplete615L(next.close_slot.management,timecandidate.lo,next.close_slot.management.ticket))return false;
 next.revision++;return store.Commit(old,clock,next,timecandidate);
}
bool MDConfirmCancelB1(MDResponseStore615Q &source,MDStore615L7 &store,int level,const MDSnapshot69 &snapshot,
 long account,string server,long market_now,bool fresh,string domain,long raw_now)
{
 if(!fresh||!source.IdentityB1(account,server)||snapshot.account_key!=account||snapshot.server_key!=server)return false;
 MDJournal610 j;MDPair615L3 old,next;MDClock615L5 clock,timecandidate;MDOrigin68 origin;MDChainInput68 chain;MDChainResult68 result;string why;
 if(!source.JournalB1(j)||!store.Load(old,clock)||level<0||level>4||!j.r[level].cancel||
   old.cancel_slot.key!=MDPairKey615L3(j,level,old.close_slot.management.ticket)+"|CANCEL"||
   !MDOrigin611(j,j.scope,level,snapshot,origin)||!MDBuild69(snapshot,origin,market_now,chain,why)||
   !MDReconcileChain68(chain,result)||chain.order.state==0||
   !MDPairResolve615L3(old,3,old.cancel_slot.attempt,j.r[level].ticket,true,next)||
   !MDClockAdvance615L5(clock,domain,raw_now,timecandidate))return false;
 return store.Commit(old,clock,next,timecandidate);
}
bool MDConfirmCloseB1(MDResponseStore615Q &source,MDStore615L7 &store,int level,const MDBinding615L6 &binding,
 const MDSnapshot69 &snapshot,long account,string server,long market_now,bool fresh,string domain,long raw_now,double &residual)
{
 residual=0;if(!source.IdentityB1(account,server))return false;
 MDJournal610 j;MDResponseState615Q q;MDPair615L3 old,next;MDClock615L5 clock,newclock;
 if(!source.JournalB1(j)||!source.Load(q)||!store.Load(old,clock))return false;
 return MDConfirmPersist615L7(store,old,clock,binding,q.journal,j.scope,j.contract,j.date,j.instance,level,snapshot,
   account,server,market_now,domain,raw_now,fresh,next,newclock,residual);
}
#endif
