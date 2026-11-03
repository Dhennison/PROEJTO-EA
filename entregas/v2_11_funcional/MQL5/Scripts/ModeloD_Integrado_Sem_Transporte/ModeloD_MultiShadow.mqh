#ifndef MODELOD_MULTI_SHADOW
#define MODELOD_MULTI_SHADOW
#include "ModeloD_Coordinator.mqh"
#include "ModeloD_MultiPersist_Bancada.mqh"
// Envelope de observacao. Nao transporta ordens, reservas nem confirma protecao.
struct MDMultiShadow {string scope,contract,data_key,journal;int date,instance;long revision,cursor;MDMultiBench level[5];double volume[5][16],entered[5][16],exited[5][16];};
void MDResetMultiShadow(MDMultiShadow &s)
{
 s.scope="";s.contract="";s.data_key="";s.journal="";s.date=0;s.instance=0;s.revision=0;s.cursor=0;
 for(int i=0;i<5;i++){MDMultiResetBench(s.level[i]);for(int k=0;k<16;k++){s.volume[i][k]=0;s.entered[i][k]=0;s.exited[i][k]=0;}}
}
bool MDShadowColdControl(const MDManagement615L &m)
{
 MDProtection p=m.protection;
 return m.ticket>0&&m.last_ms==-1&&!p.started&&!p.inflight&&p.initial_completed==0&&p.last_started_ms==-1&&p.sixth_completed_ms==-1;
}
// Esta versao registra somente controladores observacionais virgens; recusa
// tentativa em andamento, pois nao produz evidencia real da chamada.
string MDEncodeMultiShadow(const MDMultiShadow &s)
{
 if(s.revision<1||s.revision>1000000||!MDToken67(s.scope)||!MDToken67(s.contract)||!MDDateValid67(s.date)||
    MDMagic67(s.instance,0)<0||s.cursor<=0||s.data_key==""||StringFind(s.data_key,"\n")>=0||StringLen(s.journal)>50000)return "";
 MDJournal610 j;if(!MDReplay610(s.journal,s.scope,s.contract,s.date,s.instance,j))return "";
 string part[5];int total=StringLen(s.journal),total_positions=0;
 for(int i=0;i<5;i++)
 {
  part[i]="";int count=s.level[i].count;
  if(count<0||count>16)return "";
  if(count>0)
  {
   total_positions+=count;if(total_positions>64)return "";
   double sum_volume=0;
   if(j.r[i].id==0||j.r[i].ticket<=0||s.level[i].order!=j.r[i].ticket||s.level[i].magic!=MDMagic67(s.instance,i)||
      s.level[i].accepted!=j.r[i].accepted_msc||s.level[i].symbol!=s.contract||s.level[i].date!=s.date)return "";
   for(int k=0;k<count;k++)
   {
    if(!MDShadowColdControl(s.level[i].slots[k].control)||!MDVolume68(s.volume[i][k])||s.volume[i][k]<=0||
       !MDVolume68(s.entered[i][k])||s.entered[i][k]<=0||!MDVolume68(s.exited[i][k])||
       !MDEqual68(s.entered[i][k]-s.exited[i][k],s.volume[i][k]))return "";
    string qty_text=DoubleToString(s.volume[i][k],8),in_text=DoubleToString(s.entered[i][k],8),out_text=DoubleToString(s.exited[i][k],8);
    if(MathAbs(StringToDouble(qty_text)-s.volume[i][k])>0.00000001||
       MathAbs(StringToDouble(in_text)-s.entered[i][k])>0.00000001||MathAbs(StringToDouble(out_text)-s.exited[i][k])>0.00000001)return "";
    sum_volume+=s.entered[i][k];
    for(int q=0;q<i;q++)for(int t=0;t<s.level[q].count;t++)
     if(s.level[i].slots[k].identifier==s.level[q].slots[t].identifier||
        s.level[i].slots[k].control.ticket==s.level[q].slots[t].control.ticket)return "";
   }
   if(sum_volume>(double)j.r[i].volume+0.00000001)return "";
   part[i]=MDMultiEncodeBench(s.level[i],1,s.scope);if(part[i]=="")return "";
   part[i]+="~";for(int k=0;k<count;k++)part[i]+=DoubleToString(s.volume[i][k],8)+","+
    DoubleToString(s.entered[i][k],8)+","+DoubleToString(s.exited[i][k],8)+",";
  }
  total+=StringLen(part[i]);
 }
 if(total>60000)return "";
 string body="MD_MULTI_SHADOW_1\n"+IntegerToString(s.revision)+"\n"+s.scope+"\n"+s.contract+"\n"+
  IntegerToString(s.date)+"\n"+IntegerToString(s.instance)+"\n"+IntegerToString(s.cursor)+"\n"+s.data_key+"\n"+
  IntegerToString(StringLen(s.journal))+"\n";
 for(int i=0;i<5;i++)body+=IntegerToString(StringLen(part[i]))+"\n";
 body+=s.journal;for(int i=0;i<5;i++)body+=part[i];
 if(StringLen(body)>64000)return "";
 return body+"\n"+IntegerToString(MDHash67(body));
}
bool MDShadowAmount(string text,double &value)
{
 int n=StringLen(text),dot=n-9;
 if(n<10||n>24||dot<1||StringSubstr(text,dot,1)!=".")return false;
 if(dot>1&&StringSubstr(text,0,1)=="0")return false;
 for(int i=0;i<n;i++)if(i!=dot)
 {int c=StringGetCharacter(text,i);if(c<48||c>57)return false;}
 value=StringToDouble(text);
 return MDVolume68(value)&&DoubleToString(value,8)==text;
}
bool MDDecodeMultiShadow(string text,string expected_scope,string expected_contract,int expected_date,int expected_instance,MDMultiShadow &out)
{
 if(StringLen(text)>65536)return false;
 string f[14];int pos=0;
 for(int i=0;i<14;i++){int end=StringFind(text,"\n",pos);if(end<0)return false;f[i]=StringSubstr(text,pos,end-pos);pos=end+1;}
 long rev,date,instance,cursor,nj,lens[5];
 if(f[0]!="MD_MULTI_SHADOW_1"||f[2]!=expected_scope||f[3]!=expected_contract||!MDLong610(f[1],rev)||!MDLong610(f[4],date)||
    !MDLong610(f[5],instance)||!MDLong610(f[6],cursor)||!MDLong610(f[8],nj)||date!=expected_date||instance!=expected_instance||nj<1||nj>50000)return false;
 int total=(int)nj;
 for(int i=0;i<5;i++){if(!MDLong610(f[9+i],lens[i])||lens[i]>16000)return false;total+=(int)lens[i];}
 if(total>60000||pos+total>=StringLen(text)||StringSubstr(text,pos+total,1)!="\n")return false;
 long hash;if(!MDLong610(StringSubstr(text,pos+total+1),hash)||hash!=MDHash67(StringSubstr(text,0,pos+total)))return false;
 MDMultiShadow candidate;MDResetMultiShadow(candidate);candidate.scope=f[2];candidate.contract=f[3];candidate.date=(int)date;
 candidate.instance=(int)instance;candidate.revision=rev;candidate.cursor=cursor;candidate.data_key=f[7];
 candidate.journal=StringSubstr(text,pos,(int)nj);pos+=(int)nj;
 for(int i=0;i<5;i++)if(lens[i]>0)
 {
  string part=StringSubstr(text,pos,(int)lens[i]);long partrev=0;int sep=StringFind(part,"~");
  if(sep<=0||!MDMultiDecodeBench(StringSubstr(part,0,sep),candidate.scope,1,0,candidate.level[i],partrev)||partrev!=1)return false;
  int vp=sep+1;
  for(int k=0;k<candidate.level[i].count;k++)
  {
   double amounts[3];
   for(int q=0;q<3;q++)
   {
    int comma=StringFind(part,",",vp);if(comma<0)return false;
    string amount=StringSubstr(part,vp,comma-vp);double v=0;
    if(!MDShadowAmount(amount,v))return false;
    amounts[q]=v;vp=comma+1;
   }
   candidate.volume[i][k]=amounts[0];candidate.entered[i][k]=amounts[1];candidate.exited[i][k]=amounts[2];
  }
  if(vp!=StringLen(part))return false;
  pos+=(int)lens[i];
 }
 if(MDEncodeMultiShadow(candidate)!=text)return false;
 out=candidate;return true;
}
int MDShadowTotal(const MDMultiShadow &s)
{int n=0;for(int i=0;i<5;i++)n+=s.level[i].count;return n;}
// Recebe o diario e DUAS coletas, reconcilia cada origem comprovada e monta
// uma copia candidata. Qualquer erro preserva integralmente o estado anterior.
bool MDAdvanceMultiShadow(string previous,string journal,const MDStream615 &stream,int instance,long account,string server,
 const MDSnapshot69 &first,const MDSnapshot69 &second,long now,MDMultiShadow &out,string &why)
{
 why="BLOQUEADO";MDReview615D review;
 if(!MDReviewState615D(journal,stream,instance,account,server,first,second,now,review)){why=review.reason;return false;}
 string scope=MDContext612(account,server,instance);MDMultiShadow candidate;MDResetMultiShadow(candidate);
 if(previous!="")
 {
  if(!MDDecodeMultiShadow(previous,scope,stream.data.contract,stream.data.date,instance,candidate)){why="ESTADO_MULTI_INVALIDO";return false;}
  if(candidate.data_key!=MDDataKey615B(stream.data)||candidate.cursor>stream.cursor||
     StringSubstr(journal,0,StringLen(candidate.journal))!=candidate.journal)
  {why="CONTEXTO_OU_DIARIO_MULTI_DIVERGENTE";return false;}
  if(candidate.revision>=1000000){why="REVISAO_MULTI_EXCEDIDA";return false;}
  candidate.revision++;
 }
 else
 {
  candidate.scope=scope;candidate.contract=stream.data.contract;candidate.date=stream.data.date;
  candidate.instance=instance;candidate.data_key=MDDataKey615B(stream.data);candidate.revision=1;
 }
 MDJournal610 j;if(!MDReplay610(journal,scope,stream.data.contract,stream.data.date,instance,j)){why="DIARIO_INVALIDO";return false;}
 for(int i=0;i<5;i++)
 {
  if(j.r[i].id==0){if(candidate.level[i].count>0){why="ORIGEM_MULTI_DESAPARECEU";return false;}continue;}
  MDOrigin68 origin;MDChainInput68 chain;MDChainResult68 result;string reason;
  if(!MDOrigin611(j,scope,i,second,origin)||!MDBuild69(second,origin,now,chain,reason)||!MDReconcileChain68(chain,result))
  {why="CADEIA_MULTI_NAO_CONCILIADA";return false;}
  if(result.open_positions==0&&candidate.level[i].count==0)continue;
  // external_pending=true: desconhecemos a ausencia de pedidos de gestao reais.
  if(!MDMultiReconcileBench(candidate.level[i],chain,true,true,reason)){why="MULTI_"+reason;return false;}
  for(int k=0;k<candidate.level[i].count;k++)
  {
   int idx=MDPosIndex68(result,candidate.level[i].slots[k].identifier);
   if(idx<0||result.positions[idx].open_volume<=0){why="MULTI_SALDO_AUSENTE";return false;}
   if(result.positions[idx].entered+0.00000001<candidate.entered[i][k]||
      result.positions[idx].exited+0.00000001<candidate.exited[i][k])
   {why="MULTI_HISTORICO_DEALS_REGREDIU";return false;}
   candidate.volume[i][k]=result.positions[idx].open_volume;
   candidate.entered[i][k]=result.positions[idx].entered;candidate.exited[i][k]=result.positions[idx].exited;
  }
 }
 candidate.journal=journal;candidate.cursor=stream.cursor;
 if(MDEncodeMultiShadow(candidate)==""){why="ESTADO_MULTI_INVALIDO";return false;}
 out=candidate;why=MDShadowTotal(candidate)>0?"MULTI_CONFERIDO":"SEM_POSICOES_VINCULADAS";return true;
}
#endif
