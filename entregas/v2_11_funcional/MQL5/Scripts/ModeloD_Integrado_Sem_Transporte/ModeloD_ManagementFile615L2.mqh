#ifndef MD_MANAGEMENT_FILE615L2
#define MD_MANAGEMENT_FILE615L2
#include "ModeloD_ManagementState615L2.mqh"
bool MDPath615L2(string path)
{return StringFind(path,"ModeloD_TEST_ONLY_615L2_")==0&&StringFind(path,"/")<0&&StringFind(path,"\\")<0&&StringFind(path,"..")==-1;}
bool MDLoad615L2(string path,string key,string domain,long min_revision,long now,MDState615L2 &s)
{
 if(!MDPath615L2(path))return false;
 int h=FileOpen(path,FILE_READ|FILE_BIN|FILE_ANSI|FILE_COMMON,0,CP_UTF8);if(h==INVALID_HANDLE)return false;
 ulong size=FileSize(h);string text="";bool ok=size>0&&size<8192;
 if(ok){ResetLastError();text=FileReadString(h,(int)size);ok=GetLastError()==0;}
 FileClose(h);return ok&&MDDecode615L2(text,key,domain,min_revision,now,s);
}
bool MDSave615L2(string path,const MDState615L2 &s,MDState615L2 &restored)
{
 if(!MDPath615L2(path)||FileIsExist(path,FILE_COMMON))return false;
 string text=MDEncode615L2(s);if(text=="")return false;
 // ASCII somente: tamanho em caracteres equivale ao numero de bytes deste formato.
 for(int i=0;i<StringLen(text);i++)if(StringGetCharacter(text,i)>127)return false;
 int h=FileOpen(path,FILE_WRITE|FILE_BIN|FILE_ANSI|FILE_COMMON,0,CP_UTF8);if(h==INVALID_HANDLE)return false;
 ResetLastError();uint n=FileWriteString(h,text,StringLen(text));FileFlush(h);bool ok=n==(uint)StringLen(text)&&GetLastError()==0;FileClose(h);
 return ok&&MDLoad615L2(path,s.key,s.clock_domain,s.revision,s.management.last_ms<0?0:s.management.last_ms,restored)&&MDEncode615L2(restored)==text;
}
#endif
