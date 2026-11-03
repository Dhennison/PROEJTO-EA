#ifndef MD_PREVIEW_INTEGRADO_FILE
#define MD_PREVIEW_INTEGRADO_FILE
#include "ModeloD_PreviewIntegrado.mqh"
#include "ModeloD_CoordinatorFile.mqh"
// Este checkpoint salva um resumo consultivo e seu diario de observacao.
// Nao e reserva operacional nem comprovante de tentativa enviada.
string MDPreviewStamp(const MDStream615 &s,const MDPreviewIntegrado &p)
{
 if(!p.valid||p.plans<0||p.chains<0)return "";
 string body="MD_PREVIEW_INTEGRADO_1\n"+MDDataKey615B(s.data)+"\n"+IntegerToString(s.cursor)+"\n"+
  IntegerToString(p.chains)+"\n"+IntegerToString(p.plans)+"\n"+IntegerToString(p.cancel)+"\n"+
  IntegerToString(p.protect)+"\n"+IntegerToString(p.close)+"\n"+
  IntegerToString(MDHash67(p.lines+p.journal_candidate))+"\n";
 return body+IntegerToString(MDHash67(body));
}
bool MDPreviewReadStamp(string text,const MDStream615 &s,long &cursor)
{
 string f[10];int pos=0;
 for(int i=0;i<9;i++){int end=StringFind(text,"\n",pos);if(end<0)return false;f[i]=StringSubstr(text,pos,end-pos);pos=end+1;}
 f[9]=StringSubstr(text,pos);long hash,n[7];
 if(f[0]!="MD_PREVIEW_INTEGRADO_1"||f[1]!=MDDataKey615B(s.data)||
    !MDLong610(f[9],hash)||hash!=MDHash67(StringSubstr(text,0,pos)))return false;
 for(int i=0;i<7;i++)if(!MDLong610(f[i+2],n[i]))return false;
 if(n[0]<=0||n[0]>s.cursor||n[1]>5||n[2]>85||n[3]+n[4]+n[5]!=n[2])return false;
 cursor=n[0];return true;
}
bool MDPreviewSync(string path,int lock_handle,bool &loaded,string &last,string journal,const MDStream615 &s,
 const MDPreviewIntegrado &preview,string scope,int instance,long &revision,string &reason)
{
 reason="CHECKPOINT_PREVIA_BLOQUEADO";revision=0;
 if(lock_handle==INVALID_HANDLE||!MDPath615D(path)||!preview.valid||preview.cursor!=s.cursor||
    preview.data_key!=MDDataKey615B(s.data)||preview.source_journal!=journal||FileIsExist(path+".tmp",FILE_COMMON))return false;
 string guard=path+".init",guard_value=MDGuardText615D(scope,s.data),disk="",actual="";
 bool has=FileIsExist(path,FILE_COMMON),has_guard=FileIsExist(guard,FILE_COMMON);
 if(has!=has_guard){reason="PAR_PREVIA_INCOMPLETO";return false;}
 if(has&&(!MDRead615D(path,disk)||!MDRead615D(guard,actual)||actual!=guard_value))
 {reason="ESTADO_OU_MARCADOR_PREVIA_INVALIDO";return false;}
 if(loaded&&disk!=last){reason="ESTADO_PREVIA_ALTERADO";return false;}
 MDBundle615D old;long cursor=0;
 if(has&&(!MDUnpack615D(disk,old)||!MDPreviewReadStamp(old.observed,s,cursor)||
    StringSubstr(journal,0,StringLen(old.journal))!=old.journal))
 {reason="PREVIA_ANTERIOR_OU_DIARIO_DIVERGENTE";return false;}
 MDJournal610 parsed;if(!MDReplay610(journal,scope,s.data.contract,s.data.date,instance,parsed))return false;
 string stamp=MDPreviewStamp(s,preview);if(stamp=="")return false;
 if(has&&old.journal==journal&&old.observed==stamp)
 {loaded=true;last=disk;revision=old.revision;reason="PREVIA_JA_GRAVADA";return true;}
 MDBundle615D next;next.revision=has?old.revision+1:1;next.journal=journal;next.observed=stamp;
 string encoded=MDPack615D(next);if(encoded=="")return false;
 if(!has&&!MDCreateGuard615D(guard,lock_handle,guard_value)){reason="FALHA_CRIAR_MARCADOR_PREVIA";return false;}
 if(!MDStore615D(path,lock_handle,disk,encoded)){reason="FALHA_GRAVAR_PREVIA";return false;}
 loaded=true;last=encoded;revision=next.revision;reason=has?"PREVIA_ATUALIZADA":"PREVIA_CRIADA";return true;
}
#endif
