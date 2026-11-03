#ifndef MD_RESPONSE_STORE615Q
#define MD_RESPONSE_STORE615Q
#include "ModeloD_EntryBundle615P.mqh"
#include "ModeloD_Rehearsal.mqh"
#include "ModeloD_Management615L.mqh"
struct MDResponseState615Q {long revision;string journal;MDSubmission615K receipt;};
// Bancada: diario, resposta e vinculo publicados juntos. Nao envia ordens.
class MDResponseStore615Q
{
 private:
 int handle,level,date,instance;long account;string base,scope,contract,server,key;
 string Prefix(){return "MD615Q\n"+IntegerToString(account)+"\n"+server+"\n";}
 bool Valid(const MDResponseState615Q &s)
 {
  MDJournal610 j;
  if(s.revision<1||s.revision>1000000000||s.receipt.phase<2||s.receipt.phase>5||s.receipt.attempt!=1||
    !MDReplay610(s.journal,scope,contract,date,instance,j)||MDRequestKey615K(j,level)!=key||s.receipt.key!=key)return false;
  if(s.receipt.phase==5)return s.receipt.ticket>0&&j.r[level].ticket==s.receipt.ticket;
  return j.r[level].ticket==0;
 }
 string Encode(const MDResponseState615Q &s)
 {
  if(!Valid(s))return "";
  string receipt=MDEncode615K(s.receipt);if(receipt=="")return "";
  string body=Prefix()+IntegerToString(s.revision)+"\n"+IntegerToString(StringLen(s.journal))+"\n"+s.journal+
    IntegerToString(StringLen(receipt))+"\n"+receipt;
  return body+IntegerToString(MDHash67(body));
 }
 bool Number(string text,int &pos,long &value)
 {int end=StringFind(text,"\n",pos);if(end<0||!MDLong610(StringSubstr(text,pos,end-pos),value))return false;pos=end+1;return true;}
 bool Decode(string text,MDResponseState615Q &out)
 {
  string prefix=Prefix();if(StringFind(text,prefix)!=0)return false;
  int pos=StringLen(prefix);long n;MDResponseState615Q s;
  if(!Number(text,pos,s.revision)||!Number(text,pos,n)||n<1||n>12000||pos+n>=StringLen(text))return false;
  s.journal=StringSubstr(text,pos,(int)n);pos+=(int)n;
  if(!Number(text,pos,n)||n<1||n>3000||pos+n>=StringLen(text))return false;
  string receipt=StringSubstr(text,pos,(int)n);pos+=(int)n;long hash;
  if(!MDLong610(StringSubstr(text,pos),hash)||hash!=MDHash67(StringSubstr(text,0,pos))||
    !MDDecode615K(receipt,key,s.receipt)||!Valid(s))return false;
  out=s;return true;
 }
 bool Publish(const MDResponseState615Q &s,bool replace)
 {
  string text=Encode(s);MDResponseState615Q check;
  if(text==""||!Decode(text,check)||FileIsExist(base+".tmp",FILE_COMMON)||
    !MDWriteStore615L4(base+".tmp",text)||!FileMove(base+".tmp",FILE_COMMON,base+".head",FILE_COMMON|(replace?FILE_REWRITE:0)))return false;
  string readback;return MDReadStore615L4(base+".head",readback)&&readback==text;
 }
 bool Commit(const MDResponseState615Q &old,const MDResponseState615Q &next)
 {
  MDResponseState615Q disk;
  if(next.revision!=old.revision+1||!Load(disk)||Encode(disk)!=Encode(old))return false;
  return Publish(next,true);
 }
 public:
 MDResponseStore615Q(){handle=INVALID_HANDLE;}
 ~MDResponseStore615Q(){Close();}
 void Close(){if(handle!=INVALID_HANDLE)FileClose(handle);handle=INVALID_HANDLE;}
 bool Open(string path,const MDJournal610 &j,int k,long acct,string broker)
 {
  string rk=MDRequestKey615K(j,k);
  if(handle!=INVALID_HANDLE||StringFind(path,"ModeloD_TEST_ONLY_615L4_Q_")!=0||!MDStorePath615L4(path)||
    StringFind(path,"\n")>=0||StringFind(path,"\r")>=0||rk==""||acct<=0||broker==""||StringFind(broker,"\n")>=0||StringFind(broker,"\r")>=0)return false;
  int h=FileOpen(path+".lock",FILE_READ|FILE_WRITE|FILE_BIN|FILE_COMMON);if(h==INVALID_HANDLE)return false;
  handle=h;base=path;scope=j.scope;contract=j.contract;date=j.date;instance=j.instance;level=k;account=acct;server=broker;key=rk;return true;
 }
 bool Load(MDResponseState615Q &out)
 {
  if(handle==INVALID_HANDLE||FileIsExist(base+".tmp",FILE_COMMON))return false;
  string text;if(!MDReadStore615L4(base+".head",text))return false;return Decode(text,out);
 }
 bool Import(MDEntryBundle615P &source)
 {
  if(handle==INVALID_HANDLE||FileIsExist(base+".head",FILE_COMMON)||FileIsExist(base+".tmp",FILE_COMMON))return false;
  MDResponseState615Q s;s.revision=1;
  if(!source.MatchesIdentity(account,server,key)||!source.Restore(s.journal,s.receipt)||s.receipt.key!=key||s.receipt.phase!=2)return false;
  return Publish(s,false);
 }
 bool Response(long expected_revision,long attempt,bool api_ok,long retcode,long external,long ticket)
 {
  MDResponseState615Q old;if(!Load(old)||old.revision!=expected_revision)return false;
  MDResponseState615Q next=old;
  if(!MDResponse615K(next.receipt,attempt,api_ok,retcode,external,ticket)||MDEncode615K(next.receipt)==MDEncode615K(old.receipt))return false;
  next.revision++;return Commit(old,next);
 }
 bool Bind(long expected_revision,const MDRawOrder69 &order,double price,long first_touch,
  bool history_complete,bool fresh,long evidence_account,string evidence_server)
 {
  if(!fresh||evidence_account!=account||evidence_server!=server)return false;
  MDResponseState615Q old;if(!Load(old)||old.revision!=expected_revision)return false;
  MDResponseState615Q next=old;bool late;
  if(!MDBind615K(next.receipt,old.journal,scope,contract,date,instance,level,order,price,first_touch,next.journal,late,history_complete))return false;
  next.receipt.phase=5;next.receipt.touched=old.receipt.touched||late;next.revision++;
  return Commit(old,next);
 }
 // Ponte R: concilia e publica intencoes ANTES de expor planos de bancada.
 // Nao reserva tentativas de gestao, nao envia e nao confirma execucoes.
 bool Reconcile615R(long expected_revision,const MDSnapshot69 &snapshot,long now,
  const MDRecoveryEvidence67 &market,bool cutoff,const MDExecGate613 &gate,MDPlan615C &out)
 {
  MDClearPlan615C(out);MDResponseState615Q old;
  if(!Load(old)||old.revision!=expected_revision||old.receipt.phase!=5)return false;
  MDExecGate613 planning=gate;
  planning.intent_durable=true; // candidato em memoria; nao exposto antes do commit.
  MDPlan615C candidate;
  if(!MDTestRecoverPlan615C(old.journal,scope,contract,date,instance,level,snapshot,account,server,now,market,cutoff,planning,candidate))return false;
  if(candidate.journal!=old.journal)
  {
   MDResponseState615Q next=old;next.journal=candidate.journal;next.revision++;
   MDJournal610 parsed;if(!MDReplay610(next.journal,scope,contract,date,instance,parsed))return false;
   next.receipt.touched=next.receipt.touched||parsed.r[level].consumed;
   if(!Commit(old,next))return false;
  }
  else
  {
   MDResponseState615Q check;if(!Load(check)||Encode(check)!=Encode(old))return false;
  }
  candidate.reason="INTENCOES_DURAVEIS_PLANOS_DE_BANCADA_SEM_TRANSPORTE";
  out=candidate;return true;
 }

