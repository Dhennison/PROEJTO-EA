#ifndef MD_RESPONSE_STORE_CASES615Q
#define MD_RESPONSE_STORE_CASES615Q
#include "ModeloD_EntryBundleCases615P.mqh"
#include "ModeloD_ResponseStore615Q.mqh"
int checks615Q=0,failures615Q=0;string log615Q="";
void Check615Q(bool ok,string name){checks615Q++;if(!ok)failures615Q++;log615Q+=(ok?"PASS: ":"FAIL: ")+name+"\r\n";}
void Run615Q(string suffix)
{
 Run615P(suffix);checks615Q=checks615P;failures615Q=failures615P;log615Q=log615P;
 string text;MDJournal610 j,parsed;MDSubmission615K request;Prepared615K(0,text,j,request);
 MDExecGate613 gate;MDReadiness615M e;MDCommand613 command;MDDecision615M decision;
 MDTestGate615C(gate);Evidence615M(e);MDEntryBundle615P source;
 string base="ModeloD_TEST_ONLY_615L4_Q_"+suffix;
 bool prepared=source.Open("ModeloD_TEST_ONLY_615L4_P_Q_"+suffix,j,0,123,"SINTETICO")&&source.Prepare(text,gate,e,command,decision);
 MDResponseStore615Q store,other;MDResponseState615Q state;
 Check615Q(prepared&&store.Open(base,j,0,123,"SINTETICO")&&store.Import(source),"Q: importa diario e reserva relidos de P");
 Check615Q(!store.Import(source),"Q: importacao repetida nao sobrescreve estado");
 Check615Q(!other.Open(base,j,0,123,"SINTETICO"),"Q: segundo escritor bloqueado");
 Check615Q(store.Load(state)&&state.revision==1&&state.receipt.phase==2&&state.journal==text,"Q: estado inicial preserva incerteza e diario");
 Check615Q(!store.Response(1,2,true,10008,0,100),"Q: resposta de outra tentativa rejeitada");
 Check615Q(!store.Response(99,1,true,10008,0,100),"Q: revisao antiga ou inexistente rejeitada");
 Check615Q(store.Response(1,1,true,10008,0,100)&&store.Load(state)&&state.receipt.phase==3&&state.revision==2,"Q: resposta aceita persistida aguardando prova");
 Check615Q(MDReplay610(state.journal,j.scope,j.contract,j.date,j.instance,parsed)&&parsed.r[0].ticket==0,"Q: retorno aceito sozinho nao vincula ticket ao diario");
 Check615Q(!store.Response(2,1,true,10008,0,100),"Q: resposta aceita duplicada nao incrementa revisao");
 store.Close();Check615Q(store.Open(base,j,0,123,"SINTETICO")&&store.Load(state)&&state.receipt.phase==3,"Q: reabertura conserva resposta aceita sem inventar vinculo");
 MDRawOrder69 order;order.entry_limit=true;order.setup_msc=j.r[0].prepared_msc+10;order.order.ticket=100;
 order.order.magic=MDMagic67(1,0);order.order.symbol="WINZ26";order.order.buy=true;order.order.state=0;order.order.initial_volume=3;order.order.remaining=3;
 double price=(double)j.r[0].entry;long touch=order.setup_msc+1;
 Check615Q(!store.Bind(2,order,price,touch,false,true,123,"SINTETICO"),"Q: historico incompleto bloqueia vinculo");
 Check615Q(!store.Bind(2,order,price,touch,true,false,123,"SINTETICO"),"Q: leitura antiga bloqueia vinculo");
 Check615Q(!store.Bind(2,order,price,touch,true,true,999,"SINTETICO"),"Q: conta da evidencia divergente rejeitada");
 Check615Q(!store.Bind(2,order,price,touch,true,true,123,"OUTRO"),"Q: servidor da evidencia divergente rejeitado");
 Check615Q(!store.Bind(2,order,price+5,touch,true,true,123,"SINTETICO"),"Q: preco divergente bloqueia vinculo");
 order.order.ticket=999;Check615Q(!store.Bind(2,order,price,touch,true,true,123,"SINTETICO"),"Q: ticket divergente bloqueia vinculo");order.order.ticket=100;
 Check615Q(store.Bind(2,order,price,touch,true,true,123,"SINTETICO")&&store.Load(state)&&state.revision==3&&state.receipt.phase==5,"Q: vinculo e diario confirmados na mesma revisao");
 Check615Q(MDReplay610(state.journal,j.scope,j.contract,j.date,j.instance,parsed)&&parsed.r[0].ticket==100&&!parsed.r[0].consumed,"Q: aceite anterior ao toque preserva oportunidade");
 Check615Q(!store.Bind(3,order,price,touch,true,true,123,"SINTETICO"),"Q: vinculo repetido nao reaplica eventos");
 store.Close();Check615Q(store.Open(base,j,0,123,"SINTETICO")&&store.Load(state)&&state.receipt.phase==5&&state.receipt.ticket==100,"Q: reabertura recupera vinculo persistido");store.Close();
 Check615Q(other.Open(base,j,0,999,"SINTETICO")&&!other.Load(state),"Q: arquivo de outra conta rejeitado");other.Close();
 string latepath=base+"_LATE";store.Open(latepath,j,0,123,"SINTETICO");store.Import(source);store.Response(1,1,true,10008,0,100);
 Check615Q(store.Bind(2,order,price,order.setup_msc,true,true,123,"SINTETICO")&&store.Load(state)&&state.receipt.touched,"Q: aceite no mesmo milissegundo do toque marcado tardio");
 Check615Q(MDReplay610(state.journal,j.scope,j.contract,j.date,j.instance,parsed)&&parsed.r[0].consumed&&parsed.r[0].cancel,"Q: consumo e intencao de cancelamento persistidos juntos");store.Close();
 string timeoutpath=base+"_TIMEOUT";store.Open(timeoutpath,j,0,123,"SINTETICO");store.Import(source);
 Check615Q(store.Response(1,1,true,10012,0,0)&&store.Load(state)&&state.receipt.phase==2&&!MDRetry615K(state.receipt,true,true,true),"Q: timeout persistido nao libera reenvio");
 Check615Q(!store.Bind(2,order,price,touch,true,true,123,"SINTETICO"),"Q: tentativa incerta nao vira vinculo sem resposta aceita");store.Close();
 string rejectpath=base+"_REJECT";store.Open(rejectpath,j,0,123,"SINTETICO");store.Import(source);
 Check615Q(store.Response(1,1,true,10006,0,0)&&store.Load(state)&&state.receipt.phase==4,"Q: rejeicao preservada para classificacao sem retry neste adaptador");store.Close();
 string residue=base+"_TMP";store.Open(residue,j,0,123,"SINTETICO");store.Import(source);MDWriteStore615L4(residue+".tmp","FALHA_CONTROLADA");
 Check615Q(!store.Response(1,1,true,10008,0,100)&&!store.Load(state),"Q: residuo temporario bloqueia atualizacao e leitura");store.Close();
 string mismatch=base+"_IMPORT_ID";other.Open(mismatch,j,0,999,"SINTETICO");
 Check615Q(!other.Import(source),"Q: importacao entre contas diferentes rejeitada");other.Close();
 other.Open(mismatch,j,0,123,"OUTRO");
 Check615Q(!other.Import(source),"Q: importacao entre servidores diferentes rejeitada");other.Close();
 source.Close();
}
#endif
