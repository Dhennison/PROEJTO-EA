#property strict
#property version "1.01"
#property description "Retoma somente o simbolo local de pesquisa ja criado. Sem ordens."
#property script_show_inputs

// Recuperacao da preparacao que parou em DESCRIPTION_FAILED;error=5309.
// Nao cria/apaga simbolos e nao altera a descricao herdada de WINZ26.
// Unica escrita de historico: M1 de 29/10 no simbolo custom de pesquisa.
const string MD_RESEARCH_SYMBOL="MD_PESQ_WINZ26_1030";
int md_research_file=INVALID_HANDLE;
void MDResearchLog(string message)
{
   Print("MD_PESQ;",message);
   if(md_research_file!=INVALID_HANDLE)
   {FileWriteString(md_research_file,"MD_PESQ;"+message+"\r\n");FileFlush(md_research_file);}
}
void MDResearchClose()
{
   if(md_research_file!=INVALID_HANDLE)
   {FileClose(md_research_file);md_research_file=INVALID_HANDLE;}
}
bool MDMatchingInteger(ENUM_SYMBOL_INFO_INTEGER property)
{
   long source=0,target=0;
   return SymbolInfoInteger("WINZ26",property,source)&&
          SymbolInfoInteger(MD_RESEARCH_SYMBOL,property,target)&&source==target;
}
bool MDMatchingDouble(ENUM_SYMBOL_INFO_DOUBLE property)
{
   double source=0,target=0;
   return SymbolInfoDouble("WINZ26",property,source)&&
          SymbolInfoDouble(MD_RESEARCH_SYMBOL,property,target)&&
          MathIsValidNumber(source)&&MathIsValidNumber(target)&&source>0&&source==target;
}
bool MDMatchingString(ENUM_SYMBOL_INFO_STRING property)
{
   string source="",target="";
   return SymbolInfoString("WINZ26",property,source)&&
          SymbolInfoString(MD_RESEARCH_SYMBOL,property,target)&&source!=""&&source==target;
}
void OnStart()
{
   if(MQLInfoInteger(MQL_TESTER))
   {Print("MD_PESQ;RECUSADO;EXECUTAR_COMO_SCRIPT_NO_TERMINAL_ISOLADO");return;}
   bool custom=false;
   if(!SymbolExist(MD_RESEARCH_SYMBOL,custom)||!custom)
   {Print("MD_PESQ;RECUSADO;EXIGE_SIMBOLO_CUSTOM_JA_CRIADO;",MD_RESEARCH_SYMBOL);return;}
   ResetLastError();
   if(!SymbolSelect(MD_RESEARCH_SYMBOL,true))
   {Print("MD_PESQ;CUSTOM_SELECT_FAILED;error=",GetLastError());return;}
   bool source_custom=false;
   if(!SymbolExist("WINZ26",source_custom)||source_custom||!SymbolSelect("WINZ26",true))
   {Print("MD_PESQ;RECUSADO;ORIGEM_WINZ26_REAL_INDISPONIVEL");return;}
   if(!MDMatchingInteger(SYMBOL_CHART_MODE)||!MDMatchingInteger(SYMBOL_DIGITS)||
      !MDMatchingInteger(SYMBOL_TRADE_CALC_MODE)||!MDMatchingDouble(SYMBOL_TRADE_TICK_SIZE)||
      !MDMatchingDouble(SYMBOL_POINT)||!MDMatchingDouble(SYMBOL_TRADE_CONTRACT_SIZE)||
      !MDMatchingString(SYMBOL_CURRENCY_PROFIT)||!MDMatchingString(SYMBOL_CURRENCY_MARGIN))
   {Print("MD_PESQ;RECUSADO;PROPRIEDADES_DIFEREM_DA_ORIGEM_OU_LEITURA_FALHOU");return;}
   MqlRates prior[];ResetLastError();
   int count=CopyRates("WINZ26",PERIOD_M1,D'2026.10.29 00:00:00',D'2026.10.29 23:59:59',prior);
   int error=GetLastError();
   if(count<500||count!=ArraySize(prior)||error!=0)
   {Print("MD_PESQ;HISTORICO_29_INSUFICIENTE;returned=",count,";error=",error,";HISTORICO_CUSTOM_NAO_ALTERADO");return;}
   for(int i=0;i<count;i++)
   {
      MqlRates bar=prior[i];
      if(bar.time<D'2026.10.29 00:00:00'||bar.time>=D'2026.10.30 00:00:00'||
         (i>0&&bar.time<=prior[i-1].time)||
         !MathIsValidNumber(bar.open)||!MathIsValidNumber(bar.high)||
         !MathIsValidNumber(bar.low)||!MathIsValidNumber(bar.close)||bar.low<=0||
         bar.high<bar.low||bar.open<bar.low||bar.open>bar.high||bar.close<bar.low||bar.close>bar.high||
         bar.tick_volume<0||bar.real_volume<0)
      {Print("MD_PESQ;BARRA_29_INVALIDA;index=",i,";HISTORICO_CUSTOM_NAO_ALTERADO");return;}
   }
   string file="MD_PESQ_CONTINUACAO_"+IntegerToString((long)GetMicrosecondCount())+
               "_"+IntegerToString((long)GetTickCount64())+".txt";
   if(FileIsExist(file,FILE_COMMON))
   {Print("MD_PESQ;COLISAO_RELATORIO;",file);return;}
   md_research_file=FileOpen(file,FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_COMMON|FILE_SHARE_READ,0,CP_UTF8);
   if(md_research_file==INVALID_HANDLE)
   {Print("MD_PESQ;RELATORIO_FALHOU;error=",GetLastError());return;}
   MDResearchLog("START;CONTINUACAO_SEM_ORDENS;build="+IntegerToString(TerminalInfoInteger(TERMINAL_BUILD)));
   MDResearchLog("REPORT;Common\\Files\\"+file);
   MDResearchLog("EXISTING_CUSTOM_CONFIRMED;symbol="+MD_RESEARCH_SYMBOL+";PROPERTIES_MATCH_WINZ26");
   MDResearchLog("DESCRIPTION_PRESERVED;NO_METADATA_WRITE;NO_SYMBOL_CREATED_OR_DELETED");
   ResetLastError();
   int written=CustomRatesReplace(MD_RESEARCH_SYMBOL,D'2026.10.29 00:00:00',D'2026.10.29 23:59:59',prior);
   error=GetLastError();
   MDResearchLog("PRIOR_M1_COPY;source_rows="+IntegerToString(count)+
                 ";written="+IntegerToString(written)+";error="+IntegerToString(error));
   if(written!=count||error!=0)
   {MDResearchLog("STOP;COPY_INCOMPLETE;PRESERVAR_SIMBOLO_PARA_DIAGNOSTICO");MDResearchClose();return;}
   MqlRates check[];ResetLastError();
   int read=CopyRates(MD_RESEARCH_SYMBOL,PERIOD_M1,D'2026.10.29 00:00:00',D'2026.10.29 23:59:59',check);
   error=GetLastError();bool same=read==count&&read==ArraySize(check)&&error==0;
   for(int i=0;same&&i<count;i++)
      same=prior[i].time==check[i].time&&prior[i].open==check[i].open&&
           prior[i].high==check[i].high&&prior[i].low==check[i].low&&prior[i].close==check[i].close&&
           prior[i].tick_volume==check[i].tick_volume&&prior[i].real_volume==check[i].real_volume&&
           prior[i].spread==check[i].spread;
   MDResearchLog("PRIOR_READBACK;rows="+IntegerToString(read)+";same="+IntegerToString((int)same)+
                 ";error="+IntegerToString(error));
   if(!same){MDResearchLog("STOP;READBACK_NOT_CONFIRMED");MDResearchClose();return;}
   MDResearchLog("READY_FOR_MANUAL_TICK_IMPORT;symbol="+MD_RESEARCH_SYMBOL+
                 ";CSV_30OUT_0900_0901;NO_TICKS_IMPORTED_BY_THIS_SCRIPT;NO_ORDERS");
   MDResearchClose();
}