 bool JournalB1(MDJournal610 &out)
 {MDResponseState615Q state;return Load(state)&&MDReplay610(state.journal,scope,contract,date,instance,out);}
 bool IdentityB1(long acct,string broker){return handle!=INVALID_HANDLE&&account==acct&&server==broker;}
 bool ManageB1(long expected_revision,MDManagement615L &management,const MDSnapshot69 &snapshot,
  long market_now,long monotonic_now,const MDRecoveryEvidence67 &market,bool cutoff,bool sl,bool tp,
  MDExecGate613 &gate,MDPlan615C &out)
 {
  MDClearPlan615C(out);MDResponseState615Q old;
  if(!Load(old)||old.revision!=expected_revision||old.receipt.phase!=5)return false;
  // Nao inicializar outro controlador silenciosamente para segundo ticket.
  MDJournal610 j;MDOrigin68 origin;MDChainInput68 chain;MDChainResult68 result;string why;
  if(!MDReplay610(old.journal,scope,contract,date,instance,j)||!MDOrigin611(j,scope,level,snapshot,origin)||
    !MDBuild69(snapshot,origin,market_now,chain,why)||!MDReconcileChain68(chain,result))return false;
  int live=0;for(int i=0;i<result.position_count;i++)if(result.positions[i].open_volume>0)
  {live++;if(result.positions[i].current_ticket!=management.ticket)return false;}
  if(live>1)return false;
  MDManagement615L candidate=management;MDPlan615C plan;
  if(!MDManage615L(candidate,old.journal,scope,contract,date,instance,level,snapshot,account,server,market_now,monotonic_now,
    market,cutoff,sl,tp,gate,plan))return false;
  if(plan.journal!=old.journal)
  {
   MDResponseState615Q next=old;next.journal=plan.journal;next.revision++;
   if(!MDReplay610(next.journal,scope,contract,date,instance,j))return false;
   next.receipt.touched=next.receipt.touched||j.r[level].consumed;
   if(!Commit(old,next))return false;
  }
  management=candidate;out=plan;return true;
 }

};
#endif
