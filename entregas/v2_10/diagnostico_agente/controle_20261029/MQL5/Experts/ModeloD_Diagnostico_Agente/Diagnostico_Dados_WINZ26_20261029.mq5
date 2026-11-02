#property strict
#property version "1.00"
#property description "Controle de dados WINZ26 29/10/2026. Sem negociacao."

int diag_file=INVALID_HANDLE;
bool diag_done=false;
bool diag_first_tick=false;
string diag_path="";

void DiagLog(string message)
{
   Print("MD_DIAG;",message);
   if(diag_file!=INVALID_HANDLE)
   {
      FileWriteString(diag_file,"MD_DIAG;"+message+"\r\n");
      FileFlush(diag_file);
   }
}

string DiagNumber(double value){return DoubleToString(value,8);}

void DiagTick(string tag,const MqlTick &tick)
{
   DiagLog(tag+";time="+TimeToString(tick.time,TIME_DATE|TIME_SECONDS)+
           ";msc="+IntegerToString(tick.time_msc)+
           ";bid="+DiagNumber(tick.bid)+";ask="+DiagNumber(tick.ask)+
           ";last="+DiagNumber(tick.last)+";volume="+IntegerToString((long)tick.volume)+
           ";volume_real="+DiagNumber(tick.volume_real)+
           ";flags="+IntegerToString((long)tick.flags));
}

void DiagInteger(string name,ENUM_SYMBOL_INFO_INTEGER property)
{
   long value=0;ResetLastError();
   bool ok=SymbolInfoInteger(_Symbol,property,value);int error=GetLastError();
   DiagLog("PROPERTY;name="+name+";ok="+IntegerToString((int)ok)+
           ";value="+IntegerToString(value)+";error="+IntegerToString(error));
}

void DiagDouble(string name,ENUM_SYMBOL_INFO_DOUBLE property)
{
   double value=0;ResetLastError();
   bool ok=SymbolInfoDouble(_Symbol,property,value);int error=GetLastError();
   DiagLog("PROPERTY;name="+name+";ok="+IntegerToString((int)ok)+
           ";value="+DiagNumber(value)+";error="+IntegerToString(error));
}

void DiagQuery(string label,uint selection)
{
   ulong begin=(ulong)D'2026.10.29 09:00:00'*1000;
   ulong end=(ulong)D'2026.10.29 09:01:00'*1000-1;
   MqlTick ticks[];ResetLastError();
   int count=CopyTicksRange(_Symbol,ticks,selection,begin,end);
   int error=GetLastError();
   DiagLog("QUERY;mode="+label+";from="+IntegerToString((long)begin)+
           ";to="+IntegerToString((long)end)+";returned="+IntegerToString(count)+
           ";array="+IntegerToString(ArraySize(ticks))+";error="+IntegerToString(error));
   // Even an error with partial output is recorded; never certify it as complete.
   int available=count>0 ? count : 0;
   if(available>ArraySize(ticks))available=ArraySize(ticks);
   int trades=0,zeros=0,zero_flags=0,regressions=0,outside=0,shown=0;
   double open=0,high=0,low=0,close=0,volume=0,volume_real=0;
   long previous=-1;
   for(int i=0;i<available;i++)
   {
      MqlTick tick=ticks[i];
      if(i<3)DiagTick("SAMPLE;mode="+label+";index="+IntegerToString(i),tick);
      if(tick.time_msc<(long)begin||tick.time_msc>(long)end)outside++;
      if(previous>=0&&tick.time_msc<previous)regressions++;
      previous=tick.time_msc;
      if(tick.flags==0)zero_flags++;
      if(!MathIsValidNumber(tick.last)||tick.last<=0)zeros++;
      bool trade=(tick.flags&(TICK_FLAG_LAST|TICK_FLAG_VOLUME|TICK_FLAG_BUY|TICK_FLAG_SELL))!=0;
      if(!trade||!MathIsValidNumber(tick.last)||tick.last<=0)continue;
      if(trades==0){open=tick.last;high=tick.last;low=tick.last;}
      high=MathMax(high,tick.last);low=MathMin(low,tick.last);close=tick.last;
      trades++;volume+=(double)tick.volume;volume_real+=tick.volume_real;
      if(shown<3){DiagTick("TRADE;mode="+label+";index="+IntegerToString(i),tick);shown++;}
   }
   DiagLog("SUMMARY;mode="+label+";complete_without_api_error="+
           IntegerToString((int)(count>=0&&error==0&&count==ArraySize(ticks)))+
           ";positive_trade_rows="+IntegerToString(trades)+
           ";zero_or_invalid_last="+IntegerToString(zeros)+
           ";flags_zero="+IntegerToString(zero_flags)+
           ";regressions="+IntegerToString(regressions)+";outside="+IntegerToString(outside)+
           ";open="+DiagNumber(open)+";high="+DiagNumber(high)+
           ";low="+DiagNumber(low)+";close="+DiagNumber(close)+
           ";sum_volume="+DiagNumber(volume)+";sum_volume_real="+DiagNumber(volume_real));
   if(available>0)DiagTick("LAST_SAMPLE;mode="+label,ticks[available-1]);
}

