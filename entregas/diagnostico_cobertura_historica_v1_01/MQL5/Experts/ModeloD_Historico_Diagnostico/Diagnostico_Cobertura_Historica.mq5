#property version "1.01"
#property description "Diagnostico historico Modelo D v1.01 - SOMENTE LEITURA, SEM ORDENS."
#property tester_file "PLANO_HC100_877.csv"
#include "HC_Core.mqh"

input datetime InpDe=D'2026.09.01 00:00:00';
input datetime InpAte=D'2026.09.21 00:00:00';
input string InpIdentificador="XP_PILOTO";
input string InpSimbolo=""; // vazio: candidato do plano; nao identifica contrato historico
input bool InpConsultarAlternativo=false;
input int InpBlocoMinutos=5; // 1 a 15, memoria limitada por janela
input int InpTentativasPorBloco=4; // duas leituras consecutivas iguais sao obrigatorias
input bool InpReconsultarPendencias=false;

struct HCPlan
{
   string date,previous,ending,cutoff,candidate,alternative,confirmed,contract_evidence,b3_evidence,source,first_work;
   datetime day;
   double adjustment,b3_adjustment,opening,high_prev,low_prev,close_prev;
   bool b3_present,brt;
   int bars_work;
};
HCPlan g_plan[];
int g_rows[],g_done[],g_index=0,g_attempt=0;
string g_symbols[],g_round="",g_prefix="",g_reason="",g_description="";
int g_days=INVALID_HANDLE,g_blocks=INVALID_HANDLE;
bool g_active=false,g_busy=false,g_failed=false;
datetime g_cursor=0,g_end=0;
ulong g_started=0;
MqlTick g_previous_ticks[];
bool g_have_previous=false;
int g_windows=0,g_ok=0,g_empty=0,g_bad=0,g_missing_ticks=0,g_missing_bars=0,g_different=0;
long g_all=0,g_trades=0,g_first=0,g_last=0;
double g_open=0,g_high=0,g_low=0,g_close=0,g_dh=0,g_dl=0,g_dc=0;
bool g_d1=false,g_d1_match=false,g_open_match=false;
long g_chart_mode=-1;

