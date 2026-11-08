#property version "1.02"
#property description "Modelo D - diagnostico focal v1.02, somente leitura, SEM ORDENS."
#include "Focal_Core.mqh"

input string InpSimbolo="WINV26";
input datetime InpInicio1=D'2026.09.01 18:20:00';
input datetime InpFim1=D'2026.09.01 18:25:00'; // exclusivo
input datetime InpInicio2=D'2026.09.02 16:10:00';
input datetime InpFim2=D'2026.09.02 16:15:00'; // exclusivo
input string InpIdentificador="GENIAL_FOCAL";
input int InpMaxTentativas=6;

datetime g_from[2],g_to[2];
int g_window=0,g_attempt=0,g_trace=INVALID_HANDLE;
bool g_failed=false,g_busy=false,g_have_previous=false;
string g_folder="";
MqlTick g_all[],g_trade[],g_previous_all[],g_previous_trade[];
MqlRates g_m1[],g_previous_m1[];

string FInt(const long value){return StringFormat("%I64d",value);}
string FUInt(const ulong value){return StringFormat("%I64u",value);}
string FPrice(const double value){return DoubleToString(value,-16);}
string FTime(const datetime value){return TimeToString(value,TIME_DATE|TIME_SECONDS);}
string FCell(string value){StringReplace(value,";",",");StringReplace(value,"\r"," ");StringReplace(value,"\n"," ");return value;}
string FClean(const string value)
{
   string out="";
   for(int i=0;i<StringLen(value) && i<24;i++)
   {
      ushort ch=StringGetCharacter(value,i);
      if((ch>='A' && ch<='Z') || (ch>='a' && ch<='z') || (ch>='0' && ch<='9'))out+=ShortToString(ch);else out+="_";
   }
   return out;
}
void FFail(const string reason)
{
   g_failed=true;EventKillTimer();Print("FOCAL102_FALHA;",reason,";pasta=",g_folder);
   if(g_trace!=INVALID_HANDLE){FileClose(g_trace);g_trace=INVALID_HANDLE;}
   Comment("Diagnostico focal v1.02\nFALHA: ",reason,"\nRelatorios incompletos nao certificam dados. SEM ORDENS.");
}
bool FWrite(const int handle,const string text)
{
   uchar encoded[];int expected=StringToCharArray(text,encoded,0,WHOLE_ARRAY,CP_UTF8)-1;
   ResetLastError();uint actual=FileWriteString(handle,text);
   if(expected<0 || actual!=(uint)expected || GetLastError()!=0){FFail("ESCRITA_INCOMPLETA");return false;}
   return true;
}
int FOpen(const string name)
{
   string path=g_folder+"\\"+name;
   if(FileIsExist(path,FILE_COMMON)){FFail("ARQUIVO_JA_EXISTE_"+name);return INVALID_HANDLE;}
   int f=FileOpen(path,FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_COMMON|FILE_SHARE_READ,0,CP_UTF8);
   if(f==INVALID_HANDLE)FFail("ABERTURA_"+name+"_"+IntegerToString(GetLastError()));
   return f;
}
bool FClose(const int handle)
{
   ResetLastError();FileFlush(handle);int err=GetLastError();FileClose(handle);
   if(err!=0){FFail("FLUSH_ARQUIVO_"+IntegerToString(err));return false;}
   return !g_failed;
}
bool FLog(const string phase,const int n,const int error,const ulong duration,const string detail)
{
   int window_id=(g_window<2?g_window+1:0);
   string line=FTime(TimeLocal())+";"+IntegerToString(window_id)+";"+IntegerToString(g_attempt)+";"+phase+";"+IntegerToString(n)+";"+
      IntegerToString(error)+";"+FUInt(duration)+";"+FCell(detail)+"\r\n";
   Print("FOCAL102_",phase,";janela=",window_id,";tentativa=",g_attempt,";n=",n,";erro=",error,";duracao_ms=",duration,";",detail);
   if(!FWrite(g_trace,line))return false;
   ResetLastError();FileFlush(g_trace);if(GetLastError()!=0){FFail("FLUSH_TENTATIVAS");return false;}
   return true;
}
void FProgress(const string stage)
{
   Comment("Diagnostico focal v1.02 - SOMENTE LEITURA\nJanela ",g_window+1,"/2; tentativa ",g_attempt,"/",InpMaxTentativas,
      "\n",InpSimbolo," ",FTime(g_from[g_window])," -> ",FTime(g_to[g_window])," exclusivo\n",stage,
      "\nUma chamada pode aguardar sincronizacao. SEM ORDENS.");ChartRedraw();
}
bool FSaveTicks(const string name,const MqlTick &ticks[])
{
   int f=FOpen(name);if(f==INVALID_HANDLE)return false;
   bool ok=FWrite(f,"indice;time;time_msc;bid;ask;last;volume;volume_real;flags\r\n");
   int written=0;
   for(int i=0;ok && i<ArraySize(ticks);i++)
   {
      string line=IntegerToString(i)+";"+FInt((long)ticks[i].time)+";"+FInt(ticks[i].time_msc)+";"+FPrice(ticks[i].bid)+";"+FPrice(ticks[i].ask)+";"+
         FPrice(ticks[i].last)+";"+FUInt(ticks[i].volume)+";"+FPrice(ticks[i].volume_real)+";"+FUInt((ulong)ticks[i].flags)+"\r\n";
      ok=FWrite(f,line);if(ok)written++;
   }
   bool closed=FClose(f);return ok && closed && written==ArraySize(ticks);
}
bool FSaveM1(const string name)
{
   int f=FOpen(name);if(f==INVALID_HANDLE)return false;
   bool ok=FWrite(f,"indice;time;horario_servidor;open;high;low;close;tick_volume;real_volume;spread\r\n");int written=0;
   for(int i=0;ok && i<ArraySize(g_m1);i++)
   {
      string line=IntegerToString(i)+";"+FInt((long)g_m1[i].time)+";"+FTime(g_m1[i].time)+";"+FPrice(g_m1[i].open)+";"+FPrice(g_m1[i].high)+";"+
         FPrice(g_m1[i].low)+";"+FPrice(g_m1[i].close)+";"+FInt(g_m1[i].tick_volume)+";"+FInt(g_m1[i].real_volume)+";"+IntegerToString(g_m1[i].spread)+"\r\n";
      ok=FWrite(f,line);if(ok)written++;
   }
   bool closed=FClose(f);return ok && closed && written==ArraySize(g_m1);
}
string FMinuteCells(const FMinute &r)
{
   string prefix=IntegerToString(r.total)+";"+IntegerToString(r.business)+";";
   if(r.business==0)return prefix+";;;;;";
   return prefix+FInt(r.first)+";"+FInt(r.last)+";"+FPrice(r.o)+";"+FPrice(r.h)+";"+FPrice(r.l)+";"+FPrice(r.c);
}
bool FSaveMinutes(const string name,const bool stable)
{
   int f=FOpen(name);if(f==INVALID_HANDLE)return false;
   bool ok=FWrite(f,"minuto_servidor;snapshot_estavel;ALL_total;ALL_negocios;ALL_primeiro_msc;ALL_ultimo_msc;ALL_O;ALL_H;ALL_L;ALL_C;TRADE_total;TRADE_negocios;TRADE_primeiro_msc;TRADE_ultimo_msc;TRADE_O;TRADE_H;TRADE_L;TRADE_C;M1_presente;M1_O;M1_H;M1_L;M1_C;campos_ALL_diferentes_M1;campos_TRADE_diferentes_M1;Delta_ALL_O;Delta_ALL_H;Delta_ALL_L;Delta_ALL_C;Delta_TRADE_O;Delta_TRADE_H;Delta_TRADE_L;Delta_TRADE_C\r\n");
   for(datetime minute=g_from[g_window];ok && minute<g_to[g_window];minute+=60)
   {
      long lo=(long)minute*1000,hi=lo+60000;FMinute a,b;FMinuteStats(g_all,lo,hi,a);FMinuteStats(g_trade,lo,hi,b);
      int index=-1;for(int j=0;j<ArraySize(g_m1);j++)if(g_m1[j].time==minute){index=j;break;}
      string line=FTime(minute)+";"+(stable?"SIM":"NAO")+";"+FMinuteCells(a)+";"+FMinuteCells(b)+";";
      if(index<0)line+="NAO;;;;;SEM_M1;SEM_M1;;;;;;;;";
      else
      {
         MqlRates rate=g_m1[index];
         line+="SIM;"+FPrice(rate.open)+";"+FPrice(rate.high)+";"+FPrice(rate.low)+";"+FPrice(rate.close)+";"+
            (a.business>0?FFields(FDiff(a,rate)):"SEM_NEGOCIO")+";"+(b.business>0?FFields(FDiff(b,rate)):"SEM_NEGOCIO")+";";
         line+=(a.business>0?FPrice(a.o-rate.open)+";"+FPrice(a.h-rate.high)+";"+FPrice(a.l-rate.low)+";"+FPrice(a.c-rate.close):";;;")+";";
         line+=(b.business>0?FPrice(b.o-rate.open)+";"+FPrice(b.h-rate.high)+";"+FPrice(b.l-rate.low)+";"+FPrice(b.c-rate.close):";;;");
      }
      ok=FWrite(f,line+"\r\n");
   }
   bool closed=FClose(f);return ok && closed;
}
bool FSnapshot()
{
   if(ArrayResize(g_previous_all,ArraySize(g_all))!=ArraySize(g_all) || ArrayResize(g_previous_trade,ArraySize(g_trade))!=ArraySize(g_trade) ||
      ArrayResize(g_previous_m1,ArraySize(g_m1))!=ArraySize(g_m1))return false;
   if(ArraySize(g_all)>0 && ArrayCopy(g_previous_all,g_all)!=ArraySize(g_all))return false;
   if(ArraySize(g_trade)>0 && ArrayCopy(g_previous_trade,g_trade)!=ArraySize(g_trade))return false;
   if(ArraySize(g_m1)>0 && ArrayCopy(g_previous_m1,g_m1)!=ArraySize(g_m1))return false;
   return true;
}
void FFinishWindow(const bool valid,const bool stable,const int all_error,const int trade_error,const int rate_error,const string reason)
{
   string base="JANELA"+IntegerToString(g_window+1);
   int f=FOpen(base+"_RELATORIO.txt");if(f==INVALID_HANDLE)return;
   string report="Diagnostico focal v1.02;SEM_ORDENS\r\nSimbolo="+InpSimbolo+"\r\nDe="+FTime(g_from[g_window])+"\r\nAteExclusivo="+FTime(g_to[g_window])+
      "\r\nTentativas="+IntegerToString(g_attempt)+"\r\nValido="+(valid?"SIM":"NAO")+"\r\nEstavel="+(stable?"SIM":"NAO")+"\r\nMotivo="+reason+
      "\r\nALL_n="+IntegerToString(ArraySize(g_all))+"\r\nTRADE_n="+IntegerToString(ArraySize(g_trade))+"\r\nM1_n="+IntegerToString(ArraySize(g_m1))+
      "\r\nErro_ALL="+IntegerToString(all_error)+"\r\nErro_TRADE="+IntegerToString(trade_error)+"\r\nErro_M1="+IntegerToString(rate_error)+
      "\r\nCriterioNegocio=flags & 120 e Last positivo finito; sem arredondar precos.\r\nOrdem original dos registros e time_msc preservados.\r\nSnapshot estavel pode divergir do M1; isso e resultado diagnostico, nao aprovacao para EA.\r\n";
   bool written=FWrite(f,report);bool closed=FClose(f);if(!written || !closed)return;
   if(valid)
   {
      if(!FSaveTicks(base+"_ALL.csv",g_all) || !FSaveTicks(base+"_TRADE.csv",g_trade) || !FSaveM1(base+"_M1.csv") || !FSaveMinutes(base+"_MINUTOS.csv",stable))return;
   }
   if(!FLog("JANELA_CONCLUIDA",ArraySize(g_all),all_error,0,(valid?"VALIDO":"INVALIDO")+(stable?"|ESTAVEL":"|NAO_ESTAVEL")+"|"+reason))return;
   g_window++;g_attempt=0;g_have_previous=false;
   ArrayResize(g_previous_all,0);ArrayResize(g_previous_trade,0);ArrayResize(g_previous_m1,0);
}
int OnInit()
{
   if(MQLInfoInteger(MQL_TESTER)){Print("FOCAL102: esta etapa e para o TERMINAL; o A/B no Tester permanece separado.");return INIT_PARAMETERS_INCORRECT;}
   g_from[0]=InpInicio1;g_to[0]=InpFim1;g_from[1]=InpInicio2;g_to[1]=InpFim2;
   if(InpSimbolo=="" || InpIdentificador=="" || InpMaxTentativas<2 || InpMaxTentativas>12)return INIT_PARAMETERS_INCORRECT;
   for(int i=0;i<2;i++)if(g_from[i]<=0 || g_to[i]<=g_from[i] || g_to[i]-g_from[i]>900 || (long)g_from[i]%60!=0 || (long)g_to[i]%60!=0)return INIT_PARAMETERS_INCORRECT;
   if(!SymbolSelect(InpSimbolo,true)){Print("FOCAL102_SIMBOLO_INDISPONIVEL;",InpSimbolo,";erro=",GetLastError());return INIT_FAILED;}
   string id="F102_"+FClean(InpIdentificador)+"_"+FClean(FTime(TimeLocal()))+"_"+FUInt(GetTickCount64())+"_"+FInt(ChartID());
   g_folder="ModeloD_Historico_Focal\\"+id;
   int meta=FOpen("META.txt");if(meta==INVALID_HANDLE)return INIT_FAILED;
   long custom=-1,mode=-1;SymbolInfoInteger(InpSimbolo,SYMBOL_CUSTOM,custom);SymbolInfoInteger(InpSimbolo,SYMBOL_CHART_MODE,mode);
   bool ok=FWrite(meta,"Diagnostico focal v1.02 - SOMENTE LEITURA\r\nServidor="+AccountInfoString(ACCOUNT_SERVER)+"\r\nAmbiente=TERMINAL\r\nSimbolo="+InpSimbolo+
      "\r\nDescricaoAtualNaoHistorica="+FCell(SymbolInfoString(InpSimbolo,SYMBOL_DESCRIPTION))+"\r\nSymbolCustom="+FInt(custom)+"\r\nModoGrafico="+FInt(mode)+
      "\r\nTimeCurrent="+FTime(TimeCurrent())+"\r\nTimeTradeServer="+FTime(TimeTradeServer())+"\r\nTimeGMT="+FTime(TimeGMT())+
      "\r\nHorarios dos pedidos sao os do servidor; fuso historico nao certificado.\r\nIdentificacao historica e vinculo B3 nao sao aprovados por esta coleta.\r\n");
   bool closed=FClose(meta);if(!ok || !closed)return INIT_FAILED;
   g_trace=FOpen("TENTATIVAS.csv");if(g_trace==INVALID_HANDLE)return INIT_FAILED;
   if(!FWrite(g_trace,"horario_local;janela;tentativa;fase;n;erro;duracao_ms;detalhe\r\n"))return INIT_FAILED;
   if(!EventSetTimer(1))return INIT_FAILED;
   Print("FOCAL102_START;SEM_ORDENS;pasta=",TerminalInfoString(TERMINAL_COMMONDATA_PATH),"\\Files\\",g_folder);
   return INIT_SUCCEEDED;
}
void OnDeinit(const int reason){EventKillTimer();if(g_trace!=INVALID_HANDLE){FileClose(g_trace);g_trace=INVALID_HANDLE;}Comment("");}
void OnTimer()
{
   if(g_busy || g_failed)return;g_busy=true;
   if(!TerminalInfoInteger(TERMINAL_CONNECTED)){Comment("Diagnostico focal v1.02\nPausado: sem conexao. SEM ORDENS.");g_busy=false;return;}
   if(g_window>=2)
   {
      if(!FLog("END",0,0,0,"DUAS_JANELAS_PROCESSADAS_NAO_SIGNIFICA_DADOS_APROVADOS")){g_busy=false;return;}
      FileClose(g_trace);g_trace=INVALID_HANDLE;EventKillTimer();
      Comment("Diagnostico focal v1.02 CONCLUIDO\nEnvie a pasta indicada no Experts em FOCAL102_START.\nResultados em Common/Files/ModeloD_Historico_Focal. SEM ORDENS.");
      Print("FOCAL102_END;pasta=",g_folder);g_busy=false;return;
   }
   g_attempt++;long lo=(long)g_from[g_window]*1000,hi=(long)g_to[g_window]*1000;
   ArrayResize(g_all,0);ArrayResize(g_trade,0);ArrayResize(g_m1,0);
   FProgress("CONSULTANDO_TICKS_ALL");if(!FLog("ALL_BEGIN",0,0,0,"")){g_busy=false;return;}
   ulong began=GetTickCount64();ResetLastError();int na=CopyTicksRange(InpSimbolo,g_all,COPY_TICKS_ALL,(ulong)lo,(ulong)(hi-1));int ea=GetLastError();
   if(!FLog("ALL_END",na,ea,GetTickCount64()-began,"")){g_busy=false;return;}
   FProgress("CONSULTANDO_TICKS_TRADE");if(!FLog("TRADE_BEGIN",0,0,0,"")){g_busy=false;return;}
   began=GetTickCount64();ResetLastError();int nt=CopyTicksRange(InpSimbolo,g_trade,COPY_TICKS_TRADE,(ulong)lo,(ulong)(hi-1));int et=GetLastError();
   if(!FLog("TRADE_END",nt,et,GetTickCount64()-began,"")){g_busy=false;return;}
   FProgress("CONSULTANDO_BARRAS_M1");if(!FLog("M1_BEGIN",0,0,0,"")){g_busy=false;return;}
   began=GetTickCount64();ResetLastError();int nr=CopyRates(InpSimbolo,PERIOD_M1,g_from[g_window],(datetime)(g_to[g_window]-1),g_m1);int er=GetLastError();
   if(!FLog("M1_END",nr,er,GetTickCount64()-began,"")){g_busy=false;return;}
   int ca=0,ct=0;string wa="",wt="",wr="";
   bool va=HCValidate(g_all,na,ea,lo,hi,ca,wa),vt=HCValidate(g_trade,nt,et,lo,hi,ct,wt),vr=FValidRates(g_m1,nr,er,lo,hi,wr);
   bool valid=va && vt && vr;
   bool stable=valid && g_have_previous && HCSame(g_all,g_previous_all) && HCSame(g_trade,g_previous_trade) && FSameRates(g_m1,g_previous_m1);
   string why="ALL="+wa+"|TRADE="+wt+"|M1="+wr;
   if(!FLog("SNAPSHOT",na,ea,0,(valid?"VALIDO":"INVALIDO")+"|"+(stable?"ESTAVEL":"NAO_ESTAVEL")+"|"+why)){g_busy=false;return;}
   if(valid && !FSaveMinutes("JANELA"+IntegerToString(g_window+1)+"_LEITURA"+IntegerToString(g_attempt)+"_MINUTOS.csv",stable)){g_busy=false;return;}
   if(stable || g_attempt>=InpMaxTentativas)FFinishWindow(valid,stable,ea,et,er,why);
   else
   {
      g_have_previous=false;
      if(valid){if(!FSnapshot()){FFail("MEMORIA_SNAPSHOT");g_busy=false;return;}g_have_previous=true;}
   }
   g_busy=false;
}
