#ifndef MD_STATE_STORE_CASES615L4
#define MD_STATE_STORE_CASES615L4
#include "ModeloD_UrgentCases615L3.mqh"
#include "ModeloD_StateStore615L4.mqh"
int checks615L4=0,failures615L4=0;string log615L4="";
void Check615L4(bool ok,string name){checks615L4++;if(!ok)failures615L4++;log615L4+=(ok?"PASS: ":"FAIL: ")+name+"\r\n";}
void Run615L4(string suffix)
{
 Run615L3(suffix);checks615L4=checks615L3;failures615L4=failures615L3;log615L4=log615L3;
 MDStore615L4 store,other;MDPair615L3 initial,current,next,loaded;MDCommand613 cmd;MDPlan615C plan;MDJournal610 j;
 string journal;MDExecGate613 gate;MDRecoveryEvidence67 market;
 bool ready=Partial615C(journal,gate,market)&&Recover615C(journal,market,true,gate,plan)&&MDReplay610(plan.journal,"TEST_ONLY_615C","WINZ26",20261016,1,j);
 Check615L4(ready,"L4: plano conciliado de corte preparado");
 string key=MDPairKey615L3(j,0,700),domain="CLOCK_FIXTURE_L4",base="ModeloD_TEST_ONLY_615L4_"+suffix;
 MDPairInit615L3(initial,key,domain,700);
 Check615L4(!store.Load(0,loaded),"L4: leitura sem lock bloqueada");
 Check615L4(!store.Open("ajuste_b3",key,domain),"L4: caminho operacional recusado");
 Check615L4(store.Open(base,key,domain),"L4 DISCO: lock exclusivo adquirido");
 Check615L4(!other.Open(base,key,domain),"L4 DISCO: segunda abertura bloqueada");
 Check615L4(!store.Load(0,loaded),"L4: arquivo ausente nao vira estado vazio valido");
 Check615L4(store.Create(initial,0),"L4 DISCO: revisao inicial gravada e conferida");
 Check615L4(!store.Create(initial,0),"L4: inicializacao nao sobrescreve estado existente");
 bool prepared=Prepare615L3(initial,plan,3,true,next,cmd);
 Check615L4(prepared&&store.Commit(initial,next,0),"L4 DISCO: cancelamento reservado publicado como revisao 2");current=next;
 prepared=Prepare615L3(current,plan,4,true,next,cmd);
 Check615L4(prepared&&store.Commit(current,next,0),"L4 DISCO: fechamento urgente publicado como revisao 3");
 Check615L4(!store.Commit(initial,current,0),"L4: escritor com estado antigo rejeitado");
 Check615L4(!store.Commit(next,next,0),"L4: mesma revisao nao e regravada");
 current=next;next.revision+=2;
 Check615L4(!store.Commit(current,next,0),"L4: salto de revisao rejeitado");
 store.Close();
 Check615L4(!store.Load(0,loaded),"L4: handle fechado impede leitura");
 Check615L4(other.Open(base,key,domain),"L4 DISCO: lock liberado permite nova instancia");
 Check615L4(other.Load(0,loaded)&&loaded.revision==3&&loaded.cancel_slot.phase==1&&loaded.close_slot.phase==1,"L4 DISCO: retomada encontra revisao mais recente e duas reservas");
 Check615L4(!Prepare615L3(loaded,plan,3,true,next,cmd)&&!Prepare615L3(loaded,plan,4,true,next,cmd),"L4: retomada nao recria chamadas");
 other.Close();
 Check615L4(store.Open(base,"OUTRO",domain)&&!store.Load(0,loaded),"L4: identidade divergente bloqueia recuperacao");store.Close();
 Check615L4(store.Open(base,key,"OUTRO_CLOCK")&&!store.Load(0,loaded),"L4: origem de relogio divergente bloqueia recuperacao");store.Close();
 store.Open(base,key,domain);
 // Falha injetada somente nos arquivos exclusivos desta execucao.
 string confirmed;MDReadStore615L4(base+".head",confirmed);
 Check615L4(MDWriteStore615L4(base+".tmp","GRAVACAO_INTERROMPIDA")&&!store.Load(0,loaded),"L4 DISCO: temporario incompleto bloqueia retorno silencioso ao estado anterior");
 Check615L4(!store.Commit(current,current,0),"L4: estado suspeito nao aceita commit");store.Close();
 string bad=base+"_corrompido";store.Open(bad,key,domain);store.Create(initial,0);
 Check615L4(MDWriteStore615L4(bad+".head","CORROMPIDO")&&!store.Load(0,loaded),"L4 DISCO: ancora corrompida bloqueia sem fallback");store.Close();
 Check615L4(!other.Open("../ModeloD_TEST_ONLY_615L4_escape",key,domain),"L4: caminho com travessia rejeitado");
 string preserved;Check615L4(MDReadStore615L4(base+".head",preserved)&&preserved==confirmed,"L4: falha temporaria preservou estado confirmado anterior");
}
#endif
