#property strict
#property version "1.00"
#property description "Sonda amostral de ticks antigos. Somente leitura, sem ordens."
#include <ModeloD_PilotoControlado/Piloto_Core.mqh>
input string InpPlano="SONDA_PILOTO_9_JANELAS.csv";
input int InpMaxTentativas=6;
struct PHProbeTask { string symbol;datetime from;datetime to; };
PHProbeTask probe_tasks[];
MqlTick probe_previous[];
int probe_index=0,probe_attempt=0,probe_file=INVALID_HANDLE;
bool probe_previous_valid=false,probe_done=false,probe_init=false;
string probe_folder="";

bool ProbeLoad()
{
   int file=FileOpen(InpPlano,FILE_READ|FILE_CSV|FILE_ANSI,';',CP_UTF8);
   if(file==INVALID_HANDLE)return false;
   string h=FileReadString(file);
   if(StringLen(h)>0&&StringGetCharacter(h,0)==0xFEFF)h=StringSubstr(h,1);
   if(h!="simbolo"||FileReadString(file)!="de"||FileReadString(file)!="ate"||!FileIsLineEnding(file))
   {FileClose(file);return false;}
   while(!FileIsEnding(file))
   {
      string symbol=FileReadString(file);if(symbol==""&&FileIsEnding(file))break;
      if(FileIsLineEnding(file)||FileIsEnding(file)){FileClose(file);return false;}
      string from=FileReadString(file);
      if(FileIsLineEnding(file)||FileIsEnding(file)){FileClose(file);return false;}
      string to=FileReadString(file);
      if(!FileIsLineEnding(file)&&!FileIsEnding(file)){FileClose(file);return false;}
      datetime a=StringToTime(from),b=StringToTime(to);int n=ArraySize(probe_tasks);
      if(n>=128||symbol==""||a<=0||b<=a||b-a>600||b>TimeLocal())
      {FileClose(file);return false;}
      if(ArrayResize(probe_tasks,n+1)!=n+1){FileClose(file);return false;}
      probe_tasks[n].symbol=symbol;probe_tasks[n].from=a;probe_tasks[n].to=b;
   }
   FileClose(file);return ArraySize(probe_tasks)>0;
}
void ProbeAdvance(const string state,const int n,const int err,const int business,const ulong hash,const bool stable)
{
   PHProbeTask task=probe_tasks[probe_index];
   string row=(string)(probe_index+1)+";"+task.symbol+";"+
      TimeToString(task.from,TIME_DATE|TIME_SECONDS)+";"+TimeToString(task.to,TIME_DATE|TIME_SECONDS)+";"+
      state+";"+(string)probe_attempt+";"+(string)n+";"+(string)err+";"+(string)business+";"+
      (string)hash+";"+(string)(int)stable+";CALENDAR_CANDIDATE_ONLY;SERVER_TIME_NOT_CERTIFIED\r\n";
   FileWriteString(probe_file,row);FileFlush(probe_file);
   Print("PILOTO100_SONDA;TASK_END;",row);
   probe_index++;probe_attempt=0;probe_previous_valid=false;ArrayResize(probe_previous,0);
   if(probe_index>=ArraySize(probe_tasks))
   {
      probe_done=true;EventKillTimer();
      Print("PILOTO100_SONDA;END;tasks=",probe_index,";AMOSTRA_NAO_CERTIFICA_RETENCAO_TOTAL;pasta=",probe_folder);
      ExpertRemove();
   }
}
int OnInit()
{
   if(MQLInfoInteger(MQL_TESTER)||InpMaxTentativas<2||InpMaxTentativas>20)
   {Print("PILOTO100_SONDA;RECUSADO;TERMINAL_ONLY;TENTATIVAS_2_A_20");return INIT_PARAMETERS_INCORRECT;}
   if(!ProbeLoad()){Print("PILOTO100_SONDA;PLANO_INVALIDO;MQL5\\Files\\",InpPlano,";erro=",GetLastError());return INIT_FAILED;}
   probe_folder=PHFolder("SONDA");if(probe_folder=="")return INIT_FAILED;
   probe_file=FileOpen(probe_folder+"\\DIAS.csv",FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_COMMON|FILE_SHARE_READ,0,CP_UTF8);
   if(probe_file==INVALID_HANDLE)return INIT_FAILED;
   FileWriteString(probe_file,"task;symbol;from_server;to_exclusive;state;attempts;ALL;error;business_flags_Last;hash;stable;contract_status;timezone_status\r\n");
   FileFlush(probe_file);
   if(!EventSetTimer(2))return INIT_FAILED;
   probe_init=true;
   Print("PILOTO100_SONDA;START;SOMENTE_LEITURA;SEM_ORDENS;tasks=",ArraySize(probe_tasks),";pasta=",probe_folder);
   return INIT_SUCCEEDED;
}
void OnTimer()
{
   if(!probe_init||probe_done||IsStopped())return;
   PHProbeTask task=probe_tasks[probe_index];probe_attempt++;
   ResetLastError();bool custom=false;
   if(!SymbolExist(task.symbol,custom))
   {ProbeAdvance("SYMBOL_NOT_REGISTERED_NO_RETENTION_INFERENCE",-1,GetLastError(),0,0,false);return;}
   if(custom)
   {ProbeAdvance("CUSTOM_REFUSED",-1,0,0,0,false);return;}
   ResetLastError();
   if(!SymbolSelect(task.symbol,true))
   {ProbeAdvance("SYMBOL_SELECT_FAILED",-1,GetLastError(),0,0,false);return;}
   Print("PILOTO100_SONDA;QUERY_BEGIN;task=",probe_index+1,";attempt=",probe_attempt,
      ";symbol=",task.symbol,";from=",TimeToString(task.from,TIME_DATE|TIME_SECONDS));
   MqlTick ticks[];ResetLastError();ulong begin=GetTickCount64();
   int n=CopyTicksRange(task.symbol,ticks,COPY_TICKS_ALL,(ulong)task.from*1000,(ulong)task.to*1000-1);
   int err=GetLastError();
   Print("PILOTO100_SONDA;QUERY_END;n=",n,";error=",err,";duration_ms=",GetTickCount64()-begin);
   string why="";bool valid=n>=0&&err==0&&n==ArraySize(ticks)&&n<=1000000;
   if(valid)valid=PHValidTicks(ticks,(long)task.from*1000,(long)task.to*1000,why);
   bool stable=valid&&probe_previous_valid&&PHSame(probe_previous,ticks);
   int business=0;ulong hash=0;
   if(valid)
   {
      hash=PHHash(ticks);
      for(int i=0;i<n;i++)if(PHBusiness(ticks[i]))business++;
   }
   if(stable)
   {
      string state=(business>0?"STABLE_BUSINESS_PRESENT":(n>0?"STABLE_QUOTES_ONLY":"STABLE_EMPTY_WINDOW"));
      ProbeAdvance(state,n,err,business,hash,true);return;
   }
   if(probe_attempt>=InpMaxTentativas)
   {ProbeAdvance("PENDING_ERROR_OR_NOT_STABLE",n,err,business,hash,false);return;}
   probe_previous_valid=valid;
   if(valid)
   {
      if(ArrayResize(probe_previous,n)!=n)
      {ProbeAdvance("PENDING_MEMORY_FAILURE",n,err,business,hash,false);return;}
      if(n>0&&ArrayCopy(probe_previous,ticks)!=n)
      {ProbeAdvance("PENDING_COPY_FAILURE",n,err,business,hash,false);return;}
   }
   else ArrayResize(probe_previous,0);
}
void OnDeinit(const int reason)
{
   EventKillTimer();
   if(probe_file!=INVALID_HANDLE){FileClose(probe_file);probe_file=INVALID_HANDLE;}
   if(probe_folder!="")
   {
      string meta="PILOTO100_SONDA;SEM_ORDENS;server="+AccountInfoString(ACCOUNT_SERVER)+
         ";build="+(string)TerminalInfoInteger(TERMINAL_BUILD)+";plan="+InpPlano+
         ";completed="+(string)probe_index+";tasks="+(string)ArraySize(probe_tasks)+
         ";done="+(string)(int)probe_done+";deinit_reason="+(string)reason+"\r\n";
      meta+="EMPTY_WINDOW_IS_NOT_GLOBAL_ABSENCE;UNKNOWN_SYMBOL_IS_NOT_NO_TICKS;CALENDAR_CANDIDATES_ONLY\r\n";
      PHText(probe_folder+"\\META.txt",meta);
   }
}
