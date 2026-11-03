#property strict
#property script_show_inputs
#include "ModeloD_PreviewIntegradoCases.mqh"
#include "ModeloD_TestRun.mqh"
#include "ModeloD_OperationalCases.mqh"
void OnStart() {
 string run_suffix,run_reason;int claim;
 if(!MDRegressionRunSuffix(run_suffix,claim,run_reason)){Print("TESTE_NAO_EXECUTADO;",run_reason);return;}
 Print("TEST_RUN;",run_suffix);
 RunPreviewIntegrado(run_suffix);RunOperationalCases();
 string path="ModeloD_Validacao_Integrada_"+run_suffix+".txt";
 int h=FileOpen(path,FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_COMMON,0,CP_UTF8);
 string summary="RESULTADO_INTEGRADO;RegressaoChecks="+IntegerToString(checksPreview)+";RegressaoFailures="+IntegerToString(failuresPreview)+
 ";OperationalChecks="+IntegerToString(op_checks)+";OperationalFailures="+IntegerToString(op_failures)+";SEM_TRANSPORTE;EVENTOS_SINTETICOS";
 if(h!=INVALID_HANDLE){FileWriteString(h,summary+"\r\n"+logPreview+op_log);FileFlush(h);FileClose(h);}
 FileClose(claim);
 Print(summary);Print("RELATORIO;",TerminalInfoString(TERMINAL_COMMONDATA_PATH),"\\Files\\",path);
}
