#ifndef MD_RESERVATION615O
#define MD_RESERVATION615O
#include "ModeloD_Readiness615M.mqh"
#include "ModeloD_Submission615K.mqh"
#include "ModeloD_StateStore615L4.mqh"
// Integracao de bancada. Nao transporta e nunca reconstrui permissao de envio.
class MDReservation615O
{
 private:
 int lock;string path,key,server;long account;
 string Prefix(){return "MD615O\n"+IntegerToString(account)+"\n"+server+"\n";}
 public:
 MDReservation615O(){lock=INVALID_HANDLE;account=0;}
 ~MDReservation615O(){Close();}
 void Close(){if(lock!=INVALID_HANDLE)FileClose(lock);lock=INVALID_HANDLE;}
 bool Open(string base,string request_key,long expected_account,string expected_server)
 {
  if(lock!=INVALID_HANDLE||StringFind(base,"ModeloD_TEST_ONLY_615L4_O_")!=0||
    StringFind(base,"/")>=0||StringFind(base,"\\")>=0||StringFind(base,"..")>=0||
    StringFind(base,"\n")>=0||StringFind(base,"\r")>=0||request_key==""||expected_account<=0||
    expected_server==""||StringFind(expected_server,"\n")>=0||StringFind(expected_server,"\r")>=0)return false;
  int h=FileOpen(base+".lock",FILE_READ|FILE_WRITE|FILE_BIN|FILE_COMMON);
  if(h==INVALID_HANDLE)return false;
  lock=h;path=base+".receipt";key=request_key;account=expected_account;server=expected_server;return true;
 }
 bool Restore(MDSubmission615K &out)
 {
  if(lock==INVALID_HANDLE)return false;
  string text,prefix=Prefix();MDSubmission615K candidate;
  if(!MDReadStore615L4(path,text)||StringFind(text,prefix)!=0||
    !MDDecode615K(StringSubstr(text,StringLen(prefix)),key,candidate))return false;
  // Decode converte tentativa reservada em INCERTA. Nao ha permissao efemera.
  out=candidate;return true;
 }
 bool Reserve(const MDJournal610 &journal,int level,const MDExecGate613 &gate,
  const MDReadiness615M &e,MDCommand613 &command,MDDecision615M &decision)
 {
  command.valid=false;decision.plan_allowed=false;decision.transport_allowed=false;decision.reason="RESERVA_NAO_CONFIRMADA";
  if(lock==INVALID_HANDLE){decision.reason="SEM_LOCK_DA_RESERVA";return false;}
  if(e.account!=account||e.server!=server||MDRequestKey615K(journal,level)!=key)
  {decision.reason="IDENTIDADE_OU_PEDIDO_DIVERGENTE";return false;}
  if(FileIsExist(path,FILE_COMMON)){decision.reason="TENTATIVA_EXISTENTE_EXIGE_CONCILIACAO";return false;}
  MDCommand613 planned;
  if(!MDGuardedCommand615M(journal,level,1,0,0,gate,e,decision,planned))return false;
  // Plano em memoria so e exposto apos gravacao e releitura da reserva.
  decision.plan_allowed=false;
  MDSubmission615K pending;
  if(!MDNew615K(journal,level,pending)){decision.reason="PEDIDO_NAO_RESERVAVEL";return false;}
  bool local_permit=true;
  if(!MDSending615K(pending,local_permit)){decision.reason="FASE_INVALIDA";return false;}
  string encoded=MDEncode615K(pending),text=Prefix()+encoded,readback;
  if(encoded==""||!MDWriteStore615L4(path,text)||!MDReadStore615L4(path,readback)||readback!=text)
  {decision.reason="PERSISTENCIA_DA_RESERVA_NAO_CONFIRMADA";return false;}
  MDSubmission615K restored;
  if(!Restore(restored)||restored.phase!=2||restored.attempt!=pending.attempt)
  {decision.reason="RELEITURA_DA_RESERVA_INVALIDA";return false;}
  command=planned;decision.plan_allowed=true;decision.transport_allowed=false;
  decision.reason="RESERVA_PERSISTIDA_PLANO_DE_BANCADA_SEM_TRANSPORTE";return true;
 }
};
#endif
