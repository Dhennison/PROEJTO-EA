#ifndef MD_EXECUTION613
#define MD_EXECUTION613
#include "ModeloD_Journal.mqh"
#include "ModeloD_Protection.mqh"
struct MDExecGate613
{
 bool connected,lock_held,snapshot_fresh,ownership,entry_eligible,intent_durable;
 double tick_size,volume_min,volume_max,volume_step;
};
struct MDCommand613
{bool valid,buy;int action,level;long ticket,magic,request_id;string symbol;double volume,price,sl,tp;};
bool MDVolume613(double value,const MDExecGate613 &g)
{
 if(!MathIsValidNumber(value)||!MathIsValidNumber(g.volume_min)||!MathIsValidNumber(g.volume_max)||!MathIsValidNumber(g.volume_step)||
 g.volume_step<=0||g.volume_min<=0||g.volume_max<g.volume_min||value<g.volume_min||value>g.volume_max)return false;
 return MathAbs(value/g.volume_step-MathRound(value/g.volume_step))<0.00000001;
}
// action: 1 pendente;2 SLTP;3 cancelar ticket;4 fechar ticket.
bool MDCommandBuild613(const MDJournal610 &j,int level,int action,long current_ticket,double current_volume,
 const MDExecGate613 &g,MDCommand613 &c)
{
 c.valid=false;
 if(!j.valid||level<0||level>4||action<1||action>4||!g.connected||!g.lock_held||!g.snapshot_fresh||g.tick_size!=5)return false;
 MDRequest610 r=j.r[level];if(r.id<=0)return false;
 if(action==1)
 {if(!g.entry_eligible||!g.intent_durable||r.ticket!=0||r.consumed||r.cancel||r.close||!MDVolume613((double)r.volume,g))return false;}
 else
 {if(!g.ownership||r.ticket<=0||current_ticket<=0)return false;
  if(action==3&&(!g.intent_durable||!r.cancel||current_ticket!=r.ticket))return false;
  if(action==4&&(!g.intent_durable||!r.close))return false;
  if((action==2||action==4)&&!MDVolume613(current_volume,g))return false;}
 c.action=action;c.level=level;c.ticket=action==1?0:current_ticket;c.magic=MDMagic67(j.instance,level);
 c.request_id=r.id;c.symbol=j.contract;c.buy=action==4?level>=3:level<3;
 c.volume=action==1?(double)r.volume:((action==2||action==4)?current_volume:0);
 c.price=action==1?(double)r.entry:0;c.sl=action==1||action==2?(double)r.sl:0;c.tp=action==1||action==2?(double)r.tp:0;
 c.valid=true;return true;
}
// Retorno nao confirma fills, protecao aplicada ou cancelamento concluido.
int MDResponse613(bool api_ok,long retcode,long external)
{
 // 0 incerto: reconciliar sem reenviar;1 aceito: reconciliar;2 rejeitado: classificar;
 // 3 sem alteracao: consultar estado atual.
 if(external!=0)return 0;
 // Explicit native rejection is evidence even when OrderSend returns false.
 // Timeout/connection loss/unknown responses remain uncertain, never auto-resend.
 if(retcode==10004||retcode==10006||retcode==10013||retcode==10014||retcode==10015||retcode==10016||
 retcode==10017||retcode==10018||retcode==10019||retcode==10020||retcode==10021||retcode==10024||
 retcode==10026||retcode==10027||retcode==10028||retcode==10029||retcode==10030||retcode==10033||
 retcode==10034||retcode==10035)return 2;
 if(!api_ok)return 0;
 if(retcode==10008||retcode==10009||retcode==10010)return 1;
 if(retcode==10025)return 3;
 if(retcode==10012||retcode==10031)return 0;
 return 0;
}
bool MDProtectionMatches613(double sl,double tp,const MDRequest610 &r)
{return sl==(double)r.sl&&tp==(double)r.tp;}
// Nao recriar essa permissao de um PREPARAR relido apos reinicio.
bool MDClaimOnce613(bool &permit)
{if(!permit)return false;permit=false;return true;}
// Limites matematicos e tempo do evento sao evidencias externas. Fill nao muda SL/TP.
#endif
