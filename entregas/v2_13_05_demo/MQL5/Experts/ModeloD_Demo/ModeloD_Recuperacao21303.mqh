#ifndef MD_RECUPERACAO21303
#define MD_RECUPERACAO21303
bool MDRepairCandidate21303(const MDOpState &s,const MDOpSnapshot &snapshot,const MDOpFrame &f,
 int k,string journal,MDOpState &candidate,string &why) {
 why="NAO_E_CANCELAMENTO_DO_INCIDENTE";
 if(!MDRepairEligibleState21303(s,k))return false;
 MDOpLevel l=s.levels[k];
 if(!f.stable||!f.connected||!f.clock_ok||f.utc<s.watermark||f.utc>=l.cutoff_utc||
    MDDateValue614((datetime)(f.server/1000))!=20261105){why="INVENTARIO_RELOGIO_OU_DATA_NAO_VALIDOS";return false;}
 // entry_ready requires actual full reconstruction + raw current tail,
 // current adjustment and native properties. Never infer no-touch from absence.
 if(f.touched[k]||f.first_touch[k]>0){why="PRIMEIRO_TOQUE_JA_OCORREU";return false;}
 if(!f.entry_ready[k]){why="HISTORICO_ATE_AGORA_OU_GATES_NAO_CONFERIDOS";return false;}
 if(!MDRepairIncident21303(journal,l.level,s.scope,s.instance)){why="TRANSICAO_DEFEITUOSA_NAO_COMPROVADA_NO_DIARIO";return false;}
 MDOpState verified=s;
 if(!MDOpReconcile(verified,snapshot,f.utc,why)||MDOpEncode(verified)!=MDOpEncode(s)){
  why="RECIBOS_ATUAIS_AINDA_NAO_CONCILIADOS";return false;
 }
 candidate=s;MDRepairClear21303(candidate,k);candidate.watermark=f.utc;
 // Historical order must remain cancelled, have matching original properties
 // and comment, and have zero linked deals. Do not rearm an executed order.
 int found=-1;for(int j=0;j<snapshot.book.orders;j++)if(snapshot.book.o[j].order.ticket==l.order){if(found>=0)return false;found=j;}
 if(found<0||!MDRepairRetired21303(candidate,snapshot,found)){why="CANCELAMENTO_SEM_EXECUCAO_NAO_COMPROVADO";return false;}
 why="CANCELAMENTO_TECNICO_COMPROVADO_E_NIVEL_AINDA_SEM_TOQUE";return true;
}
string repair_last21303[5];
bool MDRepairBackup21303(string path,string journal,string scope,int instance) {
 string backup=path+".pre21303",saved;MDOpState check;
 if(FileIsExist(backup,FILE_COMMON))
  return MDOpReadFile(backup,saved)&&StringSubstr(journal,0,StringLen(saved))==saved&&MDOpReplay(saved,scope,instance,check);
 return MDOpWriteFile(backup,journal);
}
bool MDRepairRun21303(const MDOpFrame &f,const MDOpSnapshot &snapshot) {
 if(!MDDemoGate213()||!owns615||fatal||lock615==INVALID_HANDLE||Scope615()!=operational.scope||!MDRepairScope21303(operational))return false;
 for(int k=0;k<operational.nlevels;k++) {
  if(!MDRepairEligibleState21303(operational,k))continue;
  MDOpState candidate;string why;MDOpLevel l=operational.levels[k];
  bool ready=MDRepairCandidate21303(operational,snapshot,f,k,ledger,candidate,why);
  if(!ready){
   if(repair_last21303[l.level]!=why){Report615("REPAIR21303_BLOQUEADO;key="+IntegerToString(l.key)+";motivo="+why);repair_last21303[l.level]=why;}
   continue;
  }
  long archived=l.order;
  if(!MDRepairBackup21303(ledger_path,ledger,operational.scope,operational.instance)){
   Report615("REPAIR21303_BLOQUEADO;BACKUP_NAO_CONFIRMADO;DIARIO_PRESERVADO");return false;
  }
  if(!MDDemoGate213()||Scope615()!=operational.scope)return false;
  if(!Commit(candidate,"REPAIR21303_CANCEL_"+IntegerToString(archived)))return false;
  pending_trail_started[k]=false;
  Report615("REPAIR21303_CONFIRMADO;key="+IntegerToString(l.key)+";ordem_antiga="+IntegerToString(archived)+
   ";SEM_TOQUE_ATE_MSC="+IntegerToString(f.server)+";DIARIO_ANTERIOR_PRESERVADO;NOVO_ENVIO_EXIGE_NOVA_VALIDACAO");
  return true; // At most one recovery commit per timer; bounded work.
 }
 return false;
}
#endif
