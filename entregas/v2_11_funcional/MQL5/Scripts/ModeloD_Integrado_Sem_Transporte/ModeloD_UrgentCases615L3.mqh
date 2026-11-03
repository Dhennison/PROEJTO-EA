#ifndef MD_URGENT_CASES615L3
#define MD_URGENT_CASES615L3
#include "ModeloD_ManagementStateCases615L2.mqh"
#include "ModeloD_UrgentFile615L3.mqh"
int checks615L3=0,failures615L3=0;string log615L3="";
void Check615L3(bool ok,string name){checks615L3++;if(!ok)failures615L3++;log615L3+=(ok?"PASS: ":"FAIL: ")+name+"\r\n";}
bool Prepare615L3(const MDPair615L3 &s,const MDPlan615C &p,int action,bool durable,MDPair615L3 &next,MDCommand613 &c)
{return MDPairPrepare615L3(s,p,action,durable,"TEST_ONLY_615C","WINZ26",20261016,1,0,next,c);}
void Run615L3(string suffix)
{
 Run615L2(suffix);checks615L3=checks615L2;failures615L3=failures615L2;log615L3=log615L2;
 string text;MDExecGate613 g;MDRecoveryEvidence67 e;MDPlan615C plan;MDCommand613 cmd;MDJournal610 j;
 bool partial=Partial615C(text,g,e);bool planned=Recover615C(text,e,true,g,plan);
 Check615L3(partial&&planned&&plan.count==2,"L3: cutoff gera cancelamento e fechamento conciliados");
 MDReplay610(plan.journal,"TEST_ONLY_615C","WINZ26",20261016,1,j);
 string key=MDPairKey615L3(j,0,700),domain="CLOCK_FIXTURE_L3";MDPair615L3 state,next,restored,closed;
 MDPairInit615L3(state,key,domain,700);
 Check615L3(MDPairValid615L3(state),"L3: dois controles vinculados ao mesmo pedido");
 Check615L3(!Prepare615L3(state,plan,3,false,next,cmd),"L3: intencao ainda nao duravel bloqueia reserva");
 Check615L3(Prepare615L3(state,plan,3,true,next,cmd)&&cmd.ticket==100,"L3: reserva de cancelamento do saldo");state=next;
 Check615L3(!Prepare615L3(state,plan,3,true,next,cmd),"L3: cancelamento reservado nao duplica");
 Check615L3(Prepare615L3(state,plan,4,true,next,cmd)&&cmd.ticket==700&&cmd.volume==1,"L3: fechamento urgente permitido com cancelamento incerto");state=next;
 Check615L3(state.cancel_slot.phase==1&&state.close_slot.phase==1,"L3: fechamento nao apaga incerteza do cancelamento");
 string path="ModeloD_TEST_ONLY_615L3_"+suffix+"_duas_reservas.state";
 Check615L3(MDPairDisk615L3(path,state,key,domain,restored)&&MDPairEncode615L3(restored)==MDPairEncode615L3(state),"L3 DISCO: dois controles gravados e relidos juntos");
 Check615L3(!MDPairDisk615L3(path,state,key,domain,restored),"L3 DISCO: arquivo anterior nao sobrescrito");
 Check615L3(!Prepare615L3(restored,plan,3,true,next,cmd)&&!Prepare615L3(restored,plan,4,true,next,cmd),"L3: retomada nao repete nenhum dos comandos");
 Check615L3(!MDPairResolve615L3(state,4,state.close_slot.attempt,700,false,next),"L3: retorno sem efeito confirmado nao conclui fechamento");
 Check615L3(!MDPairResolve615L3(state,4,state.close_slot.attempt+1,700,true,next),"L3: resposta de tentativa diferente rejeitada");
 Check615L3(!MDPairResolve615L3(state,4,state.close_slot.attempt,701,true,next),"L3: resposta de outro ticket rejeitada");
 Check615L3(MDPairResolve615L3(state,4,state.close_slot.attempt,700,true,closed)&&closed.cancel_slot.phase==1,"L3: confirmar fechamento preserva cancelamento pendente");
 Check615L3(!MDPairResolve615L3(closed,4,closed.close_slot.attempt,700,true,next),"L3: confirmacao duplicada rejeitada");
 Check615L3(MDPairResolve615L3(closed,3,closed.cancel_slot.attempt,100,true,next)&&next.close_slot.phase==2,"L3: cancelamento pode ser confirmado depois do fechamento");
 string encoded=MDPairEncode615L3(state);
 Check615L3(!MDPairDecode615L3(encoded,key,domain,state.revision+1,0,restored),"L3: revisao antiga rejeitada");
 Check615L3(!MDPairDecode615L3(encoded,"OUTRO",domain,1,0,restored),"L3: identidade diferente rejeitada");
 Check615L3(!MDPairDecode615L3(encoded,key,"OUTRO_RELOGIO",1,0,restored),"L3: origem de relogio diferente rejeitada");
 Check615L3(!MDPairDecode615L3(encoded+"x",key,domain,1,0,restored),"L3: arquivo corrompido rejeitado");
 Check615L3(!MDPairDecode615L3(StringSubstr(encoded,0,StringLen(encoded)/2),key,domain,1,0,restored),"L3: arquivo parcial rejeitado");
 // Execucao adicional durante cancelamento exige nova conciliacao; reserva em voo nao e alterada.
 snap615C.o[0].order.state=2;snap615C.o[0].order.remaining=0;snap615C.d[0].volume=3;snap615C.p[0].volume=3;
 Check615L3(Recover615C(text,e,true,g,plan)&&plan.count==1&&plan.commands[0].volume==3,"L3: nova evidencia recalcula necessidade total de fechamento");
 Check615L3(!Prepare615L3(state,plan,4,true,next,cmd)&&state.close_slot.volume==1,"L3: novo volume nao duplica nem altera fechamento em voo");
 MDPairInit615L3(restored,key,domain,700);
 Check615L3(Prepare615L3(restored,plan,4,true,next,cmd)&&cmd.volume==3,"L3: sem chamada anterior reserva volume atual conciliado");
 plan.commands[0].ticket=701;
 Check615L3(!Prepare615L3(restored,plan,4,true,next,cmd),"L3: plano de outro ticket rejeitado");plan.commands[0].ticket=700;
 plan.journal+="corrompido";
 Check615L3(!Prepare615L3(restored,plan,4,true,next,cmd),"L3: plano com diario invalido rejeitado");
}
#endif
