#ifndef MD_SESSAO_DEMO213
#define MD_SESSAO_DEMO213
// Only today's DEMO session. Never extrapolate a past B3 snapshot.
// A broker 00:00--24:00 record is availability metadata, NOT B3 trading hours.
// For that exact single-record case the reviewed MODEL window is 09:00--18:00.
// Its "normal_end" is the management cutoff, not a claim about exchange close.
// A real flagged trade at/after 09:00, current B3 data and all other gates remain
// mandatory. This adapter cannot authorize auction quotes or pre-09:00 entries.
bool MDDemoSession213(int date,string contract,MDSessionRule &rule)
{
 MDSessionClear(rule);string why;
 int expiry=MDWINLastTrading2026(contract);
 if(!MDDemoAccount213(why)||MDCalendar2026(date)!=1||expiry<=0||expiry==date)return false;
 MqlDateTime now;if(!TimeToStruct(TimeTradeServer(),now))return false;
 if(date!=now.year*10000+now.mon*100+now.day)return false;
 long custom=1;
 if(!SymbolInfoInteger(contract,SYMBOL_CUSTOM,custom)||custom!=0)return false;
 int found=-1,count=0;bool generic_full_day=false;
 for(uint i=0;i<16;i++){
  datetime from=0,to=0;ResetLastError();
  if(!SymbolInfoSessionTrade(contract,(ENUM_DAY_OF_WEEK)now.day_of_week,i,from,to))break;
  count++;
  if((long)from==0&&(long)to==86400){generic_full_day=true;continue;}
  int begin=(int)((long)from%86400),end=(int)((long)to%86400);
  if(begin==9*3600&&end>=18*3600&&end<86400){
   if(found>=0&&found!=end)return false;
   found=end;
  }
 }
 if(generic_full_day){
  // Do not silently merge a generic record with additional broker sessions.
  if(count!=1)return false;
  return MDSessionSet(date,9*3600,18*3600,18*3600,true,
   "DEMO_SERVER_GENERIC_00_24;MODEL_WINDOW_09_18;NOT_B3_EXCHANGE_SCHEDULE",rule);
 }
 if(found<0)return false;
 return MDSessionSet(date,9*3600,found,18*3600,true,"MT5_BROKER_CURRENT_TRADE_SESSION;MODELO_D_CORTE18",rule);
}
#endif
