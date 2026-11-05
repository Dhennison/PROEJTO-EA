#ifndef MODELOD_B3FILE_MQH
#define MODELOD_B3FILE_MQH
#include "ModeloD_B3.mqh"
bool MDB3ReadAt210(string path,bool common,MDB3File &data,string &reason)
{
   data.validated=false; data.count=0; reason="";
   ResetLastError();
   int flags=FILE_READ|FILE_TXT|FILE_ANSI|FILE_SHARE_READ;
   if(common)flags|=FILE_COMMON;
   int h=FileOpen(path,flags,0,CP_UTF8);
   if(h==INVALID_HANDLE) return MDB3Fail(reason,"ARQUIVO_INDISPONIVEL: "+IntegerToString(GetLastError()));
   string text=""; bool ok=true; int lines=0;
   while(!FileIsEnding(h))
   {
      ResetLastError(); string line=FileReadString(h);
      if(GetLastError()!=0) { ok=false; reason="ERRO_LEITURA"; break; }
      if(lines==0 && StringLen(line)>0 && StringGetCharacter(line,0)==65279) line=StringSubstr(line,1);
      text+=line+"\n";
      if(++lines>2000 || StringLen(text)>131072) { ok=false; reason="ARQUIVO_EXCESSIVO"; break; }
   }
   FileClose(h);
   if(!ok) return false;
   ok=MDB3Parse(text,data,reason);
   if(!ok) data.count=0;
   return ok;
}
bool MDB3ReadOperational(MDB3File &data,string &reason)
{return MDB3ReadAt210("ajuste_b3.txt",true,data,reason);}
#endif
