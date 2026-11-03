#ifndef MD_MANAGEMENT_STATE_CASES615L2
#define MD_MANAGEMENT_STATE_CASES615L2
#include "ModeloD_ManagementCases615L.mqh"
#include "ModeloD_ManagementFile615L2.mqh"
int checks615L2=0,failures615L2=0;string log615L2="";
void Check615L2(bool ok,string name){checks615L2++;if(!ok)failures615L2++;log615L2+=(ok?"PASS: ":"FAIL: ")+name+"\r\n";}
void Run615L2(string suffix)
{
 Run615L();checks615L2=checks615L;failures615L2=failures615L;log615L2=log615L;
 MDState615L2 state,readback,next,resolved;string key="TEST_ONLY|123|SINTETICO|WINZ26|20261016|1|0|500|700|207005|207590";
 string domain="CLOCK_FIXTURE_A";MDInit615L2(state,key,domain,700);
 Check615L2(MDValid615L2(state),"L2: estado inicial valido");
 for(int i=0;i<6;i++){MDManagementBegin615L(state.management,i*2000,700,true);MDManagementComplete615L(state.management,i*2000+100,700);}
 state.revision=2;string text=MDEncode615L2(state);
 Check615L2(MDDecode615L2(text,key,domain,2,10100,readback)&&readback.management.protection.initial_completed==6,"L2: seis tentativas preservadas");
 Check615L2(!MDProtectionCloseRequired(readback.management.protection,190099,false)&&MDProtectionCloseRequired(readback.management.protection,190100,false),"L2: releitura nao reinicia prazo de 180s");
 Check615L2(!MDProtectionDue(readback.management.protection,19999)&&MDProtectionDue(readback.management.protection,20000),"L2: releitura preserva intervalo adicional");
 Check615L2(!MDDecode615L2(text,"OUTRO",domain,2,10100,readback),"L2: identidade divergente rejeitada");
 Check615L2(!MDDecode615L2(text,key,"CLOCK_FIXTURE_B",2,10100,readback),"L2: outra origem de relogio bloqueia retomada automatica");
 Check615L2(!MDDecode615L2(text,key,domain,3,10100,readback),"L2: revisao antiga rejeitada");
 Check615L2(!MDDecode615L2(text,key,domain,2,10099,readback),"L2: relogio anterior ao estado rejeitado");
 Check615L2(!MDDecode615L2(text+"x",key,domain,2,10100,readback),"L2: corrupcao rejeitada");
 Check615L2(!MDDecode615L2(StringSubstr(text,0,20),key,domain,2,10100,readback),"L2: truncamento rejeitado");
 string path="ModeloD_TEST_ONLY_615L2_"+suffix+"_agenda.state";
 Check615L2(MDSave615L2(path,state,readback)&&MDEncode615L2(readback)==text,"L2 DISCO: agenda gravada fechada e relida");
 Check615L2(!MDSave615L2(path,state,readback),"L2 DISCO: arquivo existente nao sobrescrito");
 Check615L2(MDLoad615L2(path,key,domain,2,200000,readback)&&MDProtectionCloseRequired(readback.management.protection,200000,false),"L2 DISCO: prazo vencido continua vencido");
 MDManagementBegin615L(state.management,20000,700,true);state.revision++;
 string inflight="ModeloD_TEST_ONLY_615L2_"+suffix+"_protecao.state";
 Check615L2(MDSave615L2(inflight,state,readback)&&readback.management.protection.inflight&&!MDProtectionDue(readback.management.protection,30000),"L2 DISCO: protecao em voo nao e reenviada");
 Check615L2(!MDPrepareAction615L2(state,3,100,0,false,true,next),"L2: sem conciliacao nao prepara cancelamento");
 Check615L2(!MDPrepareAction615L2(state,3,100,0,true,false,next),"L2: sem intencao duravel nao prepara cancelamento");
 Check615L2(MDPrepareAction615L2(state,3,100,0,true,true,next),"L2: cria candidato de cancelamento");
 string cancel="ModeloD_TEST_ONLY_615L2_"+suffix+"_cancelamento.state";
 Check615L2(MDSave615L2(cancel,next,readback)&&readback.phase==1,"L2 DISCO: cancelamento reservado permanece incerto");
 Check615L2(!MDPrepareAction615L2(readback,3,100,0,true,true,resolved),"L2: cancelamento reservado nao duplica");
 Check615L2(!MDPrepareAction615L2(readback,4,700,1,true,true,resolved),"L2: outro comando aguarda resolucao da reserva");
 Check615L2(!MDResolveAction615L2(readback,readback.attempt,3,100,false,resolved),"L2: retorno sem efeito comprovado nao conclui");
 Check615L2(!MDResolveAction615L2(readback,readback.attempt+1,3,100,true,resolved),"L2: resposta de outra tentativa rejeitada");
 Check615L2(!MDResolveAction615L2(readback,readback.attempt,3,101,true,resolved),"L2: resposta de outro ticket rejeitada");
 Check615L2(MDResolveAction615L2(readback,readback.attempt,3,100,true,resolved),"L2: efeito confirmado resolve candidato");
 state=resolved;
 Check615L2(!MDResolveAction615L2(state,state.attempt,3,100,true,resolved),"L2: confirmacao duplicada nao altera estado");
 Check615L2(!MDPrepareAction615L2(state,3,100,0,true,true,next),"L2: cancelamento concluido nao reaparece");
 Check615L2(MDPrepareAction615L2(state,4,700,3,true,true,next)&&next.volume==3,"L2: fechamento usa volume conciliado apos parcial");
 string close="ModeloD_TEST_ONLY_615L2_"+suffix+"_fechamento.state";
 Check615L2(MDSave615L2(close,next,readback)&&readback.volume==3&&readback.phase==1,"L2 DISCO: fechamento reservado preservado");
 Check615L2(!MDPrepareAction615L2(readback,4,700,3,true,true,resolved),"L2: fechamento reservado nao duplica");
 Check615L2(!MDLoad615L2(close,key,"OUTRA_ORIGEM",1,30000,resolved),"L2 DISCO: reinicio com origem desconhecida bloqueado");
 Check615L2(!MDLoad615L2("ajuste_b3.txt",key,domain,1,30000,resolved),"L2: caminho operacional rejeitado");
}
#endif
