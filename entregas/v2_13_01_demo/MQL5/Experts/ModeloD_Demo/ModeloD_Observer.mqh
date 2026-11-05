#ifndef MD_OBSERVER615
#define MD_OBSERVER615
#include "ModeloD_DailyAdapter.mqh"
#include "ModeloD_Visual.mqh"
#include "ModeloD_Context.mqh"
// Supervisor de observacao. Nenhum metodo concede permissao para negociar.
struct MDObserver615
{
 bool frozen,conflict,identity_changed,visible;
 int date;
 string scope,reason;
 MDDataEvidence data;
 MDDayControl control;
};
void MDObserverStart615(MDObserver615 &s,string scope)
{
 s.frozen=false;s.conflict=false;s.identity_changed=false;s.visible=false;s.date=0;
 s.scope=scope;s.reason="AGUARDANDO_DADOS";
}
bool MDObserverIdentity615(MDObserver615 &s,string current)
{
 if(current==""||s.scope==""||s.scope!=current)s.identity_changed=true;
 if(s.identity_changed){s.visible=false;s.reason="IDENTIDADE_MUDOU_REANEXAR";return false;}
 return true;
}
bool MDObserverUpdate615(MDObserver615 &s,int date,bool collected,const MDDailyRaw614 &raw,string failure)
{
 s.visible=false;
 if(s.identity_changed){s.reason="IDENTIDADE_MUDOU_REANEXAR";return false;}
 if(date!=s.date)
 {
  if(s.date>0&&date<s.date){s.conflict=true;s.reason="DATA_REGREDIU_REANEXAR";return false;}
  s.date=date;s.frozen=false;s.conflict=false;
 }
 if(s.conflict){s.reason="DADOS_MUDARAM_REANEXAR";return false;}
 if(!collected){s.reason=failure;return false;}
 MDDataEvidence next;string why;
 if(raw.date!=date){s.reason="DATA_COLETA_DIVERGENTE";return false;}
 if(!MDDailyBuild614(raw,next,why)){s.reason=why;return false;}
 if(s.frozen&&!MDDaySameData(s.data,next))
 {s.conflict=true;s.reason="DADOS_MUDARAM_REANEXAR";return false;}
 if(!s.frozen)
 {
  if(!MDDayStart(s.control,next)){s.reason="CONTROLADOR_REJEITOU_DADOS";return false;}
  s.data=next;s.frozen=true;
 }
 // Nao chamar MDDayObserve com apenas o ultimo tick: isso perderia historico.
 s.visible=true;s.reason="VISUAL_VALIDADO_SEM_ORDENS";return true;
}
void MDObserverFixture615(MDDailyRaw614 &r)
{
 r.date=20261016;r.previous_date=20261015;r.expiry=20261216;r.chart_symbol="WIN$N";
 r.description="IBOVESPA MINI - Por Liquidez(WINZ26) - Sem Ajustes";
 r.synchronized=true;r.history_read_ok=true;r.opening_read_ok=true;r.connected=true;
 r.available_bars=3;r.previous_tick_volume=100;r.previous_real_volume=100;r.first_msc=1792141255927;
 r.o=208000;r.h=210800;r.l=207235;r.c=208495;r.day_open=209500;r.first_last=209500;r.tick_size=5;
 string reason;
 MDB3Parse("DataFonte=2026-10-15\nDataOperacional=2026-10-16\nFonte=BVBG.187.01\nStatus=OK\nQuantidadeContratos=1\nContrato.WINZ26.Ajuste=208485\nContrato.WINZ26.AjusteAnterior=210905\n",r.b3,reason);
}
#endif
