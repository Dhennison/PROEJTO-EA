#ifndef MODELO_D_CORE_MQH
#define MODELO_D_CORE_MQH
// Etapa 6.1: nucleo puro. Sem acesso a corretora e sem envio de ordens.
// Mesma fonte exercitada pelo harness C++ e pelo script MQL5.
enum MDLevelId { MD_S382=0, MD_S50=1, MD_S618=2, MD_R382=3, MD_R618=4 };
struct MDInputs
{
   double high_prev, low_prev, close_prev, open_today, adjustment;
};
struct MDLevel
{
   int id;
   bool buy, valid_open, geometry_blocked;
   double entry, sl, tp;                 // matematicos, imutaveis
   double entry_tick, sl_tick, tp_tick;  // normalizados individualmente
};
struct MDDay
{
   double pp, r200, s200, adjustment;
   bool block_buy, block_sell;
   double r236, r382, r50, r618, s236, s382, s50, s618;
   MDLevel levels[5];
};
bool MDPositive(const double x) { return MathIsValidNumber(x) && x>0.0; }
double MDRound5(const double x) { return 5.0*MathFloor(x/5.0+0.5); }
bool MDOpenValid(const bool buy,const double open_price,const double line)
{
   return buy ? open_price>=line : open_price<=line;
}
void MDSetLevel(MDLevel &l,const int id,const bool buy,const double entry,
                const double distance,const double tp,const double open_price,const bool geometry_blocked)
{
   l.id=id; l.buy=buy; l.entry=entry; l.geometry_blocked=geometry_blocked;
   l.sl=buy ? entry-distance : entry+distance; l.tp=tp;
   l.valid_open=MDOpenValid(buy,open_price,entry);
   l.entry_tick=MDRound5(entry); l.sl_tick=MDRound5(l.sl); l.tp_tick=MDRound5(tp);
}
bool MDCalculate(const MDInputs &v,MDDay &d)
{
   // Validade numerica nao comprova completude/proveniencia da sessao.
   if(!MDPositive(v.high_prev)||!MDPositive(v.low_prev)||
      !MDPositive(v.close_prev)||!MDPositive(v.open_today)||!MDPositive(v.adjustment)) return false;
   if(v.high_prev<v.low_prev||v.close_prev<v.low_prev||v.close_prev>v.high_prev) return false;
   d.pp=(v.high_prev+v.low_prev+v.close_prev)/3.0;
   d.r200=v.open_today+2.0*MathAbs(v.low_prev-d.pp);
   d.s200=v.open_today-2.0*MathAbs(v.high_prev-d.pp);
   // Regra aprovada em 15/10: avaliar ANTES de qualquer normalizacao.
   d.adjustment=v.adjustment;
   d.block_sell=(v.adjustment>=d.r200);
   d.block_buy=(v.adjustment<=d.s200);
   d.r236=v.adjustment+(d.r200-v.adjustment)*0.236;
   d.r382=v.adjustment+(d.r200-v.adjustment)*0.382;
   d.r50=v.adjustment+(d.r200-v.adjustment)*0.500;
   d.r618=v.adjustment+(d.r200-v.adjustment)*0.618;
   d.s236=v.adjustment+(d.s200-v.adjustment)*0.236;
   d.s382=v.adjustment+(d.s200-v.adjustment)*0.382;
   d.s50=v.adjustment+(d.s200-v.adjustment)*0.500;
   d.s618=v.adjustment+(d.s200-v.adjustment)*0.618;
   MDSetLevel(d.levels[0],MD_S382,true,d.s382,375.0,(d.s382+d.s236)/2.0,v.open_today,d.block_buy);
   MDSetLevel(d.levels[1],MD_S50,true,d.s50,375.0,d.s382,v.open_today,d.block_buy);
   MDSetLevel(d.levels[2],MD_S618,true,d.s618,650.0,d.s50,v.open_today,d.block_buy);
   MDSetLevel(d.levels[3],MD_R382,false,d.r382,375.0,d.r236,v.open_today,d.block_sell);
   MDSetLevel(d.levels[4],MD_R618,false,d.r618,450.0,(d.r618+d.r50)/2.0,v.open_today,d.block_sell);
   return true;
}
// Inclusivo e sem arredondamento. Inclui gap em qualquer sentido.
bool MDCrossed(const double previous,const double current,const double line)
{
   return (previous<=line && current>=line)||(previous>=line && current<=line);
}
struct MDTap
{
   bool initialized, touched, complete;
   double previous;
   long first_msc, last_msc;
};
void MDStartTape(MDTap &t,const double open_price,const double line,const long open_msc)
{
   t.initialized=true; t.complete=true; t.previous=open_price;
   t.touched=(open_price==line); t.first_msc=t.touched ? open_msc : -1;
   t.last_msc=open_msc;
}
bool MDObserve(MDTap &t,const double last,const double line,const long time_msc)
{
   if(!t.initialized||!MDPositive(last)||time_msc<t.last_msc)
   { t.complete=false; return false; }
   // Ticks distintos no mesmo milissegundo sao processados em ordem de origem.
   bool fresh=!t.touched && MDCrossed(t.previous,last,line);
   if(fresh) { t.touched=true; t.first_msc=time_msc; }
   t.previous=last; t.last_msc=time_msc; return fresh;
}
bool MDAcceptedBeforeTouch(const MDTap &t,const long accepted_msc)
{
   // Timestamp igual nao demonstra precedencia. Adaptador devera reconciliar.
   return t.complete && accepted_msc>=0 && (!t.touched||accepted_msc<t.first_msc);
}
struct MDOpportunity
{
   bool invalidated, consumed, blocked, request_inflight, accepted;
};
void MDResetOpportunity(MDOpportunity &o,const bool valid_open)
{
   o.invalidated=!valid_open; o.consumed=false; o.blocked=false;
   o.request_inflight=false; o.accepted=false;
}
bool MDCanSubmit(const MDLevel &level,const MDOpportunity &o,const MDTap &t,const bool gates_ok,const bool before_cutoff)
{
   return !level.geometry_blocked && level.valid_open && gates_ok && before_cutoff && t.initialized && t.complete && !t.touched &&
      !o.invalidated && !o.consumed && !o.blocked && !o.request_inflight && !o.accepted;
}
string MDGeometryReason(const MDLevel &level)
{
   if(!level.geometry_blocked) return "SEM_BLOQUEIO_GEOMETRICO";
   return level.buy ? "BLOQUEIO_GEOMETRICO_S_AJUSTE_LE_S200" : "BLOQUEIO_GEOMETRICO_R_AJUSTE_GE_R200";
}
void MDLogGeometry(const MDDay &day,const string operational_date,const string contract)
{
   // Chamar apos validar dados reais/calcular o dia e apos reconciliar reinicio.
   // Nao converter preços para grade antes de registrar comparacoes.
   Print("GEOMETRIA;data=",operational_date,";contrato=",contract,
         ";ajuste=",day.adjustment,";R200=",day.r200,";S200=",day.s200,
         ";ajuste_GE_R200=",day.block_sell,";ajuste_LE_S200=",day.block_buy);
   for(int i=0;i<5;i++)
      Print("GEOMETRIA_NIVEL;data=",operational_date,";contrato=",contract,
            ";nivel_id=",i,";compra=",day.levels[i].buy,
            ";motivo=",MDGeometryReason(day.levels[i]),
            ";abertura_valida=",day.levels[i].valid_open);
}
// Somente o reconciliador futuro podera confirmar ausencia de ordem no servidor.
void MDConsume(MDOpportunity &o) { o.consumed=true; }
#endif
