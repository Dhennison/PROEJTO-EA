#ifndef MD_OBSERVED_RESUME615B
#define MD_OBSERVED_RESUME615B
#include "ModeloD_Stream.mqh"
#include "ModeloD_Recovery.mqh"
// Retomada OBSERVACIONAL. Nunca concede permissao nem recupera ordens.
// O fluxo deve ser reconstruido desde a abertura antes de aplicar o marcador.
string MDDataKey615B(const MDDataEvidence &d)
{
 return IntegerToString(d.date)+"/"+d.contract+"/"+IntegerToString(d.open_msc)+"/"+
 DoubleToString(d.values.high_prev,8)+"/"+DoubleToString(d.values.low_prev,8)+"/"+
 DoubleToString(d.values.close_prev,8)+"/"+DoubleToString(d.values.open_today,8)+"/"+
 DoubleToString(d.values.adjustment,8)+"/"+DoubleToString(d.previous_adjustment,8)+"/"+
 IntegerToString(d.previous_date)+"/"+IntegerToString(d.session.scheduled_open)+"/"+
 IntegerToString(d.session.cutoff)+"/"+IntegerToString(d.session.normal_end);
}
bool MDCommitted615B(const MDStream615 &s)
{return s.ready&&s.audit.valid&&s.blocks>0&&s.block_end==-1&&s.audit.count>0&&s.control.ready&&!s.control.conflict;}
string MDObservedSave615B(const MDStream615 &s,string scope,int instance)
{
 if(!MDCommitted615B(s))return "";
 MDCheckpoint67 c;c.scope=scope;c.contract=s.data.contract;c.date=s.data.date;c.instance=instance;
 c.consumed=0;c.cancel=0;c.close=0;c.inflight=0;c.cutoff=0;c.sequence=s.blocks;
 for(int i=0;i<5;i++)if(s.control.levels[i].opportunity.consumed)c.consumed|=1<<i;
 string encoded=MDEncode67(c);if(encoded=="")return "";
 string body="MD615B\n"+IntegerToString(s.cursor)+"\n"+MDDataKey615B(s.data)+"\n"+encoded+"\n";
 return body+IntegerToString(MDHash67(body));
}
bool MDObservedRestore615B(string text,string scope,int instance,MDStream615 &rebuilt)
{
 if(!MDCommitted615B(rebuilt)||StringLen(text)>4096)return false;
 string f[5];int pos=0,hash_start=0;
 for(int i=0;i<4;i++)
 {int end=StringFind(text,"\n",pos);if(end<0)return false;f[i]=StringSubstr(text,pos,end-pos);pos=end+1;}
 hash_start=pos;f[4]=StringSubstr(text,pos);
 int checksum=0;if(!MDInt67(f[4],checksum)||MDHash67(StringSubstr(text,0,hash_start))!=checksum)return false;
 if(f[0]!="MD615B"||f[2]!=MDDataKey615B(rebuilt.data))return false;
 long cursor=0;if(StringLen(f[1])<1||StringLen(f[1])>16)return false;
 for(int i=0;i<StringLen(f[1]);i++){int ch=StringGetCharacter(f[1],i);if(ch<48||ch>57)return false;cursor=cursor*10+ch-48;}
 if(cursor%60000!=0||cursor<=rebuilt.audit.begin_msc||cursor>rebuilt.cutoff||rebuilt.cursor<cursor)return false;
 MDCheckpoint67 c;if(!MDDecode67(f[3],scope,rebuilt.data.contract,rebuilt.data.date,instance,c))return false;
 // Quantidade de blocos pode variar entre coleta incremental e replay em blocos maiores.
 if(c.cancel!=0||c.close!=0||c.inflight!=0||c.cutoff!=0||c.sequence<1)return false;
 for(int i=0;i<5;i++)if((c.consumed&(1<<i))!=0)rebuilt.control.levels[i].opportunity.consumed=true;
 return true;
}
#endif
