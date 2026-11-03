#ifndef MD_URGENT_FILE615L3
#define MD_URGENT_FILE615L3
#include "ModeloD_Urgent615L3.mqh"
bool MDPairDisk615L3(string path,const MDPair615L3 &s,string key,string domain,MDPair615L3 &readback)
{
 if(StringFind(path,"ModeloD_TEST_ONLY_615L3_")!=0||StringFind(path,"/")>=0||StringFind(path,"\\")>=0||StringFind(path,"..")>=0||FileIsExist(path,FILE_COMMON))return false;
 string text=MDPairEncode615L3(s);if(text=="")return false;
 for(int i=0;i<StringLen(text);i++)if(StringGetCharacter(text,i)>127)return false;
 int h=FileOpen(path,FILE_WRITE|FILE_BIN|FILE_ANSI|FILE_COMMON,0,CP_UTF8);if(h==INVALID_HANDLE)return false;
 ResetLastError();uint n=FileWriteString(h,text,StringLen(text));FileFlush(h);bool ok=n==(uint)StringLen(text)&&GetLastError()==0;FileClose(h);if(!ok)return false;
 h=FileOpen(path,FILE_READ|FILE_BIN|FILE_ANSI|FILE_COMMON,0,CP_UTF8);if(h==INVALID_HANDLE)return false;
 ulong size=FileSize(h);string loaded="";ok=size>0&&size<16384;
 if(ok){ResetLastError();loaded=FileReadString(h,(int)size);ok=GetLastError()==0;}FileClose(h);
 long now=s.cancel_slot.management.last_ms;if(s.close_slot.management.last_ms>now)now=s.close_slot.management.last_ms;if(now<0)now=0;
 return ok&&loaded==text&&MDPairDecode615L3(loaded,key,domain,s.revision,now,readback);
}
#endif
