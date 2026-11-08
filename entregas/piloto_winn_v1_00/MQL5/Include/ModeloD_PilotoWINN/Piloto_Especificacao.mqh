#ifndef MDPW_SPEC
#define MDPW_SPEC
string PWSpecLong(string symbol,ENUM_SYMBOL_INFO_INTEGER property,string label)
{
 long value=0;ResetLastError();bool ok=SymbolInfoInteger(symbol,property,value);int error=GetLastError();
 return label+"="+(ok?IntegerToString(value):"INDISPONIVEL")+";error="+IntegerToString(error)+"\r\n";
}
string PWSpecDouble(string symbol,ENUM_SYMBOL_INFO_DOUBLE property,string label)
{
 double value=0;ResetLastError();bool ok=SymbolInfoDouble(symbol,property,value);int error=GetLastError();
 return label+"="+(ok?DoubleToString(value,12):"INDISPONIVEL")+";error="+IntegerToString(error)+"\r\n";
}
string PWSpecString(string symbol,ENUM_SYMBOL_INFO_STRING property,string label)
{
 string value="";ResetLastError();bool ok=SymbolInfoString(symbol,property,value);int error=GetLastError();
 return label+"="+(ok?value:"INDISPONIVEL")+";error="+IntegerToString(error)+"\r\n";
}
string PWSpecification(string symbol)
{
 string s="ESPECIFICACAO_SOMENTE_LEITURA;symbol="+symbol+"\r\nserver="+AccountInfoString(ACCOUNT_SERVER)+
  "\r\ncompany="+AccountInfoString(ACCOUNT_COMPANY)+"\r\nbuild="+IntegerToString(TerminalInfoInteger(TERMINAL_BUILD))+
  "\r\ntester="+IntegerToString(MQLInfoInteger(MQL_TESTER))+"\r\nmargin_mode="+IntegerToString(AccountInfoInteger(ACCOUNT_MARGIN_MODE))+
  "\r\naccount_currency="+AccountInfoString(ACCOUNT_CURRENCY)+"\r\nserver_time="+TimeToString(TimeCurrent(),TIME_DATE|TIME_SECONDS)+"\r\n";
 s+=PWSpecString(symbol,SYMBOL_DESCRIPTION,"description");s+=PWSpecString(symbol,SYMBOL_PATH,"path");
 s+=PWSpecString(symbol,SYMBOL_EXCHANGE,"exchange");s+=PWSpecString(symbol,SYMBOL_BASIS,"basis");
 s+=PWSpecString(symbol,SYMBOL_ISIN,"isin");s+=PWSpecString(symbol,SYMBOL_CURRENCY_PROFIT,"currency_profit");
 s+=PWSpecString(symbol,SYMBOL_CURRENCY_MARGIN,"currency_margin");
 s+=PWSpecLong(symbol,SYMBOL_CUSTOM,"custom");s+=PWSpecLong(symbol,SYMBOL_DIGITS,"digits");
 s+=PWSpecLong(symbol,SYMBOL_CHART_MODE,"chart_mode");s+=PWSpecLong(symbol,SYMBOL_TRADE_MODE,"trade_mode");
 s+=PWSpecLong(symbol,SYMBOL_TRADE_CALC_MODE,"calc_mode");s+=PWSpecLong(symbol,SYMBOL_TRADE_EXEMODE,"execution_mode");
 s+=PWSpecLong(symbol,SYMBOL_ORDER_MODE,"order_mode");s+=PWSpecLong(symbol,SYMBOL_FILLING_MODE,"filling_mode");
 s+=PWSpecLong(symbol,SYMBOL_EXPIRATION_MODE,"expiration_mode");s+=PWSpecLong(symbol,SYMBOL_START_TIME,"start_time");
 s+=PWSpecLong(symbol,SYMBOL_EXPIRATION_TIME,"expiration_time");s+=PWSpecLong(symbol,SYMBOL_TRADE_STOPS_LEVEL,"stops_level");
 s+=PWSpecLong(symbol,SYMBOL_TRADE_FREEZE_LEVEL,"freeze_level");
 s+=PWSpecDouble(symbol,SYMBOL_POINT,"point");s+=PWSpecDouble(symbol,SYMBOL_TRADE_TICK_SIZE,"tick_size");
 s+=PWSpecDouble(symbol,SYMBOL_TRADE_TICK_VALUE,"tick_value");s+=PWSpecDouble(symbol,SYMBOL_TRADE_CONTRACT_SIZE,"contract_size");
 s+=PWSpecDouble(symbol,SYMBOL_VOLUME_MIN,"volume_min");s+=PWSpecDouble(symbol,SYMBOL_VOLUME_MAX,"volume_max");
 s+=PWSpecDouble(symbol,SYMBOL_VOLUME_STEP,"volume_step");
 MqlTick tick;ZeroMemory(tick);ResetLastError();bool got=SymbolInfoTick(symbol,tick);int error=GetLastError();
 s+="latest_tick_ok="+IntegerToString(got?1:0)+";error="+IntegerToString(error)+";msc="+IntegerToString(tick.time_msc)+
  ";bid="+DoubleToString(tick.bid,8)+";ask="+DoubleToString(tick.ask,8)+";last="+DoubleToString(tick.last,8)+"\r\n";
 s+="DESCRICAO_E_PROPRIEDADES_NAO_CERTIFICAM_ORIGEM_B3;CONFIRMAR_DOCUMENTACAO_DO_PRODUTO\r\n";
 return s;
}
#endif
