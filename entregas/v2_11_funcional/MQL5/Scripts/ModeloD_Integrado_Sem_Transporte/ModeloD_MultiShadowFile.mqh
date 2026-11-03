#ifndef MODELOD_MULTI_SHADOW_FILE
#define MODELOD_MULTI_SHADOW_FILE
#include "ModeloD_CoordinatorFile.mqh"
#include "ModeloD_MultiShadow.mqh"
bool MDPathMultiShadow(string p)
{return (StringFind(p,"ModeloD_SHADOW_615N_MULTI1_")==0||StringFind(p,"ModeloD_TEST_ONLY_615D_MULTI1_")==0)&&MDPath615D(p);}
bool MDWriteMultiShadow(string path,int lock_handle,string expected,string next,string scope,string contract,int date,int instance)
{
 if(lock_handle==INVALID_HANDLE||!MDPathMultiShadow(path)||FileIsExist(path+".tmp",FILE_COMMON))return false;
 MDMultiShadow candidate;if(!MDDecodeMultiShadow(next,scope,contract,date,instance,candidate))return false;
 string current;
 if(FileIsExist(path,FILE_COMMON)){if(expected==""||!MDRead615D(path,current)||current!=expected)return false;}
 else if(expected!="")return false;
 if(expected==""){if(candidate.revision!=1)return false;}
 else
 {
  MDMultiShadow old;
  if(!MDDecodeMultiShadow(expected,scope,contract,date,instance,old)||candidate.revision!=old.revision+1||
     candidate.data_key!=old.data_key||candidate.cursor<old.cursor||
     StringSubstr(candidate.journal,0,StringLen(old.journal))!=old.journal)return false;
 }
 int h=FileOpen(path+".tmp",FILE_WRITE|FILE_BIN|FILE_ANSI|FILE_COMMON,0,CP_UTF8);if(h==INVALID_HANDLE)return false;
 ResetLastError();uint n=FileWriteString(h,next,StringLen(next));FileFlush(h);bool ok=n==(uint)StringLen(next)&&GetLastError()==0;FileClose(h);
 string verify;if(!ok||!MDRead615D(path+".tmp",verify)||verify!=next)return false;
 if(!FileMove(path+".tmp",FILE_COMMON,path,FILE_COMMON|FILE_REWRITE))return false;
 return MDRead615D(path,verify)&&verify==next;
}
// O EA mantem lock exclusivo ao longo da sessao; os dados sao SOMENTE SHADOW.
// O arquivo do diario/fluxo e este arquivo multi NAO formam transacao atomica;
// se o diario estiver mais adiantado, revalidar prefixo e reconstruir; nunca
// aceitar arquivo multi adiantado em relacao ao fluxo reconstruido.
bool MDSyncMultiShadow(string path,int lock_handle,bool &loaded,string &last,string journal,const MDStream615 &stream,int instance,
 long account,string server,const MDSnapshot69 &first,const MDSnapshot69 &second,long now,MDMultiShadow &out,string &why)
{
 why="ARQUIVO_MULTI_BLOQUEADO";
 if(lock_handle==INVALID_HANDLE||!MDPathMultiShadow(path))return false;
 if(FileIsExist(path+".tmp",FILE_COMMON)){why="ARQUIVO_TEMPORARIO_MULTI_PENDENTE";return false;}
 string scope=MDContext612(account,server,instance),guard=path+".init",expected_guard=MDGuardText615D(scope,stream.data);
 if(scope==""||expected_guard=="")return false;
 bool state_exists=FileIsExist(path,FILE_COMMON),guard_exists=FileIsExist(guard,FILE_COMMON);
 if(state_exists!=guard_exists){why="MARCADOR_OU_ESTADO_MULTI_AUSENTE";return false;}
 string disk="",actual_guard="";
 if(state_exists&&(!MDRead615D(path,disk)||!MDRead615D(guard,actual_guard)||actual_guard!=expected_guard))
 {why="ESTADO_OU_MARCADOR_MULTI_ILEGIVEL";return false;}
 if(loaded&&disk!=last){why="ESTADO_MULTI_ALTERADO_EXTERIORMENTE";return false;}
 MDMultiShadow candidate;
 if(!MDAdvanceMultiShadow(disk,journal,stream,instance,account,server,first,second,now,candidate,why))return false;
 if(disk!="")
 {
  candidate.revision--;
  string same=MDEncodeMultiShadow(candidate);
  if(same==disk){out=candidate;last=disk;loaded=true;return true;}
  candidate.revision++;
 }
 string next=MDEncodeMultiShadow(candidate);if(next==""){why="FALHA_CODIFICAR_MULTI";return false;}
 if(!state_exists&&!MDCreateGuard615D(guard,lock_handle,expected_guard)){why="FALHA_CRIAR_MARCADOR_MULTI";return false;}
 if(!MDWriteMultiShadow(path,lock_handle,disk,next,scope,stream.data.contract,stream.data.date,instance))
 {why="FALHA_GRAVAR_OU_RELER_MULTI";return false;}
 last=next;loaded=true;out=candidate;return true;
}
#endif
