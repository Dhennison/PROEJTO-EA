#ifndef MD_LIFECYCLE_MQH
#define MD_LIFECYCLE_MQH
#include "ModeloD_Core.mqh"
// Redutor puro de eventos para UMA oportunidade/data/contrato.
// Nao acessa servidor. Adaptador deve fornecer historico integro, eventos
// reconciliados e snapshots por ticket. Nao usar como reconciliador pronto.
struct MDLifecycle
{
   MDLevel level;
   MDTap tape;
   MDOpportunity opportunity;
   bool pending, cancel_intent, cutoff, boundary_seen;
   bool cancel_inflight, close_inflight, position_open;
   double filled_total;
   long accepted_msc, open_msc;
};
void MDLifeStart(MDLifecycle &s,const MDLevel &level,const double open_price,const long open_msc)
{
   s.level=level; MDStartTape(s.tape,open_price,level.entry,open_msc);
   MDResetOpportunity(s.opportunity,level.valid_open);
   s.pending=false; s.cancel_intent=false; s.cutoff=false; s.boundary_seen=false;
   s.cancel_inflight=false; s.close_inflight=false; s.position_open=false;
   s.filled_total=0; s.accepted_msc=-1; s.open_msc=open_msc;
   if(!MDPositive(open_price)||open_msc<0) {s.tape.complete=false;s.opportunity.blocked=true;}
   if(s.tape.touched) s.opportunity.consumed=true;
}
bool MDLifeCanSubmit(const MDLifecycle &s,const bool gates_ok)
{
   return !s.pending && !s.cancel_intent && MDCanSubmit(s.level,s.opportunity,s.tape,gates_ok,!s.cutoff);
}
bool MDLifeRequest(MDLifecycle &s,const bool gates_ok)
{
   if(!MDLifeCanSubmit(s,gates_ok)) return false;
   s.opportunity.request_inflight=true; return true;
}
void MDLifeIncomplete(MDLifecycle &s)
{
   s.tape.complete=false; s.opportunity.blocked=true;
   // Intencao mantida mesmo se a aceitacao chegar depois desta falha.
   s.cancel_intent=true;
}
bool MDLifeTick(MDLifecycle &s,const double last,const long msc)
{
   double previous=s.tape.previous;
   if(!s.tape.complete || !s.tape.initialized || !MDPositive(last) || msc<s.tape.last_msc)
   { MDLifeIncomplete(s); return false; }
   bool fresh=MDObserve(s.tape,last,s.level.entry,msc);
   if(fresh && ((!s.opportunity.accepted && !s.opportunity.request_inflight) ||
      (s.opportunity.accepted && !MDAcceptedBeforeTouch(s.tape,s.accepted_msc))))
   { s.opportunity.consumed=true; s.cancel_intent=true; }
   // SL/TP matematicos, inclusive igualdade e saltos. Nunca usa arredondados.
   if((s.pending || s.opportunity.request_inflight) &&
      (MDCrossed(previous,last,s.level.sl) || MDCrossed(previous,last,s.level.tp)))
   { s.boundary_seen=true; s.opportunity.consumed=true; s.cancel_intent=true; }
   return true;
}
// Confirmacao real de aceite, nunca mero retorno de envio.
// Mesma marca de milissegundo nao prova precedencia; exige reconciliacao futura.
bool MDLifeAccepted(MDLifecycle &s,const long accepted_msc)
{
   if(s.opportunity.accepted) return false; // evento repetido nao reseta estado
   s.opportunity.request_inflight=false; s.opportunity.accepted=true;
   s.pending=true; s.accepted_msc=accepted_msc;
   bool valid=accepted_msc>=s.open_msc && s.tape.complete && !s.cutoff &&
      !s.level.geometry_blocked && !s.opportunity.invalidated &&
      !s.opportunity.blocked && !s.opportunity.consumed &&
      MDAcceptedBeforeTouch(s.tape,accepted_msc);
   if(!valid) {s.opportunity.consumed=true;s.cancel_intent=true;}
   return valid;
}
// Somente depois de confirmar no servidor que o pedido foi rejeitado e
// nao criou ordem/deal. Rejeicao transitoria pode liberar novo pedido.
void MDLifeRejectedConfirmed(MDLifecycle &s,const bool definitive)
{
   if(s.opportunity.accepted || s.pending) return;
   s.opportunity.request_inflight=false;
   if(definitive) s.opportunity.blocked=true;
   if(s.tape.touched) s.opportunity.consumed=true;
}
// Volume CUMULATIVO confirmado da mesma ordem; duplicata e regressao ignoradas.
// O adaptador protege cada posicao/ticket: este modulo nao agrega tickets.
bool MDLifeFillTotal(MDLifecycle &s,const double total)
{
   if(!MDPositive(total) || total<=s.filled_total) return false;
   s.filled_total=total; s.position_open=true; s.opportunity.consumed=true;
   return true;
}
void MDLifeCutoff(MDLifecycle &s)
{
   s.cutoff=true; s.cancel_intent=true; s.opportunity.consumed=true;
}
bool MDLifeCancelDue(const MDLifecycle &s,const bool connected)
{ return connected && s.pending && s.cancel_intent && !s.cancel_inflight; }
bool MDLifeCancelStart(MDLifecycle &s,const bool connected)
{
   if(!MDLifeCancelDue(s,connected)) return false;
   s.cancel_inflight=true; return true;
}
// Ausencia confirmada por reconciliacao, nao por retorno OrderSend.
void MDLifeCancelResult(MDLifecycle &s,const bool absence_confirmed)
{
   s.cancel_inflight=false;
   if(absence_confirmed) s.pending=false;
}
bool MDLifeCloseDue(const MDLifecycle &s,const bool connected)
{ return connected && s.cutoff && s.position_open && !s.close_inflight; }
bool MDLifeCloseStart(MDLifecycle &s,const bool connected)
{
   if(!MDLifeCloseDue(s,connected)) return false;
   s.close_inflight=true; return true;
}
void MDLifeCloseResult(MDLifecycle &s,const bool absence_confirmed)
{
   s.close_inflight=false;
   if(absence_confirmed) s.position_open=false;
}
#endif
