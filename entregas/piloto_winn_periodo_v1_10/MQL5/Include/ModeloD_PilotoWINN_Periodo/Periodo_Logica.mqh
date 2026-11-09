#ifndef PM_LOGIC_110
#define PM_LOGIC_110
#include "Periodo_Referencias.mqh"
int PMSlotDay(const int slot){return slot/5;}
int PMSlotLevel(const int slot){return slot%5;}
bool PMValidSlot(const int slot){return slot>=0&&slot<PM_SLOTS;}
int PMFindDay(const long stamp)
{
 for(int d=0;d<PM_DAYS;d++)if(stamp>=(long)pm_ref[d].begin*1000&&stamp<(long)pm_ref[d].end*1000)return d;
 return -1;
}
bool PMExitCrossed(const MDLevel &l,const double previous,const double last)
{
 return l.buy ? (last<=l.sl || last>=l.tp || MDCrossed(previous,last,l.sl) || MDCrossed(previous,last,l.tp))
              : (last>=l.sl || last<=l.tp || MDCrossed(previous,last,l.sl) || MDCrossed(previous,last,l.tp));
}
bool PMVolumeOne(const double minimum,const double maximum,const double step)
{
 if(!MDPositive(minimum)||!MDPositive(maximum)||!MDPositive(step)||minimum>1||maximum<1)return false;
 double units=(1.0-minimum)/step;return MathAbs(units-MathRound(units))<1e-8;
}
bool PMClosedPoints(const bool buy,const double entered,const double exited,const double entry_value,const double exit_value,double &points)
{
 points=0;if(entered<=0||MathAbs(entered-exited)>1e-8)return false;
 points=(buy?1.0:-1.0)*(exit_value-entry_value)/entered;return MathIsValidNumber(points);
}
#endif
