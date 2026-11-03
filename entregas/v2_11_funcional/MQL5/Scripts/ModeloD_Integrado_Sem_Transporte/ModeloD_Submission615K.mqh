#ifndef MD_SUBMISSION615K
#define MD_SUBMISSION615K
#include "ModeloD_Execution.mqh"
#include "ModeloD_Collect.mqh"
struct MDSubmission615K {string key;long attempt,ticket,retcode;int phase;bool touched;};
// Fases:0 preparado;1 em voo;2 incerto;3 resposta aceita aguardando prova;
// 4 rejeitado exige classificacao;5 vinculo confirmado. Nao existe envio aqui.
string MDRequestKey615K(const MDJournal610 &j,int level)
{
 if(!j.valid||level<0||level>4||j.r[level].id<=0)return "";
 MDRequest610 q=j.r[level];
 return j.scope+"|"+j.contract+"|"+IntegerToString(j.date)+"|"+IntegerToString(j.instance)+"|"+IntegerToString(level)+"|"+
 IntegerToString(q.id)+"|"+IntegerToString(q.volume)+"|"+IntegerToString(q.entry)+"|"+IntegerToString(q.sl)+"|"+IntegerToString(q.tp)+"|"+IntegerToString(q.prepared_msc);
}
bool MDNew615K(const MDJournal610 &j,int level,MDSubmission615K &s)
{
 s.key=MDRequestKey615K(j,level);s.attempt=1;s.phase=0;s.ticket=0;s.retcode=0;s.touched=false;
 return s.key!=""&&j.r[level].ticket==0&&!j.r[level].consumed&&!j.r[level].cancel&&!j.r[level].close;
}
bool MDSending615K(MDSubmission615K &s,bool &permit)
{if(s.key==""||s.phase!=0||s.touched||!permit)return false;permit=false;s.phase=1;return true;}
bool MDResponse615K(MDSubmission615K &s,long attempt,bool api_ok,long retcode,long external,long ticket)
{
 if(attempt!=s.attempt||(s.phase!=1&&s.phase!=2)||ticket<0)return false;
 int classification=MDResponse613(api_ok,retcode,external);
 s.retcode=retcode;s.ticket=ticket;
 if(classification==1)s.phase=3;
 else if(classification==2)s.phase=4;
 else s.phase=2;
 return true;
}
bool MDRetry615K(MDSubmission615K &s,bool rejection_classified_transient,bool no_order_proven,bool gates_current)
{
 // A prova de nao aceite NAO e simplesmente inventario vazio.
 // A politica de classificacao vem do adaptador de transporte, nao do retcode isolado.
 if(s.phase!=4||s.ticket!=0||s.touched||!rejection_classified_transient||!no_order_proven||!gates_current||s.attempt>=1000000000)return false;
 s.attempt++;s.phase=0;s.retcode=0;return true;
}
string MDEncode615K(const MDSubmission615K &s)
{
 if(s.key==""||StringFind(s.key,"\n")>=0||s.attempt<1||s.phase<0||s.phase>5||s.ticket<0||s.retcode<0)return "";
 string body="MD615K\n"+s.key+"\n"+IntegerToString(s.attempt)+"\n"+IntegerToString(s.phase)+"\n"+IntegerToString(s.ticket)+"\n"+IntegerToString(s.retcode)+"\n"+IntegerToString(s.touched?1:0)+"\n";
 return body+IntegerToString(MDHash67(body));
}
bool MDDecode615K(string text,string expected_key,MDSubmission615K &s)
{
 string f[8];int pos=0;
 for(int i=0;i<7;i++){int end=StringFind(text,"\n",pos);if(end<0)return false;f[i]=StringSubstr(text,pos,end-pos);pos=end+1;}
 f[7]=StringSubstr(text,pos);long attempt,phase,ticket,retcode,touched,hash;
 if(f[0]!="MD615K"||expected_key==""||f[1]!=expected_key||!MDLong610(f[2],attempt)||attempt<1||!MDLong610(f[3],phase)||phase>5||
 !MDLong610(f[4],ticket)||!MDLong610(f[5],retcode)||!MDLong610(f[6],touched)||touched>1||!MDLong610(f[7],hash)||hash!=MDHash67(StringSubstr(text,0,pos)))return false;
 s.key=f[1];s.attempt=attempt;s.phase=(int)phase;s.ticket=ticket;s.retcode=retcode;s.touched=touched==1;
 // Reabertura nao concede permissao efemera de enviar, mesmo se salvo antes da chamada.
 if(s.phase==0||s.phase==1)s.phase=2;
 return true;
}
bool MDBind615K(MDSubmission615K &s,string journal,string scope,string contract,int date,int instance,int level,
 const MDRawOrder69 &order,double observed_price,long first_touch_msc,string &next,bool &late,bool touch_history_complete)
{
 next="";late=false;MDJournal610 j;
 if(!touch_history_complete||!MDReplay610(journal,scope,contract,date,instance,j)||s.key!=MDRequestKey615K(j,level)||s.phase!=3||s.ticket<=0)return false;
 MDRequest610 q=j.r[level];
 if(q.ticket!=0||order.order.ticket!=s.ticket||!order.entry_limit||order.order.symbol!=contract||order.order.magic!=MDMagic67(instance,level)||
 order.order.buy!=(level<3)||!MDEqual68(order.order.initial_volume,(double)q.volume)||observed_price!=(double)q.entry||order.setup_msc<q.prepared_msc||
 order.order.state<0||order.order.state>2)return false;
 // O timestamp de aceite e verificado; retorno PLACED sozinho nao o fornece.
 MDEvent610 e;e.kind=2;e.level=level;e.request=q.id;e.ticket=s.ticket;e.msc=order.setup_msc;
 e.volume=q.volume;e.entry=q.entry;e.sl=q.sl;e.tp=q.tp;
 if(!MDAppend610(journal,scope,contract,date,instance,e,next))return false;
 late=first_touch_msc>0&&order.setup_msc>=first_touch_msc;
 if(late)
 {
  MDJournal610 accepted;if(!MDReplay610(next,scope,contract,date,instance,accepted))return false;
  for(int kind=3;kind<=4;kind++)
  {e.kind=kind;string added;if(!MDAppend610(next,scope,contract,date,instance,e,added))return false;next=added;}
 }
 // Candidato apenas: chamador precisa gravar antes de considerar vinculo confirmado.
 return true;
}
#endif
