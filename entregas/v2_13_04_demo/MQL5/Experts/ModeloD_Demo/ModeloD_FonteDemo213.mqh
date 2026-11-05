#ifndef MD_FONTE_DEMO213
#define MD_FONTE_DEMO213
bool demo_native_called213=false;
// Direct broker data only. No synthetic alias and no frozen historical fallback.
bool MDSymbolInfoInteger213(string s,ENUM_SYMBOL_INFO_INTEGER p,long &v){return SymbolInfoInteger(s,p,v);}
bool MDSymbolInfoDouble213(string s,ENUM_SYMBOL_INFO_DOUBLE p,double &v){return SymbolInfoDouble(s,p,v);}
string MDSymbolInfoString213(string s,ENUM_SYMBOL_INFO_STRING p){return SymbolInfoString(s,p);}
bool MDSymbolInfoString213(string s,ENUM_SYMBOL_INFO_STRING p,string &v){return SymbolInfoString(s,p,v);}
bool MDSymbolInfoTick213(string s,MqlTick &v){return SymbolInfoTick(s,v);}
bool MDSymbolSelect213(string s,bool selected){return SymbolSelect(s,selected);}
int MDCopyRates213(string s,ENUM_TIMEFRAMES p,int start,int count,MqlRates &v[]){return CopyRates(s,p,start,count,v);}
int MDCopyRates213(string s,ENUM_TIMEFRAMES p,datetime start,datetime end,MqlRates &v[]){return CopyRates(s,p,start,end,v);}
int MDCopyTicksRange213(string s,MqlTick &v[],uint flags,ulong start,ulong end)
{
 if(flags!=COPY_TICKS_TRADE)return CopyTicksRange(s,v,flags,start,end);
 int n=CopyTicksRange(s,v,COPY_TICKS_ALL,start,end);
 if(n<0||GetLastError()!=0)return n;
 if(n>500000)return -1;
 int used=0;
 for(int i=0;i<n;i++)if((v[i].flags&120)!=0){if(used!=i)v[used]=v[i];used++;}
 if(ArrayResize(v,used)!=used)return -1;
 return used;
}
bool MDSeriesInfoInteger213(string s,ENUM_TIMEFRAMES p,ENUM_SERIES_INFO_INTEGER prop,long &v){return SeriesInfoInteger(s,p,prop,v);}
bool MDOrderCalcMargin213(ENUM_ORDER_TYPE type,string s,double volume,double price,double &margin){return OrderCalcMargin(type,s,volume,price,margin);}
bool MDDemoOwnedRequest213(const MqlTradeRequest &request);
bool MDDemoOrderSend213(const MqlTradeRequest &request,MqlTradeResult &result)
{
 demo_native_called213=false;
 if(!MDDemoGate213()||!MDDemoOwnedRequest213(request))return false;
 long custom=1;
 if(!SymbolInfoInteger(request.symbol,SYMBOL_CUSTOM,custom)||custom!=0)return false;
 // Recheck account after the metadata read and immediately before the API call.
 if(!MDDemoGate213())return false;
 demo_native_called213=true;
 return OrderSend(request,result);
}
bool MDOrderGetString213(ENUM_ORDER_PROPERTY_STRING p,string &v){return OrderGetString(p,v);}
bool MDHistoryOrderGetString213(ulong ticket,ENUM_ORDER_PROPERTY_STRING p,string &v){return HistoryOrderGetString(ticket,p,v);}
bool MDHistoryDealGetString213(ulong ticket,ENUM_DEAL_PROPERTY_STRING p,string &v){return HistoryDealGetString(ticket,p,v);}
bool MDPositionGetString213(ENUM_POSITION_PROPERTY_STRING p,string &v){return PositionGetString(p,v);}
bool MDReferenceMinute213(long minute,const MqlTick &ticks[],int size){return false;}
#endif
