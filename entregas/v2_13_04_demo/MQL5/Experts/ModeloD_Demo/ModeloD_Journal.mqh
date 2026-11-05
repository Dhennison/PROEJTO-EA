#ifndef MD_JOURNAL610
#define MD_JOURNAL610
#include "ModeloD_Recovery.mqh"
// Diario append-only: PREPARAR antes de enviar; ACEITE somente por evidencia.
// Hash detecta corrupcao acidental, nao autentica autoria nem impede rollback.
struct MDRequest610
{long id,volume,entry,sl,tp,prepared_msc,ticket,accepted_msc;bool consumed,cancel,close;};
struct MDJournal610
{
 bool valid;string scope,contract;int date,instance,sequence;long hash,last_msc;
 MDRequest610 r[5];
};
struct MDEvent610
{int kind,level;long request,ticket,msc,volume,entry,sl,tp;};
string MDHeader610(string scope,string contract,int date,int instance)
{
 if(!MDToken67(scope)||!MDToken67(contract)||!MDDateValid67(date)||MDMagic67(instance,0)<0)return "";
 string s="MD610|"+scope+"|"+contract+"|"+IntegerToString(date)+"|"+IntegerToString(instance);
 return s+"|"+IntegerToString(MDHash67(s))+"\n";
}
void MDReset610(MDJournal610 &s,string scope,string contract,int date,int instance)
{
 s.valid=false;s.scope=scope;s.contract=contract;s.date=date;s.instance=instance;s.sequence=0;s.hash=0;s.last_msc=0;
 for(int i=0;i<5;i++)
 {s.r[i].id=0;s.r[i].volume=0;s.r[i].entry=0;s.r[i].sl=0;s.r[i].tp=0;s.r[i].prepared_msc=0;
 s.r[i].ticket=0;s.r[i].accepted_msc=0;s.r[i].consumed=false;s.r[i].cancel=false;s.r[i].close=false;}
}
bool MDLong610(string text,long &v)
{
 v=0;if(StringLen(text)<1||StringLen(text)>16)return false;
 for(int i=0;i<StringLen(text);i++){int c=StringGetCharacter(text,i);if(c<48||c>57)return false;
 v=v*10+c-48;if(v>9000000000000000)return false;}
 return true;
}
bool MDApply610(MDJournal610 &s,const MDEvent610 &e)
{
 if(e.level<0||e.level>4||e.kind<1||e.kind>5||e.request<=0||e.msc<=0||e.msc<s.last_msc||
 e.volume<1||e.volume>1000000||e.entry<=0||e.sl<=0||e.tp<=0||e.entry%5!=0||e.sl%5!=0||e.tp%5!=0)return false;
 bool buy=e.level<3;
 if(buy?!(e.sl<e.entry&&e.tp>e.entry):!(e.sl>e.entry&&e.tp<e.entry))return false;
 int k=e.level;
 if(e.kind==1)
 {
  if(s.r[k].id!=0||e.ticket!=0)return false;
  for(int i=0;i<5;i++)if(s.r[i].id==e.request)return false;
  s.r[k].id=e.request;s.r[k].volume=e.volume;s.r[k].entry=e.entry;s.r[k].sl=e.sl;s.r[k].tp=e.tp;s.r[k].prepared_msc=e.msc;
 }
 else
 {
  if(s.r[k].id!=e.request||s.r[k].volume!=e.volume||s.r[k].entry!=e.entry||s.r[k].sl!=e.sl||s.r[k].tp!=e.tp)return false;
  if(e.kind==2)
  {
   if(s.r[k].ticket!=0||e.ticket<=0)return false;
   for(int i=0;i<5;i++)if(s.r[i].ticket==e.ticket)return false;
   s.r[k].ticket=e.ticket;s.r[k].accepted_msc=e.msc;
  }
  else
  {
   if(e.ticket!=s.r[k].ticket)return false;
   s.r[k].consumed=true;if(e.kind==4)s.r[k].cancel=true;if(e.kind==5)s.r[k].close=true;
  }
 }
 s.last_msc=e.msc;return true;
}
string MDLine610(int sequence,long previous,const MDEvent610 &e)
{
 string s=IntegerToString(sequence)+"|"+IntegerToString(e.kind)+"|"+IntegerToString(e.level)+"|"+
 IntegerToString(e.request)+"|"+IntegerToString(e.ticket)+"|"+IntegerToString(e.msc)+"|"+IntegerToString(e.volume)+"|"+
 IntegerToString(e.entry)+"|"+IntegerToString(e.sl)+"|"+IntegerToString(e.tp)+"|"+IntegerToString(previous);
 return s+"|"+IntegerToString(MDHash67(s))+"\n";
}
bool MDReplay610(string text,string scope,string contract,int date,int instance,MDJournal610 &s)
{
 MDReset610(s,scope,contract,date,instance);string header=MDHeader610(scope,contract,date,instance);
 if(header==""||StringLen(text)>524288||StringSubstr(text,0,StringLen(header))!=header)return false;
 s.hash=MDHash67(header);int pos=StringLen(header);
 while(pos<StringLen(text))
 {
  int end=StringFind(text,"\n",pos);if(end<0||end-pos>400||s.sequence>=1000)return false;
  string row=StringSubstr(text,pos,end-pos);long f[12];int start=0,hashpos=-1;
  for(int i=0;i<12;i++)
  {
   int sep=StringFind(row,"|",start);
   if(i<11){if(sep<0||!MDLong610(StringSubstr(row,start,sep-start),f[i]))return false;start=sep+1;if(i==10)hashpos=sep;}
   else {if(sep>=0||!MDLong610(StringSubstr(row,start),f[i]))return false;}
  }
  if(f[0]!=s.sequence+1||f[10]!=s.hash||f[11]!=MDHash67(StringSubstr(row,0,hashpos))||f[1]>5||f[2]>4)return false;
  MDEvent610 e;e.kind=(int)f[1];e.level=(int)f[2];e.request=f[3];e.ticket=f[4];e.msc=f[5];e.volume=f[6];e.entry=f[7];e.sl=f[8];e.tp=f[9];
  if(!MDApply610(s,e))return false;
  s.sequence++;s.hash=f[11];pos=end+1;
 }
 s.valid=true;return true;
}
bool MDAppend610(string current,string scope,string contract,int date,int instance,const MDEvent610 &e,string &next)
{
 next="";MDJournal610 s;if(!MDReplay610(current,scope,contract,date,instance,s)||s.sequence>=1000)return false;
 if(!MDApply610(s,e))return false;
 next=current+MDLine610(s.sequence+1,s.hash,e);MDJournal610 verify;
 return MDReplay610(next,scope,contract,date,instance,verify);
}
// Somente ausencia de solicitacao. Demais gates de dados/tempo/toque sao externos.
bool MDNoRequest610(const MDJournal610 &s,int level)
{return s.valid&&level>=0&&level<5&&s.r[level].id==0;}
#endif
