#ifndef MD_REFERENCE_CORTE212_HEADER
#define MD_REFERENCE_CORTE212_HEADER
#include "../../Include/ModeloD_Corte212/Cenario.mqh"
long md_reference_hits211=0,md_reference_minute211=0;
bool MDReferenceMinute211(long minute,const MqlTick &ticks[],int size)
{
 if(!MDFonteAtiva211()||minute%60000!=0||minute+60000>(long)TimeCurrent()*1000)return false;
 long from=minute;if(from<MD_CORTE212_BEGIN)from=MD_CORTE212_BEGIN;
 long end=minute+59999;if(end>MD_CORTE212_END)end=MD_CORTE212_END;
 if(from>end||from%1000!=0)return false;
 int count=0,expected=(int)((end-from)/1000+1);
 for(int i=0;i<size;i++){
  if(ticks[i].time_msc<minute||ticks[i].time_msc>=minute+60000||(ticks[i].flags&120)==0)continue;
  int index=(int)((from-MD_CORTE212_BEGIN)/1000)+count;
  if(count>=expected||!MDCorteTickSame212(ticks[i],index))return false;
  count++;
 }
 if(count!=expected)return false;
 md_reference_hits211++;md_reference_minute211=minute;return true;
}
#endif
