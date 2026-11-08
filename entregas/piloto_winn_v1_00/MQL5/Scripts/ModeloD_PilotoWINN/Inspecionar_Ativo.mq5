#property strict
#property version "1.00"
#property script_show_inputs
#property description "Somente leitura: registra as propriedades do ativo escolhido. Nao envia ordens."
#include <ModeloD_PilotoWINN/Piloto_Especificacao.mqh>
input string InpSymbol=""; // vazio = ativo do grafico
void OnStart()
{
 string symbol=(InpSymbol==""?_Symbol:InpSymbol);
 if(!SymbolSelect(symbol,true)){Print("PWIN100_SPEC;SYMBOL_SELECT_FAILED;",symbol,";error=",GetLastError());return;}
 string body=PWSpecification(symbol);
 FolderCreate("ModeloD_Piloto_WINN",FILE_COMMON);
 string path="ModeloD_Piloto_WINN\\ESPEC_"+IntegerToString((long)TimeLocal())+"_"+IntegerToString((long)GetMicrosecondCount())+".txt";
 int h=FileOpen(path,FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_COMMON,0,CP_UTF8);
 if(h==INVALID_HANDLE){Print("PWIN100_SPEC;FILE_FAILED;error=",GetLastError());return;}
 ResetLastError();uint n=FileWriteString(h,body);FileFlush(h);int error=GetLastError();FileClose(h);
 Print(body);Print("PWIN100_SPEC;END;write_ok=",n>0&&error==0,";Common\\Files\\",path);
}
