#property strict
#property version "1.01"
#property script_show_inputs
#property description "Copia nova do piloto com M1 real anterior; preserva janela e copia original. Sem ordens."
#include <ModeloD_PilotoControlado/Piloto_Core.mqh>
input string InpCopiaOriginal="MDDP29_1794146086_769098390";
input string InpArquivoFonte=PH_DEFAULT_SOURCE;
string cx_folder="",cx_report="";
#define CX_CONTEXT_FROM D'2026.10.27 00:00:00'
#define CX_CONTEXT_TO D'2026.10.29 00:00:00'

void CXLog(const string line)
{cx_report+=line+"\r\n";Print("PILOTO101_CONTEXT;",line);}
void CXSave(){if(!PHText(cx_folder+"\\RESULTADO.txt",cx_report))Print("PILOTO101_CONTEXT;REPORT_WRITE_FAILED");}
bool CXSameRates(const MqlRates &a[],const MqlRates &b[])
{
   if(ArraySize(a)!=ArraySize(b))return false;
   for(int i=0;i<ArraySize(a);i++)
      if(a[i].time!=b[i].time||a[i].open!=b[i].open||a[i].high!=b[i].high||
         a[i].low!=b[i].low||a[i].close!=b[i].close||a[i].tick_volume!=b[i].tick_volume||
         a[i].spread!=b[i].spread||a[i].real_volume!=b[i].real_volume)return false;
   return true;
}
bool CXSafeContext(const MqlRates &bars[])
{
   long previous=-1;
   for(int i=0;i<ArraySize(bars);i++)
   {
      MqlRates b=bars[i];
      if(b.time<CX_CONTEXT_FROM||b.time>=CX_CONTEXT_TO||b.time%60!=0||b.time<=previous)return false;
      if(!MathIsValidNumber(b.open)||!MathIsValidNumber(b.high)||!MathIsValidNumber(b.low)||
         !MathIsValidNumber(b.close)||b.low<=0||b.low>MathMin(b.open,b.close)||
         b.high<MathMax(b.open,b.close)||b.tick_volume<0||b.real_volume<0)return false;
      previous=b.time;
   }
   return ArraySize(bars)>0;
}
int CXGroupsM5(const MqlRates &bars[])
{
   long previous=-1;int groups=0;
   for(int i=0;i<ArraySize(bars);i++)
   {long key=(long)bars[i].time/300;if(key!=previous){groups++;previous=key;}}
   return groups;
}
bool CXExportRates(const string path,const MqlRates &bars[])
{
   string text="time;open;high;low;close;tick_volume;spread;real_volume\r\n";
   for(int i=0;i<ArraySize(bars);i++)
      text+=(string)(long)bars[i].time+";"+PHNum(bars[i].open)+";"+PHNum(bars[i].high)+";"+
         PHNum(bars[i].low)+";"+PHNum(bars[i].close)+";"+(string)bars[i].tick_volume+";"+
         (string)bars[i].spread+";"+(string)bars[i].real_volume+"\r\n";
   return PHText(path,text);
}
bool CXReadTicks(const string symbol,MqlTick &ticks[])
{
   MqlTick previous[];bool have=false;
   for(int attempt=1;attempt<=6&&!IsStopped();attempt++)
   {
      ResetLastError();int n=CopyTicksRange(symbol,ticks,COPY_TICKS_ALL,(ulong)PH_FROM*1000,(ulong)PH_TO*1000-1);
      int err=GetLastError();CXLog("READ_TICKS;symbol="+symbol+";attempt="+(string)attempt+";n="+(string)n+";error="+(string)err);
      bool valid=n==PH_ROWS&&err==0&&n==ArraySize(ticks);
      if(valid&&have&&PHSame(previous,ticks))return true;
      have=valid;
      if(valid){if(ArrayResize(previous,n)!=n||ArrayCopy(previous,ticks)!=n)return false;}
      Sleep(250);
   }
   return false;
}
bool CXReadRates(const string symbol,const datetime from,const datetime to,MqlRates &bars[])
{
   MqlRates previous[];bool have=false;
   for(int attempt=1;attempt<=6&&!IsStopped();attempt++)
   {
      CXLog("READ_M1_BEGIN;symbol="+symbol+";attempt="+(string)attempt+";from="+TimeToString(from,TIME_DATE|TIME_SECONDS));
      ResetLastError();int n=CopyRates(symbol,PERIOD_M1,from,to-1,bars);int err=GetLastError();
      CXLog("READ_M1_END;symbol="+symbol+";n="+(string)n+";error="+(string)err);
      bool valid=n>0&&err==0&&n==ArraySize(bars);
      if(valid&&have&&CXSameRates(previous,bars))return true;
      have=valid;
      if(valid){if(ArrayResize(previous,n)!=n||ArrayCopy(previous,bars)!=n)return false;}
      Sleep(250);
   }
   return false;
}
// Comparison view only. The source array and all imported ticks stay untouched.
bool CXMatchesObservedMapping(const MqlTick &source[],const MqlTick &stored[])
{
   if(ArraySize(source)!=ArraySize(stored))return false;
   for(int i=0;i<ArraySize(source);i++)
   {
      MqlTick expected=source[i];expected.flags&=126;
      if(!PHSameTick(expected,stored[i]))return false;
   }
   return true;
}
void OnStart()
{
   if(MQLInfoInteger(MQL_TESTER)){Print("PILOTO101_CONTEXT;TERMINAL_ONLY");return;}
   cx_folder=PHFolder("CONTEXT");if(cx_folder=="")return;
   CXLog("START;v=1.01;SEM_ORDENS;ORIGINAL_COPY_READ_ONLY;source_symbol="+InpCopiaOriginal);
   CXLog("CONTEXT_PROVENANCE;native=WINZ26;period=M1;from=2026.10.27;to_exclusive=2026.10.29;NO_WARMUP_TICKS;NO_SYNTHETIC_BARS");
   MqlTick source[],baseline[];string why="";
   if(!PHLoadPilot(InpArquivoFonte,source,why)){CXLog("SOURCE_FAILED;"+why);CXSave();return;}
   bool original_custom=false;
   if(StringFind(InpCopiaOriginal,"MDDP29_")!=0||!SymbolExist(InpCopiaOriginal,original_custom)||
      !original_custom||!SymbolSelect(InpCopiaOriginal,true))
   {CXLog("ORIGINAL_CUSTOM_GUARD_FAILED");CXSave();return;}
   if(!CXReadTicks(InpCopiaOriginal,baseline)||!CXMatchesObservedMapping(source,baseline))
   {CXLog("ORIGINAL_SNAPSHOT_DIFFERS_FROM_AUDITED_MAPPING");CXSave();return;}
   CXLog("ORIGINAL_SNAPSHOT_CONFERRED;"+PHStats(baseline));
   MqlRates original_target[],context[];
   if(!CXReadRates(InpCopiaOriginal,PH_FROM,PH_TO,original_target)||ArraySize(original_target)!=10)
   {CXLog("ORIGINAL_TARGET_M1_UNAVAILABLE");CXSave();return;}
   long native_custom=0;
   if(!SymbolSelect("WINZ26",true)||!SymbolInfoInteger("WINZ26",SYMBOL_CUSTOM,native_custom)||native_custom!=0)
   {CXLog("NATIVE_CONTEXT_SOURCE_UNAVAILABLE");CXSave();return;}
   if(!CXReadRates("WINZ26",CX_CONTEXT_FROM,CX_CONTEXT_TO,context)||!CXSafeContext(context)||CXGroupsM5(context)<200)
   {CXLog("CONTEXT_PENDING;NEEDS_200_REAL_PREVIOUS_M5_GROUPS;NO_SYNTHETIC_FILL");CXSave();return;}
   if(!CXExportRates(cx_folder+"\\CONTEXT_SOURCE_M1.csv",context)||
      !CXExportRates(cx_folder+"\\ORIGINAL_TARGET_M1.csv",original_target))
   {CXLog("SOURCE_EXPORT_FAILED");CXSave();return;}
   string symbol="MDDP29_"+(string)(long)TimeLocal()+"_"+(string)GetTickCount();bool existing=false;
   if(StringLen(symbol)>31||SymbolExist(symbol,existing))
   {CXLog("NEW_NAME_UNAVAILABLE");CXSave();return;}
   ResetLastError();bool created=CustomSymbolCreate(symbol,"ModeloD_Piloto","WINZ26");int err=GetLastError();
   CXLog("NEW_COPY;symbol="+symbol+";created="+(string)(int)created+";error="+(string)err);
   bool custom=false;
   if(!created||!SymbolExist(symbol,custom)||!custom||StringFind(symbol,"MDDP29_")!=0)
   {CXLog("NEW_CUSTOM_GUARD_FAILED");CXSave();return;}
   if(!CustomSymbolSetInteger(symbol,SYMBOL_CHART_MODE,SYMBOL_CHART_MODE_LAST)||!SymbolSelect(symbol,true))
   {CXLog("CUSTOM_MODE_FAILED;error="+(string)GetLastError());CXSave();return;}
   int start=0,total=0;
   while(start<ArraySize(baseline)&&!IsStopped())
   {
      int end=PHBatchEnd(baseline,start,100000),count=end-start;MqlTick batch[];
      if(count<=0||ArrayResize(batch,count)!=count||ArrayCopy(batch,baseline,0,start,count)!=count)
      {CXLog("BATCH_COPY_FAILED");CXSave();return;}
      ResetLastError();int added=CustomTicksReplace(symbol,baseline[start].time_msc,baseline[end-1].time_msc,batch);err=GetLastError();
      CXLog("COPY_BATCH;expected="+(string)count+";returned="+(string)added+";error="+(string)err);
      if(added!=count||err!=0){CXLog("COPY_FAILED");CXSave();return;}
      total+=added;start=end;
   }
   if(total!=PH_ROWS){CXLog("COPY_INTERRUPTED");CXSave();return;}
   MqlTick before[],after[];MqlRates before_target[],after_target[],context_back[];
   if(!CXReadTicks(symbol,before)||!PHSame(baseline,before)||
      !CXReadRates(symbol,PH_FROM,PH_TO,before_target)||!CXSameRates(original_target,before_target))
   {CXLog("COPY_NOT_IDENTICAL_TO_BASELINE;NO_CONTEXT_WRITTEN");CXSave();return;}
   CXLog("NEW_COPY_BASELINE_EXACT;target_ticks_and_M1_preserved");
   // The guard proves every written context bar precedes the target day.
   if(!CXSafeContext(context)){CXLog("CONTEXT_RANGE_GUARD_FAILED");CXSave();return;}
   ResetLastError();int changed=CustomRatesUpdate(symbol,context);err=GetLastError();
   CXLog("REAL_PREVIOUS_M1_WRITE;expected="+(string)ArraySize(context)+";returned="+(string)changed+";error="+(string)err);
   if(changed!=ArraySize(context)||err!=0){CXLog("CONTEXT_WRITE_FAILED");CXSave();return;}
   bool ticks_ok=CXReadTicks(symbol,after)&&PHSame(before,after);
   bool target_ok=CXReadRates(symbol,PH_FROM,PH_TO,after_target)&&CXSameRates(before_target,after_target);
   bool context_ok=CXReadRates(symbol,CX_CONTEXT_FROM,CX_CONTEXT_TO,context_back)&&CXSameRates(context,context_back);
   bool files=PHExport(cx_folder+"\\TARGET_TICKS_AFTER_CONTEXT.csv",after);
   files=CXExportRates(cx_folder+"\\TARGET_M1_AFTER_CONTEXT.csv",after_target)&&files;
   files=CXExportRates(cx_folder+"\\CONTEXT_READBACK_M1.csv",context_back)&&files;
   CXLog("SOURCE_FULL_COMPARE;"+PHCompare(source,after));
   CXLog("BASELINE_EXACT_COMPARE;"+PHCompare(baseline,after));
   CXLog("END;symbol="+symbol+";target_ticks_equal="+(string)(int)ticks_ok+
      ";target_M1_equal="+(string)(int)target_ok+";context_M1_equal="+(string)(int)context_ok+
      ";prior_M5_groups="+(string)CXGroupsM5(context_back)+";exports_ok="+(string)(int)files);
   CXLog("ORIGINAL_UNCHANGED;NO_TARGET_M1_REBUILD;NO_DATE_GUARD_WEAKENING;TESTER_AND_ONTICK_PENDING;pasta=Common\\Files\\"+cx_folder);
   CXSave();
}
