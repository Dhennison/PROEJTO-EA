#property strict
#property version "1.10"
#property description "Exportacao M1 mensal, somente leitura, sem estrategia ou ordens. Rodar em grafico do terminal Genial."
#include <ModeloD_PilotoWINN_Periodo/Piloto_Especificacao.mqh>
input string InpSymbol="WIN$N";
input datetime InpInicio=D'2023.03.01 00:00:00';
input datetime InpFim=D'2026.09.22 00:00:00'; // exclusivo
input int InpMaxTentativasPorMes=10;
datetime pe_cursor=0,pe_end=0;int pe_attempt=0,pe_months=0,pe_pending=0;
long pe_total_rows=0;bool pe_have=false,pe_done=false,pe_io_failed=false;
MqlRates pe_previous[];string pe_folder="";int pe_status=INVALID_HANDLE;
string PEN(double x){return DoubleToString(x,16);}
datetime PENextMonth(datetime stamp)
{
 MqlDateTime parts;ZeroMemory(parts);if(!TimeToStruct(stamp,parts))return 0;
 parts.day=1;parts.hour=0;parts.min=0;parts.sec=0;parts.mon++;
 if(parts.mon>12){parts.mon=1;parts.year++;}return StructToTime(parts);
}
string PEMonth(datetime stamp)
{
 MqlDateTime parts;ZeroMemory(parts);TimeToStruct(stamp,parts);
 return IntegerToString(parts.year)+(parts.mon<10?"0":"")+IntegerToString(parts.mon);
}
bool PEMidnight(datetime stamp)
{
 MqlDateTime p;ZeroMemory(p);return TimeToStruct(stamp,p)&&p.hour==0&&p.min==0&&p.sec==0;
}
bool PEValid(const MqlRates &r)
{
 return MathIsValidNumber(r.open)&&r.open>0&&MathIsValidNumber(r.high)&&r.high>0&&MathIsValidNumber(r.low)&&r.low>0&&MathIsValidNumber(r.close)&&r.close>0&&
  r.low<=r.open&&r.open<=r.high&&r.low<=r.close&&r.close<=r.high&&r.low<=r.high&&r.tick_volume>=0&&r.real_volume>=0;
}
bool PESame(const MqlRates &a[],const MqlRates &b[])
{
 int n=ArraySize(a);if(n!=ArraySize(b))return false;
 for(int j=0;j<n;j++)if(a[j].time!=b[j].time||a[j].open!=b[j].open||a[j].high!=b[j].high||a[j].low!=b[j].low||a[j].close!=b[j].close||
  a[j].tick_volume!=b[j].tick_volume||a[j].real_volume!=b[j].real_volume||a[j].spread!=b[j].spread)return false;
 return true;
}
bool PEWrite(string name,string body)
{
 int h=FileOpen(pe_folder+"\\"+name,FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_COMMON,0,CP_UTF8);if(h==INVALID_HANDLE){pe_io_failed=true;return false;}
 ResetLastError();uint n=FileWriteString(h,body);FileFlush(h);int error=GetLastError();FileClose(h);bool ok=n>0&&error==0;
 if(!ok)pe_io_failed=true;
 return ok;
}
void PEStatus(string state,int n,int error,string file)
{
 string row=TimeToString(pe_cursor,TIME_DATE|TIME_SECONDS)+";"+TimeToString(pe_end,TIME_DATE|TIME_SECONDS)+";"+state+";"+
  IntegerToString(pe_attempt)+";"+IntegerToString(n)+";"+IntegerToString(error)+";"+file+"\r\n";
 ResetLastError();uint written=FileWriteString(pe_status,row);FileFlush(pe_status);if(written==0||GetLastError()!=0)pe_io_failed=true;
 Print("M1EXP110;",row);
}
void PEComplete()
{
 pe_done=true;EventKillTimer();Print("M1EXP110;END;months=",pe_months,";pending_months=",pe_pending,";rows=",pe_total_rows,
  ";io_failed=",pe_io_failed,";Common\\Files\\",pe_folder,";SOMENTE_LEITURA;COBERTURA_WORK_A_CONFERIR");ExpertRemove();
}
void OnTimer()
{
 if(pe_done)return;
 if(pe_io_failed){PEComplete();return;}
 if(pe_cursor>=InpFim){PEComplete();return;}
 pe_attempt++;MqlRates current[];ArraySetAsSeries(current,false);ResetLastError();
 int n=CopyRates(InpSymbol,PERIOD_M1,pe_cursor,pe_end-1,current);int error=GetLastError();
 bool valid=n>=0&&error==0;
 for(int j=0;valid&&j<n;j++)if(!PEValid(current[j])||current[j].time<pe_cursor||current[j].time>=pe_end||(long)current[j].time%60!=0||
   (j>0&&current[j].time<=current[j-1].time))valid=false;
 bool stable=valid&&pe_have&&PESame(current,pe_previous);
 if(stable)
 {
  string body="time;open;high;low;close;tick_volume;real_volume;spread\r\n";
  for(int j=0;j<n;j++)body+=TimeToString(current[j].time,TIME_DATE|TIME_MINUTES)+";"+PEN(current[j].open)+";"+PEN(current[j].high)+";"+PEN(current[j].low)+";"+PEN(current[j].close)+";"+
   IntegerToString(current[j].tick_volume)+";"+IntegerToString(current[j].real_volume)+";"+IntegerToString(current[j].spread)+"\r\n";
  string file="M1_"+PEMonth(pe_cursor)+".csv";
  if(!PEWrite(file,body)){PEStatus("ESCRITA_FALHOU",n,error,file);PEComplete();return;}
  PEStatus(n==0?"VAZIO_ESTAVEL_NAO_CERTIFICA_AUSENCIA_GLOBAL":"EXPORTADO_ESTAVEL",n,error,file);pe_total_rows+=n;pe_months++;
 }
 else if(pe_attempt>=InpMaxTentativasPorMes){PEStatus("PENDENTE_SEM_DUAS_LEITURAS_VALIDAS_IGUAIS",n,error,"");pe_pending++;pe_months++;}
 else
 {
  pe_have=valid;if(valid){if(ArrayResize(pe_previous,n)!=n||ArrayCopy(pe_previous,current)!=n){pe_io_failed=true;PEStatus("COPIA_INTERNA_FALHOU",n,error,"");PEComplete();return;}}
  else ArrayResize(pe_previous,0);
  Print("M1EXP110;WAIT;month=",PEMonth(pe_cursor),";attempt=",pe_attempt,";n=",n,";error=",error,";valid=",valid);
  return;
 }
 pe_cursor=pe_end;pe_end=PENextMonth(pe_cursor);if(pe_end>InpFim)pe_end=InpFim;
 pe_attempt=0;pe_have=false;ArrayResize(pe_previous,0);
}
int OnInit()
{
 if(MQLInfoInteger(MQL_TESTER)||InpSymbol==""||InpInicio>=InpFim||InpFim>TimeCurrent()||!PEMidnight(InpInicio)||!PEMidnight(InpFim)||InpMaxTentativasPorMes<2||InpMaxTentativasPorMes>100)
 {Print("M1EXP110;RECUSADO;USAR_GRAFICO_TERMINAL_E_INTERVALO_PASSADO_EXCLUSIVO_MEIA_NOITE");return INIT_PARAMETERS_INCORRECT;}
 if(!SymbolSelect(InpSymbol,true)){Print("M1EXP110;SYMBOL_SELECT_FAILED;error=",GetLastError());return INIT_FAILED;}
 pe_cursor=InpInicio;pe_end=PENextMonth(pe_cursor);if(pe_end>InpFim)pe_end=InpFim;
 if(pe_end<=pe_cursor)return INIT_PARAMETERS_INCORRECT;
 FolderCreate("ModeloD_Cobertura_WINN",FILE_COMMON);
 pe_folder="ModeloD_Cobertura_WINN\\EXPORT110_"+IntegerToString((long)TimeLocal())+"_"+IntegerToString((long)GetMicrosecondCount());
 if(!FolderCreate(pe_folder,FILE_COMMON))return INIT_FAILED;
 if(!PEWrite("ESPECIFICACAO.txt",PWSpecification(InpSymbol)))return INIT_FAILED;
 pe_status=FileOpen(pe_folder+"\\STATUS.csv",FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_COMMON,0,CP_UTF8);if(pe_status==INVALID_HANDLE)return INIT_FAILED;
 ResetLastError();uint header_written=FileWriteString(pe_status,"from_inclusive;to_exclusive;state;attempts;rows;error;file\r\n");FileFlush(pe_status);
 if(header_written==0||GetLastError()!=0)return INIT_FAILED;
 Print("M1EXP110;START;symbol=",InpSymbol,";from=",TimeToString(InpInicio,TIME_DATE),";end_exclusive=",TimeToString(InpFim,TIME_DATE),
  ";Common\\Files\\",pe_folder,";SEM_ORDENS;SEM_ALTERAR_HISTORICO;PAGINACAO_MENSAL");
 if(!EventSetTimer(2))return INIT_FAILED;
 return INIT_SUCCEEDED;
}
void OnDeinit(const int reason)
{
 EventKillTimer();if(!pe_done&&pe_status!=INVALID_HANDLE)Print("M1EXP110;INTERROMPIDO;cursor=",TimeToString(pe_cursor,TIME_DATE),";COBERTURA_PENDENTE");
 if(pe_status!=INVALID_HANDLE){FileClose(pe_status);pe_status=INVALID_HANDLE;}
}
