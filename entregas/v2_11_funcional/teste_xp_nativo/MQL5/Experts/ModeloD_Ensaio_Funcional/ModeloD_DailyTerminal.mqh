#ifndef MD_DAILY_TERMINAL614
#define MD_DAILY_TERMINAL614
#include "ModeloD_DailyAdapter.mqh"
#include "ModeloD_B3File.mqh"
#include "ModeloD_OpeningTicks.mqh"
int MDDateValue614(datetime time)
{MqlDateTime x;if(!TimeToStruct(time,x))return 0;return x.year*10000+x.mon*100+x.day;}
bool MDCollectDaily614(int date,MDDailyRaw614 &r,string &reason)
{
 r.connected=(bool)TerminalInfoInteger(TERMINAL_CONNECTED);r.synchronized=false;r.history_read_ok=false;r.opening_read_ok=false;
 r.date=date;r.chart_symbol="WIN$N";r.available_bars=0;r.first_msc=0;r.first_last=0;
 if(!r.connected)return MDB3Fail(reason,"DESCONECTADO");
 if(!MDSymbolInfoString211("WIN$N",SYMBOL_DESCRIPTION,r.description))return MDB3Fail(reason,"DESCRICAO_INDISPONIVEL");
 string contract;if(!MDContractCandidate(r.chart_symbol,r.description,contract,reason))return false;
 if(!MDSymbolSelect211(contract,true))return MDB3Fail(reason,"CONTRATO_INDISPONIVEL");
 long expiry=0;if(!MDSymbolInfoInteger211(contract,SYMBOL_EXPIRATION_TIME,expiry)||!MDSymbolInfoDouble211(contract,SYMBOL_TRADE_TICK_SIZE,r.tick_size))return MDB3Fail(reason,"PROPRIEDADES_INDISPONIVEIS");
 r.expiry=MDDateValue614((datetime)expiry);
 MDSessionRule rule;if(!MDSession614(date,contract,rule))return MDB3Fail(reason,"SESSAO_NAO_REVISADA");
 int prior=MDPreviousSession2026(date);datetime prior_start=(datetime)(MDCivilMidnight2026(prior)/1000),day_start=(datetime)(MDCivilMidnight2026(date)/1000);
 long opening_begin=((long)day_start+rule.scheduled_open)*1000;
 long opening_end=((long)day_start+rule.cutoff)*1000;
 if(!MDOpeningRead208(contract,opening_begin,opening_end,(long)TimeTradeServer()*1000,r.first_msc,r.first_last,reason))return false;
 r.opening_read_ok=true;
 MqlRates recent[],previous[],today[];ResetLastError();int n=MDCopyRates211(contract,PERIOD_D1,0,3,recent);
 if(n<3||GetLastError()!=0)return MDB3Fail(reason,"HISTORICO_AINDA_INDISPONIVEL");r.available_bars=n;
 ResetLastError();n=MDCopyRates211(contract,PERIOD_D1,prior_start,prior_start+86399,previous);
 if(n!=1||GetLastError()!=0)return MDB3Fail(reason,"D1_ANTERIOR_INDISPONIVEL");
 r.previous_date=MDDateValue614(previous[0].time);r.o=previous[0].open;r.h=previous[0].high;r.l=previous[0].low;r.c=previous[0].close;
 r.previous_tick_volume=previous[0].tick_volume;r.previous_real_volume=previous[0].real_volume;
 ResetLastError();n=MDCopyRates211(contract,PERIOD_D1,day_start,day_start+86399,today);
 if(n!=1||GetLastError()!=0||MDDateValue614(today[0].time)!=date)return MDB3Fail(reason,"D1_DA_SESSAO_INDISPONIVEL");
 r.day_open=today[0].open;long sync=0;
 if(!MDSeriesInfoInteger211(contract,PERIOD_D1,SERIES_SYNCHRONIZED,sync))return MDB3Fail(reason,"ESTADO_SERIE_INDISPONIVEL");
 r.synchronized=sync!=0;r.history_read_ok=true;
 if(!MDB3ReadOperational(r.b3,reason))return false;
 string again;if(!MDSymbolInfoString211("WIN$N",SYMBOL_DESCRIPTION,again)||again!=r.description)return MDB3Fail(reason,"DESCRICAO_MUDOU_DURANTE_COLETA");
 reason="COLETA_DIARIA_CONCLUIDA";return true;
}
#endif
