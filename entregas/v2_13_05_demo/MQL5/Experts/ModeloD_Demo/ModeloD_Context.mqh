#ifndef MD_CONTEXT612
#define MD_CONTEXT612
#include "ModeloD_Journal.mqh"
// Chave injetiva para servidor ASCII, sem hash truncado de identidade.
string MDContext612(long account,string server,int instance)
{
 if(account<=0||account>9000000000000000||StringLen(server)<1||StringLen(server)>32||MDMagic67(instance,0)<0)return "";
 string hex="0123456789ABCDEF",encoded="";
 for(int i=0;i<StringLen(server);i++)
 {int c=StringGetCharacter(server,i);if(c>127)return "";for(int shift=4;shift>=0;shift-=4)encoded+=StringSubstr(hex,(c>>shift)&15,1);}
 string s="A"+IntegerToString(account)+"S"+encoded+"I"+IntegerToString(instance);
 // Diario 6.10 aceita escopo ate 100 caracteres. Contextos maiores bloqueiam.
 return MDToken67(s)?s:"";
}
struct MDAnchor612 {bool valid;string scope,contract;int date,instance,sequence;long hash;};
string MDAnchorEncode612(const MDJournal610 &s)
{
 if(!s.valid)return "";
 string b="MD612|"+s.scope+"|"+s.contract+"|"+IntegerToString(s.date)+"|"+IntegerToString(s.instance)+"|"+
 IntegerToString(s.sequence)+"|"+IntegerToString(s.hash);
 return b+"|"+IntegerToString(MDHash67(b));
}
bool MDAnchorDecode612(string text,MDAnchor612 &a)
{
 a.valid=false;string f[8];int pos=0,last=-1;
 for(int i=0;i<8;i++)
 {int sep=StringFind(text,"|",pos);if(i<7){if(sep<0)return false;f[i]=StringSubstr(text,pos,sep-pos);pos=sep+1;if(i==6)last=sep;}
 else {if(sep>=0)return false;f[i]=StringSubstr(text,pos);}}
 long hash,check;
 if(f[0]!="MD612"||!MDToken67(f[1])||!MDToken67(f[2])||!MDInt67(f[3],a.date)||!MDInt67(f[4],a.instance)||
 !MDInt67(f[5],a.sequence)||a.sequence>1000||!MDLong610(f[6],hash)||!MDLong610(f[7],check)||
 check!=MDHash67(StringSubstr(text,0,last))||!MDDateValid67(a.date)||MDMagic67(a.instance,0)<0)return false;
 a.scope=f[1];a.contract=f[2];a.hash=hash;a.valid=true;return true;
}
bool MDRecoverAnchored612(string text,const MDAnchor612 &a,MDJournal610 &s,string &reason)
{
 s.valid=false;reason="ANCORA_AUSENTE_OU_INVALIDA";if(!a.valid)return false;
 if(!MDReplay610(text,a.scope,a.contract,a.date,a.instance,s)){reason="DIARIO_INVALIDO";return false;}
 if(s.sequence<a.sequence){s.valid=false;reason="DIARIO_ANTERIOR_A_ANCORA";return false;}
 // Confere prefixo observado. Permite journal mais novo apos crash antes da ancora.
 int pos=StringLen(MDHeader610(a.scope,a.contract,a.date,a.instance));
 for(int i=0;i<a.sequence;i++){int end=StringFind(text,"\n",pos);if(end<0){s.valid=false;return false;}pos=end+1;}
 MDJournal610 prefix;
 if(!MDReplay610(StringSubstr(text,0,pos),a.scope,a.contract,a.date,a.instance,prefix)||prefix.hash!=a.hash)
 {s.valid=false;reason="ANCORA_NAO_CORRESPONDE_AO_PREFIXO";return false;}
 reason=s.sequence==a.sequence?"DIARIO_E_ANCORA_CONFEREM":"DIARIO_MAIS_NOVO_VALIDADO_ATUALIZAR_ANCORA";return true;
}
// Runtime deve manter o handle do lock aberto ate OnDeinit, inclusive entre dias.
// Esta camada nao permite recuperar diario perdido inicializando um novo.
#endif
