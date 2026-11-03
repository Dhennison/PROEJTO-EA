#ifndef MODELOD_MULTI_SHADOW_CASES
#define MODELOD_MULTI_SHADOW_CASES
#include "ModeloD_MultiCiclo_Casos.mqh"
#include "ModeloD_MultiShadowFile.mqh"
int checksShadow=0,failuresShadow=0;string logShadow="";
void CheckShadow(bool ok,string name){checksShadow++;if(!ok)failuresShadow++;logShadow+=(ok?"PASS: ":"FAIL: ")+name+"\r\n";}
// Fixture produz um diario em escopo derivado de conta/servidor. Os snapshots
// sao artificiais; somente o arquivo e o lock sao reais durante o teste MT5.
bool FixtureMultiShadow(string &journal,MDStream615 &stream,MDSnapshot69 &first,MDSnapshot69 &second,long &now)
{
 string old;MDExecGate613 gate;MDRecoveryEvidence67 market;
 if(!Partial615C(old,gate,market))return false;
 MDDayControl day;if(!Day615C(day))return false;
 string scope=MDContext612(123,"SINTETICO",1);MDPlan615C plan;long prepared=day.frozen.open_msc+10;
 if(!MDTestEntry615C(day,MDHeader610(scope,"WINZ26",20261016,1),scope,1,0,3,prepared,true,true,true,gate,plan))return false;
 MDJournal610 j;if(!MDReplay610(plan.journal,scope,"WINZ26",20261016,1,j))return false;
 MDEvent610 accepted;accepted.kind=2;accepted.level=0;accepted.request=j.r[0].id;accepted.ticket=100;
 accepted.msc=prepared+10;accepted.volume=3;accepted.entry=j.r[0].entry;accepted.sl=j.r[0].sl;accepted.tp=j.r[0].tp;
 if(!MDAppend610(plan.journal,scope,"WINZ26",20261016,1,accepted,journal))return false;
 snap615C.o[0].order.remaining=1;snap615C.deals=2;snap615C.d[1]=snap615C.d[0];snap615C.d[1].ticket=102;snap615C.d[1].position=501;
 snap615C.positions=2;snap615C.p[1]=snap615C.p[0];snap615C.p[1].identifier=501;snap615C.p[1].ticket=701;
 first=snap615C;second=snap615C;
 if(!MDStreamStart615(stream,day.frozen))return false;
 long begin=stream.cursor;
 if(!MDStreamBegin615(stream,begin,begin+59999)||!MDStreamPush615(stream,day.frozen.open_msc,day.frozen.values.open_today)||!MDStreamFinish615(stream,true))return false;
 now=stream.cursor+60000;return MDCommitted615B(stream);
}
// Acrescenta outra origem de nivel 1 ao mesmo diario e inventario sinteticos.
bool AddSecondLevelShadow(string previous,string &next_journal,MDSnapshot69 &snapshot,const MDStream615 &stream)
{
 string scope=MDContext612(123,"SINTETICO",1);MDDayControl day;MDExecGate613 gate;MDPlan615C plan;
 if(!Day615C(day))return false;
 MDTestGate615C(gate);
 long prepared=stream.data.open_msc+100;
 if(!MDTestEntry615C(day,previous,scope,1,1,3,prepared,true,true,true,gate,plan))return false;
 MDJournal610 j;if(!MDReplay610(plan.journal,scope,"WINZ26",20261016,1,j))return false;
 MDEvent610 accepted;accepted.kind=2;accepted.level=1;accepted.request=j.r[1].id;accepted.ticket=200;
 accepted.msc=prepared+10;accepted.volume=3;accepted.entry=j.r[1].entry;accepted.sl=j.r[1].sl;accepted.tp=j.r[1].tp;
 if(!MDAppend610(plan.journal,scope,"WINZ26",20261016,1,accepted,next_journal))return false;
 snapshot.orders=2;snapshot.o[1]=snapshot.o[0];snapshot.o[1].order.ticket=200;snapshot.o[1].order.magic=MDMagic67(1,1);
 snapshot.o[1].order.remaining=2;snapshot.o[1].setup_msc=accepted.msc;
 snapshot.deals=3;snapshot.d[2]=snapshot.d[0];snapshot.d[2].ticket=103;snapshot.d[2].order=200;
 snapshot.d[2].position=502;snapshot.d[2].magic=MDMagic67(1,1);snapshot.d[2].msc=accepted.msc+1;
 snapshot.positions=3;snapshot.p[2]=snapshot.p[0];snapshot.p[2].identifier=502;snapshot.p[2].ticket=702;snapshot.p[2].magic=MDMagic67(1,1);
 return true;
}
void RunMultiShadow(string suffix)
{
 RunCycle(suffix);checksShadow=checksCycle;failuresShadow=failuresCycle;logShadow=logCycle;
 string journal,why;MDStream615 stream;MDSnapshot69 a,b;long now=0;
 bool fixture=FixtureMultiShadow(journal,stream,a,b,now);CheckShadow(fixture,"integracao: diario, fluxo e duas coletas sinteticas prontos");if(!fixture)return;
 string scope=MDContext612(123,"SINTETICO",1);MDMultiShadow state,decoded,next;MDResetMultiShadow(state);
 bool assembled=MDAdvanceMultiShadow("",journal,stream,1,123,"SINTETICO",a,b,now,state,why);
 CheckShadow(assembled&&state.revision==1&&state.level[0].count==2&&MDShadowTotal(state)==2,"integracao: duas posicoes ligadas a origem do diario");if(!assembled)return;
 int x=MDIndexBench(state.level[0],500),y=MDIndexBench(state.level[0],501);
 CheckShadow(x>=0&&y>=0&&state.level[0].slots[x].control.ticket==700&&state.level[0].slots[y].control.ticket==701,"integracao: identificadores e tickets distintos preservados");
 CheckShadow(MDShadowColdControl(state.level[0].slots[x].control)&&MDShadowColdControl(state.level[0].slots[y].control),"integracao: controle observacional nao inventa tentativa de protecao");
 CheckShadow(state.volume[0][x]==1&&state.volume[0][y]==1,"integracao: volume por posicao e observado separadamente");
 double parsed_amount=0;
 CheckShadow(MDShadowAmount("1.00000000",parsed_amount)&&parsed_amount==1,"integracao: quantidade canonica aceita");
 CheckShadow(MDShadowAmount("0.00000000",parsed_amount)&&parsed_amount==0,"integracao: saida zero canonica aceita");
 CheckShadow(!MDShadowAmount("xyz",parsed_amount),"integracao: quantidade nao numerica rejeitada");
 CheckShadow(!MDShadowAmount("1..0000000",parsed_amount),"integracao: quantidade malformada rejeitada");
 CheckShadow(!MDShadowAmount("01.00000000",parsed_amount),"integracao: quantidade nao canonica rejeitada");
 string encoded=MDEncodeMultiShadow(state);
 CheckShadow(encoded!=""&&MDDecodeMultiShadow(encoded,scope,"WINZ26",20261016,1,decoded)&&MDShadowTotal(decoded)==2,"integracao: estado e diario reabertos no mesmo envelope");
 CheckShadow(!MDDecodeMultiShadow(encoded+"X",scope,"WINZ26",20261016,1,decoded),"integracao: adulteracao rejeitada");
 CheckShadow(!MDDecodeMultiShadow(StringSubstr(encoded,0,StringLen(encoded)/2),scope,"WINZ26",20261016,1,decoded),"integracao: truncamento rejeitado");
 CheckShadow(!MDDecodeMultiShadow(encoded,MDContext612(999,"SINTETICO",1),"WINZ26",20261016,1,decoded),"integracao: outra conta rejeitada");
 CheckShadow(!MDDecodeMultiShadow(encoded,scope,"WINZ26",20261019,1,decoded),"integracao: outra sessao rejeitada");
 CheckShadow(!MDDecodeMultiShadow(encoded,scope,"WINV26",20261016,1,decoded),"integracao: outro contrato rejeitado");
 CheckShadow(MDAdvanceMultiShadow(encoded,journal,stream,1,123,"SINTETICO",a,b,now,next,why)&&next.revision==2&&MDShadowTotal(next)==2,"integracao: replay nao duplica controladores");
 b.p[0].ticket=702;
 CheckShadow(!MDAdvanceMultiShadow(encoded,journal,stream,1,123,"SINTETICO",a,b,now,next,why),"integracao: duas leituras divergentes bloqueadas");
 a.p[0].ticket=702;
 CheckShadow(!MDAdvanceMultiShadow(encoded,journal,stream,1,123,"SINTETICO",a,b,now,next,why)&&why=="MULTI_TICKET_ALTERADO_COM_PENDENCIA","integracao: troca de ticket sem prova de pendencias bloqueada");
 a.p[0].ticket=700;b.p[0].ticket=700;
 a.positions=1;b.positions=1;
 CheckShadow(!MDAdvanceMultiShadow(encoded,journal,stream,1,123,"SINTETICO",a,b,now,next,why),"integracao: posicao ausente sem baixa comprovada bloqueada");a.positions=2;b.positions=2;
 a.account_key=999;
 CheckShadow(!MDAdvanceMultiShadow(encoded,journal,stream,1,123,"SINTETICO",a,b,now,next,why),"integracao: snapshot de outra conta bloqueado");a.account_key=123;
 a.complete=false;CheckShadow(!MDAdvanceMultiShadow(encoded,journal,stream,1,123,"SINTETICO",a,b,now,next,why),"integracao: coleta incompleta bloqueada");a.complete=true;
 CheckShadow(!MDAdvanceMultiShadow(encoded,MDHeader610(scope,"WINZ26",20261016,1),stream,1,123,"SINTETICO",a,b,now,next,why),"integracao: diario truncado nao rearma posicao");
 MDStream615 earlier=stream;earlier.cursor-=60000;
 CheckShadow(!MDAdvanceMultiShadow(encoded,journal,earlier,1,123,"SINTETICO",a,b,now,next,why),"integracao: fluxo atrasado nao restaura marcador mais novo");
 MDMultiShadow invalid=state;invalid.level[0].slots[x].control.protection.started=true;
 CheckShadow(MDEncodeMultiShadow(invalid)=="","integracao: tentativa operacional nao e inventada em estado observacional");
 // Fluxo sem origem conhecida nao adota posicao apenas por magic.
 string header=MDHeader610(scope,"WINZ26",20261016,1);
 CheckShadow(!MDAdvanceMultiShadow("",header,stream,1,123,"SINTETICO",a,b,now,next,why),"integracao: magic sem origem no diario nao autoriza adocao");
 MDSnapshot69 empty=a;empty.orders=0;empty.deals=0;empty.positions=0;
 CheckShadow(MDAdvanceMultiShadow("",header,stream,1,123,"SINTETICO",empty,empty,now,next,why)&&MDShadowTotal(next)==0&&why=="SEM_POSICOES_VINCULADAS","integracao: ausencia de cadeia e relatorio claro, sem simular posicoes");
 // Mais uma parcela para a mesma posicao atualiza apenas seu saldo.
 MDSnapshot69 more=a;more.o[0].order.remaining=0;more.o[0].order.state=2;
 more.deals=3;more.d[2]=more.d[0];more.d[2].ticket=104;more.d[2].msc=more.d[0].msc+1;more.p[0].volume=2;
 MDMultiShadow additional;
 bool partial_ok=MDAdvanceMultiShadow(encoded,journal,stream,1,123,"SINTETICO",more,more,now,additional,why);
 CheckShadow(partial_ok&&additional.volume[0][x]==2&&additional.volume[0][y]==1,"integracao: parcela adicional atualiza somente volume conciliado");
 CheckShadow(partial_ok&&MDDecodeMultiShadow(MDEncodeMultiShadow(additional),scope,"WINZ26",20261016,1,decoded)&&decoded.volume[0][x]==2,"integracao: volume adicional sobrevive a reabertura");
 string encoded_add=MDEncodeMultiShadow(additional);
 CheckShadow(partial_ok&&!MDAdvanceMultiShadow(encoded_add,journal,stream,1,123,"SINTETICO",a,b,now,next,why)&&why=="MULTI_HISTORICO_DEALS_REGREDIU","integracao: historico nao pode perder entrada ja observada");
 MDSnapshot69 with_exit=more;with_exit.deals=4;with_exit.d[3]=with_exit.d[0];with_exit.d[3].ticket=105;
 with_exit.d[3].order=300;with_exit.d[3].entry=1;with_exit.d[3].buy=false;with_exit.d[3].volume=1;with_exit.d[3].msc=with_exit.d[2].msc+1;with_exit.p[0].volume=1;
 MDMultiShadow exited;
 bool exit_ok=partial_ok&&MDAdvanceMultiShadow(encoded_add,journal,stream,1,123,"SINTETICO",with_exit,with_exit,now,exited,why);
 CheckShadow(exit_ok&&exited.entered[0][x]==2&&exited.exited[0][x]==1&&exited.volume[0][x]==1,"integracao: saida parcial vinculada reduz saldo preservando entrada");
 CheckShadow(exit_ok&&!MDAdvanceMultiShadow(MDEncodeMultiShadow(exited),journal,stream,1,123,"SINTETICO",more,more,now,next,why)&&why=="MULTI_HISTORICO_DEALS_REGREDIU","integracao: historico nao pode perder saida ja observada");
 MDMultiShadow bad_amount=state;bad_amount.volume[0][x]=0;
 CheckShadow(MDEncodeMultiShadow(bad_amount)=="","integracao: volume zero em posicao ativa e recusado");
 bad_amount=state;bad_amount.entered[0][x]=4;bad_amount.volume[0][x]=4;
 CheckShadow(MDEncodeMultiShadow(bad_amount)=="","integracao: volume acima da ordem original nao e serializado");
 // Outra ordem e outro nivel nao podem compartilhar controlador ou ticket.
 MDSnapshot69 twolevel=a;string journal_two;
 bool second_added=AddSecondLevelShadow(journal,journal_two,twolevel,stream);
 CheckShadow(second_added,"integracao: segunda origem de nivel diferente preparada na fixture");
 MDMultiShadow two;
 bool second_ok=second_added&&MDAdvanceMultiShadow(encoded,journal_two,stream,1,123,"SINTETICO",twolevel,twolevel,now,two,why);
 CheckShadow(second_ok&&two.level[0].count==2&&two.level[1].count==1&&MDShadowTotal(two)==3,"integracao: diario, duas ordens, dois niveis e tres posicoes preservados");
 if(second_ok)
 {
  string encoded_two=MDEncodeMultiShadow(two);
  CheckShadow(MDDecodeMultiShadow(encoded_two,scope,"WINZ26",20261016,1,decoded)&&decoded.level[1].slots[0].identifier==502,"integracao: origem do segundo nivel sobrevive a serializacao");
  MDMultiShadow collision=two;collision.level[1].slots[0].identifier=500;
  CheckShadow(MDEncodeMultiShadow(collision)=="","integracao: identificador compartilhado entre niveis recusado");
 }
 // Estado de disco separado, mesmo codec do EA observacional.
 string path="ModeloD_TEST_ONLY_615D_MULTI1_"+suffix+".state";
 int lock=FileOpen(path+".lock",FILE_READ|FILE_WRITE|FILE_BIN|FILE_COMMON);bool loaded=false;string last="";
 CheckShadow(lock!=INVALID_HANDLE,"disco: trava exclusiva obtida");
 int other=FileOpen(path+".lock",FILE_READ|FILE_WRITE|FILE_BIN|FILE_COMMON);CheckShadow(other==INVALID_HANDLE,"disco: segunda trava recusada");if(other!=INVALID_HANDLE)FileClose(other);
 bool stored=MDSyncMultiShadow(path,lock,loaded,last,journal,stream,1,123,"SINTETICO",a,b,now,next,why);
 CheckShadow(stored&&loaded&&next.revision==1&&MDShadowTotal(next)==2,"disco: dados reais de arquivo com diario e duas posicoes sinteticas");
 CheckShadow(MDSyncMultiShadow(path,lock,loaded,last,journal,stream,1,123,"SINTETICO",a,b,now,next,why)&&next.revision==1,"disco: coleta identica nao cria revisoes inutilmente");
 if(lock!=INVALID_HANDLE)FileClose(lock);
 loaded=false;last="";
 lock=FileOpen(path+".lock",FILE_READ|FILE_WRITE|FILE_BIN|FILE_COMMON);
 CheckShadow(lock!=INVALID_HANDLE&&MDSyncMultiShadow(path,lock,loaded,last,journal,stream,1,123,"SINTETICO",a,b,now,next,why)&&next.revision==1&&MDShadowTotal(next)==2,"disco: reabertura recupera estado sem rearmar");
 CheckShadow(!MDSyncMultiShadow(path,lock,loaded,last,journal,earlier,1,123,"SINTETICO",a,b,now,next,why),"disco: reconstrucao aquem do marcador bloqueada");
 CheckShadow(second_added&&MDSyncMultiShadow(path,lock,loaded,last,journal_two,stream,1,123,"SINTETICO",twolevel,twolevel,now,next,why)&&next.revision==2&&MDShadowTotal(next)==3,"disco: nova origem estende diario e preserva a anterior");
 CheckShadow(!MDSyncMultiShadow(path,lock,loaded,last,journal,stream,1,123,"SINTETICO",a,b,now,next,why),"disco: diario anterior nao sobrescreve revisao nova");
 string saved=last;
 int f=FileOpen(path+".tmp",FILE_WRITE|FILE_BIN|FILE_ANSI|FILE_COMMON,0,CP_UTF8);if(f!=INVALID_HANDLE){FileWriteString(f,"INTERROMPIDO");FileClose(f);}
 CheckShadow(f!=INVALID_HANDLE&&!MDSyncMultiShadow(path,lock,loaded,last,journal,stream,1,123,"SINTETICO",a,b,now,next,why)&&last==saved,"disco: residuo temporario bloqueia sem apagar estado");
 if(lock!=INVALID_HANDLE)FileClose(lock);
 // Inconsistencias de estado e marcador nunca iniciam uma projecao vazia.
 string orphan="ModeloD_TEST_ONLY_615D_MULTI1_ORPHAN_"+suffix+".state";
 int orphan_lock=FileOpen(orphan+".lock",FILE_READ|FILE_WRITE|FILE_BIN|FILE_COMMON);
 bool guard=orphan_lock!=INVALID_HANDLE&&MDCreateGuard615D(orphan+".init",orphan_lock,MDGuardText615D(scope,stream.data));
 bool orphan_loaded=false;string orphan_last="";
 CheckShadow(guard&&!MDSyncMultiShadow(orphan,orphan_lock,orphan_loaded,orphan_last,journal,stream,1,123,"SINTETICO",a,b,now,next,why)&&why=="MARCADOR_OU_ESTADO_MULTI_AUSENTE","disco: marcador sem estado nao e recriado silenciosamente");
 if(orphan_lock!=INVALID_HANDLE)FileClose(orphan_lock);
 string volpath="ModeloD_TEST_ONLY_615D_MULTI1_VOLUME_"+suffix+".state";
 int vol_lock=FileOpen(volpath+".lock",FILE_READ|FILE_WRITE|FILE_BIN|FILE_COMMON);bool vol_loaded=false;string vol_last="";
 bool vol_created=vol_lock!=INVALID_HANDLE&&MDSyncMultiShadow(volpath,vol_lock,vol_loaded,vol_last,journal,stream,1,123,"SINTETICO",a,b,now,next,why);
 CheckShadow(vol_created&&MDSyncMultiShadow(volpath,vol_lock,vol_loaded,vol_last,journal,stream,1,123,"SINTETICO",more,more,now,next,why)&&next.revision==2&&next.volume[0][x]==2,"disco: parcela adicional atualiza saldo e revisao sem novo candle");
 string before_regression=vol_last;
 CheckShadow(!MDSyncMultiShadow(volpath,vol_lock,vol_loaded,vol_last,journal,stream,1,123,"SINTETICO",a,b,now,next,why)&&why=="MULTI_HISTORICO_DEALS_REGREDIU"&&vol_last==before_regression,"disco: retrocesso de historico nao substitui arquivo");
 if(vol_lock!=INVALID_HANDLE)FileClose(vol_lock);
 string tamperpath="ModeloD_TEST_ONLY_615D_MULTI1_TAMPER_"+suffix+".state";
 int tamper_lock=FileOpen(tamperpath+".lock",FILE_READ|FILE_WRITE|FILE_BIN|FILE_COMMON);bool tamper_loaded=false;string tamper_last="";
 bool tamper_created=tamper_lock!=INVALID_HANDLE&&MDSyncMultiShadow(tamperpath,tamper_lock,tamper_loaded,tamper_last,journal,stream,1,123,"SINTETICO",a,b,now,next,why);
 int tamper_file=FileOpen(tamperpath,FILE_WRITE|FILE_BIN|FILE_ANSI|FILE_COMMON,0,CP_UTF8);
 if(tamper_file!=INVALID_HANDLE){FileWriteString(tamper_file,"ALTERADO_EXTERNAMENTE");FileClose(tamper_file);}
 CheckShadow(tamper_created&&tamper_file!=INVALID_HANDLE&&!MDSyncMultiShadow(tamperpath,tamper_lock,tamper_loaded,tamper_last,journal,stream,1,123,"SINTETICO",a,b,now,next,why)&&why=="ESTADO_MULTI_ALTERADO_EXTERIORMENTE","disco: alteracao externa durante sessao e bloqueada");
 if(tamper_lock!=INVALID_HANDLE)FileClose(tamper_lock);
 string no_guard="ModeloD_TEST_ONLY_615D_MULTI1_NOGUARD_"+suffix+".state";
 int no_guard_lock=FileOpen(no_guard+".lock",FILE_READ|FILE_WRITE|FILE_BIN|FILE_COMMON);
 int no_guard_file=FileOpen(no_guard,FILE_WRITE|FILE_BIN|FILE_ANSI|FILE_COMMON,0,CP_UTF8);
 if(no_guard_file!=INVALID_HANDLE){FileWriteString(no_guard_file,"ESTADO_SEM_MARCADOR");FileClose(no_guard_file);}
 bool no_guard_loaded=false;string no_guard_last="";
 CheckShadow(no_guard_file!=INVALID_HANDLE&&!MDSyncMultiShadow(no_guard,no_guard_lock,no_guard_loaded,no_guard_last,journal,stream,1,123,"SINTETICO",a,b,now,next,why)&&why=="MARCADOR_OU_ESTADO_MULTI_AUSENTE","disco: estado sem marcador bloqueia retomada");
 if(no_guard_lock!=INVALID_HANDLE)FileClose(no_guard_lock);
 string origpath="ModeloD_TEST_ONLY_615D_MULTI1_COORD_"+suffix+".state";
 int coord_lock=FileOpen(origpath+".lock",FILE_READ|FILE_WRITE|FILE_BIN|FILE_COMMON);
 string original_next;bool original_built=MDNext615D("",header,scope,1,stream,original_next);
 int temp=FileOpen(origpath+".tmp",FILE_WRITE|FILE_BIN|FILE_ANSI|FILE_COMMON,0,CP_UTF8);
 if(temp!=INVALID_HANDLE){FileWriteString(temp,"PARCIAL");FileClose(temp);}
 CheckShadow(original_built&&temp!=INVALID_HANDLE&&!MDStore615D(origpath,coord_lock,"",original_next),"disco: coordenador nao sobrescreve arquivo temporario remanescente");
 if(coord_lock!=INVALID_HANDLE)FileClose(coord_lock);
}
#endif
