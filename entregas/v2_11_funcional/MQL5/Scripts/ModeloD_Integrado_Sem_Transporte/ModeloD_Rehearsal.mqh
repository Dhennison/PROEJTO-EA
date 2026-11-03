#ifndef MD_REHEARSAL615C
#define MD_REHEARSAL615C
#include "ModeloD_Observer.mqh"
#include "ModeloD_IntegratedRecovery.mqh"
#include "ModeloD_Execution.mqh"
// BANCADA SINTETICA: diario em memoria, nenhuma permissao de transporte.
// Flags de gates neste arquivo sao fornecidas pela fixture, nao certificadas.
struct MDPlan615C {bool valid;int count;string reason,journal;MDCommand613 commands[17];};
void MDClearPlan615C(MDPlan615C &p)
{
 p.valid=false;p.count=0;p.reason="BLOQUEADO";p.journal="";
 // Cópias do plano incluem os 17 slots, mesmo quando count e menor.
 for(int i=0;i<17;i++)
 {
  p.commands[i].valid=false;p.commands[i].buy=false;p.commands[i].action=0;p.commands[i].level=0;
  p.commands[i].ticket=0;p.commands[i].magic=0;p.commands[i].request_id=0;p.commands[i].symbol="";
  p.commands[i].volume=0;p.commands[i].price=0;p.commands[i].sl=0;p.commands[i].tp=0;
 }
}
void MDTestGate615C(MDExecGate613 &g)
{
 g.connected=true;g.lock_held=true;g.snapshot_fresh=true;g.ownership=true;g.entry_eligible=true;
 g.intent_durable=true; // Simulado. Nao houve gravacao fisica nesta bancada.
 g.tick_size=5;g.volume_min=1;g.volume_max=1000;g.volume_step=1;
}
bool MDTestEntry615C(MDDayControl &day,string text,string scope,int instance,int level,long volume,long now,
 bool clock_ok,bool history_ok,bool reconciled,MDExecGate613 &g,MDPlan615C &p)
{
 MDClearPlan615C(p);
 if(!day.ready||level<0||level>4)return false;
 MDJournal610 j;if(!MDReplay610(text,scope,day.frozen.contract,day.frozen.date,instance,j)||!MDNoRequest610(j,level))return false;
 long midnight=MDCivilMidnight2026(day.frozen.date);int second=(int)((now-midnight)/1000);
 string why=MDDayReason(day,day.frozen,day.frozen.contract,day.frozen.date,second,now,g.connected,clock_ok,history_ok,reconciled,level);
 if(why!="ELEGIVEL_NA_SIMULACAO_SEM_ORDENS"){p.reason=why;return false;}
 MDLevel l=day.day.levels[level];MDEvent610 e;e.kind=1;e.level=level;e.request=level+1;e.ticket=0;e.msc=now;
 e.volume=volume;e.entry=(long)l.entry_tick;e.sl=(long)l.sl_tick;e.tp=(long)l.tp_tick;
 string next;if(!MDAppend610(text,scope,j.contract,j.date,instance,e,next))return false;
 MDJournal610 prepared;if(!MDReplay610(next,scope,j.contract,j.date,instance,prepared))return false;
 MDCommand613 cmd;if(!MDCommandBuild613(prepared,level,1,0,0,g,cmd))return false;
 if(!MDLifeRequest(day.levels[level],true))return false;
 p.commands[0]=cmd;p.count=1;p.valid=true;p.journal=next;p.reason="PLANO_ENTRADA_SIMULADO_SEM_TRANSPORTE";return true;
}
bool MDTestIntent615C(string &text,MDJournal610 &j,int level,int kind,long now)
{
 bool exists=kind==3?j.r[level].consumed:(kind==4?j.r[level].cancel:j.r[level].close);
 if(exists)return true;
 MDRequest610 r=j.r[level];MDEvent610 e;e.kind=kind;e.level=level;e.request=r.id;e.ticket=r.ticket;
 e.msc=now;e.volume=r.volume;e.entry=r.entry;e.sl=r.sl;e.tp=r.tp;
 string next;if(!MDAppend610(text,j.scope,j.contract,j.date,j.instance,e,next))return false;
 MDJournal610 candidate;if(!MDReplay610(next,j.scope,j.contract,j.date,j.instance,candidate))return false;
 text=next;j=candidate;return true;
}
bool MDTestRecoverPlan615C(string text,string scope,string contract,int date,int instance,int level,
 const MDSnapshot69 &snapshot,long account,string server,long now,const MDRecoveryEvidence67 &market,
 bool cutoff,MDExecGate613 &gate,MDPlan615C &p)
{
 MDClearPlan615C(p);
 if(level<0||level>4||snapshot.account_key!=account||snapshot.server_key!=server||!gate.connected||!gate.lock_held||!gate.snapshot_fresh)return false;
 MDJournal610 j;if(!MDReplay610(text,scope,contract,date,instance,j)||j.last_msc>now)return false;
 MDIntegrated611 rec;if(!MDIntegratedRecover611(j,scope,level,snapshot,now,market,cutoff,rec)){p.reason=rec.reason;return false;}
 MDOrigin68 origin;MDChainInput68 chain;MDChainResult68 resolved;string why;
 if(!MDOrigin611(j,scope,level,snapshot,origin)||!MDBuild69(snapshot,origin,now,chain,why)||!MDReconcileChain68(chain,resolved))return false;
 string next=text;
 if(rec.decision.consumed&&!MDTestIntent615C(next,j,level,3,now))return false;
 if(rec.decision.cancel_pending&&!MDTestIntent615C(next,j,level,4,now))return false;
 if(rec.decision.close_positions&&!MDTestIntent615C(next,j,level,5,now))return false;
 MDPlan615C candidate;MDClearPlan615C(candidate);MDCommand613 cmd;
 if(rec.decision.cancel_pending)
 {if(!MDCommandBuild613(j,level,3,j.r[level].ticket,0,gate,cmd))return false;candidate.commands[candidate.count++]=cmd;}
 if(rec.decision.close_positions||rec.decision.protect_positions)
 {
  int action=rec.decision.close_positions?4:2;
  for(int i=0;i<resolved.position_count;i++)if(resolved.positions[i].open_volume>0)
  {
   if(candidate.count>=17||!MDCommandBuild613(j,level,action,resolved.positions[i].current_ticket,resolved.positions[i].open_volume,gate,cmd))return false;
   candidate.commands[candidate.count++]=cmd;
  }
 }
 candidate.valid=true;candidate.journal=next;candidate.reason="PLANO_RECUPERACAO_SIMULADO_SEM_TRANSPORTE";p=candidate;return true;
}
#endif
