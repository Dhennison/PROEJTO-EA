#property strict
#property version "2.133" // entrega 2.13.03
#property description "Modelo D: operacao exclusiva em conta DEMO Hedge BRL; conta real bloqueada."
#include "ModeloD_RuntimeDemo213.mqh"
#include "ModeloD_FonteDemo213.mqh"
#include "ModeloD_Observer.mqh"
#include "ModeloD_Chart.mqh"
#include "ModeloD_StreamTerminal.mqh"
#include "ModeloD_Retry132.mqh"
#include "ModeloD_OperationalTerminal.mqh"
#include "ModeloD_CurrentCoverage.mqh"
input int Instancia=1;
input int VolumePorNivel=1;
// Default approved volume 1; the later principal backtest uses 5.
input int IntervaloSegundos=2;
MDObserver615 obs615;MDStream615 stream615;MDRetry132 retry132;
MDOpState operational;MDOpSnapshot inventory_a,inventory_b;MDOpClock opclock;
MDOpTrail pending_trail[MDOP_LEVELS],position_trail[MDOP_POSITIONS];
bool pending_trail_started[MDOP_LEVELS],position_trail_started[MDOP_POSITIONS];
string coverage_last209="";
int lock615=INVALID_HANDLE,report615=INVALID_HANDLE;
bool owns615=false,fatal=false,report_error=false;
string ledger="",ledger_path="",last_status="",stream_status615="AGUARDANDO_DADOS";
string report_path="";string diagnostic_last[10];
long transactions=0;
bool stream_started615=false,stream_failed615=false;
int stream_retries615=0;long stream_reported615=-1;
bool marker_loaded615=false,marker_restored615=false;long marker_saved_cursor615=-1;
string marker_text615="",marker_path615="";
bool LockMarkerMatches(int handle,string expected,string &why) {
 ulong size=FileSize(handle);if(size==0){why="EMPTY";return false;}
 ResetLastError();
 if(!FileSeek(handle,0,SEEK_SET)){why="SEEK_FAILED;error="+IntegerToString(GetLastError());return false;}
 string actual=FileReadString(handle,(int)size);int error=GetLastError();
 if(error!=0){why="READ_FAILED;error="+IntegerToString(error);return false;}
 if(actual!=expected){why="CONTENT_MISMATCH;size="+IntegerToString((long)size);return false;}
 why="CONFIRMED";return true;
}
enum MDMode615 {DADOS_ATUAIS=0};const MDMode615 Modo=DADOS_ATUAIS;
string Scope615(){return MDContext612(MDAccount213(),MDServer213(),Instancia);}
void Report615(string text) {
 if(MDDemoGate213())StringReplace(text,";SEM_ORDENS",";COLETA_OBSERVACIONAL_DEMO");
 Print(text);
 if(report615==INVALID_HANDLE)return;
 ResetLastError();uint n=FileWriteString(report615,TimeToString(TimeLocal(),TIME_DATE|TIME_SECONDS)+";"+text+"\r\n");
 FileFlush(report615);int report_errno=GetLastError();
 if(n==0||report_errno!=0){
  if(!report_error)Print("RELATORIO_ESCRITA_FALHOU;erro=",report_errno,";arquivo=",report_path);
  report_error=true;
 }
}
// Diagnostic-only state; never persisted as trading evidence or used to release gates.
void Diagnostic(int channel,string component,string reason,string recovery) {
 if(channel<0||channel>=10)return;
 string line="DIAGNOSTICO;componente="+component+";motivo="+reason+";recuperacao="+recovery;
 if(diagnostic_last[channel]==line)return;
 diagnostic_last[channel]=line;Report615(line);
}
void Status(string text) {
 string policy="REAVALIA_NO_TIMER";
 if(stream_failed615)policy="SEM_NOVA_TENTATIVA_DE_TICKS_NESTA_SESSAO;EXIGE_DIAGNOSTICO";
 else if(retry132.active)policy=MDSlow132(retry132,MDLogicalMillis213())?"MONITORAMENTO_LENTO_120S;ENTRADAS_BLOQUEADAS":"RECONSULTA_BLOCO_30S;FASE_RAPIDA_600S";
 Diagnostic(4,"FLUXO_TICKS",stream_status615,policy);
 string mode="Observacao: ordens desativadas";
 if(MDDemoGate213())mode="Negociacao na conta de simulacao";
 else if(ExecutarNaDemo)mode="Negociacao bloqueada: "+MDDemoPermission213();
 Comment("MODELO D — DEMO v2.13\n",mode,"\n",stream_status615);
 if(text!=last_status){last_status=text;Report615(text);}
}
void TouchSummary615()
{
 string names[5]={"S38,2","S50","S61,8","R38,2","R61,8"};
 for(int i=0;i<5;i++)
 {
  MDTouchAudit t=stream615.audit.touches[i];MDLevel level=stream615.control.day.levels[i];
  Report615("TOQUE_6_15;data="+IntegerToString(stream615.data.date)+";contrato="+stream615.data.contract+
   ";nivel="+names[i]+";estado="+(t.tape.touched?"TOQUE_OBSERVADO":"SEM_TOQUE_NO_TRECHO_CONFERIDO")+
   ";primeiro_msc="+IntegerToString(t.tape.first_msc)+";last_anterior="+DoubleToString(t.previous_at_touch,6)+
   ";last_atual="+DoubleToString(t.last_at_touch,6)+";indice="+IntegerToString(t.index_at_touch)+
   ";entrada_matematica="+DoubleToString(level.entry,6)+";entrada_tick="+DoubleToString(level.entry_tick,0)+
   ";abertura_valida="+IntegerToString(level.valid_open?1:0)+";geometria_bloqueada="+IntegerToString(level.geometry_blocked?1:0)+
   ";ate_exclusivo_msc="+IntegerToString(stream615.cursor)+";NAO_E_EXECUCAO;SEM_ORDENS");
 }
}
void ReportQuery209(const MDQuery209 &q,bool accepted)
{
 if(!q.attempted)return;
 Report615("TICKS_CONSULTA;"+MDQueryTicksText209(q)+";consulta_confere="+IntegerToString(accepted?1:0));
 Report615("TICKS_REFERENCIA;"+MDQueryPricesText209(q));
}
void Pump615()
{
 if(!owns615||!obs615.visible||!obs615.frozen||obs615.conflict||obs615.identity_changed)return;
 if(Modo!=DADOS_ATUAIS){stream_status615="TICKS: REPRODUCAO FIXA SOMENTE VISUAL";return;}
 if(!stream_started615||stream615.data.date!=obs615.data.date)
 {
  MDReset132(retry132);
  stream_started615=MDStreamStart615(stream615,obs615.data);
  marker_loaded615=false;marker_restored615=false;marker_saved_cursor615=-1;marker_text615="";
  marker_path615=demo_prefix213+"ModeloD_OBSERVADO_615N_"+Scope615()+"_"+IntegerToString(obs615.data.date)+".dat";
  stream_failed615=!stream_started615;stream_retries615=0;stream_reported615=-1;
  Report615("TICKS_6_15_INICIO;data="+IntegerToString(obs615.data.date)+";contrato="+obs615.data.contract+";SEM_ORDENS");
 }
 if(stream_failed615){stream_status615="TICKS: BLOQUEADO — ENVIAR RELATORIO";return;}
 if(!MDDaySameData(stream615.data,obs615.data))
 {stream_failed615=true;Report615("TICKS_6_15_BLOQUEADO;DADOS_MUDARAM;SEM_ORDENS");return;}
 if(retry132.active&&MDLogicalMillis213()<retry132.started)
 {stream_failed615=true;Report615("TICKS_6_15_BLOQUEADO;RELOGIO_MONOTONICO_REGREDIU;SEM_ORDENS");return;}
 if(MDEnterSlow132(retry132,MDLogicalMillis213()))
  Report615("TICKS_6_15_MONITORAMENTO_LENTO;intervalo_s=120;de_msc="+IntegerToString(retry132.from)+
   ";ate_msc="+IntegerToString(retry132.end)+";ENTRADAS_BLOQUEADAS;NAO_REINICIA_PRAZOS;SEM_ORDENS");
 if(!MDConnected213()){stream_status615="TICKS: SEM CONEXAO";return;}
 if(!MDDue132(retry132,MDLogicalMillis213()))return;
 MqlTick latest;
 if(!MDSymbolInfoTick213(stream615.data.contract,latest)||latest.time_msc<stream615.audit.begin_msc)
 {stream_status615="TICKS: AGUARDANDO COTACAO DA SESSAO";return;}
 long target=MDStreamHorizon615(latest.time_msc,stream615.cutoff);
 if(target<stream615.cursor)
 {stream_failed615=true;Report615("TICKS_6_15_BLOQUEADO;TEMPO_REGREDIU;SEM_ORDENS");return;}
 // No maximo dois blocos por evento; nenhuma espera Sleep nem loop ate o presente.
 for(int b=0;b<2&&stream615.cursor<target&&!IsStopped();b++)
 {
  long end=stream615.cursor+299999;if(end>=target)end=target-1;
  if(retry132.active)end=retry132.end; // Reconsulta exatamente o bloco rejeitado.
  stream_reported615=-1; // Nenhum checkpoint/conciliacao enquanto falta este bloco.
  MDStream615 candidate=stream615;string why;
  long collect_began=(long)GetTickCount64();
  bool collected=MDStreamCollect615(candidate,end,why,true);
  Report615("TICKS_BLOCO;de_msc="+IntegerToString(stream615.cursor)+";ate_msc="+IntegerToString(end)+
   ";duracao_total_ms="+IntegerToString((long)GetTickCount64()-collect_began)+";consulta_confere="+IntegerToString(collected?1:0));
  ReportQuery209(query_trade209,collected&&!query_all209.attempted);
  ReportQuery209(query_all209,collected&&query_all209.attempted);
  if(!collected)
  {
   if(IsStopped())return;
   if(StringFind(why,"TICKS_DIVERGEM_M1;")==0)
   {
    bool waiting=MDFail132(retry132,stream615.cursor,end,MDLogicalMillis213());
    Report615("TICKS_6_15_RECUPERACAO;tentativa="+IntegerToString(retry132.failures)+";nova_consulta_em_s="+IntegerToString(retry132.slow?120:30)+";fase="+(retry132.slow?"MONITORAMENTO_LENTO":"RECUPERACAO_RAPIDA")+";decorrido_ms="+IntegerToString(MDLogicalMillis213()-retry132.started)+";motivo="+why+";SEM_ORDENS");
    if(!waiting){stream_failed615=true;Report615("TICKS_6_15_BLOQUEADO;RECUPERACAO_JANELA_OU_RELOGIO_DIVERGENTE;SEM_ORDENS");}
    stream_status615="TICKS: RECUPERACAO PENDENTE — SEM APROVAR BLOCO";return;
   }
   stream_retries615++;
   Report615("TICKS_6_15_RETRY;tentativa="+IntegerToString(stream_retries615)+";de_msc="+IntegerToString(stream615.cursor)+";motivo="+why+";SEM_ORDENS");
   if(stream_retries615>=3){stream_failed615=true;Report615("TICKS_6_15_BLOQUEADO;TRES_TENTATIVAS_SEM_BLOCO_VALIDO;SEM_ORDENS");}
   stream_status615=stream_failed615?"TICKS: BLOQUEADO — ENVIAR RELATORIO":"TICKS: AGUARDANDO NOVA TENTATIVA";return;
  }
  if(!MDCanCommit132(retry132,stream615.cursor,end,MDLogicalMillis213()))
  {stream_failed615=true;Report615("TICKS_6_15_BLOQUEADO;RECUPERACAO_JANELA_OU_RELOGIO_INVALIDO;SEM_ORDENS");return;}
  if(!MDConnected213()){stream_status615="TICKS: DESCONECTADO_APOS_COLETA";return;}
  if(!MDObserverIdentity615(obs615,Scope615()))
  {MDVisualClear(0,(uint)Instancia);stream_failed615=true;Report615("TICKS_6_15_BLOQUEADO;IDENTIDADE_MUDOU;SEM_ORDENS");return;}
  if(retry132.active)Report615("TICKS_6_15_RECUPERADO;de_msc="+IntegerToString(stream615.cursor)+";ate_msc="+IntegerToString(end)+";M1_DISPONIVEL_CONFERIDO;fase="+(retry132.slow?"MONITORAMENTO_LENTO":"RECUPERACAO_RAPIDA")+";SEM_ORDENS");
  bool new_touch=false;
  for(int i=0;i<5;i++)if(candidate.audit.touches[i].tape.touched&&!stream615.audit.touches[i].tape.touched)new_touch=true;
  MDReset132(retry132);stream615=candidate;stream_retries615=0;
  Report615("COBERTURA_615N;"+why+";SEM_ORDENS");
  Report615("TICKS_6_15_PROGRESSO;blocos="+IntegerToString(stream615.blocks)+";ticks="+IntegerToString(stream615.audit.count)+
   ";ate_exclusivo="+TimeToString((datetime)(stream615.cursor/1000),TIME_DATE|TIME_SECONDS)+";M1_DISPONIVEL_CONFERIDO;SEM_ORDENS");
  if(new_touch)TouchSummary615();
 }
 if(stream615.cursor==target&&stream615.audit.count>0)
 {
  stream_status615="TICKS: CONFERIDOS ATE "+TimeToString((datetime)(target/1000),TIME_SECONDS)+" (exclusivo)";
  if(stream_reported615!=target)
  {
   Report615("TICKS_6_15_ATUALIZADO;data="+IntegerToString(stream615.data.date)+";contrato="+stream615.data.contract+
    ";ate_exclusivo="+TimeToString((datetime)(target/1000),TIME_DATE|TIME_SECONDS)+";ticks="+IntegerToString(stream615.audit.count)+
    ";abertura_confere=1;M1_consistente=1;INTEGRIDADE_TOTAL_NAO_CERTIFICADA;SEM_ORDENS");
   TouchSummary615();stream_reported615=target;
  }
 }
 else stream_status615="TICKS: RECONSTRUINDO DESDE A ABERTURA";
}

