#property strict
#property version "1.00"
#property description "Cria simbolo de pesquisa isolado. Sem negociacao e sem modificar WINZ26."
#property script_show_inputs

// Nome fixo e exclusivo. Recusa qualquer simbolo preexistente com esse nome.
const string MD_RESEARCH_SYMBOL="MD_PESQ_WINZ26_DIA1030";
int md_research_file=INVALID_HANDLE;
void MDResearchLog(string message)
{
   Print("MD_PESQ_DIA;",message);
   if(md_research_file!=INVALID_HANDLE)
   {FileWriteString(md_research_file,"MD_PESQ_DIA;"+message+"\r\n");FileFlush(md_research_file);}
}
void MDResearchClose()
{
   if(md_research_file!=INVALID_HANDLE)
   {FileClose(md_research_file);md_research_file=INVALID_HANDLE;}
}
void OnStart()
{
   if(MQLInfoInteger(MQL_TESTER))
   {Print("MD_PESQ_DIA;RECUSADO;EXECUTAR_COMO_SCRIPT_NO_TERMINAL_ISOLADO");return;}
   bool custom=false;
   if(SymbolExist(MD_RESEARCH_SYMBOL,custom))
   {Print("MD_PESQ_DIA;RECUSADO;SIMBOLO_JA_EXISTE;NAO_SOBRESCREVER;",MD_RESEARCH_SYMBOL);return;}
   bool source_custom=false;
   if(!SymbolExist("WINZ26",source_custom)||source_custom)
   {Print("MD_PESQ_DIA;RECUSADO;ORIGEM_WINZ26_REAL_INDISPONIVEL");return;}
   ResetLastError();
   if(!SymbolSelect("WINZ26",true))
   {Print("MD_PESQ_DIA;WINZ26_INDISPONIVEL;error=",GetLastError());return;}
   // Somente barras reais do DIA ANTERIOR para aquecimento. Nao cria barras
   // artificiais nem copia M1 do primeiro minuto que sera importado depois.
   MqlRates prior[];ResetLastError();
   int count=CopyRates("WINZ26",PERIOD_M1,D'2026.10.29 00:00:00',D'2026.10.29 23:59:59',prior);
   int error=GetLastError();
   if(count<500||count!=ArraySize(prior)||error!=0)
   {Print("MD_PESQ_DIA;HISTORICO_29_INSUFICIENTE;returned=",count,";error=",error,";NENHUM_SIMBOLO_CRIADO");return;}
   for(int i=0;i<count;i++)
   {
      MqlRates bar=prior[i];
      if(bar.time<D'2026.10.29 00:00:00'||bar.time>=D'2026.10.30 00:00:00'||
         (i>0&&bar.time<=prior[i-1].time)||
         !MathIsValidNumber(bar.open)||!MathIsValidNumber(bar.high)||
         !MathIsValidNumber(bar.low)||!MathIsValidNumber(bar.close)||bar.low<=0||
         bar.high<bar.low||bar.open<bar.low||bar.open>bar.high||bar.close<bar.low||bar.close>bar.high||
         bar.tick_volume<0||bar.real_volume<0)
      {Print("MD_PESQ_DIA;BARRA_29_INVALIDA;index=",i,";NENHUM_SIMBOLO_CRIADO");return;}
   }
   string file="MD_PESQ_DIA_PREPARACAO_"+IntegerToString((long)GetMicrosecondCount())+
               "_"+IntegerToString((long)GetTickCount64())+".txt";
   if(FileIsExist(file,FILE_COMMON))
   {Print("MD_PESQ_DIA;COLISAO_RELATORIO;",file);return;}
   md_research_file=FileOpen(file,FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_COMMON|FILE_SHARE_READ,0,CP_UTF8);
   if(md_research_file==INVALID_HANDLE)
   {Print("MD_PESQ_DIA;RELATORIO_FALHOU;error=",GetLastError());return;}
   MDResearchLog("START;PESQUISA_SEM_ORDENS;build="+IntegerToString(TerminalInfoInteger(TERMINAL_BUILD)));
   MDResearchLog("REPORT;Common\\Files\\"+file);
   ResetLastError();
   if(!CustomSymbolCreate(MD_RESEARCH_SYMBOL,"ModeloD_Pesquisa_Dia","WINZ26"))
   {MDResearchLog("CREATE_FAILED;error="+IntegerToString(GetLastError()));MDResearchClose();return;}
   MDResearchLog("CREATED;symbol="+MD_RESEARCH_SYMBOL+";origin=WINZ26;ONLY_NEW_SYMBOL");
   MDResearchLog("DESCRIPTION_INHERITED;NO_DESCRIPTION_WRITE");
   ResetLastError();
   int written=CustomRatesReplace(MD_RESEARCH_SYMBOL,D'2026.10.29 00:00:00',D'2026.10.29 23:59:59',prior);
   error=GetLastError();
   MDResearchLog("PRIOR_M1_COPY;source_rows="+IntegerToString(count)+
                 ";written="+IntegerToString(written)+";error="+IntegerToString(error));
   if(written!=count||error!=0)
   {MDResearchLog("STOP;COPY_INCOMPLETE;PRESERVAR_SIMBOLO_NOVO_PARA_DIAGNOSTICO");MDResearchClose();return;}
   ResetLastError();
   if(!SymbolSelect(MD_RESEARCH_SYMBOL,true))
   {MDResearchLog("SELECT_FAILED;error="+IntegerToString(GetLastError()));MDResearchClose();return;}
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
                 ";CSV_ORIGINAL_30OUT_DIA_INTEIRO;NO_CURRENT_DAY_TICKS_IMPORTED_YET;NO_ORDERS");
   MDResearchClose();
}
