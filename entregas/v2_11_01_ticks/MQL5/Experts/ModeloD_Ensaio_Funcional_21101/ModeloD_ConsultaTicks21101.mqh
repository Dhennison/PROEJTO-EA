#ifndef MD_CONSULTA_TICKS21101
#define MD_CONSULTA_TICKS21101
// Experimental native Tester adapter. No live or imported path is changed.
input bool UsarConsultaAllFiltradaNoTester=true;
int md_comparacoes21101=0;
void Report615(string text);
string MDAmostra21101(MqlTick &ticks[],int n)
{
 if(n<=0||ArraySize(ticks)==0)return "SEM_REGISTRO";
 return "msc="+IntegerToString(ticks[0].time_msc)+";last="+DoubleToString(ticks[0].last,6)+
  ";bid="+DoubleToString(ticks[0].bid,6)+";ask="+DoubleToString(ticks[0].ask,6)+
  ";flags="+IntegerToString((long)ticks[0].flags);
}
int MDConsultaNativa21101(string symbol,MqlTick &out[],uint flags,ulong start,ulong end)
{
 if(!MDIsTester210()||!ExecutarNoTester||UsarFonteImportadaNoTester||flags!=COPY_TICKS_TRADE)
  return CopyTicksRange(symbol,out,flags,start,end);
 // Pair only the first 32 requests; diagnostics must not flood the journal.
 bool compare=md_comparacoes21101<32;
 if(!compare&&!UsarConsultaAllFiltradaNoTester)return CopyTicksRange(symbol,out,flags,start,end);
 int trade_n=0,trade_error=0;
 MqlTick trades[];
 if(compare||!UsarConsultaAllFiltradaNoTester){
  ResetLastError();trade_n=CopyTicksRange(symbol,trades,COPY_TICKS_TRADE,start,end);
  trade_error=GetLastError();
 }
 MqlTick all[];
 ResetLastError();int all_n=CopyTicksRange(symbol,all,COPY_TICKS_ALL,start,end);
 int all_error=GetLastError();int used=0;bool valid=all_n>=0&&all_error==0&&all_n==ArraySize(all)&&all_n<=500000;
 if(valid){
  long previous=-1;
  for(int i=0;i<all_n;i++){
   // Never sort, fill prices, drop duplicates or accept out-of-window records.
   if(all[i].time_msc<0||(ulong)all[i].time_msc<start||(ulong)all[i].time_msc>end||
      all[i].time_msc<previous){valid=false;break;}
   previous=all[i].time_msc;
  }
 }
 string first_all=MDAmostra21101(all,all_n);
 if(valid){
  for(int i=0;i<all_n;i++){
   if((all[i].flags&(TICK_FLAG_LAST|TICK_FLAG_VOLUME|TICK_FLAG_BUY|TICK_FLAG_SELL))==0)continue;
   // A quote carrying a Last but no trade-related flag is not trade evidence.
   if(!MathIsValidNumber(all[i].last)||all[i].last<=0){valid=false;break;}
   if(used!=i)all[used]=all[i];
   used++;
  }
 }
 if(compare){
  md_comparacoes21101++;
  Report615("TICKS21101_COMPARE;symbol="+symbol+";de_msc="+IntegerToString((long)start)+
   ";ate_msc="+IntegerToString((long)end)+";TRADE_n="+IntegerToString(trade_n)+
   ";TRADE_erro="+IntegerToString(trade_error)+";ALL_n="+IntegerToString(all_n)+
   ";ALL_erro="+IntegerToString(all_error)+";ALL_negocios="+IntegerToString(valid?used:-1)+
   ";ALL_valido="+IntegerToString(valid?1:0)+";selecionada="+(UsarConsultaAllFiltradaNoTester?"ALL_FILTRADO":"TRADE"));
  Report615("TICKS21101_TRADE_PRIMEIRO;"+MDAmostra21101(trades,trade_n));
  Report615("TICKS21101_ALL_PRIMEIRO;"+first_all);
  Report615("TICKS21101_ALL_NEGOCIO_PRIMEIRO;"+(valid?MDAmostra21101(all,used):"RETORNO_REJEITADO"));
 }
 if(!UsarConsultaAllFiltradaNoTester){
  if(trade_n<0||trade_error!=0||trade_n!=ArraySize(trades))return -1;
  if(ArrayResize(out,trade_n)!=trade_n)return -1;
  for(int i=0;i<trade_n;i++)out[i]=trades[i];
  ResetLastError();return trade_n;
 }
 if(!valid)return -1; // Partial data with timeout/error are never certified.
 if(ArrayResize(out,used)!=used)return -1;
 for(int i=0;i<used;i++)out[i]=all[i];
 ResetLastError();return used;
}
#endif
