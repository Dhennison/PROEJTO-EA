#ifndef MD_COORDINATOR_FILE615D
#define MD_COORDINATOR_FILE615D
#include "ModeloD_Coordinator.mqh"
bool MDPath615D(string path)
{return (StringFind(path,"ModeloD_SHADOW_615N_")==0||StringFind(path,"ModeloD_TEST_ONLY_615D_")==0)&&StringFind(path,"\\")<0&&StringFind(path,"/")<0&&StringFind(path,"..")<0;}
bool MDRead615D(string path,string &text)
{
 text="";if(!MDPath615D(path))return false;
 int h=FileOpen(path,FILE_READ|FILE_BIN|FILE_ANSI|FILE_COMMON,0,CP_UTF8);if(h==INVALID_HANDLE)return false;
 ulong n=FileSize(h);bool ok=n>0&&n<=65536;
 if(ok){ResetLastError();text=FileReadString(h,(int)n);ok=GetLastError()==0&&StringLen(text)==(int)n;}
 FileClose(h);return ok;
}
// Chamador deve conservar seu lock exclusivo durante toda a sessao.
// expected impede sobrescrever uma versao diferente daquela efetivamente lida.
bool MDStore615D(string path,int lock_handle,string expected,string next)
{
 MDBundle615D b;
 if(lock_handle==INVALID_HANDLE||!MDPath615D(path)||FileIsExist(path+".tmp",FILE_COMMON)||!MDUnpack615D(next,b))return false;
 string current;
 if(FileIsExist(path,FILE_COMMON)){if(expected==""||!MDRead615D(path,current)||current!=expected)return false;}
 else if(expected!="")return false;
 if(expected!="")
 {MDBundle615D old;if(!MDUnpack615D(expected,old)||b.revision!=old.revision+1||StringSubstr(b.journal,0,StringLen(old.journal))!=old.journal)return false;}
 else if(b.revision!=1)return false;
 string temp=path+".tmp";
 int h=FileOpen(temp,FILE_WRITE|FILE_BIN|FILE_ANSI|FILE_COMMON,0,CP_UTF8);if(h==INVALID_HANDLE)return false;
 ResetLastError();uint written=FileWriteString(h,next,StringLen(next));FileFlush(h);
 bool ok=written==(uint)StringLen(next)&&GetLastError()==0;FileClose(h);
 string verify;if(!ok||!MDRead615D(temp,verify)||verify!=next)return false;
 if(!FileMove(temp,FILE_COMMON,path,FILE_COMMON|FILE_REWRITE))return false;
 return MDRead615D(path,verify)&&verify==next;
}
string MDGuardText615D(string scope,const MDDataEvidence &d)
{return "MD615D_SHADOW_INICIADO\n"+scope+"\n"+MDDataKey615B(d);}
bool MDCreateGuard615D(string path,int lock_handle,string text)
{
 if(lock_handle==INVALID_HANDLE||!MDPath615D(path)||FileIsExist(path,FILE_COMMON)||text=="")return false;
 int h=FileOpen(path,FILE_READ|FILE_WRITE|FILE_BIN|FILE_ANSI|FILE_COMMON,0,CP_UTF8);if(h==INVALID_HANDLE)return false;
 bool ok=FileSize(h)==0;
 if(ok){ResetLastError();uint n=FileWriteString(h,text,StringLen(text));FileFlush(h);ok=n==(uint)StringLen(text)&&GetLastError()==0;}
 FileClose(h);string check;return ok&&MDRead615D(path,check)&&check==text;
}
#endif
