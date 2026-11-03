#property strict
#property version "1.00"
#property description "Auditoria somente leitura no terminal, sem ordens. Configuration fixa."
#property script_show_inputs

const string MD_SYMBOL="MD_PESQ_WINZ26_DIA1030";
const datetime MD_BEGIN=D'2026.10.30 00:00:00';
const long MD_LAST_MSC=1793385084719;
const long MD_EXPECT_ALL=4319271,MD_EXPECT_TRADE=3190938;
const ulong MD_EXPECT_VOLUME=20884960;
// Fingerprint sobre SEIS INTEIROS por evento; nao e FNV de bytes nem SHA256.
const ulong MD_SEED=0xCBF29CE484222325;
const ulong MD_EXPECT_HASH_ALL=0xB565B48B9B550B5E;
const ulong MD_EXPECT_HASH_TRADE=0x49982C8C78AC71B8;
int md_file=INVALID_HANDLE;

struct MDDayStats
{
   long returned,valid_rows,trades,zero_flags,bad_fields,outside,regressions;
   ulong volume,hash_all,hash_trade;
};
struct MDDayMinute
{
   long trades;
   double open,high,low,close;
   ulong volume;
   bool bar_seen;
};
MDDayMinute md_minutes[1440];

void MDLog(string value)
{
   Print("MD_TERM;",value);
   if(md_file!=INVALID_HANDLE)
   {FileWriteString(md_file,"MD_TERM;"+value+"\r\n");FileFlush(md_file);}
}
void MDMix(ulong &hash,ulong value){hash^=value;hash*=1099511628211;}
void MDHash(ulong &hash,long msc,uint flags,ulong bid,ulong ask,ulong last,ulong volume)
{
   MDMix(hash,(ulong)msc);MDMix(hash,(ulong)flags);MDMix(hash,bid);
   MDMix(hash,ask);MDMix(hash,last);MDMix(hash,volume);
}
bool MDWhole(double value,ulong &result)
{
   if(!MathIsValidNumber(value)||value<0||value>9007199254740991.0)return false;
   result=(ulong)value;return (double)result==value;
}
long MD_MARKERS[14]={1793343574907,1793350845911,1793350847069,1793350847221,1793350849870,1793350852134,1793350852707,1793350853027,1793350877053,1793350877183,1793350878192,1793361522701,1793375647199,1793378319298};
bool MDMarker(long msc){for(int i=0;i<14;i++)if(msc==MD_MARKERS[i])return true;return false;}
bool MDQuery(string mode,uint selection,bool store_minutes,MDDayStats &stats)
{
   ZeroMemory(stats);stats.hash_all=MD_SEED;stats.hash_trade=MD_SEED;
   MqlTick ticks[];ResetLastError();
   int count=CopyTicksRange(MD_SYMBOL,ticks,selection,(ulong)MD_BEGIN*1000,(ulong)MD_LAST_MSC);
   int error=GetLastError();stats.returned=count;
   bool complete=count>=0&&count==ArraySize(ticks)&&error==0;
   MDLog("QUERY;mode="+mode+";returned="+IntegerToString(count)+
         ";array="+IntegerToString(ArraySize(ticks))+";error="+IntegerToString(error));
   int available=count>0?count:0;
   if(available>ArraySize(ticks))available=ArraySize(ticks);
   long previous=-1;
   for(int i=0;i<available;i++)
   {
      MqlTick tick=ticks[i];
      if(tick.time_msc<(long)MD_BEGIN*1000||tick.time_msc>MD_LAST_MSC)
      {stats.outside++;continue;}
      if(previous>=0&&tick.time_msc<previous)stats.regressions++;
      previous=tick.time_msc;
      if(MDMarker(tick.time_msc))MDLog("MARKER;mode="+mode+";index="+IntegerToString(i)+
         ";msc="+IntegerToString(tick.time_msc)+";flags="+IntegerToString((long)tick.flags)+
         ";bid="+DoubleToString(tick.bid,0)+";ask="+DoubleToString(tick.ask,0)+
         ";last="+DoubleToString(tick.last,0)+";volume="+IntegerToString((long)tick.volume)+
         ";volume_real="+DoubleToString(tick.volume_real,8));
      if(tick.flags==0){stats.zero_flags++;continue;}
      ulong b=0,a=0,l=0,v=0;
      bool valid=(!(tick.flags&TICK_FLAG_BID)||MDWhole(tick.bid,b))&&
                 (!(tick.flags&TICK_FLAG_ASK)||MDWhole(tick.ask,a))&&
                 (!(tick.flags&TICK_FLAG_LAST)||MDWhole(tick.last,l))&&
                 (!(tick.flags&TICK_FLAG_VOLUME)||MDWhole(tick.volume_real,v));
      if(!valid){stats.bad_fields++;continue;}
      stats.valid_rows++;MDHash(stats.hash_all,tick.time_msc,tick.flags,b,a,l,v);
      bool trade=(tick.flags&(TICK_FLAG_LAST|TICK_FLAG_VOLUME|TICK_FLAG_BUY|TICK_FLAG_SELL))!=0;
      if(!trade||!MathIsValidNumber(tick.last)||tick.last<=0)continue;
      ulong trade_last=0,trade_volume=0;
      if(!MDWhole(tick.last,trade_last)||!MDWhole(tick.volume_real,trade_volume)||
         tick.volume!=trade_volume)
      {stats.bad_fields++;continue;}
      stats.trades++;stats.volume+=trade_volume;
      MDHash(stats.hash_trade,tick.time_msc,tick.flags,b,a,l,v);
      if(store_minutes)
      {
         int minute=(int)((tick.time_msc-(long)MD_BEGIN*1000)/60000);
         if(md_minutes[minute].trades==0)
         {md_minutes[minute].open=tick.last;md_minutes[minute].high=tick.last;md_minutes[minute].low=tick.last;}
         md_minutes[minute].trades++;md_minutes[minute].volume+=trade_volume;
         md_minutes[minute].high=MathMax(md_minutes[minute].high,tick.last);
         md_minutes[minute].low=MathMin(md_minutes[minute].low,tick.last);
         md_minutes[minute].close=tick.last;
      }
   }
   bool good=complete&&stats.bad_fields==0&&stats.outside==0&&stats.regressions==0;
   MDLog("SUMMARY;mode="+mode+";api_complete="+IntegerToString((int)complete)+
         ";signaled="+IntegerToString(stats.valid_rows)+";trades="+IntegerToString(stats.trades)+
         ";volume="+IntegerToString((long)stats.volume)+";flags_zero="+IntegerToString(stats.zero_flags)+
         ";bad_fields="+IntegerToString(stats.bad_fields)+";outside="+IntegerToString(stats.outside)+
         ";regressions="+IntegerToString(stats.regressions)+
         ";hash_all_signed="+IntegerToString((long)stats.hash_all)+
         ";hash_trade_signed="+IntegerToString((long)stats.hash_trade));
   ArrayFree(ticks);return good;
}
bool MDBars()
{
   MqlRates bars[];ResetLastError();
   int count=CopyRates(MD_SYMBOL,PERIOD_M1,MD_BEGIN,(datetime)(MD_LAST_MSC/1000),bars);
   int error=GetLastError(),mismatches=0,missing=0;
   bool complete=count>=0&&count==ArraySize(bars)&&error==0;
   int available=count>0?count:0;
   if(available>ArraySize(bars))available=ArraySize(bars);
   for(int i=0;i<available;i++)
   {
      MqlRates bar=bars[i];
      if(bar.time<MD_BEGIN||bar.time>(datetime)(MD_LAST_MSC/1000)||((bar.time-MD_BEGIN)%60)!=0)
      {mismatches++;continue;}
      int minute=(int)((bar.time-MD_BEGIN)/60);
      bool same=!md_minutes[minute].bar_seen&&md_minutes[minute].trades>0&&
                bar.open==md_minutes[minute].open&&bar.high==md_minutes[minute].high&&
                bar.low==md_minutes[minute].low&&bar.close==md_minutes[minute].close&&
                bar.real_volume>=0&&(ulong)bar.real_volume==md_minutes[minute].volume;
      md_minutes[minute].bar_seen=true;
      if(!same)mismatches++;
      MDLog("M1;time="+TimeToString(bar.time,TIME_DATE|TIME_SECONDS)+
            ";open="+DoubleToString(bar.open,0)+";high="+DoubleToString(bar.high,0)+
            ";low="+DoubleToString(bar.low,0)+";close="+DoubleToString(bar.close,0)+
            ";tick_volume="+IntegerToString(bar.tick_volume)+";real_volume="+IntegerToString(bar.real_volume)+
            ";same_ohlc_volume_as_query="+IntegerToString((int)same));
   }
   for(int minute=0;minute<1440;minute++)
      if(md_minutes[minute].trades>0&&!md_minutes[minute].bar_seen)missing++;
   MDLog("M1_SUMMARY;rows="+IntegerToString(count)+";error="+IntegerToString(error)+
         ";api_complete="+IntegerToString((int)complete)+";mismatches="+IntegerToString(mismatches)+
         ";missing="+IntegerToString(missing)+";TICKVOL_NOT_ASSUMED_EQUAL_TO_TRADE_COUNT");
   return complete&&mismatches==0&&missing==0;
}

