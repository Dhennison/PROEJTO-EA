#ifndef MD_SUBMISSION_CASES615K
#define MD_SUBMISSION_CASES615K
#include "ModeloD_Submission615K.mqh"
#include "ModeloD_RehearsalCases.mqh"
int checks615K=0,failures615K=0;string log615K="";
void Check615K(bool ok,string s){checks615K++;if(!ok)failures615K++;log615K+=(ok?"PASS: ":"FAIL: ")+s+"\r\n";}
bool Prepared615K(int level,string &text,MDJournal610 &j,MDSubmission615K &s)
{
 MDDayControl day;MDExecGate613 g;MDPlan615C p;
 if(!Day615C(day))return false;
 MDTestGate615C(g);
 if(!MDTestEntry615C(day,Header615C(),"TEST_ONLY_615C",1,level,3,day.frozen.open_msc+10,true,true,true,g,p))return false;
 text=p.journal;return MDReplay610(text,"TEST_ONLY_615C","WINZ26",20261016,1,j)&&MDNew615K(j,level,s);
}
void Sent615K(MDSubmission615K &s){bool permit=true;MDSending615K(s,permit);}
void Run615K()
{
 checks615K=0;failures615K=0;log615K="";string text,next;MDJournal610 j;MDSubmission615K s,reopened;
 MDExecGate613 gate;MDTestGate615C(gate);MDCommand613 cmd;
 for(int k=0;k<5;k++)
 {
  Check615K(Prepared615K(k,text,j,s)&&MDCommandBuild613(j,k,1,0,0,gate,cmd)&&cmd.buy==(k<3)&&cmd.magic==MDMagic67(1,k),"nivel "+IntegerToString(k)+": comando vinculado ao diario");
  Check615K(cmd.price==(double)j.r[k].entry&&cmd.sl==(double)j.r[k].sl&&cmd.tp==(double)j.r[k].tp,"nivel "+IntegerToString(k)+": precos originais preservados");
 }
 Prepared615K(0,text,j,s);bool permit=false;
 Check615K(!MDSending615K(s,permit),"sem permissao apos persistencia nao encaminha");permit=true;
 Check615K(MDSending615K(s,permit)&&!permit&&!MDSending615K(s,permit),"permissao efemera usada uma vez");
 string receipt=MDEncode615K(s);
 Check615K(MDDecode615K(receipt,s.key,reopened)&&reopened.phase==2,"reinicio com pedido em voo conserva incerteza");
 Check615K(!MDRetry615K(reopened,true,true,true),"timeout ou reinicio incerto nao reenvia");
 Check615K(!MDDecode615K(receipt+"X",s.key,reopened),"recibo corrompido rejeitado");
 Check615K(!MDDecode615K(receipt,"OUTRO_PEDIDO",reopened),"recibo de outro pedido rejeitado");
 Prepared615K(0,text,j,s);Check615K(MDDecode615K(MDEncode615K(s),s.key,reopened)&&reopened.phase==2,"salvo antes da chamada nao recria permissao apos reinicio");
 Sent615K(s);Check615K(!MDResponse615K(s,2,true,10008,0,100)&&s.phase==1,"resposta de tentativa diferente nao e aplicada");
 Check615K(MDResponse615K(s,1,true,10008,0,100)&&s.phase==3&&j.r[0].ticket==0,"PLACED nao vira aceite no diario sem prova");
 Check615K(!MDResponse615K(s,1,true,10008,0,100),"resposta repetida nao altera estado novamente");
 Check615K(!MDRetry615K(s,true,true,true),"resposta aceita nao permite nova entrada");
 MDRawOrder69 order;order.entry_limit=true;order.setup_msc=j.r[0].prepared_msc+10;
 order.order.ticket=100;order.order.magic=MDMagic67(1,0);order.order.symbol="WINZ26";order.order.buy=true;
 order.order.state=0;order.order.initial_volume=3;order.order.remaining=3;bool late;
 Check615K(!MDBind615K(s,text,"TEST_ONLY_615C","WINZ26",20261016,1,0,order,(double)j.r[0].entry+5,0,next,late,true),"preco solicitado divergente bloqueia vinculo");
 order.order.ticket=999;Check615K(!MDBind615K(s,text,"TEST_ONLY_615C","WINZ26",20261016,1,0,order,(double)j.r[0].entry,0,next,late,true),"ticket divergente bloqueia vinculo");order.order.ticket=100;
 Check615K(MDBind615K(s,text,"TEST_ONLY_615C","WINZ26",20261016,1,0,order,(double)j.r[0].entry,order.setup_msc+1,next,late,true)&&!late,"aceite anterior ao primeiro toque gera candidato vinculado");
 Check615K(!MDBind615K(s,text,"TEST_ONLY_615C","WINZ26",20261016,1,0,order,(double)j.r[0].entry,0,next,late,false),"historico de toque incompleto impede classificacao de aceite");
 MDBind615K(s,text,"TEST_ONLY_615C","WINZ26",20261016,1,0,order,(double)j.r[0].entry,order.setup_msc+1,next,late,true);
 MDJournal610 accepted;Check615K(MDReplay610(next,"TEST_ONLY_615C","WINZ26",20261016,1,accepted)&&accepted.r[0].ticket==100&&!accepted.r[0].consumed,"candidato de aceite nao inventa fill");
 Check615K(MDBind615K(s,text,"TEST_ONLY_615C","WINZ26",20261016,1,0,order,(double)j.r[0].entry,order.setup_msc,next,late,true)&&late,"mesmo milissegundo nao comprova aceite anterior ao toque");
 Check615K(MDReplay610(next,"TEST_ONLY_615C","WINZ26",20261016,1,accepted)&&accepted.r[0].consumed&&accepted.r[0].cancel,"aceite tardio consome nivel e registra intencao cancelar saldo");
 long codes[4]={10012,10031,10025,99999};
 for(int i=0;i<4;i++){Prepared615K(0,text,j,s);Sent615K(s);Check615K(MDResponse615K(s,1,true,codes[i],0,0)&&s.phase==2&&!MDRetry615K(s,true,true,true),"resposta incerta "+IntegerToString(codes[i])+" exige conciliacao");}
 Prepared615K(0,text,j,s);Sent615K(s);Check615K(MDResponse615K(s,1,false,10008,0,100)&&s.phase==2,"falha da API prevalece sobre codigo aparentemente aceito");
 Prepared615K(0,text,j,s);Sent615K(s);Check615K(MDResponse615K(s,1,true,10008,1,100)&&s.phase==2,"retorno externo nao zero exige conciliacao");
 Prepared615K(0,text,j,s);Sent615K(s);Check615K(MDResponse615K(s,1,true,10024,0,0)&&s.phase==4,"rejeicao exige classificacao adicional");
 Check615K(!MDRetry615K(s,false,true,true),"sem classificacao transitoria nao repete");
 Check615K(!MDRetry615K(s,true,false,true),"sem prova de nao aceite nao repete");
 Check615K(!MDRetry615K(s,true,true,false),"gates desatualizados nao repetem");
 Check615K(MDRetry615K(s,true,true,true)&&s.attempt==2&&s.phase==0,"nova tentativa somente com todas as evidencias");
 Sent615K(s);Check615K(!MDResponse615K(s,1,true,10008,0,100),"resposta antiga nao vincula tentativa nova");
 MDResponse615K(s,2,true,10024,0,0);s.touched=true;
 Check615K(!MDRetry615K(s,true,true,true),"toque impede nova tentativa apos rejeicao");
 Check615K(MDDecode615K(MDEncode615K(s),s.key,reopened)&&reopened.touched&&!MDRetry615K(reopened,true,true,true),"reinicio preserva impedimento por toque");
 Prepared615K(0,text,j,s);Sent615K(s);MDResponse615K(s,1,true,10016,0,0);
 Check615K(!MDRetry615K(s,false,true,true)&&s.phase==4,"stops invalidos nao sao deslocados nem reenviados automaticamente");
 gate.tick_size=1;Check615K(!MDCommandBuild613(j,0,1,0,0,gate,cmd),"grade diferente de cinco bloqueada");
 MDTestGate615C(gate);gate.volume_max=2;Check615K(!MDCommandBuild613(j,0,1,0,0,gate,cmd),"volume acima do limite bloqueado");
 MDTestGate615C(gate);gate.intent_durable=false;Check615K(!MDCommandBuild613(j,0,1,0,0,gate,cmd),"diario nao duravel bloqueia comando");
}
#endif
