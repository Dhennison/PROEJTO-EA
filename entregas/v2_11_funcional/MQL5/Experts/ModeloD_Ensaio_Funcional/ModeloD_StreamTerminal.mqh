#ifndef MD_STREAM_TERMINAL615
#define MD_STREAM_TERMINAL615
#include "ModeloD_SparseM1615N.mqh"
#include "ModeloD_QueryEvidence.mqh"
// Uma chamada consome no maximo cinco minutos FECHADOS, com auditoria M1.
// O estado original so muda depois que o bloco completo passa nas verificacoes.
// Em divergencia, ALL pode atualizar antes/depois de TRADE no cache do terminal.
// A recuperacao preserva a regra: somente eventos com flags de negociacao entram.
bool MDStreamRecoverAll615(const MDStream615 &state,long end,bool observation_only,MDStream615 &recovered,string &reason)
{
 long from=state.cursor;MDStream615 candidate=state;
 if(!MDStreamBegin615(candidate,from,end)){reason="ALL_JANELA_INVALIDA";return false;}
 MDQueryReset209(query_all209,"ALL_FILTRADO",from,end);query_all209.attempted=true;
 MqlTick all[];ResetLastError();long tick_began=(long)GetTickCount64();
 int total=MDCopyTicksRange211(state.data.contract,all,COPY_TICKS_ALL,(ulong)from,(ulong)end);int error=GetLastError();
 query_all209.returned=total;query_all209.tick_error=error;query_all209.ticks_ms=(long)GetTickCount64()-tick_began;
 if(total<0||error!=0){reason="ALL_COPY_ERRO_"+IntegerToString(error)+";retornados="+IntegerToString(total);return false;}
 if(total>500000){reason="ALL_EXCEDE_CAPACIDADE_500000";return false;}
 uint mask=TICK_FLAG_LAST|TICK_FLAG_VOLUME|TICK_FLAG_BUY|TICK_FLAG_SELL;int accepted=0;
 for(int i=0;i<total;i++)
 {
  if(IsStopped()){reason="ALL_INTERROMPIDO";return false;}
  if((all[i].flags&mask)==0)continue;
  if(!MDStreamPush615(candidate,all[i].time_msc,all[i].last))
  {reason="ALL_TICK_NEGOCIACAO_INVALIDO;indice="+IntegerToString(i)+";msc="+IntegerToString(all[i].time_msc)+
    ";last="+DoubleToString(all[i].last,16)+";flags="+IntegerToString((long)all[i].flags);return false;}
  MDQueryTick209(query_all209,all[i].time_msc,all[i].last,all[i].flags);accepted++;
 }
 MqlRates rates[];ArraySetAsSeries(rates,false);ResetLastError();
 long rates_began=(long)GetTickCount64();
 int bars=MDCopyRates211(state.data.contract,PERIOD_M1,(datetime)(from/1000),(datetime)(end/1000),rates);error=GetLastError();
 query_all209.bars=bars;query_all209.m1_error=error;query_all209.m1_ms=(long)GetTickCount64()-rates_began;
 int expected=(int)((end-from+1)/60000),r=0,empty=0;string absent="";
 if(error!=0||bars<0||bars>expected){reason="ALL_COBERTURA_M1_INVALIDA;erro="+IntegerToString(error)+";barras="+IntegerToString(bars);return false;}
 for(int j=0;j<bars;j++){
  long stamp=(long)rates[j].time*1000;
  if(stamp<from||stamp>end||stamp%60000!=0||(j>0&&rates[j].time<=rates[j-1].time))
  {reason="ALL_M1_FORA_JANELA_DUPLICADO_OU_FORA_ORDEM";return false;}
  MDQueryBar209(query_all209,j,stamp,rates[j].open,rates[j].high,rates[j].low,rates[j].close);
 }
 for(int i=0;i<expected;i++)
 {
  long stamp=from+(long)i*60000;int k=(int)((stamp-candidate.audit.begin_msc)/60000);
  if(k<0||k>=540){reason="ALL_INDICE_MINUTO_INVALIDO";return false;}
  bool present=r<bars;if(present)present=(long)rates[r].time*1000==stamp;
  double o=0,h=0,l=0,c=0;if(present){o=rates[r].open;h=rates[r].high;l=rates[r].low;c=rates[r].close;}
  MDMinuteAudit m=candidate.audit.minutes[k];
  if(!MDSparseMinute615N(m,present?1:0,o,h,l,c,observation_only)&&
     !(present&&MDReferenceMinute211(stamp,all,total)))
  {reason="ALL_FILTRADO_DIVERGE_M1;minuto_msc="+IntegerToString(stamp)+";filtrados="+IntegerToString(accepted)+
    ";ticks_minuto="+IntegerToString(m.count)+";ticks_O="+DoubleToString(m.o,8)+";ticks_H="+DoubleToString(m.h,8)+
    ";ticks_L="+DoubleToString(m.l,8)+";ticks_C="+DoubleToString(m.c,8)+";M1_O="+DoubleToString(o,8)+
    ";M1_H="+DoubleToString(h,8)+";M1_L="+DoubleToString(l,8)+";M1_C="+DoubleToString(c,8);return false;}
  if(present)r++;else{empty++;absent+=IntegerToString(stamp)+",";}
 }
 if(IsStopped()){reason="ALL_INTERROMPIDO";return false;}
 if(!MDConnected210()){reason="ALL_DESCONECTADO_APOS_COLETA";return false;}
 if(!MDSparseFinish615N(candidate,observation_only)){reason="ALL_BLOCO_NAO_CONCLUIDO";return false;}
 recovered=candidate;reason="BLOCO_RECUPERADO_COPY_TICKS_ALL_FILTRADO;registros_all="+IntegerToString(total)+
  ";eventos_negociacao="+IntegerToString(accepted)+";minutos_com_registros="+IntegerToString(bars)+
  ";minutos_sem_registros="+IntegerToString(empty)+";ausentes_msc="+absent+";M1_CONFERIDO;INTEGRIDADE_TOTAL_NAO_CERTIFICADA";return true;
}
bool MDStreamCollect615(MDStream615 &state,long end,string &reason,bool observation_only=false)
{
 long from=state.cursor;MDStream615 candidate=state;
 MDQueryReset209(query_trade209,"TRADE",from,end);MDQueryReset209(query_all209,"ALL_FILTRADO",from,end);
 if(!MDStreamBegin615(candidate,from,end)){reason="JANELA_DE_BLOCO_INVALIDA";return false;}
 MqlTick ticks[];ResetLastError();query_trade209.attempted=true;long tick_began=(long)GetTickCount64();
 int count=MDCopyTicksRange211(state.data.contract,ticks,COPY_TICKS_TRADE,(ulong)from,(ulong)end);
 int error=GetLastError();
 query_trade209.returned=count;query_trade209.tick_error=error;query_trade209.ticks_ms=(long)GetTickCount64()-tick_began;
 if(count<0||error!=0){reason="COPY_TICKS_ERRO_"+IntegerToString(error)+";retornados="+IntegerToString(count);return false;}
 if(count>500000){reason="BLOCO_EXCEDE_CAPACIDADE_500000";return false;}
 for(int i=0;i<count;i++)
 {
  if(IsStopped()){reason="INTERROMPIDO";return false;}
  uint mask=TICK_FLAG_LAST|TICK_FLAG_VOLUME|TICK_FLAG_BUY|TICK_FLAG_SELL;
  if((ticks[i].flags&mask)==0||!MDStreamPush615(candidate,ticks[i].time_msc,ticks[i].last))
  {reason="TICK_OU_ABERTURA_INCONSISTENTE;indice="+IntegerToString(i)+
   ";msc="+IntegerToString(ticks[i].time_msc)+";last="+DoubleToString(ticks[i].last,16)+";flags="+IntegerToString((long)ticks[i].flags)+
   ";previous_accepted_msc="+IntegerToString(candidate.audit.last_msc)+";from="+IntegerToString(from)+";end="+IntegerToString(end)+
   ";expected_open_msc="+IntegerToString(candidate.data.open_msc)+";expected_open="+DoubleToString(candidate.data.values.open_today,16);return false;}
  MDQueryTick209(query_trade209,ticks[i].time_msc,ticks[i].last,ticks[i].flags);
 }
 MqlRates rates[];ArraySetAsSeries(rates,false);ResetLastError();long rates_began=(long)GetTickCount64();
 int bars=MDCopyRates211(state.data.contract,PERIOD_M1,(datetime)(from/1000),(datetime)(end/1000),rates);
 error=GetLastError();query_trade209.bars=bars;query_trade209.m1_error=error;query_trade209.m1_ms=(long)GetTickCount64()-rates_began;
 int expected=(int)((end-from+1)/60000);
 if(error!=0||bars<0||bars>expected){reason="COBERTURA_M1_INVALIDA;erro="+IntegerToString(error)+";barras="+IntegerToString(bars);return false;}
 long previous=from-1;
 for(int i=0;i<bars;i++)
 {
  long stamp=(long)rates[i].time*1000;
  if(!MDSparseStamp615N(stamp,from,end,previous)){reason="M1_FORA_JANELA_DUPLICADO_OU_FORA_ORDEM";return false;}
  MDQueryBar209(query_trade209,i,stamp,rates[i].open,rates[i].high,rates[i].low,rates[i].close);
  previous=stamp;
 }
 int r=0,empty=0;string absent="";
 for(int i=0;i<expected;i++)
 {
  long stamp=from+(long)i*60000;
  int k=(int)((stamp-candidate.audit.begin_msc)/60000);
  if(k<0||k>=540){reason="INDICE_MINUTO_INVALIDO";return false;}
  bool present=r<bars;
  if(present)present=(long)rates[r].time*1000==stamp;
  double o=0,h=0,l=0,c=0;
  if(present){o=rates[r].open;h=rates[r].high;l=rates[r].low;c=rates[r].close;}
  MDMinuteAudit m=candidate.audit.minutes[k];
  if(!MDSparseMinute615N(m,present?1:0,o,h,l,c,observation_only)&&
     !(present&&MDReferenceMinute211(stamp,ticks,count)))
  {
   MDStream615 recovered;string recovery_reason;
   if(MDStreamRecoverAll615(state,end,observation_only,recovered,recovery_reason))
   {state=recovered;reason=recovery_reason;return true;}
   reason="TICKS_DIVERGEM_M1;minuto_msc="+IntegerToString(stamp)+
    ";bloco_inicio="+IntegerToString(from)+";bloco_fim="+IntegerToString(end)+
    ";ticks_minuto="+IntegerToString(m.count)+";barras_minuto="+IntegerToString(present?1:0)+
    ";ticks_O="+DoubleToString(m.o,8)+";ticks_H="+DoubleToString(m.h,8)+
    ";ticks_L="+DoubleToString(m.l,8)+";ticks_C="+DoubleToString(m.c,8)+
    ";M1_O="+DoubleToString(o,8)+";M1_H="+DoubleToString(h,8)+
    ";M1_L="+DoubleToString(l,8)+";M1_C="+DoubleToString(c,8)+";recuperacao_ALL="+recovery_reason;
   return false;
  }
  if(present)r++;
  else{empty++;absent+=IntegerToString(stamp)+",";}
 }
 if(IsStopped()){reason="INTERROMPIDO";return false;}
 if(!MDConnected210()){reason="DESCONECTADO_APOS_COLETA";return false;}
 if(!MDSparseFinish615N(candidate,observation_only)){reason="BLOCO_NAO_CONCLUIDO";return false;}
 state=candidate;reason="BLOCO_OBSERVADO;minutos_com_registros="+IntegerToString(bars)+";minutos_sem_registros="+IntegerToString(empty)+";ausentes_msc="+absent+";INTEGRIDADE_TOTAL_NAO_CERTIFICADA";return true;
}
#endif
