#ifndef MD_READINESS615M
#define MD_READINESS615M
#include "ModeloD_Execution.mqh"
// Evidencias produzidas externamente. Nao sao atestados emitidos por este modulo.
struct MDReadiness615M
{
 long account,expected_account,snapshot_ms,now_ms,max_age_ms;
 string server,expected_server,scope,clock_domain,snapshot_domain;
 int session_date;
 bool state_durable,reconciled,properties_valid,uncertain_action;
 bool calendar_valid,daily_valid,touches_complete,clock_certified,session_open,cutoff,level_eligible;
 bool protection_due,protection_inflight,close_intent;
};
struct MDDecision615M {bool plan_allowed,transport_allowed;string reason;};
void MDReason615M(bool ok,string reason,string &all)
{if(!ok){if(all!="")all+=";";all+=reason;}}
bool MDReady615M(const MDJournal610 &j,int action,const MDExecGate613 &g,const MDReadiness615M &e,MDDecision615M &out)
{
 out.plan_allowed=false;out.transport_allowed=false;out.reason="";
 MDReason615M(j.valid,"DIARIO_INVALIDO",out.reason);
 MDReason615M(action>=1&&action<=4,"ACAO_INVALIDA",out.reason);
 MDReason615M(e.account>0&&e.account==e.expected_account&&e.server!=""&&e.server==e.expected_server&&e.scope==j.scope,"IDENTIDADE_DIVERGENTE",out.reason);
 MDReason615M(g.connected,"DESCONECTADO",out.reason);
 MDReason615M(g.lock_held,"SEM_LOCK",out.reason);
 MDReason615M(e.state_durable&&g.intent_durable,"ESTADO_OU_INTENCAO_NAO_DURAVEL",out.reason);
 MDReason615M(e.reconciled,"CONCILIACAO_PENDENTE",out.reason);
 bool fresh=g.snapshot_fresh&&e.now_ms>=0&&e.snapshot_ms>=0&&e.now_ms>=e.snapshot_ms&&e.max_age_ms>0&&
 e.now_ms-e.snapshot_ms<=e.max_age_ms&&e.clock_domain!=""&&e.clock_domain==e.snapshot_domain;
 MDReason615M(fresh,"LEITURA_ANTIGA_OU_ORIGEM_TEMPORAL_DIVERGENTE",out.reason);
 MDReason615M(e.properties_valid&&g.tick_size==5,"PROPRIEDADES_NAO_VALIDADAS",out.reason);
 MDReason615M(!e.uncertain_action,"TENTATIVA_DA_ACAO_AINDA_INCERTA",out.reason);
 if(action==1)
 {
  MDReason615M(e.session_date==j.date,"SESSAO_DIVERGENTE",out.reason);
  MDReason615M(e.calendar_valid,"CALENDARIO_PENDENTE",out.reason);
  MDReason615M(e.daily_valid,"DADOS_DIARIOS_PENDENTES",out.reason);
  MDReason615M(e.touches_complete,"HISTORICO_DE_TOQUES_PENDENTE",out.reason);
  MDReason615M(e.clock_certified,"RELOGIO_NAO_CERTIFICADO",out.reason);
  MDReason615M(e.session_open&&!e.cutoff,"FORA_DA_JANELA_DE_ENTRADA",out.reason);
  MDReason615M(e.level_eligible&&g.entry_eligible,"NIVEL_INELEGIVEL",out.reason);
 }
 if(action>=2&&action<=4)MDReason615M(g.ownership,"TITULARIDADE_NAO_COMPROVADA",out.reason);
 if(action==2)
 {
  MDReason615M(e.protection_due&&!e.protection_inflight,"AGENDA_DE_PROTECAO_BLOQUEADA",out.reason);
  MDReason615M(!e.close_intent&&!e.cutoff,"ENCERRAMENTO_TEM_PRIORIDADE",out.reason);
 }
 if(out.reason!="")return false;
 out.plan_allowed=true;out.reason="PLANO_ADMISSIVEL_SEM_TRANSPORTE";return true;
}
bool MDGuardedCommand615M(const MDJournal610 &j,int level,int action,long ticket,double volume,
 const MDExecGate613 &g,const MDReadiness615M &e,MDDecision615M &decision,MDCommand613 &command)
{
 command.valid=false;
 if(!MDReady615M(j,action,g,e,decision))return false;
 if(action==2&&level>=0&&level<5&&j.r[level].close)
 {decision.plan_allowed=false;decision.reason="ENCERRAMENTO_REGISTRADO_TEM_PRIORIDADE";return false;}
 if(!MDCommandBuild613(j,level,action,ticket,volume,g,command))
 {decision.plan_allowed=false;decision.reason="COMANDO_REJEITADO_PELO_NUCLEO";return false;}
 return true;
}
string MDReadinessLine615M(int action,const MDDecision615M &d)
{return "PRONTIDAO_615M;acao="+IntegerToString(action)+";plano_admissivel="+IntegerToString(d.plan_allowed?1:0)+";transporte=0;motivos="+d.reason;}
#endif
