#ifndef MD_RECUPERACAO21304
#define MD_RECUPERACAO21304
bool MDRepairCandidate21304(const MDOpState &s,const MDOpSnapshot &snapshot,const MDOpFrame &f,
 string journal,MDOpState &candidate,string &why) {
 why="NAO_E_O_INCIDENTE_R61_DA_RETOMADA";if(!MDRepairEligible21304(s))return false;
 int k=MDOpFindLevel(s,20261105,4);MDOpLevel l=s.levels[k];
 if(!f.stable||!f.connected||!f.clock_ok||f.utc<s.watermark||f.utc>=l.cutoff_utc||
    MDDateValue614((datetime)(f.server/1000))!=20261105){why="RELOGIO_DATA_OU_INVENTARIO_INVALIDOS";return false;}
 if(f.touched[k]||f.first_touch[k]>0){why="R61_PRIMEIRO_TOQUE_JA_OCORREU";return false;}
 if(!f.entry_ready[k]){why="RECONSTRUCAO_COMPLETA_E_GATES_AINDA_PENDENTES";return false;}
 if(!MDRepairIncident21304(journal,s.scope,s.instance)){why="INCIDENTE_NAO_COMPROVADO_NO_DIARIO";return false;}
 MDOpState verified=s;
 if(!MDOpReconcile(verified,snapshot,f.utc,why)||MDOpEncode(verified)!=MDOpEncode(s)){
  why="RECIBOS_AINDA_NAO_CONCILIADOS";return false;
 }
 candidate=s;MDRepairClear21304(candidate);candidate.watermark=f.utc;
 int found=-1;for(int j=0;j<snapshot.book.orders;j++)if(snapshot.book.o[j].order.ticket==2585252290){if(found>=0)return false;found=j;}
 if(found<0||!MDRepairRetired21304(candidate,snapshot,found)){why="CANCELAMENTO_SEM_EXECUCAO_NAO_COMPROVADO";return false;}
 why="R61_CANCELADA_POR_RECONSTRUCAO_E_AINDA_SEM_TOQUE";return true;
}
string repair_last21304="";
bool MDRepairRun21304(const MDOpFrame &f,const MDOpSnapshot &snapshot) {
 if(!MDDemoGate213()||!owns615||fatal||lock615==INVALID_HANDLE||Scope615()!=operational.scope||!MDRepairEligible21304(operational))return false;
 MDOpState candidate;string why;
 if(!MDRepairCandidate21304(operational,snapshot,f,ledger,candidate,why)){
  if(repair_last21304!=why){Report615("REPAIR21304_BLOQUEADO;motivo="+why);repair_last21304=why;}return false;
 }
 string path=ledger_path+".pre21304",saved;MDOpState check;
 bool backup=FileIsExist(path,FILE_COMMON)?
  (MDOpReadFile(path,saved)&&StringSubstr(ledger,0,StringLen(saved))==saved&&MDOpReplay(saved,operational.scope,operational.instance,check)):
  MDOpWriteFile(path,ledger);
 if(!backup){Report615("REPAIR21304_BLOQUEADO;BACKUP_NAO_CONFIRMADO");return false;}
 if(!MDDemoGate213()||Scope615()!=operational.scope)return false;
 if(!Commit(candidate,"REPAIR21304_RESUME_2585252290"))return false;
 int k=MDOpFindLevel(operational,20261105,4);pending_trail_started[k]=false;
 Report615("REPAIR21304_CONFIRMADO;ordem_antiga=2585252290;R61_SEM_TOQUE_ATE_MSC="+IntegerToString(f.server)+
  ";RESULTADOS_S50_S618_PRESERVADOS;NOVO_ENVIO_EXIGE_REVALIDACAO");return true;
}
#endif
