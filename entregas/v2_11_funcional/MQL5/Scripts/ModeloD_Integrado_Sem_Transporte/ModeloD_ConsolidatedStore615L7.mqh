#ifndef MD_CONSOLIDATED_STORE615L7
#define MD_CONSOLIDATED_STORE615L7
#include "ModeloD_ClockRecovery615L5.mqh"
#include "ModeloD_ConfirmResidual615L6.mqh"
// Bancada: estado e mapa temporal publicados juntos. Sem transporte.
string MDEnvelope615L7(const MDPair615L3 &pair,const MDClock615L5 &clock,long account,string server)
{
 if(account<=0||server==""||StringFind(server,"\n")>=0||StringFind(server,"\r")>=0)return "";
 string checkpoint=MDCheckpointEncode615L5(pair,clock);if(checkpoint=="")return "";
 string body="MD615L7\n"+IntegerToString(account)+"\n"+server+"\n"+checkpoint;
 return body+"\n@@ENVELOPE_L7@@\n"+IntegerToString(MDHash67(body));
}
bool MDEnvelopeRead615L7(string text,string key,string logical,long account,string server,MDPair615L3 &pair,MDClock615L5 &clock)
{
 string prefix="MD615L7\n"+IntegerToString(account)+"\n"+server+"\n",sep="\n@@ENVELOPE_L7@@\n";
 if(account<=0||server==""||StringFind(server,"\n")>=0||StringFind(server,"\r")>=0||StringFind(text,prefix)!=0)return false;
 int tail=StringFind(text,sep);long hash;
 if(tail<StringLen(prefix)||!MDLong610(StringSubstr(text,tail+StringLen(sep)),hash)||hash!=MDHash67(StringSubstr(text,0,tail)))return false;
 return MDCheckpointDecode615L5(StringSubstr(text,StringLen(prefix),tail-StringLen(prefix)),key,logical,1,pair,clock);
}
class MDStore615L7
{
 private:
 int handle;string base,key,logical,server;long account;
 bool Publish(const MDPair615L3 &pair,const MDClock615L5 &clock)
 {
  string encoded=MDEnvelope615L7(pair,clock,account,server);MDPair615L3 check;MDClock615L5 timecheck;
  if(encoded==""||!MDEnvelopeRead615L7(encoded,key,logical,account,server,check,timecheck)||FileIsExist(base+".tmp",FILE_COMMON))return false;
  if(!MDWriteStore615L4(base+".tmp",encoded)||!FileMove(base+".tmp",FILE_COMMON,base+".head",FILE_COMMON|FILE_REWRITE))return false;
  string reread;return MDReadStore615L4(base+".head",reread)&&reread==encoded;
 }
 public:
 MDStore615L7(){handle=INVALID_HANDLE;account=0;}
 ~MDStore615L7(){Close();}
 void Close(){if(handle!=INVALID_HANDLE)FileClose(handle);handle=INVALID_HANDLE;}
 bool Open(string path,string expected_key,string domain,long expected_account,string expected_server)
 {
  if(handle!=INVALID_HANDLE||!MDStorePath615L4(path)||StringFind(path,"ModeloD_TEST_ONLY_615L4_L7_")!=0||expected_key==""||domain==""||expected_account<=0||expected_server==""||StringFind(expected_server,"\n")>=0||StringFind(expected_server,"\r")>=0)return false;
  int h=FileOpen(path+".lock",FILE_READ|FILE_WRITE|FILE_BIN|FILE_COMMON);if(h==INVALID_HANDLE)return false;
  handle=h;base=path;key=expected_key;logical=domain;account=expected_account;server=expected_server;return true;
 }
 bool Load(MDPair615L3 &pair,MDClock615L5 &clock)
 {
  if(handle==INVALID_HANDLE||FileIsExist(base+".tmp",FILE_COMMON))return false;
  string text;if(!MDReadStore615L4(base+".head",text))return false;
  return MDEnvelopeRead615L7(text,key,logical,account,server,pair,clock);
 }
 bool Create(const MDPair615L3 &pair,const MDClock615L5 &clock)
 {
  if(handle==INVALID_HANDLE||pair.revision!=1||FileIsExist(base+".head",FILE_COMMON)||FileIsExist(base+".tmp",FILE_COMMON))return false;
  return Publish(pair,clock);
 }
 bool Commit(const MDPair615L3 &expected,const MDClock615L5 &oldclock,const MDPair615L3 &next,const MDClock615L5 &newclock)
 {
  if(handle==INVALID_HANDLE||expected.revision>=1000000000||next.revision!=expected.revision+1||newclock.lo<oldclock.lo||newclock.hi<oldclock.hi)return false;
  MDPair615L3 current;MDClock615L5 currentclock;
  if(!Load(current,currentclock)||MDEnvelope615L7(current,currentclock,account,server)!=MDEnvelope615L7(expected,oldclock,account,server))return false;
  // Transicoes de negocio e evidencia temporal sao validadas pelo coordenador.
  return Publish(next,newclock);
 }
};
// Somente sucesso apos publicacao permite ao chamador adotar o novo estado.
// Nenhuma destas funcoes concede permissao de enviar ordens.
bool MDConfirmPersist615L7(MDStore615L7 &store,const MDPair615L3 &old,const MDClock615L5 &clock,const MDBinding615L6 &binding,
 string journal,string scope,string contract,int date,int instance,int level,const MDSnapshot69 &snapshot,long account,string server,
 long market_now,string raw_domain,long raw_now,bool fresh,MDPair615L3 &out,MDClock615L5 &outclock,double &residual)
{
 residual=0;MDPair615L3 candidate;MDClock615L5 timecandidate;double remaining;
 if(!MDClockAdvance615L5(clock,raw_domain,raw_now,timecandidate)||
 !MDConfirmClose615L6(old,binding,journal,scope,contract,date,instance,level,snapshot,account,server,market_now,fresh,true,candidate,remaining)||
 !store.Commit(old,clock,candidate,timecandidate))return false;
 out=candidate;outclock=timecandidate;residual=remaining;return true;
}
bool MDRebasePersist615L7(MDStore615L7 &store,const MDPair615L3 &old,const MDClock615L5 &clock,string new_domain,long raw_now,
 long utc_lo,long utc_hi,bool certified,MDPair615L3 &out,MDClock615L5 &outclock)
{
 if(old.revision>=1000000000)return false;
 MDClock615L5 timecandidate;
 if(!MDClockRebase615L5(clock,new_domain,raw_now,utc_lo,utc_hi,certified,timecandidate))return false;
 MDPair615L3 candidate=old;candidate.revision++;
 if(!store.Commit(old,clock,candidate,timecandidate))return false;
 out=candidate;outclock=timecandidate;return true;
}
#endif
