#ifndef MD_RECOVERY67
#define MD_RECOVERY67
// Predicados puros. O adaptador deve construir evidencias por simbolo/data/nivel
// e correlacionar ordem, deal e POSITION_IDENTIFIER. Magic sozinho e candidato.
long MDMagic67(const int instance,const int level)
{return instance>=1 && instance<=9999 && level>=0 && level<5 ? 260614000+(long)instance*10+level : -1;}
int MDLevelMagic67(const long magic,const int instance)
{if(instance<1||instance>9999)return -1;long v=magic-MDMagic67(instance,0);return v>=0&&v<5?(int)v:-1;}
struct MDCheckpoint67
{
   string scope,contract;
   int date,instance,consumed,cancel,close,inflight,cutoff,sequence;
};
struct MDRecoveryEvidence67
{
   bool server_complete,ownership_resolved,history_complete,request_resolved;
   bool had_entry,touched,accepted_before_touch,boundary_after_accept,exit_after_entry,cutoff;
   int pending_count,position_count;
};
struct MDRecoveryResult67
{
   bool consumed,block_new,cancel_pending,close_positions,protect_positions;
};
void MDRecover67(const MDCheckpoint67 &local,const MDRecoveryEvidence67 &e,const int level,MDRecoveryResult67 &r)
{
   r.consumed=false;r.block_new=true;r.cancel_pending=false;r.close_positions=false;r.protect_positions=false;
   if(level<0||level>=5 || e.pending_count<0 || e.position_count<0)return;
   int bit=1<<level;
   r.consumed=(local.consumed&bit)!=0 || e.had_entry || e.touched || e.position_count>0;
   // Sem propriedade comprovada nao produzir intencao mutante sobre candidatos.
   if(!e.ownership_resolved)return;
   bool cutoff=e.cutoff || local.cutoff==1;
   r.cancel_pending=e.pending_count>0 && (cutoff || (local.cancel&bit)!=0 ||
      !e.history_complete || !e.accepted_before_touch || e.boundary_after_accept);
   r.close_positions=e.position_count>0 && (cutoff || (local.close&bit)!=0 || e.exit_after_entry);
   r.protect_positions=e.position_count>0 && !r.close_positions;
   if(r.cancel_pending || cutoff)r.consumed=true;
   bool unknown_request=(local.inflight&bit)!=0 && !e.request_resolved;
   r.block_new=!e.server_complete || !e.history_complete || !e.request_resolved ||
      unknown_request || r.consumed || cutoff || e.pending_count>0 || e.position_count>0 ||
      (local.cancel&bit)!=0 || (local.close&bit)!=0;
}
// Hash para detectar arquivo incompleto/corrompido, NAO assinatura criptografica.
long MDHash67(const string text)
{long h=17;for(int i=0;i<StringLen(text);i++)h=(h*131+StringGetCharacter(text,i))%1000000007;return h;}
bool MDToken67(const string s)
{
   if(StringLen(s)<1 || StringLen(s)>100)return false;
   for(int i=0;i<StringLen(s);i++)
   {int c=StringGetCharacter(s,i);if(!((c>=48&&c<=57)||(c>=65&&c<=90)||(c>=97&&c<=122)||c==95||c==45))return false;}
   return true;
}
bool MDDateValid67(const int date)
{
   int y=date/10000,m=(date/100)%100,d=date%100;
   if(y<2020||y>2099||m<1||m>12||d<1)return false;
   int days[12]={31,28,31,30,31,30,31,31,30,31,30,31};
   if(m==2 && y%4==0) return d<=29;
   return d<=days[m-1];
}
bool MDCheckpointValid67(const MDCheckpoint67 &s)
{
   return MDToken67(s.scope)&&MDToken67(s.contract)&&MDDateValid67(s.date)&&s.instance>=1&&s.instance<=9999&&
      s.consumed>=0&&s.consumed<=31&&s.cancel>=0&&s.cancel<=31&&s.close>=0&&s.close<=31&&s.inflight>=0&&s.inflight<=31&&
      (s.cutoff==0||s.cutoff==1)&&s.sequence>=0;
}
string MDEncode67(const MDCheckpoint67 &s)
{
   if(!MDCheckpointValid67(s))return "";
   string body="MD67|"+s.scope+"|"+s.contract+"|"+IntegerToString(s.date)+"|"+IntegerToString(s.instance)+"|"+
      IntegerToString(s.consumed)+"|"+IntegerToString(s.cancel)+"|"+IntegerToString(s.close)+"|"+
      IntegerToString(s.inflight)+"|"+IntegerToString(s.cutoff)+"|"+IntegerToString(s.sequence);
   return body+"|"+IntegerToString(MDHash67(body));
}
bool MDInt67(const string s,int &out)
{
   if(StringLen(s)<1||StringLen(s)>10)return false;
   long value=0;
   for(int i=0;i<StringLen(s);i++)
   {int c=StringGetCharacter(s,i);if(c<48||c>57)return false;value=value*10+c-48;if(value>2147483647)return false;}
   out=(int)value;return true;
}
bool MDDecode67(const string text,const string expected_scope,const string expected_contract,
   const int expected_date,const int expected_instance,MDCheckpoint67 &out)
{
   // Saida zerada nao deve ser usada se retorno=false. Nunca autoriza reentrada.
   out.scope="";out.contract="";out.date=0;out.instance=0;out.consumed=31;out.cancel=31;out.close=31;out.inflight=31;out.cutoff=1;out.sequence=0;
   string fields[12];int pos=0,checksum_start=-1;
   for(int i=0;i<12;i++)
   {
      int next=StringFind(text,"|",pos);
      if(i<11){if(next<0)return false;fields[i]=StringSubstr(text,pos,next-pos);pos=next+1;if(i==10)checksum_start=next;}
      else {if(next>=0)return false;fields[i]=StringSubstr(text,pos);}
   }
   if(fields[0]!="MD67" || fields[1]!=expected_scope || fields[2]!=expected_contract)return false;
   MDCheckpoint67 s;s.scope=fields[1];s.contract=fields[2];int checksum=0;
   if(!MDInt67(fields[3],s.date)||!MDInt67(fields[4],s.instance)||!MDInt67(fields[5],s.consumed)||
      !MDInt67(fields[6],s.cancel)||!MDInt67(fields[7],s.close)||!MDInt67(fields[8],s.inflight)||
      !MDInt67(fields[9],s.cutoff)||!MDInt67(fields[10],s.sequence)||!MDInt67(fields[11],checksum))return false;
   if(s.date!=expected_date||s.instance!=expected_instance||!MDCheckpointValid67(s)||MDHash67(StringSubstr(text,0,checksum_start))!=checksum)return false;
   out=s;return true;
}
#endif
