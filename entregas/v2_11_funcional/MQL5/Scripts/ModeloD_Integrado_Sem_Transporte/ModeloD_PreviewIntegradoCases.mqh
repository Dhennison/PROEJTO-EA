#ifndef MD_PREVIEW_INTEGRADO_CASES
#define MD_PREVIEW_INTEGRADO_CASES
#include "ModeloD_MultiShadowCases.mqh"
#include "ModeloD_PreviewIntegradoFile.mqh"
int checksPreview=0,failuresPreview=0;string logPreview="";
void CheckPreview(bool ok,string name)
{checksPreview++;if(!ok)failuresPreview++;logPreview+=(ok?"PASS: ":"FAIL: ")+name+"\r\n";}
void RunPreviewIntegrado(string suffix)
{
 RunMultiShadow(suffix);checksPreview=checksShadow;failuresPreview=failuresShadow;logPreview=logShadow;
 string journal,why;MDStream615 stream;MDSnapshot69 a,b;long now;
 bool built=FixtureMultiShadow(journal,stream,a,b,now);
 CheckPreview(built,"preview: diario, fluxo e duas posicoes sinteticas");if(!built)return;
 MDExecGate613 gate;MDTestGate615C(gate);MDRecoveryEvidence67 e;MDPreviewEvidenceUnknown(e,false);
 MDPreviewIntegrado plan;
 bool ok=MDPreviewIntegrado615(journal,stream,1,123,"SINTETICO",a,b,now,gate,e,e,e,e,e,false,plan);
 CheckPreview(ok&&plan.valid&&plan.chains==1&&plan.plans==3&&plan.cancel==1&&plan.protect==2&&plan.close==0,
  "preview: historico incerto indica saldo e protecao por posicao sem despacho");
 CheckPreview(ok&&StringFind(plan.lines,"ticket=700")>=0&&StringFind(plan.lines,"ticket=701")>=0,
  "preview: tickets das duas posicoes aparecem separadamente");
 CheckPreview(ok&&StringFind(plan.lines,"CANDIDATO_NAO_ENVIADO")>=0,"preview: candidatos explicitamente nao enviados");
 string candidate=plan.journal_candidate;MDJournal610 original,simulated;
 string scope=MDContext612(123,"SINTETICO",1);
 CheckPreview(MDReplay610(journal,scope,"WINZ26",20261016,1,original)&&!original.r[0].cancel&&
  MDReplay610(candidate,scope,"WINZ26",20261016,1,simulated)&&simulated.r[0].cancel,
  "preview: diario candidato separado do diario observado");
 MDRecoveryEvidence67 certain;Market615C(certain);
 CheckPreview(MDPreviewIntegrado615(journal,stream,1,123,"SINTETICO",a,b,now,gate,certain,certain,certain,certain,certain,false,plan)&&
  plan.cancel==0&&plan.protect==2&&plan.close==0,"preview: evidencia sintetica completa nao cancela saldo valido");
 CheckPreview(MDPreviewIntegrado615(journal,stream,1,123,"SINTETICO",a,b,now,gate,certain,certain,certain,certain,certain,true,plan)&&
  plan.cancel==1&&plan.close==2&&plan.protect==0,"preview: corte sintetico inclui saldo e ambas posicoes");
 certain.exit_after_entry=true;certain.boundary_after_accept=true;
 CheckPreview(MDPreviewIntegrado615(journal,stream,1,123,"SINTETICO",a,b,now,gate,certain,certain,certain,certain,certain,false,plan)&&
  plan.cancel==1&&plan.close==2,"preview: fronteira posterior sintetica inclui cancelamento e fechamento");
 MDPreviewEvidenceUnknown(e,false);MDSnapshot69 unstable=b;unstable.p[0].ticket++;
 CheckPreview(!MDPreviewIntegrado615(journal,stream,1,123,"SINTETICO",a,unstable,now,gate,e,e,e,e,e,false,plan)&&!plan.valid,
  "preview: duas leituras divergentes rejeitadas");
 gate.snapshot_fresh=false;
 CheckPreview(!MDPreviewIntegrado615(journal,stream,1,123,"SINTETICO",a,b,now,gate,e,e,e,e,e,false,plan),"preview: leitura antiga bloqueada");
 MDTestGate615C(gate);gate.tick_size=1;
 CheckPreview(!MDPreviewIntegrado615(journal,stream,1,123,"SINTETICO",a,b,now,gate,e,e,e,e,e,false,plan),"preview: grade divergente bloqueada");
 MDTestGate615C(gate);gate.volume_step=0;
 CheckPreview(!MDPreviewIntegrado615(journal,stream,1,123,"SINTETICO",a,b,now,gate,e,e,e,e,e,false,plan),"preview: propriedades de volume invalidas bloqueadas");
 MDTestGate615C(gate);MDSnapshot69 twolevel=a;string journal_two;
 bool added=AddSecondLevelShadow(journal,journal_two,twolevel,stream);
 CheckPreview(added&&MDPreviewIntegrado615(journal_two,stream,1,123,"SINTETICO",twolevel,twolevel,now,gate,e,e,e,e,e,false,plan)&&
  plan.chains==2&&plan.cancel==2&&plan.protect==3&&plan.close==0,
  "preview: dois niveis e tres posicoes independentes");
 MDTestGate615C(gate);MDSnapshot69 empty=a;empty.orders=0;empty.deals=0;empty.positions=0;
 string header=MDHeader610(scope,"WINZ26",20261016,1);
 CheckPreview(MDPreviewIntegrado615(header,stream,1,123,"SINTETICO",empty,empty,now,gate,e,e,e,e,e,false,plan)&&
  plan.chains==0&&plan.plans==0&&StringFind(plan.lines,"NAO_AUTORIZA_ENTRADA")>=0,
  "preview: sem origem nao inventa ordens nem posicoes");
 CheckPreview(!MDPreviewIntegrado615(header,stream,1,123,"SINTETICO",a,b,now,gate,e,e,e,e,e,false,plan),
  "preview: magic sem origem nao e adotado");
 bool calculated=MDPreviewIntegrado615(journal,stream,1,123,"SINTETICO",a,b,now,gate,e,e,e,e,e,false,plan);
 string path="ModeloD_TEST_ONLY_615D_PREVIEW_"+suffix+".state";
 int lock=FileOpen(path+".lock",FILE_READ|FILE_WRITE|FILE_BIN|FILE_COMMON);bool loaded=false;string last="";long rev=0;
 bool stored=calculated&&lock!=INVALID_HANDLE&&MDPreviewSync(path,lock,loaded,last,journal,stream,plan,scope,1,rev,why);
 CheckPreview(stored&&rev==1&&why=="PREVIA_CRIADA","disco: preview e diario observacional gravados juntos");
 CheckPreview(stored&&MDPreviewSync(path,lock,loaded,last,journal,stream,plan,scope,1,rev,why)&&rev==1,
  "disco: leitura identica nao duplica revisao");
 MDPreviewIntegrado wrong=plan;wrong.source_journal=header;
 CheckPreview(!MDPreviewSync(path,lock,loaded,last,journal,stream,wrong,scope,1,rev,why),
  "disco: preview de outro diario nao e armazenada");
 if(lock!=INVALID_HANDLE){FileClose(lock);}
 loaded=false;last="";
 lock=FileOpen(path+".lock",FILE_READ|FILE_WRITE|FILE_BIN|FILE_COMMON);
 CheckPreview(lock!=INVALID_HANDLE&&MDPreviewSync(path,lock,loaded,last,journal,stream,plan,scope,1,rev,why)&&rev==1,
  "disco: reabertura recupera preview sem executar comando");
 string before=last;MDStream615 earlier=stream;earlier.cursor-=60000;
 CheckPreview(!MDPreviewSync(path,lock,loaded,last,journal,earlier,plan,scope,1,rev,why)&&last==before,
  "disco: horizonte anterior nao sobrescreve preview");
 int tmp=FileOpen(path+".tmp",FILE_WRITE|FILE_BIN|FILE_ANSI|FILE_COMMON,0,CP_UTF8);
 if(tmp!=INVALID_HANDLE){FileWriteString(tmp,"INTERRUPCAO");FileClose(tmp);}
 CheckPreview(tmp!=INVALID_HANDLE&&!MDPreviewSync(path,lock,loaded,last,journal,stream,plan,scope,1,rev,why)&&last==before,
  "disco: temporario pendente bloqueia substituicao");
 if(lock!=INVALID_HANDLE)FileClose(lock);
}
#endif
