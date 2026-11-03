#ifndef MD_OBSERVATION_CASES615N
#define MD_OBSERVATION_CASES615N
#include "ModeloD_ReadinessCases615M.mqh"
#include "ModeloD_ObservationBridge615N.mqh"
#include "ModeloD_SparseM1615N.mqh"
int checks615N=0,failures615N=0;string log615N="";
void Check615N(bool ok,string name){checks615N++;if(!ok)failures615N++;log615N+=(ok?"PASS: ":"FAIL: ")+name+"\r\n";}
void ObservationFixture615N(MDObservation615N &s)
{
 s.account=123;s.expected_account=123;s.now_ms=1100;s.snapshot_ms=1000;s.server="SINTETICO";s.expected_server="SINTETICO";s.scope="TEST_ONLY_615C";s.domain="RAW_N";s.date=20261016;
 s.connected=true;s.lock_held=true;s.daily_valid=true;s.calendar_valid=true;s.closed_minutes_checked=true;s.review_current=true;s.shadow_saved=true;
 s.session_open=true;s.cutoff=false;s.level_eligible=true;s.properties_valid=true;s.tick_size=5;s.volume_min=1;s.volume_max=1000;s.volume_step=1;
}
void Run615N(string suffix)
{
 Run615M(suffix);checks615N=checks615M;failures615N=failures615M;log615N=log615M;
 MDObservation615N s;MDDecision615M decision;MDJournal610 j;MDReplay610(Header615C(),"TEST_ONLY_615C","WINZ26",20261016,1,j);ObservationFixture615N(s);
 MDObservationGate615N(j,s,decision);
 Check615N(!decision.plan_allowed&&!decision.transport_allowed,"N: observacao totalmente preenchida nao vira permissao operacional");
 Check615N(StringFind(decision.reason,"ESTADO_OU_INTENCAO_NAO_DURAVEL")>=0,"N: checkpoint shadow nao substitui diario operacional");
 Check615N(StringFind(decision.reason,"HISTORICO_DE_TOQUES_PENDENTE")>=0,"N: minutos fechados nao certificam ticks ate o instante atual");
 Check615N(StringFind(decision.reason,"RELOGIO_NAO_CERTIFICADO")>=0,"N: hora estimada do servidor nao certifica UTC");
 Check615N(StringFind(decision.reason,"TENTATIVA_DA_ACAO_AINDA_INCERTA")>=0,"N: falta de produtor de tentativas nao e resolucao implicita");
 Check615N(StringFind(decision.reason,"CONCILIACAO_PENDENTE")<0,"N: revisao observacional atual reconhecida separadamente");
 s.review_current=false;MDObservationGate615N(j,s,decision);
 Check615N(StringFind(decision.reason,"CONCILIACAO_PENDENTE")>=0,"N: revisao antiga nao persiste como atual no proximo ciclo");
 ObservationFixture615N(s);s.now_ms=4001;MDObservationGate615N(j,s,decision);
 Check615N(StringFind(decision.reason,"LEITURA_ANTIGA_OU_ORIGEM_TEMPORAL_DIVERGENTE")>=0,"N: coleta lenta nao satisfaz frescor");
 ObservationFixture615N(s);s.account=999;MDObservationGate615N(j,s,decision);
 Check615N(StringFind(decision.reason,"IDENTIDADE_DIVERGENTE")>=0,"N: troca de conta permanece bloqueada");
 ObservationFixture615N(s);s.daily_valid=false;s.calendar_valid=false;s.session_open=false;MDObservationGate615N(j,s,decision);
 Check615N(StringFind(decision.reason,"DADOS_DIARIOS_PENDENTES")>=0&&StringFind(decision.reason,"CALENDARIO_PENDENTE")>=0&&StringFind(decision.reason,"FORA_DA_JANELA_DE_ENTRADA")>=0,"N: dia sem dados mostra todos os motivos");
 ObservationFixture615N(s);s.connected=false;MDObservationGate615N(j,s,decision);
 Check615N(StringFind(decision.reason,"DESCONECTADO")>=0,"N: desconexao aparece no relatorio");
 ObservationFixture615N(s);s.level_eligible=false;MDObservationGate615N(j,s,decision);
 Check615N(StringFind(decision.reason,"NIVEL_INELEGIVEL")>=0,"N: nivel consumido ou bloqueado nao e rearmado");
 ObservationFixture615N(s);s.properties_valid=false;MDObservationGate615N(j,s,decision);
 Check615N(StringFind(decision.reason,"PROPRIEDADES_NAO_VALIDADAS")>=0,"N: falha de leitura das propriedades nao vira valor padrao valido");
 string line=MDObservationLine615N(0,s,decision);
 Check615N(StringFind(line,"plano_entrada=0;transporte=0")>=0&&StringFind(line,"estado_shadow_gravado=1")>=0,"N: relatorio separa observacao persistida de permissao");
 log615N+=line+"\r\n";
 MDSessionRule rule;
 for(int date=20261026;date<=20261030;date++)
  Check615N(MDSession614(date,"WINZ26",rule)&&rule.scheduled_open==32400&&rule.normal_end==66300&&rule.cutoff==64800,"N101: grade revisada "+IntegerToString(date));
 Check615N(!MDSession614(20261031,"WINZ26",rule),"N101: nao extrapola para sabado");
 Check615N(!MDSession614(20261103,"WINZ26",rule),"N101: nao extrapola para novembro");
 Check615N(!MDSession614(20261026,"WINV26",rule),"N101: nao aceita contrato diferente");

 MDMinuteAudit minute;minute.count=0;minute.o=0;minute.h=0;minute.l=0;minute.c=0;
 Check615N(MDSparseMinute615N(minute,0,0,0,0,0,true),"N102: ausencia conjunta registrada em observacao");
 Check615N(!MDSparseMinute615N(minute,0,0,0,0,0,false),"N102: modo estrito nao relaxado");
 Check615N(!MDSparseMinute615N(minute,1,100,100,100,100,true),"N102: candle sem ticks rejeitado");
 minute.count=2;minute.o=100;minute.h=105;minute.l=95;minute.c=100;
 Check615N(!MDSparseMinute615N(minute,0,0,0,0,0,true),"N102: ticks sem candle rejeitados");
 Check615N(MDSparseMinute615N(minute,1,100,105,95,100,true),"N102: OHLC existente conferido");
 Check615N(!MDSparseMinute615N(minute,1,100,105,95,105,true),"N102: fechamento divergente rejeitado");
 Check615N(!MDSparseMinute615N(minute,2,100,105,95,100,true),"N102: candle duplicado rejeitado");
 Check615N(!MDSparseMinute615N(minute,-1,0,0,0,0,true),"N102: retorno de erro rejeitado");
 Check615N(MDSparseStamp615N(180000,0,299999,-1),"N102: primeiro candle pode ser no quarto minuto");
 Check615N(!MDSparseStamp615N(180000,0,299999,180000),"N102: timestamps iguais rejeitados");
 Check615N(!MDSparseStamp615N(120000,0,299999,180000),"N102: regressao M1 rejeitada");
 Check615N(!MDSparseStamp615N(300000,0,299999,-1),"N102: candle apos janela rejeitado");
 Check615N(!MDSparseStamp615N(60001,0,299999,-1),"N102: minuto desalinhado rejeitado");
 MDDailyRaw614 raw;MDObserverFixture615(raw);MDDataEvidence data;string why;
 bool built=MDDailyBuild614(raw,data,why);MDStream615 stream;
 bool started=built&&MDStreamStart615(stream,data);long begin=stream.cursor;
 stream.data.open_msc=begin+360000;
 Check615N(started&&MDStreamBegin615(stream,begin,begin+299999),"N102: bloco anterior a abertura tardia iniciado");
 MDStream615 strict=stream;
 Check615N(!MDSparseFinish615N(strict,false)&&strict.cursor==begin,"N102: bloco vazio nao avanca modo estrito");
 Check615N(MDSparseFinish615N(stream,true)&&stream.cursor==begin+300000&&stream.audit.count==0,"N102: bloco vazio observacional avanca sem inventar tick");
 Check615N(!stream.audit.touches[0].tape.touched,"N102: bloco vazio nao inventa toque");
 Check615N(MDStreamBegin615(stream,stream.cursor,begin+599999)&&MDStreamPush615(stream,begin+360000,data.values.open_today),"N102: primeiro tick real apos bloco vazio mantem abertura");
 Check615N(MDSparseFinish615N(stream,true)&&stream.audit.count==1,"N102: bloco com abertura real concluido");
 MDStream615 invalid=strict;invalid.data.open_msc=begin+1000;
 Check615N(!MDSparseFinish615N(invalid,true),"N102: abertura esperada dentro do vazio nao e ignorada");
 invalid=strict;invalid.audit.valid=false;
 Check615N(!MDSparseFinish615N(invalid,true),"N102: auditoria invalida nao avanca");
 MDStream615 gap=stream;long gapfrom=gap.cursor;
 Check615N(MDStreamBegin615(gap,gapfrom,gapfrom+59999)&&MDSparseFinish615N(gap,true)&&gap.audit.count==stream.audit.count,"N102: pausa intermediaria nao cria tick");

}
#endif
