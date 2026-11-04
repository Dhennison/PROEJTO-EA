#ifndef MODELOD_CALENDAR_MQH
#define MODELOD_CALENDAR_MQH
// Snapshot B3 2026; fontes e limites em docs/VALIDACAO.txt.
// 1=pregao previsto, 0=fechado, -1=data invalida/ano nao cadastrado.
bool MDDate2026(const int date)
{
   int y=date/10000,m=(date/100)%100,d=date%100;
   if(y!=2026 || m<1 || m>12 || d<1)return false;
   int lengths[12]={31,28,31,30,31,30,31,31,30,31,30,31};
   return d<=lengths[m-1];
}
int MDOrdinal2026(const int date)
{
   if(!MDDate2026(date))return -1;
   int lengths[12]={31,28,31,30,31,30,31,31,30,31,30,31};
   int result=date%100;
   for(int m=1;m<(date/100)%100;m++)result+=lengths[m-1];
   return result;
}
int MDCalendar2026(const int date)
{
   int ordinal=MDOrdinal2026(date);if(ordinal<0)return -1;
   // 01/01/2026 quinta-feira; domingo=0.
   int weekday=(ordinal+3)%7;
   if(weekday==0 || weekday==6)return 0;
   int holidays[13]={20260101,20260216,20260217,20260403,20260421,
      20260501,20260604,20260907,20261012,20261102,20261120,20261224,20261225};
   for(int i=0;i<13;i++)if(date==holidays[i])return 0;
   if(date==20261231)return 0;
   return 1;
}
int MDPreviousSession2026(const int date)
{
   if(!MDDate2026(date))return 0;
   int m=(date/100)%100,d=date%100;
   int lengths[12]={31,28,31,30,31,30,31,31,30,31,30,31};
   while(true)
   {
      d--;if(d==0){m--;if(m==0)return 0;d=lengths[m-1];}
      int prior=20260000+m*100+d;
      if(MDCalendar2026(prior)==1)return prior;
   }
}
int MDWINLastTrading2026(const string symbol)
{
   if(symbol=="WING26")return 20260218;
   if(symbol=="WINJ26")return 20260415;
   if(symbol=="WINM26")return 20260617;
   if(symbol=="WINQ26")return 20260812;
   if(symbol=="WINV26")return 20261014;
   if(symbol=="WINZ26")return 20261216;
   return 0;
}
// Validade por vencimento somente: nao escolhe contrato e nao comprova listagem.
bool MDWINExpiryCheck2026(const string candidate,const int date,
                         const int broker_expiration_date,string &reason)
{
   reason="";
   if(MDCalendar2026(date)!=1){reason="DATA_SEM_PREGAO_OU_NAO_CADASTRADA";return false;}
   int expiry=MDWINLastTrading2026(candidate);
   if(expiry==0){reason="CONTRATO_NAO_CADASTRADO";return false;}
   if(date>expiry){reason="CONTRATO_VENCIDO";return false;}
   if(broker_expiration_date!=expiry){reason="VENCIMENTO_BROKER_DIVERGENTE";return false;}
   return true;
}
#endif
