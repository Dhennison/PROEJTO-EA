#ifndef PM_REPORT_110
#define PM_REPORT_110
string PMExitLabel(long reason,int slot,long msc,string comment)
{
 if(reason==DEAL_REASON_TP)return "ALVO";
 if(reason==DEAL_REASON_SL)return "STOP";
 if(reason==DEAL_REASON_EXPERT&&pm_close_requested[slot]&&msc>=(long)pm_ref[PMSlotDay(slot)].cut*1000&&comment=="PM110_CORTE")return "HORARIO";
 return "OUTRO_"+IntegerToString(reason);
}
void PMFinish(string hook)
{
 if(!pm_initialized||pm_reported)return;
 pm_reported=true;PMInitWorkReport(); // Future outcomes are used ONLY for the report.
 bool history=HistorySelect(PM_BEGIN,PM_END-1);
 double vin[PM_SLOTS],vout[PM_SLOTS],valuein[PM_SLOTS],valueout[PM_SLOTS];
 long first[PM_SLOTS],last[PM_SLOTS];ulong identifiers[PM_SLOTS];
 int pending[PM_SLOTS],positions[PM_SLOTS];string reasons[PM_SLOTS],exit_label[PM_SLOTS];
 ArrayInitialize(vin,0);ArrayInitialize(vout,0);ArrayInitialize(valuein,0);ArrayInitialize(valueout,0);
 ArrayInitialize(first,0);ArrayInitialize(last,0);ArrayInitialize(identifiers,0);ArrayInitialize(pending,0);ArrayInitialize(positions,0);
 for(int s=0;s<PM_SLOTS;s++){reasons[s]="";exit_label[s]="";}
 int total=history?HistoryDealsTotal():0;
 for(int j=0;j<total;j++)
 {
  ulong ticket=HistoryDealGetTicket(j);if(HistoryDealGetString(ticket,DEAL_SYMBOL)!=_Symbol)continue;
  int slot=PMIndex(HistoryDealGetInteger(ticket,DEAL_MAGIC));if(!PMValidSlot(slot))continue;
  if(HistoryDealGetInteger(ticket,DEAL_ENTRY)==DEAL_ENTRY_IN)
  {
   ulong identifier=(ulong)HistoryDealGetInteger(ticket,DEAL_POSITION_ID);
   if(identifiers[slot]!=0&&identifiers[slot]!=identifier){history=false;PMFailDay(PMSlotDay(slot),"MULTIPLAS_POSICOES_NO_HISTORICO");}
   identifiers[slot]=identifier;
  }
 }
 string deal_rows="ticket;position;data;nivel;entry;time_msc;price;volume;reason;comment\r\n";
 for(int j=0;j<total;j++)
 {
  ulong ticket=HistoryDealGetTicket(j);if(HistoryDealGetString(ticket,DEAL_SYMBOL)!=_Symbol)continue;
  ulong identifier=(ulong)HistoryDealGetInteger(ticket,DEAL_POSITION_ID);int slot=-1;
  for(int s=0;s<PM_SLOTS;s++)if(identifiers[s]==identifier&&identifier!=0){slot=s;break;}
  if(slot<0)slot=PMIndex(HistoryDealGetInteger(ticket,DEAL_MAGIC));
  if(!PMValidSlot(slot))continue;
  long entry=HistoryDealGetInteger(ticket,DEAL_ENTRY),msc=HistoryDealGetInteger(ticket,DEAL_TIME_MSC),reason=HistoryDealGetInteger(ticket,DEAL_REASON);
  double volume=HistoryDealGetDouble(ticket,DEAL_VOLUME),price=HistoryDealGetDouble(ticket,DEAL_PRICE);
  if(!MDPositive(volume)||!MDPositive(price)){history=false;PMFailDay(PMSlotDay(slot),"DEAL_PRECO_VOLUME_INVALIDO");continue;}
  if(entry==DEAL_ENTRY_IN){vin[slot]+=volume;valuein[slot]+=price*volume;if(first[slot]==0||msc<first[slot])first[slot]=msc;}
  else if(entry==DEAL_ENTRY_OUT||entry==DEAL_ENTRY_OUT_BY)
  {
   vout[slot]+=volume;valueout[slot]+=price*volume;if(msc>last[slot])last[slot]=msc;
   reasons[slot]+=(reasons[slot]==""?"":"|")+IntegerToString(reason);
   string label=PMExitLabel(reason,slot,msc,HistoryDealGetString(ticket,DEAL_COMMENT));
   if(exit_label[slot]=="")exit_label[slot]=label;
   else if(exit_label[slot]!=label)exit_label[slot]="MISTO";
  }
  else {history=false;PMFailDay(PMSlotDay(slot),"HISTORICO_INOUT_INESPERADO");}
  deal_rows+=IntegerToString((long)ticket)+";"+IntegerToString((long)identifier)+";"+PMDay(slot)+";"+PMName(PMSlotLevel(slot))+";"+
   IntegerToString(entry)+";"+IntegerToString(msc)+";"+PMN(price)+";"+PMN(volume)+";"+IntegerToString(reason)+";"+HistoryDealGetString(ticket,DEAL_COMMENT)+"\r\n";
 }
 PMWrite("DEALS.csv",deal_rows);
 string order_rows="ticket;data;nivel;type;state;setup_msc;done_msc;price;SL;TP;volume_initial;volume_current;comment\r\n";
 int order_total=history?HistoryOrdersTotal():0;
 for(int j=0;j<order_total;j++)
 {
  ulong ticket=HistoryOrderGetTicket(j);if(HistoryOrderGetString(ticket,ORDER_SYMBOL)!=_Symbol)continue;
  int slot=PMIndex(HistoryOrderGetInteger(ticket,ORDER_MAGIC));if(!PMValidSlot(slot))continue;
  order_rows+=IntegerToString((long)ticket)+";"+PMDay(slot)+";"+PMName(PMSlotLevel(slot))+";"+
   IntegerToString(HistoryOrderGetInteger(ticket,ORDER_TYPE))+";"+IntegerToString(HistoryOrderGetInteger(ticket,ORDER_STATE))+";"+
   IntegerToString(HistoryOrderGetInteger(ticket,ORDER_TIME_SETUP_MSC))+";"+IntegerToString(HistoryOrderGetInteger(ticket,ORDER_TIME_DONE_MSC))+";"+
   PMN(HistoryOrderGetDouble(ticket,ORDER_PRICE_OPEN))+";"+PMN(HistoryOrderGetDouble(ticket,ORDER_SL))+";"+PMN(HistoryOrderGetDouble(ticket,ORDER_TP))+";"+
   PMN(HistoryOrderGetDouble(ticket,ORDER_VOLUME_INITIAL))+";"+PMN(HistoryOrderGetDouble(ticket,ORDER_VOLUME_CURRENT))+";"+HistoryOrderGetString(ticket,ORDER_COMMENT)+"\r\n";
 }
 PMWrite("ORDERS.csv",order_rows);
 for(int j=0;j<OrdersTotal();j++){ulong t=OrderGetTicket(j);int slot=-1;if(t>0&&PMSelectedOrder(slot))pending[slot]++;}
 for(int j=0;j<PositionsTotal();j++){ulong t=PositionGetTicket(j);int slot=-1;if(t>0&&PMSelectedPosition(slot))positions[slot]++;}
 bool day_complete[PM_DAYS];int observed_bars[PM_DAYS],native_bars[PM_DAYS],m1_differences[PM_DAYS];
 ArrayInitialize(observed_bars,0);ArrayInitialize(native_bars,0);ArrayInitialize(m1_differences,0);
 string observed="time;O_OnTick;H_OnTick;L_OnTick;C_OnTick;n_classificados\r\n";
 string native="time;open;high;low;close;tick_volume;real_volume;spread\r\n";
 for(int d=0;d<PM_DAYS;d++)
 {
  for(int minute=0;minute<1440;minute++)
  {
   int index=d*1440+minute;if(pm_n[index]==0)continue;observed_bars[d]++;
   observed+=TimeToString(pm_ref[d].begin+minute*60,TIME_DATE|TIME_MINUTES)+";"+PMN(pm_o[index])+";"+PMN(pm_h[index])+";"+PMN(pm_l[index])+";"+PMN(pm_c[index])+";"+IntegerToString(pm_n[index])+"\r\n";
  }
  MqlRates rates[];ArraySetAsSeries(rates,false);ResetLastError();
  int n=CopyRates(_Symbol,PERIOD_M1,pm_ref[d].begin,pm_ref[d].end-1,rates);int error=GetLastError();native_bars[d]=n;
  bool coherent=n==pm_ref[d].expected_bars&&error==0&&observed_bars[d]==n;
  for(int j=0;j<n;j++)
  {
   native+=TimeToString(rates[j].time,TIME_DATE|TIME_MINUTES)+";"+PMN(rates[j].open)+";"+PMN(rates[j].high)+";"+PMN(rates[j].low)+";"+PMN(rates[j].close)+";"+
    IntegerToString(rates[j].tick_volume)+";"+IntegerToString(rates[j].real_volume)+";"+IntegerToString(rates[j].spread)+"\r\n";
   int minute=(int)((rates[j].time-pm_ref[d].begin)/60),index=d*1440+minute;
   bool same=minute>=0&&minute<1440&&rates[j].time>=pm_ref[d].begin&&rates[j].time<pm_ref[d].end;
   if(same)same=pm_n[index]>0&&pm_o[index]==rates[j].open&&pm_h[index]==rates[j].high&&pm_l[index]==rates[j].low&&pm_c[index]==rates[j].close;
   if(!same){m1_differences[d]++;coherent=false;}
  }
  if(n>0&&(rates[0].time!=pm_ref[d].first||rates[n-1].time!=pm_ref[d].last_bar))coherent=false;
  bool flat=true,balanced=true;
  for(int l=0;l<5;l++){int slot=d*5+l;if(pending[slot]>0||positions[slot]>0)flat=false;if(MathAbs(vin[slot]-vout[slot])>1e-8)balanced=false;}
  day_complete[d]=pm_started[d]&&!pm_failed[d]&&!pm_global_failed&&!pm_io_failed&&pm_cut_seen[d]&&flat&&balanced&&coherent&&history;
  PMLog("AUDITORIA_DIA;data="+pm_ref[d].date+";started="+IntegerToString(pm_started[d]?1:0)+";cut_seen="+IntegerToString(pm_cut_seen[d]?1:0)+
   ";observed_M1="+IntegerToString(observed_bars[d])+";native_M1="+IntegerToString(n)+";expected_M1="+IntegerToString(pm_ref[d].expected_bars)+
   ";M1_error="+IntegerToString(error)+";M1_differences="+IntegerToString(m1_differences[d])+";day_complete="+IntegerToString(day_complete[d]?1:0)+";OHLC_WORK_A_CONFERIR_FORA_DO_EA");
 }
 PMWrite("M1_ONTICK.csv",observed);PMWrite("M1_TESTER.csv",native);
 string cmp="data;nivel;estado_dia;estado_operacao;abertura_Work;ajuste_Work;entrada_math;SL_math;TP_math;entrada_grade5;SL_grade5;TP_grade5;volume_in;volume_out;entrada_media;saida_media;primeiro_in_msc;ultimo_out_msc;pontos_EA_brutos;motivo_EA;motivos_nativos;ordens_pendentes;posicoes_abertas;Work_tem_operacao;pontos_Work_original;motivo_Work;ambiguo_Work;Work_entrada_hora;Work_saida_hora;referencia_grade5_mesmo_motivo;diferenca_normalizacao;diferenca_execucao;diferenca_EA_Work;classificacao;observacao\r\n";
 string days="data;estado;started;bloqueado;cut_seen;ticks;classificados;observed_M1;native_M1;expected_M1;M1_differences;requests;accepted;closed;residual;pontos_EA_encerradas;operacoes_Work;pontos_Work;ambiguidades_Work;OHLC_Work\r\n";
 double total_points=0,total_work=0;int total_closed=0,completed=0,total_residual=0;long ticks=0;
 for(int d=0;d<PM_DAYS;d++)
 {
  string day_state=pm_ticks[d]==0?"SEM_EVENTOS":(day_complete[d]?"CONCLUIDO_CONFERIR_WORK":"INCOMPLETO");
  double daily_points=0,daily_work=0;int daily_closed=0,daily_residual=0,work_count=0,ambiguous=0;
  for(int l=0;l<5;l++)
  {
   int slot=d*5+l;MDLevel level=pm_day[d].levels[l];double points=0;
   bool closed=history&&PMClosedPoints(level.buy,vin[slot],vout[slot],valuein[slot],valueout[slot],points)&&pending[slot]==0&&positions[slot]==0;
   string state=closed?"ENCERRADA":(vin[slot]>0?"INCOMPLETA":(pending[slot]>0?"PENDENTE":"SEM_EXECUCAO"));
   if(pm_ticks[d]==0)state="SEM_EVENTOS";else if(!pm_started[d])state="ABERTURA_NAO_VALIDADA";else if(!history)state="HISTORICO_INDISPONIVEL";
   if(closed){daily_closed++;daily_points+=points;}
   daily_residual+=pending[slot]+positions[slot];if(pm_work[slot].exists){work_count++;daily_work+=pm_work[slot].points;}if(pm_work[slot].ambiguous)ambiguous++;
   string classification="DADOS_OU_EXECUCAO_PENDENTES";
   if(day_complete[d])
   {
    if(closed&&pm_work[slot].exists)classification=exit_label[slot]==pm_work[slot].reason?"MESMO_MOTIVO_CONFERIR_PRECOS":"MOTIVOS_DIFERENTES";
    else if(closed)classification="OPERACAO_EA_SEM_WORK";
    else if(pm_work[slot].exists)classification="OPERACAO_WORK_SEM_EA";
    else classification="SEM_OPERACAO_NOS_DOIS";
   }
   string note=pm_work[slot].ambiguous?"WORK_AMBIGUO_STOP_PRESERVADO,EA_SINTETICO_NAO_PROVA_CRONOLOGIA_REAL":"MODELAGEM_A_CONFIRMAR_PELO_DIARIO";
   bool same_reason=closed&&pm_work[slot].exists&&exit_label[slot]==pm_work[slot].reason&&(exit_label[slot]=="ALVO"||exit_label[slot]=="STOP");
   double normalized=0;if(same_reason)normalized=(level.buy?1.0:-1.0)*((exit_label[slot]=="ALVO"?level.tp_tick:level.sl_tick)-level.entry_tick);
   cmp+=pm_ref[d].date+";"+PMName(l)+";"+day_state+";"+state+";"+PMN(pm_ref[d].values.open_today)+";"+PMN(pm_ref[d].values.adjustment)+";"+
    PMN(level.entry)+";"+PMN(level.sl)+";"+PMN(level.tp)+";"+PMN(level.entry_tick)+";"+PMN(level.sl_tick)+";"+PMN(level.tp_tick)+";"+
    PMN(vin[slot])+";"+PMN(vout[slot])+";"+(vin[slot]>0?PMN(valuein[slot]/vin[slot]):"")+";"+(vout[slot]>0?PMN(valueout[slot]/vout[slot]):"")+";"+
    IntegerToString(first[slot])+";"+IntegerToString(last[slot])+";"+(closed?PMN(points):"")+";"+exit_label[slot]+";"+reasons[slot]+";"+
    IntegerToString(pending[slot])+";"+IntegerToString(positions[slot])+";"+IntegerToString(pm_work[slot].exists?1:0)+";"+pm_work[slot].points_text+";"+
    pm_work[slot].reason+";"+(pm_work[slot].ambiguous?"SIM":"NAO")+";"+pm_work[slot].entry_time+";"+pm_work[slot].exit_time+";"+
    (same_reason?PMN(normalized):"")+";"+(same_reason?PMN(normalized-pm_work[slot].points):"")+";"+(same_reason?PMN(points-normalized):"")+";"+
    (closed&&pm_work[slot].exists?PMN(points-pm_work[slot].points):"")+";"+classification+";"+note+"\r\n";
  }
  days+=pm_ref[d].date+";"+day_state+";"+IntegerToString(pm_started[d]?1:0)+";"+IntegerToString(pm_failed[d]?1:0)+";"+IntegerToString(pm_cut_seen[d]?1:0)+";"+
   IntegerToString(pm_ticks[d])+";"+IntegerToString(pm_classified[d])+";"+IntegerToString(observed_bars[d])+";"+IntegerToString(native_bars[d])+";"+
   IntegerToString(pm_ref[d].expected_bars)+";"+IntegerToString(m1_differences[d])+";"+IntegerToString(pm_requests[d])+";"+IntegerToString(pm_accepted[d])+";"+
   IntegerToString(daily_closed)+";"+IntegerToString(daily_residual)+";"+(pm_started[d]&&history?PMN(daily_points):"")+";"+IntegerToString(work_count)+";"+
   PMN(daily_work)+";"+IntegerToString(ambiguous)+";PENDENTE_CONFERENCIA_EXTERNA\r\n";
  total_points+=daily_points;total_work+=daily_work;total_closed+=daily_closed;total_residual+=daily_residual;ticks+=pm_ticks[d];if(day_complete[d])completed++;
 }
 PMWrite("COMPARATIVO.csv",cmp);PMWrite("DIAS.csv",days);
 PMLog("RESUMO_PERIODO;hook="+hook+";expected_days="+IntegerToString(PM_DAYS)+";days_complete="+IntegerToString(completed)+
  ";closed="+IntegerToString(total_closed)+";residual="+IntegerToString(total_residual)+";points_closed="+PMN(total_points)+";Work_reference_points="+PMN(total_work)+
  ";ticks="+IntegerToString(ticks)+";unknown_date_events="+IntegerToString(pm_unknown_events)+";global_block="+IntegerToString(pm_global_failed?1:0)+
  ";history_ok="+IntegerToString(history?1:0)+";io_failed="+IntegerToString(pm_io_failed?1:0)+";SEM_HOMOLOGACAO_AUTOMATICA;CONFERIR_DIARIO_E_CANDLES_WORK");
 PMLog("ARQUIVOS;Common\\Files\\"+pm_folder);
}
#endif
