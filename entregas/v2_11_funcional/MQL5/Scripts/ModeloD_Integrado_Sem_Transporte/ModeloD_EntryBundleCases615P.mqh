#ifndef MD_ENTRY_BUNDLE_CASES615P
#define MD_ENTRY_BUNDLE_CASES615P
#include "ModeloD_ReservationCases615O.mqh"
#include "ModeloD_EntryBundle615P.mqh"
int checks615P=0,failures615P=0;string log615P="";
void Check615P(bool ok,string name){checks615P++;if(!ok)failures615P++;log615P+=(ok?"PASS: ":"FAIL: ")+name+"\r\n";}
void Run615P(string suffix)
{
 Run615O(suffix);checks615P=checks615O;failures615P=failures615O;log615P=log615O;
 string journal,restored;MDJournal610 j;MDSubmission615K request,receipt;MDExecGate613 gate;
 MDReadiness615M e;MDCommand613 command;MDDecision615M decision;MDEntryBundle615P store,other;
 bool ready=Prepared615K(0,journal,j,request);MDTestGate615C(gate);Evidence615M(e);
 gate.intent_durable=false;e.state_durable=false;
 string base="ModeloD_TEST_ONLY_615L4_P_"+suffix;
 Check615P(ready&&store.Open(base,j,0,123,"SINTETICO"),"P: conjunto abre com pedido esperado");
 Check615P(!other.Open(base,j,0,123,"SINTETICO"),"P: segundo escritor bloqueado");
 e.clock_certified=false;
 Check615P(!store.Prepare(journal,gate,e,command,decision)&&!command.valid&&!FileIsExist(base+".head",FILE_COMMON)&&!FileIsExist(base+".tmp",FILE_COMMON),"P: falha de prontidao nao publica nenhum componente");
 e.clock_certified=true;e.touches_complete=false;
 Check615P(!store.Prepare(journal,gate,e,command,decision),"P: historico incompleto continua bloqueado");e.touches_complete=true;
 e.account=999;Check615P(!store.Prepare(journal,gate,e,command,decision),"P: conta divergente nao publica");e.account=123;
 Check615P(!store.Prepare(journal+"CORROMPIDO",gate,e,command,decision),"P: diario invalido nao publica");
 Check615P(store.Prepare(journal,gate,e,command,decision)&&command.valid&&decision.plan_allowed&&!decision.transport_allowed,"P: diario e reserva publicados antes de expor plano");
 Check615P(!gate.intent_durable&&!e.state_durable,"P: entradas do chamador nao viram atestados por mutacao");
 Check615P(FileIsExist(base+".head",FILE_COMMON)&&!FileIsExist(base+".tmp",FILE_COMMON),"P: publicacao completa sem temporario residual");
 Check615P(store.Restore(restored,receipt)&&restored==journal&&receipt.key==request.key&&receipt.phase==2,"P: releitura recupera diario exato e tentativa incerta juntos");
 Check615P(command.price==j.r[0].entry&&command.sl==j.r[0].sl&&command.tp==j.r[0].tp,"P: precos aprovados preservados");
 Check615P(!store.Prepare(journal,gate,e,command,decision)&&!command.valid,"P: conjunto existente impede segunda preparacao");
 store.Close();Check615P(store.Open(base,j,0,123,"SINTETICO")&&store.Restore(restored,receipt),"P: reabertura real recupera ambos componentes");
 Check615P(!store.Prepare(journal,gate,e,command,decision)&&!MDRetry615K(receipt,true,true,true),"P: reabertura nao autoriza reenvio");store.Close();
 Check615P(other.Open(base,j,0,999,"SINTETICO")&&!other.Restore(restored,receipt),"P: conta errada rejeita conjunto");other.Close();
 Check615P(other.Open(base,j,0,123,"OUTRO")&&!other.Restore(restored,receipt),"P: servidor errado rejeita conjunto");other.Close();
 string temp=base+"_TMP";MDWriteStore615L4(temp+".tmp","GRAVACAO_INTERROMPIDA");store.Open(temp,j,0,123,"SINTETICO");
 Check615P(!store.Restore(restored,receipt)&&!store.Prepare(journal,gate,e,command,decision)&&!command.valid,"P: temporario isolado bloqueia retomada e preparacao");store.Close();
 string corrupt=base+"_BAD";MDWriteStore615L4(corrupt+".head","TRUNCADO");store.Open(corrupt,j,0,123,"SINTETICO");
 Check615P(!store.Restore(restored,receipt)&&!store.Prepare(journal,gate,e,command,decision),"P: head corrompido nao e sobrescrito");store.Close();
 string existing;MDReadStore615L4(base+".head",existing);MDWriteStore615L4(base+".tmp","RESIDUO");store.Open(base,j,0,123,"SINTETICO");
 Check615P(!store.Restore(restored,receipt),"P: head valido com temporario residual tambem bloqueia");store.Close();
 string damaged=base+"_HASH";MDWriteStore615L4(damaged+".head",existing+"9");store.Open(damaged,j,0,123,"SINTETICO");
 Check615P(!store.Restore(restored,receipt),"P: checksum adulterado rejeitado");store.Close();
 Check615P(!store.Open("ESTADO_REAL",j,0,123,"SINTETICO"),"P: caminho fora de bancada rejeitado");
 for(int level=1;level<5;level++)
 {
  Prepared615K(level,journal,j,request);MDTestGate615C(gate);Evidence615M(e);gate.intent_durable=false;e.state_durable=false;
  string slot=base+"_L"+IntegerToString(level);
  bool ok=store.Open(slot,j,level,123,"SINTETICO")&&store.Prepare(journal,gate,e,command,decision)&&store.Restore(restored,receipt);
  Check615P(ok&&restored==journal&&receipt.key==request.key&&command.level==level&&command.buy==(level<3),"P: diario reserva e lado conferidos no nivel "+IntegerToString(level));store.Close();
 }
}
#endif
