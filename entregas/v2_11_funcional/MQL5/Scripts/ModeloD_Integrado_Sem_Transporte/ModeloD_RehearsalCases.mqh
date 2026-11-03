#ifndef MD_REHEARSAL_CASES615C
#define MD_REHEARSAL_CASES615C
#include "ModeloD_Rehearsal.mqh"
int checks615C=0,failures615C=0;string log615C="";
MDSnapshot69 snap615C;
void Check615C(bool ok,string name)
{checks615C++;if(!ok)failures615C++;string line=(ok?"PASS: ":"FAIL: ")+name;Print(line);log615C+=line+"\r\n";}
bool Day615C(MDDayControl &d)
{MDDailyRaw614 raw;MDObserverFixture615(raw);MDDataEvidence e;string why;return MDDailyBuild614(raw,e,why)&&MDDayStart(d,e);}
string Header615C(){return MDHeader610("TEST_ONLY_615C","WINZ26",20261016,1);}
void Market615C(MDRecoveryEvidence67 &e)
{
 e.server_complete=false;e.ownership_resolved=false;e.history_complete=true;e.request_resolved=false;
 e.had_entry=false;e.touched=false;e.accepted_before_touch=true;e.boundary_after_accept=false;e.exit_after_entry=false;e.cutoff=false;
 e.pending_count=0;e.position_count=0;
}
// Ponte calculo->PREPARAR->ACEITE simulado->snapshot parcial ligado por identifier.
bool Partial615C(string &text,MDExecGate613 &g,MDRecoveryEvidence67 &e)
{
 MDDayControl day;if(!Day615C(day))return false;MDTestGate615C(g);Market615C(e);MDPlan615C p;
 long now=day.frozen.open_msc+10;
 if(!MDTestEntry615C(day,Header615C(),"TEST_ONLY_615C",1,0,3,now,true,true,true,g,p))return false;
 MDJournal610 j;if(!MDReplay610(p.journal,"TEST_ONLY_615C","WINZ26",20261016,1,j))return false;
 MDEvent610 accepted;accepted.kind=2;accepted.level=0;accepted.request=j.r[0].id;accepted.ticket=100;
 accepted.msc=now+10;accepted.volume=3;accepted.entry=j.r[0].entry;accepted.sl=j.r[0].sl;accepted.tp=j.r[0].tp;
 if(!MDAppend610(p.journal,j.scope,j.contract,j.date,j.instance,accepted,text))return false;
 snap615C.complete=true;snap615C.connected=true;snap615C.hedge=true;snap615C.account_key=123;snap615C.server_key="SINTETICO";
 snap615C.orders=1;snap615C.deals=1;snap615C.positions=1;
 snap615C.o[0].setup_msc=accepted.msc;snap615C.o[0].entry_limit=true;
 snap615C.o[0].order.ticket=100;snap615C.o[0].order.magic=MDMagic67(1,0);snap615C.o[0].order.symbol="WINZ26";
 snap615C.o[0].order.buy=true;snap615C.o[0].order.state=0;snap615C.o[0].order.initial_volume=3;snap615C.o[0].order.remaining=2;
 snap615C.d[0].ticket=101;snap615C.d[0].order=100;snap615C.d[0].position=500;snap615C.d[0].magic=MDMagic67(1,0);
 snap615C.d[0].msc=now+20;snap615C.d[0].symbol="WINZ26";snap615C.d[0].buy=true;snap615C.d[0].entry=0;snap615C.d[0].volume=1;
 snap615C.p[0].ticket=700;snap615C.p[0].identifier=500;snap615C.p[0].magic=MDMagic67(1,0);
 snap615C.p[0].symbol="WINZ26";snap615C.p[0].buy=true;snap615C.p[0].volume=1;
 return true;
}
bool Recover615C(string text,MDRecoveryEvidence67 &e,bool cutoff,MDExecGate613 &g,MDPlan615C &p)
{return MDTestRecoverPlan615C(text,"TEST_ONLY_615C","WINZ26",20261016,1,0,snap615C,123,"SINTETICO",1792141256927,e,cutoff,g,p);}
int Run615C()
{
 checks615C=0;failures615C=0;log615C="";
 MDDayControl day;MDExecGate613 g;MDPlan615C p;MDRecoveryEvidence67 e;MDJournal610 j;
 Check615C(Day615C(day),"dados fixos constroem controlador");
 MDTestGate615C(g);string text=Header615C();long now=day.frozen.open_msc+10;
 for(int i=0;i<5;i++)
 {
  bool ok=MDTestEntry615C(day,text,"TEST_ONLY_615C",1,i,3,now,true,true,true,g,p);
  Check615C(ok&&p.count==1&&p.commands[0].price==day.day.levels[i].entry_tick&&p.commands[0].sl==day.day.levels[i].sl_tick&&p.commands[0].tp==day.day.levels[i].tp_tick,"nivel "+IntegerToString(i)+" calculo diario ligado a comando simulado");
  if(ok)text=p.journal;
 }
 Check615C(!MDTestEntry615C(day,text,"TEST_ONLY_615C",1,0,3,now,true,true,true,g,p),"pedido em voo nao duplica entrada");
 Day615C(day);Check615C(!MDTestEntry615C(day,text,"TEST_ONLY_615C",1,0,3,now,true,true,true,g,p),"reiniciar controlador nao apaga PREPARAR do diario");
 Day615C(day);MDDayObserve(day,now,210105);
 Check615C(!MDTestEntry615C(day,Header615C(),"TEST_ONLY_615C",1,3,3,now,true,true,true,g,p),"primeiro toque bloqueia preparacao tardia");
 Day615C(day);Check615C(!MDTestEntry615C(day,Header615C(),"TEST_ONLY_615C",1,0,3,now,false,true,true,g,p),"sem relogio verificado nao prepara");
 Check615C(!MDTestEntry615C(day,Header615C(),"TEST_ONLY_615C",1,0,3,now,true,false,true,g,p),"sem historia verificada nao prepara");
 Check615C(!MDTestEntry615C(day,Header615C(),"TEST_ONLY_615C",1,0,3,now,true,true,false,g,p),"sem conciliacao nao prepara");
 g.lock_held=false;Check615C(!MDTestEntry615C(day,Header615C(),"TEST_ONLY_615C",1,0,3,now,true,true,true,g,p),"sem lock nao cria comando");MDTestGate615C(g);
 Check615C(!MDTestEntry615C(day,Header615C(),"TEST_ONLY_615C",1,0,0,now,true,true,true,g,p),"volume invalido nao prepara");
 long cutoff=MDCivilMidnight2026(day.frozen.date)+(long)day.frozen.session.cutoff*1000;
 Check615C(!MDTestEntry615C(day,Header615C(),"TEST_ONLY_615C",1,0,3,cutoff,true,true,true,g,p)&&day.cutoff,"timer de corte sem tick bloqueia entrada");
 Check615C(Partial615C(text,g,e),"cadeia parcial nasce do comando e diario calculados");
 Check615C(Recover615C(text,e,false,g,p)&&p.count==1&&p.commands[0].action==2&&p.commands[0].ticket==700&&p.commands[0].volume==1&&p.commands[0].sl==207005&&p.commands[0].tp==207590,"parcial protege somente ticket conciliado com SL TP originais");
 string saved=p.journal;MDReplay610(saved,"TEST_ONLY_615C","WINZ26",20261016,1,j);
 Check615C(j.r[0].consumed&&j.r[0].ticket==100,"parcial registra consumo no diario simulado");
 Check615C(Recover615C(saved,e,false,g,p)&&p.journal==saved,"nova conciliacao nao duplica consumo no diario");
 Check615C(Recover615C(text,e,true,g,p)&&p.count==2&&p.commands[0].action==3&&p.commands[0].ticket==100&&p.commands[1].action==4&&p.commands[1].ticket==700&&!p.commands[1].buy,"corte planeja cancelar saldo e fechar parcial por ticket");
 saved=p.journal;
 Check615C(Recover615C(saved,e,false,g,p)&&p.count==2&&p.commands[1].action==4,"retomada conserva intencoes mesmo sem novo evento de corte");
 e.boundary_after_accept=true;
 Check615C(Recover615C(text,e,false,g,p)&&p.count==2&&p.commands[0].action==3&&p.commands[1].action==2,"fronteira sem prova apos fill cancela saldo e protege posicao");
 e.exit_after_entry=true;
 Check615C(Recover615C(text,e,false,g,p)&&p.count==2&&p.commands[1].action==4,"fronteira comprovada apos fill planeja fechamento");
 Partial615C(text,g,e);g.connected=false;
 Check615C(!Recover615C(text,e,true,g,p)&&p.count==0,"desconexao nao produz comando despachavel");
 g.connected=true;Check615C(Recover615C(saved,e,false,g,p)&&p.commands[1].action==4,"reconexao retoma intencao anterior");
 Partial615C(text,g,e);snap615C.account_key=999;Check615C(!Recover615C(text,e,false,g,p),"conta diferente rejeitada");
 Partial615C(text,g,e);snap615C.server_key="OUTRO";Check615C(!Recover615C(text,e,false,g,p),"servidor diferente rejeitado");
 Partial615C(text,g,e);snap615C.o[0].order.magic++;Check615C(!Recover615C(text,e,false,g,p),"Magic divergente nao recebe comando");
 Partial615C(text,g,e);snap615C.p[0].identifier=501;Check615C(!Recover615C(text,e,false,g,p),"posicao sem cadeia comprovada nao recebe comando");
 Partial615C(text,g,e);snap615C.p[0].volume=2;Check615C(!Recover615C(text,e,false,g,p),"volume divergente bloqueia plano inteiro");
 Partial615C(text,g,e);snap615C.complete=false;Check615C(!Recover615C(text,e,false,g,p),"snapshot incompleto bloqueia plano");
 Partial615C(text,g,e);g.snapshot_fresh=false;Check615C(!Recover615C(text,e,false,g,p),"snapshot antigo bloqueia plano");
 Partial615C(text,g,e);Check615C(!Recover615C(text+"corrompido",e,false,g,p),"diario corrompido bloqueia plano");
 Partial615C(text,g,e);snap615C.p[0].ticket=701;
 Check615C(Recover615C(text,e,false,g,p)&&p.commands[0].ticket==701,"mudanca de ticket respeita identifier conciliado");
 Partial615C(text,g,e);e.history_complete=false;
 Check615C(Recover615C(text,e,false,g,p)&&p.count==2&&p.commands[0].action==3,"historico incompleto cancela saldo comprovado sem nova entrada");
 Partial615C(text,g,e);snap615C.o[0].order.state=2;snap615C.o[0].order.remaining=0;snap615C.d[0].volume=3;snap615C.p[0].volume=3;
 Check615C(Recover615C(text,e,true,g,p)&&p.count==1&&p.commands[0].action==4&&p.commands[0].volume==3,"fill durante cancelamento fecha volume conciliado total");
 Partial615C(text,g,e);snap615C.deals=2;snap615C.d[1]=snap615C.d[0];snap615C.d[1].ticket=102;snap615C.d[1].position=501;snap615C.d[1].msc++;
 snap615C.positions=2;snap615C.p[1]=snap615C.p[0];snap615C.p[1].identifier=501;snap615C.p[1].ticket=701;snap615C.o[0].order.remaining=1;
 Check615C(Recover615C(text,e,false,g,p)&&p.count==2&&p.commands[0].ticket==700&&p.commands[1].ticket==701,"duas posicoes da mesma ordem recebem protecao individual");
 MDProtection protection;MDProtectionReset(protection);
 Check615C(MDProtectionDue(protection,0),"agenda permite primeira protecao imediata");
 MDProtectionStarted(protection,0);Check615C(!MDProtectionDue(protection,10000),"protecao em voo nao duplica tentativa");MDProtectionCompleted(protection,100);
 Check615C(!MDProtectionDue(protection,1999)&&MDProtectionDue(protection,2000),"espacamento inicial preservado");
 for(int i=1;i<6;i++){MDProtectionStarted(protection,i*2000);MDProtectionCompleted(protection,i*2000+100);}
 Check615C(!MDProtectionCloseRequired(protection,190099,false)&&MDProtectionCloseRequired(protection,190100,false),"prazo adicional inicia apos conclusao da sexta tentativa");
 Partial615C(text,g,e);e.exit_after_entry=MDProtectionCloseRequired(protection,190100,false);
 Check615C(Recover615C(text,e,false,g,p)&&p.commands[p.count-1].action==4,"prazo sem SL chega ao comando simulado de fechamento");
 Partial615C(text,g,e);e.exit_after_entry=MDProtectionCloseRequired(protection,190100,true);
 Check615C(Recover615C(text,e,false,g,p)&&p.count==1&&p.commands[0].action==2,"SL presente TP ausente continua protecao sem fechar por prazo");
 string row="TESTE_615C;Checks="+IntegerToString(checks615C)+";Failures="+IntegerToString(failures615C)+";INTEGRACAO_SINTETICA;SEM_ORDENS";
 Print(row);log615C+=row+"\r\n";return failures615C;
}
#endif
