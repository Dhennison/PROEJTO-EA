#ifndef MD_TICK_AUDIT
#define MD_TICK_AUDIT
#include "ModeloD_Core.mqh"
// Agregacao pura da janela explicita [begin_msc,end_msc]. Sem negociacao.
struct MDMinuteAudit { long count; double o,h,l,c; };
struct MDTouchAudit
{
   MDTap tape;
   double previous_at_touch,last_at_touch;
   long index_at_touch;
};
struct MDTickAudit
{
   long begin_msc,end_msc,count,first_msc,last_msc,max_gap_msc;
   double first_price,last_price;
   bool valid;
   MDDay day;
   MDTouchAudit touches[5];
   MDMinuteAudit minutes[540];
};
void MDAuditStart(MDTickAudit &a,const MDDay &day,const long begin_msc,const long end_msc)
{
   a.day=day;a.begin_msc=begin_msc;a.end_msc=end_msc;a.count=0;
   a.first_msc=-1;a.last_msc=-1;a.max_gap_msc=0;a.first_price=0;a.last_price=0;
   a.valid=begin_msc>=0 && end_msc>=begin_msc && end_msc-begin_msc<540*60000;
   for(int i=0;i<540;i++){a.minutes[i].count=0;a.minutes[i].o=0;a.minutes[i].h=0;a.minutes[i].l=0;a.minutes[i].c=0;}
   for(int i=0;i<5;i++)
   {
      a.touches[i].tape.initialized=false;a.touches[i].tape.touched=false;
      a.touches[i].tape.complete=false;a.touches[i].tape.previous=0;
      a.touches[i].tape.first_msc=-1;a.touches[i].tape.last_msc=-1;
      a.touches[i].previous_at_touch=0;a.touches[i].last_at_touch=0;a.touches[i].index_at_touch=-1;
   }
}
bool MDAuditPush(MDTickAudit &a,const long msc,const double last)
{
   if(!a.valid || !MDPositive(last) || msc<a.begin_msc || msc>a.end_msc || (a.count>0 && msc<a.last_msc))
   {a.valid=false;return false;}
   int minute=(int)((msc-a.begin_msc)/60000);
   if(a.count==0){a.first_msc=msc;a.first_price=last;}
   else if(msc-a.last_msc>a.max_gap_msc)a.max_gap_msc=msc-a.last_msc;
   for(int i=0;i<5;i++)
   {
      bool fresh=false;
      double previous=a.count==0?last:a.last_price;
      if(a.count==0)
      {MDStartTape(a.touches[i].tape,last,a.day.levels[i].entry,msc);fresh=a.touches[i].tape.touched;}
      else fresh=MDObserve(a.touches[i].tape,last,a.day.levels[i].entry,msc);
      if(fresh)
      {a.touches[i].previous_at_touch=previous;a.touches[i].last_at_touch=last;a.touches[i].index_at_touch=a.count;}
   }
   if(a.minutes[minute].count==0)
   {a.minutes[minute].o=last;a.minutes[minute].h=last;a.minutes[minute].l=last;}
   else
   {if(last>a.minutes[minute].h)a.minutes[minute].h=last;if(last<a.minutes[minute].l)a.minutes[minute].l=last;}
   a.minutes[minute].c=last;a.minutes[minute].count++;
   a.count++;a.last_msc=msc;a.last_price=last;return true;
}
// Igualdade de OHLC e evidencia de consistencia, nao prova ausencia de ticks omitidos.
bool MDAuditMinuteMatches(const MDMinuteAudit &m,const double o,const double h,const double l,const double c)
{return m.count>0 && MathAbs(m.o-o)<0.0000001 && MathAbs(m.h-h)<0.0000001 && MathAbs(m.l-l)<0.0000001 && MathAbs(m.c-c)<0.0000001;}
#endif
