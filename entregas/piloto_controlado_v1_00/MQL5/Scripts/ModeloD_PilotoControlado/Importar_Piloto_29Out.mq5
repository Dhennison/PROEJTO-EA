#property strict
#property version "1.00"
#property script_show_inputs
#property description "Piloto de dados: cria simbolo personalizado novo. Sem ordens."
#include <ModeloD_PilotoControlado/Piloto_Core.mqh>
input string InpArquivoFonte=PH_DEFAULT_SOURCE;
input string InpClonarSimbolo="WINZ26";
input int InpTamanhoLote=100000;
input bool InpConstruirM1=false;

void OnStart()
{
   if(MQLInfoInteger(MQL_TESTER))
   {Print("PILOTO100_IMPORT;RECUSADO;USAR_SCRIPT_NO_TERMINAL");return;}
   if(InpTamanhoLote<1000||InpTamanhoLote>1000000)
   {Print("PILOTO100_IMPORT;LOTE_INVALIDO;USAR_1000_A_1000000");return;}
   string folder=PHFolder("IMPORT");
   if(folder==""){Print("PILOTO100_IMPORT;PASTA_FALHOU;erro=",GetLastError());return;}
   string report="PILOTO100_IMPORT;v=1.00;SEM_ORDENS;NOVA_COPIA_CUSTOM\r\n";
   report+="source="+InpArquivoFonte+";clone="+InpClonarSimbolo+"\r\n";
   MqlTick source[];string why="";
   Print("PILOTO100_IMPORT;LENDO_FONTE;Common\\Files\\",InpArquivoFonte);
   if(!PHLoadPilot(InpArquivoFonte,source,why))
   {
      report+="SOURCE_FAILED;"+why+"\r\n";PHText(folder+"\\RESULTADO.txt",report);
      Print("PILOTO100_IMPORT;SOURCE_FAILED;",why,";pasta=",folder);return;
   }
   report+="SOURCE_OK;"+why+";"+PHStats(source)+";"+PHFlagHistogram(source)+"\r\n";
   long native_custom=0;
   if(!SymbolSelect(InpClonarSimbolo,true)||
      !SymbolInfoInteger(InpClonarSimbolo,SYMBOL_CUSTOM,native_custom)||native_custom!=0)
   {
      report+="CLONE_NATIVE_UNAVAILABLE\r\n";PHText(folder+"\\RESULTADO.txt",report);
      Print("PILOTO100_IMPORT;CLONE_NATIVE_UNAVAILABLE;pasta=",folder);return;
   }
   string symbol="MDDP29_"+IntegerToString((long)TimeLocal())+"_"+(string)GetTickCount();
   bool old_custom=false;
   if(StringLen(symbol)>31||SymbolExist(symbol,old_custom))
   {Print("PILOTO100_IMPORT;NOME_INDISPONIVEL;",symbol);return;}
   ResetLastError();bool created=CustomSymbolCreate(symbol,"ModeloD_Piloto",InpClonarSimbolo);
   int creation_error=GetLastError();
   report+="CUSTOM_CREATE;symbol="+symbol+";ok="+(string)(int)created+";error="+(string)creation_error+"\r\n";
   if(!created)
   {PHText(folder+"\\RESULTADO.txt",report);Print("PILOTO100_IMPORT;CREATE_FAILED;pasta=",folder);return;}
   // Guard every mutation: only the newly created symbol, never a native symbol.
   bool is_custom=false;
   bool guarded=SymbolExist(symbol,is_custom)&&is_custom&&StringFind(symbol,"MDDP29_")==0;
   if(!guarded)
   {report+="CUSTOM_GUARD_FAILED\r\n";PHText(folder+"\\RESULTADO.txt",report);return;}
   ResetLastError();bool mode=CustomSymbolSetInteger(symbol,SYMBOL_CHART_MODE,SYMBOL_CHART_MODE_LAST);
   int mode_error=GetLastError();
   report+="CHART_MODE_LAST;ok="+(string)(int)mode+";error="+(string)mode_error+"\r\n";
   if(!mode||!SymbolSelect(symbol,true))
   {report+="CUSTOM_SETUP_FAILED\r\n";PHText(folder+"\\RESULTADO.txt",report);Print("PILOTO100_IMPORT;SETUP_FAILED;pasta=",folder);return;}
   Print("PILOTO100_IMPORT;IMPORTANDO;symbol=",symbol,";n=",ArraySize(source));
   int written=0,write_error=0,start=0,batches=0;bool batch_ok=true;
   while(start<ArraySize(source)&&!IsStopped())
   {
      int end=PHBatchEnd(source,start,InpTamanhoLote),count=end-start;
      MqlTick batch[];
      if(count<=0||ArrayResize(batch,count)!=count||ArrayCopy(batch,source,0,start,count)!=count)
      {batch_ok=false;report+="BATCH_COPY_FAILED\r\n";break;}
      ResetLastError();
      int added=CustomTicksReplace(symbol,source[start].time_msc,source[end-1].time_msc,batch);
      write_error=GetLastError();batches++;
      report+="CUSTOM_TICKS_REPLACE;batch="+(string)batches+";from="+(string)source[start].time_msc+
         ";to_inclusive="+(string)source[end-1].time_msc+";expected="+(string)count+
         ";returned="+(string)added+";error="+(string)write_error+"\r\n";
      Print("PILOTO100_IMPORT;BATCH;",batches,";expected=",count,";returned=",added,";error=",write_error);
      if(added!=count||write_error!=0){batch_ok=false;break;}
      written+=added;start=end;
   }
   batch_ok=batch_ok&&start==ArraySize(source);
   report+="BATCHES_DONE;ok="+(string)(int)batch_ok+";written="+(string)written+"\r\n";
   MqlTick previous[],readback[];bool stable=false,previous_valid=false;int got=-1,read_error=0;
   if(batch_ok&&written==ArraySize(source)&&write_error==0)
   {
      for(int attempt=1;attempt<=8&&!IsStopped();attempt++)
      {
         ResetLastError();got=CopyTicksRange(symbol,readback,COPY_TICKS_ALL,(ulong)PH_FROM*1000,(ulong)PH_TO*1000-1);
         read_error=GetLastError();
         bool valid=(got>=0&&read_error==0&&got==ArraySize(readback));
         report+="READBACK;attempt="+(string)attempt+";n="+(string)got+";error="+(string)read_error+"\r\n";
         if(valid&&previous_valid&&PHSame(previous,readback)){stable=true;break;}
         if(valid)
         {
            if(ArrayResize(previous,got)!=got)break;
            if(got>0&&ArrayCopy(previous,readback)!=got)break;
         }
         else ArrayResize(previous,0);
         previous_valid=valid;
         Sleep(250);
      }
   }
   bool exported=false;
   if(got>=0&&read_error==0)exported=PHExport(folder+"\\IMPORT_READBACK.csv",readback);
   bool exact=stable&&batch_ok&&written==PH_ROWS&&write_error==0&&PHSame(source,readback);
   report+="READBACK_COMPARE;stable="+(string)(int)stable+";"+PHCompare(source,readback)+"\r\n";
   report+="READBACK_STATS;"+PHStats(readback)+";"+PHFlagHistogram(readback)+"\r\n";
   // First preserve automatic bars before the explicitly optional construction.
   report+="AUTO_"+PHCheckBars(symbol,source,folder+"\\IMPORT_M1_AUTO.csv")+"\r\n";
   report+="M1_CONSTRUCTION_REQUESTED="+(string)(int)InpConstruirM1+"\r\n";
   if(InpConstruirM1&&exact)
   {
      MqlRates derived[];int expected_bars=PHBars(source,derived);
      ResetLastError();int changed=CustomRatesUpdate(symbol,derived);int rates_error=GetLastError();
      report+="EXPLICIT_M1_CONSTRUCTION;expected="+(string)expected_bars+";returned="+(string)changed+
         ";error="+(string)rates_error+";OHLC_FROM_FLAGGED_LAST;tick_volume=SOURCE_TRADE_ROWS;real_volume=SUM_SOURCE_INTEGER_VOLUME\r\n";
      MqlTick post1[],post2[];
      ResetLastError();int p1=CopyTicksRange(symbol,post1,COPY_TICKS_ALL,(ulong)PH_FROM*1000,(ulong)PH_TO*1000-1);
      int pe1=GetLastError();
      ResetLastError();int p2=CopyTicksRange(symbol,post2,COPY_TICKS_ALL,(ulong)PH_FROM*1000,(ulong)PH_TO*1000-1);
      int pe2=GetLastError();
      bool post_valid=p1==PH_ROWS&&p2==PH_ROWS&&pe1==0&&pe2==0&&PHSame(post1,post2);
      exact=exact&&changed==expected_bars&&rates_error==0&&post_valid&&PHSame(source,post2);
      report+="AFTER_M1_TICKS;read1="+(string)p1+";error1="+(string)pe1+";read2="+(string)p2+
         ";error2="+(string)pe2+";"+PHCompare(source,post2)+"\r\n";
      if(p2>=0&&pe2==0)
         report+="AFTER_M1_EXPORT="+(string)(int)PHExport(folder+"\\IMPORT_READBACK_AFTER_M1.csv",post2)+"\r\n";
   }
   // Derived bars are from this source, never native M1 bars or the Work.
   string bars=PHCheckBars(symbol,source,folder+"\\IMPORT_M1.csv");
   report+=bars+"\r\n";
   report+="SOURCE_QUALITY_UNCHANGED;NO_FILTER;NO_SORT;NO_DEDUP;NO_NORMALIZATION\r\n";
   report+="IMPORT_EXACT="+(string)(int)exact+";export_ok="+(string)(int)exported+
      ";CUSTOM_SYMBOL="+symbol+";TESTER_DIARY_AND_ONTICK_STILL_PENDING\r\n";
   bool saved=PHText(folder+"\\RESULTADO.txt",report);
   Print("PILOTO100_IMPORT;END;symbol=",symbol,";import_exact=",exact,
         ";export_ok=",exported,";report_ok=",saved,";pasta=Common\\Files\\",folder);
   Print("PILOTO100_IMPORT;",bars,";SEM_ACEITE_AUTOMATICO;ENVIAR_RESULTADOS");
}
