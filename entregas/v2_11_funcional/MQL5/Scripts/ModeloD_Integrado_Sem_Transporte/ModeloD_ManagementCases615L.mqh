#ifndef MD_MANAGEMENT_CASES615L
#define MD_MANAGEMENT_CASES615L
#include "ModeloD_RehearsalCases.mqh"
#include "ModeloD_Management615L.mqh"
int checks615L=0,failures615L=0;string log615L="";
void Check615L(bool ok,string name){checks615L++;if(!ok)failures615L++;log615L+=(ok?"PASS: ":"FAIL: ")+name+"\r\n";}
bool Plan615L(MDManagement615L &m,string text,MDRecoveryEvidence67 &e,MDExecGate613 &g,long ms,bool sl,bool tp,bool cutoff,MDPlan615C &p)
{return MDManage615L(m,text,"TEST_ONLY_615C","WINZ26",20261016,1,0,snap615C,123,"SINTETICO",1792141256927,ms,e,cutoff,sl,tp,g,p);}
void Run615L()
{
 Run615C();checks615L=checks615C;failures615L=failures615C;log615L=log615C;
 string text;MDExecGate613 g;MDRecoveryEvidence67 e;MDPlan615C p;MDManagement615L m;
 Check615L(Partial615C(text,g,e),"L: cadeia parcial inicializada");MDManagementReset615L(m,700);
 Check615L(Plan615L(m,text,e,g,0,false,false,false,p)&&p.count==1&&p.commands[0].action==2,"L: parcial inicia protecao");
 Check615L(!MDManagementBegin615L(m,0,700,false),"L: intencao nao duravel nao inicia tentativa");
 Check615L(!MDManagementBegin615L(m,0,701,true),"L: ticket divergente nao inicia tentativa");
 Check615L(MDManagementBegin615L(m,0,700,true),"L: tentativa de protecao iniciada");
 Check615L(Plan615L(m,text,e,g,100,false,false,false,p)&&p.count==0,"L: protecao em voo nao duplica plano");
 Check615L(!MDManagementComplete615L(m,100,701),"L: conclusao de outro ticket rejeitada");
 Check615L(MDManagementComplete615L(m,100,700),"L: tentativa concluida sem presumir SL confirmado");
 Check615L(!MDManagementComplete615L(m,100,700),"L: conclusao duplicada rejeitada");
 Check615L(Plan615L(m,text,e,g,1999,false,false,false,p)&&p.count==0,"L: antes de dois segundos aguarda");
 Check615L(Plan615L(m,text,e,g,2000,false,false,false,p)&&p.count==1,"L: segunda tentativa no prazo");
 for(int i=1;i<6;i++)
 {
  bool started=MDManagementBegin615L(m,i*2000,700,true);
  bool ended=MDManagementComplete615L(m,i*2000+100,700);
  Check615L(started&&ended,"L: tentativa inicial "+IntegerToString(i+1));
 }
 Check615L(Plan615L(m,text,e,g,19999,false,false,false,p)&&p.count==0,"L: adicional aguarda dez segundos");
 Check615L(Plan615L(m,text,e,g,20000,false,false,false,p)&&p.count==1,"L: adicional permite nova protecao");
 Check615L(Plan615L(m,text,e,g,190099,false,false,false,p)&&p.commands[0].action==2,"L: antes de 180s apos sexta nao fecha por prazo");
 Check615L(Plan615L(m,text,e,g,190100,false,false,false,p)&&p.commands[p.count-1].action==4&&p.commands[p.count-1].ticket==700,"L: sem SL no prazo gera intencao e fechamento");
 string closing=p.journal;MDJournal610 j;MDReplay610(closing,"TEST_ONLY_615C","WINZ26",20261016,1,j);
 Check615L(j.r[0].close,"L: fechamento representado no diario candidato");
 MDManagementReset615L(m,700);
 Check615L(Plan615L(m,closing,e,g,0,false,false,false,p)&&p.commands[p.count-1].action==4,"L: diario de fechamento nao rearma protecao apos reset");
 MDManagementReset615L(m,700);
 for(int i=0;i<6;i++){MDManagementBegin615L(m,i*2000,700,true);MDManagementComplete615L(m,i*2000+100,700);}
 Check615L(Plan615L(m,text,e,g,190100,true,false,false,p)&&p.count==1&&p.commands[0].action==2,"L: SL confirmado TP ausente continua reparacao");
 Check615L(Plan615L(m,text,e,g,190101,true,true,false,p)&&p.count==0,"L: SL e TP confirmados dispensam reparacao");
 Check615L(!Plan615L(m,text,e,g,190000,true,true,false,p)&&p.count==0,"L: relogio monotono regressivo bloqueia");
 MDManagementReset615L(m,700);e.boundary_after_accept=true;e.exit_after_entry=true;
 Check615L(Plan615L(m,text,e,g,0,true,true,false,p)&&p.count==2&&p.commands[0].action==3&&p.commands[1].action==4,"L: fronteira comprovada cancela saldo e fecha parcial protegida");
 Partial615C(text,g,e);MDManagementReset615L(m,700);
 Check615L(Plan615L(m,text,e,g,0,true,true,true,p)&&p.count==2,"L: cutoff prevalece sobre protecoes presentes");
 string cutoff_text=p.journal;g.connected=false;
 Check615L(!Plan615L(m,cutoff_text,e,g,1,true,true,true,p)&&p.count==0,"L: desconexao bloqueia comandos");g.connected=true;
 Check615L(Plan615L(m,cutoff_text,e,g,2,true,true,false,p)&&p.count==2,"L: reconexao conserva encerramento registrado");
 snap615C.o[0].order.state=2;snap615C.o[0].order.remaining=0;snap615C.d[0].volume=3;snap615C.p[0].volume=3;
 Check615L(Plan615L(m,cutoff_text,e,g,3,true,true,false,p)&&p.count==1&&p.commands[0].volume==3,"L: fill durante cancelamento atualiza volume de fechamento");
 snap615C.deals=2;snap615C.d[1]=snap615C.d[0];snap615C.d[1].ticket=102;snap615C.d[1].order=200;snap615C.d[1].entry=1;snap615C.d[1].buy=false;snap615C.d[1].volume=3;snap615C.d[1].msc++;
 snap615C.positions=0;
 Check615L(Plan615L(m,cutoff_text,e,g,4,true,true,false,p)&&p.count==0,"L: saida conciliada encerra planos da cadeia");
}
#endif
