#ifndef MD_STREAM615
#define MD_STREAM615
#include "ModeloD_TickAudit.mqh"
#include "ModeloD_DayControl.mqh"
// Estado observacional. Nao libera ordens e nao substitui diario operacional.
struct MDStream615
{
 bool ready;long cursor,cutoff,block_end;int blocks;
 MDDataEvidence data;
 MDTickAudit audit;
 MDDayControl control;
};
bool MDStreamStart615(MDStream615 &s,const MDDataEvidence &data)
{
 s.ready=false;s.blocks=0;s.block_end=-1;
 if(!MDDayStart(s.control,data))return false;
 s.data=data;s.cursor=MDCivilMidnight2026(data.date)+(long)data.session.scheduled_open*1000;
 s.cutoff=MDCivilMidnight2026(data.date)+(long)data.session.cutoff*1000;
 MDAuditStart(s.audit,s.control.day,s.cursor,s.cutoff-1);
 s.ready=s.audit.valid;return s.ready;
}
// Contrato inclusivo de CopyTicksRange: [cursor,end], proximo cursor=end+1.
bool MDStreamBegin615(MDStream615 &s,long from,long end)
{
 if(!s.ready||s.block_end>=0||from!=s.cursor||end<from||end>=s.cutoff||
    from%60000!=0||(end+1)%60000!=0||end-from>=300000)return false;
 s.block_end=end;return true;
}
bool MDStreamPush615(MDStream615 &s,long msc,double last)
{
 if(!s.ready||s.block_end<0||msc<s.cursor||msc>s.block_end){s.ready=false;return false;}
 if(s.audit.count==0&&(msc!=s.data.open_msc||last!=s.data.values.open_today)){s.ready=false;return false;}
 if(!MDAuditPush(s.audit,msc,last)){s.ready=false;return false;}
 MDDayObserve(s.control,msc,last);return true;
}
bool MDStreamFinish615(MDStream615 &s,bool m1_matches)
{
 if(!s.ready||s.block_end<0||!m1_matches||!s.audit.valid||s.audit.count==0)return false;
 s.cursor=s.block_end+1;s.block_end=-1;s.blocks++;return true;
}
// Trabalhar numa copia e chamar Finish somente apos conferir todos os minutos.
// Falha descarta a copia inteira: retry nao duplica ticks nem consome toques.
long MDStreamHorizon615(long latest_tick,long cutoff)
{long closed=latest_tick/60000*60000;return closed<cutoff?closed:cutoff;}
#endif
