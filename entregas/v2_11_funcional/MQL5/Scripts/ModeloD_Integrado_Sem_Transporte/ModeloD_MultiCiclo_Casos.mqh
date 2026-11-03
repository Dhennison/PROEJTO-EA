#ifndef MODELOD_MULTI_CICLO_CASOS
#define MODELOD_MULTI_CICLO_CASOS
#include "ModeloD_MultiPersist_Casos.mqh"
#include "ModeloD_MultiCiclo_Bancada.mqh"
int checksCycle=0,failuresCycle=0;string logCycle="";
void CheckCycle(bool ok,string name){checksCycle++;if(!ok)failuresCycle++;logCycle+=(ok?"PASS: ":"FAIL: ")+name+"\r\n";}
void RunCycle(string suffix)
{
 RunPersist(suffix);checksCycle=checksPersist;failuresCycle=failuresPersist;logCycle=logPersist;
 string text,why;MDExecGate613 gate;MDRecoveryEvidence67 market;Partial615C(text,gate,market);
 MDJournal610 j;MDReplay610(text,"TEST_ONLY_615C","WINZ26",20261016,1,j);
 snap615C.o[0].order.remaining=1;snap615C.deals=2;snap615C.d[1]=snap615C.d[0];snap615C.d[1].ticket=102;snap615C.d[1].position=501;
 snap615C.positions=2;snap615C.p[1]=snap615C.p[0];snap615C.p[1].identifier=501;snap615C.p[1].ticket=701;
 MDOrigin68 origin;MDChainInput68 chain_input;MDMultiBench m,readback;MDMultiResetBench(m);long rev=0;
 bool setup=MDOrigin611(j,"TEST_ONLY_615C",0,snap615C,origin)&&MDBuild69(snap615C,origin,1792141256927,chain_input,why)&&MDMultiReconcileBench(m,chain_input,true,false,why);
 string base="ModeloD_TEST_ONLY_615L4_MULTI_CYCLE_"+suffix;MDMultiStoreBench store;
 setup=setup&&store.Open(base,"BENCH_123")&&store.Create(m,0);
 CheckCycle(setup,"ciclo: duas posicoes conciliadas e gravadas");if(!setup){store.Close();return;}
 CheckCycle(!MDMultiBeginDurableBench(store,1,100,chain_input,false,false,500,700,why),"ciclo: coleta antiga nao reserva tentativa");
 CheckCycle(!MDMultiBeginDurableBench(store,1,100,chain_input,true,false,500,999,why),"ciclo: ticket incorreto nao reserva tentativa");
 CheckCycle(MDMultiBeginDurableBench(store,1,100,chain_input,true,false,500,700,why),"ciclo: primeira tentativa reservada em disco");
 CheckCycle(!MDMultiBeginDurableBench(store,1,100,chain_input,true,false,501,701,why),"ciclo: revisao antiga nao reserva segunda posicao");
 CheckCycle(MDMultiBeginDurableBench(store,2,100,chain_input,true,false,501,701,why),"ciclo: segunda posicao reservada separadamente");
 store.Close();CheckCycle(store.Open(base,"BENCH_123")&&store.Load(3,100,readback,rev)&&readback.slots[MDIndexBench(readback,500)].control.protection.inflight&&readback.slots[MDIndexBench(readback,501)].control.protection.inflight,"ciclo: reabertura conserva duas chamadas em voo");
 CheckCycle(!MDMultiBeginDurableBench(store,3,100,chain_input,true,false,500,700,why),"ciclo: retomada nao duplica tentativa em voo");
 CheckCycle(!MDMultiCompleteDurableBench(store,3,200,500,700,100,false),"ciclo: resposta nao verificada bloqueada");
 CheckCycle(!MDMultiCompleteDurableBench(store,3,200,500,700,101,true),"ciclo: horario de outra tentativa rejeitado");
 CheckCycle(MDMultiCompleteDurableBench(store,3,200,500,700,100,true),"ciclo: primeira conclusao persistida");
 CheckCycle(!MDMultiCompleteDurableBench(store,4,200,500,700,100,true),"ciclo: mesma conclusao nao conta duas vezes");
 CheckCycle(store.Load(4,200,readback,rev)&&readback.slots[MDIndexBench(readback,500)].control.protection.initial_completed==1&&readback.slots[MDIndexBench(readback,501)].control.protection.inflight,"ciclo: estado da segunda posicao independente");
 CheckCycle(MDMultiCompleteDurableBench(store,4,200,501,701,100,true),"ciclo: segunda conclusao persistida");
 CheckCycle(!MDMultiBeginDurableBench(store,5,2099,chain_input,true,false,500,700,why),"ciclo: antes de dois segundos nao inicia nova chamada");
 CheckCycle(MDMultiBeginDurableBench(store,5,2100,chain_input,true,false,500,700,why),"ciclo: apos dois segundos grava nova chamada");
 store.Close();CheckCycle(store.Open(base,"BENCH_123")&&store.Load(6,2100,readback,rev)&&readback.slots[MDIndexBench(readback,500)].control.protection.inflight,"ciclo: segunda abertura preserva nova tentativa");store.Close();
}
#endif
