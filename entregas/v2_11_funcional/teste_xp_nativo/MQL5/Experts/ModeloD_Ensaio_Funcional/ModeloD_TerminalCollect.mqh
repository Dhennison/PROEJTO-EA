#ifndef MD_TERMINAL69
#define MD_TERMINAL69
#include "ModeloD_Collect.mqh"
// Todas as propriedades usam overload com retorno bool. Falha nao vira zero valido.
bool OI69(ENUM_ORDER_PROPERTY_INTEGER prop,long &value){return OrderGetInteger(prop,value);}
bool OD69(ENUM_ORDER_PROPERTY_DOUBLE prop,double &value){return OrderGetDouble(prop,value);}
bool OS69(ENUM_ORDER_PROPERTY_STRING prop,string &value){return MDOrderGetString211(prop,value);}
bool HI69(ulong ticket,ENUM_ORDER_PROPERTY_INTEGER prop,long &value){return HistoryOrderGetInteger(ticket,prop,value);}
bool HD69(ulong ticket,ENUM_ORDER_PROPERTY_DOUBLE prop,double &value){return HistoryOrderGetDouble(ticket,prop,value);}
bool HS69(ulong ticket,ENUM_ORDER_PROPERTY_STRING prop,string &value){return MDHistoryOrderGetString211(ticket,prop,value);}
bool DI69(ulong ticket,ENUM_DEAL_PROPERTY_INTEGER prop,long &value){return HistoryDealGetInteger(ticket,prop,value);}
bool DD69(ulong ticket,ENUM_DEAL_PROPERTY_DOUBLE prop,double &value){return HistoryDealGetDouble(ticket,prop,value);}
bool DS69(ulong ticket,ENUM_DEAL_PROPERTY_STRING prop,string &value){return MDHistoryDealGetString211(ticket,prop,value);}
bool PI69(ENUM_POSITION_PROPERTY_INTEGER prop,long &value){return PositionGetInteger(prop,value);}
bool PD69(ENUM_POSITION_PROPERTY_DOUBLE prop,double &value){return PositionGetDouble(prop,value);}
bool PS69(ENUM_POSITION_PROPERTY_STRING prop,string &value){return MDPositionGetString211(prop,value);}
int State69(long value)
{
 if(value==ORDER_STATE_PLACED||value==ORDER_STATE_PARTIAL)return 0;
 if(value==ORDER_STATE_CANCELED||value==ORDER_STATE_EXPIRED)return 1;
 if(value==ORDER_STATE_FILLED)return 2;
 if(value==ORDER_STATE_REJECTED)return 3;
 return -1;
}
bool ReadOrder69(ulong ticket,bool history,MDRawOrder69 &r)
{
 long magic=0,type=0,state=0,setup=0;double initial=0,remaining=0;string symbol="";
 bool ok=false;
 if(history)ok=HI69(ticket,ORDER_MAGIC,magic)&&HI69(ticket,ORDER_TYPE,type)&&HI69(ticket,ORDER_STATE,state)&&
 HI69(ticket,ORDER_TIME_SETUP_MSC,setup)&&HD69(ticket,ORDER_VOLUME_INITIAL,initial)&&HD69(ticket,ORDER_VOLUME_CURRENT,remaining)&&HS69(ticket,ORDER_SYMBOL,symbol);
 else ok=OI69(ORDER_MAGIC,magic)&&OI69(ORDER_TYPE,type)&&OI69(ORDER_STATE,state)&&OI69(ORDER_TIME_SETUP_MSC,setup)&&
 OD69(ORDER_VOLUME_INITIAL,initial)&&OD69(ORDER_VOLUME_CURRENT,remaining)&&OS69(ORDER_SYMBOL,symbol);
 if(!ok)return false;
 r.order.ticket=(long)ticket;r.order.magic=magic;r.order.symbol=symbol;r.order.state=State69(state);
 r.order.buy=type==ORDER_TYPE_BUY||type==ORDER_TYPE_BUY_LIMIT||type==ORDER_TYPE_BUY_STOP||type==ORDER_TYPE_BUY_STOP_LIMIT;
 r.order.initial_volume=initial;r.order.remaining=remaining;r.setup_msc=setup;
 r.entry_limit=type==ORDER_TYPE_BUY_LIMIT||type==ORDER_TYPE_SELL_LIMIT;return true;
}
bool Collect69(datetime start,datetime end,MDSnapshot69 &s,string &reason)
{
 s.complete=false;s.orders=0;s.deals=0;s.positions=0;
 s.connected=(bool)MDConnected210();
 s.hedge=AccountInfoInteger(ACCOUNT_MARGIN_MODE)==ACCOUNT_MARGIN_MODE_RETAIL_HEDGING;
 s.account_key=MDAccount210();s.server_key=MDServer210();
 reason="INICIO";
 if(!s.connected){reason="DESCONECTADO";return false;}
 if(start<=0||end<start){reason="INTERVALO_INVALIDO";return false;}
 ResetLastError();if(!HistorySelect(start,end)){reason="HISTORICO_ERRO_"+IntegerToString(GetLastError());return false;}
 int no=OrdersTotal(),nh=HistoryOrdersTotal(),nd=HistoryDealsTotal(),np=PositionsTotal();
 if(no+nh>256||nd>4096||np>64){reason="CAPACIDADE_GLOBAL_EXCEDIDA";return false;}
 for(int i=0;i<no;i++)
 {
  ulong t=OrderGetTicket(i);
  if(t==0||!ReadOrder69(t,false,s.o[s.orders])){reason="LEITURA_ORDEM_ATIVA_FALHOU";return false;}s.orders++;
 }
 for(int i=0;i<nh;i++)
 {
  ulong t=HistoryOrderGetTicket(i);
  if(t==0||!ReadOrder69(t,true,s.o[s.orders])){reason="LEITURA_ORDEM_HISTORICA_FALHOU";return false;}s.orders++;
 }
 for(int i=0;i<nd;i++)
 {
  ulong t=HistoryDealGetTicket(i);long type=0;
  if(t==0||!DI69(t,DEAL_TYPE,type)){reason="TIPO_DEAL_FALHOU";return false;}
  if(type!=DEAL_TYPE_BUY&&type!=DEAL_TYPE_SELL)continue;
  MDDeal68 v;long entry=0;
  if(!DI69(t,DEAL_ORDER,v.order)||!DI69(t,DEAL_POSITION_ID,v.position)||!DI69(t,DEAL_MAGIC,v.magic)||
   !DI69(t,DEAL_TIME_MSC,v.msc)||!DI69(t,DEAL_ENTRY,entry)||!DS69(t,DEAL_SYMBOL,v.symbol)||!DD69(t,DEAL_VOLUME,v.volume))
  {reason="PROPRIEDADE_DEAL_FALHOU";return false;}
  v.ticket=(long)t;v.buy=type==DEAL_TYPE_BUY;v.entry=(int)entry;s.d[s.deals++]=v;
 }
 for(int i=0;i<np;i++)
 {
  ulong t=PositionGetTicket(i);MDPosition68 v;long type=0;
  if(t==0||!PI69(POSITION_IDENTIFIER,v.identifier)||!PI69(POSITION_MAGIC,v.magic)||!PI69(POSITION_TYPE,type)||
   !PS69(POSITION_SYMBOL,v.symbol)||!PD69(POSITION_VOLUME,v.volume))
  {reason="PROPRIEDADE_POSICAO_FALHOU";return false;}
  v.ticket=(long)t;v.buy=type==POSITION_TYPE_BUY;s.p[s.positions++]=v;
 }
 if(no!=OrdersTotal()||nh!=HistoryOrdersTotal()||nd!=HistoryDealsTotal()||np!=PositionsTotal()||
 s.account_key!=MDAccount210()||s.server_key!=MDServer210()||!MDConnected210())
 {reason="CONTAGEM_CONTA_OU_CONEXAO_MUDOU";return false;}
 s.complete=true;reason="LEITURA_CONCLUIDA_NAO_ATOMICA";return true;
}
#endif
