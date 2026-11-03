#ifndef MULTI_PERSIST_CASOS
#define MULTI_PERSIST_CASOS
#include "ModeloD_MultiPosicao_Casos.mqh"
#include "ModeloD_MultiPersist_Bancada.mqh"
int checksPersist=0,failuresPersist=0;string logPersist="";
void CheckPersist(bool ok,string name){checksPersist++;if(!ok)failuresPersist++;logPersist+=(ok?"PASS: ":"FAIL: ")+name+"\r\n";}
void RunPersist(string suffix)
{
 RunMulti(suffix);checksPersist=checksMulti;failuresPersist=failuresMulti;logPersist=logMulti;
 string accepted,why;MDExecGate613 gate;MDRecoveryEvidence67 market;Partial615C(accepted,gate,market);
 MDJournal610 j;MDReplay610(accepted,"TEST_ONLY_615C","WINZ26",20261016,1,j);
 snap615C.o[0].order.remaining=1;snap615C.deals=2;snap615C.d[1]=snap615C.d[0];snap615C.d[1].ticket=102;snap615C.d[1].position=501;
 snap615C.positions=2;snap615C.p[1]=snap615C.p[0];snap615C.p[1].identifier=501;snap615C.p[1].ticket=701;
 MDOrigin68 origin;MDChainInput68 chain_input;long now=1792141256927;
 bool valid=MDOrigin611(j,"TEST_ONLY_615C",0,snap615C,origin)&&MDBuild69(snap615C,origin,now,chain_input,why);
 MDMultiBench m,readback;MDMultiResetBench(m);
 bool initialized=valid&&MDMultiReconcileBench(m,chain_input,true,false,why);
 CheckPersist(initialized&&m.count==2,"persistencia: duas posicoes reconciliadas");if(!initialized)return;
 int a=MDIndexBench(m,500),b=MDIndexBench(m,501);
 CheckPersist(a>=0&&b>=0,"persistencia: identificadores independentes");if(a<0||b<0)return;
 CheckPersist(MDManagementBegin615L(m.slots[a].control,100,700,true)&&MDManagementComplete615L(m.slots[a].control,200,700),"persistencia: primeira tentativa concluida");
 CheckPersist(MDManagementBegin615L(m.slots[b].control,100,701,true),"persistencia: segunda tentativa permanece em voo");
 string encoded=MDMultiEncodeBench(m,1,"BENCH_123");long rev=0;
 CheckPersist(encoded!=""&&MDMultiDecodeBench(encoded,"BENCH_123",1,200,readback,rev)&&rev==1,"persistencia: codificacao e leitura completas");
 CheckPersist(!MDMultiDecodeBench(encoded+"X","BENCH_123",1,200,readback,rev),"persistencia: adulteracao rejeitada");
 CheckPersist(!MDMultiDecodeBench(StringSubstr(encoded,0,StringLen(encoded)/2),"BENCH_123",1,200,readback,rev),"persistencia: arquivo truncado rejeitado");
 CheckPersist(!MDMultiDecodeBench(encoded,"OUTRA_CONTA",1,200,readback,rev),"persistencia: escopo divergente rejeitado");
 CheckPersist(!MDMultiDecodeBench(encoded,"BENCH_123",2,200,readback,rev),"persistencia: revisao inferior recusada");
 CheckPersist(!MDMultiDecodeBench(encoded,"BENCH_123",1,199,readback,rev),"persistencia: relogio anterior bloqueado");
 string base="ModeloD_TEST_ONLY_615L4_MULTI_"+suffix;MDMultiStoreBench store,other;
 CheckPersist(store.Open(base,"BENCH_123")&&!other.Open(base,"BENCH_123"),"disco: trava exclusiva bloqueia segunda abertura");
 CheckPersist(store.Create(m,200)&&!store.Create(m,200),"disco: criacao nao sobrescreve estado existente");
 CheckPersist(store.Load(1,200,readback,rev)&&rev==1&&readback.slots[a].control.protection.initial_completed==1&&readback.slots[b].control.protection.inflight,"disco: ambas as posicoes relidas com estados diferentes");
 store.Close();CheckPersist(store.Open(base,"BENCH_123")&&store.Load(1,200,readback,rev),"disco: fechamento e reabertura recuperam estado");
 MDMultiBench probe=readback;CheckPersist(!MDManagementBegin615L(probe.slots[b].control,2200,701,true),"retomada: tentativa em voo nao e duplicada");
 MDMultiBench next=readback;
 CheckPersist(MDManagementComplete615L(next.slots[b].control,300,701)&&next.slots[b].control.protection.initial_completed==1,"retomada: apenas segunda posicao conclui");
 CheckPersist(store.Commit(readback,1,next,300),"disco: alteracao e nova revisao gravadas");
 CheckPersist(!store.Commit(readback,1,next,300),"disco: revisao antiga nao sobrescreve novo estado");
 CheckPersist(store.Load(2,300,readback,rev)&&rev==2&&readback.slots[a].control.protection.initial_completed==1&&readback.slots[b].control.protection.initial_completed==1,"disco: controles preservados apos gravacao");
 store.Close();CheckPersist(store.Open(base,"OUTRA_CONTA")&&!store.Load(1,300,readback,rev),"disco: outro escopo nao adota estado");store.Close();
 CheckPersist(store.Open(base,"BENCH_123")&&MDWriteStore615L4(base+".tmp","ESCRITA_INTERROMPIDA")&&!store.Load(1,300,readback,rev),"disco: temporario remanescente impede retomada silenciosa");store.Close();
}
#endif
