#ifndef MD_CONFIRM_CASES615L6
#define MD_CONFIRM_CASES615L6
#include "ModeloD_ClockRecoveryCases615L5.mqh"
#include "ModeloD_ConfirmResidual615L6.mqh"
int checks615L6=0,failures615L6=0;string log615L6="";
void Check615L6(bool ok,string name){checks615L6++;if(!ok)failures615L6++;log615L6+=(ok?"PASS: ":"FAIL: ")+name+"\r\n";}
bool Fixture615L6(MDPair615L3 &state,MDBinding615L6 &binding,string &journal)
{
 string text;MDExecGate613 g;MDRecoveryEvidence67 e;MDPlan615C plan;MDJournal610 j;MDCommand613 cmd;MDPair615L3 next;
 if(!Partial615C(text,g,e))return false;
 snap615C.o[0].order.state=2;snap615C.o[0].order.remaining=0;snap615C.d[0].volume=3;snap615C.p[0].volume=3;
 if(!Recover615C(text,e,true,g,plan)||!MDReplay610(plan.journal,"TEST_ONLY_615C","WINZ26",20261016,1,j))return false;
 journal=plan.journal;MDPairInit615L3(state,MDPairKey615L3(j,0,700),"L6_LOGICAL",700);
 if(!Prepare615L3(state,plan,4,true,next,cmd))return false;
 state=next;
 binding.verified=true;binding.attempt=state.close_slot.attempt;binding.order=200;binding.position=500;binding.requested_msc=snap615C.d[0].msc+100;
 snap615C.orders=2;snap615C.o[1]=snap615C.o[0];snap615C.o[1].entry_limit=false;snap615C.o[1].setup_msc=binding.requested_msc;
 snap615C.o[1].order.ticket=200;snap615C.o[1].order.buy=false;snap615C.o[1].order.state=1;snap615C.o[1].order.remaining=2;
 snap615C.deals=2;snap615C.d[1]=snap615C.d[0];snap615C.d[1].ticket=102;snap615C.d[1].order=200;snap615C.d[1].buy=false;snap615C.d[1].entry=1;snap615C.d[1].volume=1;snap615C.d[1].msc=binding.requested_msc+1;
 snap615C.p[0].volume=2;return true;
}
bool Confirm615L6(const MDPair615L3 &state,const MDBinding615L6 &b,string journal,bool fresh,bool reserve,MDPair615L3 &next,double &residual)
{return MDConfirmClose615L6(state,b,journal,"TEST_ONLY_615C","WINZ26",20261016,1,0,snap615C,123,"SINTETICO",1792141256927,fresh,reserve,next,residual);}
void Run615L6(string suffix)
{
 Run615L5(suffix);checks615L6=checks615L5;failures615L6=failures615L5;log615L6=log615L5;
 MDPair615L3 state,next,restored;MDBinding615L6 b;string journal;double residual=0;
 Check615L6(Fixture615L6(state,b,journal),"L6: fixture vem do diario e plano integrado");
 string original=MDPairEncode615L3(state);
 Check615L6(Confirm615L6(state,b,journal,true,false,next,residual)&&residual==2&&next.close_slot.phase==2,"L6: fechamento parcial terminal confirmado por ordem e deals");
 Check615L6(MDPairEncode615L3(state)==original,"L6: confirmacao produz candidato sem alterar estado de entrada");
 Check615L6(Confirm615L6(state,b,journal,true,true,next,residual)&&residual==2&&next.close_slot.phase==1&&next.close_slot.volume==2&&next.close_slot.attempt==state.close_slot.attempt+1&&next.revision==state.revision+1&&MDPairValid615L3(next),"L6: nova reserva contem somente volume residual");
 state=next;
 Check615L6(!Confirm615L6(state,b,journal,true,true,next,residual),"L6: prova da tentativa anterior nao libera novo envio");
 // Persistir e reabrir o candidato antes de qualquer futuro transporte.
 MDJournal610 j;MDReplay610(journal,"TEST_ONLY_615C","WINZ26",20261016,1,j);string key=MDPairKey615L3(j,0,700);
 string path="ModeloD_TEST_ONLY_615L3_L6_"+suffix+".state";
 Check615L6(MDPairDisk615L3(path,state,key,"L6_LOGICAL",restored)&&restored.close_slot.volume==2&&restored.close_slot.phase==1,"L6 DISCO: reserva residual preservada apos releitura");
 Check615L6(!Confirm615L6(restored,b,journal,true,true,next,residual),"L6 DISCO: releitura nao aceita confirmacao antiga");
 // Segunda tentativa encerra o saldo de dois contratos apos releitura.
 state=restored;b.attempt=state.close_slot.attempt;b.order=201;b.requested_msc+=10;
 snap615C.orders=3;snap615C.o[2]=snap615C.o[1];snap615C.o[2].order.ticket=201;
 snap615C.o[2].order.initial_volume=2;snap615C.o[2].order.remaining=0;snap615C.o[2].order.state=2;snap615C.o[2].setup_msc=b.requested_msc;
 snap615C.deals=3;snap615C.d[2]=snap615C.d[1];snap615C.d[2].ticket=103;snap615C.d[2].order=201;snap615C.d[2].volume=2;snap615C.d[2].msc=b.requested_msc+1;snap615C.positions=0;
 Check615L6(Confirm615L6(state,b,journal,true,true,next,residual)&&residual==0&&next.close_slot.phase==2,"L6: segunda tentativa confirmada encerra residual apos retomada");
 state=next;Check615L6(!Confirm615L6(state,b,journal,true,true,next,residual),"L6: segunda confirmacao nao pode ser reutilizada");
 Fixture615L6(state,b,journal);snap615C.o[1].order.state=2;snap615C.o[1].order.remaining=0;snap615C.d[1].volume=3;snap615C.positions=0;
 Check615L6(Confirm615L6(state,b,journal,true,true,next,residual)&&residual==0&&next.close_slot.phase==2&&next.close_slot.attempt==state.close_slot.attempt,"L6: fechamento total nao reserva volume zero");
 state=next;Check615L6(!Confirm615L6(state,b,journal,true,true,next,residual),"L6: confirmacao total duplicada rejeitada");
 Fixture615L6(state,b,journal);b.verified=false;Check615L6(!Confirm615L6(state,b,journal,true,true,next,residual),"L6: vinculo nao comprovado bloqueia confirmacao");
 Fixture615L6(state,b,journal);b.attempt++;Check615L6(!Confirm615L6(state,b,journal,true,true,next,residual),"L6: tentativa diferente bloqueia confirmacao");
 Fixture615L6(state,b,journal);b.order=999;Check615L6(!Confirm615L6(state,b,journal,true,true,next,residual),"L6: ordem ausente bloqueia confirmacao");
 Fixture615L6(state,b,journal);b.position=999;Check615L6(!Confirm615L6(state,b,journal,true,true,next,residual),"L6: identifier diferente bloqueia confirmacao");
 Fixture615L6(state,b,journal);snap615C.account_key=999;Check615L6(!Confirm615L6(state,b,journal,true,true,next,residual),"L6: conta diferente bloqueia confirmacao");
 Fixture615L6(state,b,journal);snap615C.server_key="OUTRO";Check615L6(!Confirm615L6(state,b,journal,true,true,next,residual),"L6: servidor diferente bloqueia confirmacao");
 Fixture615L6(state,b,journal);snap615C.complete=false;Check615L6(!Confirm615L6(state,b,journal,true,true,next,residual),"L6: coleta incompleta bloqueia confirmacao");
 Fixture615L6(state,b,journal);snap615C.connected=false;Check615L6(!Confirm615L6(state,b,journal,true,true,next,residual),"L6: desconexao bloqueia confirmacao");
 Fixture615L6(state,b,journal);snap615C.hedge=false;Check615L6(!Confirm615L6(state,b,journal,true,true,next,residual),"L6: modo de conta divergente bloqueia confirmacao");
 Fixture615L6(state,b,journal);snap615C.o[1].order.state=0;Check615L6(!Confirm615L6(state,b,journal,true,true,next,residual),"L6: parcial ainda ativa bloqueia confirmacao");
 Fixture615L6(state,b,journal);snap615C.o[1].order.state=3;Check615L6(!Confirm615L6(state,b,journal,true,true,next,residual),"L6: rejeicao nao classificada bloqueia confirmacao");
 Fixture615L6(state,b,journal);snap615C.o[1].order.magic++;Check615L6(!Confirm615L6(state,b,journal,true,true,next,residual),"L6: Magic diferente bloqueia confirmacao");
 Fixture615L6(state,b,journal);snap615C.o[1].order.buy=true;Check615L6(!Confirm615L6(state,b,journal,true,true,next,residual),"L6: lado de fechamento errado bloqueia confirmacao");
 Fixture615L6(state,b,journal);snap615C.o[1].order.initial_volume=4;Check615L6(!Confirm615L6(state,b,journal,true,true,next,residual),"L6: volume solicitado divergente bloqueia confirmacao");
 Fixture615L6(state,b,journal);snap615C.o[1].order.remaining=1;Check615L6(!Confirm615L6(state,b,journal,true,true,next,residual),"L6: saldo da ordem incompativel com deals bloqueia confirmacao");
 Fixture615L6(state,b,journal);snap615C.o[1].entry_limit=true;Check615L6(!Confirm615L6(state,b,journal,true,true,next,residual),"L6: ordem marcada como entrada bloqueia confirmacao");
 Fixture615L6(state,b,journal);snap615C.o[1].setup_msc=b.requested_msc-1;Check615L6(!Confirm615L6(state,b,journal,true,true,next,residual),"L6: ordem anterior ao pedido bloqueia confirmacao");
 Fixture615L6(state,b,journal);snap615C.o[1].setup_msc=b.requested_msc+2;Check615L6(!Confirm615L6(state,b,journal,true,true,next,residual),"L6: deal anterior a criacao da ordem bloqueia confirmacao");
 Fixture615L6(state,b,journal);snap615C.deals=1;Check615L6(!Confirm615L6(state,b,journal,true,true,next,residual),"L6: ausencia de deal nao confirma bloqueia confirmacao");
 Fixture615L6(state,b,journal);snap615C.p[0].volume=1;Check615L6(!Confirm615L6(state,b,journal,true,true,next,residual),"L6: saldo da posicao divergente bloqueia confirmacao");
 Fixture615L6(state,b,journal);snap615C.p[0].ticket=701;Check615L6(!Confirm615L6(state,b,journal,true,true,next,residual),"L6: ticket atual diferente bloqueia confirmacao");
 Fixture615L6(state,b,journal);snap615C.d[1].msc=b.requested_msc-1;Check615L6(!Confirm615L6(state,b,journal,true,true,next,residual),"L6: deal anterior ao pedido bloqueia confirmacao");
 Fixture615L6(state,b,journal);snap615C.d[1].entry=3;Check615L6(!Confirm615L6(state,b,journal,true,true,next,residual),"L6: OUT_BY fora do escopo bloqueia confirmacao");
 Fixture615L6(state,b,journal);snap615C.deals=3;snap615C.d[2]=snap615C.d[1];snap615C.d[2].volume=2;Check615L6(!Confirm615L6(state,b,journal,true,true,next,residual),"L6: duplicata conflitante bloqueia confirmacao");
 Fixture615L6(state,b,journal);journal+="corrompido";Check615L6(!Confirm615L6(state,b,journal,true,true,next,residual),"L6: diario adulterado bloqueia confirmacao");
 Fixture615L6(state,b,journal);Check615L6(!Confirm615L6(state,b,journal,false,true,next,residual),"L6: leitura antiga rejeitada");
 Fixture615L6(state,b,journal);snap615C.deals=3;snap615C.d[2]=snap615C.d[1];
 Check615L6(Confirm615L6(state,b,journal,true,true,next,residual)&&residual==2,"L6: deal identico repetido nao duplica volume fechado");
}
#endif
