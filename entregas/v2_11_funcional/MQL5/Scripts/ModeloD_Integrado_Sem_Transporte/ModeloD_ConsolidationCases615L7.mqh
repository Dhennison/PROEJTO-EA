#ifndef MD_CONSOLIDATION_CASES615L7
#define MD_CONSOLIDATION_CASES615L7
#include "ModeloD_ConfirmResidualCases615L6.mqh"
#include "ModeloD_ConsolidatedStore615L7.mqh"
int checks615L7=0,failures615L7=0;string log615L7="";
void Check615L7(bool ok,string name){checks615L7++;if(!ok)failures615L7++;log615L7+=(ok?"PASS: ":"FAIL: ")+name+"\r\n";}
bool ConfirmPersist615L7(MDStore615L7 &store,const MDPair615L3 &pair,const MDClock615L5 &clock,const MDBinding615L6 &b,string journal,long raw,
 MDPair615L3 &out,MDClock615L5 &outclock,double &residual)
{return MDConfirmPersist615L7(store,pair,clock,b,journal,"TEST_ONLY_615C","WINZ26",20261016,1,0,snap615C,123,"SINTETICO",1792141256927,"RAW_A",raw,true,out,outclock,residual);}
void Run615L7(string suffix)
{
 Run615L6(suffix);checks615L7=checks615L6;failures615L7=failures615L6;log615L7=log615L6;
 MDPair615L3 initial,reserved,loaded,candidate,oldpair;MDClock615L5 clock,readclock,nextclock,oldclock;
 MDBinding615L6 binding;string journal;double residual=0;MDJournal610 j;
 Check615L7(Fixture615L6(reserved,binding,journal),"L7: diario e fechamento reservado integrados");
 MDReplay610(journal,"TEST_ONLY_615C","WINZ26",20261016,1,j);string key=MDPairKey615L3(j,0,700);
 MDPairInit615L3(initial,key,"L6_LOGICAL",700);ClockFixture615L5(clock);
 string base="ModeloD_TEST_ONLY_615L4_L7_"+suffix;MDStore615L7 store,other;
 Check615L7(!store.Load(loaded,readclock)&&!store.Create(initial,clock),"L7: acesso sem lock recusado");
 Check615L7(store.Open(base,key,"L6_LOGICAL",123,"SINTETICO"),"L7 DISCO: lock exclusivo adquirido");
 Check615L7(!other.Open(base,key,"L6_LOGICAL",123,"SINTETICO"),"L7 DISCO: segunda abertura bloqueada");
 Check615L7(store.Create(initial,clock),"L7 DISCO: estado e mapa temporal criados no mesmo envelope");
 Check615L7(!store.Create(initial,clock),"L7: criacao nao sobrescreve ancora existente");
 Check615L7(store.Load(loaded,readclock)&&MDEnvelope615L7(loaded,readclock,123,"SINTETICO")==MDEnvelope615L7(initial,clock,123,"SINTETICO"),"L7 DISCO: conteudo integral relido");
 Check615L7(store.Commit(initial,clock,reserved,clock),"L7 DISCO: reserva inicial publicada sob lock");
 oldclock=clock;oldclock.raw++;
 Check615L7(!store.Commit(reserved,oldclock,reserved,clock),"L7: revisao sem avanco rejeitada");
 candidate=reserved;candidate.revision++;
 Check615L7(!store.Commit(reserved,oldclock,candidate,clock),"L7: mapa temporal esperado divergente rejeitado");
 Check615L7(!ConfirmPersist615L7(store,reserved,clock,binding,journal,clock.raw-1,candidate,nextclock,residual),"L7: contador regressivo nao confirma fechamento");
 store.Close();candidate=reserved;nextclock=clock;
 Check615L7(!ConfirmPersist615L7(store,reserved,clock,binding,journal,clock.raw+100,candidate,nextclock,residual)&&MDPairEncode615L3(candidate)==MDPairEncode615L3(reserved)&&MDClockEncode615L5(nextclock)==MDClockEncode615L5(clock)&&residual==0,"L7: falha de persistencia nao entrega novo estado ao chamador");
 Check615L7(store.Open(base,key,"L6_LOGICAL",123,"SINTETICO")&&store.Load(loaded,readclock)&&MDPairEncode615L3(loaded)==MDPairEncode615L3(reserved),"L7 DISCO: tentativa nao publicada preserva estado anterior");
 Check615L7(ConfirmPersist615L7(store,reserved,clock,binding,journal,clock.raw+100,candidate,nextclock,residual)&&residual==2&&candidate.close_slot.phase==1&&candidate.close_slot.volume==2,"L7 DISCO: parcial confirma e publica reserva residual");
 oldpair=reserved;oldclock=clock;reserved=candidate;clock=nextclock;
 Check615L7(!ConfirmPersist615L7(store,oldpair,oldclock,binding,journal,oldclock.raw+100,candidate,nextclock,residual),"L7: mesmo evento com estado anterior nao republica");
 store.Close();
 Check615L7(store.Open(base,key,"L6_LOGICAL",123,"SINTETICO")&&store.Load(loaded,readclock)&&MDEnvelope615L7(loaded,readclock,123,"SINTETICO")==MDEnvelope615L7(reserved,clock,123,"SINTETICO"),"L7 DISCO: reabertura preserva residual e tempo juntos");
 Check615L7(!ConfirmPersist615L7(store,loaded,readclock,binding,journal,readclock.raw,candidate,nextclock,residual),"L7: retomada rejeita vinculacao da tentativa anterior");
 Check615L7(!MDRebasePersist615L7(store,loaded,readclock,"RAW_B",10,1200000,1200000,false,candidate,nextclock),"L7: origem nova sem evidencia temporal bloqueada");
 Check615L7(!MDRebasePersist615L7(store,loaded,readclock,"RAW_B",10,1200000,1200000,true,candidate,nextclock),"L7: ancora UTC antiga nao certificada bloqueia ponte");
 // Nova tentativa simulada termina o saldo; nao ha envio de ordem.
 binding.attempt=loaded.close_slot.attempt;binding.order=201;binding.requested_msc+=10;
 snap615C.orders=3;snap615C.o[2]=snap615C.o[1];snap615C.o[2].order.ticket=201;snap615C.o[2].order.initial_volume=2;
 snap615C.o[2].order.remaining=0;snap615C.o[2].order.state=2;snap615C.o[2].setup_msc=binding.requested_msc;
 snap615C.deals=3;snap615C.d[2]=snap615C.d[1];snap615C.d[2].ticket=103;snap615C.d[2].order=201;snap615C.d[2].volume=2;snap615C.d[2].msc=binding.requested_msc+1;snap615C.positions=0;
 Check615L7(ConfirmPersist615L7(store,loaded,readclock,binding,journal,readclock.raw+10,candidate,nextclock,residual)&&residual==0&&candidate.close_slot.phase==2,"L7 DISCO: fechamento do residual publicado sem nova reserva");
 Check615L7(store.Load(loaded,readclock)&&loaded.close_slot.phase==2&&readclock.raw==clock.raw+10,"L7 DISCO: estado final e tempo conferidos");
 string good=MDEnvelope615L7(loaded,readclock,123,"SINTETICO");store.Close();
 Check615L7(store.Open(base,key,"L6_LOGICAL",999,"SINTETICO")&&!store.Load(candidate,nextclock),"L7: outra conta nao adota arquivo existente");store.Close();
 Check615L7(store.Open(base,key,"L6_LOGICAL",123,"OUTRO")&&!store.Load(candidate,nextclock),"L7: outro servidor nao adota arquivo existente");store.Close();
 Check615L7(store.Open(base,"OUTRO","L6_LOGICAL",123,"SINTETICO")&&!store.Load(candidate,nextclock),"L7: outra identidade nao adota arquivo existente");store.Close();
 Check615L7(!MDEnvelopeRead615L7(good+"x",key,"L6_LOGICAL",123,"SINTETICO",candidate,nextclock),"L7: envelope adulterado rejeitado");
 Check615L7(!MDEnvelopeRead615L7(StringSubstr(good,0,StringLen(good)/2),key,"L6_LOGICAL",123,"SINTETICO",candidate,nextclock),"L7: envelope truncado rejeitado");
 Check615L7(store.Open(base,key,"L6_LOGICAL",123,"SINTETICO")&&MDWriteStore615L4(base+".tmp","INCOMPLETO")&&!store.Load(candidate,nextclock),"L7 DISCO: escrita interrompida bloqueia retomada");
 candidate=loaded;candidate.revision++;
 Check615L7(!store.Commit(loaded,readclock,candidate,readclock),"L7: arquivo temporario nao e ignorado");store.Close();
 // Cenario independente de ponte temporal certificada somente na fixture.
 string timebase=base+"_tempo";ClockFixture615L5(clock);
 Check615L7(store.Open(timebase,key,"L6_LOGICAL",123,"SINTETICO")&&store.Create(initial,clock),"L7 DISCO: ancora temporal de bancada criada");
 Check615L7(MDRebasePersist615L7(store,initial,clock,"RAW_B",10,1200000,1200000,true,candidate,nextclock)&&nextclock.lo==210100&&candidate.revision==2,"L7: ponte certificada pela fixture preserva tempo decorrido");
 store.Close();
 Check615L7(store.Open(timebase,key,"L6_LOGICAL",123,"SINTETICO")&&store.Load(loaded,readclock)&&readclock.domain=="RAW_B"&&readclock.lo==210100,"L7 DISCO: novo mapa temporal persiste com revisao");
 Check615L7(!MDRebasePersist615L7(store,initial,clock,"RAW_C",1,1300000,1300000,true,candidate,nextclock),"L7: ponte antiga nao sobrescreve revisao atual");
 Check615L7(MDWriteStore615L4(timebase+".head","CORROMPIDO")&&!store.Load(candidate,nextclock),"L7 DISCO: ancora corrompida bloqueada sem fallback");store.Close();
 Check615L7(!store.Open("ModeloD_OPERACIONAL",key,"L6_LOGICAL",123,"SINTETICO"),"L7: pacote restrito a arquivos de bancada");
}
#endif