void DiagProcess()
{
   if(diag_done||TimeCurrent()<D'2026.10.29 09:02:00')return;
   diag_done=true;
   DiagLog("PROBE;time_current="+TimeToString(TimeCurrent(),TIME_DATE|TIME_SECONDS)+
           ";time_server="+TimeToString(TimeTradeServer(),TIME_DATE|TIME_SECONDS)+
           ";time_gmt="+TimeToString(TimeGMT(),TIME_DATE|TIME_SECONDS));
   DiagInteger("SYMBOL_CHART_MODE",SYMBOL_CHART_MODE);
   DiagLog("ENUMS;CHART_BID="+IntegerToString((int)SYMBOL_CHART_MODE_BID)+
           ";CHART_LAST="+IntegerToString((int)SYMBOL_CHART_MODE_LAST));
   DiagInteger("SYMBOL_TRADE_CALC_MODE",SYMBOL_TRADE_CALC_MODE);
   DiagInteger("SYMBOL_DIGITS",SYMBOL_DIGITS);
   DiagDouble("SYMBOL_TRADE_TICK_SIZE",SYMBOL_TRADE_TICK_SIZE);
   DiagDouble("SYMBOL_TRADE_TICK_VALUE",SYMBOL_TRADE_TICK_VALUE);
   DiagDouble("SYMBOL_POINT",SYMBOL_POINT);
   DiagLog("CURRENCIES;profit="+SymbolInfoString(_Symbol,SYMBOL_CURRENCY_PROFIT)+
           ";margin="+SymbolInfoString(_Symbol,SYMBOL_CURRENCY_MARGIN)+
           ";account="+AccountInfoString(ACCOUNT_CURRENCY));
   MqlTick current;ResetLastError();bool ok=SymbolInfoTick(_Symbol,current);
   int current_error=GetLastError();
   DiagLog("CURRENT_TICK;ok="+IntegerToString((int)ok)+";error="+IntegerToString(current_error));
   if(ok)DiagTick("CURRENT_TICK_DATA",current);
   MqlRates bars[];ResetLastError();
   int n=CopyRates(_Symbol,PERIOD_M1,D'2026.10.29 09:00:00',D'2026.10.29 09:00:59',bars);
   int rates_error=GetLastError();
   DiagLog("M1_QUERY;returned="+IntegerToString(n)+";error="+IntegerToString(rates_error));
   for(int i=0;i<n&&i<ArraySize(bars);i++)
      DiagLog("M1;time="+TimeToString(bars[i].time,TIME_DATE|TIME_SECONDS)+
              ";open="+DiagNumber(bars[i].open)+";high="+DiagNumber(bars[i].high)+
              ";low="+DiagNumber(bars[i].low)+";close="+DiagNumber(bars[i].close)+
              ";tick_volume="+IntegerToString(bars[i].tick_volume)+
              ";real_volume="+IntegerToString(bars[i].real_volume));
   DiagQuery("ALL",COPY_TICKS_ALL);
   DiagQuery("TRADE",COPY_TICKS_TRADE);
   DiagLog("END;SEM_ORDENS;SEM_ACEITE_DE_BACKTEST;CONSULTAR_TAMBEM_LOG_DO_MOTOR");
   EventKillTimer();ExpertRemove();
}

int OnInit()
{
   if(!MQLInfoInteger(MQL_TESTER)||MQLInfoInteger(MQL_OPTIMIZATION)||_Symbol!="WINZ26")
   {Print("MD_DIAG;RECUSADO;USAR_SOMENTE_TESTER_UNICO_WINZ26");return INIT_PARAMETERS_INCORRECT;}
   if(TimeCurrent()<D'2026.10.29 00:00:00'||TimeCurrent()>=D'2026.10.30 00:00:00')
   {Print("MD_DIAG;RECUSADO;INTERVALO_FIXO_29_OUTUBRO_2026");return INIT_PARAMETERS_INCORRECT;}
   diag_path="MD_DIAG_DADOS_20261029_"+IntegerToString((long)GetMicrosecondCount())+
             "_"+IntegerToString((long)GetTickCount64())+".txt";
   if(FileIsExist(diag_path,FILE_COMMON))return INIT_FAILED;
   diag_file=FileOpen(diag_path,FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_COMMON|FILE_SHARE_READ,0,CP_UTF8);
   if(diag_file==INVALID_HANDLE){Print("MD_DIAG;ARQUIVO_FALHOU;error=",GetLastError());return INIT_FAILED;}
   DiagLog("START;VERSION=1.00;TESTER_ONLY;SEM_ORDENS;symbol="+_Symbol+
           ";build="+IntegerToString(TerminalInfoInteger(TERMINAL_BUILD))+
           ";visual="+IntegerToString((int)MQLInfoInteger(MQL_VISUAL_MODE))+
           ";margin_mode="+IntegerToString(AccountInfoInteger(ACCOUNT_MARGIN_MODE)));
   DiagLog("REPORT;Common\\Files\\"+diag_path);
   if(!EventSetTimer(2)){DiagLog("TIMER_FAILED");return INIT_FAILED;}
   return INIT_SUCCEEDED;
}

void OnTick()
{
   if(!diag_first_tick&&TimeCurrent()>=D'2026.10.29 09:00:00')
   {
      MqlTick tick;if(SymbolInfoTick(_Symbol,tick))
      {diag_first_tick=true;DiagTick("FIRST_OBSERVED_EVENT_NOT_CERTIFIED_OPEN",tick);}
   }
   DiagProcess();
}
void OnTimer(){DiagProcess();}
void OnDeinit(const int reason)
{
   EventKillTimer();DiagLog("DEINIT;reason="+IntegerToString(reason)+";probe_executed="+IntegerToString((int)diag_done));
   if(diag_file!=INVALID_HANDLE){FileClose(diag_file);diag_file=INVALID_HANDLE;}
}
