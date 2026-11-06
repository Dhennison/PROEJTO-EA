#ifndef MD_RETOMADA21305
#define MD_RETOMADA21305
bool MDRearmCandidate21305(const MDOpState &s,const MDOpSnapshot &snapshot,const MDOpFrame &f,int k,
 MDOpState &candidate,string &why) {
 why="ORIGEM_NAO_ELEGIVEL_A_REENVIO";if(!MDRearmEligible21305(s,k))return false;MDOpLevel l=s.levels[k];
 if(!f.stable||!f.connected||!f.clock_ok||f.utc<s.watermark||f.utc>=l.cutoff_utc||
    l.date!=MDDateValue614((datetime)(f.server/1000))){why="CONTA_RELOGIO_INVENTARIO_OU_CORTE";return false;}
 if(!f.entry_ready[k]||f.touched[k]||f.first_touch[k]>0||f.pending_boundary[k]){
  why="SEM_PROVA_ATUAL_DE_NIVEL_INTACTO";return false;
 }
 MDOpState verified=s;
 if(!MDOpReconcile(verified,snapshot,f.utc,why)||MDOpEncode(verified)!=MDOpEncode(s)){
  why="RECIBOS_AINDA_NAO_CONCILIADOS";return false;
 }
 int found=-1;for(int j=0;j<snapshot.book.orders;j++)if(snapshot.book.o[j].order.ticket==l.order){if(found>=0)return false;found=j;}
 if(found<0){why="CANCELAMENTO_NAO_COMPROVADO";return false;}
 MDRawOrder69 o=snapshot.book.o[found];MDOpOrderExtra x=snapshot.orders[found];
 if(o.order.state!=1||o.order.remaining!=l.volume||!MDOpOrderMatch(l,o,x,s.instance)||
    x.sl!=l.prices.sl_tick||x.tp!=l.prices.tp_tick||x.comment!=MDOpComment(l)||x.position_id!=0){
  why="ORDEM_NAO_CANCELADA_INTEGRALMENTE_SEM_EXECUCAO";return false;
 }
 for(int d=0;d<snapshot.book.deals;d++)if(snapshot.book.d[d].order==l.order){why="HA_EXECUCAO_INCLUSIVE_PARCIAL";return false;}
 candidate=s;MDRearmClear21305(candidate,k);candidate.watermark=f.utc;why="CANCELADA_SEM_EXECUCAO_E_SEM_TOQUE";return true;
}
bool MDArchiveCandidate21305(const MDOpState &s,const MDOpSnapshot &snapshot,const MDOpFrame &f,int date,
 MDOpState &candidate,string &why) {
 why="SESSAO_NAO_TERMINAL";
 if(!f.stable||!f.connected||!f.clock_ok||f.utc<s.watermark||
    date>=MDDateValue614((datetime)(f.server/1000))||!MDArchiveEligible21305(s,date))return false;
 MDOpState verified=s;
 if(!MDOpReconcile(verified,snapshot,f.utc,why)||MDOpEncode(verified)!=MDOpEncode(s))return false;
 for(int k=0;k<s.nlevels;k++)if(s.levels[k].date==date){
  MDOpLevel l=s.levels[k];if(f.utc<l.cutoff_utc)return false;
  if(l.order>0){bool terminal=false;
   for(int j=0;j<snapshot.book.orders;j++)if(snapshot.book.o[j].order.ticket==l.order)terminal=snapshot.book.o[j].order.state!=0;
   if(!terminal)return false;
  }
 }
 candidate=s;MDArchiveClear21305(candidate,date);candidate.watermark=f.utc;why="SESSAO_FECHADA_RECIBOS_PRESERVADOS_NO_DIARIO";return true;
}
bool MDBackup21305() {
 string path=ledger_path+".pre21305",saved;MDOpState decoded;
 if(FileIsExist(path,FILE_COMMON))return MDOpReadFile(path,saved)&&StringSubstr(ledger,0,StringLen(saved))==saved&&
  MDOpReplay(saved,operational.scope,operational.instance,decoded)&&MDOpReplay(ledger,operational.scope,operational.instance,decoded);
 return MDOpWriteFile(path,ledger);
}
bool MDRetomadaRun21305(const MDOpFrame &f,const MDOpSnapshot &snapshot,bool archive_ready=true) {
 if(!MDDemoGate213()||fatal||!owns615||lock615==INVALID_HANDLE||Scope615()!=operational.scope)return false;
 MDOpState next;string why;
 // Release only past, closed working slots. No receipt or old revision is erased.
 if(archive_ready)for(int k=0;k<operational.nlevels;k++){
  int date=operational.levels[k].date;
  if(!MDArchiveCandidate21305(operational,snapshot,f,date,next,why))continue;
  if(!MDBackup21305()||!MDDemoGate213())return false;
  if(!Commit(next,"ARCHIVE21305_"+IntegerToString(date)))return false;
  for(int j=0;j<MDOP_LEVELS;j++)pending_trail_started[j]=false;
  for(int p=0;p<MDOP_POSITIONS;p++)position_trail_started[p]=false;
  Report615("ARCHIVE21305_CONFIRMADO;data="+IntegerToString(date)+";RECIBOS_E_REVISOES_PRESERVADOS;SLOTS_ATIVOS_REUTILIZAVEIS");return true;
 }
 for(int k=0;k<operational.nlevels;k++){
  if(!MDRearmCandidate21305(operational,snapshot,f,k,next,why))continue;
  MDOpLevel l=operational.levels[k];long native_state=0;
  // Native state distinguishes an actual cancellation from expiry/rejection.
  if(!HI69((ulong)l.order,ORDER_STATE,native_state)||native_state!=ORDER_STATE_CANCELED){
   Report615("REARM21305_BLOQUEADO;key="+IntegerToString(l.key)+";CANCELAMENTO_NATIVO_NAO_CONFIRMADO");continue;
  }
  if(!MDBackup21305()||!MDDemoGate213())return false;
  if(!Commit(next,"REARM21305_"+IntegerToString(l.key)+"_"+IntegerToString(l.order)))return false;
  pending_trail_started[k]=false;
  Report615("REARM21305_CONFIRMADO;key="+IntegerToString(l.key)+";ordem_antiga="+IntegerToString(l.order)+
   ";SEM_TOQUE_SEM_EXECUCAO;NOVO_PEDIDO_EXIGE_REVALIDACAO;DIARIO_PRESERVADO");return true;
 }
 return false;
}
#endif