string HTrim(string value){StringTrimLeft(value);StringTrimRight(value);return value;}
string HCell(string value){StringReplace(value,";",",");StringReplace(value,"\r"," ");StringReplace(value,"\n"," ");return value;}
ulong HHash(const string value)
{
   ulong h=1469598103934665603;
   for(int i=0;i<StringLen(value);i++){h^=(ulong)StringGetCharacter(value,i);h*=1099511628211;}
   return h;
}
string HU(const ulong value){return StringFormat("%I64u",value);}
string HL(const long value){return StringFormat("%I64d",value);}
string HD(const double value){return DoubleToString(value,8);}
string HDate(const datetime value){return TimeToString(value,TIME_DATE);}
string HClean(const string value)
{
   string out="";
   for(int i=0;i<StringLen(value) && i<24;i++)
   {
      ushort ch=StringGetCharacter(value,i);
      out+=((ch>='A' && ch<='Z') || (ch>='a' && ch<='z') || (ch>='0' && ch<='9'))?ShortToString(ch):"_";
   }
   return out;
}
void HProgress(const string stage,const datetime begin,const datetime ending,const int reading)
{
   Comment("Diagnostico historico v1.01 - SOMENTE LEITURA\nTarefa ",g_index+1,"/",ArraySize(g_rows)," ",g_symbols[g_index],
      "\nEtapa: ",stage,"\nDe ",TimeToString(begin,TIME_DATE|TIME_SECONDS)," ate ",TimeToString(ending,TIME_DATE|TIME_SECONDS),
      "\nLeitura ",reading,"/",InpTentativasPorBloco,"; conferidos: ",g_ok,"; pendentes: ",g_bad,
      "\nChamada de historico pode aguardar sincronizacao. SEM ORDENS.");
   ChartRedraw();
}
void HStop(const string why)
{
   g_failed=true;EventKillTimer();Print("HC100_FALHA;",why);
   if(g_days!=INVALID_HANDLE){FileClose(g_days);g_days=INVALID_HANDLE;}
   if(g_blocks!=INVALID_HANDLE){FileClose(g_blocks);g_blocks=INVALID_HANDLE;}
   Comment("Diagnostico historico v1.01\nFALHA: ",why,"\nNenhuma ordem enviada.");
}
bool HWrite(const int handle,const string line)
{
   string payload=line+"\r\n";uchar bytes[];
   int expected=StringToCharArray(payload,bytes,0,WHOLE_ARRAY,CP_UTF8)-1;
   ResetLastError();
   uint n=FileWriteString(handle,payload);
   if(expected<0 || n!=(uint)expected || GetLastError()!=0){HStop("ESCRITA_RELATORIO");return false;}
   ResetLastError();FileFlush(handle);
   if(GetLastError()!=0){HStop("FLUSH_RELATORIO");return false;}
   return true;
}
bool HReal(const string symbol)
{
   return StringLen(symbol)==6 && StringSubstr(symbol,0,3)=="WIN" && StringFind("GJMQVZ",StringSubstr(symbol,3,1))>=0 &&
          StringGetCharacter(symbol,4)>='0' && StringGetCharacter(symbol,4)<='9' && StringGetCharacter(symbol,5)>='0' && StringGetCharacter(symbol,5)<='9';
}
string HHeader()
{
   return "Task;Data;SimboloConsultado;Rodada;Janelas;JanelasConferidas;JanelasVazias;JanelasPendentes;TicksALLValidosEstaveis;NegociosValidosEstaveis;PrimeiroMsc;UltimoMsc;TicksEstado;ContratoHistorico;AjusteVinculo;FusoDeclarado;AnteriorD1;ContextoAnteriorWork;AberturaWork;ModoGrafico;MinutosSemTicksComM1;MinutosSemM1ComTicks;MinutosDiferentes;AjusteWork;AjusteB3Declarado;HighAnteriorContrato;LowAnteriorContrato;CloseAnteriorContrato;OpenTicksContrato;CandidatoTecnicoSemVinculos;DadosPrimeiroPiloto;Motivo;DescricaoAtualNaoHistorica;DuracaoMs;Checksum";
}
bool HLoadPlan(ulong &fingerprint)
{
   int f=FileOpen("PLANO_HC100_877.csv",FILE_READ|FILE_TXT|FILE_ANSI,0,CP_UTF8);
   if(f==INVALID_HANDLE){Print("HC100_PLANO_AUSENTE;copiar MQL5/Files/PLANO_HC100_877.csv");return false;}
   string header=HTrim(FileReadString(f));
   string expected="Data;Anterior;FimExclusivo;CorteWork;AjusteWork;Candidato1;Candidato2;ContratoConfirmado;EvidenciaContrato;AjusteB3;EvidenciaB3;FusoBRTConfirmado;AberturaWork;HighAnteriorWork;LowAnteriorWork;CloseAnteriorWork;FonteWork;BarrasWork;PrimeiraBarraWork";
   if(header!=expected){FileClose(f);Print("HC100_CABECALHO_PLANO_INVALIDO");return false;}
   string all=header;datetime last_day=0;int total=0;
   while(!FileIsEnding(f))
   {
      string line=HTrim(FileReadString(f));if(line=="")continue;
      string c[];int n=StringSplit(line,';',c);
      if(n!=19){FileClose(f);Print("HC100_PLANO_COLUNAS_INVALIDAS");return false;}
      datetime day=StringToTime(c[0]+" 00:00:00");
      datetime previous=StringToTime(c[1]+" 00:00:00");
      if(day<=last_day || HDate(day)!=c[0] || previous<=0 || HDate(previous)!=c[1] || previous>=day || !HReal(c[5]) || !HReal(c[6]))
         {FileClose(f);Print("HC100_PLANO_DATA_OU_CANDIDATO_INVALIDO");return false;}
      last_day=day;all+="\n"+line;total++;
      if(day<InpDe || day>InpAte)continue;
      int k=ArraySize(g_plan);if(ArrayResize(g_plan,k+1)!=k+1){FileClose(f);return false;}
      g_plan[k].day=day;g_plan[k].date=c[0];g_plan[k].previous=c[1];g_plan[k].ending=c[2];g_plan[k].cutoff=c[3];
      g_plan[k].adjustment=StringToDouble(c[4]);g_plan[k].candidate=c[5];g_plan[k].alternative=c[6];
      g_plan[k].confirmed=c[7];g_plan[k].contract_evidence=c[8];g_plan[k].b3_present=(c[9]!="");
      g_plan[k].b3_adjustment=StringToDouble(c[9]);g_plan[k].b3_evidence=c[10];g_plan[k].brt=(c[11]=="SIM");
      g_plan[k].opening=StringToDouble(c[12]);g_plan[k].high_prev=StringToDouble(c[13]);g_plan[k].low_prev=StringToDouble(c[14]);
      g_plan[k].close_prev=StringToDouble(c[15]);g_plan[k].source=c[16];g_plan[k].bars_work=(int)StringToInteger(c[17]);g_plan[k].first_work=c[18];
      datetime end=StringToTime(c[0]+" "+c[2]);
      if(!MathIsValidNumber(g_plan[k].adjustment) || !MathIsValidNumber(g_plan[k].opening) || !MathIsValidNumber(g_plan[k].high_prev) ||
         !MathIsValidNumber(g_plan[k].low_prev) || !MathIsValidNumber(g_plan[k].close_prev) || g_plan[k].adjustment<=0 ||
         g_plan[k].opening<=0 || g_plan[k].low_prev<=0 || g_plan[k].high_prev<g_plan[k].low_prev ||
         g_plan[k].close_prev<g_plan[k].low_prev || g_plan[k].close_prev>g_plan[k].high_prev ||
         g_plan[k].bars_work<=0 || end<=day+9*3600 || end>day+86400)
         {FileClose(f);Print("HC100_PLANO_NUMEROS_OU_FIM_INVALIDOS");return false;}
      int copies=(InpConsultarAlternativo && InpSimbolo=="")?2:1;
      for(int j=0;j<copies;j++)
      {
         int t=ArraySize(g_rows);
         if(ArrayResize(g_rows,t+1)!=t+1 || ArrayResize(g_symbols,t+1)!=t+1 || ArrayResize(g_done,t+1)!=t+1){FileClose(f);return false;}
         g_rows[t]=k;g_done[t]=0;g_symbols[t]=(InpSimbolo!="")?InpSimbolo:(j==0?c[5]:c[6]);
      }
   }
   FileClose(f);fingerprint=HHash(all);
   if(total!=877 || ArraySize(g_rows)==0){Print("HC100_PLANO_SEM_877_DATAS_OU_RECORTE_VAZIO");return false;}
   return true;
}
bool HResume()
{
   if(FileSize(g_days)==0)return HWrite(g_days,HHeader());
   FileSeek(g_days,0,SEEK_SET);
   if(HTrim(FileReadString(g_days))!=HHeader()){HStop("CABECALHO_RELATORIO_INCOMPATIVEL");return false;}
   while(!FileIsEnding(g_days))
   {
      string line=HTrim(FileReadString(g_days));if(line=="")continue;
      string c[];int n=StringSplit(line,';',c);
      if(n!=35){HStop("LINHA_INCOMPLETA_USAR_OUTRO_IDENTIFICADOR");return false;}
      int last=StringLen(line)-StringLen(c[34])-1;
      if(last<0 || HU(HHash(StringSubstr(line,0,last)))!=c[34]){HStop("CHECKSUM_RELATORIO_INVALIDO");return false;}
      int task=(int)StringToInteger(c[0]);
      if(task<0 || task>=ArraySize(g_rows) || c[1]!=g_plan[g_rows[task]].date || c[2]!=g_symbols[task])
         {HStop("RETOMADA_IDENTIDADE_INVALIDA");return false;}
      g_done[task]=(!InpReconsultarPendencias || (c[12]=="ESTAVEL_COM_NEGOCIOS_M1_COMPATIVEL" && c[16]=="RECUPERADO"))?1:0;
   }
   FileSeek(g_days,0,SEEK_END);return true;
}
bool HOpen()
{
   ulong fingerprint=0;if(!HLoadPlan(fingerprint))return false;
   string identity=AccountInfoString(ACCOUNT_SERVER)+"|"+HL(AccountInfoInteger(ACCOUNT_LOGIN))+"|"+
      HDate(InpDe)+"|"+HDate(InpAte)+"|"+InpSimbolo+"|"+IntegerToString(InpBlocoMinutos)+"|"+
      IntegerToString(InpTentativasPorBloco)+"|"+IntegerToString((int)InpConsultarAlternativo)+"|"+HU(fingerprint)+"|"+IntegerToString((int)MQLInfoInteger(MQL_TESTER));
   g_prefix="ModeloD_Historico_Cobertura\\HC100_"+HClean(InpIdentificador)+"_"+HU(HHash(identity));
   g_days=FileOpen(g_prefix+"_DIAS.csv",FILE_READ|FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_COMMON|FILE_SHARE_READ,0,CP_UTF8);
   if(g_days==INVALID_HANDLE){Print("HC100_FALHA_ABERTURA_DIARIO;",GetLastError());return false;}
   if(!HResume())return false;
   g_blocks=FileOpen(g_prefix+"_BLOCOS.csv",FILE_READ|FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_COMMON|FILE_SHARE_READ,0,CP_UTF8);
   if(g_blocks==INVALID_HANDLE)return false;
   if(FileSize(g_blocks)==0 && !HWrite(g_blocks,"Task;Data;Simbolo;Rodada;DeMsc;AteExclusivoMsc;Leituras;ALL_n;Negocios;ErroTicks;ErroM1;Estado;Motivo"))return false;
   FileSeek(g_blocks,0,SEEK_END);
   int meta=FileOpen(g_prefix+"_META.txt",FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_COMMON|FILE_SHARE_READ,0,CP_UTF8);
   if(meta==INVALID_HANDLE)return false;
   bool ok=HWrite(meta,"HC100 v1.01 SOMENTE_LEITURA;SEM_ORDENS\r\nServidor="+HCell(AccountInfoString(ACCOUNT_SERVER))+"\r\nAmbiente="+(MQLInfoInteger(MQL_TESTER)?"TESTER":"TERMINAL")+
      "\r\nPlanoHash="+HU(fingerprint)+"\r\nDe="+HDate(InpDe)+"\r\nAte="+HDate(InpAte)+
      "\r\nTimeCurrent="+TimeToString(TimeCurrent(),TIME_DATE|TIME_SECONDS)+"\r\nTimeTradeServer="+TimeToString(TimeTradeServer(),TIME_DATE|TIME_SECONDS)+
      "\r\nTimeGMT="+TimeToString(TimeGMT(),TIME_DATE|TIME_SECONDS)+"\r\nIntegridade total dos ticks e fuso historico nao certificados.\r\nDescricao atual nao prova contrato historico.\r\nCandidatos por calendario nao sao identificacao historica.\r\nResumo e retomada por pregão concluido; pregão interrompido sera reconsultado.\r\nVinculos declarados dependem de revisao documental externa.");
   FileClose(meta);
   Print("HC100_RELATORIOS;",TerminalInfoString(TERMINAL_COMMONDATA_PATH),"\\Files\\",g_prefix,"_DIAS.csv");
   return ok;
}
void HStart()
{
   HCPlan p=g_plan[g_rows[g_index]];
   g_started=GetTickCount64();g_round=TimeToString(TimeLocal(),TIME_DATE|TIME_SECONDS)+"_"+HU(g_started);
   g_cursor=p.day+9*3600;g_end=StringToTime(p.date+" "+p.ending);
   g_windows=0;g_ok=0;g_empty=0;g_bad=0;g_missing_ticks=0;g_missing_bars=0;g_different=0;
   g_all=0;g_trades=0;g_first=0;g_last=0;g_open=0;g_high=0;g_low=0;g_close=0;
   g_dh=0;g_dl=0;g_dc=0;g_d1=false;g_d1_match=false;g_open_match=false;
   g_attempt=0;g_have_previous=false;ArrayResize(g_previous_ticks,0);g_reason="";g_chart_mode=-1;g_description="";
   g_active=true;
   if(!SymbolSelect(g_symbols[g_index],true)){g_reason="SIMBOLO_INDISPONIVEL_"+IntegerToString(GetLastError());g_bad=1;g_cursor=g_end;return;}
   SymbolInfoInteger(g_symbols[g_index],SYMBOL_CHART_MODE,g_chart_mode);
   g_description=SymbolInfoString(g_symbols[g_index],SYMBOL_DESCRIPTION);
   datetime prior=StringToTime(p.previous+" 00:00:00");MqlRates daily[];
   HProgress("CONSULTANDO_D1_ANTERIOR",prior,(datetime)(prior+86399),0);
   Print("HC101_API_BEGIN;tipo=D1;data=",p.date,";simbolo=",g_symbols[g_index],";anterior=",p.previous);
   ulong d1_started=GetTickCount64();
   ResetLastError();int n=CopyRates(g_symbols[g_index],PERIOD_D1,prior,(datetime)(prior+86399),daily);int err=GetLastError();
   Print("HC101_API_END;tipo=D1;data=",p.date,";n=",n,";erro=",err,";duracao_ms=",HU(GetTickCount64()-d1_started));
   Print("HC100_D1;",p.date,";anterior=",p.previous,";n=",n,";erro=",err);
   if(n==1 && err==0 && HDate(daily[0].time)==p.previous && MathIsValidNumber(daily[0].high) && MathIsValidNumber(daily[0].low) && MathIsValidNumber(daily[0].close) && daily[0].low>0 && daily[0].high>=daily[0].low && daily[0].close>=daily[0].low && daily[0].close<=daily[0].high)
   {
      g_d1=true;g_dh=daily[0].high;g_dl=daily[0].low;g_dc=daily[0].close;
      g_d1_match=(g_dh==p.high_prev && g_dl==p.low_prev && g_dc==p.close_prev);
   }
}
void HFinish()
{
   HCPlan p=g_plan[g_rows[g_index]];
   bool good=(g_bad==0 && g_trades>0 && g_ok==g_windows && g_chart_mode==SYMBOL_CHART_MODE_LAST);
   string tick_state=good?"ESTAVEL_COM_NEGOCIOS_M1_COMPATIVEL":(g_trades==0 && g_bad==0?"SEM_NEGOCIOS_OBSERVADOS":"PENDENTE_OU_DIVERGENTE");
   bool contract=(HReal(g_symbols[g_index]) && p.confirmed==g_symbols[g_index] && p.contract_evidence!="");
   bool adjustment=(contract && p.b3_present && MathIsValidNumber(p.b3_adjustment) && p.b3_adjustment>0 && p.b3_evidence!="");
   bool homogeneous=(g_d1_match && g_open_match && adjustment && p.b3_adjustment==p.adjustment);
   string readiness=(good && contract && adjustment && p.brt && homogeneous)?"CANDIDATO_PILOTO_CONFORME_VINCULOS_DECLARADOS":"PENDENTE";
   string reason=g_reason;
   if(!contract)reason+="|IDENTIFICACAO_HISTORICA_PENDENTE";
   if(!adjustment)reason+="|VINCULO_AJUSTE_B3_PENDENTE";
   if(!p.brt)reason+="|FUSO_HISTORICO_PENDENTE";
   if(!g_d1)reason+="|D1_ANTERIOR_PENDENTE";
   else if(!g_d1_match)reason+="|HLC_ANTERIOR_DIFERE_WORK";
   if(!g_open_match)reason+="|ABERTURA_NAO_CONFERIDA_COM_WORK";
   string body=IntegerToString(g_index)+";"+p.date+";"+g_symbols[g_index]+";"+HCell(g_round)+";"+IntegerToString(g_windows)+";"+IntegerToString(g_ok)+";"+
      IntegerToString(g_empty)+";"+IntegerToString(g_bad)+";"+HL(g_all)+";"+HL(g_trades)+";"+HL(g_first)+";"+HL(g_last)+";"+tick_state+";"+
      (contract?"DECLARADO_COM_EVIDENCIA_A_REVISAR":"PENDENTE")+";"+(adjustment?"DECLARADO_COM_EVIDENCIA_A_REVISAR":"PENDENTE")+";"+(p.brt?"SIM":"NAO")+";"+
      (g_d1?"RECUPERADO":"PENDENTE")+";"+(g_d1_match?"IGUAL":"NAO_CONFERIDO_OU_DIFERENTE")+";"+(g_open_match?"IGUAL":"NAO_CONFERIDA_OU_DIFERENTE")+";"+
      HL(g_chart_mode)+";"+IntegerToString(g_missing_ticks)+";"+IntegerToString(g_missing_bars)+";"+IntegerToString(g_different)+";"+HD(p.adjustment)+";"+
      (p.b3_present?HD(p.b3_adjustment):"")+";"+HD(g_dh)+";"+HD(g_dl)+";"+HD(g_dc)+";"+HD(g_open)+";"+
      ((good && g_d1_match && g_open_match)?"SIM_SUJEITO_A_VINCULOS":"NAO")+";"+readiness+";"+HCell(reason)+";"+HCell(g_description)+";"+HU(GetTickCount64()-g_started);
   if(!HWrite(g_days,body+";"+HU(HHash(body))))return;
   Print("HC100_DIA;",p.date,";",g_symbols[g_index],";",tick_state,";",readiness,";",HCell(reason));
   g_done[g_index]=1;g_index++;g_active=false;
}
void HBlock()
{
   datetime end=(datetime)MathMin((double)g_end,(double)(g_cursor+InpBlocoMinutos*60));
   long lo=(long)g_cursor*1000,hi=(long)end*1000;
   g_attempt++;
   HProgress("CONSULTANDO_TICKS_ALL",g_cursor,end,g_attempt);
   Print("HC101_API_BEGIN;tipo=TICKS_ALL;simbolo=",g_symbols[g_index],";de_msc=",HL(lo),";ate_exclusivo_msc=",HL(hi),";leitura=",g_attempt);
   ulong tick_started=GetTickCount64();
   MqlTick ticks[];ResetLastError();int n=CopyTicksRange(g_symbols[g_index],ticks,COPY_TICKS_ALL,(ulong)lo,(ulong)(hi-1));int err=GetLastError();
   Print("HC101_API_END;tipo=TICKS_ALL;de_msc=",HL(lo),";leitura=",g_attempt,";n=",n,";erro=",err,";duracao_ms=",HU(GetTickCount64()-tick_started));
   int trades=0;string why="";bool valid=HCValidate(ticks,n,err,lo,hi,trades,why);
   bool stable=valid && g_have_previous && HCSame(ticks,g_previous_ticks);
   int rate_error=0,missing_ticks=0,missing_bars=0,different=0;bool match=false;
   if(stable)
   {
      HProgress("CONSULTANDO_M1",g_cursor,end,g_attempt);
      Print("HC101_API_BEGIN;tipo=M1;simbolo=",g_symbols[g_index],";de_msc=",HL(lo),";leitura=",g_attempt);
      ulong rate_started=GetTickCount64();
      MqlRates rates[];ResetLastError();int nr=CopyRates(g_symbols[g_index],PERIOD_M1,g_cursor,(datetime)(end-1),rates);rate_error=GetLastError();
      Print("HC101_API_END;tipo=M1;de_msc=",HL(lo),";leitura=",g_attempt,";n=",nr,";erro=",rate_error,";duracao_ms=",HU(GetTickCount64()-rate_started));
      if(nr<0 || nr!=ArraySize(rates) || rate_error!=0)why="API_M1";
      else if(g_chart_mode!=SYMBOL_CHART_MODE_LAST)why="MODO_GRAFICO_NAO_LAST";
      else match=HCM1(ticks,rates,lo,hi,missing_ticks,missing_bars,different,why);
   }
   if(!(stable && match) && g_attempt<InpTentativasPorBloco)
   {
      Print("HC101_RELEITURA;de_msc=",HL(lo),";leitura=",g_attempt,";valida=",valid,";igual_anterior=",stable,";negocios=",trades,";motivo=",(why==""?"AGUARDA_SEGUNDA_LEITURA_IGUAL":why));
      g_have_previous=false;
      if(valid)
      {
         if(ArrayResize(g_previous_ticks,n)!=n){HStop("MEMORIA_SNAPSHOT");return;}
         if(n>0 && ArrayCopy(g_previous_ticks,ticks)!=n){HStop("COPIA_SNAPSHOT");return;}
         g_have_previous=true;
      }
      return;
   }
   bool ok=stable && match;
   if(!stable && valid)why="SEM_DUAS_LEITURAS_IGUAIS";
   string line=IntegerToString(g_index)+";"+g_plan[g_rows[g_index]].date+";"+g_symbols[g_index]+";"+HCell(g_round)+";"+HL(lo)+";"+HL(hi)+";"+
      IntegerToString(g_attempt)+";"+IntegerToString(n)+";"+IntegerToString(trades)+";"+IntegerToString(err)+";"+IntegerToString(rate_error)+";"+(ok?"CONFERIDO":"PENDENTE")+";"+HCell(why);
   if(!HWrite(g_blocks,line))return;
   Print("HC101_BLOCO;de_msc=",HL(lo),";ate_exclusivo_msc=",HL(hi),";leituras=",g_attempt,";estado=",(ok?"CONFERIDO":"PENDENTE"),";motivo=",why);
   g_windows++;g_missing_ticks+=missing_ticks;g_missing_bars+=missing_bars;g_different+=different;
   if(ok)
   {
      g_ok++;if(n==0)g_empty++;g_all+=n;g_trades+=trades;
      for(int i=0;i<n;i++)if((ticks[i].flags & 120)!=0)
      {
         double last=ticks[i].last;
         if(g_first==0){g_first=ticks[i].time_msc;g_open=last;g_high=last;g_low=last;g_open_match=(last==g_plan[g_rows[g_index]].opening);}
         g_last=ticks[i].time_msc;g_close=last;if(last>g_high)g_high=last;if(last<g_low)g_low=last;
      }
   }
   else{g_bad++;g_reason=why+";erro_ticks="+IntegerToString(err)+";erro_m1="+IntegerToString(rate_error);}
   g_cursor=end;g_attempt=0;g_have_previous=false;ArrayResize(g_previous_ticks,0);
}
int OnInit()
{
   if(InpDe<=0 || InpAte<InpDe || InpDe!=StringToTime(HDate(InpDe)+" 00:00:00") ||
      InpAte!=StringToTime(HDate(InpAte)+" 00:00:00") || InpBlocoMinutos<1 || InpBlocoMinutos>15 ||
      InpTentativasPorBloco<2 || InpTentativasPorBloco>20 || InpIdentificador=="" || (InpSimbolo!="" && !HReal(InpSimbolo)))
      return INIT_PARAMETERS_INCORRECT;
   if(!HOpen())return INIT_FAILED;
   if(!EventSetMillisecondTimer(250))return INIT_FAILED;
   Print("HC100_START;v1.01;SOMENTE_LEITURA;SEM_ORDENS;tasks=",ArraySize(g_rows));
   return INIT_SUCCEEDED;
}
void OnDeinit(const int reason)
{
   EventKillTimer();if(g_days!=INVALID_HANDLE)FileClose(g_days);if(g_blocks!=INVALID_HANDLE)FileClose(g_blocks);Comment("");
}
void OnTimer()
{
   if(g_busy || g_failed)return;g_busy=true;
   if(!MQLInfoInteger(MQL_TESTER) && !TerminalInfoInteger(TERMINAL_CONNECTED))
   {Comment("Diagnostico historico v1.01\nPausado: sem conexao. Nenhuma ordem enviada.");g_busy=false;return;}
   while(g_index<ArraySize(g_rows) && g_done[g_index]!=0)g_index++;
   if(g_index>=ArraySize(g_rows))
   {
      EventKillTimer();
      if(g_days!=INVALID_HANDLE){FileClose(g_days);g_days=INVALID_HANDLE;}
      if(g_blocks!=INVALID_HANDLE){FileClose(g_blocks);g_blocks=INVALID_HANDLE;}
      Comment("Diagnostico historico v1.01\nCONCLUIDO. Consulte DIAS.csv, BLOCOS.csv e META.txt em Common/Files/ModeloD_Historico_Cobertura.\nConclusao da consulta nao significa dados aprovados. SEM ORDENS.");
      Print("HC100_END;",g_prefix);g_busy=false;return;
   }
   if(!g_active)HStart();
   if(g_cursor>=g_end)HFinish();else HBlock();
   if(!g_failed)Comment("Diagnostico historico v1.01 - SOMENTE LEITURA\nTarefa ",(int)MathMin(g_index+1,ArraySize(g_rows)),"/",ArraySize(g_rows)," ",g_symbols[(int)MathMin(g_index,ArraySize(g_rows)-1)],
      "\nBlocos conferidos: ",g_ok," pendentes: ",g_bad,"\n",TimeToString(g_cursor,TIME_DATE|TIME_MINUTES),
      "\nLeituras do bloco: ",g_attempt,"/",InpTentativasPorBloco,"\nSem ordens. Retomada por pregao concluido.");
   g_busy=false;
}
