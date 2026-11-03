#ifndef MD_INTEGRATED611
#define MD_INTEGRATED611
#include "ModeloD_Journal.mqh"
#include "ModeloD_Collect.mqh"
struct MDIntegrated611
{
 bool valid,persist_consumption;string reason;
 MDRecoveryResult67 decision;
};
void MDBlock611(MDIntegrated611 &r,string reason)
{
 r.valid=false;r.persist_consumption=false;r.reason=reason;
 r.decision.consumed=false;r.decision.block_new=true;r.decision.cancel_pending=false;
 r.decision.close_positions=false;r.decision.protect_positions=false;
}
bool MDOrigin611(const MDJournal610 &j,string expected_scope,int level,const MDSnapshot69 &s,MDOrigin68 &origin)
{
 origin.verified=false;
 if(!j.valid||j.scope!=expected_scope||level<0||level>4||j.r[level].ticket<=0||!s.complete||!s.connected||!s.hedge||!MDCounts69(s))return false;
 int found=-1;
 for(int i=0;i<s.orders;i++)if(s.o[i].order.ticket==j.r[level].ticket)
 {if(found>=0)return false;found=i;}
 if(found<0)return false;
 MDRawOrder69 o=s.o[found];
 if(!o.entry_limit||o.order.magic!=MDMagic67(j.instance,level)||o.order.symbol!=j.contract||
 o.order.buy!=(level<3)||o.order.initial_volume!=(double)j.r[level].volume||o.setup_msc!=j.r[level].accepted_msc)return false;
 origin.symbol=j.contract;origin.instance=j.instance;origin.level=level;origin.date=j.date;origin.buy=level<3;
 origin.order_ticket=j.r[level].ticket;origin.magic=MDMagic67(j.instance,level);origin.accepted_msc=j.r[level].accepted_msc;
 origin.initial_volume=(double)j.r[level].volume;origin.verified=true;return true;
}
bool MDIntegratedRecover611(const MDJournal610 &j,string scope,int level,const MDSnapshot69 &s,long snapshot_msc,
 const MDRecoveryEvidence67 &market,bool cutoff,MDIntegrated611 &out)
{
 MDBlock611(out,"ORIGEM_OU_COLETA_NAO_COMPROVADA");MDOrigin68 origin;
 if(!MDOrigin611(j,scope,level,s,origin))return false;
 MDChainInput68 chain;string reason;
 if(!MDBuild69(s,origin,snapshot_msc,chain,reason)){out.reason=reason;return false;}
 MDChainResult68 result;if(!MDReconcileChain68(chain,result)){out.reason=result.reason;return false;}
 MDRecoveryEvidence67 e=market;
 if(!MDChainEvidence68(result,e))return false;
 e.cutoff=e.cutoff||cutoff;
 MDCheckpoint67 local;local.scope=j.scope;local.contract=j.contract;local.date=j.date;local.instance=j.instance;
 local.consumed=0;local.cancel=0;local.close=0;local.inflight=0;local.cutoff=cutoff?1:0;local.sequence=j.sequence;
 for(int i=0;i<5;i++)
 {
  if(j.r[i].consumed)local.consumed|=1<<i;
  if(j.r[i].cancel)local.cancel|=1<<i;
  if(j.r[i].close)local.close|=1<<i;
  if(j.r[i].id>0&&j.r[i].ticket==0)local.inflight|=1<<i;
 }
 MDRecover67(local,e,level,out.decision);
 out.persist_consumption=out.decision.consumed&&!j.r[level].consumed;
 out.valid=true;out.reason="CONCILIACAO_E_INTENCOES_CALCULADAS_SEM_ENVIO";return true;
}
#endif
