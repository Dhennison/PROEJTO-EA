#ifndef MD_B1_CASES
#define MD_B1_CASES
#include "ModeloD_ReconcileCases615R.mqh"
#include "ModeloD_ManagementBridgeB1.mqh"
int checksB1=0,failuresB1=0;string logB1="";
void CheckB1(bool ok,string name){checksB1++;if(!ok)failuresB1++;logB1+=(ok?"PASS: ":"FAIL: ")+name+"\r\n";}
string ManifestB1(){return "ModeloD_TEST_ONLY_615L4_B1_RESTART.txt";}
bool SetupB1(string suffix,MDResponseStore615Q &q,MDStore615L7 &store,MDJournal610 &j,MDExecGate613 &gate,MDRecoveryEvidence67 &market)
{
 string text,accepted;MDSubmission615K request;Prepared615K(0,text,j,request);Partial615C(accepted,gate,market);
 MDReadiness615M e;Evidence615M(e);MDCommand613 c;MDDecision615M decision;MDEntryBundle615P p;
 bool ok=p.Open("ModeloD_TEST_ONLY_615L4_P_B1_"+suffix,j,0,123,"SINTETICO")&&p.Prepare(text,gate,e,c,decision)&&
 q.Open("ModeloD_TEST_ONLY_615L4_Q_B1_"+suffix,j,0,123,"SINTETICO")&&q.Import(p)&&q.Response(1,1,true,10008,0,100)&&
 q.Bind(2,snap615C.o[0],(double)j.r[0].entry,snap615C.o[0].setup_msc+1,true,true,123,"SINTETICO");p.Close();
 MDPair615L3 pair;MDClock615L5 clock;MDPairInit615L3(pair,MDPairKey615L3(j,0,700),"B1_LOGICAL",700);
 ClockFixture615L5(clock);clock.domain="B1_RAW";clock.raw=0;clock.lo=0;clock.hi=0;clock.utc_trusted=false;
 return ok&&store.Open("ModeloD_TEST_ONLY_615L4_L7_B1_"+suffix,MDPairKey615L3(j,0,700),"B1_LOGICAL",123,"SINTETICO")&&store.Create(pair,clock);
}
bool BeginB1(MDResponseStore615Q &q,MDStore615L7 &store,MDExecGate613 &gate,MDRecoveryEvidence67 &market,long raw,int action,bool cutoff, bool sl, bool tp,MDCommand613 &c)
{string reason;return MDBeginManagedB1(q,store,0,snap615C,123,"SINTETICO",1792141256927,"B1_RAW",raw,market,cutoff,sl,tp,gate,action,c,reason);}
void RunB1(string suffix)
{
 Run615R(suffix);checksB1=checks615R;failuresB1=failures615R;logB1=log615R;
 MDResponseStore615Q q;MDStore615L7 store;MDJournal610 j;MDExecGate613 gate;MDRecoveryEvidence67 market;MDCommand613 c;
 MDPair615L3 pair;MDClock615L5 clock;MDResponseState615Q qs;
 bool setup=SetupB1(suffix+"_schedule",q,store,j,gate,market);CheckB1(setup,"B1: diario vinculado e controlador duravel criados");
 if(!setup){q.Close();store.Close();return;}
 gate.snapshot_fresh=false;CheckB1(!BeginB1(q,store,gate,market,0,2,false,false,false,c)&&!c.valid,"B1: snapshot antigo nao reserva tentativa");gate.snapshot_fresh=true;
 snap615C.p[0].ticket=701;CheckB1(!BeginB1(q,store,gate,market,0,2,false,false,false,c),"B1: troca de ticket bloqueada explicitamente");snap615C.p[0].ticket=700;
 // Duas posicoes conciliaveis: o controlador deste pacote nao e multiposicao.
 snap615C.o[0].order.remaining=1;snap615C.deals=2;snap615C.d[1]=snap615C.d[0];snap615C.d[1].ticket=102;snap615C.d[1].position=501;
 snap615C.positions=2;snap615C.p[1]=snap615C.p[0];snap615C.p[1].identifier=501;snap615C.p[1].ticket=701;
 CheckB1(!BeginB1(q,store,gate,market,0,2,false,false,false,c),"B1: multiplas posicoes nao reinicializam controlador silenciosamente");
 string accepted;Partial615C(accepted,gate,market);
 for(int i=0;i<6;i++)
 {
  long start=i*2000;
  CheckB1(BeginB1(q,store,gate,market,start,2,false,false,false,c)&&c.valid&&c.action==2&&c.ticket==700&&c.sl==j.r[0].sl&&c.tp==j.r[0].tp,"B1: inicio duravel da protecao "+IntegerToString(i+1));
  CheckB1(!BeginB1(q,store,gate,market,start,2,false,false,false,c)&&!c.valid,"B1: tentativa em voo nao duplicada");
  CheckB1(!MDCompleteProtectionB1(store,start,"B1_RAW",start+100,false),"B1: conclusao sem evidencia rejeitada");
  CheckB1(MDCompleteProtectionB1(store,start,"B1_RAW",start+100,true),"B1: conclusao conhecida persistida");
  CheckB1(!MDCompleteProtectionB1(store,start,"B1_RAW",start+100,true),"B1: mesma conclusao nao contada duas vezes");
  if(i<5)CheckB1(!BeginB1(q,store,gate,market,start+1999,2,false,false,false,c),"B1: intervalo inferior a dois segundos bloqueado");
 }
 CheckB1(store.Load(pair,clock)&&pair.close_slot.management.protection.initial_completed==6&&pair.close_slot.management.protection.sixth_completed_ms==10100,"B1: prazo inicia na conclusao da sexta tentativa");
 CheckB1(!BeginB1(q,store,gate,market,19999,2,false,false,false,c),"B1: repeticao apos sexta exige dez segundos");
 CheckB1(BeginB1(q,store,gate,market,20000,2,false,false,false,c)&&MDCompleteProtectionB1(store,20000,"B1_RAW",20100,true),"B1: repeticao apos dez segundos preserva contador inicial");
 CheckB1(!BeginB1(q,store,gate,market,190099,4,false,false,false,c),"B1: um milissegundo antes do prazo nao reserva fechamento");
 CheckB1(!BeginB1(q,store,gate,market,190100,4,false,true,false,c),"B1: SL presente impede fechamento somente por falta de TP");
 CheckB1(BeginB1(q,store,gate,market,190100,4,false,false,false,c)&&c.ticket==700&&c.volume==1,"B1: prazo sem SL persiste intencao e reserva fechamento");
 CheckB1(q.JournalB1(j)&&j.r[0].close&&store.Load(pair,clock)&&pair.close_slot.phase==1,"B1: diario e reserva confirmados antes do comando");
 CheckB1(!BeginB1(q,store,gate,market,190100,4,false,false,false,c),"B1: fechamento pendente nao e reservado novamente");
 q.Close();store.Close();
 // Confirmacao vinculada de fechamento parcial, sem inferir execucao por resposta.
 setup=SetupB1(suffix+"_partial",q,store,j,gate,market);CheckB1(setup,"B1: fixture de preenchimento integral criada");
 if(!setup){q.Close();store.Close();return;}
 snap615C.o[0].order.state=2;snap615C.o[0].order.remaining=0;snap615C.d[0].volume=3;snap615C.p[0].volume=3;
 CheckB1(BeginB1(q,store,gate,market,0,4,true,false,false,c)&&c.volume==3,"B1: reserva de fechamento dos tres contratos");
 MDBinding615L6 binding;binding.verified=true;binding.attempt=1;binding.order=200;binding.position=500;binding.requested_msc=snap615C.d[0].msc+100;
 snap615C.orders=2;snap615C.o[1]=snap615C.o[0];snap615C.o[1].order.ticket=200;snap615C.o[1].order.buy=false;snap615C.o[1].entry_limit=false;
 snap615C.o[1].order.state=1;snap615C.o[1].order.initial_volume=3;snap615C.o[1].order.remaining=2;snap615C.o[1].setup_msc=binding.requested_msc;
 snap615C.deals=2;snap615C.d[1]=snap615C.d[0];snap615C.d[1].ticket=102;snap615C.d[1].order=200;snap615C.d[1].buy=false;snap615C.d[1].entry=1;snap615C.d[1].volume=1;snap615C.d[1].msc=binding.requested_msc+1;snap615C.p[0].volume=2;
 double residual=0;binding.verified=false;
 CheckB1(!MDConfirmCloseB1(q,store,0,binding,snap615C,123,"SINTETICO",1792141256927,true,"B1_RAW",10,residual),"B1: vinculacao nao verificada nao confirma fechamento");binding.verified=true;
 CheckB1(MDConfirmCloseB1(q,store,0,binding,snap615C,123,"SINTETICO",1792141256927,true,"B1_RAW",10,residual)&&residual==2,"B1: ordem e deal vinculados confirmam parcial e reservam residual");
 CheckB1(store.Load(pair,clock)&&pair.close_slot.phase==1&&pair.close_slot.attempt==2&&pair.close_slot.volume==2,"B1: residual conserva tentativa e volume em disco");
 CheckB1(!MDConfirmCloseB1(q,store,0,binding,snap615C,123,"SINTETICO",1792141256927,true,"B1_RAW",10,residual),"B1: confirmacao anterior nao consome tentativa residual");
 q.Close();store.Close();
 // Corte pode reservar cancelamento e fechamento mesmo com protecao em voo.
 setup=SetupB1(suffix+"_restart",q,store,j,gate,market);CheckB1(setup,"B1: fixture independente de corte criada");
 if(!setup){q.Close();store.Close();return;}
 CheckB1(BeginB1(q,store,gate,market,0,2,false,false,false,c),"B1: protecao em voo antes do corte");
 CheckB1(BeginB1(q,store,gate,market,10,3,true,false,false,c)&&c.ticket==100,"B1: corte reserva cancelamento do saldo");
 CheckB1(BeginB1(q,store,gate,market,10,4,true,false,false,c)&&c.ticket==700,"B1: fechamento urgente independente da protecao em voo");
 CheckB1(!MDConfirmCancelB1(q,store,0,snap615C,123,"SINTETICO",1792141256927,true,"B1_RAW",10),"B1: ordem ainda ativa nao confirma cancelamento");
 CheckB1(store.Load(pair,clock)&&pair.cancel_slot.phase==1&&pair.close_slot.phase==1&&pair.close_slot.management.protection.inflight,"B1: tres estados pendentes preservados juntos");
 q.Close();store.Close();
 if(failuresB1==0)CheckB1(MDWriteStore615L4(ManifestB1(),suffix+"_restart"),"B1: referencia para segunda execucao gravada");
}
#endif
