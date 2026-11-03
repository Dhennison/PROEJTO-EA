#ifndef MD_RESERVATION_CASES615O
#define MD_RESERVATION_CASES615O
#include "ModeloD_ObservationBridgeCases615N.mqh"
#include "ModeloD_SubmissionCases615K.mqh"
#include "ModeloD_Reservation615O.mqh"
int checks615O=0,failures615O=0;string log615O="";
void Check615O(bool ok,string name){checks615O++;if(!ok)failures615O++;log615O+=(ok?"PASS: ":"FAIL: ")+name+"\r\n";}
void Run615O(string suffix)
{
 Run615N(suffix);checks615O=checks615N;failures615O=failures615N;log615O=log615N;
 string text;MDJournal610 j;MDSubmission615K initial,reopened;
 MDExecGate613 g;MDReadiness615M e;MDDecision615M decision;MDCommand613 command;
 bool prepared=Prepared615K(0,text,j,initial);MDTestGate615C(g);Evidence615M(e);
 string base="ModeloD_TEST_ONLY_615L4_O_"+suffix;
 MDReservation615O store,other;
 Check615O(prepared&&store.Open(base,initial.key,123,"SINTETICO"),"O: reserva abre com identidade e pedido");
 Check615O(!other.Open(base,initial.key,123,"SINTETICO"),"O: segundo escritor bloqueado pelo lock real");
 e.clock_certified=false;
 Check615O(!store.Reserve(j,0,g,e,command,decision)&&!command.valid&&!FileIsExist(base+".receipt",FILE_COMMON),"O: relogio nao certificado impede gravar tentativa");
 Evidence615M(e);e.touches_complete=false;
 Check615O(!store.Reserve(j,0,g,e,command,decision)&&!FileIsExist(base+".receipt",FILE_COMMON),"O: historico incompleto nao reserva");
 Evidence615M(e);e.uncertain_action=true;
 Check615O(!store.Reserve(j,0,g,e,command,decision),"O: tentativa incerta anterior bloqueia");
 Evidence615M(e);e.account=999;
 Check615O(!store.Reserve(j,0,g,e,command,decision),"O: troca de conta bloqueia antes de gravar");
 Evidence615M(e);e.server="OUTRO";
 Check615O(!store.Reserve(j,0,g,e,command,decision),"O: troca de servidor bloqueia");
 Evidence615M(e);e.cutoff=true;
 Check615O(!store.Reserve(j,0,g,e,command,decision),"O: corte bloqueia reserva de entrada");
 Evidence615M(e);g.intent_durable=false;
 Check615O(!store.Reserve(j,0,g,e,command,decision),"O: reserva nao inventa persistencia previa do diario");
 MDTestGate615C(g);e.now_ms=99999;
 Check615O(!store.Reserve(j,0,g,e,command,decision),"O: evidencias antigas bloqueiam");
 Evidence615M(e);g.connected=false;
 Check615O(!store.Reserve(j,0,g,e,command,decision),"O: desconexao bloqueia reserva");MDTestGate615C(g);
 Check615O(store.Reserve(j,0,g,e,command,decision)&&command.valid&&decision.plan_allowed&&!decision.transport_allowed,"O: gravacao releitura e plano encadeados sem transporte");
 Check615O(command.price==j.r[0].entry&&command.sl==j.r[0].sl&&command.tp==j.r[0].tp&&command.request_id==j.r[0].id,"O: reserva preserva precos e pedido do diario");
 Check615O(store.Restore(reopened)&&reopened.phase==2&&reopened.attempt==1,"O: releitura conserva tentativa como incerta");
 Check615O(!store.Reserve(j,0,g,e,command,decision)&&!command.valid&&!decision.plan_allowed,"O: repeticao no mesmo processo nao produz segundo plano");
 store.Close();Check615O(store.Open(base,initial.key,123,"SINTETICO")&&store.Restore(reopened),"O: estado reaberto do disco");
 Check615O(!store.Reserve(j,0,g,e,command,decision)&&!MDRetry615K(reopened,true,true,true),"O: reabertura nao autoriza reenvio automatico");
 store.Close();Check615O(other.Open(base,initial.key,999,"SINTETICO")&&!other.Restore(reopened),"O: recibo de outra conta rejeitado");other.Close();
 Check615O(other.Open(base,initial.key,123,"OUTRO")&&!other.Restore(reopened),"O: recibo de outro servidor rejeitado");other.Close();
 Check615O(other.Open(base,"OUTRO_PEDIDO",123,"SINTETICO")&&!other.Restore(reopened),"O: recibo de outro pedido rejeitado");other.Close();
 Check615O(!store.Open("arquivo_operacional",initial.key,123,"SINTETICO"),"O: caminho fora de bancada rejeitado");
 string bad=base+"_BAD";Check615O(MDWriteStore615L4(bad+".receipt","TRUNCADO")&&store.Open(bad,initial.key,123,"SINTETICO")&&!store.Restore(reopened),"O: arquivo truncado nao e estado valido");
 Check615O(!store.Reserve(j,0,g,e,command,decision)&&!command.valid,"O: arquivo corrompido existente nao e sobrescrito");store.Close();
 string denied=base+"_DENIED";store.Open(denied,initial.key,123,"SINTETICO");
 int hold=FileOpen(denied+".receipt",FILE_WRITE|FILE_BIN|FILE_COMMON);
 Check615O(hold!=INVALID_HANDLE&&!store.Reserve(j,0,g,e,command,decision)&&!command.valid&&!decision.transport_allowed,"O: arquivo ocupado nao produz comando");
 if(hold!=INVALID_HANDLE){FileClose(hold);}
 store.Close();
 Check615O(!store.Reserve(j,0,g,e,command,decision)&&!command.valid,"O: objeto fechado nao reserva");
}
#endif
