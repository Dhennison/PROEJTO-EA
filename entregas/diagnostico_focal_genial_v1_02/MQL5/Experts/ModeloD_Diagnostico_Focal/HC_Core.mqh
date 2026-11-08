#ifndef HC_CORE_MQH
#define HC_CORE_MQH
// Apenas validacao de dados. Sem bibliotecas ou transporte do EA.
bool HCSame(const MqlTick &a[],const MqlTick &b[])
{
   if(ArraySize(a)!=ArraySize(b))return false;
   for(int i=0;i<ArraySize(a);i++)
      if(a[i].time!=b[i].time || a[i].time_msc!=b[i].time_msc ||
         a[i].bid!=b[i].bid || a[i].ask!=b[i].ask || a[i].last!=b[i].last ||
         a[i].volume!=b[i].volume || a[i].volume_real!=b[i].volume_real || a[i].flags!=b[i].flags)return false;
   return true;
}
bool HCValidate(const MqlTick &ticks[],const int n,const int err,const long lo,const long hi,int &trades,string &why)
{
   trades=0;why="";
   if(n<0 || err!=0 || n!=ArraySize(ticks)){why="API_OU_TAMANHO";return false;}
   long previous=lo;
   for(int i=0;i<n;i++)
   {
      if(!MathIsValidNumber(ticks[i].bid) || !MathIsValidNumber(ticks[i].ask) ||
         !MathIsValidNumber(ticks[i].last) || !MathIsValidNumber(ticks[i].volume_real))
         {why="CAMPO_NAO_FINITO";return false;}
      if(ticks[i].time_msc<lo || ticks[i].time_msc>=hi || ticks[i].time_msc<previous)
         {why="JANELA_OU_ORDEM";return false;}
      previous=ticks[i].time_msc;
      if((ticks[i].flags & 120)!=0)
      {
         if(ticks[i].last<=0){why="NEGOCIO_LAST_INVALIDO";return false;}
         trades++;
      }
   }
   return true;
}
bool HCM1(const MqlTick &ticks[],const MqlRates &rates[],const long lo,const long hi,
          int &missing_ticks,int &missing_bars,int &different,string &why)
{
   missing_ticks=0;missing_bars=0;different=0;why="";
   int minutes=(int)((hi-lo)/60000);
   if(minutes<1 || minutes>15 || (hi-lo)%60000!=0){why="JANELA_M1_INVALIDA";return false;}
   double oo[15],hh[15],ll[15],cc[15];int counts[15],bars[15];
   for(int m=0;m<15;m++){oo[m]=0;hh[m]=0;ll[m]=0;cc[m]=0;counts[m]=0;bars[m]=0;}
   for(int i=0;i<ArraySize(ticks);i++)
   {
      if((ticks[i].flags & 120)==0)continue;
      int m=(int)((ticks[i].time_msc-lo)/60000);
      if(m<0 || m>=minutes){why="TICK_FORA_M1";return false;}
      double last=ticks[i].last;
      if(counts[m]==0){oo[m]=last;hh[m]=last;ll[m]=last;}
      if(last>hh[m])hh[m]=last;
      if(last<ll[m])ll[m]=last;
      cc[m]=last;counts[m]++;
   }
   for(int i=0;i<ArraySize(rates);i++)
   {
      long ms=(long)rates[i].time*1000;
      if(ms<lo || ms>=hi || (ms-lo)%60000!=0){why="BARRA_FORA_JANELA";return false;}
      int m=(int)((ms-lo)/60000);
      if(bars[m]!=0){why="BARRA_DUPLICADA";return false;}
      bars[m]=1;
      if(!MathIsValidNumber(rates[i].open) || !MathIsValidNumber(rates[i].high) ||
         !MathIsValidNumber(rates[i].low) || !MathIsValidNumber(rates[i].close) ||
         rates[i].low>rates[i].high || rates[i].open<rates[i].low || rates[i].open>rates[i].high ||
         rates[i].close<rates[i].low || rates[i].close>rates[i].high)
         {why="OHLC_INVALIDO";return false;}
      if(counts[m]==0){if(rates[i].tick_volume>0)missing_ticks++;continue;}
      if(oo[m]!=rates[i].open || hh[m]!=rates[i].high || ll[m]!=rates[i].low || cc[m]!=rates[i].close)different++;
   }
   for(int m=0;m<minutes;m++)if(counts[m]>0 && bars[m]==0)missing_bars++;
   if(missing_ticks>0 || missing_bars>0 || different>0){why="TICKS_M1_DIVERGENTES_OU_AUSENTES";return false;}
   return true;
}
#endif
