#ifndef MD_DAY_CONTROL
#define MD_DAY_CONTROL
#include "ModeloD_Lifecycle.mqh"
#include "ModeloD_Session.mqh"
// Contrato entre adaptador de dados e controlador puro. Flags de evidencia
// nao sao verificadas magicamente: o adaptador deve estabelecer proveniencia.
struct MDDataEvidence
{
   int date,previous_date,adjustment_date,source_date,expiry_date;
   string contract,ohlc_contract,opening_contract,adjustment_contract,source;
   bool ohlc_verified,opening_verified,adjustment_verified;
   double previous_adjustment,tick_size;
   long open_msc;
   MDInputs values;
   MDSessionRule session;
};
struct MDDayControl
{
   bool ready,conflict,cutoff;
   MDDataEvidence frozen;
   MDDay day;
   MDLifecycle levels[5];
};
// Epoch civil do servidor para 2026; conversao de fuso pertence ao adaptador.
long MDCivilMidnight2026(const int date)
{int day=MDOrdinal2026(date);return day<0?-1:1767225600000+(long)(day-1)*86400000;}
bool MDDataValid(const MDDataEvidence &e)
{
   string why;
   if(e.date!=e.adjustment_date || MDPreviousSession2026(e.date)!=e.previous_date || e.previous_date==0 ||
      e.source_date!=e.previous_date || e.contract=="" || e.ohlc_contract!=e.contract ||
      e.opening_contract!=e.contract || e.adjustment_contract!=e.contract ||
      e.source!="BVBG.187.01" || !e.ohlc_verified || !e.opening_verified || !e.adjustment_verified ||
      !MDPositive(e.previous_adjustment) || e.tick_size!=5 || e.open_msc<0 ||
      !MDWINExpiryCheck2026(e.contract,e.date,e.expiry_date,why)) return false;
   if(MDSessionEvaluate(e.session,e.date,e.session.scheduled_open,true,true)!=MD_ENTRY_WINDOW)return false;
   long midnight=MDCivilMidnight2026(e.date);
   if(e.open_msc<midnight+(long)e.session.scheduled_open*1000 || e.open_msc>=midnight+(long)e.session.cutoff*1000)return false;
   MDDay check;return MDCalculate(e.values,check);
}
bool MDDayStart(MDDayControl &s,const MDDataEvidence &e)
{
   s.ready=false;s.conflict=false;s.cutoff=false;
   if(!MDDataValid(e))return false;
   s.frozen=e;
   if(!MDCalculate(e.values,s.day))return false;
   for(int i=0;i<5;i++)MDLifeStart(s.levels[i],s.day.levels[i],e.values.open_today,e.open_msc);
   s.ready=true;return true;
}
bool MDDaySameData(const MDDataEvidence &a,const MDDataEvidence &b)
{
   return a.date==b.date && a.previous_date==b.previous_date && a.contract==b.contract &&
      a.open_msc==b.open_msc && a.expiry_date==b.expiry_date && a.previous_adjustment==b.previous_adjustment &&
      a.values.high_prev==b.values.high_prev && a.values.low_prev==b.values.low_prev &&
      a.values.close_prev==b.values.close_prev && a.values.open_today==b.values.open_today &&
      a.values.adjustment==b.values.adjustment && a.session.scheduled_open==b.session.scheduled_open &&
      a.session.cutoff==b.session.cutoff && a.session.normal_end==b.session.normal_end;
}
void MDDayObserve(MDDayControl &s,const long msc,const double last)
{
   if(!s.ready)return;
   for(int i=0;i<5;i++)MDLifeTick(s.levels[i],last,msc);
}
// Chamavel por timer/replay sem tick. Nenhum envio de ordens nesta camada.
void MDDayClock(MDDayControl &s,const int date,const int second,const bool clock_verified)
{
   if(!s.ready)return;
   if(clock_verified && MDDate2026(date) && second>=0 && second<86400 &&
      (date>s.frozen.date || MDSessionEvaluate(s.frozen.session,date,second,true,true)==MD_CUTOFF))
   {s.cutoff=true;for(int i=0;i<5;i++)MDLifeCutoff(s.levels[i]);}
}
// Retorna MOTIVO de simulacao; nao autoriza negociacao no servidor.
string MDDayReason(MDDayControl &s,const MDDataEvidence &current,const string observed_contract,
   const int date,const int second,const long now_msc,const bool connected,
   const bool clock_verified,const bool history_verified,const bool reconciled,const int level)
{
   if(!s.ready)return "BLOQUEADO_DADOS_INICIAIS";
   if(level<0||level>=5)return "BLOQUEADO_NIVEL_INVALIDO";
   if(observed_contract!=s.frozen.contract)s.conflict=true;
   if(clock_verified && (MDCivilMidnight2026(date)<0 || second<0 || second>=86400 ||
      now_msc<MDCivilMidnight2026(date)+(long)second*1000 || now_msc>=MDCivilMidnight2026(date)+(long)(second+1)*1000))
      return "BLOQUEADO_RELOGIO_INCOERENTE";
   // Horario de corte prevalece mesmo com desconexao ou dados faltantes.
   MDDayClock(s,date,second,clock_verified);
   if(s.cutoff)return "CORTE_HORARIO";
   if(date!=s.frozen.date)return "BLOQUEADO_DATA";
   if(s.conflict)return "BLOQUEADO_CONFLITO_CONTRATO_OU_DADOS";
   if(!connected)return "BLOQUEADO_CONEXAO";
   if(!clock_verified)return "BLOQUEADO_RELOGIO";
   if(!MDDataValid(current))return "BLOQUEADO_DADOS_ATUAIS";
   if(!MDDaySameData(s.frozen,current)){s.conflict=true;return "BLOQUEADO_CONFLITO_CONTRATO_OU_DADOS";}
   if(MDSessionEvaluate(s.frozen.session,date,second,true,true)!=MD_ENTRY_WINDOW || now_msc<s.frozen.open_msc)
      return "FORA_JANELA_OU_ANTES_ABERTURA_REAL";
   if(!history_verified || !s.levels[level].tape.complete || now_msc<s.levels[level].tape.last_msc)
      return "BLOQUEADO_HISTORICO";
   if(!reconciled)return "BLOQUEADO_RECONCILIACAO";
   if(s.day.levels[level].geometry_blocked)return "BLOQUEADO_GEOMETRIA";
   if(!s.day.levels[level].valid_open)return "INVALIDADO_ABERTURA";
   if(s.levels[level].tape.touched)return "PRIMEIRO_TOQUE_JA_OCORREU";
   if(!MDLifeCanSubmit(s.levels[level],true))return "OPORTUNIDADE_INDISPONIVEL";
   return "ELEGIVEL_NA_SIMULACAO_SEM_ORDENS";
}
#endif
