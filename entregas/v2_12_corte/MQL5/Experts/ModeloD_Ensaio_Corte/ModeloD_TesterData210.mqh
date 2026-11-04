#ifndef MD_TESTER_DATA210
#define MD_TESTER_DATA210
#include "ModeloD_B3File.mqh"
#include "ModeloD_OpeningTicks.mqh"
// Fixed reviewed smoke-test dataset. Files are transferred to the agent sandbox.
string MDTesterB3Path210(){return "ModeloD_Tester_20261030_ajuste_b3.txt";}
MDB3File tester_b3_210;
bool MDTesterValidate210(string &why)
{
 if(!MDIsTester210()){why="TESTER_ONLY";return false;}
 if(!ExecutarNoTester||MQLInfoInteger(MQL_OPTIMIZATION)){why="TESTER_OPTIN_REQUIRED_NO_OPTIMIZATION";return false;}
 if(DataTester!=20261030||ContratoTester!="WINZ26"||!MDGraficoValido211()||FusoServidorTester!=-10800)
 {why="TESTER_210_REQUIRES_WINZ26_20261030_BRT";return false;}
 if(UsarCenarioSinteticoNoTester&&!MDValidarFonte211(why))return false;
 if(AccountInfoInteger(ACCOUNT_MARGIN_MODE)!=ACCOUNT_MARGIN_MODE_RETAIL_HEDGING)
 {why="TESTER_REQUIRES_HEDGING";return false;}
 if(!MDSymbolSelect211(ContratoTester,true)){why="TESTER_CONTRACT_UNAVAILABLE";return false;}
 if(!MDB3ReadAt210(MDTesterB3Path210(),false,tester_b3_210,why))return false;
 double adjustment=0,previous=0;
 if(!MDB3Select(tester_b3_210,MDISO614(DataTester),ContratoTester,adjustment,previous,why))return false;
 if(MDISODate614(tester_b3_210.source_date)!=MDPreviousSession2026(DataTester))
 {why="TESTER_B3_SOURCE_DATE_MISMATCH";return false;}
 MDSessionRule session;if(!MDSession614(DataTester,ContratoTester,session)){why="TESTER_SESSION_UNREVIEWED";return false;}
 why="TESTER_DATASET_PINNED_STILL_REQUIRES_NATIVE_HISTORY";return true;
}
bool MDTesterReadDaily210(int date,MDDailyRaw614 &r,string &why)
{
 if(!MDTesterGate210()||date!=DataTester){why="TESTER_OUTSIDE_PINNED_DAY";return false;}
 r.connected=true;r.synchronized=false;r.history_read_ok=false;r.opening_read_ok=false;
 r.date=date;r.chart_symbol="WIN$N";r.description="TESTER_CONTRATO_EXPLICITO("+ContratoTester+")";
 r.available_bars=0;r.first_msc=0;r.first_last=0;r.b3=tester_b3_210;
 long expiry=0;
 if(!MDSymbolInfoInteger211(ContratoTester,SYMBOL_EXPIRATION_TIME,expiry)||
    !MDSymbolInfoDouble211(ContratoTester,SYMBOL_TRADE_TICK_SIZE,r.tick_size))
 {why="TESTER_SYMBOL_PROPERTIES_UNAVAILABLE";return false;}
 r.expiry=MDDateValue614((datetime)expiry);
 MDSessionRule session;if(!MDSession614(date,ContratoTester,session)){why="TESTER_SESSION_UNREVIEWED";return false;}
 int prior=MDPreviousSession2026(date);
 long midnight=MDCivilMidnight2026(date),begin=midnight+(long)session.scheduled_open*1000;
 long end=midnight+(long)session.cutoff*1000,now=(long)TimeCurrent()*1000;
 if(!MDOpeningRead208(ContratoTester,begin,end,now,r.first_msc,r.first_last,why,MDLogicalMillis210(),true))return false;
 r.opening_read_ok=true;
 MqlRates recent[];MqlRates previous[];MqlRates today[];ResetLastError();
 int n=MDCopyRates211(ContratoTester,PERIOD_D1,0,3,recent);
 if(n<3||GetLastError()!=0){why="TESTER_D1_HISTORY_INSUFFICIENT";return false;}r.available_bars=n;
 datetime prior_start=(datetime)(MDCivilMidnight2026(prior)/1000),day_start=(datetime)(midnight/1000);
 ResetLastError();n=MDCopyRates211(ContratoTester,PERIOD_D1,prior_start,prior_start+86399,previous);
 if(n!=1||GetLastError()!=0){why="TESTER_PREVIOUS_D1_UNAVAILABLE";return false;}
 r.previous_date=MDDateValue614(previous[0].time);r.o=previous[0].open;r.h=previous[0].high;r.l=previous[0].low;r.c=previous[0].close;
 r.previous_tick_volume=previous[0].tick_volume;r.previous_real_volume=previous[0].real_volume;
 ResetLastError();n=MDCopyRates211(ContratoTester,PERIOD_D1,day_start,day_start+86399,today);
 if(n!=1||GetLastError()!=0){why="TESTER_CURRENT_D1_UNAVAILABLE";return false;}
 r.day_open=today[0].open; // Never consume today's H/L/C to make an entry decision.
 long sync=0;if(!MDSeriesInfoInteger211(ContratoTester,PERIOD_D1,SERIES_SYNCHRONIZED,sync)||sync==0)
 {why="TESTER_HISTORY_NOT_SYNCHRONIZED";return false;}
 r.synchronized=true;r.history_read_ok=true;why="TESTER_RAW_DAILY_READY";return true;
}
#endif
