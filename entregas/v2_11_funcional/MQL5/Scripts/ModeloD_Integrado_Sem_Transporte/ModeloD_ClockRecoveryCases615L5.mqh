#ifndef MD_CLOCK_RECOVERY_CASES615L5
#define MD_CLOCK_RECOVERY_CASES615L5
#include "ModeloD_StateStoreCases615L4.mqh"
#include "ModeloD_ClockRecovery615L5.mqh"
int checks615L5=0,failures615L5=0;string log615L5="";
void Check615L5(bool ok,string name){checks615L5++;if(!ok)failures615L5++;log615L5+=(ok?"PASS: ":"FAIL: ")+name+"\r\n";}
void ClockFixture615L5(MDClock615L5 &c)
{c.domain="RAW_A";c.raw=10100;c.lo=10100;c.hi=10100;c.utc_lo=1000000;c.utc_hi=1000000;c.utc_trusted=true;}
void Run615L5(string suffix)
{
 Run615L4(suffix);checks615L5=checks615L4;failures615L5=failures615L4;log615L5=log615L4;
 MDClock615L5 old,c,readclock;ClockFixture615L5(old);
 MDProtection protection;MDProtectionReset(protection);
 for(int i=0;i<6;i++){MDProtectionStarted(protection,i*2000);MDProtectionCompleted(protection,i*2000+100);}
 Check615L5(MDClockAdvance615L5(old,"RAW_A",20100,c)&&c.lo==20100&&c.hi==20100,"L5: contador continuo avanca tempo logico");
 Check615L5(!c.utc_trusted,"L5: UTC antigo nao vira prova atual automaticamente");
 Check615L5(!MDClockAdvance615L5(old,"RAW_A",10099,c),"L5: contador regressivo rejeitado");
 Check615L5(!MDClockAdvance615L5(old,"RAW_B",10,c),"L5: origem diferente exige ponte temporal");
 Check615L5(!MDClockRebase615L5(old,"RAW_B",10,1100000,1100000,false,c),"L5: horario novo nao certificado rejeitado");
 old.utc_trusted=false;
 Check615L5(!MDClockRebase615L5(old,"RAW_B",10,1100000,1100000,true,c),"L5: ancora antiga nao certificada rejeitada");ClockFixture615L5(old);
 Check615L5(!MDClockRebase615L5(old,"RAW_B",10,999000,999000,true,c),"L5: UTC comprovadamente regressivo rejeitado");
 Check615L5(!MDClockRebase615L5(old,"RAW_B",10,1100010,1100000,true,c),"L5: intervalo UTC invertido rejeitado");
 Check615L5(MDClockRebase615L5(old,"RAW_B",10,1100000,1100000,true,c)&&c.lo==110100&&c.raw==10,"L5: reinicio do contador preserva cem segundos decorridos");
 Check615L5(MDProtectionExpiry615L5(c,protection,false)==0,"L5: prazo restante nao reinicia nem expira cedo");
 MDClock615L5 later;
 Check615L5(MDClockAdvance615L5(c,"RAW_B",80009,later)&&MDProtectionExpiry615L5(later,protection,false)==0,"L5: um ms antes do prazo ainda nao expirou");
 Check615L5(MDClockAdvance615L5(c,"RAW_B",80010,later)&&MDProtectionExpiry615L5(later,protection,false)==1,"L5: prazo original expira exatamente apos retomada");
 Check615L5(MDProtectionExpiry615L5(later,protection,true)==0,"L5: SL confirmado impede fechamento apenas por prazo");
 Check615L5(MDClockRebase615L5(old,"RAW_B",10,1200000,1200000,true,c)&&MDProtectionExpiry615L5(c,protection,false)==1,"L5: prazo vencido durante parada continua vencido");
 Check615L5(MDClockRebase615L5(old,"RAW_B",10,1179999,1180001,true,c)&&MDProtectionExpiry615L5(c,protection,false)==-1,"L5: incerteza que cruza prazo nao inventa resultado");
 Check615L5(MDClockAdvance615L5(c,"RAW_B",11,later)&&MDProtectionExpiry615L5(later,protection,false)==1,"L5: limite inferior posterior comprova prazo vencido");
 Check615L5(MDClockRebase615L5(old,"RAW_B",10,1009899,1009901,true,c)&&MDProtectionDue615L5(c,protection)==-1,"L5: intervalo incerto de tentativa aguarda evidencia");
 protection.inflight=true;
 Check615L5(MDProtectionDue615L5(c,protection)==0,"L5: reinicio nao libera tentativa de protecao em voo");protection.inflight=false;
 Check615L5(MDClockRebase615L5(old,"RAW_B",10,1000000,1000000,true,c)&&c.lo==10100,"L5: troca de origem nao reseta contagem logica");
 string encoded=MDClockEncode615L5(c);
 Check615L5(MDClockDecode615L5(encoded,readclock)&&MDClockEncode615L5(readclock)==encoded,"L5: serializacao preserva mapa temporal");
 Check615L5(!MDClockDecode615L5(encoded+"x",readclock),"L5: corrupcao temporal rejeitada");
 string text;MDExecGate613 g;MDRecoveryEvidence67 e;MDPlan615C plan;MDJournal610 j;
 Partial615C(text,g,e);Recover615C(text,e,true,g,plan);MDReplay610(plan.journal,"TEST_ONLY_615C","WINZ26",20261016,1,j);
 string key=MDPairKey615L3(j,0,700),logical="LOGICAL_ORIGINAL";MDPair615L3 pair,next,restored;MDCommand613 cmd;MDPairInit615L3(pair,key,logical,700);
 pair.close_slot.management.protection=protection;pair.close_slot.management.last_ms=10100;
 Prepare615L3(pair,plan,3,true,next,cmd);pair=next;Prepare615L3(pair,plan,4,true,next,cmd);pair=next;
 string checkpoint=MDCheckpointEncode615L5(pair,c);
 Check615L5(MDCheckpointDecode615L5(checkpoint,key,logical,pair.revision,restored,readclock)&&restored.close_slot.management.protection.initial_completed==6,"L5: checkpoint liga agenda e mapa temporal");
 Check615L5(restored.cancel_slot.phase==1&&restored.close_slot.phase==1,"L5: cancelamento e fechamento incertos preservados");
 Check615L5(!MDCheckpointDecode615L5(checkpoint,"OUTRO",logical,1,restored,readclock),"L5: checkpoint de outra identidade rejeitado");
 Check615L5(!MDCheckpointDecode615L5(checkpoint,key,logical,pair.revision+1,restored,readclock),"L5: checkpoint antigo rejeitado");
 Check615L5(!MDCheckpointDecode615L5(checkpoint+"x",key,logical,1,restored,readclock),"L5: checkpoint adulterado rejeitado");
 string path="ModeloD_TEST_ONLY_615L4_L5_"+suffix+".checkpoint";
 bool written=!FileIsExist(path,FILE_COMMON)&&MDWriteStore615L4(path,checkpoint);string disk;
 Check615L5(written&&MDReadStore615L4(path,disk)&&disk==checkpoint&&MDCheckpointDecode615L5(disk,key,logical,pair.revision,restored,readclock),"L5 DISCO: checkpoint fechado e relido");
 Check615L5(MDClockRebase615L5(readclock,"RAW_C",5,1200000,1200000,true,later)&&MDProtectionExpiry615L5(later,restored.close_slot.management.protection,false)==1,"L5 DISCO: segunda retomada preserva prazo original");
 Check615L5(!Prepare615L3(restored,plan,3,true,next,cmd)&&!Prepare615L3(restored,plan,4,true,next,cmd),"L5: ponte temporal nao autoriza reenvio de gestao");
 // A decisao chega ao plano integrado usando o tempo logico comprovado.
 MDManagement615L management=restored.close_slot.management;
 Check615L5(MDManage615L(management,text,"TEST_ONLY_615C","WINZ26",20261016,1,0,snap615C,123,"SINTETICO",1792141256927,later.lo,e,false,false,false,g,plan)&&plan.commands[plan.count-1].action==4,"L5: prazo recuperado produz plano de fechamento sem reiniciar agenda");
}
#endif
