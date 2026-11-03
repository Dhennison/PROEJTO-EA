#ifndef MD_STATE_STORE615L4
#define MD_STATE_STORE615L4
#include "ModeloD_Urgent615L3.mqh"
bool MDStorePath615L4(string p)
{return StringFind(p,"ModeloD_TEST_ONLY_615L4_")==0&&StringFind(p,"/")<0&&StringFind(p,"\\")<0&&StringFind(p,"..")<0;}
bool MDReadStore615L4(string path,string &text)
{
 text="";if(!MDStorePath615L4(path))return false;
 int h=FileOpen(path,FILE_READ|FILE_BIN|FILE_ANSI|FILE_COMMON,0,CP_UTF8);if(h==INVALID_HANDLE)return false;
 ulong size=FileSize(h);bool ok=size>0&&size<16384;
 if(ok){ResetLastError();text=FileReadString(h,(int)size);ok=GetLastError()==0&&StringLen(text)==(int)size;}
 FileClose(h);return ok;
}
// Usada para candidatos temporarios de bancada e injecao de falhas no teste.
bool MDWriteStore615L4(string path,string text)
{
 if(!MDStorePath615L4(path)||text=="")return false;
 for(int i=0;i<StringLen(text);i++)if(StringGetCharacter(text,i)>127)return false;
 int h=FileOpen(path,FILE_WRITE|FILE_BIN|FILE_ANSI|FILE_COMMON,0,CP_UTF8);if(h==INVALID_HANDLE)return false;
 ResetLastError();uint n=FileWriteString(h,text,StringLen(text));FileFlush(h);bool ok=n==(uint)StringLen(text)&&GetLastError()==0;FileClose(h);
 string read;return ok&&MDReadStore615L4(path,read)&&read==text;
}
class MDStore615L4
{
 private:
 int handle;string base,key,domain;
 bool Promote(string text,long revision,long now)
 {
  MDPair615L3 check;
  if(!MDPairDecode615L3(text,key,domain,revision,now,check)||check.revision!=revision)return false;
  if(FileIsExist(base+".tmp",FILE_COMMON))return false;
  if(!MDWriteStore615L4(base+".tmp",text))return false;
  // Nao promete atomicidade contra queda de energia. Residuo tmp bloqueia retomada.
  if(!FileMove(base+".tmp",FILE_COMMON,base+".head",FILE_COMMON|FILE_REWRITE))return false;
  string reread;return MDReadStore615L4(base+".head",reread)&&reread==text;
 }
 public:
 MDStore615L4(){handle=INVALID_HANDLE;}
 ~MDStore615L4(){Close();}
 void Close(){if(handle!=INVALID_HANDLE)FileClose(handle);handle=INVALID_HANDLE;}
 bool Open(string path,string expected_key,string clock_domain)
 {
  if(handle!=INVALID_HANDLE||!MDStorePath615L4(path)||expected_key==""||clock_domain=="")return false;
  int h=FileOpen(path+".lock",FILE_READ|FILE_WRITE|FILE_BIN|FILE_COMMON);
  if(h==INVALID_HANDLE)return false;
  handle=h;base=path;key=expected_key;domain=clock_domain;return true;
 }
 bool Load(long now,MDPair615L3 &out)
 {
  if(handle==INVALID_HANDLE||FileIsExist(base+".tmp",FILE_COMMON))return false;
  string text;if(!MDReadStore615L4(base+".head",text))return false;
  return MDPairDecode615L3(text,key,domain,1,now,out);
 }
 bool Create(const MDPair615L3 &s,long now)
 {
  if(handle==INVALID_HANDLE||s.revision!=1||FileIsExist(base+".head",FILE_COMMON)||FileIsExist(base+".tmp",FILE_COMMON))return false;
  return Promote(MDPairEncode615L3(s),1,now);
 }
 bool Commit(const MDPair615L3 &expected,const MDPair615L3 &next,long now)
 {
  if(handle==INVALID_HANDLE||expected.revision>=1000000000||next.revision!=expected.revision+1)return false;
  MDPair615L3 current;if(!Load(now,current)||MDPairEncode615L3(current)!=MDPairEncode615L3(expected))return false;
  // Persistencia nao valida transicao de negocio; candidato vem do coordenador.
  return Promote(MDPairEncode615L3(next),next.revision,now);
 }
};
#endif
