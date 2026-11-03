#ifndef MD_OBSERVATION_BRIDGE615N
#define MD_OBSERVATION_BRIDGE615N
#include "ModeloD_Readiness615M.mqh"
struct MDObservation615N
{
 long account,expected_account,now_ms,snapshot_ms;
 string server,expected_server,scope,domain;
 int date;
 bool connected,lock_held,daily_valid,calendar_valid,closed_minutes_checked,review_current,shadow_saved,session_open,cutoff,level_eligible,properties_valid;
 double tick_size,volume_min,volume_max,volume_step;
};
// Dados observacionais nao sao promovidos a provas operacionais ausentes.
void MDObservationGate615N(const MDJournal610 &journal,const MDObservation615N &s,MDDecision615M &decision)
{
 MDExecGate613 g;g.connected=s.connected;g.lock_held=s.lock_held;g.snapshot_fresh=s.review_current;
 g.ownership=false;g.entry_eligible=s.level_eligible;g.intent_durable=false;
 g.tick_size=s.tick_size;g.volume_min=s.volume_min;g.volume_max=s.volume_max;g.volume_step=s.volume_step;
 MDReadiness615M e;
 e.account=s.account;e.expected_account=s.expected_account;e.server=s.server;e.expected_server=s.expected_server;e.scope=s.scope;
 e.now_ms=s.now_ms;e.snapshot_ms=s.snapshot_ms;e.max_age_ms=3000;e.clock_domain=s.domain;e.snapshot_domain=s.domain;
 e.session_date=s.date;e.state_durable=false;e.reconciled=s.review_current;e.properties_valid=s.properties_valid;e.uncertain_action=true;
 e.calendar_valid=s.calendar_valid;e.daily_valid=s.daily_valid;
 // Fluxo atual termina no minuto fechado: nao certifica todos os ticks ate agora.
 e.touches_complete=false;e.clock_certified=false;e.session_open=s.session_open;e.cutoff=s.cutoff;e.level_eligible=s.level_eligible;
 e.protection_due=false;e.protection_inflight=false;e.close_intent=false;
 MDReady615M(journal,1,g,e,decision);
 // Fronteira explicita: esta ponte nunca produz comando nem libera gestao.
 decision.plan_allowed=false;decision.transport_allowed=false;
}
string MDObservationLine615N(int level,const MDObservation615N &s,const MDDecision615M &decision)
{
 return "PRONTIDAO_615N;nivel="+IntegerToString(level)+";data="+IntegerToString(s.date)+
 ";dados_diarios="+IntegerToString(s.daily_valid?1:0)+";minutos_fechados_conferidos="+IntegerToString(s.closed_minutes_checked?1:0)+
 ";conciliacao_observacional="+IntegerToString(s.review_current?1:0)+";estado_shadow_gravado="+IntegerToString(s.shadow_saved?1:0)+
 ";plano_entrada=0;transporte=0;motivos="+decision.reason;
}
#endif
