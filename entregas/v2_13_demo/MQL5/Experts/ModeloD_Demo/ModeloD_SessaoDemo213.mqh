#ifndef MD_SESSAO_DEMO213
#define MD_SESSAO_DEMO213
// Only today's broker trade session. Never extrapolate a past B3 snapshot.
bool MDDemoSession213(int date,string contract,MDSessionRule &rule)
{
 MDSessionClear(rule);string why;
 if(!MDDemoAccount213(why)||MDCalendar2026(date)!=1||MDWINLastTrading2026(contract)==date)return false;
 MqlDateTime now;if(!TimeToStruct(TimeTradeServer(),now))return false;
 if(date!=now.year*10000+now.mon*100+now.day)return false;
 long custom=1;
 if(!SymbolInfoInteger(contract,SYMBOL_CUSTOM,custom)||custom!=0)return false;
 int found=-1;
 for(uint i=0;i<16;i++){
  datetime from=0,to=0;ResetLastError();
  if(!SymbolInfoSessionTrade(contract,(ENUM_DAY_OF_WEEK)now.day_of_week,i,from,to))break;
  int begin=(int)((long)from%86400),end=(int)((long)to%86400);
  if(begin==9*3600&&end>=18*3600&&end<86400){
   if(found>=0&&found!=end)return false;
   found=end;
  }
 }
 if(found<0)return false;
 return MDSessionSet(date,9*3600,found,18*3600,true,"MT5_BROKER_CURRENT_TRADE_SESSION;MODELO_D_CORTE18",rule);
}
#endif
