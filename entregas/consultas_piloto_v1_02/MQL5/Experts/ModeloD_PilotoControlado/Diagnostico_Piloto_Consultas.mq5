#property strict
#property version "1.02"
#property description "Controla ALL/TRADE/INFO, minutos e callbacks com estrutura zerada. Sem ordens."
#include <ModeloD_PilotoControlado/Piloto_Core.mqh>
input string InpArquivoFonte=PH_DEFAULT_SOURCE;
MqlTick pilot_source[],pilot_events[];
int pilot_count=0;
long pilot_callbacks=0,pilot_symbolinfo_fail=0,pilot_outside=0,pilot_overflow=0;
bool pilot_init=false,pilot_finished=false,pilot_ontester=false;
string pilot_folder="";
string query_audit="";

int OnInit()
{
   long custom=0;
   if(!MQLInfoInteger(MQL_TESTER)||MQLInfoInteger(MQL_OPTIMIZATION)||
      StringFind(_Symbol,"MDDP29_")!=0||!SymbolInfoInteger(_Symbol,SYMBOL_CUSTOM,custom)||custom!=1)
   {Print("PILOTO102_QUERY;RECUSADO;SOMENTE_TESTER_LOCAL_SIMBOLO_MDDP29_CUSTOM");return INIT_PARAMETERS_INCORRECT;}
   if(TimeCurrent()<D'2026.10.29 00:00:00'||TimeCurrent()>=D'2026.10.30 00:00:00')
   {Print("PILOTO102_QUERY;RECUSADO;USAR_29_ATE_30_OUTUBRO");return INIT_PARAMETERS_INCORRECT;}
   string why="";
   if(!PHLoadPilot(InpArquivoFonte,pilot_source,why))
   {Print("PILOTO102_QUERY;SOURCE_FAILED;",why);return INIT_FAILED;}
   if(ArrayResize(pilot_events,PH_ROWS*3)!=PH_ROWS*3)
   {Print("PILOTO102_QUERY;SEM_MEMORIA_EVENTOS");return INIT_FAILED;}
   pilot_folder=PHFolder("QUERIES102");
   if(pilot_folder==""){Print("PILOTO102_QUERY;PASTA_FALHOU");return INIT_FAILED;}
   pilot_init=true;
   Print("PILOTO102_QUERY;START;v=1.02;SEM_ORDENS;symbol=",_Symbol,
         ";source_n=",ArraySize(pilot_source),";ON_TICK_ONLY_BUFFERING;pasta=Common\\Files\\",pilot_folder);
   return INIT_SUCCEEDED;
}
void OnTick()
{
   if(!pilot_init||pilot_finished)return;
   pilot_callbacks++;
   MqlTick tick;ZeroMemory(tick);
   if(!SymbolInfoTick(_Symbol,tick)){pilot_symbolinfo_fail++;return;}
   if(tick.time_msc<(long)PH_FROM*1000||tick.time_msc>=(long)PH_TO*1000)
   {pilot_outside++;return;}
   if(pilot_count>=ArraySize(pilot_events)){pilot_overflow++;return;}
   pilot_events[pilot_count]=tick;pilot_count++;
}
// Additional queries run only after the event stream finishes.
bool QueryRead(const string label,const uint mode,const long lo,const long hi,MqlTick &result[])
{
   Print("PILOTO102_QUERY;QUERY_BEGIN;label=",label,";mode=",mode);
   MqlTick first[],second[];
   ResetLastError();int n1=CopyTicksRange(_Symbol,first,mode,(ulong)lo,(ulong)(hi-1));int err1=GetLastError();
   ResetLastError();int n2=CopyTicksRange(_Symbol,second,mode,(ulong)lo,(ulong)(hi-1));int err2=GetLastError();
   bool valid1=n1>=0&&err1==0&&n1==ArraySize(first);
   bool valid2=n2>=0&&err2==0&&n2==ArraySize(second);
   string why1="",why2="";
   if(valid1)valid1=PHValidTicks(first,lo,hi,why1);
   if(valid2)valid2=PHValidTicks(second,lo,hi,why2);
   bool stable=valid1&&valid2&&PHSame(first,second);
   query_audit+="QUERY_MODE;label="+label+";mode="+(string)mode+";from="+(string)lo+
      ";to_exclusive="+(string)hi+";n1="+(string)n1+";error1="+(string)err1+
      ";n2="+(string)n2+";error2="+(string)err2+";stable="+(string)(int)stable+"\r\n";
   if(valid2)
   {
      if(ArrayResize(result,n2)!=n2){query_audit+="QUERY_COPY_MEMORY_FAILED\r\n";return false;}
      if(n2>0&&ArrayCopy(result,second)!=n2){query_audit+="QUERY_COPY_FAILED\r\n";return false;}
      bool saved=PHExport(pilot_folder+"\\"+label+".csv",result);
      query_audit+="QUERY_MODE_STATS;label="+label+";"+PHStats(result)+";"+PHFlagHistogram(result)+
         ";export_ok="+(string)(int)saved+"\r\n";
   }
   else ArrayResize(result,0);
   Print("PILOTO102_QUERY;QUERY_END;label=",label,";n=",n2,";error=",err2,";stable=",stable);
   return stable;
}
void QueryAudit()
{
   long lo=(long)PH_FROM*1000,hi=(long)PH_TO*1000;
   MqlTick trades[],information[],source_trades[],source_info[];
   if(ArrayResize(source_trades,PH_ROWS)!=PH_ROWS||ArrayResize(source_info,PH_ROWS)!=PH_ROWS)
   {query_audit+="SOURCE_FILTER_MEMORY_FAILED\r\n";return;}
   int nt=0,ni=0;
   for(int i=0;i<ArraySize(pilot_source);i++)
   {
      if(PHBusiness(pilot_source[i])){source_trades[nt]=pilot_source[i];nt++;}
      if((pilot_source[i].flags&6)!=0){source_info[ni]=pilot_source[i];ni++;}
   }
   ArrayResize(source_trades,nt);ArrayResize(source_info,ni);
   bool trade_ok=QueryRead("MODE_TRADE",COPY_TICKS_TRADE,lo,hi,trades);
   bool info_ok=QueryRead("MODE_INFO",COPY_TICKS_INFO,lo,hi,information);
   query_audit+="MODE_TRADE_SOURCE_COMPARE;stable="+(string)(int)trade_ok+";"+PHCompare(source_trades,trades)+"\r\n";
   query_audit+="MODE_INFO_SOURCE_COMPARE;stable="+(string)(int)info_ok+";"+PHCompare(source_info,information)+"\r\n";
   MqlTick combined[];
   if(ArrayResize(combined,PH_ROWS*3)!=PH_ROWS*3){query_audit+="COMBINED_MEMORY_FAILED\r\n";return;}
   int used=0;bool minute_ok=true;
   for(int minute=0;minute<10;minute++)
   {
      MqlTick part[];long begin=lo+(long)minute*60000;
      bool ok=QueryRead("MINUTE_"+IntegerToString(minute),COPY_TICKS_ALL,begin,begin+60000,part);
      int n=ArraySize(part);
      if(!ok||used+n>ArraySize(combined)){minute_ok=false;break;}
      if(n>0&&ArrayCopy(combined,part,used,0,n)!=n){minute_ok=false;break;}
      used+=n;
   }
   ArrayResize(combined,used);bool saved=PHExport(pilot_folder+"\\MINUTES_COMBINED.csv",combined);
   query_audit+="MINUTES_COMBINED;complete="+(string)(int)minute_ok+";export_ok="+(string)(int)saved+
      ";"+PHCompare(pilot_source,combined)+"\r\n";
   // Controls for the exact timestamp that lost two rows in the first snapshot.
   MqlTick group_all[],group_trade[],final_all[];
   QueryRead("GROUP_ALL",COPY_TICKS_ALL,1793264548680,1793264548681,group_all);
   QueryRead("GROUP_TRADE",COPY_TICKS_TRADE,1793264548680,1793264548681,group_trade);
   QueryRead("ALL_AFTER_MODES",COPY_TICKS_ALL,lo,hi,final_all);
   query_audit+="ALL_AFTER_SOURCE_COMPARE;"+PHCompare(pilot_source,final_all)+"\r\n";
   query_audit+="CONTROLS;ONTICK_LOCAL_STRUCT_ZEROED_BEFORE_SYMBOLINFOTICK;NO_SOURCE_OR_CUSTOM_MUTATION;NO_FILTER_OR_FLAG_REPAIR\r\n";
}
void PilotFinish(const string trigger)
{
   if(!pilot_init||pilot_finished)return;
   pilot_finished=true;ArrayResize(pilot_events,pilot_count);
   // OnTick contains no file writes, hashes, queries or dynamic resizing.
   MqlTick query1[],query2[];
   ResetLastError();int n1=CopyTicksRange(_Symbol,query1,COPY_TICKS_ALL,(ulong)PH_FROM*1000,(ulong)PH_TO*1000-1);
   int e1=GetLastError();
   ResetLastError();int n2=CopyTicksRange(_Symbol,query2,COPY_TICKS_ALL,(ulong)PH_FROM*1000,(ulong)PH_TO*1000-1);
   int e2=GetLastError();
   bool valid1=n1>=0&&e1==0&&n1==ArraySize(query1);
   bool valid2=n2>=0&&e2==0&&n2==ArraySize(query2);
   bool stable=valid1&&valid2&&PHSame(query1,query2);
   string why="";bool events_valid=PHValidTicks(pilot_events,(long)PH_FROM*1000,(long)PH_TO*1000,why);
   string report="PILOTO102_QUERY;v=1.02;SEM_ORDENS;trigger="+trigger+";symbol="+_Symbol+"\r\n";
   report+="source="+InpArquivoFonte+";source_time_seconds=derived_from_time_msc;NO_TIMEZONE_SHIFT\r\n";
   report+="callbacks="+(string)pilot_callbacks+";buffered="+(string)pilot_count+
      ";symbolinfo_fail="+(string)pilot_symbolinfo_fail+";outside="+(string)pilot_outside+
      ";overflow="+(string)pilot_overflow+";OnTester_called="+(string)(int)pilot_ontester+"\r\n";
   report+="QUERY_1;n="+(string)n1+";error="+(string)e1+"\r\nQUERY_2;n="+(string)n2+
      ";error="+(string)e2+";stable="+(string)(int)stable+"\r\n";
   report+="SOURCE_STATS;"+PHStats(pilot_source)+"\r\nONTICK_STATS;"+PHStats(pilot_events)+"\r\n";
   report+="ONTICK_COMPARE;"+PHCompare(pilot_source,pilot_events)+"\r\n";
   report+=PHTimeCoverage(pilot_source,pilot_events)+"\r\n";
   report+="SOURCE_"+PHFlagHistogram(pilot_source)+"\r\nONTICK_"+PHFlagHistogram(pilot_events)+"\r\n";
   report+="ONTICK_STRUCTURAL_VALID="+(string)(int)events_valid+";"+why+"\r\n";
   report+="ONTICK_ORDERED_SUBSEQUENCE_SOURCE="+(string)(int)PHSubsequence(pilot_source,pilot_events)+"\r\n";
   if(valid2)report+="TESTER_QUERY_COMPARE;"+PHCompare(pilot_source,query2)+"\r\n";
   bool events_export=PHExport(pilot_folder+"\\ONTICK.csv",pilot_events);
   bool query_export=valid2&&PHExport(pilot_folder+"\\TESTER_COPYTICKS.csv",query2);
   report+=PHCheckBars(_Symbol,pilot_source,pilot_folder+"\\TESTER_M1.csv")+"\r\n";
   report+="EXPORTS;events="+(string)(int)events_export+";query="+(string)(int)query_export+"\r\n";
   report+="HISTORY_EXACT="+(string)(int)(stable&&PHSame(pilot_source,query2))+
      ";ONTICK_EXACT="+(string)(int)PHSame(pilot_source,pilot_events)+"\r\n";
   report+="LIMITS;CALLBACK_COALESCENCE_POSSIBLE;NO_AUTOMATIC_DATA_LOSS_INFERENCE;CHECK_TESTER_DIARY_FOR_DISCARD\r\n";
   report+="NO_EA_STRATEGY_HOMOLOGATION;NO_WORK_OPERATION_RESULT;ONLY_TEN_MINUTES\r\n";
   QueryAudit();
   report+=query_audit;
   bool saved=PHText(pilot_folder+"\\RESULTADO.txt",report);
   Print("PILOTO102_QUERY;END;callbacks=",pilot_callbacks,";buffered=",pilot_count,
      ";history_exact=",(stable&&PHSame(pilot_source,query2)),
      ";ontick_exact=",PHSame(pilot_source,pilot_events),";overflow=",pilot_overflow,
      ";export_events=",events_export,";export_query=",query_export,";report_ok=",saved,
      ";pasta=Common\\Files\\",pilot_folder);
}
double OnTester()
{
   pilot_ontester=true;PilotFinish("ONTESTER");return 0.0;
}
void OnDeinit(const int reason)
{
   PilotFinish("ONDEINIT_"+IntegerToString(reason));
}
