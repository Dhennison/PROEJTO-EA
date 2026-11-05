#ifndef MD_FONTE_FUNCIONAL211
#define MD_FONTE_FUNCIONAL211
// Ponte de infraestrutura SOMENTE do ensaio. O modelo continua em WINZ26.
// D1 permanece na fonte original do mesmo contrato; ticks/M1/execucao vao
// ao custom cuja sequencia ja foi comparada ao CSV. Nenhuma formula muda.
input bool UsarFonteImportadaNoTester=false;
const string MD_FONTE211="MD_PESQ_WINZ26_DIA1030";
bool MDFonteAtiva211()
{return MDIsTester210()&&ExecutarNoTester&&UsarFonteImportadaNoTester&&
        !MQLInfoInteger(MQL_OPTIMIZATION)&&DataTester==20261030&&ContratoTester=="WINZ26"&&
        FusoServidorTester==-10800&&_Symbol==MD_FONTE211;}
bool MDGraficoValido211()
{return UsarFonteImportadaNoTester?MDFonteAtiva211():_Symbol==ContratoTester;}
string MDPrecoSimbolo211(string symbol)
{return MDFonteAtiva211()&&symbol=="WINZ26"?MD_FONTE211:symbol;}
string MDLogico211(string symbol)
{return MDFonteAtiva211()&&symbol==MD_FONTE211?"WINZ26":symbol;}
bool MDValidarFonte211(string &why)
{
   if(!MDFonteAtiva211()){why="FONTE_FUNCIONAL_CONTEXTO_INVALIDO";return false;}
   long custom=0;double tick=0;
   if(!SymbolSelect(MD_FONTE211,true)||!SymbolInfoInteger(MD_FONTE211,SYMBOL_CUSTOM,custom)||custom!=1||
      !SymbolInfoDouble(MD_FONTE211,SYMBOL_TRADE_TICK_SIZE,tick)||tick!=5)
   {why="FONTE_FUNCIONAL_CUSTOM_OU_TICK_INVALIDO";return false;}
   return true;
}
bool MDSymbolInfoInteger211(string s,ENUM_SYMBOL_INFO_INTEGER p,long &v)
{
   // Vencimento pertence ao contrato real, nao ao nome interno da fita.
   if(MDFonteAtiva211()&&s=="WINZ26"&&p==SYMBOL_EXPIRATION_TIME)
   {if(!SymbolSelect(s,true))return false;return SymbolInfoInteger(s,p,v);}
   return SymbolInfoInteger(MDPrecoSimbolo211(s),p,v);
}
bool MDSymbolInfoDouble211(string s,ENUM_SYMBOL_INFO_DOUBLE p,double &v)
{return SymbolInfoDouble(MDPrecoSimbolo211(s),p,v);}
string MDSymbolInfoString211(string s,ENUM_SYMBOL_INFO_STRING p)
{return SymbolInfoString(MDPrecoSimbolo211(s),p);}
bool MDSymbolInfoString211(string s,ENUM_SYMBOL_INFO_STRING p,string &v)
{return SymbolInfoString(MDPrecoSimbolo211(s),p,v);}
bool MDSymbolInfoTick211(string s,MqlTick &v)
{return SymbolInfoTick(MDPrecoSimbolo211(s),v);}
bool MDSymbolSelect211(string s,bool selected)
{return SymbolSelect(MDPrecoSimbolo211(s),selected);}
string MDSerieSimbolo211(string s,ENUM_TIMEFRAMES p)
{return p==PERIOD_D1?s:MDPrecoSimbolo211(s);}
bool MDPrepararSerie211(string s,ENUM_TIMEFRAMES p)
{return SymbolSelect(MDSerieSimbolo211(s,p),true);}
int MDCopyRates211(string s,ENUM_TIMEFRAMES p,int start,int count,MqlRates &v[])
{if(!MDPrepararSerie211(s,p))return -1;return CopyRates(MDSerieSimbolo211(s,p),p,start,count,v);}
int MDCopyRates211(string s,ENUM_TIMEFRAMES p,datetime start,datetime end,MqlRates &v[])
{if(!MDPrepararSerie211(s,p))return -1;return CopyRates(MDSerieSimbolo211(s,p),p,start,end,v);}
int MDCopyTicksRange211(string s,MqlTick &v[],uint flags,ulong start,ulong end)
{
 if(!MDFonteAtiva211()||s!="WINZ26"||flags!=COPY_TICKS_TRADE)
  return CopyTicksRange(MDPrecoSimbolo211(s),v,flags,start,end);
 // Read the imported source explicitly; carried Last with flags=0 is not a trade.
 int n=CopyTicksRange(MD_FONTE211,v,COPY_TICKS_ALL,start,end);
 if(n<0||GetLastError()!=0)return n;
 if(n>500000)return -1;
 int used=0;
 for(int i=0;i<n;i++)if((v[i].flags&120)!=0){if(used!=i)v[used]=v[i];used++;}
 if(ArrayResize(v,used)!=used)return -1;
 return used;
}
bool MDSeriesInfoInteger211(string s,ENUM_TIMEFRAMES p,ENUM_SERIES_INFO_INTEGER prop,long &v)
{if(!MDPrepararSerie211(s,p))return false;return SeriesInfoInteger(MDSerieSimbolo211(s,p),p,prop,v);}
bool MDOrderCalcMargin211(ENUM_ORDER_TYPE type,string s,double volume,double price,double &margin)
{return OrderCalcMargin(type,MDPrecoSimbolo211(s),volume,price,margin);}
bool MDOrderSend211(const MqlTradeRequest &request,MqlTradeResult &result)
{
   if(!MDIsTester210()||!MDTesterGate210())return false;
   if(UsarFonteImportadaNoTester&&!MDFonteAtiva211())return false;
   if(UsarFonteImportadaNoTester&&request.symbol!="WINZ26")return false;
   MqlTradeRequest physical=request;physical.symbol=MDPrecoSimbolo211(request.symbol);
   return OrderSend(physical,result);
}
bool MDOrderGetString211(ENUM_ORDER_PROPERTY_STRING p,string &v)
{bool ok=OrderGetString(p,v);if(ok&&p==ORDER_SYMBOL)v=MDLogico211(v);return ok;}
bool MDHistoryOrderGetString211(ulong ticket,ENUM_ORDER_PROPERTY_STRING p,string &v)
{bool ok=HistoryOrderGetString(ticket,p,v);if(ok&&p==ORDER_SYMBOL)v=MDLogico211(v);return ok;}
bool MDHistoryDealGetString211(ulong ticket,ENUM_DEAL_PROPERTY_STRING p,string &v)
{bool ok=HistoryDealGetString(ticket,p,v);if(ok&&p==DEAL_SYMBOL)v=MDLogico211(v);return ok;}
bool MDPositionGetString211(ENUM_POSITION_PROPERTY_STRING p,string &v)
{bool ok=PositionGetString(p,v);if(ok&&p==POSITION_SYMBOL)v=MDLogico211(v);return ok;}
#include "ModeloD_ReferenciaOriginal211.mqh"
#endif
