#ifndef MODELOD_PILOTO_CORE_100
#define MODELOD_PILOTO_CORE_100
#define PH_ROWS 204027
#define PH_FROM D'2026.10.29 09:00:00'
#define PH_TO D'2026.10.29 09:10:00'
#define PH_SOURCE_HASH ((ulong)1055272009950594377*10+2)
#define PH_ROOT "ModeloD_Piloto_Controlado"
#define PH_DEFAULT_SOURCE "DiagTicksAB_TERMINAL_GenialInvestimentos-PRD_WINZ26_2026_10_29_09_00_2026_10_29_09_10_GTR_06_20261029_A_765756968_ALL.csv"

string PHNum(const double value) { return DoubleToString(value,-16); }
void PHMix(ulong &hash,const ulong value) { hash^=value; hash*=1099511628211; }
ulong PHQ(const double value)
{
   string word=PHNum(value); ulong hash=1469598103934665603;
   for(int i=0;i<StringLen(word);i++) PHMix(hash,(ulong)StringGetCharacter(word,i));
   return hash;
}
void PHHashTick7(ulong &hash,const MqlTick &tick)
{
   PHMix(hash,(ulong)tick.time_msc);PHMix(hash,PHQ(tick.bid));
   PHMix(hash,PHQ(tick.ask));PHMix(hash,PHQ(tick.last));
   PHMix(hash,tick.volume);PHMix(hash,PHQ(tick.volume_real));
   PHMix(hash,(ulong)tick.flags);
}
void PHHashTick(ulong &hash,const MqlTick &tick)
{ PHMix(hash,(ulong)tick.time);PHHashTick7(hash,tick); }
ulong PHLegacyHash(const MqlTick &ticks[])
{
   ulong hash=1469598103934665603;
   for(int i=0;i<ArraySize(ticks);i++)PHHashTick7(hash,ticks[i]);
   return hash;
}
ulong PHHash(const MqlTick &ticks[])
{
   ulong hash=1469598103934665603;
   for(int i=0;i<ArraySize(ticks);i++) PHHashTick(hash,ticks[i]);
   return hash;
}
bool PHBusiness(const MqlTick &tick)
{ return (tick.flags & 120)!=0 && MathIsValidNumber(tick.last) && tick.last>0; }
bool PHSameTick(const MqlTick &a,const MqlTick &b)
{
   return a.time==b.time && a.time_msc==b.time_msc && a.bid==b.bid &&
          a.ask==b.ask && a.last==b.last && a.volume==b.volume &&
          a.volume_real==b.volume_real && a.flags==b.flags;
}
bool PHSame(const MqlTick &a[],const MqlTick &b[])
{
   if(ArraySize(a)!=ArraySize(b)) return false;
   for(int i=0;i<ArraySize(a);i++) if(!PHSameTick(a[i],b[i])) return false;
   return true;
}
// Greedy ordered subsequence, including all fields and repeated identical rows.
// This proves representability, not that each callback represents a unique trade.
bool PHSubsequence(const MqlTick &source[],const MqlTick &events[])
{
   int cursor=0;
   for(int e=0;e<ArraySize(events);e++)
   {
      while(cursor<ArraySize(source) && !PHSameTick(source[cursor],events[e])) cursor++;
      if(cursor>=ArraySize(source)) return false;
      cursor++;
   }
   return true;
}
// Never split a timestamp group between CustomTicksReplace calls.
int PHBatchEnd(const MqlTick &ticks[],const int begin,const int requested)
{
   int n=ArraySize(ticks);
   if(begin<0||begin>=n||requested<=0)return begin;
   int end=begin+MathMin(requested,n-begin);
   while(end<n&&ticks[end].time_msc==ticks[end-1].time_msc)end++;
   return end;
}
string PHTickText(const MqlTick &t)
{
   return "time="+(string)(long)t.time+";msc="+(string)t.time_msc+";bid="+PHNum(t.bid)+
      ";ask="+PHNum(t.ask)+";last="+PHNum(t.last)+";volume="+(string)t.volume+
      ";volume_real="+PHNum(t.volume_real)+";flags="+(string)t.flags;
}
string PHFlagHistogram(const MqlTick &ticks[])
{
   uint values[64];long counts[64];int used=0;long omitted=0;
   for(int i=0;i<ArraySize(ticks);i++)
   {
      int at=-1;
      for(int j=0;j<used;j++)if(values[j]==ticks[i].flags){at=j;break;}
      if(at<0&&used<64){at=used;used++;values[at]=ticks[i].flags;counts[at]=0;}
      if(at>=0)counts[at]++;else omitted++;
   }
   string text="flags=";
   for(int j=0;j<used;j++)text+=(j>0?",":"")+(string)values[j]+"x"+(string)counts[j];
   return text+";unrepresented_records="+(string)omitted;
}
// Timestamp coverage is separate from record-level equality and subsequence.
string PHTimeCoverage(const MqlTick &source[],const MqlTick &events[])
{
   for(int i=1;i<ArraySize(events);i++)if(events[i].time_msc<events[i-1].time_msc)
      return "MSC_COVERAGE=PENDING_EVENTS_OUT_OF_ORDER";
   int j=0,groups=0,unseen=0,observed=0;
   for(int i=0;i<ArraySize(events);i++)
      if(i==0||events[i].time_msc!=events[i-1].time_msc)observed++;
   for(int i=0;i<ArraySize(source);i++)
   {
      if(i>0&&source[i].time_msc==source[i-1].time_msc)continue;
      groups++;long msc=source[i].time_msc;
      while(j<ArraySize(events)&&events[j].time_msc<msc)j++;
      if(j>=ArraySize(events)||events[j].time_msc!=msc)unseen++;
   }
   return "MSC_COVERAGE;source_groups="+(string)groups+";event_groups="+(string)observed+
      ";source_groups_without_callback="+(string)unseen+";NOT_AUTOMATIC_IMPORT_LOSS";
}
bool PHUnsigned(const string word)
{
   int n=StringLen(word);if(n==0)return false;
   for(int i=0;i<n;i++)
   { ushort c=StringGetCharacter(word,i);if(c<'0'||c>'9')return false; }
   return true;
}
bool PHNumeric(const string word)
{
   int n=StringLen(word),i=0,digits=0;
   if(n==0)return false;
   ushort c=StringGetCharacter(word,i);
   if(c=='+'||c=='-')i++;
   while(i<n)
   {c=StringGetCharacter(word,i);if(c<'0'||c>'9')break;digits++;i++;}
   if(i<n && StringGetCharacter(word,i)=='.')
   {
      i++;while(i<n)
      {c=StringGetCharacter(word,i);if(c<'0'||c>'9')break;digits++;i++;}
   }
   if(digits==0)return false;
   if(i<n && (StringGetCharacter(word,i)=='e'||StringGetCharacter(word,i)=='E'))
   {
      i++;if(i<n && (StringGetCharacter(word,i)=='+'||StringGetCharacter(word,i)=='-'))i++;
      int exponent=0;
      while(i<n)
      {c=StringGetCharacter(word,i);if(c<'0'||c>'9')break;exponent++;i++;}
      if(exponent==0)return false;
   }
   return i==n;
}
bool PHValidTicks(const MqlTick &ticks[],const long lo,const long hi,string &why)
{
   long previous=lo;
   for(int i=0;i<ArraySize(ticks);i++)
   {
      MqlTick t=ticks[i];
      if(t.time_msc<lo||t.time_msc>=hi||t.time_msc<previous||
         t.time!=(datetime)(t.time_msc/1000))
      {why="TEMPO_INVALIDO;index="+IntegerToString(i);return false;}
      if(!MathIsValidNumber(t.bid)||!MathIsValidNumber(t.ask)||
         !MathIsValidNumber(t.last)||!MathIsValidNumber(t.volume_real)||
         t.bid<0||t.ask<0||t.last<0||t.volume_real<0)
      {why="NUMERO_INVALIDO;index="+IntegerToString(i);return false;}
      if((t.flags&120)!=0 && t.last<=0)
      {why="LAST_NEGOCIO_INVALIDO;index="+IntegerToString(i);return false;}
      previous=t.time_msc;
   }
   why="VALIDO";return true;
}
bool PHLoadPilot(const string name,MqlTick &ticks[],string &why)
{
   ArrayResize(ticks,0);
   int file=FileOpen(name,FILE_READ|FILE_CSV|FILE_ANSI|FILE_COMMON,';',CP_UTF8);
   if(file==INVALID_HANDLE){why="CSV_NAO_ABERTO;erro="+IntegerToString(GetLastError());return false;}
   string headers[7]={"time_msc","bid","ask","last","volume","volume_real","flags"};
   for(int h=0;h<7;h++)
   {
      string header=FileReadString(file);
      if(h==0 && StringLen(header)>0 && StringGetCharacter(header,0)==0xFEFF)header=StringSubstr(header,1);
      if(header!=headers[h]){FileClose(file);why="CABECALHO_INVALIDO";return false;}
   }
   if(!FileIsLineEnding(file)){FileClose(file);why="COLUNAS_EXTRAS_CABECALHO";return false;}
   if(ArrayResize(ticks,PH_ROWS)!=PH_ROWS){FileClose(file);why="SEM_MEMORIA_FONTE";return false;}
   int count=0;
   while(!FileIsEnding(file))
   {
      string fields[7];fields[0]=FileReadString(file);
      if(fields[0]=="" && FileIsEnding(file))break;
      if(count>=PH_ROWS){FileClose(file);why="CSV_LINHAS_EXTRAS";return false;}
      for(int k=1;k<7;k++)
      {
         if(FileIsLineEnding(file)||FileIsEnding(file))
         {FileClose(file);why="LINHA_TRUNCADA;index="+IntegerToString(count);return false;}
         fields[k]=FileReadString(file);
      }
      if(!FileIsLineEnding(file)&&!FileIsEnding(file))
      {FileClose(file);why="COLUNAS_EXTRAS";return false;}
      if(!PHUnsigned(fields[0])||!PHUnsigned(fields[4])||!PHUnsigned(fields[6]))
      {FileClose(file);why="INTEIRO_INVALIDO";return false;}
      if(StringLen(fields[0])>16||StringLen(fields[4])>16||StringLen(fields[6])>10)
      {FileClose(file);why="INTEIRO_FORA_DO_LIMITE";return false;}
      for(int k=1;k<6;k++)if(k!=4 && !PHNumeric(fields[k]))
      {FileClose(file);why="DECIMAL_INVALIDO";return false;}
      long msc=StringToInteger(fields[0]),flags=StringToInteger(fields[6]);
      if(flags<0||flags>4294967295){FileClose(file);why="FLAGS_FORA_UINT";return false;}
      ticks[count].time_msc=msc;ticks[count].time=(datetime)(msc/1000);
      ticks[count].bid=StringToDouble(fields[1]);ticks[count].ask=StringToDouble(fields[2]);
      ticks[count].last=StringToDouble(fields[3]);ticks[count].volume=(ulong)StringToInteger(fields[4]);
      ticks[count].volume_real=StringToDouble(fields[5]);ticks[count].flags=(uint)flags;count++;
   }
   FileClose(file);
   if(count!=PH_ROWS){why="CONTAGEM_FONTE_DIVERGE;n="+IntegerToString(count);return false;}
   if(!PHValidTicks(ticks,(long)PH_FROM*1000,(long)PH_TO*1000,why))return false;
   ulong hash=PHLegacyHash(ticks);
   if(hash!=(ulong)PH_SOURCE_HASH)
   {why="HASH_FONTE_DIVERGE;hash="+(string)hash;return false;}
   why="FONTE_29OUT_CONFERIDA;legacy_hash7="+(string)hash;return true;
}
string PHFolder(const string stage)
{
   FolderCreate(PH_ROOT,FILE_COMMON);
   string folder=PH_ROOT+"\\"+stage+"_"+IntegerToString((long)TimeLocal())+"_"+(string)GetMicrosecondCount();
   if(!FolderCreate(folder,FILE_COMMON))return "";
   return folder;
}
bool PHText(const string name,const string text)
{
   int file=FileOpen(name,FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_COMMON|FILE_SHARE_READ,0,CP_UTF8);
   if(file==INVALID_HANDLE)return false;
   uint n=FileWriteString(file,text);FileFlush(file);bool ok=(n>0);FileClose(file);return ok;
}
bool PHExport(const string name,const MqlTick &ticks[])
{
   int file=FileOpen(name,FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_COMMON|FILE_SHARE_READ,0,CP_UTF8);
   if(file==INVALID_HANDLE)return false;
   bool ok=FileWriteString(file,"time_msc;bid;ask;last;volume;volume_real;flags;time\r\n")>0;
   for(int i=0;i<ArraySize(ticks);i++)
   {
      MqlTick t=ticks[i];
      string row=(string)t.time_msc+";"+PHNum(t.bid)+";"+PHNum(t.ask)+";"+PHNum(t.last)+";"+
                 (string)t.volume+";"+PHNum(t.volume_real)+";"+(string)t.flags+";"+(string)(long)t.time+"\r\n";
      if(FileWriteString(file,row)==0){ok=false;break;}
   }
   FileFlush(file);FileClose(file);return ok;
}
string PHCompare(const MqlTick &source[],const MqlTick &seen[])
{
   int ns=ArraySize(source),nr=ArraySize(seen),limit=MathMin(ns,nr);
   long dif[8];ArrayInitialize(dif,0);int first=-1,shown=0;string examples="";
   for(int i=0;i<limit;i++)
   {
      if(source[i].time!=seen[i].time)dif[0]++;
      if(source[i].time_msc!=seen[i].time_msc)dif[1]++;
      if(source[i].bid!=seen[i].bid)dif[2]++;
      if(source[i].ask!=seen[i].ask)dif[3]++;
      if(source[i].last!=seen[i].last)dif[4]++;
      if(source[i].volume!=seen[i].volume)dif[5]++;
      if(source[i].volume_real!=seen[i].volume_real)dif[6]++;
      if(source[i].flags!=seen[i].flags)dif[7]++;
      if(!PHSameTick(source[i],seen[i]))
      {
         if(first<0)first=i;
         if(shown<3)
         {
            examples+="\r\nDIFF_SAMPLE;index="+(string)i+";SOURCE;"+PHTickText(source[i])+"\r\n";
            examples+="DIFF_SAMPLE;index="+(string)i+";SEEN;"+PHTickText(seen[i]);shown++;
         }
      }
   }
   string result="source_n="+IntegerToString(ns)+";seen_n="+IntegerToString(nr)+
      ";exact="+IntegerToString((int)PHSame(source,seen))+";source_hash="+(string)PHHash(source)+
      ";seen_hash="+(string)PHHash(seen)+";positional_differences_on_common_prefix=";
   for(int k=0;k<8;k++)result+=(k>0?",":"")+(string)dif[k];
   return result+";fields=time,time_msc,bid,ask,last,volume,volume_real,flags;first_diff="+(string)first+examples;
}
string PHStats(const MqlTick &ticks[])
{
   int business=0,invalid_last=0,inverted=0,zero_quotes=0;
   for(int i=0;i<ArraySize(ticks);i++)
   {
      if(PHBusiness(ticks[i]))business++;
      if((ticks[i].flags&120)!=0 && (!MathIsValidNumber(ticks[i].last)||ticks[i].last<=0))invalid_last++;
      if(ticks[i].bid>ticks[i].ask)inverted++;
      if(ticks[i].bid==0||ticks[i].ask==0)zero_quotes++;
   }
   return "n="+IntegerToString(ArraySize(ticks))+";business="+IntegerToString(business)+
          ";invalid_last="+IntegerToString(invalid_last)+";bid_gt_ask="+IntegerToString(inverted)+
          ";zero_quotes="+IntegerToString(zero_quotes)+";hash="+(string)PHHash(ticks);
}
// Build theoretical minute bars from SOURCE trades, never Bid or carried Last.
int PHBars(const MqlTick &ticks[],MqlRates &bars[])
{
   ArrayResize(bars,10);int count=0;long key=-1;
   for(int i=0;i<ArraySize(ticks);i++)
   {
      if(!PHBusiness(ticks[i]))continue;
      long minute=ticks[i].time_msc/60000*60;
      if(minute!=key)
      {
         if(count>=10)return -1;
         ZeroMemory(bars[count]);key=minute;bars[count].time=(datetime)key;
         bars[count].open=ticks[i].last;bars[count].high=ticks[i].last;bars[count].low=ticks[i].last;
         count++;
      }
      int b=count-1;
      bars[b].high=MathMax(bars[b].high,ticks[i].last);bars[b].low=MathMin(bars[b].low,ticks[i].last);
      bars[b].close=ticks[i].last;bars[b].tick_volume++;
      bars[b].real_volume+=(long)ticks[i].volume;
   }
   ArrayResize(bars,count);return count;
}
string PHCheckBars(const string symbol,const MqlTick &source[],const string path)
{
   MqlRates expected[],actual[];int n=PHBars(source,expected);
   ResetLastError();int got=CopyRates(symbol,PERIOD_M1,PH_FROM,PH_TO-1,actual);int err=GetLastError();
   bool equal=(n>0&&got==n&&err==0);string report="M1;expected_n="+IntegerToString(n)+
      ";returned="+IntegerToString(got)+";error="+IntegerToString(err)+"\r\n";
   report+="minute;source_O;source_H;source_L;source_C;source_trade_rows;source_sum_volume;actual_O;actual_H;actual_L;actual_C;actual_tick_volume;actual_real_volume;OHLC_equal\r\n";
   for(int i=0;i<n;i++)
   {
      int match=-1;for(int j=0;j<ArraySize(actual);j++)if(actual[j].time==expected[i].time){match=j;break;}
      bool same=false;string seen=";;;;;;";
      if(match>=0)
      {
         MqlRates a=actual[match];same=(a.open==expected[i].open&&a.high==expected[i].high&&
            a.low==expected[i].low&&a.close==expected[i].close);
         seen=PHNum(a.open)+";"+PHNum(a.high)+";"+PHNum(a.low)+";"+PHNum(a.close)+";"+
            (string)a.tick_volume+";"+(string)a.real_volume+";";
      }
      equal=equal&&same;
      report+=TimeToString(expected[i].time,TIME_DATE|TIME_MINUTES)+";"+PHNum(expected[i].open)+";"+
         PHNum(expected[i].high)+";"+PHNum(expected[i].low)+";"+PHNum(expected[i].close)+";"+
         (string)expected[i].tick_volume+";"+(string)expected[i].real_volume+";"+seen+(string)(int)same+"\r\n";
   }
   bool written=PHText(path,report);
   return "M1_OHLC_EQUAL="+(string)(int)equal+";expected_n="+(string)n+";got="+(string)got+
          ";error="+(string)err+";export_ok="+(string)(int)written+";VOLUMES_OBSERVED_NOT_AUTO_CERTIFIED";
}
#endif