void OnStart()
{
   if(MQLInfoInteger(MQL_TESTER))
   {Print("MD_TERM;REFUSED;TERMINAL_ONLY");return;}
   long custom=0;
   if(!SymbolSelect(MD_SYMBOL,true)||!SymbolInfoInteger(MD_SYMBOL,SYMBOL_CUSTOM,custom)||custom!=1)
   {Print("MD_TERM;REFUSED;FIXED_CUSTOM_SYMBOL_REQUIRED");return;}
   string file="MD_AUDIT_TERMINAL_DIA_20261030_"+IntegerToString((long)GetMicrosecondCount())+
               "_"+IntegerToString((long)GetTickCount64())+".txt";
   if(FileIsExist(file,FILE_COMMON)){Print("MD_TERM;REPORT_COLLISION");return;}
   md_file=FileOpen(file,FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_COMMON|FILE_SHARE_READ,0,CP_UTF8);
   if(md_file==INVALID_HANDLE){Print("MD_TERM;REPORT_FAILED;error=",GetLastError());return;}
   MDLog("START;TERMINAL_ONLY;NO_ORDERS;symbol="+MD_SYMBOL+";build="+IntegerToString(TerminalInfoInteger(TERMINAL_BUILD)));
   MDLog("REPORT;Common\\Files\\"+file);
   for(int i=0;i<1440;i++)ZeroMemory(md_minutes[i]);
   MDDayStats all,trade;
   bool a=MDQuery("ALL",COPY_TICKS_ALL,true,all);
   bool t=MDQuery("TRADE",COPY_TICKS_TRADE,false,trade);
   bool ca=a&&all.valid_rows==MD_EXPECT_ALL&&all.trades==MD_EXPECT_TRADE&&all.volume==MD_EXPECT_VOLUME&&
           all.hash_all==MD_EXPECT_HASH_ALL&&all.hash_trade==MD_EXPECT_HASH_TRADE;
   bool ct=t&&trade.valid_rows==MD_EXPECT_TRADE&&trade.trades==MD_EXPECT_TRADE&&trade.volume==MD_EXPECT_VOLUME&&
           trade.hash_all==MD_EXPECT_HASH_TRADE&&trade.hash_trade==MD_EXPECT_HASH_TRADE;
   bool bars=MDBars();
   MDLog("RESULT;canonical_all_match="+IntegerToString((int)ca)+";canonical_trade_match="+IntegerToString((int)ct)+
         ";m1_matches_terminal_all_trades="+IntegerToString((int)bars));
   MDLog("END;READ_ONLY_AUDIT;NO_IMPORT;NO_DATA_CORRECTION;NO_STRATEGY_ACCEPTANCE");
   FileClose(md_file);md_file=INVALID_HANDLE;
}
