#ifndef MDPW_LOGIC
#define MDPW_LOGIC
#include "ModeloD_Core.mqh"
// Este piloto e fixo em um dia. Nao resolve calendario/ajuste de outros dias.
bool PWExpectedDay(const long stamp){return stamp>=1789948800000 && stamp<1790035200000;}
bool PWExitCrossed(const MDLevel &l,const double previous,const double last)
{
 return l.buy ? (last<=l.sl || last>=l.tp || MDCrossed(previous,last,l.sl) || MDCrossed(previous,last,l.tp))
              : (last>=l.sl || last<=l.tp || MDCrossed(previous,last,l.sl) || MDCrossed(previous,last,l.tp));
}
bool PWVolumeOne(const double minimum,const double maximum,const double step)
{
 if(!MDPositive(minimum)||!MDPositive(maximum)||!MDPositive(step)||minimum>1 || maximum<1)return false;
 double units=(1.0-minimum)/step;
 return MathAbs(units-MathRound(units))<1e-8;
}
// Ponderado por volume; so e resultado encerrado com entrada e saida iguais.
bool PWClosedPoints(const bool buy,const double entered,const double exited,const double entry_value,const double exit_value,double &points)
{
 points=0;if(entered<=0 || MathAbs(entered-exited)>1e-8)return false;
 points=(buy?1.0:-1.0)*(exit_value-entry_value)/entered;return MathIsValidNumber(points);
}
#endif
