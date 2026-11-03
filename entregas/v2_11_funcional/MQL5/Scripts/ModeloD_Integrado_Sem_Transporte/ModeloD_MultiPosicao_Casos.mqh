#ifndef MODELOD_MULTIPOSICAO_CASOS
#define MODELOD_MULTIPOSICAO_CASOS
#include "ModeloD_ManagementBridgeCasesB1.mqh"
#include "ModeloD_MultiPosicao_Bancada.mqh"
int checksMulti=0,failuresMulti=0;string logMulti="";
void CheckMulti(bool yes,string label){checksMulti++;if(!yes)failuresMulti++;logMulti+=(yes?"PASS: ":"FAIL: ")+label+"\r\n";}
void RunMulti(string suffix)
{
 RunB1(suffix);checksMulti=checksB1;failuresMulti=failuresB1;logMulti=logB1;
 string text,why;MDExecGate613 gate;MDRecoveryEvidence67 market;Partial615C(text,gate,market);
 MDJournal610 journal;MDReplay610(text,"TEST_ONLY_615C","WINZ26",20261016,1,journal);
 // Segunda execucao para identificador independente da mesma ordem.
 snap615C.o[0].order.remaining=1;snap615C.deals=2;snap615C.d[1]=snap615C.d[0];snap615C.d[1].ticket=102;snap615C.d[1].position=501;
 snap615C.positions=2;snap615C.p[1]=snap615C.p[0];snap615C.p[1].identifier=501;snap615C.p[1].ticket=701;
 MDOrigin68 origin;MDChainInput68 chain_input;MDChainResult68 result;long now=1792141256927;
 bool valid=MDOrigin611(journal,"TEST_ONLY_615C",0,snap615C,origin)&&MDBuild69(snap615C,origin,now,chain_input,why)&&MDReconcileChain68(chain_input,result);
 CheckMulti(valid&&result.open_positions==2,"duas posicoes comprovadas na mesma cadeia");if(!valid)return;
 MDMultiBench m;MDMultiResetBench(m);CheckMulti(!MDMultiReconcileBench(m,chain_input,false,false,why)&&m.count==0,"coleta antiga nao cria controles");
 CheckMulti(MDMultiReconcileBench(m,chain_input,true,false,why)&&m.count==2,"controle independente para cada identificador");
 int a=MDIndexBench(m,500),b=MDIndexBench(m,501);CheckMulti(a>=0&&b>=0&&a!=b,"identificadores distintos");if(a<0||b<0)return;
 CheckMulti(MDManagementBegin615L(m.slots[a].control,100,700,true),"primeira posicao inicia tentativa");
 CheckMulti(!m.slots[b].control.protection.inflight&&MDManagementBegin615L(m.slots[b].control,100,701,true),"segunda posicao inicia sem herdar tentativa da primeira");
 CheckMulti(MDManagementComplete615L(m.slots[a].control,200,700)&&m.slots[a].control.protection.initial_completed==1&&m.slots[b].control.protection.initial_completed==0&&m.slots[b].control.protection.inflight,"resultado de uma tentativa nao altera a outra");
 chain_input.positions[0].ticket=702;
 CheckMulti(!MDMultiReconcileBench(m,chain_input,true,true,why)&&m.slots[a].control.ticket==700,"troca com pendencia externa bloqueada sem alterar estado");
 CheckMulti(MDMultiReconcileBench(m,chain_input,true,false,why)&&m.slots[a].control.ticket==702&&m.slots[a].control.protection.initial_completed==1,"troca conciliada sem pendencia preserva tentativas");
 chain_input.positions[1].ticket=703;
 CheckMulti(!MDMultiReconcileBench(m,chain_input,true,false,why)&&m.slots[b].control.ticket==701,"troca com tentativa em voo bloqueada");
 chain_input.positions[1].ticket=701;
 CheckMulti(!MDManagementComplete615L(m.slots[a].control,200,700),"ticket antigo nao conclui tentativa");
 CheckMulti(MDManagementComplete615L(m.slots[b].control,200,701),"tentativa da segunda posicao conclui separadamente");
 chain_input.snapshot_complete=false;CheckMulti(!MDMultiReconcileBench(m,chain_input,true,false,why)&&m.count==2,"coleta incompleta nao altera controles");chain_input.snapshot_complete=true;
 chain_input.positions[1].ticket=702;CheckMulti(!MDMultiReconcileBench(m,chain_input,true,false,why),"ticket duplicado nao e adotado");chain_input.positions[1].ticket=701;
 chain_input.positions[1].volume=2;CheckMulti(!MDMultiReconcileBench(m,chain_input,true,false,why),"divergencia de volume bloqueia atualizacao");chain_input.positions[1].volume=1;
 CheckMulti(MDMultiReconcileBench(m,chain_input,true,false,why)&&m.slots[a].control.protection.initial_completed==1&&m.slots[b].control.protection.initial_completed==1,"reconciliacao repetida preserva contadores");
 chain_input.origin.accepted_msc--;CheckMulti(!MDMultiReconcileBench(m,chain_input,true,false,why),"outra origem nao adota controle existente");
}
#endif
