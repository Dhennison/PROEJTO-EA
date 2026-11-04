#ifndef MD_DAILY614
#define MD_DAILY614
#include "ModeloD_DayControl.mqh"
#include "ModeloD_Contract.mqh"
struct MDDailyRaw614
{
 int date,previous_date,expiry;string chart_symbol,description;
 bool synchronized,history_read_ok,opening_read_ok,connected;
 int available_bars;long previous_tick_volume,previous_real_volume,first_msc;
 double o,h,l,c,day_open,first_last,tick_size;
 MDB3File b3;
};
bool MDSession614(int date,string contract,MDSessionRule &rule)
{
 if(MDObservedSessionRule(date,contract,rule))return true;
 // Grade WIN consultada em 18/10/2026. Janela curta revisada; nao extrapolar
 // para vencimento ou mudancas de grade anunciadas para fim de outubro.
 if(date>=20261019&&date<=20261023&&contract=="WINZ26")
 return MDSessionSet(date,32400,66300,64800,true,"B3_INDICES_CONSULTA_20261018_JANELA_19_A_23",rule);
 // Grade normal WIN 09:00-18:25 consultada na B3 em 26/10/2026.
 // Cutoff do Modelo D preservado em 18:00; janela revisada de 26 a 30.
 if(date>=20261026&&date<=20261030&&contract=="WINZ26")
 return MDSessionSet(date,32400,66300,64800,true,"B3_INDICES_CONSULTA_20261026_JANELA_26_A_30",rule);
 MDSessionClear(rule);return false;
}
int MDISODate614(string text)
{if(!MDB3Date(text))return 0;return (int)StringToInteger(StringSubstr(text,0,4))*10000+(int)StringToInteger(StringSubstr(text,5,2))*100+(int)StringToInteger(StringSubstr(text,8,2));}
string MDISO614(int date)
{
 int m=(date/100)%100,d=date%100;
 return IntegerToString(date/10000)+"-"+(m<10?"0":"")+IntegerToString(m)+"-"+(d<10?"0":"")+IntegerToString(d);
}
bool MDDailyBuild614(const MDDailyRaw614 &raw,MDDataEvidence &out,string &reason)
{
 out.ohlc_verified=false;out.opening_verified=false;out.adjustment_verified=false;
 reason="";string contract;
 if(!raw.connected)return MDB3Fail(reason,"SEM_CONEXAO");
 if(!MDContractCandidate(raw.chart_symbol,raw.description,contract,reason))return false;
 if(MDCalendar2026(raw.date)!=1)return MDB3Fail(reason,"SEM_PREGAO_OU_ANO_NAO_CADASTRADO");
 if(!MDWINExpiryCheck2026(contract,raw.date,raw.expiry,reason))return false;
 if(!MDSession614(raw.date,contract,out.session))return MDB3Fail(reason,"GRADE_DA_SESSAO_NAO_REVISADA");
 int prior=MDPreviousSession2026(raw.date);
 if(raw.previous_date!=prior||prior==0||MDOrdinal2026(raw.date)-MDOrdinal2026(prior)>5)return MDB3Fail(reason,"DATA_OHLC_ANTERIOR_INVALIDA");
 if(!raw.synchronized||!raw.history_read_ok||raw.available_bars<3||raw.previous_tick_volume<=0||raw.previous_real_volume<=0)
 return MDB3Fail(reason,"HISTORICO_OHLC_INSUFICIENTE");
 if(!MDPositive(raw.o)||!MDPositive(raw.h)||!MDPositive(raw.l)||!MDPositive(raw.c)||raw.h<raw.l||
 raw.o<raw.l||raw.o>raw.h||raw.c<raw.l||raw.c>raw.h)return MDB3Fail(reason,"OHLC_INCONSISTENTE");
 long midnight=MDCivilMidnight2026(raw.date);
 if(!raw.opening_read_ok||!MDPositive(raw.first_last)||raw.first_last!=raw.day_open||
 raw.first_msc<midnight+(long)out.session.scheduled_open*1000||raw.first_msc>=midnight+(long)out.session.cutoff*1000)
 return MDB3Fail(reason,"ABERTURA_NAO_CONFIRMADA");
 if(raw.tick_size!=5)return MDB3Fail(reason,"GRADE_PRECO_DIVERGENTE");
 double adjustment,previous;
 if(!MDB3Select(raw.b3,MDISO614(raw.date),contract,adjustment,previous,reason))return false;
 if(MDISODate614(raw.b3.source_date)!=prior)return MDB3Fail(reason,"DATA_FONTE_AJUSTE_DIVERGENTE");
 out.date=raw.date;out.previous_date=prior;out.adjustment_date=raw.date;out.source_date=prior;out.expiry_date=raw.expiry;
 out.contract=contract;out.ohlc_contract=contract;out.opening_contract=contract;out.adjustment_contract=contract;out.source=raw.b3.source;
 out.ohlc_verified=true;out.opening_verified=true;out.adjustment_verified=true;
 out.previous_adjustment=previous;out.tick_size=raw.tick_size;out.open_msc=raw.first_msc;
 out.values.high_prev=raw.h;out.values.low_prev=raw.l;out.values.close_prev=raw.c;out.values.open_today=raw.first_last;out.values.adjustment=adjustment;
 if(!MDDataValid(out)){out.ohlc_verified=false;out.opening_verified=false;out.adjustment_verified=false;return MDB3Fail(reason,"EVIDENCIA_DIARIA_REJEITADA");}
 reason="DADOS_DIARIOS_CONFERIDOS_AINDA_EXIGE_HISTORICO_TOQUES_E_RECONCILIACAO";return true;
}
#endif
