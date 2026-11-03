#ifndef MD_READINESS_CASES615M
#define MD_READINESS_CASES615M
#include "ModeloD_ConsolidationCases615L7.mqh"
#include "ModeloD_Readiness615M.mqh"
int checks615M=0,failures615M=0;string log615M="";
void Check615M(bool ok,string name){checks615M++;if(!ok)failures615M++;log615M+=(ok?"PASS: ":"FAIL: ")+name+"\r\n";}
void Evidence615M(MDReadiness615M &e)
{
 e.account=123;e.expected_account=123;e.snapshot_ms=1000;e.now_ms=1100;e.max_age_ms=500;
 e.server="SINTETICO";e.expected_server="SINTETICO";e.scope="TEST_ONLY_615C";e.clock_domain="RAW_A";e.snapshot_domain="RAW_A";
 e.session_date=20261016;e.state_durable=true;e.reconciled=true;e.properties_valid=true;e.uncertain_action=false;
 e.calendar_valid=true;e.daily_valid=true;e.touches_complete=true;e.clock_certified=true;e.session_open=true;e.cutoff=false;e.level_eligible=true;
 e.protection_due=true;e.protection_inflight=false;e.close_intent=false;
}
void Run615M(string suffix)
{
 Run615L7(suffix);checks615M=checks615L7;failures615M=failures615L7;log615M=log615L7;
 MDReadiness615M e;MDDecision615M decision;MDCommand613 cmd;MDJournal610 j;MDExecGate613 g;
 MDDayControl day;MDPlan615C plan;string journal;MDRecoveryEvidence67 market;
 bool entry=Day615C(day);MDTestGate615C(g);
 entry=entry&&MDTestEntry615C(day,Header615C(),"TEST_ONLY_615C",1,0,3,day.frozen.open_msc+10,true,true,true,g,plan)&&MDReplay610(plan.journal,"TEST_ONLY_615C","WINZ26",20261016,1,j);
 Evidence615M(e);
 Check615M(entry&&MDGuardedCommand615M(j,0,1,0,0,g,e,decision,cmd)&&cmd.valid&&cmd.price==207380,"M: entrada elegivel preserva comando do nucleo");
 Check615M(!decision.transport_allowed,"M: plano admissivel nao habilita transporte");
 Evidence615M(e);MDTestGate615C(g);e.account=999;Check615M(!MDGuardedCommand615M(j,0,1,0,0,g,e,decision,cmd)&&!cmd.valid&&!decision.transport_allowed&&StringFind(decision.reason,"IDENTIDADE_DIVERGENTE")>=0,"M: bloqueio de entrada 1 - IDENTIDADE_DIVERGENTE");
 Evidence615M(e);MDTestGate615C(g);e.server="OUTRO";Check615M(!MDGuardedCommand615M(j,0,1,0,0,g,e,decision,cmd)&&!cmd.valid&&!decision.transport_allowed&&StringFind(decision.reason,"IDENTIDADE_DIVERGENTE")>=0,"M: bloqueio de entrada 2 - IDENTIDADE_DIVERGENTE");
 Evidence615M(e);MDTestGate615C(g);e.scope="OUTRO";Check615M(!MDGuardedCommand615M(j,0,1,0,0,g,e,decision,cmd)&&!cmd.valid&&!decision.transport_allowed&&StringFind(decision.reason,"IDENTIDADE_DIVERGENTE")>=0,"M: bloqueio de entrada 3 - IDENTIDADE_DIVERGENTE");
 Evidence615M(e);MDTestGate615C(g);g.connected=false;Check615M(!MDGuardedCommand615M(j,0,1,0,0,g,e,decision,cmd)&&!cmd.valid&&!decision.transport_allowed&&StringFind(decision.reason,"DESCONECTADO")>=0,"M: bloqueio de entrada 4 - DESCONECTADO");
 Evidence615M(e);MDTestGate615C(g);g.lock_held=false;Check615M(!MDGuardedCommand615M(j,0,1,0,0,g,e,decision,cmd)&&!cmd.valid&&!decision.transport_allowed&&StringFind(decision.reason,"SEM_LOCK")>=0,"M: bloqueio de entrada 5 - SEM_LOCK");
 Evidence615M(e);MDTestGate615C(g);e.state_durable=false;Check615M(!MDGuardedCommand615M(j,0,1,0,0,g,e,decision,cmd)&&!cmd.valid&&!decision.transport_allowed&&StringFind(decision.reason,"ESTADO_OU_INTENCAO_NAO_DURAVEL")>=0,"M: bloqueio de entrada 6 - ESTADO_OU_INTENCAO_NAO_DURAVEL");
 Evidence615M(e);MDTestGate615C(g);g.intent_durable=false;Check615M(!MDGuardedCommand615M(j,0,1,0,0,g,e,decision,cmd)&&!cmd.valid&&!decision.transport_allowed&&StringFind(decision.reason,"ESTADO_OU_INTENCAO_NAO_DURAVEL")>=0,"M: bloqueio de entrada 7 - ESTADO_OU_INTENCAO_NAO_DURAVEL");
 Evidence615M(e);MDTestGate615C(g);e.reconciled=false;Check615M(!MDGuardedCommand615M(j,0,1,0,0,g,e,decision,cmd)&&!cmd.valid&&!decision.transport_allowed&&StringFind(decision.reason,"CONCILIACAO_PENDENTE")>=0,"M: bloqueio de entrada 8 - CONCILIACAO_PENDENTE");
 Evidence615M(e);MDTestGate615C(g);g.snapshot_fresh=false;Check615M(!MDGuardedCommand615M(j,0,1,0,0,g,e,decision,cmd)&&!cmd.valid&&!decision.transport_allowed&&StringFind(decision.reason,"LEITURA_ANTIGA_OU_ORIGEM_TEMPORAL_DIVERGENTE")>=0,"M: bloqueio de entrada 9 - LEITURA_ANTIGA_OU_ORIGEM_TEMPORAL_DIVERGENTE");
 Evidence615M(e);MDTestGate615C(g);e.now_ms=1501;Check615M(!MDGuardedCommand615M(j,0,1,0,0,g,e,decision,cmd)&&!cmd.valid&&!decision.transport_allowed&&StringFind(decision.reason,"LEITURA_ANTIGA_OU_ORIGEM_TEMPORAL_DIVERGENTE")>=0,"M: bloqueio de entrada 10 - LEITURA_ANTIGA_OU_ORIGEM_TEMPORAL_DIVERGENTE");
 Evidence615M(e);MDTestGate615C(g);e.snapshot_ms=1101;Check615M(!MDGuardedCommand615M(j,0,1,0,0,g,e,decision,cmd)&&!cmd.valid&&!decision.transport_allowed&&StringFind(decision.reason,"LEITURA_ANTIGA_OU_ORIGEM_TEMPORAL_DIVERGENTE")>=0,"M: bloqueio de entrada 11 - LEITURA_ANTIGA_OU_ORIGEM_TEMPORAL_DIVERGENTE");
 Evidence615M(e);MDTestGate615C(g);e.snapshot_domain="RAW_B";Check615M(!MDGuardedCommand615M(j,0,1,0,0,g,e,decision,cmd)&&!cmd.valid&&!decision.transport_allowed&&StringFind(decision.reason,"LEITURA_ANTIGA_OU_ORIGEM_TEMPORAL_DIVERGENTE")>=0,"M: bloqueio de entrada 12 - LEITURA_ANTIGA_OU_ORIGEM_TEMPORAL_DIVERGENTE");
 Evidence615M(e);MDTestGate615C(g);e.max_age_ms=0;Check615M(!MDGuardedCommand615M(j,0,1,0,0,g,e,decision,cmd)&&!cmd.valid&&!decision.transport_allowed&&StringFind(decision.reason,"LEITURA_ANTIGA_OU_ORIGEM_TEMPORAL_DIVERGENTE")>=0,"M: bloqueio de entrada 13 - LEITURA_ANTIGA_OU_ORIGEM_TEMPORAL_DIVERGENTE");
 Evidence615M(e);MDTestGate615C(g);e.properties_valid=false;Check615M(!MDGuardedCommand615M(j,0,1,0,0,g,e,decision,cmd)&&!cmd.valid&&!decision.transport_allowed&&StringFind(decision.reason,"PROPRIEDADES_NAO_VALIDADAS")>=0,"M: bloqueio de entrada 14 - PROPRIEDADES_NAO_VALIDADAS");
 Evidence615M(e);MDTestGate615C(g);e.uncertain_action=true;Check615M(!MDGuardedCommand615M(j,0,1,0,0,g,e,decision,cmd)&&!cmd.valid&&!decision.transport_allowed&&StringFind(decision.reason,"TENTATIVA_DA_ACAO_AINDA_INCERTA")>=0,"M: bloqueio de entrada 15 - TENTATIVA_DA_ACAO_AINDA_INCERTA");
 Evidence615M(e);MDTestGate615C(g);e.session_date=20261019;Check615M(!MDGuardedCommand615M(j,0,1,0,0,g,e,decision,cmd)&&!cmd.valid&&!decision.transport_allowed&&StringFind(decision.reason,"SESSAO_DIVERGENTE")>=0,"M: bloqueio de entrada 16 - SESSAO_DIVERGENTE");
 Evidence615M(e);MDTestGate615C(g);e.calendar_valid=false;Check615M(!MDGuardedCommand615M(j,0,1,0,0,g,e,decision,cmd)&&!cmd.valid&&!decision.transport_allowed&&StringFind(decision.reason,"CALENDARIO_PENDENTE")>=0,"M: bloqueio de entrada 17 - CALENDARIO_PENDENTE");
 Evidence615M(e);MDTestGate615C(g);e.daily_valid=false;Check615M(!MDGuardedCommand615M(j,0,1,0,0,g,e,decision,cmd)&&!cmd.valid&&!decision.transport_allowed&&StringFind(decision.reason,"DADOS_DIARIOS_PENDENTES")>=0,"M: bloqueio de entrada 18 - DADOS_DIARIOS_PENDENTES");
 Evidence615M(e);MDTestGate615C(g);e.touches_complete=false;Check615M(!MDGuardedCommand615M(j,0,1,0,0,g,e,decision,cmd)&&!cmd.valid&&!decision.transport_allowed&&StringFind(decision.reason,"HISTORICO_DE_TOQUES_PENDENTE")>=0,"M: bloqueio de entrada 19 - HISTORICO_DE_TOQUES_PENDENTE");
 Evidence615M(e);MDTestGate615C(g);e.clock_certified=false;Check615M(!MDGuardedCommand615M(j,0,1,0,0,g,e,decision,cmd)&&!cmd.valid&&!decision.transport_allowed&&StringFind(decision.reason,"RELOGIO_NAO_CERTIFICADO")>=0,"M: bloqueio de entrada 20 - RELOGIO_NAO_CERTIFICADO");
 Evidence615M(e);MDTestGate615C(g);e.session_open=false;Check615M(!MDGuardedCommand615M(j,0,1,0,0,g,e,decision,cmd)&&!cmd.valid&&!decision.transport_allowed&&StringFind(decision.reason,"FORA_DA_JANELA_DE_ENTRADA")>=0,"M: bloqueio de entrada 21 - FORA_DA_JANELA_DE_ENTRADA");
 Evidence615M(e);MDTestGate615C(g);e.cutoff=true;Check615M(!MDGuardedCommand615M(j,0,1,0,0,g,e,decision,cmd)&&!cmd.valid&&!decision.transport_allowed&&StringFind(decision.reason,"FORA_DA_JANELA_DE_ENTRADA")>=0,"M: bloqueio de entrada 22 - FORA_DA_JANELA_DE_ENTRADA");
 Evidence615M(e);MDTestGate615C(g);e.level_eligible=false;Check615M(!MDGuardedCommand615M(j,0,1,0,0,g,e,decision,cmd)&&!cmd.valid&&!decision.transport_allowed&&StringFind(decision.reason,"NIVEL_INELEGIVEL")>=0,"M: bloqueio de entrada 23 - NIVEL_INELEGIVEL");
 Evidence615M(e);MDTestGate615C(g);e.now_ms=1500;
 Check615M(MDGuardedCommand615M(j,0,1,0,0,g,e,decision,cmd),"M: fronteira inclusiva de frescor respeitada");
 e.daily_valid=false;e.touches_complete=false;g.lock_held=false;
 Check615M(!MDGuardedCommand615M(j,0,1,0,0,g,e,decision,cmd)&&StringFind(decision.reason,"SEM_LOCK")>=0&&StringFind(decision.reason,"DADOS_DIARIOS_PENDENTES")>=0&&StringFind(decision.reason,"HISTORICO_DE_TOQUES_PENDENTE")>=0,"M: relatorio mostra bloqueios simultaneos");
 log615M+=MDReadinessLine615M(1,decision)+"\r\n";
 Evidence615M(e);MDTestGate615C(g);
 Check615M(!MDGuardedCommand615M(j,5,1,0,0,g,e,decision,cmd)&&!decision.plan_allowed&&!cmd.valid,"M: nivel inexistente continua rejeitado pelo nucleo");
 // Nao deixar falha de entrada impedir gestao de exposicao comprovada.
 Partial615C(journal,g,market);Recover615C(journal,market,true,g,plan);MDReplay610(plan.journal,"TEST_ONLY_615C","WINZ26",20261016,1,j);
 Evidence615M(e);e.daily_valid=false;e.touches_complete=false;e.calendar_valid=false;e.clock_certified=false;e.session_open=false;e.cutoff=true;e.level_eligible=false;e.session_date=20261019;e.close_intent=true;
 Check615M(MDGuardedCommand615M(j,0,3,100,0,g,e,decision,cmd)&&cmd.ticket==100,"M: falhas de entrada nao impedem plano de cancelamento comprovado");
 Check615M(MDGuardedCommand615M(j,0,4,700,1,g,e,decision,cmd)&&cmd.ticket==700&&cmd.volume==1&&!cmd.buy,"M: encerramento preserva contrato ticket e volume conciliados");
 log615M+=MDReadinessLine615M(4,decision)+"\r\n";
 Check615M(!MDGuardedCommand615M(j,0,2,700,1,g,e,decision,cmd)&&StringFind(decision.reason,"ENCERRAMENTO_TEM_PRIORIDADE")>=0,"M: protecao nao concorre com encerramento");
 e.uncertain_action=true;
 Check615M(!MDGuardedCommand615M(j,0,4,700,1,g,e,decision,cmd),"M: fechamento em voo nao e duplicado");e.uncertain_action=false;
 g.connected=false;Check615M(!MDGuardedCommand615M(j,0,4,700,1,g,e,decision,cmd),"M: desconexao bloqueia comando mesmo no corte");g.connected=true;
 g.ownership=false;Check615M(!MDGuardedCommand615M(j,0,4,700,1,g,e,decision,cmd),"M: sem titularidade nao fecha posicao");g.ownership=true;
 e.reconciled=false;Check615M(!MDGuardedCommand615M(j,0,4,700,1,g,e,decision,cmd),"M: volume nao conciliado nao produz fechamento");
 Evidence615M(e);MDTestGate615C(g);
 Check615M(!MDGuardedCommand615M(j,0,2,700,1,g,e,decision,cmd)&&decision.reason=="ENCERRAMENTO_REGISTRADO_TEM_PRIORIDADE","M: evidencia desatualizada nao apaga encerramento do diario");
 // Protecao usa niveis persistidos; ajuste diario ausente nao apaga a exposicao.
 Partial615C(journal,g,market);MDReplay610(journal,"TEST_ONLY_615C","WINZ26",20261016,1,j);Evidence615M(e);e.daily_valid=false;
 Check615M(MDGuardedCommand615M(j,0,2,700,1,g,e,decision,cmd)&&cmd.sl==207005&&cmd.tp==207590,"M: protecao usa SL TP originais mesmo sem novos dados diarios");
 e.protection_due=false;Check615M(!MDGuardedCommand615M(j,0,2,700,1,g,e,decision,cmd),"M: agenda ainda nao vencida bloqueia protecao");e.protection_due=true;
 e.protection_inflight=true;Check615M(!MDGuardedCommand615M(j,0,2,700,1,g,e,decision,cmd),"M: protecao em voo nao duplica");e.protection_inflight=false;
 Check615M(!MDGuardedCommand615M(j,0,4,700,1,g,e,decision,cmd)&&!decision.plan_allowed,"M: gates nao substituem intencao de fechamento no diario");
 Check615M(!MDGuardedCommand615M(j,0,3,100,0,g,e,decision,cmd)&&!decision.plan_allowed,"M: gates nao substituem intencao de cancelamento no diario");
 Check615M(!MDGuardedCommand615M(j,0,0,700,1,g,e,decision,cmd),"M: acao desconhecida rejeitada");
}
#endif
