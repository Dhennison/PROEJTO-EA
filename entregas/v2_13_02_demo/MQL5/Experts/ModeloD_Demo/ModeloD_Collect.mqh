#ifndef MD_COLLECT69
#define MD_COLLECT69
#include "ModeloD_Chain.mqh"
// Coleta limitada. Nao representa snapshot atomico do servidor.
struct MDRawOrder69 { MDOrder68 order;long setup_msc;bool entry_limit; };
struct MDSnapshot69
{
 bool complete,connected,hedge;
 long account_key;string server_key;
 int orders,deals,positions;
 MDRawOrder69 o[256];MDDeal68 d[4096];MDPosition68 p[64];
};
bool MDOrderEqual69(const MDRawOrder69 &a,const MDRawOrder69 &b)
{
 return a.setup_msc==b.setup_msc&&a.entry_limit==b.entry_limit&&
 a.order.ticket==b.order.ticket&&a.order.magic==b.order.magic&&a.order.symbol==b.order.symbol&&
 a.order.buy==b.order.buy&&a.order.state==b.order.state&&
 a.order.initial_volume==b.order.initial_volume&&a.order.remaining==b.order.remaining;
}
bool MDPositionEqual69(const MDPosition68 &a,const MDPosition68 &b)
{return a.ticket==b.ticket&&a.identifier==b.identifier&&a.magic==b.magic&&a.symbol==b.symbol&&a.buy==b.buy&&a.volume==b.volume;}
bool MDCounts69(const MDSnapshot69 &s)
{return s.orders>=0&&s.orders<=256&&s.deals>=0&&s.deals<=4096&&s.positions>=0&&s.positions<=64;}
bool MDSame69(const MDSnapshot69 &a,const MDSnapshot69 &b)
{
 if(!a.complete||!b.complete||!a.connected||!b.connected||!a.hedge||!b.hedge||!MDCounts69(a)||!MDCounts69(b)||
 a.account_key!=b.account_key||a.server_key!=b.server_key||a.orders!=b.orders||a.deals!=b.deals||a.positions!=b.positions)return false;
 // Coletor preserva ordem de enumeracao. Reordenacao e tratada conservadoramente como instabilidade.
 for(int i=0;i<a.orders;i++)if(!MDOrderEqual69(a.o[i],b.o[i]))return false;
 for(int i=0;i<a.deals;i++)if(!MDDealSame68(a.d[i],b.d[i]))return false;
 for(int i=0;i<a.positions;i++)if(!MDPositionEqual69(a.p[i],b.p[i]))return false;
 return true;
}
bool MDLinked69(const MDSnapshot69 &s,long origin,long identifier)
{
 for(int i=0;i<s.deals;i++)if(s.d[i].order==origin&&s.d[i].entry==0&&s.d[i].position==identifier)return true;
 return false;
}
bool MDBuild69(const MDSnapshot69 &s,const MDOrigin68 &origin,long snapshot_msc,MDChainInput68 &out,string &reason)
{
 out.snapshot_complete=false;out.deal_count=0;out.position_count=0;out.origin=origin;out.snapshot_msc=snapshot_msc;
 reason="COLETA_INVALIDA";
 if(!s.complete||!s.connected||!s.hedge||!MDCounts69(s))return false;
 int found=-1;
 for(int i=0;i<s.orders;i++)if(s.o[i].order.ticket==origin.order_ticket)
 {if(found>=0){reason="ORDEM_DUPLICADA_ENTRE_LISTAS";return false;}found=i;}
 if(found<0){reason="ORDEM_ORIGINAL_AUSENTE";return false;}
 out.order=s.o[found].order;
 for(int i=0;i<s.deals;i++)
 {
  if(s.d[i].order!=origin.order_ticket&&!MDLinked69(s,origin.order_ticket,s.d[i].position))continue;
  if(out.deal_count>=128){reason="CADEIA_EXCEDE_128_DEALS";return false;}
  out.deals[out.deal_count++]=s.d[i];
 }
 for(int i=0;i<s.positions;i++)if(MDLinked69(s,origin.order_ticket,s.p[i].identifier))
 {
  if(out.position_count>=16){reason="CADEIA_EXCEDE_16_POSICOES";return false;}
  out.positions[out.position_count++]=s.p[i];
 }
 out.snapshot_complete=true;reason="CADEIA_EXTRAIDA_ORIGEM_AINDA_EXIGE_PROVA";return true;
}
#endif
