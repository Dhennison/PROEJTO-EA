#property strict
#property version "1.10"
#property description "Modelo D: piloto de periodo 01 a 21/09/2026. Apenas Tester WIN$N Hedge BRL; 1 contrato/nivel."
#include <ModeloD_PilotoWINN_Periodo/Periodo_Logica.mqh>
#include <ModeloD_PilotoWINN_Periodo/Piloto_Especificacao.mqh>
#include <ModeloD_PilotoWINN_Periodo/Periodo_WorkRelatorio.mqh>
const ulong PM_MAGIC=926090100;
MDDay pm_day[PM_DAYS];MDTap pm_tape[PM_SLOTS];
bool pm_sent[PM_SLOTS],pm_ended[PM_SLOTS],pm_exit_seen[PM_SLOTS],pm_close_requested[PM_SLOTS];
ulong pm_position[PM_SLOTS];long pm_retry_cancel[PM_SLOTS],pm_retry_close[PM_SLOTS];
bool pm_started[PM_DAYS],pm_failed[PM_DAYS],pm_cut_seen[PM_DAYS];
long pm_ticks[PM_DAYS],pm_classified[PM_DAYS],pm_first_msc[PM_DAYS],pm_last_msc[PM_DAYS];
int pm_requests[PM_DAYS],pm_accepted[PM_DAYS];
// Flat global arrays avoid repeated copies of large daily structs on callbacks.
double pm_o[PM_DAYS*1440],pm_h[PM_DAYS*1440],pm_l[PM_DAYS*1440],pm_c[PM_DAYS*1440];
long pm_n[PM_DAYS*1440];
bool pm_initialized=false,pm_global_failed=false,pm_io_failed=false,pm_reported=false;
long pm_last_global_msc=0,pm_unknown_events=0;int pm_active_day=-1;
int pm_report=INVALID_HANDLE;string pm_folder="";
string PMName(int level){if(level==0)return "S38.2";if(level==1)return "S50";if(level==2)return "S61.8";if(level==3)return "R38.2";return "R61.8";}
string PMN(double x){return DoubleToString(x,10);}
string PMDay(int slot){return PMValidSlot(slot)?pm_ref[PMSlotDay(slot)].date:"FORA_REFERENCIA";}
bool PMGuard(){return (bool)MQLInfoInteger(MQL_TESTER)&&!MQLInfoInteger(MQL_OPTIMIZATION)&&_Symbol=="WIN$N";}
void PMLog(string text)
{
 Print("PM110;",text);
 if(pm_report==INVALID_HANDLE)return;
 ResetLastError();uint n=FileWriteString(pm_report,TimeToString(TimeCurrent(),TIME_DATE|TIME_SECONDS)+";"+text+"\r\n");
 FileFlush(pm_report);if(n==0||GetLastError()!=0)pm_io_failed=true;
}
void PMFailDay(int d,string why)
{
 if(d<0||d>=PM_DAYS){pm_global_failed=true;PMLog("BLOQUEIO_GLOBAL;"+why);return;}
 if(!pm_failed[d]){pm_failed[d]=true;PMLog("DIA_BLOQUEADO;data="+pm_ref[d].date+";"+why+";SEM_NOVAS_ENTRADAS_NO_DIA");}
}
bool PMWrite(string name,string text)
{
 int h=FileOpen(pm_folder+"\\"+name,FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_COMMON,0,CP_UTF8);
 if(h==INVALID_HANDLE){pm_io_failed=true;return false;}
 ResetLastError();uint n=FileWriteString(h,text);FileFlush(h);int error=GetLastError();FileClose(h);
 bool ok=n>0&&error==0;if(!ok)pm_io_failed=true;return ok;
}
int PMIndex(long magic){long slot=magic-(long)PM_MAGIC;return slot>=0&&slot<PM_SLOTS?(int)slot:-1;}
bool PMSelectedOrder(int &slot)
{
 if(OrderGetString(ORDER_SYMBOL)!=_Symbol)return false;
 slot=PMIndex(OrderGetInteger(ORDER_MAGIC));return PMValidSlot(slot);
}
bool PMSelectedPosition(int &slot)
{
 if(PositionGetString(POSITION_SYMBOL)!=_Symbol)return false;
 slot=PMIndex(PositionGetInteger(POSITION_MAGIC));return PMValidSlot(slot);
}
bool PMSend(MqlTradeRequest &request,string action,int slot,MqlTradeResult &result)
{
 ZeroMemory(result);
 if(!PMGuard()||!PMValidSlot(slot)||AccountInfoString(ACCOUNT_CURRENCY)!="BRL")
 {pm_global_failed=true;PMLog("TRANSPORTE_RECUSADO;GUARDA_TESTER_ATIVO_MOEDA_OU_NIVEL");return false;}
 MqlTradeCheckResult check;ZeroMemory(check);ResetLastError();bool checked=OrderCheck(request,check);int error=GetLastError();
 string identity=";data="+PMDay(slot)+";nivel="+PMName(PMSlotLevel(slot));
 PMLog("ORDER_CHECK;action="+action+identity+";ok="+IntegerToString(checked?1:0)+";retcode="+IntegerToString(check.retcode)+";error="+IntegerToString(error)+";comment="+check.comment);
 if(!checked||(check.retcode!=0&&check.retcode!=TRADE_RETCODE_DONE))return false;
 if(action=="ENTRADA"&&pm_io_failed)return false;
 ResetLastError();bool sent=OrderSend(request,result);error=GetLastError();
 bool accepted=sent&&(result.retcode==TRADE_RETCODE_DONE||result.retcode==TRADE_RETCODE_PLACED||result.retcode==TRADE_RETCODE_DONE_PARTIAL);
 PMLog("ORDER_SEND;action="+action+identity+";ok="+IntegerToString(sent?1:0)+";accepted="+IntegerToString(accepted?1:0)+
  ";retcode="+IntegerToString(result.retcode)+";error="+IntegerToString(error)+";quote_msc="+IntegerToString(pm_last_global_msc)+
  ";order="+IntegerToString((long)result.order)+";deal="+IntegerToString((long)result.deal)+";volume="+PMN(result.volume)+";price="+PMN(result.price)+";comment="+result.comment);
 return accepted;
}
void PMSubmit(int slot)
{
 if(!PMGuard()||!PMValidSlot(slot)||pm_global_failed||pm_io_failed||pm_sent[slot])return;
 int d=PMSlotDay(slot),level=PMSlotLevel(slot);if(pm_failed[d]||!pm_started[d])return;
 if(pm_last_global_msc>=(long)pm_ref[d].cut*1000)return;
 MDOpportunity opportunity;MDResetOpportunity(opportunity,pm_day[d].levels[level].valid_open);
 if(!MDCanSubmit(pm_day[d].levels[level],opportunity,pm_tape[slot],true,true))return;
 MDLevel l=pm_day[d].levels[level];MqlTradeRequest request;MqlTradeResult result;ZeroMemory(request);
 request.action=TRADE_ACTION_PENDING;request.magic=PM_MAGIC+(ulong)slot;request.symbol=_Symbol;request.volume=1;
 request.type=l.buy?ORDER_TYPE_BUY_LIMIT:ORDER_TYPE_SELL_LIMIT;request.price=l.entry_tick;request.sl=l.sl_tick;request.tp=l.tp_tick;
 request.type_filling=ORDER_FILLING_RETURN;long expiration=SymbolInfoInteger(_Symbol,SYMBOL_EXPIRATION_MODE);
 request.type_time=(expiration&SYMBOL_EXPIRATION_GTC)!=0?ORDER_TIME_GTC:ORDER_TIME_DAY;request.comment="PM110_"+pm_ref[d].date+"_"+PMName(level);
 pm_sent[slot]=true;pm_requests[d]++;
 if(PMSend(request,"ENTRADA",slot,result))pm_accepted[d]++;
 else PMFailDay(d,"ENTRADA_RECUSADA;nivel="+PMName(level));
}
void PMCancel(ulong ticket,int slot,long now,string why)
{
 if(now<pm_retry_cancel[slot])return;
 pm_retry_cancel[slot]=now+1000;MqlTradeRequest request;MqlTradeResult result;ZeroMemory(request);
 request.action=TRADE_ACTION_REMOVE;request.order=ticket;request.symbol=_Symbol;request.magic=PM_MAGIC+(ulong)slot;
 if(!PMSend(request,"CANCELAR_"+why,slot,result))PMLog("CANCELAMENTO_PENDENTE;data="+PMDay(slot)+";nivel="+PMName(PMSlotLevel(slot)));
}
void PMClose(ulong ticket,int slot,long now)
{
 if(now<pm_retry_close[slot])return;
 pm_retry_close[slot]=now+1000;if(!PositionSelectByTicket(ticket))return;
 MqlTick quote;ZeroMemory(quote);if(!SymbolInfoTick(_Symbol,quote)||!MDPositive(quote.bid)||!MDPositive(quote.ask))return;
 MqlTradeRequest request;MqlTradeResult result;ZeroMemory(request);request.action=TRADE_ACTION_DEAL;
 request.position=ticket;request.symbol=_Symbol;request.magic=PM_MAGIC+(ulong)slot;request.volume=PositionGetDouble(POSITION_VOLUME);
 request.type=PositionGetInteger(POSITION_TYPE)==POSITION_TYPE_BUY?ORDER_TYPE_SELL:ORDER_TYPE_BUY;
 request.price=request.type==ORDER_TYPE_SELL?quote.bid:quote.ask;request.deviation=0;request.comment="PM110_CORTE";
 long filling=SymbolInfoInteger(_Symbol,SYMBOL_FILLING_MODE);
 if((filling&SYMBOL_FILLING_FOK)!=0)request.type_filling=ORDER_FILLING_FOK;
 else if((filling&SYMBOL_FILLING_IOC)!=0)request.type_filling=ORDER_FILLING_IOC;
 else if(SymbolInfoInteger(_Symbol,SYMBOL_TRADE_EXEMODE)!=SYMBOL_TRADE_EXECUTION_MARKET)request.type_filling=ORDER_FILLING_RETURN;
 else {PMFailDay(PMSlotDay(slot),"SEM_FILLING_PARA_ZERAGEM");return;}
 pm_close_requested[slot]=true;
 PMLog("CORTE_PRECO;data="+PMDay(slot)+";position="+IntegerToString((long)ticket)+";quote_msc="+IntegerToString(quote.time_msc));
 if(!PMSend(request,"CORTE_HORARIO",slot,result))PMLog("ZERAGEM_PENDENTE;data="+PMDay(slot));
}
bool PMHasOlderInventory(int active)
{
 for(int j=0;j<OrdersTotal();j++){ulong t=OrderGetTicket(j);int slot=-1;if(t>0&&PMSelectedOrder(slot)&&PMSlotDay(slot)<active)return true;}
 for(int j=0;j<PositionsTotal();j++){ulong t=PositionGetTicket(j);int slot=-1;if(t>0&&PMSelectedPosition(slot)&&PMSlotDay(slot)<active)return true;}
 return false;
}
void PMManage(long now)
{
 for(int j=OrdersTotal()-1;j>=0;j--)
 {
  ulong ticket=OrderGetTicket(j);int slot=-1;if(ticket==0||!PMSelectedOrder(slot))continue;
  bool cutoff=now>=(long)pm_ref[PMSlotDay(slot)].cut*1000;
  if(cutoff||pm_ended[slot]||pm_exit_seen[slot])PMCancel(ticket,slot,now,cutoff?"CORTE":(pm_exit_seen[slot]?"PRIMEIRA_SAIDA":"SLTP_TEORICO_APOS_TOQUE"));
 }
 for(int j=PositionsTotal()-1;j>=0;j--)
 {
  ulong ticket=PositionGetTicket(j);int slot=-1;if(ticket==0||!PMSelectedPosition(slot))continue;
  if(now>=(long)pm_ref[PMSlotDay(slot)].cut*1000)PMClose(ticket,slot,now);
 }
}
void PMStart(int d,const MqlTick &tick)
{
 if(tick.time_msc!=(long)pm_ref[d].first*1000||tick.last!=pm_ref[d].values.open_today)
 {PMFailDay(d,"ABERTURA_DIVERGENTE;msc="+IntegerToString(tick.time_msc)+";last="+PMN(tick.last));return;}
 pm_started[d]=true;
 PMLog("ABERTURA_CONFIRMADA;data="+pm_ref[d].date+";prev="+pm_ref[d].previous_date+";open="+PMN(tick.last)+
  ";Hprev="+PMN(pm_ref[d].values.high_prev)+";Lprev="+PMN(pm_ref[d].values.low_prev)+";Cprev="+PMN(pm_ref[d].values.close_prev)+
  ";ajuste_Work="+PMN(pm_ref[d].values.adjustment)+";BASE_HISTORICA_EXPLICITA_WORK");
 for(int l=0;l<5;l++)
 {
  int slot=d*5+l;MDLevel level=pm_day[d].levels[l];MDStartTape(pm_tape[slot],tick.last,level.entry,tick.time_msc);
  PMLog("NIVEL;data="+pm_ref[d].date+";id="+PMName(l)+";entry_math="+PMN(level.entry)+";sl_math="+PMN(level.sl)+";tp_math="+PMN(level.tp)+
   ";entry_tick="+PMN(level.entry_tick)+";sl_tick="+PMN(level.sl_tick)+";tp_tick="+PMN(level.tp_tick)+
   ";valid_open="+IntegerToString(level.valid_open?1:0)+";geometry_blocked="+IntegerToString(level.geometry_blocked?1:0));
 }
 for(int l=0;l<5&&!pm_failed[d];l++)PMSubmit(d*5+l);
}
void OnTick()
{
 if(!pm_initialized||!PMGuard())return;
 MqlTick tick;ZeroMemory(tick);if(!SymbolInfoTick(_Symbol,tick)){PMFailDay(pm_active_day,"SYMBOL_INFO_TICK_FALHOU");return;}
 if(pm_last_global_msc>tick.time_msc){pm_global_failed=true;PMLog("BLOQUEIO_GLOBAL;RELOGIO_REGREDIU");PMManage(pm_last_global_msc);return;}
 pm_last_global_msc=tick.time_msc;
 int d=pm_active_day;
 if(d<0||tick.time_msc<(long)pm_ref[d].begin*1000||tick.time_msc>=(long)pm_ref[d].end*1000)d=PMFindDay(tick.time_msc);
 if(d<0)
 {
  pm_unknown_events++;if(pm_unknown_events==1){pm_global_failed=true;PMLog("BLOQUEIO_GLOBAL;EVENTO_EM_DATA_SEM_REFERENCIA;msc="+IntegerToString(tick.time_msc));}
  PMManage(tick.time_msc);return;
 }
 if(d!=pm_active_day)
 {
  if(PMHasOlderInventory(d)){pm_global_failed=true;PMLog("BLOQUEIO_GLOBAL;SALDO_DE_DIA_ANTERIOR;data="+pm_ref[d].date);}
  pm_active_day=d;PMLog("SESSAO_OBSERVADA;data="+pm_ref[d].date);
 }
 pm_ticks[d]++;if(pm_first_msc[d]==0)pm_first_msc[d]=tick.time_msc;pm_last_msc[d]=tick.time_msc;
 bool cutoff=tick.time_msc>=(long)pm_ref[d].cut*1000;
 if(cutoff&&!pm_cut_seen[d]){pm_cut_seen[d]=true;PMLog("PRIMEIRO_EVENTO_NO_CORTE;data="+pm_ref[d].date+";msc="+IntegerToString(tick.time_msc));}
 bool classified=(tick.flags&120)!=0&&MDPositive(tick.last);
 if(classified)
 {
  pm_classified[d]++;int minute=(int)((tick.time_msc/1000-(long)pm_ref[d].begin)/60),index=d*1440+minute;
  if(minute>=0&&minute<1440)
  {
   if(pm_n[index]==0){pm_o[index]=tick.last;pm_h[index]=tick.last;pm_l[index]=tick.last;}
   pm_h[index]=MathMax(pm_h[index],tick.last);pm_l[index]=MathMin(pm_l[index],tick.last);pm_c[index]=tick.last;pm_n[index]++;
  }
  if(!pm_started[d]&&!pm_failed[d]&&!pm_global_failed&&!pm_io_failed&&!cutoff)PMStart(d,tick);
  else if(pm_started[d])for(int l=0;l<5;l++)
  {
   int slot=d*5+l;bool touched=pm_tape[slot].touched;double previous=pm_tape[slot].previous;
   bool fresh=MDObserve(pm_tape[slot],tick.last,pm_day[d].levels[l].entry,tick.time_msc);
   if(!pm_tape[slot].complete){PMFailDay(d,"FITA_INCOMPLETA");break;}
   if(fresh)PMLog("PRIMEIRO_TOQUE_MATEMATICO;data="+pm_ref[d].date+";nivel="+PMName(l)+";msc="+IntegerToString(tick.time_msc)+";last="+PMN(tick.last));
   if((touched||fresh)&&PMExitCrossed(pm_day[d].levels[l],touched?previous:pm_day[d].levels[l].entry,tick.last))pm_ended[slot]=true;
  }
 }
 PMManage(tick.time_msc);
}
void OnTradeTransaction(const MqlTradeTransaction &transaction,const MqlTradeRequest &request,const MqlTradeResult &result)
{
 if(!pm_initialized||!PMGuard()||transaction.type!=TRADE_TRANSACTION_DEAL_ADD||transaction.deal==0)return;
 if(!HistoryDealSelect(transaction.deal)||HistoryDealGetString(transaction.deal,DEAL_SYMBOL)!=_Symbol)return;
 long entry=HistoryDealGetInteger(transaction.deal,DEAL_ENTRY);ulong position=(ulong)HistoryDealGetInteger(transaction.deal,DEAL_POSITION_ID);
 int slot=PMIndex(HistoryDealGetInteger(transaction.deal,DEAL_MAGIC));
 if(slot<0)for(int s=0;s<PM_SLOTS;s++)if(pm_position[s]==position&&position!=0){slot=s;break;}
 if(!PMValidSlot(slot))return;
 if(entry==DEAL_ENTRY_IN)
 {
  if(pm_position[slot]!=0&&pm_position[slot]!=position)PMFailDay(PMSlotDay(slot),"MULTIPLAS_POSICOES_POR_NIVEL");
  pm_position[slot]=position;
 }
 else if(entry==DEAL_ENTRY_OUT||entry==DEAL_ENTRY_OUT_BY)pm_exit_seen[slot]=true;
 else PMFailDay(PMSlotDay(slot),"DEAL_INOUT_INESPERADO_HEDGE");
 PMLog("DEAL;data="+PMDay(slot)+";nivel="+PMName(PMSlotLevel(slot))+";ticket="+IntegerToString((long)transaction.deal)+
  ";entry="+IntegerToString(entry)+";msc="+IntegerToString(HistoryDealGetInteger(transaction.deal,DEAL_TIME_MSC))+
  ";price="+PMN(HistoryDealGetDouble(transaction.deal,DEAL_PRICE))+";volume="+PMN(HistoryDealGetDouble(transaction.deal,DEAL_VOLUME))+
  ";reason="+IntegerToString(HistoryDealGetInteger(transaction.deal,DEAL_REASON)));
}
#include "Periodo_Relatorio.mqh"
int OnInit()
{
 if(!PMGuard()){Print("PM110;RECUSADO;SOMENTE_TESTER_WIN$N_SEM_OTIMIZACAO");return INIT_PARAMETERS_INCORRECT;}
 PMInitReference();
 if(_Period!=PERIOD_M5||TimeCurrent()<PM_BEGIN||TimeCurrent()>=pm_ref[0].first)
 {Print("PM110;RECUSADO;USAR_M5_2026.09.01_ATE_2026.09.22;inicio=",TimeToString(TimeCurrent(),TIME_DATE|TIME_SECONDS));return INIT_PARAMETERS_INCORRECT;}
 for(int d=0;d<PM_DAYS;d++)
 {
  if(pm_ref[d].begin>=pm_ref[d].first||pm_ref[d].first>=pm_ref[d].cut||pm_ref[d].cut>=pm_ref[d].end||pm_ref[d].last_bar>=pm_ref[d].end||
     pm_ref[d].expected_bars<=0||!MDCalculate(pm_ref[d].values,pm_day[d])||(d>0&&pm_ref[d].begin<pm_ref[d-1].end))
  {Print("PM110;REFERENCIA_INVALIDA;indice=",d);return INIT_PARAMETERS_INCORRECT;}
 }
 FolderCreate("ModeloD_WINN_Periodo",FILE_COMMON);
 pm_folder="ModeloD_WINN_Periodo\\PM110_"+IntegerToString((long)TimeLocal())+"_"+IntegerToString((long)GetMicrosecondCount());
 if(!FolderCreate(pm_folder,FILE_COMMON)){Print("PM110;FOLDER_FAILED;error=",GetLastError());return INIT_FAILED;}
 pm_report=FileOpen(pm_folder+"\\RESULTADO.txt",FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_COMMON,0,CP_UTF8);
 if(pm_report==INVALID_HANDLE){Print("PM110;FILE_FAILED;error=",GetLastError());return INIT_FAILED;}
 PMWrite("ESPECIFICACAO.txt",PWSpecification(_Symbol));
 string reference="data;pregao_anterior;abertura_Work;Hprev;Lprev;Cprev;ajuste_Work;primeira_barra;corte;ultima_barra;expected_M1\r\n";
 for(int d=0;d<PM_DAYS;d++)reference+=pm_ref[d].date+";"+pm_ref[d].previous_date+";"+PMN(pm_ref[d].values.open_today)+";"+
  PMN(pm_ref[d].values.high_prev)+";"+PMN(pm_ref[d].values.low_prev)+";"+PMN(pm_ref[d].values.close_prev)+";"+PMN(pm_ref[d].values.adjustment)+";"+
  TimeToString(pm_ref[d].first,TIME_MINUTES)+";"+TimeToString(pm_ref[d].cut,TIME_MINUTES)+";"+TimeToString(pm_ref[d].last_bar,TIME_MINUTES)+";"+IntegerToString(pm_ref[d].expected_bars)+"\r\n";
 PMWrite("REFERENCIA_USADA.csv",reference);
 PMLog("START;v=1.10;PILOTO_EXPERIMENTAL_POR_PERIODO;WIN$N;01_A_21_SETEMBRO_2026;UM_CONTRATO_POR_NIVEL;CORE_V21305_INTACTO;NAO_E_EA_DEMO_COMPLETO");
 string why="";
 if(AccountInfoString(ACCOUNT_CURRENCY)!="BRL")why="EXIGE_BRL_POR_INI_NO_SECUNDARIO";
 else if(AccountInfoInteger(ACCOUNT_MARGIN_MODE)!=ACCOUNT_MARGIN_MODE_RETAIL_HEDGING)why="EXIGE_HEDGE";
 else if(SymbolInfoInteger(_Symbol,SYMBOL_CUSTOM)!=0)why="EXIGE_WIN$N_NATIVO";
 else if(SymbolInfoInteger(_Symbol,SYMBOL_TRADE_MODE)!=SYMBOL_TRADE_MODE_FULL)why="TRADE_MODE_NAO_FULL";
 else if(SymbolInfoDouble(_Symbol,SYMBOL_TRADE_TICK_SIZE)!=5)why="TICK_SIZE_NAO_5";
 else if(!PMVolumeOne(SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN),SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MAX),SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_STEP)))why="VOLUME_1_FORA_DA_GRADE";
 long mode=SymbolInfoInteger(_Symbol,SYMBOL_ORDER_MODE),expiration=SymbolInfoInteger(_Symbol,SYMBOL_EXPIRATION_MODE);
 if(why==""&&((mode&SYMBOL_ORDER_LIMIT)==0||(mode&SYMBOL_ORDER_SL)==0||(mode&SYMBOL_ORDER_TP)==0))why="LIMIT_SL_TP_NAO_SUPORTADOS";
 if(why==""&&(expiration&SYMBOL_EXPIRATION_GTC)==0&&(expiration&SYMBOL_EXPIRATION_DAY)==0)why="GTC_DAY_NAO_SUPORTADO";
 if(pm_io_failed){PMLog("RECUSADO;ESCRITA_FALHOU");return INIT_FAILED;}
 if(why!=""){PMLog("RECUSADO;"+why);return INIT_PARAMETERS_INCORRECT;}
 pm_initialized=true;return INIT_SUCCEEDED;
}
double OnTester(){PMFinish("OnTester");return 0;}
void OnDeinit(const int reason)
{
 PMFinish("OnDeinit");if(pm_report!=INVALID_HANDLE){FileClose(pm_report);pm_report=INVALID_HANDLE;}
}
