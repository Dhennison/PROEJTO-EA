#ifndef MODELOD_MULTIPOSICAO_BANCADA
#define MODELOD_MULTIPOSICAO_BANCADA
#include "ModeloD_Management615L.mqh"
// Gerencia de bancada em memoria. Nao ha transporte ou persistencia operacional.
struct MDPositionControlBench {long identifier; MDManagement615L control;};
struct MDMultiBench {int count; long order,magic,accepted; string symbol; int date; MDPositionControlBench slots[16];};
void MDMultiResetBench(MDMultiBench &m){m.count=0;m.order=0;m.magic=0;m.accepted=0;m.symbol="";m.date=0;}
int MDIndexBench(const MDMultiBench &m,long id)
{for(int i=0;i<m.count;i++)if(m.slots[i].identifier==id)return i;return -1;}
// Exige cadeia validada internamente. Desaparecimento de posicao bloqueia:
// fechamento e limpeza necessitam conciliacao e registro persistente externos.
// Em caso de ticket alterado a origem do evento pendente e desconhecida:
// pendencias externas ou chamada em voo bloqueiam a transferencia do controle.
bool MDMultiReconcileBench(MDMultiBench &state,const MDChainInput68 &chain_input,bool fresh,bool external_pending,string &reason)
{
 reason="DADOS_NAO_CONFIAVEIS";MDChainResult68 chain;
 if(!fresh||!MDReconcileChain68(chain_input,chain))return false;
 if(state.count<0||state.count>16)return false;
 MDMultiBench next=state;
 if(state.order==0){next.order=chain_input.origin.order_ticket;next.magic=chain_input.origin.magic;next.accepted=chain_input.origin.accepted_msc;next.symbol=chain_input.origin.symbol;next.date=chain_input.origin.date;}
 else if(state.order!=chain_input.origin.order_ticket||state.magic!=chain_input.origin.magic||state.accepted!=chain_input.origin.accepted_msc||state.symbol!=chain_input.origin.symbol||state.date!=chain_input.origin.date){reason="ORIGEM_DIVERGENTE";return false;}
 for(int i=0;i<state.count;i++)
 {
  if(state.slots[i].identifier<=0||state.slots[i].control.ticket<=0)return false;
  for(int j=0;j<i;j++)if(state.slots[j].identifier==state.slots[i].identifier||state.slots[j].control.ticket==state.slots[i].control.ticket)return false;
  int k=MDPosIndex68(chain,state.slots[i].identifier);
  if(k<0||chain.positions[k].open_volume<=0||chain.positions[k].current_ticket<=0){reason="POSICAO_AUSENTE_EXIGE_CONCILIACAO";return false;}
  long current=chain.positions[k].current_ticket;
  if(current!=state.slots[i].control.ticket)
  {
   if(external_pending||state.slots[i].control.protection.inflight){reason="TICKET_ALTERADO_COM_PENDENCIA";return false;}
   next.slots[i].control.ticket=current;
  }
 }
 for(int k=0;k<chain.position_count;k++)if(chain.positions[k].open_volume>0)
 {
  if(MDIndexBench(next,chain.positions[k].identifier)<0)
  {
   if(next.count>=16){reason="CAPACIDADE";return false;}
   int at=next.count++;next.slots[at].identifier=chain.positions[k].identifier;
   MDManagementReset615L(next.slots[at].control,chain.positions[k].current_ticket);
  }
 }
 for(int i=0;i<next.count;i++)for(int j=0;j<i;j++)if(next.slots[i].control.ticket==next.slots[j].control.ticket)return false;
 state=next;reason="CADEIA_CONCILIADA_BANCADA";return true;
}
#endif
