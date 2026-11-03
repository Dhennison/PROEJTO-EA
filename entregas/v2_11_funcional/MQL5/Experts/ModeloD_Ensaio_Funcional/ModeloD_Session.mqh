#ifndef MODELOD_SESSION_MQH
#define MODELOD_SESSION_MQH
#include "ModeloD_Calendar.mqh"
struct MDSessionRule
{
   int date,scheduled_open,normal_end,cutoff;
   bool verified;
   string source;
};
void MDSessionClear(MDSessionRule &r)
{r.date=0;r.scheduled_open=0;r.normal_end=0;r.cutoff=0;r.verified=false;r.source="";}
// Horarios em segundos desde meia-noite de Brasilia. Regra por data exata.
// normal_end NAO certifica fim de leilao nem completude do OHLC.
bool MDSessionSet(const int date,const int open_sec,const int normal_end_sec,
                  const int cutoff_sec,const bool reviewed,const string source,
                  MDSessionRule &r)
{
   MDSessionClear(r);
   if(!reviewed || source=="" || MDCalendar2026(date)!=1)return false;
   if(open_sec<0 || normal_end_sec>=86400 || open_sec>=normal_end_sec)return false;
   if(cutoff_sec<=open_sec || cutoff_sec>normal_end_sec)return false;
   r.date=date;r.scheduled_open=open_sec;r.normal_end=normal_end_sec;
   r.cutoff=cutoff_sec;r.verified=true;r.source=source;return true;
}
// Snapshot limitado aos dias examinados; nao estende grade atual ao passado/futuro.
// Para outro dia, o adaptador devera fornecer regra revisada via MDSessionSet.
bool MDObservedSessionRule(const int date,const string candidate,MDSessionRule &r)
{
   MDSessionClear(r);
   if(date!=20261009 && date!=20261013 && date!=20261014 && date!=20261015 && date!=20261016)return false;
   // WINV26 no vencimento tem grade especial e cutoff ainda nao revisado.
   if(candidate!="WINZ26")return false;
   return MDSessionSet(date,9*3600,18*3600+25*60,18*3600,true,
      "B3_INDICES_CONSULTA_20261016;MODELO_D_9.2_9.8",r);
}
enum MDSessionPhase
{MD_SESSION_BLOCKED=0,MD_BEFORE_OPEN=1,MD_WAIT_REAL_OPEN=2,MD_ENTRY_WINDOW=3,MD_CUTOFF=4};
MDSessionPhase MDSessionEvaluate(const MDSessionRule &r,const int date,
   const int now_sec,const bool clock_verified,const bool real_open_verified)
{
   if(!r.verified || r.source=="" || r.date!=date || MDCalendar2026(date)!=1 ||
      !clock_verified || now_sec<0 || now_sec>=86400 ||
      r.scheduled_open<0 || r.cutoff<=r.scheduled_open ||
      r.normal_end<r.cutoff || r.normal_end>=86400)return MD_SESSION_BLOCKED;
   // Cutoff independe de tick/abertura e prevalece sobre espera pela abertura.
   if(now_sec>=r.cutoff)return MD_CUTOFF;
   if(now_sec<r.scheduled_open)return MD_BEFORE_OPEN;
   if(!real_open_verified)return MD_WAIT_REAL_OPEN;
   return MD_ENTRY_WINDOW; // Apenas janela temporal; NAO autoriza ordem.
}
#endif
