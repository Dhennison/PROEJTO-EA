#ifndef MODELOD_MULTI_PERSIST_BANCADA
#define MODELOD_MULTI_PERSIST_BANCADA
#include "ModeloD_MultiPosicao_Bancada.mqh"
#include "ModeloD_StateStore615L4.mqh"
// Armazenamento de bancada, conta e servidor sinteticos, sem permissao de transporte.
// Relogio de teste deve ser da MESMA origem; reinicio real requer ponte comprovada.
string MDMultiEncodeBench(const MDMultiBench &m,long revision,string scope)
{
 if(revision<1||revision>1000000000||scope==""||StringFind(scope,"|")>=0||m.count<1||m.count>16||m.order<=0||m.magic<=0||m.accepted<0||m.symbol==""||StringFind(m.symbol,"|")>=0||!MDDateValid67(m.date))return "";
 string body="MULTI1|"+scope+"|"+IntegerToString(revision)+"|"+IntegerToString(m.count)+"|"+IntegerToString(m.order)+"|"+IntegerToString(m.magic)+"|"+IntegerToString(m.accepted)+"|"+m.symbol+"|"+IntegerToString(m.date)+"|";
 for(int i=0;i<m.count;i++)
 {
  MDState615L2 s;MDInit615L2(s,"BENCH","SAME_CLOCK",m.slots[i].control.ticket);s.management=m.slots[i].control;
  if(m.slots[i].identifier<=0||!MDValid615L2(s))return "";
  for(int j=0;j<i;j++)if(m.slots[j].identifier==m.slots[i].identifier||m.slots[j].control.ticket==s.management.ticket)return "";
  MDProtection p=s.management.protection;
  body+=IntegerToString(m.slots[i].identifier)+"|"+IntegerToString(s.management.ticket)+"|"+IntegerToString(s.management.last_ms+1)+"|"+IntegerToString(p.initial_completed)+"|"+IntegerToString(p.inflight?1:0)+"|"+IntegerToString(p.started?1:0)+"|"+IntegerToString(p.last_started_ms+1)+"|"+IntegerToString(p.sixth_completed_ms+1)+"|";
 }
 return body+IntegerToString(MDHash67(body));
}
bool MDFieldMultiBench(string text,int &pos,string &value)
{int e=StringFind(text,"|",pos);if(e<0)return false;value=StringSubstr(text,pos,e-pos);pos=e+1;return true;}
bool MDNumberMultiBench(string text,int &pos,long &number)
{string s;return MDFieldMultiBench(text,pos,s)&&MDLong610(s,number);}
bool MDMultiDecodeBench(string text,string scope,long minimum,long now,MDMultiBench &result,long &revision)
{
 int pos=0;string tag,readscope,symbol;long ver,count,order,magic,accepted,date;
 if(!MDFieldMultiBench(text,pos,tag)||tag!="MULTI1"||!MDFieldMultiBench(text,pos,readscope)||readscope!=scope||
 !MDNumberMultiBench(text,pos,ver)||!MDNumberMultiBench(text,pos,count)||!MDNumberMultiBench(text,pos,order)||
 !MDNumberMultiBench(text,pos,magic)||!MDNumberMultiBench(text,pos,accepted)||!MDFieldMultiBench(text,pos,symbol)||!MDNumberMultiBench(text,pos,date)||count<1||count>16||ver<minimum)return false;
 MDMultiBench candidate;MDMultiResetBench(candidate);candidate.count=(int)count;candidate.order=order;candidate.magic=magic;candidate.accepted=accepted;candidate.symbol=symbol;candidate.date=(int)date;
 for(int i=0;i<candidate.count;i++)
 {
  long v[8];for(int k=0;k<8;k++)if(!MDNumberMultiBench(text,pos,v[k]))return false;
  if(v[3]>6||v[4]>1||v[5]>1)return false;
  candidate.slots[i].identifier=v[0];MDManagementReset615L(candidate.slots[i].control,v[1]);
  candidate.slots[i].control.last_ms=v[2]-1;
  candidate.slots[i].control.protection.initial_completed=(int)v[3];candidate.slots[i].control.protection.inflight=(v[4]==1);
  candidate.slots[i].control.protection.started=(v[5]==1);candidate.slots[i].control.protection.last_started_ms=v[6]-1;
  candidate.slots[i].control.protection.sixth_completed_ms=v[7]-1;
  if(now<0||candidate.slots[i].control.last_ms>now)return false;
 }
 long hash;if(!MDLong610(StringSubstr(text,pos),hash)||hash!=MDHash67(StringSubstr(text,0,pos)))return false;
 if(MDMultiEncodeBench(candidate,ver,scope)!=text)return false;
 result=candidate;revision=ver;return true;
}
class MDMultiStoreBench
{
 int handle;string base,scope;
 public:
 MDMultiStoreBench(){handle=INVALID_HANDLE;}
 ~MDMultiStoreBench(){Close();}
 void Close(){if(handle!=INVALID_HANDLE)FileClose(handle);handle=INVALID_HANDLE;}
 bool Open(string path,string expected_scope)
 {
  if(handle!=INVALID_HANDLE||!MDStorePath615L4(path)||expected_scope==""||StringFind(expected_scope,"|")>=0)return false;
  int h=FileOpen(path+".lock",FILE_READ|FILE_WRITE|FILE_BIN|FILE_COMMON);if(h==INVALID_HANDLE)return false;
  handle=h;base=path;scope=expected_scope;return true;
 }
 bool Load(long minimum,long now,MDMultiBench &out,long &revision)
 {
  if(handle==INVALID_HANDLE||FileIsExist(base+".tmp",FILE_COMMON))return false;
  string data;if(!MDReadStore615L4(base+".head",data))return false;
  return MDMultiDecodeBench(data,scope,minimum,now,out,revision);
 }
 bool Create(const MDMultiBench &state,long now)
 {
  if(handle==INVALID_HANDLE||FileIsExist(base+".head",FILE_COMMON)||FileIsExist(base+".tmp",FILE_COMMON))return false;
  string data=MDMultiEncodeBench(state,1,scope);MDMultiBench check;long rev;
  if(data==""||!MDMultiDecodeBench(data,scope,1,now,check,rev)||!MDWriteStore615L4(base+".tmp",data))return false;
  if(!FileMove(base+".tmp",FILE_COMMON,base+".head",FILE_COMMON|FILE_REWRITE))return false;
  return Load(1,now,check,rev)&&rev==1;
 }
 bool Commit(const MDMultiBench &before,long old_revision,const MDMultiBench &after,long now)
 {
  MDMultiBench current,check;long rev;
  if(!Load(old_revision,now,current,rev)||rev!=old_revision||MDMultiEncodeBench(current,rev,scope)!=MDMultiEncodeBench(before,rev,scope)||old_revision>=1000000000)return false;
  string data=MDMultiEncodeBench(after,old_revision+1,scope);long v;
  if(data==""||!MDMultiDecodeBench(data,scope,old_revision+1,now,check,v)||!MDWriteStore615L4(base+".tmp",data))return false;
  if(!FileMove(base+".tmp",FILE_COMMON,base+".head",FILE_COMMON|FILE_REWRITE))return false;
  return Load(old_revision+1,now,check,v)&&v==old_revision+1;
 }
};
#endif
