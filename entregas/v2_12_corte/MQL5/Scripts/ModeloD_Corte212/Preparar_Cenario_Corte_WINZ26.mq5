#property strict
#property version "2.12"
#property description "Cria somente o simbolo SINTETICO de corte. Este script nao envia ordens."
#include "../../Include/ModeloD_Corte212/Cenario.mqh"
const string MD_CUT_SYMBOL="MD_SINT_CORTE_WINZ26";
int cut_report=INVALID_HANDLE;
void CutLog(string line){Print("CORTE212_PREP;",line);if(cut_report!=INVALID_HANDLE){FileWriteString(cut_report,line+"\r\n");FileFlush(cut_report);}}
void CutClose(){if(cut_report!=INVALID_HANDLE){FileClose(cut_report);cut_report=INVALID_HANDLE;}}
bool CutCheck(const MqlRates &prior[])
{
 MqlTick read[];ResetLastError();
 int n=CopyTicksRange(MD_CUT_SYMBOL,read,COPY_TICKS_ALL,(ulong)MD_CORTE212_BEGIN,(ulong)MD_CORTE212_END);
 int error=GetLastError();
 if(n!=MD_CORTE212_COUNT||error!=0){CutLog("READBACK_TICKS_FAILED;n="+IntegerToString(n)+";error="+IntegerToString(error));return false;}
 for(int i=0;i<n;i++)if(!MDCorteTickSame212(read[i],i)){CutLog("READBACK_TICK_DIFFERENT;index="+IntegerToString(i));return false;}
 MqlRates before[];ResetLastError();
 int p=CopyRates(MD_CUT_SYMBOL,PERIOD_M1,D'2026.10.29 00:00:00',D'2026.10.29 23:59:59',before);
 if(GetLastError()!=0||p!=ArraySize(prior)){CutLog("READBACK_PRIOR_FAILED");return false;}
 for(int i=0;i<p;i++)if(before[i].time!=prior[i].time||before[i].open!=prior[i].open||before[i].high!=prior[i].high||
  before[i].low!=prior[i].low||before[i].close!=prior[i].close||before[i].tick_volume!=prior[i].tick_volume||
  before[i].real_volume!=prior[i].real_volume||before[i].spread!=prior[i].spread){CutLog("READBACK_PRIOR_DIFFERENT");return false;}
 MqlRates bars[];ResetLastError();
 int count=CopyRates(MD_CUT_SYMBOL,PERIOD_M1,(datetime)(MD_CORTE212_BEGIN/60000*60),(datetime)(MD_CORTE212_END/1000),bars);
 int expected=(int)(MD_CORTE212_END/60000-MD_CORTE212_BEGIN/60000+1);
 if(GetLastError()!=0||count!=expected){CutLog("READBACK_M1_FAILED;bars="+IntegerToString(count));return false;}
 for(int i=0;i<count;i++){
  long minute=(MD_CORTE212_BEGIN/60000+i)*60000,from=minute,to=minute+59000;
  if(from<MD_CORTE212_BEGIN)from=MD_CORTE212_BEGIN;
  if(to>MD_CORTE212_END)to=MD_CORTE212_END;
  double o=MDCortePrice212(from),c=MDCortePrice212(to),h=o,l=o;
  for(long t=from;t<=to;t+=1000){double price=MDCortePrice212(t);if(price>h)h=price;if(price<l)l=price;}
  if(bars[i].time!=(datetime)(minute/1000)||bars[i].open!=o||bars[i].high!=h||bars[i].low!=l||bars[i].close!=c){CutLog("READBACK_M1_DIFFERENT;index="+IntegerToString(i));return false;}
 }
 CutLog("READBACK_OK;ticks="+IntegerToString(n)+";M1="+IntegerToString(count)+";prior_M1="+IntegerToString(p));return true;
}
void OnStart()
{
 if(MQLInfoInteger(MQL_TESTER)){Print("CORTE212_PREP;EXECUTAR_SCRIPT_NO_TERMINAL_SECUNDARIO");return;}
 string name="MD_CORTE212_PREPARACAO_"+IntegerToString((long)GetTickCount64())+"_"+IntegerToString((long)GetMicrosecondCount())+".txt";
 cut_report=FileOpen(name,FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_COMMON|FILE_SHARE_READ,0,CP_UTF8);
 if(cut_report==INVALID_HANDLE){Print("CORTE212_PREP;REPORT_FAILED;",GetLastError());return;}
 CutLog("START;CENARIO_SINTETICO;SCRIPT_SEM_ORDENS;REPORT=Common\\Files\\"+name);
 bool source_custom=false;
 if(!SymbolExist("WINZ26",source_custom)||source_custom||!SymbolSelect("WINZ26",true)){CutLog("WINZ26_REAL_INDISPONIVEL");CutClose();return;}
 MqlRates prior[];ResetLastError();
 int count=CopyRates("WINZ26",PERIOD_M1,D'2026.10.29 00:00:00',D'2026.10.29 23:59:59',prior);
 if(count<500||GetLastError()!=0){CutLog("HISTORICO_29_INDISPONIVEL;REEXECUTAR_APOS_CARREGAMENTO");CutClose();return;}
 for(int i=0;i<count;i++)if((i>0&&prior[i].time<=prior[i-1].time)||prior[i].time<D'2026.10.29 00:00:00'||prior[i].time>=D'2026.10.30 00:00:00'){
  CutLog("HISTORICO_29_FORA_ORDEM_OU_DATA");CutClose();return;
 }
 bool custom=false;
 if(SymbolExist(MD_CUT_SYMBOL,custom)){
  if(!custom){CutLog("NOME_EXISTENTE_NAO_CUSTOM;SEM_ALTERACAO");CutClose();return;}
  if(!SymbolSelect(MD_CUT_SYMBOL,true)){CutLog("SELECT_EXISTING_FAILED");CutClose();return;}
  if(CutCheck(prior))CutLog("READY;REUTILIZADO_SEM_ESCRITA;symbol="+MD_CUT_SYMBOL+";NENHUMA_ORDEM");
  else CutLog("EXISTENTE_DIVERGE;NENHUMA_ALTERACAO;ENVIAR_RELATORIO");
  CutClose();return;
 }
 ResetLastError();
 if(!CustomSymbolCreate(MD_CUT_SYMBOL,"ModeloD_SINTETICO_CORTE","WINZ26")){CutLog("CREATE_FAILED;error="+IntegerToString(GetLastError()));CutClose();return;}
 if(!SymbolSelect(MD_CUT_SYMBOL,true)){CutLog("SELECT_NEW_FAILED");CutClose();return;}
 CutLog("CREATED;APENAS_NOVO_SIMBOLO;symbol="+MD_CUT_SYMBOL);
 ResetLastError();int written=CustomRatesReplace(MD_CUT_SYMBOL,D'2026.10.29 00:00:00',D'2026.10.29 23:59:59',prior);
 if(written!=count||GetLastError()!=0){CutLog("PRIOR_COPY_FAILED;PRESERVAR_SIMBOLO");CutClose();return;}
 MqlTick ticks[];if(ArrayResize(ticks,MD_CORTE212_COUNT)!=MD_CORTE212_COUNT){CutLog("ALLOCATION_FAILED");CutClose();return;}
 for(int i=0;i<MD_CORTE212_COUNT;i++)MDCorteTick212(i,ticks[i]);
 ResetLastError();int imported=CustomTicksReplace(MD_CUT_SYMBOL,(ulong)MD_CORTE212_BEGIN,(ulong)MD_CORTE212_END,ticks);
 if(imported!=MD_CORTE212_COUNT||GetLastError()!=0){CutLog("SYNTHETIC_TICKS_FAILED;n="+IntegerToString(imported)+";error="+IntegerToString(GetLastError()));CutClose();return;}
 if(CutCheck(prior))CutLog("READY;CENARIO_SINTETICO;symbol="+MD_CUT_SYMBOL+";EA_TESTER_ONLY;NENHUMA_ORDEM");
 CutClose();
}
