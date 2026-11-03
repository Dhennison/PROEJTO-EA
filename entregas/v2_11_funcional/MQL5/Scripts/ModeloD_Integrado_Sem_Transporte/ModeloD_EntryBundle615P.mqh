#ifndef MD_ENTRY_BUNDLE615P
#define MD_ENTRY_BUNDLE615P
#include "ModeloD_Reservation615O.mqh"
// Publicacao unica de diario + reserva de entrada. Bancada, nunca transporte.
class MDEntryBundle615P
{
 private:
 int handle,level,date,instance;long account;string base,server,scope,contract,key;
 string Prefix(){return "MD615P\n"+IntegerToString(account)+"\n"+server+"\n";}
 bool Decode(string text,string &journal,MDSubmission615K &receipt)
 {
  string prefix=Prefix();if(StringFind(text,prefix)!=0)return false;
  int pos=StringLen(prefix),end=StringFind(text,"\n",pos);long size;
  if(end<0||!MDLong610(StringSubstr(text,pos,end-pos),size)||size<1||size>12000)return false;
  pos=end+1;if(pos+size>=StringLen(text))return false;
  string jt=StringSubstr(text,pos,(int)size);pos+=(int)size;
  end=StringFind(text,"\n",pos);long rs;
  if(end<0||!MDLong610(StringSubstr(text,pos,end-pos),rs)||rs<1||rs>3000)return false;
  pos=end+1;if(pos+rs>=StringLen(text))return false;
  string rt=StringSubstr(text,pos,(int)rs);pos+=(int)rs;
  long hash;if(!MDLong610(StringSubstr(text,pos),hash)||hash!=MDHash67(StringSubstr(text,0,pos)))return false;
  MDJournal610 parsed;MDSubmission615K restored;
  if(!MDReplay610(jt,scope,contract,date,instance,parsed)||MDRequestKey615K(parsed,level)!=key||
    !MDDecode615K(rt,key,restored)||restored.attempt!=1||restored.phase!=2)return false;
  journal=jt;receipt=restored;return true;
 }
 public:
 MDEntryBundle615P(){handle=INVALID_HANDLE;}
 ~MDEntryBundle615P(){Close();}
 void Close(){if(handle!=INVALID_HANDLE)FileClose(handle);handle=INVALID_HANDLE;}
 bool Open(string path,const MDJournal610 &expected,int entry_level,long acct,string broker)
 {
  string expected_key=MDRequestKey615K(expected,entry_level);
  if(handle!=INVALID_HANDLE||StringFind(path,"ModeloD_TEST_ONLY_615L4_P_")!=0||!MDStorePath615L4(path)||
    StringFind(path,"\n")>=0||StringFind(path,"\r")>=0||expected_key==""||acct<=0||broker==""||
    StringFind(broker,"\n")>=0||StringFind(broker,"\r")>=0)return false;
  int h=FileOpen(path+".lock",FILE_READ|FILE_WRITE|FILE_BIN|FILE_COMMON);if(h==INVALID_HANDLE)return false;
  handle=h;base=path;level=entry_level;date=expected.date;instance=expected.instance;scope=expected.scope;
  contract=expected.contract;key=expected_key;account=acct;server=broker;return true;
 }
 bool MatchesIdentity(long acct,string broker,string request_key)
 {return handle!=INVALID_HANDLE&&account==acct&&server==broker&&key==request_key;}
 bool Restore(string &journal,MDSubmission615K &receipt)
 {
  if(handle==INVALID_HANDLE||FileIsExist(base+".tmp",FILE_COMMON))return false;
  string text;if(!MDReadStore615L4(base+".head",text))return false;
  return Decode(text,journal,receipt);
 }
 bool Prepare(string journal,const MDExecGate613 &gate,const MDReadiness615M &e,
  MDCommand613 &command,MDDecision615M &decision)
 {
  command.valid=false;decision.plan_allowed=false;decision.transport_allowed=false;decision.reason="PUBLICACAO_NAO_CONFIRMADA";
  if(handle==INVALID_HANDLE){decision.reason="SEM_LOCK_DO_CONJUNTO";return false;}
  if(FileIsExist(base+".head",FILE_COMMON)||FileIsExist(base+".tmp",FILE_COMMON))
  {decision.reason="CONJUNTO_OU_RESIDUO_EXISTENTE_EXIGE_CONCILIACAO";return false;}
  MDJournal610 parsed;
  if(e.account!=account||e.server!=server||!MDReplay610(journal,scope,contract,date,instance,parsed)||MDRequestKey615K(parsed,level)!=key)
  {decision.reason="DIARIO_OU_IDENTIDADE_DIVERGENTE";return false;}
  // Fase de preparacao: permite apenas calcular candidato em memoria.
  // Estas copias NAO sao atestados de persistencia nem permissao de transporte.
  MDReadiness615M planning=e;MDExecGate613 planning_gate=gate;
  planning.state_durable=true;planning_gate.intent_durable=true;
  MDCommand613 planned;
  if(!MDGuardedCommand615M(parsed,level,1,0,0,planning_gate,planning,decision,planned))return false;
  decision.plan_allowed=false;
  MDSubmission615K reserved;bool permit=true;
  if(!MDNew615K(parsed,level,reserved)||!MDSending615K(reserved,permit))return false;
  string receipt=MDEncode615K(reserved);
  string body=Prefix()+IntegerToString(StringLen(journal))+"\n"+journal+IntegerToString(StringLen(receipt))+"\n"+receipt;
  string text=body+IntegerToString(MDHash67(body)),jt;MDSubmission615K check;
  if(receipt==""||!Decode(text,jt,check)||!MDWriteStore615L4(base+".tmp",text)||
    !FileMove(base+".tmp",FILE_COMMON,base+".head",FILE_COMMON))
  {decision.reason="PUBLICACAO_CONJUNTA_FALHOU";return false;}
  string readback;
  if(!MDReadStore615L4(base+".head",readback)||readback!=text||!Restore(jt,check)||jt!=journal)
  {decision.reason="RELEITURA_CONJUNTA_FALHOU";return false;}
  // Diario e reserva comprovados juntos nesta chamada. Reabertura jamais chega aqui.
  command=planned;decision.plan_allowed=true;decision.transport_allowed=false;
  decision.reason="DIARIO_E_RESERVA_PUBLICADOS_PLANO_DE_BANCADA_SEM_TRANSPORTE";return true;
 }
};
#endif
