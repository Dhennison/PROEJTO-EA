#property strict
#property version "1.00"
#property description "Audita fonte, CopyTicksRange e eventos OnTick. Sem ordens."
#include <ModeloD_PilotoControlado/Piloto_Core.mqh>
input string InpArquivoFonte=PH_DEFAULT_SOURCE;
MqlTick pilot_source[],pilot_events[];
int pilot_count=0;
long pilot_callbacks=0,pilot_symbolinfo_fail=0,pilot_outside=0,pilot_overflow=0;
bool pilot_init=false,pilot_finished=false,pilot_ontester=false;
string pilot_folder="";

int OnInit()
{
   long custom=0;
   if(!MQLInfoInteger(MQL_TESTER)||MQLInfoInteger(MQL_OPTIMIZATION)||
      StringFind(_Symbol,"MDDP29_")!=0||!SymbolInfoInteger(_Symbol,SYMBOL_CUSTOM,custom)||custom!=1)
   {Print("PILOTO100_TESTER;RECUSADO;SOMENTE_TESTER_LOCAL_SIMBOLO_MDDP29_CUSTOM");return INIT_PARAMETERS_INCORRECT;}
   if(TimeCurrent()<D'2026.10.29 00:00:00'||TimeCurrent()>=D'2026.10.30 00:00:00')
   {Print("PILOTO100_TESTER;RECUSADO;USAR_29_ATE_30_OUTUBRO");return INIT_PARAMETERS_INCORRECT;}
   string why="";
   if(!PHLoadPilot(InpArquivoFonte,pilot_source,why))
   {Print("PILOTO100_TESTER;SOURCE_FAILED;",why);return INIT_FAILED;}
   if(ArrayResize(pilot_events,PH_ROWS*3)!=PH_ROWS*3)
   {Print("PILOTO100_TESTER;SEM_MEMORIA_EVENTOS");return INIT_FAILED;}
   pilot_folder=PHFolder("TESTER");
   if(pilot_folder==""){Print("PILOTO100_TESTER;PASTA_FALHOU");return INIT_FAILED;}
   pilot_init=true;
   Print("PILOTO100_TESTER;START;v=1.00;SEM_ORDENS;symbol=",_Symbol,
         ";source_n=",ArraySize(pilot_source),";ON_TICK_ONLY_BUFFERING;pasta=Common\\Files\\",pilot_folder);
   return INIT_SUCCEEDED;
}
void OnTick()
{
   if(!pilot_init||pilot_finished)return;
   pilot_callbacks++;
   MqlTick tick;
   if(!SymbolInfoTick(_Symbol,tick)){pilot_symbolinfo_fail++;return;}
   if(tick.time_msc<(long)PH_FROM*1000||tick.time_msc>=(long)PH_TO*1000)
   {pilot_outside++;return;}
   if(pilot_count>=ArraySize(pilot_events)){pilot_overflow++;return;}
   pilot_events[pilot_count]=tick;pilot_count++;
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
   string report="PILOTO100_TESTER;v=1.00;SEM_ORDENS;trigger="+trigger+";symbol="+_Symbol+"\r\n";
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
   bool saved=PHText(pilot_folder+"\\RESULTADO.txt",report);
   Print("PILOTO100_TESTER;END;callbacks=",pilot_callbacks,";buffered=",pilot_count,
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
