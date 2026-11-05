#ifndef MD_OPENING_TICKS208
#define MD_OPENING_TICKS208
// Volatile acquisition state only. Never writes the ledger or stream cursor.
struct MDOpening208 {
 string symbol;long begin,end,cursor,next_due,first_msc;double first_last;
 int failures,attempts;bool confirmed;
};
MDOpening208 opening208;
bool MDOpeningRead208(string symbol,long begin,long end,long now,long &first_msc,double &first_last,string &why,
 long logical_mono=-1,bool partial_window=false)
{
 if(IsStopped()){why="PRIMEIRO_TICK_INTERROMPIDO;parando=1";return false;}
 if(opening208.symbol!=symbol||opening208.begin!=begin||opening208.end!=end){
  opening208.symbol=symbol;opening208.begin=begin;opening208.end=end;opening208.cursor=begin;
  opening208.next_due=0;opening208.first_msc=0;opening208.first_last=0;
  opening208.failures=0;opening208.attempts=0;opening208.confirmed=false;
 }
 if(opening208.confirmed){first_msc=opening208.first_msc;first_last=opening208.first_last;why="PRIMEIRO_TICK_CONFIRMADO";return true;}
 long wall_begin=(long)GetTickCount64();long mono=logical_mono<0?wall_begin:logical_mono;
 string progress=";cursor_msc="+IntegerToString(opening208.cursor)+";tentativas="+IntegerToString(opening208.attempts);
 if(mono<opening208.next_due){why="PRIMEIRO_TICK_BACKOFF"+progress+";restante_ms="+IntegerToString(opening208.next_due-mono);return false;}
 if(begin<=0||end<=begin||opening208.cursor>=end){why="PRIMEIRO_TICK_SESSAO_SEM_NEGOCIOS"+progress;return false;}
 long until=opening208.cursor+59999;if(until>=end)until=end-1;
 // Do not certify an empty window that has not ended yet.
 bool complete=now>until;
 if(!complete){
  if(!partial_window||now<=opening208.cursor){why="PRIMEIRO_TICK_AGUARDA_JANELA_COMPLETA"+progress;return false;}
  until=now-1; // Positive, exact tick evidence only; NEVER skip an unfinished empty window.
 }
 Print("PRIMEIRO_TICK_CONSULTA;de_msc="+IntegerToString(opening208.cursor)+";ate_msc="+IntegerToString(until)+";tentativa="+IntegerToString(opening208.attempts+1)+(partial_window?";DEMO_CORRETORA_JANELA_PARCIAL":";JANELA_COMPLETA"));
 MqlTick ticks[];ResetLastError();opening208.attempts++;
 int n=MDCopyTicksRange213(symbol,ticks,COPY_TICKS_TRADE,(ulong)opening208.cursor,(ulong)until);
 int error=GetLastError();long finished=logical_mono<0?(long)GetTickCount64():logical_mono;
 if(IsStopped()){why="PRIMEIRO_TICK_INTERROMPIDO;parando=1;erro="+IntegerToString(error);return false;}
 if(n<0||error!=0){
  opening208.failures++;int delay=2000;
  for(int i=1;i<opening208.failures&&delay<30000;i++)delay*=2;
  if(delay>30000)delay=30000;
  opening208.next_due=finished+delay;
  why="PRIMEIRO_TICK_INDISPONIVEL;retornados="+IntegerToString(n)+";erro="+IntegerToString(error)+
   ";parando=0;de_msc="+IntegerToString(opening208.cursor)+";ate_msc="+IntegerToString(until)+
   ";tentativa="+IntegerToString(opening208.attempts)+";duracao_ms="+IntegerToString((long)GetTickCount64()-wall_begin)+";backoff_ms="+IntegerToString(delay);
  return false;
 }
 opening208.failures=0;opening208.next_due=finished+2000;
 if(n==0){
  if(!complete){why="PRIMEIRO_TICK_AGUARDA_NEGOCIO_NA_JANELA_PARCIAL"+progress;return false;}
  opening208.cursor=until+1;why="PRIMEIRO_TICK_JANELA_VAZIA_CONFIRMADA;ate_msc="+IntegerToString(until);return false;
 }
 // Reject malformed results; never use M1 or a partial timeout as opening proof.
 if(n!=ArraySize(ticks)||ticks[0].time_msc<opening208.cursor||ticks[0].time_msc>until||
    !MathIsValidNumber(ticks[0].last)||ticks[0].last<=0||
    (ticks[0].flags&(TICK_FLAG_LAST|TICK_FLAG_VOLUME|TICK_FLAG_BUY|TICK_FLAG_SELL))==0){
  why="PRIMEIRO_TICK_RETORNO_INVALIDO";return false;
 }
 opening208.first_msc=ticks[0].time_msc;opening208.first_last=ticks[0].last;opening208.confirmed=true;
 first_msc=opening208.first_msc;first_last=opening208.first_last;why="PRIMEIRO_TICK_CONFIRMADO";return true;
}
#endif
