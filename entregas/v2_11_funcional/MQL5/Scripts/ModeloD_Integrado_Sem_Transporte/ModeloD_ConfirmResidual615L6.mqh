#ifndef MD_CONFIRM_RESIDUAL615L6
#define MD_CONFIRM_RESIDUAL615L6
#include "ModeloD_Urgent615L3.mqh"
// Vinculo deve ser produzido pelo transporte persistido; Magic sozinho nao basta.
struct MDBinding615L6 {bool verified;long attempt,order,position,requested_msc;};
bool MDConfirmClose615L6(const MDPair615L3 &state,const MDBinding615L6 &binding,string journal,
 string scope,string contract,int date,int instance,int level,const MDSnapshot69 &snapshot,long account,string server,long now,
 bool fresh,bool reserve_residual,MDPair615L3 &next,double &residual)
{
 residual=0;
 if(!MDPairValid615L3(state)||state.close_slot.phase!=1||!binding.verified||binding.attempt!=state.close_slot.attempt||
 binding.order<=0||binding.position<=0||binding.requested_msc<=0||binding.requested_msc>now||!fresh||
 snapshot.account_key!=account||snapshot.server_key!=server||!snapshot.complete||!snapshot.connected||!snapshot.hedge||!MDCounts69(snapshot))return false;
 MDJournal610 j;if(!MDReplay610(journal,scope,contract,date,instance,j)||level<0||level>4||!j.r[level].close||
 state.close_slot.key!=MDPairKey615L3(j,level,state.close_slot.management.ticket)+"|CLOSE")return false;
 MDOrigin68 origin;MDChainInput68 chain;MDChainResult68 result;string why;
 if(!MDOrigin611(j,scope,level,snapshot,origin)||!MDBuild69(snapshot,origin,now,chain,why)||!MDReconcileChain68(chain,result))return false;
 int idx=MDPosIndex68(result,binding.position);if(idx<0)return false;
 if(result.positions[idx].open_volume>0&&result.positions[idx].current_ticket!=state.close_slot.action_ticket)return false;
 int found=-1;for(int i=0;i<snapshot.orders;i++)if(snapshot.o[i].order.ticket==binding.order){if(found>=0)return false;found=i;}
 if(found<0)return false;
 MDRawOrder69 raw=snapshot.o[found];MDOrder68 order=raw.order;
 if(raw.entry_limit||raw.setup_msc<binding.requested_msc||raw.setup_msc>now||order.symbol!=contract||order.magic!=MDMagic67(instance,level)||
 order.buy==origin.buy||(order.state!=1&&order.state!=2)||order.initial_volume!=(double)state.close_slot.volume||
 !MDVolume68(order.remaining)||order.remaining>order.initial_volume||(order.state==2&&order.remaining!=0))return false;
 double exited=0;
 for(int i=0;i<snapshot.deals;i++)if(snapshot.d[i].order==binding.order)
 {
  MDDeal68 d=snapshot.d[i];
  if(d.position!=binding.position||d.symbol!=contract||d.magic!=order.magic||d.buy==origin.buy||d.entry!=1||d.msc<binding.requested_msc||d.msc<raw.setup_msc||d.msc>now||!MDVolume68(d.volume)||d.volume<=0)return false;
  bool duplicate=false;for(int k=0;k<i;k++)if(snapshot.d[k].ticket==d.ticket){if(!MDDealSame68(snapshot.d[k],d))return false;duplicate=true;}
  if(!duplicate)exited+=d.volume;
 }
 // Ausencia de posicao ou retcode isolado nao substituem ordem terminal e deals ligados.
 if(exited<=0||!MDEqual68(exited,order.initial_volume-order.remaining))return false;
 MDPair615L3 candidate;
 if(!MDPairResolve615L3(state,4,binding.attempt,state.close_slot.action_ticket,true,candidate))return false;
 residual=result.positions[idx].open_volume;
 if(!MDVolume68(residual)||residual!=(double)((long)residual))return false;
 if(reserve_residual&&residual>0)
 {
  if(candidate.close_slot.attempt>=1000000000||candidate.close_slot.revision>=1000000000)return false;
  candidate.close_slot.attempt++;candidate.close_slot.revision++;candidate.close_slot.phase=1;candidate.close_slot.volume=(long)residual;
 }
 next=candidate;return true;
}
#endif
