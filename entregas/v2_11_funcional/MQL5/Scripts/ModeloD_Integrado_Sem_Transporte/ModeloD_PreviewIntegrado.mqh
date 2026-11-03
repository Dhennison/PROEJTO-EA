#ifndef MD_PREVIEW_INTEGRADO_NO_SEND
#define MD_PREVIEW_INTEGRADO_NO_SEND
#include "ModeloD_Coordinator.mqh"
#include "ModeloD_Rehearsal.mqh"
// Avaliacao consultiva. Jamais despacha comando, registra chamada ao servidor,
// prova preenchimento/protecao ou altera o diario de origem.
struct MDPreviewIntegrado {bool valid;int chains,plans,cancel,protect,close;long cursor;string source_journal,data_key,journal_candidate,lines,reason;};
void MDPreviewClear(MDPreviewIntegrado &v)
{v.valid=false;v.chains=0;v.plans=0;v.cancel=0;v.protect=0;v.close=0;v.cursor=0;v.source_journal="";v.data_key="";v.journal_candidate="";v.lines="";v.reason="NAO_AVALIADO";}
void MDPreviewEvidenceUnknown(MDRecoveryEvidence67 &e,bool touched)
{
 e.server_complete=false;e.ownership_resolved=false;e.history_complete=false;e.request_resolved=false;
 e.had_entry=false;e.touched=touched;e.accepted_before_touch=false;e.boundary_after_accept=false;
 e.exit_after_entry=false;e.cutoff=false;e.pending_count=0;e.position_count=0;
}
// As entradas de evidencia sao fornecidas separadamente. Em dados atuais o
// chamador usa sempre MDPreviewEvidenceUnknown: minuto fechado nao comprova
// historico completo ate agora, SL/TP ou relogio de corte certificado.
bool MDPreviewIntegrado615(string journal,const MDStream615 &stream,int instance,long account,string server,
 const MDSnapshot69 &first,const MDSnapshot69 &second,long now,const MDExecGate613 &gate,
 const MDRecoveryEvidence67 &e0,const MDRecoveryEvidence67 &e1,const MDRecoveryEvidence67 &e2,
 const MDRecoveryEvidence67 &e3,const MDRecoveryEvidence67 &e4,bool cutoff_certified,
 MDPreviewIntegrado &out)
{
 MDPreviewClear(out);MDReview615D review;
 if(!MDReviewState615D(journal,stream,instance,account,server,first,second,now,review))
 {out.reason=review.reason;return false;}
 if(!gate.connected||!gate.lock_held||!gate.snapshot_fresh||!gate.ownership||gate.tick_size!=5||
    !MathIsValidNumber(gate.volume_min)||!MathIsValidNumber(gate.volume_max)||!MathIsValidNumber(gate.volume_step)||
    gate.volume_min<=0||gate.volume_max<gate.volume_min||gate.volume_step<=0)
 {out.reason="PORTOES_OU_PROPRIEDADES_NAO_CONFERIDOS";return false;}
 string scope=MDContext612(account,server,instance),candidate=journal;MDJournal610 j;
 if(!MDReplay610(journal,scope,stream.data.contract,stream.data.date,instance,j))return false;
 MDRecoveryEvidence67 ev[5];ev[0]=e0;ev[1]=e1;ev[2]=e2;ev[3]=e3;ev[4]=e4;
 out.chains=review.chains;
 for(int level=0;level<5;level++)
 {
  if(j.r[level].id==0)
  {
   out.lines+="PREVIA_NIVEL;id="+IntegerToString(level)+";origem=SEM_PEDIDO;toque_no_trecho="+
    IntegerToString(stream.audit.touches[level].tape.touched?1:0)+";NAO_AUTORIZA_ENTRADA\n";
   continue;
  }
  if(j.r[level].ticket<=0){out.reason="SOLICITACAO_SEM_RESOLUCAO";return false;}
  // Apenas para construir candidato em memoria. Nao e evidencia de commit de
  // intencao operacional nem cria permissao de despachar.
  MDExecGate613 planning=gate;planning.intent_durable=true;
  MDPlan615C p;
  if(!MDTestRecoverPlan615C(candidate,scope,stream.data.contract,stream.data.date,instance,level,
      second,account,server,now,ev[level],cutoff_certified,planning,p))
  {out.reason="PREVIA_NIVEL_"+IntegerToString(level)+"_BLOQUEADA:"+p.reason;return false;}
  candidate=p.journal;
  for(int k=0;k<p.count;k++)
  {
   MDCommand613 c=p.commands[k];if(!c.valid||c.action<2||c.action>4){out.reason="PREVIA_INVALIDA";return false;}
   out.plans++;if(c.action==2)out.protect++;if(c.action==3)out.cancel++;if(c.action==4)out.close++;
   out.lines+="PREVIA_ACAO;id="+IntegerToString(level)+";tipo="+IntegerToString(c.action)+
    ";ticket="+IntegerToString(c.ticket)+";volume="+DoubleToString(c.volume,8)+
    ";SL="+DoubleToString(c.sl,0)+";TP="+DoubleToString(c.tp,0)+
    ";CANDIDATO_NAO_ENVIADO;PROTECAO_REAL_NAO_VERIFICADA\n";
  }
 }
 out.cursor=stream.cursor;out.data_key=MDDataKey615B(stream.data);out.source_journal=journal;
 out.journal_candidate=candidate;out.valid=true;out.reason="PREVIA_SEM_TRANSPORTE_E_SEM_CONFIRMACAO_REAL";return true;
}
#endif
