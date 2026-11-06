#ifndef MD_SESSOES_VERIFICADAS21305
#define MD_SESSOES_VERIFICADAS21305
#include "ModeloD_Session.mqh"
bool MDSessionTime21305(string text,int &value) {
 if(StringLen(text)!=8||StringSubstr(text,2,1)!=":"||StringSubstr(text,5,1)!=":"||
  !MDB3Digits(StringSubstr(text,0,2))||!MDB3Digits(StringSubstr(text,3,2))||!MDB3Digits(StringSubstr(text,6,2)))return false;
 int h=(int)StringToInteger(StringSubstr(text,0,2)),m=(int)StringToInteger(StringSubstr(text,3,2)),s=(int)StringToInteger(StringSubstr(text,6,2));
 if(h>23||m>59||s>59)return false;value=h*3600+m*60+s;return true;
}
// 1=explicit reviewed row for this exact date/contract; 0=no such row;
// -1=invalid file, which must never silently fall back to regular hours.
int MDSessionConfig21305(int date,string contract,MDSessionRule &out) {
 MDSessionClear(out);string path="ModeloD_Sessoes_Verificadas.csv";
 if(!FileIsExist(path,FILE_COMMON))return 0;
 int file=FileOpen(path,FILE_READ|FILE_TXT|FILE_ANSI|FILE_COMMON,0,CP_UTF8);if(file==INVALID_HANDLE)return -1;
 if(FileSize(file)>65536){FileClose(file);return -1;}
 string header=MDB3Trim(FileReadString(file));
 if(StringLen(header)>0&&StringGetCharacter(header,0)==65279)header=StringSubstr(header,1);
 if(header!="Data;Contrato;Abertura;Fim;Zeragem;Verificado;Fonte"){FileClose(file);return -1;}
 string seen="|";int rows=0,lines=0,result=0;
 while(!FileIsEnding(file)){
  if(++lines>1024){FileClose(file);return -1;}
  string row=MDB3Trim(FileReadString(file));if(row=="")continue;
  if(++rows>512){FileClose(file);return -1;}
  string values[7];int from=0;
  for(int c=0;c<7;c++){
   int stop=c==6?StringLen(row):StringFind(row,";",from);
   if(stop<from){FileClose(file);return -1;}
   values[c]=MDB3Trim(StringSubstr(row,from,stop-from));from=stop+1;
  }
  int d=(int)StringToInteger(values[0]),opening=0,ending=0,cutoff=0;MDSessionRule rule;
  string key=values[0]+"_"+values[1]+"|";
  if(StringLen(values[0])!=8||!MDB3Digits(values[0])||!MDB3Symbol(values[1])||MDWINLastTrading2026(values[1])<d||
     values[5]!="SIM"||values[6]==""||StringLen(values[6])>256||StringFind(values[6],";")>=0||
     StringFind(seen,"|"+key)>=0||!MDSessionTime21305(values[2],opening)||!MDSessionTime21305(values[3],ending)||
     !MDSessionTime21305(values[4],cutoff)||!MDSessionSet(d,opening,ending,cutoff,true,"CSV_REVISADO;"+values[6],rule)){
   FileClose(file);return -1;
  }
  seen+=key;if(d==date&&values[1]==contract){out=rule;result=1;}
 }
 FileClose(file);return result;
}
bool MDKnownSpecial21305(int date) {
 // Ash Wednesday 2026 is not a regular 09h session. No timetable is inferred.
 return date==20260218;
}
#endif
