#property strict
#property version "1.00"
#property description "Piloto experimental WIN$N 21/09/2026. Ordens APENAS no Tester. Nucleo ModeloD preservado; transporte isolado."
#include <ModeloD_PilotoWINN/Piloto_Logica.mqh>
#include <ModeloD_PilotoWINN/Piloto_Especificacao.mqh>

const ulong PW_MAGIC=921260100;
const datetime PW_DAY=D'2026.09.21 00:00:00';
const datetime PW_FIRST=D'2026.09.21 09:02:00';
const datetime PW_CUT=D'2026.09.21 18:00:00';
const datetime PW_END=D'2026.09.22 00:00:00';
MDDay pw_day;MDTap pw_tape[5];
bool pw_sent[5],pw_ended[5],pw_exit_seen[5];ulong pw_position[5];
long pw_retry_cancel[5],pw_retry_close[5];
bool pw_started=false,pw_failed=false,pw_io_failed=false,pw_cut_seen=false,pw_reported=false,pw_initialized=false;
long pw_first_msc=0,pw_last_msc=0,pw_ticks=0,pw_classified=0;
int pw_report=INVALID_HANDLE,pw_requests=0,pw_accepted=0;
string pw_folder="";
double pw_o[1440],pw_h[1440],pw_l[1440],pw_c[1440];long pw_n[1440];
string PWName(int i){if(i==0)return "S38.2";if(i==1)return "S50";if(i==2)return "S61.8";if(i==3)return "R38.2";return "R61.8";}
string PWN(double x){return DoubleToString(x,10);}
bool PWGuard(){return (bool)MQLInfoInteger(MQL_TESTER) && !MQLInfoInteger(MQL_OPTIMIZATION) && _Symbol=="WIN$N";}
void PWLog(string text)
{
 Print("PWIN100;",text);
 if(pw_report==INVALID_HANDLE)return;
 ResetLastError();uint n=FileWriteString(pw_report,TimeToString(TimeCurrent(),TIME_DATE|TIME_SECONDS)+";"+text+"\r\n");
 FileFlush(pw_report);if(n==0||GetLastError()!=0)pw_io_failed=true;
}
void PWFail(string why){pw_failed=true;PWLog("BLOQUEADO;"+why+";SEM_NOVAS_ENTRADAS");}
bool PWWrite(string name,string text)
{
 int h=FileOpen(pw_folder+"\\"+name,FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_COMMON,0,CP_UTF8);
 if(h==INVALID_HANDLE){pw_io_failed=true;return false;}
 ResetLastError();uint n=FileWriteString(h,text);FileFlush(h);int error=GetLastError();FileClose(h);
 bool ok=(n>0&&error==0);if(!ok)pw_io_failed=true;return ok;
}
int PWIndex(long magic){long i=magic-(long)PW_MAGIC;return (i>=0&&i<5)?(int)i:-1;}
bool PWSelectedOrder(int &i)
{
 if(OrderGetString(ORDER_SYMBOL)!=_Symbol)return false;
 i=PWIndex(OrderGetInteger(ORDER_MAGIC));return i>=0;
}
bool PWSelectedPosition(int &i)
{
 if(PositionGetString(POSITION_SYMBOL)!=_Symbol)return false;
 i=PWIndex(PositionGetInteger(POSITION_MAGIC));return i>=0;
}
bool PWSend(MqlTradeRequest &request,string action,int level,MqlTradeResult &result)
{
 ZeroMemory(result);
 if(!PWGuard()){PWFail("GUARDA_TESTER_RECUSOU");return false;}
 MqlTradeCheckResult check;ZeroMemory(check);ResetLastError();bool checked=OrderCheck(request,check);int check_error=GetLastError();
 PWLog("ORDER_CHECK;action="+action+";nivel="+PWName(level)+";ok="+IntegerToString(checked?1:0)+
  ";retcode="+IntegerToString(check.retcode)+";error="+IntegerToString(check_error)+";comment="+check.comment);
 if(!checked || (check.retcode!=0 && check.retcode!=TRADE_RETCODE_DONE))return false;
 if(action=="ENTRADA"&&pw_io_failed)return false;
 ResetLastError();bool sent=OrderSend(request,result);int error=GetLastError();
 bool accepted=sent&&(result.retcode==TRADE_RETCODE_DONE||result.retcode==TRADE_RETCODE_PLACED||result.retcode==TRADE_RETCODE_DONE_PARTIAL);
 PWLog("ORDER_SEND;action="+action+";nivel="+PWName(level)+";ok="+IntegerToString(sent?1:0)+
  ";accepted="+IntegerToString(accepted?1:0)+";retcode="+IntegerToString(result.retcode)+";error="+IntegerToString(error)+
  ";quote_msc="+IntegerToString(pw_last_msc)+";order="+IntegerToString((long)result.order)+";deal="+IntegerToString((long)result.deal)+";volume="+PWN(result.volume)+
  ";price="+PWN(result.price)+";comment="+result.comment);
 return accepted;
}
void PWSubmit(int i)
{
 if(!PWGuard()||pw_failed||pw_io_failed||pw_sent[i])return;
 MDOpportunity opportunity;MDResetOpportunity(opportunity,pw_day.levels[i].valid_open);
 if(!MDCanSubmit(pw_day.levels[i],opportunity,pw_tape[i],true,true))return;
 MDLevel l=pw_day.levels[i];MqlTradeRequest request;MqlTradeResult result;ZeroMemory(request);
 request.action=TRADE_ACTION_PENDING;request.magic=PW_MAGIC+(ulong)i;request.symbol=_Symbol;
 request.volume=1.0;request.type=l.buy?ORDER_TYPE_BUY_LIMIT:ORDER_TYPE_SELL_LIMIT;
 request.price=l.entry_tick;request.sl=l.sl_tick;request.tp=l.tp_tick;request.type_filling=ORDER_FILLING_RETURN;
 long expiration=SymbolInfoInteger(_Symbol,SYMBOL_EXPIRATION_MODE);
 request.type_time=((expiration&SYMBOL_EXPIRATION_GTC)!=0)?ORDER_TIME_GTC:ORDER_TIME_DAY;
 request.comment="PWIN100_"+PWName(i);
 pw_sent[i]=true;pw_requests++;
 if(PWSend(request,"ENTRADA",i,result))pw_accepted++;
 else PWFail("ENTRADA_RECUSADA;nivel="+PWName(i));
}
void PWCancel(ulong ticket,int i,long now,string why)
{
 if(now<pw_retry_cancel[i])return;
 pw_retry_cancel[i]=now+1000;
 MqlTradeRequest request;MqlTradeResult result;ZeroMemory(request);
 request.action=TRADE_ACTION_REMOVE;request.order=ticket;request.symbol=_Symbol;request.magic=PW_MAGIC+(ulong)i;
 if(!PWSend(request,"CANCELAR_"+why,i,result))PWLog("CANCELAMENTO_PENDENTE;nivel="+PWName(i));
}
void PWClose(ulong ticket,int i,long now)
{
 if(now<pw_retry_close[i])return;
 pw_retry_close[i]=now+1000;
 if(!PositionSelectByTicket(ticket))return;
 MqlTick quote;ZeroMemory(quote);if(!SymbolInfoTick(_Symbol,quote)||quote.bid<=0||quote.ask<=0)return;
 MqlTradeRequest request;MqlTradeResult result;ZeroMemory(request);
 request.action=TRADE_ACTION_DEAL;request.position=ticket;request.symbol=_Symbol;request.magic=PW_MAGIC+(ulong)i;
 request.volume=PositionGetDouble(POSITION_VOLUME);
 request.type=(PositionGetInteger(POSITION_TYPE)==POSITION_TYPE_BUY)?ORDER_TYPE_SELL:ORDER_TYPE_BUY;
 request.price=(request.type==ORDER_TYPE_SELL)?quote.bid:quote.ask;request.deviation=0;request.comment="PWIN100_CORTE_18H";
 long filling=SymbolInfoInteger(_Symbol,SYMBOL_FILLING_MODE);
 if((filling&SYMBOL_FILLING_FOK)!=0)request.type_filling=ORDER_FILLING_FOK;
 else if((filling&SYMBOL_FILLING_IOC)!=0)request.type_filling=ORDER_FILLING_IOC;
 else if(SymbolInfoInteger(_Symbol,SYMBOL_TRADE_EXEMODE)!=SYMBOL_TRADE_EXECUTION_MARKET)request.type_filling=ORDER_FILLING_RETURN;
 else {PWFail("SEM_FILLING_PARA_ZERAGEM");return;}
 PWLog("CORTE_PRECO;position="+IntegerToString((long)ticket)+";quote_msc="+IntegerToString(quote.time_msc));
 if(!PWSend(request,"CORTE_18H",i,result))PWLog("ZERAGEM_PENDENTE;nivel="+PWName(i));
}
void PWManage(long now,bool cutoff)
{
 for(int j=OrdersTotal()-1;j>=0;j--)
 {
  ulong ticket=OrderGetTicket(j);int i=-1;if(ticket==0||!PWSelectedOrder(i))continue;
  if(cutoff||pw_ended[i]||pw_exit_seen[i])PWCancel(ticket,i,now,cutoff?"CORTE":(pw_exit_seen[i]?"PRIMEIRA_SAIDA":"SLTP_TEORICO_APOS_TOQUE"));
 }
 if(cutoff)for(int j=PositionsTotal()-1;j>=0;j--)
 {
  ulong ticket=PositionGetTicket(j);int i=-1;if(ticket==0||!PWSelectedPosition(i))continue;PWClose(ticket,i,now);
 }
}
void PWStart(const MqlTick &tick)
{
 // Base explicita do Work, sem pesquisa de candles futuros nem ajuste live substituido.
 if(tick.time_msc!=(long)PW_FIRST*1000 || tick.last!=187980.0)
 {PWFail("PRIMEIRO_NEGOCIO_DIVERGE;expected=2026.09.21_09:02:00.000_187980;msc="+IntegerToString(tick.time_msc)+";last="+PWN(tick.last));return;}
 MDInputs values;values.high_prev=188730;values.low_prev=185880;values.close_prev=187135;values.open_today=tick.last;values.adjustment=186745;
 if(!MDCalculate(values,pw_day)){PWFail("NUCLEO_RECUSOU_DADOS");return;}
 pw_started=true;PWLog("ABERTURA_CONFIRMADA;BASE_WORK_EXPLICITA;prev=2026.09.18;H=188730;L=185880;C=187135;ajuste=186745;open=187980");
 for(int i=0;i<5;i++)
 {
  MDStartTape(pw_tape[i],tick.last,pw_day.levels[i].entry,tick.time_msc);MDLevel l=pw_day.levels[i];
  PWLog("NIVEL;id="+PWName(i)+";entry_math="+PWN(l.entry)+";sl_math="+PWN(l.sl)+";tp_math="+PWN(l.tp)+
   ";entry_tick="+PWN(l.entry_tick)+";sl_tick="+PWN(l.sl_tick)+";tp_tick="+PWN(l.tp_tick)+
   ";valid_open="+IntegerToString(l.valid_open?1:0)+";geometry_blocked="+IntegerToString(l.geometry_blocked?1:0));
 }
 for(int i=0;i<5&&!pw_failed;i++)PWSubmit(i);
}
void OnTick()
{
 if(!pw_initialized||!PWGuard())return;
 MqlTick tick;ZeroMemory(tick);if(!SymbolInfoTick(_Symbol,tick)){PWFail("SYMBOL_INFO_TICK");return;}
 pw_ticks++;if(pw_first_msc==0)pw_first_msc=tick.time_msc;
 if(pw_last_msc>tick.time_msc){PWFail("RELOGIO_REGREDIU");return;}pw_last_msc=tick.time_msc;
 bool cutoff=tick.time_msc>=(long)PW_CUT*1000;
 if(cutoff&&!pw_cut_seen){pw_cut_seen=true;PWLog("PRIMEIRO_EVENTO_NO_CORTE;msc="+IntegerToString(tick.time_msc));}
 if(!PWExpectedDay(tick.time_msc)){PWFail("EVENTO_FORA_DO_DIA_FIXO");PWManage(tick.time_msc,true);return;}
 bool classified=(tick.flags&120)!=0&&MDPositive(tick.last);
 if(classified)
 {
  pw_classified++;int minute=(int)((tick.time_msc/1000-(long)PW_DAY)/60);
  if(minute>=0&&minute<1440)
  {
   if(pw_n[minute]==0){pw_o[minute]=tick.last;pw_h[minute]=tick.last;pw_l[minute]=tick.last;}
   pw_h[minute]=MathMax(pw_h[minute],tick.last);pw_l[minute]=MathMin(pw_l[minute],tick.last);pw_c[minute]=tick.last;pw_n[minute]++;
  }
  if(!pw_started&&!pw_failed&&!cutoff)PWStart(tick);
  else if(pw_started)for(int i=0;i<5;i++)
  {
   bool touched=pw_tape[i].touched;double previous=pw_tape[i].previous;
   bool fresh=MDObserve(pw_tape[i],tick.last,pw_day.levels[i].entry,tick.time_msc);
   if(!pw_tape[i].complete){PWFail("FITA_INCOMPLETA");break;}
   if(fresh)PWLog("PRIMEIRO_TOQUE_MATEMATICO;nivel="+PWName(i)+";msc="+IntegerToString(tick.time_msc)+";last="+PWN(tick.last));
   if((touched||fresh)&&PWExitCrossed(pw_day.levels[i],touched?previous:pw_day.levels[i].entry,tick.last))pw_ended[i]=true;
  }
 }
 PWManage(tick.time_msc,cutoff);
}
void OnTradeTransaction(const MqlTradeTransaction &transaction,const MqlTradeRequest &request,const MqlTradeResult &result)
{
 if(!pw_initialized||!PWGuard()||transaction.type!=TRADE_TRANSACTION_DEAL_ADD||transaction.deal==0)return;
 if(!HistoryDealSelect(transaction.deal)||HistoryDealGetString(transaction.deal,DEAL_SYMBOL)!=_Symbol)return;
 long entry=HistoryDealGetInteger(transaction.deal,DEAL_ENTRY);ulong position=(ulong)HistoryDealGetInteger(transaction.deal,DEAL_POSITION_ID);
 int i=PWIndex(HistoryDealGetInteger(transaction.deal,DEAL_MAGIC));
 if(i<0)for(int j=0;j<5;j++)if(pw_position[j]==position&&position!=0){i=j;break;}
 if(i<0)return;
 if(entry==DEAL_ENTRY_IN)pw_position[i]=position;
 else if(entry==DEAL_ENTRY_OUT||entry==DEAL_ENTRY_OUT_BY)pw_exit_seen[i]=true;
 else PWFail("DEAL_INOUT_INESPERADO_HEDGE");
 PWLog("DEAL;nivel="+PWName(i)+";ticket="+IntegerToString((long)transaction.deal)+";entry="+IntegerToString(entry)+
  ";msc="+IntegerToString(HistoryDealGetInteger(transaction.deal,DEAL_TIME_MSC))+";price="+PWN(HistoryDealGetDouble(transaction.deal,DEAL_PRICE))+
  ";volume="+PWN(HistoryDealGetDouble(transaction.deal,DEAL_VOLUME))+";reason="+IntegerToString(HistoryDealGetInteger(transaction.deal,DEAL_REASON)));
}
void PWFinish(string hook)
{
 if(!pw_initialized||pw_reported)return;
 pw_reported=true;
 bool history=HistorySelect(PW_DAY,PW_END);double vin[5],vout[5],valuein[5],valueout[5];
 long first[5],last[5];string reasons[5];ulong identifiers[5];
 ArrayInitialize(vin,0);ArrayInitialize(vout,0);ArrayInitialize(valuein,0);ArrayInitialize(valueout,0);
 ArrayInitialize(first,0);ArrayInitialize(last,0);ArrayInitialize(identifiers,0);
 string deals="ticket;position;nivel;entry;time_msc;price;volume;reason;comment\r\n";
 int total=history?HistoryDealsTotal():0;
 for(int j=0;j<total;j++)
 {
  ulong ticket=HistoryDealGetTicket(j);if(HistoryDealGetString(ticket,DEAL_SYMBOL)!=_Symbol)continue;
  int i=PWIndex(HistoryDealGetInteger(ticket,DEAL_MAGIC));if(i<0)continue;
  if(HistoryDealGetInteger(ticket,DEAL_ENTRY)==DEAL_ENTRY_IN)identifiers[i]=(ulong)HistoryDealGetInteger(ticket,DEAL_POSITION_ID);
 }
 for(int j=0;j<total;j++)
 {
  ulong ticket=HistoryDealGetTicket(j);if(HistoryDealGetString(ticket,DEAL_SYMBOL)!=_Symbol)continue;
  ulong position=(ulong)HistoryDealGetInteger(ticket,DEAL_POSITION_ID);int i=-1;
  for(int k=0;k<5;k++)if(identifiers[k]==position&&position!=0){i=k;break;}
  if(i<0)continue;
  long entry=HistoryDealGetInteger(ticket,DEAL_ENTRY),msc=HistoryDealGetInteger(ticket,DEAL_TIME_MSC),reason=HistoryDealGetInteger(ticket,DEAL_REASON);
  double volume=HistoryDealGetDouble(ticket,DEAL_VOLUME),price=HistoryDealGetDouble(ticket,DEAL_PRICE);
  if(!MDPositive(volume)||!MDPositive(price)){PWFail("DEAL_PRECO_VOLUME_INVALIDO");continue;}
  if(entry==DEAL_ENTRY_IN){vin[i]+=volume;valuein[i]+=price*volume;if(first[i]==0||msc<first[i])first[i]=msc;}
  else if(entry==DEAL_ENTRY_OUT||entry==DEAL_ENTRY_OUT_BY){vout[i]+=volume;valueout[i]+=price*volume;if(msc>last[i])last[i]=msc;reasons[i]+=(reasons[i]==""?"":"|")+IntegerToString(reason);}
  else PWFail("HISTORICO_INOUT_INESPERADO");
  deals+=IntegerToString((long)ticket)+";"+IntegerToString((long)position)+";"+PWName(i)+";"+IntegerToString(entry)+";"+IntegerToString(msc)+";"+
   PWN(price)+";"+PWN(volume)+";"+IntegerToString(reason)+";"+HistoryDealGetString(ticket,DEAL_COMMENT)+"\r\n";
 }
 PWWrite("DEALS.csv",deals);
 string order_rows="ticket;nivel;type;state;setup_msc;done_msc;price;SL;TP;volume_initial;volume_current;comment\r\n";
 int order_total=history?HistoryOrdersTotal():0;
 for(int j=0;j<order_total;j++)
 {
  ulong ticket=HistoryOrderGetTicket(j);if(HistoryOrderGetString(ticket,ORDER_SYMBOL)!=_Symbol)continue;
  int i=PWIndex(HistoryOrderGetInteger(ticket,ORDER_MAGIC));if(i<0)continue;
  order_rows+=IntegerToString((long)ticket)+";"+PWName(i)+";"+IntegerToString(HistoryOrderGetInteger(ticket,ORDER_TYPE))+";"+
   IntegerToString(HistoryOrderGetInteger(ticket,ORDER_STATE))+";"+IntegerToString(HistoryOrderGetInteger(ticket,ORDER_TIME_SETUP_MSC))+";"+
   IntegerToString(HistoryOrderGetInteger(ticket,ORDER_TIME_DONE_MSC))+";"+PWN(HistoryOrderGetDouble(ticket,ORDER_PRICE_OPEN))+";"+
   PWN(HistoryOrderGetDouble(ticket,ORDER_SL))+";"+PWN(HistoryOrderGetDouble(ticket,ORDER_TP))+";"+
   PWN(HistoryOrderGetDouble(ticket,ORDER_VOLUME_INITIAL))+";"+PWN(HistoryOrderGetDouble(ticket,ORDER_VOLUME_CURRENT))+";"+HistoryOrderGetString(ticket,ORDER_COMMENT)+"\r\n";
 }
 PWWrite("ORDERS.csv",order_rows);
 int pending[5],positions[5];ArrayInitialize(pending,0);ArrayInitialize(positions,0);
 for(int j=0;j<OrdersTotal();j++){ulong t=OrderGetTicket(j);int i=-1;if(t>0&&PWSelectedOrder(i))pending[i]++;}
 for(int j=0;j<PositionsTotal();j++){ulong t=PositionGetTicket(j);int i=-1;if(t>0&&PWSelectedPosition(i))positions[i]++;}
 string comparison="data;nivel;estado;entrada_math;SL_math;TP_math;entrada_grade5;SL_grade5;TP_grade5;volume_in;volume_out;entrada_media;saida_media;primeiro_in_msc;ultimo_out_msc;pontos_EA_brutos;motivos_nativos;ordens_pendentes;posicoes_abertas;pontos_Work_original;motivo_Work;ambiguo_Work;origem\r\n";
 double sum=0;int closed=0,residual=0;
 for(int i=0;i<5;i++)
 {
  double points=0;bool ok=history&&PWClosedPoints(i<3,vin[i],vout[i],valuein[i],valueout[i],points)&&positions[i]==0&&pending[i]==0;
  string state=ok?"ENCERRADA":(vin[i]>0?"INCOMPLETA":(pending[i]>0?"PENDENTE":"SEM_EXECUCAO"));
  if(!history)state="HISTORICO_INDISPONIVEL";
  if(ok){sum+=points;closed++;}residual+=pending[i]+positions[i];MDLevel l=pw_day.levels[i];
  comparison+="2026-09-21;"+PWName(i)+";"+state+";"+(pw_started?PWN(l.entry):"")+";"+(pw_started?PWN(l.sl):"")+";"+(pw_started?PWN(l.tp):"")+";"+
   (pw_started?PWN(l.entry_tick):"")+";"+(pw_started?PWN(l.sl_tick):"")+";"+(pw_started?PWN(l.tp_tick):"")+";"+
   PWN(vin[i])+";"+PWN(vout[i])+";"+(vin[i]>0?PWN(valuein[i]/vin[i]):"")+";"+(vout[i]>0?PWN(valueout[i]/vout[i]):"")+";"+
   IntegerToString(first[i])+";"+IntegerToString(last[i])+";"+(ok?PWN(points):"")+";"+reasons[i]+";"+IntegerToString(pending[i])+";"+IntegerToString(positions[i])+";"+
   (i==3?"579.863333333333":(i==4?"234.328333333333":""))+";"+(i>=3?"ALVO":"SEM_OPERACAO")+";NAO;MODELAGEM_A_CONFIRMAR_PELO_DIARIO\r\n";
 }
 PWWrite("COMPARATIVO.csv",comparison);
 string bars="time;O_OnTick;H_OnTick;L_OnTick;C_OnTick;n_classificados\r\n";
 for(int j=0;j<1440;j++)if(pw_n[j]>0)bars+=TimeToString(PW_DAY+j*60,TIME_DATE|TIME_MINUTES)+";"+PWN(pw_o[j])+";"+PWN(pw_h[j])+";"+PWN(pw_l[j])+";"+PWN(pw_c[j])+";"+IntegerToString(pw_n[j])+"\r\n";
 PWWrite("M1_ONTICK.csv",bars);
 MqlRates rates[];ArraySetAsSeries(rates,false);ResetLastError();int n=CopyRates(_Symbol,PERIOD_M1,PW_DAY,PW_END-1,rates);int rate_error=GetLastError();
 string native="time;open;high;low;close;tick_volume;real_volume;spread\r\n";
 for(int j=0;j<n;j++)native+=TimeToString(rates[j].time,TIME_DATE|TIME_MINUTES)+";"+PWN(rates[j].open)+";"+PWN(rates[j].high)+";"+PWN(rates[j].low)+";"+PWN(rates[j].close)+";"+IntegerToString(rates[j].tick_volume)+";"+IntegerToString(rates[j].real_volume)+";"+IntegerToString(rates[j].spread)+"\r\n";
 PWWrite("M1_TESTER.csv",native);
 PWLog("RESUMO;hook="+hook+";started="+IntegerToString(pw_started?1:0)+";blocked="+IntegerToString(pw_failed?1:0)+
  ";history_ok="+IntegerToString(history?1:0)+";cut_seen="+IntegerToString(pw_cut_seen?1:0)+";requests="+IntegerToString(pw_requests)+
  ";accepted="+IntegerToString(pw_accepted)+";closed="+IntegerToString(closed)+";residual="+IntegerToString(residual)+";points_closed="+PWN(sum)+
  ";ticks="+IntegerToString(pw_ticks)+";classified="+IntegerToString(pw_classified)+";first_msc="+IntegerToString(pw_first_msc)+";last_msc="+IntegerToString(pw_last_msc)+
  ";M1_n="+IntegerToString(n)+";M1_error="+IntegerToString(rate_error)+";io_failed="+IntegerToString(pw_io_failed?1:0)+";SEM_HOMOLOGACAO_AUTOMATICA;CONFERIR_DIARIO_E_WORK");
 PWLog("ARQUIVOS;Common\\Files\\"+pw_folder);
}
int OnInit()
{
 if(!PWGuard()){Print("PWIN100;RECUSADO;EXCLUSIVO_TESTER_SEM_OTIMIZACAO_WIN$N");return INIT_PARAMETERS_INCORRECT;}
 if(_Period!=PERIOD_M5 || TimeCurrent()<PW_DAY || TimeCurrent()>=PW_FIRST)
 {Print("PWIN100;RECUSADO;USAR_M5_2026.09.21_ATE_2026.09.22;inicio=",TimeToString(TimeCurrent(),TIME_DATE|TIME_SECONDS));return INIT_PARAMETERS_INCORRECT;}
 FolderCreate("ModeloD_Piloto_WINN",FILE_COMMON);
 pw_folder="ModeloD_Piloto_WINN\\WINN100_"+IntegerToString((long)TimeLocal())+"_"+IntegerToString((long)GetMicrosecondCount());
 if(!FolderCreate(pw_folder,FILE_COMMON)){Print("PWIN100;FOLDER_FAILED;error=",GetLastError());return INIT_FAILED;}
 pw_report=FileOpen(pw_folder+"\\RESULTADO.txt",FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_COMMON,0,CP_UTF8);
 if(pw_report==INVALID_HANDLE){Print("PWIN100;FILE_FAILED;error=",GetLastError());return INIT_FAILED;}
 PWWrite("ESPECIFICACAO.txt",PWSpecification(_Symbol));
 PWLog("START;PILOTO_EXPERIMENTAL;CONTRATOS_POR_NIVEL=1;SEM_FINANCEIRO_COMO_CRITERIO;CORE_V21305_INTACTO;NAO_E_EA_DEMO_COMPLETO;ARQUIVOS="+pw_folder);
 string why="";
 if(SymbolInfoInteger(_Symbol,SYMBOL_CUSTOM)!=0)why="SIMBOLO_PERSONALIZADO";
 else if(AccountInfoInteger(ACCOUNT_MARGIN_MODE)!=ACCOUNT_MARGIN_MODE_RETAIL_HEDGING)why="TESTER_PRECISA_HEDGE_PARA_5_NIVEIS_INDEPENDENTES";
 else if(SymbolInfoInteger(_Symbol,SYMBOL_TRADE_MODE)!=SYMBOL_TRADE_MODE_FULL)why="SYMBOL_TRADE_MODE_NAO_FULL";
 else if(SymbolInfoDouble(_Symbol,SYMBOL_TRADE_TICK_SIZE)!=5.0)why="TICK_SIZE_NAO_5";
 else if(!PWVolumeOne(SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN),SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MAX),SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_STEP)))why="VOLUME_1_FORA_DA_GRADE";
 long mode=SymbolInfoInteger(_Symbol,SYMBOL_ORDER_MODE),expiration=SymbolInfoInteger(_Symbol,SYMBOL_EXPIRATION_MODE);
 if(why==""&&((mode&SYMBOL_ORDER_LIMIT)==0||(mode&SYMBOL_ORDER_SL)==0||(mode&SYMBOL_ORDER_TP)==0))why="LIMIT_SL_TP_NAO_SUPORTADOS";
 if(why==""&&(expiration&SYMBOL_EXPIRATION_GTC)==0&&(expiration&SYMBOL_EXPIRATION_DAY)==0)why="GTC_DAY_NAO_SUPORTADO";
 if(pw_io_failed){PWFail("ESCRITA_DO_RELATORIO_FALHOU");return INIT_FAILED;}
 if(why!=""){PWFail(why);return INIT_PARAMETERS_INCORRECT;}
 pw_initialized=true;return INIT_SUCCEEDED;
}
double OnTester(){PWFinish("OnTester");return 0.0;}
void OnDeinit(const int reason)
{
 PWFinish("OnDeinit");if(pw_report!=INVALID_HANDLE){FileClose(pw_report);pw_report=INVALID_HANDLE;}
}
