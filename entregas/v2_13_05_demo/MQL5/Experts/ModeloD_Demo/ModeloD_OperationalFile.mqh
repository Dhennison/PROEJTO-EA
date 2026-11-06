#ifndef MODELOD_OPERATIONAL_FILE
#define MODELOD_OPERATIONAL_FILE
#include "ModeloD_OperationalCodec.mqh"
bool MDOpReadFile(string path,string &text) {
 int h=FileOpen(path,FILE_READ|FILE_BIN|FILE_ANSI|FILE_COMMON);if(h==INVALID_HANDLE)return false;
 ulong n=FileSize(h);if(n>134217728){FileClose(h);return false;}
 text=FileReadString(h,(int)n);FileClose(h);return StringLen(text)==(int)n;
}
bool MDOpWriteFile(string path,string text) {
 ResetLastError();int h=FileOpen(path,FILE_WRITE|FILE_BIN|FILE_ANSI|FILE_COMMON);if(h==INVALID_HANDLE)return false;
 uint count=FileWriteString(h,text,StringLen(text));FileFlush(h);int error=GetLastError();FileClose(h);
 string check;return count==(uint)StringLen(text)&&error==0&&MDOpReadFile(path,check)&&check==text;
}
// .next is only a publication candidate for the SAME complete ledger, not another subsystem.
// A torn candidate cannot have granted a transport permit. Preserve it; never erase a prior checkpoint.
bool MDOpRecoverFile(string path,string scope,int instance,string &text,MDOpState &s,string &why) {
 bool main_exists=FileIsExist(path,FILE_COMMON),next_exists=FileIsExist(path+".next",FILE_COMMON);
 string main="",pending="";MDOpState base,candidate;
 if(main_exists&&(!MDOpReadFile(path,main)||!MDOpReplay(main,scope,instance,base))){why="LEDGER_INVALID_PRESERVE_FILES";return false;}
 if(next_exists) {
  bool valid=MDOpReadFile(path+".next",pending)&&MDOpReplay(pending,scope,instance,candidate);
  if(valid&&main_exists&&pending!=main&&(StringSubstr(pending,0,StringLen(main))!=main||candidate.revision!=base.revision+1)){
   why="CANDIDATE_IS_NOT_NEXT_REVISION";return false;
  }
  if(valid) {
   if(!FileMove(path+".next",FILE_COMMON,path,FILE_COMMON|FILE_REWRITE)){why="RECOVER_PUBLICATION_FAILED";return false;}
   main=pending;base=candidate;main_exists=true;
  } else {
   if(!main_exists){why="FIRST_COMMIT_TORN_NO_BASE";return false;}
   string archive=path+".torn_"+IntegerToString((long)TimeLocal())+"_"+IntegerToString((long)GetMicrosecondCount());
   if(FileIsExist(archive,FILE_COMMON)||!FileMove(path+".next",FILE_COMMON,archive,FILE_COMMON)){why="PRESERVE_TORN_CANDIDATE_FAILED";return false;}
  }
 }
 if(!main_exists){why="NO_LEDGER";return false;}
 string verified;if(!MDOpReadFile(path,verified)||verified!=main){why="RECOVERY_READBACK_FAILED";return false;}
 text=main;s=base;why="LEDGER_RESUMED";return true;
}
bool MDOpCommitFile(string path,int lock_handle,string &ledger_text,MDOpState &state,const MDOpState &candidate,string event,string &why) {
 if(lock_handle==INVALID_HANDLE||candidate.scope!=state.scope||candidate.instance!=state.instance){why="LOCK_OR_CONTEXT";return false;}
 string disk;
 if(ledger_text!="") {if(!MDOpReadFile(path,disk)||disk!=ledger_text){why="LEDGER_CHANGED_OR_MISSING";return false;}}
 else if(FileIsExist(path,FILE_COMMON)){why="REFUSE_OVERWRITE_EXISTING";return false;}
 if(FileIsExist(path+".next",FILE_COMMON)){why="RECOVER_PENDING_CANDIDATE_FIRST";return false;}
 MDOpState next=candidate;next.revision=state.revision+1;
 if(!MDOpForwardEvent21305(state,next,event,ledger_text)){why="STATE_REGRESSION";return false;}
 string data=MDOpRecord(ledger_text,next,event);MDOpState decoded;
 if(data==""||!MDOpReplay(data,state.scope,state.instance,decoded)){why="CANDIDATE_INVALID";return false;}
 if(!MDOpWriteFile(path+".next",data)){why="WRITE_OR_FLUSH_FAILED";return false;}
 if(!FileMove(path+".next",FILE_COMMON,path,FILE_COMMON|FILE_REWRITE)){why="PUBLISH_FAILED";return false;}
 string check;
 if(!MDOpReadFile(path,check)||check!=data){why="COMMIT_READBACK_FAILED";return false;}
 ledger_text=data;state=decoded;why="COMMIT_CONFIRMED";return true;
}
#endif
