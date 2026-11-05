#ifndef MODELO_D_PROTECTION_MQH
#define MODELO_D_PROTECTION_MQH
// Agenda pura; chamadas ao servidor e confirmacao de protecoes NAO implementadas.
// Relogio monotono em ms, nunca TimeCurrent para espacamento de tentativas.
struct MDProtection
{
   int initial_completed;
   bool inflight, started;
   long last_started_ms, sixth_completed_ms;
};
void MDProtectionReset(MDProtection &p)
{
   p.initial_completed=0; p.inflight=false; p.started=false;
   p.last_started_ms=-1; p.sixth_completed_ms=-1;
}
bool MDProtectionDue(const MDProtection &p,const long now_ms)
{
   if(p.inflight) return false;
   if(!p.started) return true;
   if(p.initial_completed<6) return now_ms-p.last_started_ms>=2000;
   return now_ms-p.last_started_ms>=10000;
}
void MDProtectionStarted(MDProtection &p,const long now_ms)
{
   p.started=true; p.inflight=true; p.last_started_ms=now_ms;
}
void MDProtectionCompleted(MDProtection &p,const long now_ms)
{
   if(!p.inflight) return;
   p.inflight=false;
   if(p.initial_completed<6)
   {
      p.initial_completed++;
      if(p.initial_completed==6) p.sixth_completed_ms=now_ms;
   }
}
bool MDProtectionCloseRequired(const MDProtection &p,const long now_ms,const bool sl_present)
{
   return !sl_present && p.sixth_completed_ms>=0 && now_ms-p.sixth_completed_ms>=180000;
}
#endif
