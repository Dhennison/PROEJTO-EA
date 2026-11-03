#ifndef MD_COORDINATOR615D
#define MD_COORDINATOR615D
#include "ModeloD_Context.mqh"
#include "ModeloD_IntegratedRecovery.mqh"
#include "ModeloD_ObservedResume.mqh"
// Coordenador sem transporte. Estado de observacao e diario separados semanticamente,
// reunidos no mesmo envelope. Nenhum toque e transformado em PREPARAR ou ACEITE.
struct MDBundle615D {long revision;string journal,observed;};
struct MDReview615D {bool valid;string reason;int chains,pending,positions;};
string MDPack615D(const MDBundle615D &b)
{
 if(b.revision<1||b.revision>1000000||StringLen(b.journal)<1||StringLen(b.observed)<1)return "";
 string body="MD615D_SHADOW\n"+IntegerToString(b.revision)+"\n"+IntegerToString(StringLen(b.journal))+"\n"+
 IntegerToString(StringLen(b.observed))+"\n"+b.journal+b.observed;
 if(StringLen(body)>60000)return "";
 return body+"\n"+IntegerToString(MDHash67(body));
}
bool MDUnpack615D(string text,MDBundle615D &b)
{
 b.revision=0;b.journal="";b.observed="";
 if(StringLen(text)>65536)return false;
 string f[4];int pos=0;
 for(int i=0;i<4;i++){int end=StringFind(text,"\n",pos);if(end<0)return false;f[i]=StringSubstr(text,pos,end-pos);pos=end+1;}
 long rev,nj,no,hash;
 if(f[0]!="MD615D_SHADOW"||!MDLong610(f[1],rev)||rev<1||rev>1000000||!MDLong610(f[2],nj)||
 !MDLong610(f[3],no)||nj<1||no<1||nj>524288||no>4096||nj+no>60000)return false;
 int end=pos+(int)nj+(int)no;
 if(end>=StringLen(text)||StringSubstr(text,end,1)!="\n"||!MDLong610(StringSubstr(text,end+1),hash)||
 hash!=MDHash67(StringSubstr(text,0,end)))return false;
 b.revision=rev;b.journal=StringSubstr(text,pos,(int)nj);b.observed=StringSubstr(text,pos+(int)nj,(int)no);return true;
}
bool MDLoad615D(string text,string scope,int instance,MDStream615 &rebuilt,MDBundle615D &b)
{
 MDBundle615D candidate;MDJournal610 j;
 if(!MDUnpack615D(text,candidate)||!MDReplay610(candidate.journal,scope,rebuilt.data.contract,rebuilt.data.date,instance,j))return false;
 // Copia candidata: falha nunca altera consumo ou estado do chamador.
 MDStream615 stream=rebuilt;
 if(!MDObservedRestore615B(candidate.observed,scope,instance,stream))return false;
 rebuilt=stream;b=candidate;return true;
}
bool MDNext615D(string previous,string journal,string scope,int instance,const MDStream615 &stream,string &next)
{
 next="";MDStream615 merged=stream;MDBundle615D b;MDJournal610 j;
 if(!MDCommitted615B(stream)||!MDReplay610(journal,scope,stream.data.contract,stream.data.date,instance,j))return false;
 b.revision=1;
 if(previous!="")
 {
  if(!MDLoad615D(previous,scope,instance,merged,b)||StringSubstr(journal,0,StringLen(b.journal))!=b.journal)return false;
  b.revision++;
 }
 b.journal=journal;b.observed=MDObservedSave615B(merged,scope,instance);
 next=MDPack615D(b);return next!="";
}
int MDMagicLevel615D(long magic,int instance)
{for(int i=0;i<5;i++)if(magic==MDMagic67(instance,i))return i;return -1;}
bool MDKnownPosition615D(const MDSnapshot69 &s,const MDJournal610 &j,long identifier)
{
 for(int i=0;i<5;i++)if(j.r[i].ticket>0&&MDLinked69(s,j.r[i].ticket,identifier))return true;
 return false;
}
bool MDKnownOrder615D(const MDSnapshot69 &s,const MDJournal610 &j,long ticket)
{
 for(int i=0;i<5;i++)if(j.r[i].ticket>0&&j.r[i].ticket==ticket)return true;
 for(int k=0;k<s.deals;k++)if(s.d[k].order==ticket&&(s.d[k].entry==1||s.d[k].entry==3)&&MDKnownPosition615D(s,j,s.d[k].position))return true;
 return false;
}
bool MDFail615D(MDReview615D &r,string why)
{r.valid=false;r.reason=why;return false;}
bool MDReviewState615D(string journal,const MDStream615 &stream,int instance,long account,string server,
 const MDSnapshot69 &a,const MDSnapshot69 &b,long now,MDReview615D &out)
{
 out.valid=false;out.reason="NAO_CONFERIDO";out.chains=0;out.pending=0;out.positions=0;
 string scope=MDContext612(account,server,instance);MDJournal610 j;
 if(scope==""||!MDCommitted615B(stream)||!MDReplay610(journal,scope,stream.data.contract,stream.data.date,instance,j))return MDFail615D(out,"CONTEXTO_FLUXO_OU_DIARIO_INVALIDO");
 if(a.account_key!=account||b.account_key!=account||a.server_key!=server||b.server_key!=server)return MDFail615D(out,"IDENTIDADE_DIVERGENTE");
 if(!a.hedge||!b.hedge)return MDFail615D(out,"CONTA_NAO_HEDGE");
 if(!MDSame69(a,b))return MDFail615D(out,"COLETA_INCOMPLETA_OU_INSTAVEL");
 if(now<stream.cursor||j.last_msc>now)return MDFail615D(out,"TEMPO_DIVERGENTE");
 for(int i=0;i<5;i++)
 {
  if(j.r[i].id==0)continue;
  MDRequest610 r=j.r[i];MDLevel l=stream.control.day.levels[i];
  if(r.entry!=(long)l.entry_tick||r.sl!=(long)l.sl_tick||r.tp!=(long)l.tp_tick||r.prepared_msc<stream.data.open_msc||r.prepared_msc>=stream.cutoff)
   return MDFail615D(out,"DIARIO_DIVERGE_DOS_DADOS_DIARIOS");
  if(r.ticket==0)return MDFail615D(out,"SOLICITACAO_EM_VOO_SEM_RESOLUCAO");
  MDOrigin68 origin;MDChainInput68 chain;MDChainResult68 result;string why;
  if(!MDOrigin611(j,scope,i,b,origin))return MDFail615D(out,"ORIGEM_NAO_COMPROVADA");
  if(!MDBuild69(b,origin,now,chain,why)||!MDReconcileChain68(chain,result))return MDFail615D(out,"CADEIA_NAO_CONCILIADA");
  out.chains++;if(result.pending)out.pending++;out.positions+=result.open_positions;
 }
 // Magic sozinho nunca comprova propriedade. Colisoes, inclusive outro contrato,
 // deixam a conferencia bloqueada e nao provocam cancelamento ou fechamento.
 for(int i=0;i<b.orders;i++)if(MDMagicLevel615D(b.o[i].order.magic,instance)>=0&&!MDKnownOrder615D(b,j,b.o[i].order.ticket))
  return MDFail615D(out,"ORDEM_COM_MAGIC_SEM_ORIGEM_NO_DIARIO");
 for(int i=0;i<b.deals;i++)if(MDMagicLevel615D(b.d[i].magic,instance)>=0&&!MDKnownPosition615D(b,j,b.d[i].position))
  return MDFail615D(out,"DEAL_COM_MAGIC_SEM_ORIGEM_NO_DIARIO");
 for(int i=0;i<b.positions;i++)if(MDMagicLevel615D(b.p[i].magic,instance)>=0&&!MDKnownPosition615D(b,j,b.p[i].identifier))
  return MDFail615D(out,"POSICAO_COM_MAGIC_SEM_ORIGEM_NO_DIARIO");
 out.valid=true;out.reason=out.chains==0?"SEM_CADEIAS_DA_INSTANCIA":"CADEIAS_CONFERIDAS_NO_SNAPSHOT";return true;
}
#endif
