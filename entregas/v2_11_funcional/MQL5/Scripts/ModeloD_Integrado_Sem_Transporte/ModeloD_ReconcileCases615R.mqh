#ifndef MD_RECONCILE_CASES615R
#define MD_RECONCILE_CASES615R
#include "ModeloD_ResponseStoreCases615Q.mqh"
int checks615R=0,failures615R=0;string log615R="";
void Check615R(bool ok,string name){checks615R++;if(!ok)failures615R++;log615R+=(ok?"PASS: ":"FAIL: ")+name+"\r\n";}
void Run615R(string suffix)
{
 Run615Q(suffix);checks615R=checks615Q;failures615R=failures615Q;log615R=log615Q;
 string text,accepted;MDJournal610 j,parsed;MDSubmission615K request;Prepared615K(0,text,j,request);
 MDExecGate613 gate;MDReadiness615M e;MDCommand613 command;MDDecision615M decision;MDRecoveryEvidence67 market;
 Partial615C(accepted,gate,market);Evidence615M(e);MDEntryBundle615P source;MDResponseStore615Q store;
 string base="ModeloD_TEST_ONLY_615L4_Q_R_"+suffix;
 bool setup=source.Open("ModeloD_TEST_ONLY_615L4_P_R_"+suffix,j,0,123,"SINTETICO")&&source.Prepare(text,gate,e,command,decision)&&store.Open(base,j,0,123,"SINTETICO")&&store.Import(source);
 MDPlan615C plan;long now=1792141256927;MDResponseState615Q state;
 Check615R(setup&&!store.Reconcile615R(1,snap615C,now,market,false,gate,plan)&&!plan.valid&&plan.count==0,"R: tentativa incerta nao produz plano de gestao");
 bool linked=store.Response(1,1,true,10008,0,100)&&store.Bind(2,snap615C.o[0],(double)j.r[0].entry,snap615C.o[0].setup_msc+1,true,true,123,"SINTETICO");
 Check615R(linked&&store.Load(state)&&state.revision==3,"R: partida usa vinculo persistido em Q");
 gate.snapshot_fresh=false;
 Check615R(!store.Reconcile615R(3,snap615C,now,market,false,gate,plan)&&plan.count==0,"R: snapshot antigo nao publica intencoes");gate.snapshot_fresh=true;
 snap615C.account_key=999;
 Check615R(!store.Reconcile615R(3,snap615C,now,market,false,gate,plan),"R: snapshot de outra conta rejeitado");snap615C.account_key=123;
 snap615C.server_key="OUTRO";
 Check615R(!store.Reconcile615R(3,snap615C,now,market,false,gate,plan),"R: snapshot de outro servidor rejeitado");snap615C.server_key="SINTETICO";
 snap615C.complete=false;
 Check615R(!store.Reconcile615R(3,snap615C,now,market,false,gate,plan),"R: coleta incompleta nao altera estado");snap615C.complete=true;
 snap615C.p[0].volume=2;
 Check615R(!store.Reconcile615R(3,snap615C,now,market,false,gate,plan)&&store.Load(state)&&state.revision==3,"R: volumes divergentes rejeitados sem incrementar revisao");snap615C.p[0].volume=1;
 Check615R(store.Reconcile615R(3,snap615C,now,market,false,gate,plan)&&plan.valid&&plan.count==1&&plan.commands[0].action==2&&plan.commands[0].ticket==700&&plan.commands[0].volume==1,"R: parcial produz plano de protecao para ticket conciliado");
 Check615R(store.Load(state)&&state.revision==4&&MDReplay610(state.journal,j.scope,j.contract,j.date,j.instance,parsed)&&parsed.r[0].consumed,"R: consumo persistido antes de expor plano");
 Check615R(plan.commands[0].sl==j.r[0].sl&&plan.commands[0].tp==j.r[0].tp,"R: protecao mantem precos originais");
 Check615R(!store.Reconcile615R(3,snap615C,now,market,false,gate,plan)&&!plan.valid&&plan.count==0,"R: revisao antiga invalida plano anterior");
 Check615R(store.Reconcile615R(4,snap615C,now,market,false,gate,plan)&&store.Load(state)&&state.revision==4,"R: reconciliacao repetida nao duplica consumo no diario");
 store.Close();Check615R(store.Open(base,j,0,123,"SINTETICO")&&store.Load(state)&&state.revision==4&&state.receipt.touched,"R: reabertura preserva consumo");
 Check615R(store.Reconcile615R(4,snap615C,now,market,true,gate,plan)&&plan.count==2&&plan.commands[0].action==3&&plan.commands[0].ticket==100&&plan.commands[1].action==4&&plan.commands[1].ticket==700,"R: corte planeja cancelar saldo e fechar parcial");
 Check615R(store.Load(state)&&state.revision==5&&MDReplay610(state.journal,j.scope,j.contract,j.date,j.instance,parsed)&&parsed.r[0].cancel&&parsed.r[0].close,"R: cancelamento e fechamento persistidos juntos");
 store.Close();store.Open(base,j,0,123,"SINTETICO");
 Check615R(store.Reconcile615R(5,snap615C,now,market,false,gate,plan)&&plan.count==2&&plan.commands[1].action==4,"R: retomada conserva encerramento sem novo sinal de corte");
 gate.connected=false;Check615R(!store.Reconcile615R(5,snap615C,now,market,false,gate,plan)&&plan.count==0,"R: desconexao nao expoe plano");gate.connected=true;
 snap615C.p[0].ticket=701;
 Check615R(store.Reconcile615R(5,snap615C,now,market,false,gate,plan)&&plan.commands[1].ticket==701,"R: identifier preservado resolve novo ticket atual");snap615C.p[0].ticket=700;
 snap615C.p[0].identifier=999;
 Check615R(!store.Reconcile615R(5,snap615C,now,market,false,gate,plan),"R: posicao sem vinculo comprovado bloqueada");snap615C.p[0].identifier=500;
 MDWriteStore615L4(base+".tmp","FALHA_CONTROLADA");
 Check615R(!store.Reconcile615R(5,snap615C,now,market,false,gate,plan)&&!plan.valid&&plan.count==0,"R: residuo temporario impede exposicao de plano");
 store.Close();source.Close();
}
#endif
