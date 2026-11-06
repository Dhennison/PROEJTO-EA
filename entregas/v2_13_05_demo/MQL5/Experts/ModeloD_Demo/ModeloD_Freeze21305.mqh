#ifndef MD_FREEZE21305
#define MD_FREEZE21305
bool MDFreezeDistance21305(double distance,long freeze,double point) {
 return MathIsValidNumber(distance)&&freeze>=0&&MDPositive(point)&&(freeze==0||distance>(double)freeze*point);
}
bool MDDemoFreeze21305(const MDOpLevel &l,int kind,string &why) {
 // Freeze governs changes/removal, not a new Limit's strategy price.
 // Never suppress an emergency market close based on this precheck.
 if(kind!=2&&kind!=3)return true;
 long freeze=0;double point=0,bid=0,ask=0;
 if(!MDSymbolInfoInteger213(l.symbol,SYMBOL_TRADE_FREEZE_LEVEL,freeze)||freeze<0||
    !MDSymbolInfoDouble213(l.symbol,SYMBOL_POINT,point)||!MDPositive(point)){
  why="FREEZE_METADATA_INVALIDA";return false;
 }
 if(freeze==0)return true;
 if(!MDSymbolInfoDouble213(l.symbol,SYMBOL_BID,bid)||!MDSymbolInfoDouble213(l.symbol,SYMBOL_ASK,ask)||
    !MDPositive(bid)||!MDPositive(ask)||bid>ask){why="FREEZE_COTACAO_INVALIDA";return false;}
 if(kind==3){
  double distance=l.prices.buy?ask-l.prices.entry_tick:l.prices.entry_tick-bid;
  if(!MDFreezeDistance21305(distance,freeze,point)){why="CANCELAMENTO_AGUARDA_FREEZE_LEVEL;SEM_CONSUMO_ADICIONAL";return false;}
 }else{
  double market=l.prices.buy?bid:ask;
  double sl=l.prices.buy?market-l.prices.sl_tick:l.prices.sl_tick-market;
  double tp=l.prices.buy?l.prices.tp_tick-market:market-l.prices.tp_tick;
  if(!MDFreezeDistance21305(sl,freeze,point)||!MDFreezeDistance21305(tp,freeze,point)){
   // A protection attempt must not be silently suppressed by a local freeze check.
   // Send the same fixed prices, observe the broker retcode and keep the 6+3min schedule.
   Report615("FREEZE21305;SLTP_DENTRO_DA_ZONA;TENTATIVA_DE_PROTECAO_MANTIDA;SEM_DESLOCAR_PRECOS");
  }
 }
 return true;
}
#endif