string DataIdentity(const MDDataEvidence &d) {
 return IntegerToString(d.date)+"_"+d.contract+"_"+IntegerToString(d.open_msc)+"_"+
 DoubleToString(d.values.high_prev,16)+"_"+DoubleToString(d.values.low_prev,16)+"_"+
 DoubleToString(d.values.close_prev,16)+"_"+DoubleToString(d.values.open_today,16)+"_"+
 DoubleToString(d.values.adjustment,16)+"_"+DoubleToString(d.previous_adjustment,16)+"_"+
 IntegerToString(d.session.scheduled_open)+"_"+IntegerToString(d.session.cutoff)+"_"+
 IntegerToString(d.session.normal_end)+"_"+IntegerToString(d.expiry_date)+"_"+IntegerToString(d.source_date);
}
bool Commit(const MDOpState &next,string event) {
 if(MDOpEncode(next)==MDOpEncode(operational))return true;
 MDOpState candidate=next;if(opclock.ok&&opclock.utc>candidate.watermark)candidate.watermark=opclock.utc;
 string why;
 if(!MDOpCommitFile(ledger_path,lock615,ledger,operational,candidate,event,why)){
  fatal=true;Diagnostic(3,"PERSISTENCIA",why,"SEM_CONTINUACAO_NESTA_EXECUCAO;PRESERVAR_ARQUIVOS;RETOMADA_VALIDADA");Status("PERSISTENCIA_BLOQUEADA;"+why+";PRESERVAR_ARQUIVOS");return false;
 }
 Report615("COMMIT;revision="+IntegerToString(operational.revision)+";event="+event+";transporte=0");
 for(int i=0;i<operational.nlevels;i++){
  MDOpLevel l=operational.levels[i];
  Report615("LEVEL;key="+IntegerToString(l.key)+";symbol="+l.symbol+";origin="+IntegerToString(l.order)+
   ";accepted_server_msc="+IntegerToString(l.accepted_server)+";first_touch_server_msc="+IntegerToString(l.touch_server)+
   ";consumed="+IntegerToString(l.consumed?1:0)+";cutoff="+IntegerToString(l.cutoff?1:0)+";entry_math="+DoubleToString(l.prices.entry,16)+
   ";entry_requested="+DoubleToString(l.prices.entry_tick,0)+";SL_fixed="+DoubleToString(l.prices.sl_tick,0)+";TP_fixed="+DoubleToString(l.prices.tp_tick,0)+
   ";entry_phase="+IntegerToString(l.entry.phase)+";entry_attempt="+IntegerToString(l.entry.serial)+";cancel_phase="+IntegerToString(l.cancellation.phase));
 }
 for(int i=0;i<operational.npositions;i++){
  MDOpPosition v=operational.positions[i];
  Report615("POSITION;identifier="+IntegerToString(v.identifier)+";ticket="+IntegerToString(v.ticket)+";entered="+DoubleToString(v.entered,8)+
   ";exited="+DoubleToString(v.exited,8)+";residual="+DoubleToString(v.volume,8)+";SL_observed="+DoubleToString(v.sl,8)+";TP_observed="+DoubleToString(v.tp,8)+
   ";protection_attempt="+IntegerToString(v.protect.serial)+";close_phase="+IntegerToString(v.close.phase));
 }
 return true;
}
void Daily() {
 obs615.visible=false;
 if(!opclock.ok||opclock.offset!=-10800){
  stream_status615="DADOS: FUSO_SERVIDOR_B3_NAO_CONFIRMADO";
  Diagnostic(1,"DADOS_DIARIOS",!opclock.ok?"RELOGIO_NAO_VALIDADO":"FUSO_SERVIDOR_INCOMPATIVEL;offset_s="+IntegerToString(opclock.offset),
   !opclock.ok?"REAVALIA_APOS_RELOGIO_VALIDO":"EXIGE_VALIDACAO_DO_FUSO;SEM_CONVERSAO_SILENCIOSA");
  MDVisualClear(0,(uint)Instancia);return;
 }
 int date=MDDateValue614((datetime)(opclock.utc/1000-10800));MDDailyRaw614 raw;string why;
 bool read=MDCollectDaily614(date,raw,why);
 if(!MDObserverUpdate615(obs615,date,read,raw,why)){
  stream_status615="DADOS: "+obs615.reason;
  Diagnostic(1,"DADOS_DIARIOS",obs615.reason,
   obs615.conflict?"CONFLITO_PERSISTIDO;ENTRADAS_BLOQUEADAS_NA_SESSAO;GERENCIA_EXISTENTE_CONTINUA":"RELEITURA_NO_TIMER;DEPENDE_DE_DADOS_VALIDOS");
  MDVisualClear(0,(uint)Instancia);
  if(obs615.conflict){MDOpState conflict=operational;for(int i=0;i<conflict.nlevels;i++)if(conflict.levels[i].date==date)conflict.levels[i].conflict=true;Commit(conflict,"DAILY_CONFLICT");}
  return;
 }
 MDOpState next=operational;
 long cutoff=MDCivilMidnight2026(date)+(long)obs615.data.session.cutoff*1000+10800000;
 bool added=MDOpAddDay(next,date,obs615.data.contract,DataIdentity(obs615.data),obs615.control.day,obs615.data.open_msc,cutoff,VolumePorNivel,why);
 if(!Commit(next,added?"DAILY_DATA":"DAILY_CONFLICT"))return;
 if(!added){stream_status615="DADOS: "+why;Diagnostic(1,"DADOS_DIARIOS",why,"EXIGE_DIAGNOSTICO;NAO_APAGAR_ESTADO");return;}
 Diagnostic(1,"DADOS_DIARIOS","CONFERIDOS;data="+IntegerToString(date)+";contrato="+obs615.data.contract,
 "MONITORAMENTO_NO_TIMER;NAO_COMPROVA_EXECUCAO");
 datetime begin=(datetime)(MDCivilMidnight2026(date)/1000+obs615.data.session.scheduled_open);
 datetime end=(datetime)(MDCivilMidnight2026(date)/1000+obs615.data.session.cutoff);
 if(!MDVisualSync(0,(uint)Instancia,obs615.control.day,begin,end,true)){Report615("VISUAL_SYNC_FAILED");}
 Pump615();
}
bool EntryProperties(const MDOpLevel &l,string &property_reason) {
 property_reason="PROPRIEDADES_DO_SIMBOLO_INDISPONIVEIS";
 double tick=0,minvol=0,maxvol=0,step=0,ask=0,bid=0,point=0;long mode=0,orders=0,stops=0,freeze=0;
 if(!MDSymbolInfoDouble213(l.symbol,SYMBOL_TRADE_TICK_SIZE,tick)){property_reason="LEITURA_TICK_SIZE_FALHOU";return false;}
 if(tick!=5){property_reason="TICK_SIZE_DIVERGENTE;valor="+DoubleToString(tick,8);return false;}
 if(!MDSymbolInfoDouble213(l.symbol,SYMBOL_VOLUME_MIN,minvol)||!MDSymbolInfoDouble213(l.symbol,SYMBOL_VOLUME_MAX,maxvol)||
 !MDSymbolInfoDouble213(l.symbol,SYMBOL_VOLUME_STEP,step)||!MDSymbolInfoInteger213(l.symbol,SYMBOL_TRADE_MODE,mode)||
 !MDSymbolInfoInteger213(l.symbol,SYMBOL_ORDER_MODE,orders)||!MDSymbolInfoInteger213(l.symbol,SYMBOL_TRADE_STOPS_LEVEL,stops)||
 !MDSymbolInfoInteger213(l.symbol,SYMBOL_TRADE_FREEZE_LEVEL,freeze)||!MDSymbolInfoDouble213(l.symbol,SYMBOL_POINT,point)||
 !MDSymbolInfoDouble213(l.symbol,SYMBOL_ASK,ask)||!MDSymbolInfoDouble213(l.symbol,SYMBOL_BID,bid))return false;
 MDExecGate613 g;g.volume_min=minvol;g.volume_max=maxvol;g.volume_step=step;
 if(!MDVolume613(l.volume,g)){property_reason="VOLUME_FORA_DAS_REGRAS_DO_SIMBOLO";return false;}
 if((orders&SYMBOL_ORDER_LIMIT)==0||(orders&SYMBOL_ORDER_SL)==0||(orders&SYMBOL_ORDER_TP)==0){property_reason="TIPOS_LIMIT_SL_TP_NAO_PERMITIDOS";return false;}
 if(mode!=SYMBOL_TRADE_MODE_FULL&&(l.prices.buy?mode!=SYMBOL_TRADE_MODE_LONGONLY:mode!=SYMBOL_TRADE_MODE_SHORTONLY)){property_reason="DIRECAO_NAO_PERMITIDA_PELO_SIMBOLO";return false;}
 double distance=(double)stops*point;
 if(l.prices.buy?ask-l.prices.entry_tick<distance:l.prices.entry_tick-bid<distance){property_reason="DISTANCIA_ENTRADA_STOPS_LEVEL";return false;}
 if(MathAbs(l.prices.entry_tick-l.prices.sl_tick)<distance||MathAbs(l.prices.entry_tick-l.prices.tp_tick)<distance){property_reason="DISTANCIA_SL_TP_STOPS_LEVEL";return false;}
 double margin=0;ResetLastError();bool margin_ok=MDOrderCalcMargin213(l.prices.buy?ORDER_TYPE_BUY:ORDER_TYPE_SELL,l.symbol,l.volume,l.prices.entry_tick,margin);int margin_error=GetLastError();
 if(!margin_ok){property_reason="CALCULO_DE_MARGEM_FALHOU;erro="+IntegerToString(margin_error);return false;}
 if(!MathIsValidNumber(margin)||margin<0){property_reason="CALCULO_DE_MARGEM_RETORNOU_VALOR_INVALIDO";return false;}
 double free_margin=AccountInfoDouble(ACCOUNT_MARGIN_FREE);
 if(!MathIsValidNumber(free_margin)||free_margin<0){property_reason="MARGEM_LIVRE_INDISPONIVEL";return false;}
 if(margin>free_margin){property_reason="MARGEM_LIVRE_INSUFICIENTE";return false;}
 property_reason="PROPRIEDADES_CONFERIDAS";return true;
}
void BuildFrame(MDOpFrame &f,bool stable) {
 MDOpFrameReset(f,opclock.utc,opclock.server,opclock.ok,(bool)MDConnected213());f.stable=stable;
 bool current=obs615.visible&&stream_started615&&!stream_failed615&&!retry132.active&&
 stream_reported615==stream615.cursor&&stream615.data.date==obs615.data.date;
 bool opening_tail=MDDemoGate213()&&obs615.visible&&stream_started615&&!stream_failed615&&!retry132.active&&stream615.audit.count==0;
 if(opening_tail)current=true;
 bool live=false;string why="",coverage_reason="RECONSTRUCAO_AINDA_NAO_ATUALIZADA",coverage_details="";
 MDCoverage209 coverage;MDCoverageReset209(coverage);
 if(stream_failed615)coverage_reason="FLUXO_BLOQUEADO_EXIGE_DIAGNOSTICO";
 else if(retry132.active)coverage_reason=MDSlow132(retry132,MDLogicalMillis213())?"RECUPERACAO_EM_MONITORAMENTO_LENTO":"RECUPERACAO_DO_BLOCO_PENDENTE";
 else if(!obs615.visible)coverage_reason="DADOS_DIARIOS_NAO_CONFERIDOS";
 if(current)live=MDCurrentCoverage209(stream615,opclock.server,coverage,coverage_reason,coverage_details,opening_tail);
 string coverage_state=live?"CONFERIDA":coverage_reason;
 if(coverage_last209!=coverage_state){
  Report615("COBERTURA_ATUAL;estado="+coverage_state+";"+coverage_details);
  coverage_last209=coverage_state;
 }
 for(int k=0;k<operational.nlevels;k++) {
  MDOpLevel l=operational.levels[k];
  if(obs615.frozen&&l.date==obs615.data.date&&l.symbol==obs615.data.contract) {
   if(current){MDTap tap=stream615.audit.touches[l.level].tape;f.touched[k]=tap.touched;f.first_touch[k]=tap.touched?tap.first_msc:0;}
   if(live&&!f.touched[k]&&coverage.touched[l.level]){f.touched[k]=true;f.first_touch[k]=coverage.first[l.level];}
   string entry_reason="COBERTURA_ATE_AGORA_NAO_CONFERIDA;causa="+coverage_reason;
   f.entry_ready[k]=ExecutarNaDemo&&(_Symbol=="WIN$N"||_Symbol==l.symbol)&&live&&opclock.offset==-10800&&EntryProperties(l,entry_reason)&&!f.touched[k]&&
      opclock.utc<l.cutoff_utc&&l.date==MDDateValue614((datetime)(opclock.utc/1000-10800));
   if(_Symbol!="WIN$N"&&_Symbol!=l.symbol)entry_reason="GRAFICO_NAO_CORRESPONDE_AO_CONTRATO_ATUAL";
   else if(l.conflict)entry_reason="CONFLITO_DE_DADOS_CONGELADOS";
   else if(l.cutoff||opclock.utc>=l.cutoff_utc)entry_reason="HORARIO_DE_CORTE";
   else if(l.consumed)entry_reason="OPORTUNIDADE_CONSUMIDA";
   else if(l.prices.geometry_blocked)entry_reason="LADO_BLOQUEADO_PELA_GEOMETRIA";
   else if(!l.prices.valid_open)entry_reason="INVALIDADO_PELA_ABERTURA";
   else if(f.touched[k])entry_reason="PRIMEIRO_TOQUE_JA_OCORREU";
   else if(l.order>0)entry_reason="ORIGEM_JA_VINCULADA";
   else if(MDOpBusy(l.entry))entry_reason="TENTATIVA_OU_RESPOSTA_AGUARDA_CONCILIACAO";
   else if(f.entry_ready[k])entry_reason="GATES_DE_DADOS_CONFERIDOS;AINDA_EXIGE_CONCILIACAO_E_PERMISSAO_DEMO";
   Diagnostic(5+l.level,"ENTRADA_"+IntegerToString(l.level),entry_reason,"REAVALIA_SEM_REARMAR_CONSUMO_OU_TENTATIVA");
  }
  bool trail_needed=!stable;
  if(stable&&l.order>0){
   for(int j=0;j<inventory_b.book.orders;j++)if(inventory_b.book.o[j].order.ticket==l.order&&inventory_b.book.o[j].order.state==0)trail_needed=true;
   for(int p=0;p<operational.npositions;p++)if(operational.positions[p].owner==k&&operational.positions[p].volume>0)trail_needed=true;
  }
  if(l.order>0&&!trail_needed)f.pending_history[k]=true; // Terminal origin with no residual exposure needs no fresh tick replay.
  if(l.order>0&&trail_needed) {
   if(!pending_trail_started[k]||pending_trail[k].begin!=l.accepted_server){MDOpTrailInit(pending_trail[k],l.symbol,l.accepted_server,l.prices,true);pending_trail_started[k]=true;}
   // A freshly accepted order has no strictly post-origin interval yet.
   // Do not cancel it merely because the next simulated callback has the SAME time.
   if(MDDemoGate213()&&opclock.server==l.accepted_server)f.pending_history[k]=true;
   else f.pending_history[k]=MDOpTrailRead(pending_trail[k],opclock.server,why);
   f.pending_boundary[k]=pending_trail[k].boundary;
   if(!f.pending_history[k]&&why!="TRAIL_PREVIOUS_FAILURE")Report615("PENDING_HISTORY;key="+IntegerToString(l.key)+";"+why);
  }
 }
 if(!live)for(int k=0;k<operational.nlevels;k++)f.entry_ready[k]=false;
 for(int p=0;p<operational.npositions;p++) {
  MDOpPosition v=operational.positions[p];if(v.volume<=0)continue;MDOpLevel l=operational.levels[v.owner];
  if(!position_trail_started[p]){MDOpTrailInit(position_trail[p],l.symbol,v.first_server,l.prices);position_trail_started[p]=true;}
  f.position_history[p]=MDOpTrailRead(position_trail[p],opclock.server,why);f.position_boundary[p]=position_trail[p].boundary;
  if(!f.position_history[p])Report615("POSITION_HISTORY;identifier="+IntegerToString(v.identifier)+";"+why);
 }
}
#include "ModeloD_Recuperacao21303.mqh"
void OperationalCycle() {
 if(fatal||!owns615)return;
 string why;bool clock=MDOpClockRead(opclock,operational.watermark,why);
 Diagnostic(0,"RELOGIO",why,"REAVALIA_NO_TIMER;NAO_REINICIA_PRAZOS");
 // Persist timer deadlines BEFORE potentially slow history calls.
 bool due=false;
 if(clock) {
  for(int i=0;i<operational.nlevels;i++)if(!operational.levels[i].cutoff&&opclock.utc>=operational.levels[i].cutoff_utc)due=true;
  for(int i=0;i<operational.npositions;i++)if(operational.positions[i].volume>0&&!operational.positions[i].closing&&
    MDProtectionCloseRequired(operational.positions[i].protection,opclock.utc,
      operational.positions[i].sl==operational.levels[operational.positions[i].owner].prices.sl_tick))due=true;
 }
 if(due){
  MDOpFrame timer;MDOpFrameReset(timer,opclock.utc,opclock.server,true,(bool)MDConnected213());
  MDOpState timed;
  if(!MDOpCycle(operational,inventory_b,timer,timed,why)||!Commit(timed,"TIMER_DEADLINE"))return;
 }
 // Daily data failure never bypasses inventory, protection or timer-based cutoff processing.
 Daily();if(fatal)return;
 bool stable=false;long began=(long)GetTickCount64();
 datetime start=(datetime)(opclock.server/1000-86400);
 for(int i=0;i<operational.nlevels;i++) {
  datetime day=(datetime)(MDCivilMidnight2026(operational.levels[i].date)/1000);
  if(day<start)start=day;
 }
 string inventory_reason="DESCONECTADO";
 if(MDConnected213()) {
  if(!MDOpCollect(start,inventory_a,why))inventory_reason="PRIMEIRA_COLETA;"+why;
  else if(!MDOpCollect(start,inventory_b,why))inventory_reason="SEGUNDA_COLETA;"+why;
  else if(!MDOpSameSnapshot(inventory_a,inventory_b))inventory_reason="DUAS_LEITURAS_DIVERGENTES";
  else if((long)GetTickCount64()-began>3000)inventory_reason="COLETA_EXCEDEU_3000MS";
  else if(Scope615()!=operational.scope)inventory_reason="IDENTIDADE_MUDOU";
  else {stable=true;inventory_reason="DUAS_LEITURAS_CONFERIDAS";}
 }
 // Broker receipts may become provable only on this timer (e.g. setup time
 // has millisecond precision while the earlier snapshot clock had seconds).
 // Bind those origins BEFORE building acceptance-specific tick trails, just
 // as MDDemoFresh213 already does. An old frame with pending_history=false
 // must never be applied to an origin that was unknown when it was built.
 if(stable){
  MDOpState observed=operational;string receipt_reason;
  if(MDOpReconcile(observed,inventory_b,opclock.utc,receipt_reason)){
   if(!Commit(observed,"DEMO_TIMER_RECEIPT_RECONCILIATION"))return;
  }else{
   stable=false;inventory_reason="RECIBOS_AINDA_NAO_CONCILIADOS;"+receipt_reason;
  }
 }
 MDOpFrame frame;BuildFrame(frame,stable);
 if((long)GetTickCount64()-began>3000){frame.stable=false;inventory_reason="INVENTARIO_VENCEU_DURANTE_HISTORICO;LIMITE_3000MS;origem="+inventory_reason;}
 if(Scope615()!=operational.scope){frame.stable=false;inventory_reason="IDENTIDADE_MUDOU";}
 if(!MDConnected213()){frame.stable=false;inventory_reason="DESCONECTADO";}
 Diagnostic(2,"INVENTARIO",inventory_reason,"NOVA_DUPLA_LEITURA_NO_TIMER;NAO_CONFIRMA_ACAO_POR_AUSENCIA");
 if(frame.stable&&MDDemoGate213()&&(long)GetTickCount64()-began<=3000){
  if(MDRepairRun21303(frame,inventory_b))BuildFrame(frame,stable);
  if(fatal)return;
  if((long)GetTickCount64()-began>3000)frame.stable=false;
 }
 MDOpState next;
 if(!MDOpCycle(operational,inventory_b,frame,next,why)){Status("CYCLE_BLOCKED;"+why);return;}
 if(!Commit(next,"INTEGRATED_CYCLE"))return;
 int entries=0,protect=0,cancel=0,close=0,uncertain=0;
 for(int i=0;i<operational.nlevels;i++){
  if(operational.levels[i].entry.phase==1)entries++;
  if(operational.levels[i].cancellation.phase==1)cancel++;
  if(MDOpBusy(operational.levels[i].entry)||MDOpBusy(operational.levels[i].cancellation))uncertain++;
 }
 for(int i=0;i<operational.npositions;i++){
  if(operational.positions[i].protect.phase==1)protect++;
  if(operational.positions[i].close.phase==1)close++;
  if(MDOpBusy(operational.positions[i].protect)||MDOpBusy(operational.positions[i].close))uncertain++;
 }
 Diagnostic(3,"CONCILIACAO",why,"REAVALIA_NO_TIMER;ORIGENS_E_EFEITOS_EXIGEM_PROVA");
 Status("INTEGRATED;"+why+";revision="+IntegerToString(operational.revision)+";entry_intents="+IntegerToString(entries)+
 ";SLTP_intents="+IntegerToString(protect)+";cancel_intents="+IntegerToString(cancel)+";close_intents="+IntegerToString(close)+
 ";unresolved="+IntegerToString(uncertain)+";transport="+(MDDemoGate213()?"DEMO_ONLY":"OBSERVACAO")+";HOMOLOGACAO_NATIVA_DEMO_PENDENTE");
}
// Each native request must match the SAME durable in-flight action and owned origin.
bool MDDemoOwnedRequest213(const MqlTradeRequest &r)
{
 if(!owns615||fatal||lock615==INVALID_HANDLE||Scope615()!=operational.scope)return false;
 for(int k=0;k<operational.nlevels;k++){
  MDOpLevel l=operational.levels[k];
  if(r.symbol!=l.symbol||r.magic!=(ulong)MDMagic67(operational.instance,l.level)||r.comment!=MDOpComment(l))continue;
  if(r.action==TRADE_ACTION_PENDING){
   return l.entry.phase==2&&!l.consumed&&!l.cutoff&&!l.conflict&&l.order==0&&
    (long)TimeGMT()*1000<l.cutoff_utc&&l.date==MDDateValue614(TimeTradeServer())&&
    r.order==0&&r.position==0&&r.volume==l.volume&&r.price==l.prices.entry_tick&&
    r.sl==l.prices.sl_tick&&r.tp==l.prices.tp_tick&&r.type==(l.prices.buy?ORDER_TYPE_BUY_LIMIT:ORDER_TYPE_SELL_LIMIT);
  }
  if(r.action==TRADE_ACTION_REMOVE&&r.order>0&&r.order==(ulong)l.order&&l.cancellation.phase==2&&
     l.cancellation.ticket==l.order&&r.position==0)return true;
  for(int p=0;p<operational.npositions;p++){
   MDOpPosition v=operational.positions[p];
   if(v.owner!=k||v.volume<=0||v.identifier<=0||v.ticket<=0||r.position!=(ulong)v.ticket||r.order!=0)continue;
   if(r.action==TRADE_ACTION_SLTP&&v.protect.phase==2&&v.protect.ticket==v.ticket&&
      r.sl==l.prices.sl_tick&&r.tp==l.prices.tp_tick)return true;
   if(r.action==TRADE_ACTION_DEAL&&v.close.phase==2&&v.close.ticket==v.ticket&&
      r.volume==v.volume&&r.sl==0&&r.tp==0&&r.type==(l.prices.buy?ORDER_TYPE_SELL:ORDER_TYPE_BUY))return true;
  }
 }
 return false;
}
#include "ModeloD_TransporteDemo213.mqh"
int OnInit() {
 string account_reason;
 Print("DEMO213_CONTA;mode=",AccountInfoInteger(ACCOUNT_TRADE_MODE),";margin_mode=",AccountInfoInteger(ACCOUNT_MARGIN_MODE),";currency=",AccountInfoString(ACCOUNT_CURRENCY),";server=",MDServer213());
 if(!MDDemoAccount213(account_reason)){Print("DEMO_INIT_BLOCKED;",account_reason);return INIT_PARAMETERS_INCORRECT;}
 demo_bound_account213=MDAccount213();demo_bound_server213=MDServer213();
 fatal=false;report_error=false;last_status="";
 stream_started615=false;stream_failed615=false;stream_retries615=0;stream_reported615=-1;
 marker_loaded615=false;marker_restored615=false;marker_saved_cursor615=-1;marker_text615="";marker_path615="";
 opening208.symbol="";
 demo_prefix213="MDD213_DEMO_";ledger="";
 demo_native_called213=false;demo_prepared213=0;demo_sent213=0;demo_responses213=0;demo_deals213=";";
 for(int i=0;i<256;i++)demo_blocks213[i]="";
 for(int i=0;i<MDOP_LEVELS;i++)pending_trail_started[i]=false;
 for(int i=0;i<MDOP_POSITIONS;i++)position_trail_started[i]=false;
 for(int i=0;i<10;i++)diagnostic_last[i]="";
 coverage_last209="";
 if(IntervaloSegundos!=2){Print("DEMO_TIMER_DEVE_SER_2S");return INIT_PARAMETERS_INCORRECT;}
 if(Instancia<1||Instancia>9999||VolumePorNivel<1||VolumePorNivel>1000000||IntervaloSegundos<1||IntervaloSegundos>30)return INIT_PARAMETERS_INCORRECT;
 long chart_custom=1;
 if(!SymbolInfoInteger(_Symbol,SYMBOL_CUSTOM,chart_custom)||chart_custom!=0){Print("DEMO_CHART_CUSTOM_BLOCKED");return INIT_PARAMETERS_INCORRECT;}
 // Daily metadata may be temporarily absent after restart. Recover known exposure first.
 if(_Symbol!="WIN$N"&&(!MDB3Symbol(_Symbol)||MDWINLastTrading2026(_Symbol)==0)){
  Print("DEMO_GRAFICO_DEVE_SER_WIN_N_OU_CONTRATO_WIN_REAL");return INIT_PARAMETERS_INCORRECT;
 }
 string scope=Scope615();if(scope=="")return INIT_FAILED;
 lock615=FileOpen(demo_prefix213+"ModeloD_OPERATIONAL_"+scope+".lock",FILE_READ|FILE_WRITE|FILE_BIN|FILE_COMMON);
 if(lock615==INVALID_HANDLE){Print("EXCLUSIVE_LOCK_FAILED");return INIT_FAILED;}
 string lock_marker="MDOP_LOCK_V1_"+scope;
 bool initialized=FileSize(lock615)>0;
 string marker_why;
 if(initialized&&!LockMarkerMatches(lock615,lock_marker,marker_why)){Print("LOCK_MARKER_INVALID;",marker_why);return INIT_FAILED;}
 if(initialized&&!FileIsExist(demo_prefix213+"ModeloD_OPERATIONAL_"+scope+".ledger",FILE_COMMON)&&!FileIsExist(demo_prefix213+"ModeloD_OPERATIONAL_"+scope+".ledger.next",FILE_COMMON)){
  Print("PREVIOUS_LEDGER_MISSING_RESTORE_BACKUP_NEVER_REINITIALIZE");return INIT_FAILED;
 }
 owns615=true;MDOpInit(operational,scope,Instancia);MDOpClockInit(opclock);MDObserverStart615(obs615,scope);MDReset132(retry132);
 ledger_path=demo_prefix213+"ModeloD_OPERATIONAL_"+scope+".ledger";string why;
 bool previous_ledger=FileIsExist(ledger_path,FILE_COMMON)||FileIsExist(ledger_path+".next",FILE_COMMON);
 if(previous_ledger) {
  if(!MDOpRecoverFile(ledger_path,scope,Instancia,ledger,operational,why)){Print("LEDGER_BLOCKED;",why,";PRESERVE_FILES");return INIT_FAILED;}
 }
 report_path=demo_prefix213+"ModeloD_Integrado_"+scope+"_"+IntegerToString((long)TimeLocal())+"_"+IntegerToString((long)GetTickCount64())+".txt";
 report615=FileOpen(report_path,
 FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_COMMON|FILE_SHARE_READ,0,CP_UTF8);
 if(report615==INVALID_HANDLE){Print("RELATORIO_ABERTURA_FALHOU;erro=",GetLastError());return INIT_FAILED;}
 Report615("RELATORIO_ABERTO;"+TerminalInfoString(TERMINAL_COMMONDATA_PATH)+"\\Files\\"+report_path);
 if(ledger=="") {
  MDOpState seed=operational;
  if(!MDOpCommitFile(ledger_path,lock615,ledger,operational,seed,"CREATED",why)){Print("LEDGER_CREATE_FAILED;",why);return INIT_FAILED;}
 }
 if(!initialized){
  ResetLastError();
  if(!FileSeek(lock615,0,SEEK_SET)){Print("LOCK_MARKER_WRITE_FAILED;SEEK;error=",GetLastError());return INIT_FAILED;}
  uint marker_bytes=FileWriteString(lock615,lock_marker,StringLen(lock_marker));FileFlush(lock615);int marker_error=GetLastError();
  bool marker_confirmed=marker_error==0&&marker_bytes>0&&LockMarkerMatches(lock615,lock_marker,marker_why);
  if(!marker_confirmed){Print("LOCK_MARKER_WRITE_FAILED;bytes=",marker_bytes,";chars=",StringLen(lock_marker),";error=",marker_error,";readback=",marker_why);return INIT_FAILED;}
 }
 Diagnostic(3,"PERSISTENCIA",previous_ledger?"DIARIO_REABERTO_VALIDADO":"DIARIO_INICIAL_CRIADO",
 "ESTADO_PRESERVADO;NAO_AUTORIZA_TRANSPORTE");
 string start_line="START;v=2.13.03_DEMO;ACCOUNT_TRADE_MODE_DEMO_ONLY;";
 Report615(start_line+MDDemoPermission213()+";revision="+IntegerToString(operational.revision));
 Report615("DEMO_CONFIG;contrato_por_descricao_WIN_N;ajuste=Common\\Files\\ajuste_b3.txt;diario_persistente_por_conta_servidor_instancia;WIN_2026;CORTE18_BRT;GRADE_GENERICA_DEMO_SEPARADA_DA_JANELA_MODELO_D");
 if(!EventSetTimer(IntervaloSegundos))return INIT_FAILED;
 return INIT_SUCCEEDED;
}
void OnTimer(){
 if(!MDDemoIdentity213()||Scope615()!=operational.scope){
  fatal=true;Diagnostic(3,"IDENTIDADE","CONTA_SERVIDOR_OU_MODO_ALTERADO","TRANSPORTE_BLOQUEADO;DIARIO_PRESERVADO");Status("IDENTITY_CHANGED");return;
 }
 OperationalCycle();
 if(MDDemoGate213())MDDemoDispatch213();
 else MDDemoBlocked213(255,MDDemoPermission213());
}
void OnTradeTransaction(const MqlTradeTransaction &trans,const MqlTradeRequest &request,const MqlTradeResult &result){transactions++;}
void OnChartEvent(const int id,const long &lparam,const double &dparam,const string &sparam) {
 if(id!=CHARTEVENT_CHART_CHANGE||!obs615.visible||!owns615)return;
 datetime begin=(datetime)(MDCivilMidnight2026(obs615.data.date)/1000+obs615.data.session.scheduled_open);
 datetime end=(datetime)(MDCivilMidnight2026(obs615.data.date)/1000+obs615.data.session.cutoff);
 MDVisualSync(0,(uint)Instancia,obs615.control.day,begin,end,true);
}
void OnDeinit(const int reason) {
 EventKillTimer();if(owns615)Report615("DEMO_END;prepared="+IntegerToString(demo_prepared213)+";sent="+IntegerToString(demo_sent213)+";responses="+IntegerToString(demo_responses213)+";revision="+IntegerToString(operational.revision)+";HOMOLOGACAO_DEMO_NAO_LIBERA_REAL");if(owns615){MDVisualClear(0,(uint)Instancia);Comment("");Report615("STOP;reason="+IntegerToString(reason)+";transport="+(MDDemoGate213()?"DEMO_ONLY":"ABSENT"));}
 if(report615!=INVALID_HANDLE){FileClose(report615);report615=INVALID_HANDLE;Print(report_error?"RELATORIO_COM_ERRO;":"RELATORIO_FECHADO;",TerminalInfoString(TERMINAL_COMMONDATA_PATH),"\\Files\\",report_path);}
 if(lock615!=INVALID_HANDLE){FileClose(lock615);lock615=INVALID_HANDLE;}owns615=false;
}
