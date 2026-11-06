#ifndef MD_RELATORIO21305
#define MD_RELATORIO21305
string MDReportN21305(double value){return DoubleToString(value,8);}
string MDLevelName21305(int level){if(level==0)return "S38.2";if(level==1)return "S50";if(level==2)return "S61.8";if(level==3)return "R38.2";return "R61.8";}
string MDReportBody21305(const MDOpState &s,const MDOpSnapshot &b,int date) {
 string header="data;contrato;nivel;estado;volume_entrada;volume_saida;volume_residual;entrada_matematica;entrada_solicitada;entrada_media_executada;saida_media_executada;SL_fixo;TP_fixo;pontos_executados_por_contrato;pontos_contratos;slippage_entrada_adverso;slippage_saida_SLTP_adverso;motivos_corretora;profit_brl;commission_brl;swap_brl;fee_brl;custos_disponiveis;operacoes_encerradas;vitorias;derrotas;neutras;acerto_percentual;pontos_teoricos_work;estado_teorico\r\n";
 string body=header;double sum_points=0,sum_contract_points=0,total_in=0,total_out=0,total_profit=0,total_commission=0,total_swap=0,total_fee=0;
 int operations=0,wins=0,losses=0,neutral=0;bool all_costs=true;
 for(int k=0;k<s.nlevels;k++)if(s.levels[k].date==date){
  MDOpLevel l=s.levels[k];double entered=0,exited=0,entry_value=0,exit_value=0,profit=0,commission=0,swap=0,fee=0;
  bool costs=true,prices=b.execution_prices_known,pending=false,exit_slip_known=true;double exit_slip=0;string reasons="",seen=";";
  for(int j=0;j<b.book.orders;j++)if(b.book.o[j].order.ticket==l.order)pending=b.book.o[j].order.state==0;
  for(int d=0;d<b.book.deals;d++){
   MDDeal68 deal=b.book.d[d];bool owned=false;
   for(int p=0;p<s.npositions;p++)if(s.positions[p].owner==k&&s.positions[p].identifier==deal.position&&deal.symbol==l.symbol)owned=true;
   if(!owned)continue;
   string id=";"+IntegerToString(deal.ticket)+";";if(StringFind(seen,id)>=0)continue;seen+=IntegerToString(deal.ticket)+";";
   double price=b.deal_price[d];if(!MDPositive(price))prices=false;
   if(deal.entry==0){entered+=deal.volume;entry_value+=deal.volume*price;}
   else if(deal.entry==1||deal.entry==3){
    exited+=deal.volume;exit_value+=deal.volume*price;long reason=0;
    bool reason_known=DI69((ulong)deal.ticket,DEAL_REASON,reason);
    string code=reason_known?IntegerToString(reason):"NAO_DISPONIVEL";
    if(reason_known&&(reason==DEAL_REASON_SL||reason==DEAL_REASON_TP))
     exit_slip+=(l.prices.buy?1.0:-1.0)*((reason==DEAL_REASON_SL?l.prices.sl_tick:l.prices.tp_tick)-price)*deal.volume;
    else exit_slip_known=false;
    if(StringFind("|"+reasons+"|","|"+code+"|")<0)reasons+=(reasons==""?"":"|")+code;
   }
   double pr=0,co=0,sw=0,fe=0;
   bool available=DD69((ulong)deal.ticket,DEAL_PROFIT,pr)&&DD69((ulong)deal.ticket,DEAL_COMMISSION,co)&&
    DD69((ulong)deal.ticket,DEAL_SWAP,sw)&&DD69((ulong)deal.ticket,DEAL_FEE,fe)&&
    MathIsValidNumber(pr)&&MathIsValidNumber(co)&&MathIsValidNumber(sw)&&MathIsValidNumber(fe);
   costs=costs&&available;if(available){profit+=pr;commission+=co;swap+=sw;fee+=fe;}
  }
  bool closed=entered>0&&MDEqual68(entered,exited)&&!pending;double point_volume=(l.prices.buy?1.0:-1.0)*(exit_value-entry_value);
  double points=closed&&prices?point_volume/entered:0;
  string state=closed?"ENCERRADA":(entered>exited?"ABERTA":(pending?"PENDENTE":(l.touch_server>0?"TOCADA_SEM_EXECUCAO":"SEM_EXECUCAO")));
  if(!prices)state="PRECOS_NAO_CONFERIDOS";
  double average_in=entered>0?entry_value/entered:0,average_out=exited>0?exit_value/exited:0;
  double slip=(l.prices.buy?1.0:-1.0)*(average_in-l.prices.entry_tick);
  int count=closed&&prices?1:0,win=count>0&&points>0?1:0,loss=count>0&&points<0?1:0,zero=count-win-loss;
  body+=IntegerToString(date)+";"+l.symbol+";"+MDLevelName21305(l.level)+";"+state+";"+
   MDReportN21305(entered)+";"+MDReportN21305(exited)+";"+MDReportN21305(entered-exited)+";"+
   DoubleToString(l.prices.entry,16)+";"+MDReportN21305(l.prices.entry_tick)+";"+
   (prices&&entered>0?MDReportN21305(average_in):"")+";"+(prices&&exited>0?MDReportN21305(average_out):"")+";"+
   MDReportN21305(l.prices.sl_tick)+";"+MDReportN21305(l.prices.tp_tick)+";"+
   (count>0?MDReportN21305(points):"")+";"+(count>0?MDReportN21305(point_volume):"")+";"+
   (prices&&entered>0?MDReportN21305(slip):"")+";"+
   (prices&&exited>0&&exit_slip_known?MDReportN21305(exit_slip/exited):"")+";"+reasons+";"+
   (costs?MDReportN21305(profit):"")+";"+(costs?MDReportN21305(commission):"")+";"+
   (costs?MDReportN21305(swap):"")+";"+(costs?MDReportN21305(fee):"")+";"+IntegerToString(costs?1:0)+";"+
   IntegerToString(count)+";"+IntegerToString(win)+";"+IntegerToString(loss)+";"+IntegerToString(zero)+";"+
   (count>0?MDReportN21305(win*100.0/count):"")+";;PENDENTE_BACKTEST_TEORICO_INDEPENDENTE\r\n";
  total_in+=entered;total_out+=exited;all_costs=all_costs&&costs;
  if(costs){total_profit+=profit;total_commission+=commission;total_swap+=swap;total_fee+=fee;}
  if(count>0){sum_points+=points;sum_contract_points+=point_volume;operations++;wins+=win;losses+=loss;neutral+=zero;}
 }
 body+=IntegerToString(date)+";TODOS;TOTAL;SOMENTE_OPERACOES_ENCERRADAS;"+
  MDReportN21305(total_in)+";"+MDReportN21305(total_out)+";"+MDReportN21305(total_in-total_out)+";;;;;;;"+
  MDReportN21305(sum_points)+";"+MDReportN21305(sum_contract_points)+";;;;"+
  (all_costs?MDReportN21305(total_profit):"")+";"+(all_costs?MDReportN21305(total_commission):"")+";"+
  (all_costs?MDReportN21305(total_swap):"")+";"+(all_costs?MDReportN21305(total_fee):"")+";"+IntegerToString(all_costs?1:0)+";"+
  IntegerToString(operations)+";"+IntegerToString(wins)+";"+IntegerToString(losses)+";"+IntegerToString(neutral)+";"+
  (operations>0?MDReportN21305(wins*100.0/operations):"")+";;PENDENTE_BACKTEST_TEORICO_INDEPENDENTE\r\n";
 return body;
}
bool MDReportPoints21305(const MDOpSnapshot &b) {
 if(!b.execution_prices_known||Scope615()!=operational.scope)return false;
 string why;MDOpState checked=operational;
 if(!MDOpReconcile(checked,b,opclock.utc,why)||MDOpEncode(checked)!=MDOpEncode(operational))return false;
 for(int k=0;k<operational.nlevels;k++){
  int date=operational.levels[k].date;bool done=false;for(int j=0;j<k;j++)if(operational.levels[j].date==date)done=true;if(done)continue;
  string path="MDD21305_PONTOS_"+operational.scope+"_"+IntegerToString(date)+".csv";
  string body=MDReportBody21305(operational,b,date),previous="";
  if(FileIsExist(path,FILE_COMMON)&&MDOpReadFile(path,previous)&&previous==body)continue;
  if(!MDOpWriteFile(path+".next",body)||!FileMove(path+".next",FILE_COMMON,path,FILE_COMMON|FILE_REWRITE)||
     !MDOpReadFile(path,previous)||previous!=body){Report615("PONTOS21305_FALHA;path="+path+";SEM_ARQUIVAR_SESSAO");return false;}
  Report615("PONTOS21305_ATUALIZADO;path=Common\\Files\\"+path+";EXECUTADOS_PONDERADOS;TEORICOS_WORK_PENDENTES");
 }
 return true;
}
#endif
