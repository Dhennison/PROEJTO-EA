#ifndef FOCAL_CORE_MQH
#define FOCAL_CORE_MQH
#include "HC_Core.mqh"
struct FMinute
{
   int total,business;
   long first,last;
   double o,h,l,c;
};
void FMinuteStats(const MqlTick &ticks[],const long lo,const long hi,FMinute &r)
{
   r.total=0;r.business=0;r.first=0;r.last=0;r.o=0;r.h=0;r.l=0;r.c=0;
   for(int i=0;i<ArraySize(ticks);i++)
   {
      if(ticks[i].time_msc<lo || ticks[i].time_msc>=hi)continue;
      r.total++;
      if((ticks[i].flags & 120)==0)continue;
      if(r.business==0){r.first=ticks[i].time_msc;r.o=ticks[i].last;r.h=ticks[i].last;r.l=ticks[i].last;}
      if(ticks[i].last>r.h)r.h=ticks[i].last;
      if(ticks[i].last<r.l)r.l=ticks[i].last;
      r.last=ticks[i].time_msc;r.c=ticks[i].last;r.business++;
   }
}
bool FValidRates(const MqlRates &rates[],const int n,const int error,const long lo,const long hi,string &reason)
{
   reason="";
   if(n<0 || n!=ArraySize(rates) || error!=0){reason="API_M1_OU_TAMANHO";return false;}
   long previous=lo-1;
   for(int i=0;i<n;i++)
   {
      long ms=(long)rates[i].time*1000;
      if(ms<lo || ms>=hi || ms<=previous || (ms-lo)%60000!=0){reason="M1_ORDEM_JANELA_ALINHAMENTO";return false;}
      if(!MathIsValidNumber(rates[i].open) || !MathIsValidNumber(rates[i].high) || !MathIsValidNumber(rates[i].low) || !MathIsValidNumber(rates[i].close) ||
         rates[i].low<=0 || rates[i].high<rates[i].low || rates[i].open<rates[i].low || rates[i].open>rates[i].high || rates[i].close<rates[i].low || rates[i].close>rates[i].high)
         {reason="M1_OHLC_INVALIDO";return false;}
      previous=ms;
   }
   return true;
}
bool FSameRates(const MqlRates &a[],const MqlRates &b[])
{
   if(ArraySize(a)!=ArraySize(b))return false;
   for(int i=0;i<ArraySize(a);i++)
      if(a[i].time!=b[i].time || a[i].open!=b[i].open || a[i].high!=b[i].high || a[i].low!=b[i].low || a[i].close!=b[i].close ||
         a[i].tick_volume!=b[i].tick_volume || a[i].real_volume!=b[i].real_volume || a[i].spread!=b[i].spread)return false;
   return true;
}
int FDiff(const FMinute &r,const MqlRates &rate)
{
   int mask=0;if(r.o!=rate.open)mask|=1;if(r.h!=rate.high)mask|=2;if(r.l!=rate.low)mask|=4;if(r.c!=rate.close)mask|=8;return mask;
}
string FFields(const int mask)
{
   string out="";
   if((mask & 1)!=0)out+="O|";
   if((mask & 2)!=0)out+="H|";
   if((mask & 4)!=0)out+="L|";
   if((mask & 8)!=0)out+="C|";
   if(out=="")return "IGUAL";
   return StringSubstr(out,0,StringLen(out)-1);
}
#endif
