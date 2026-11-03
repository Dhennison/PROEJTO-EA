#ifndef MODELOD_TEST_RUN
#define MODELOD_TEST_RUN
// Per-run TEST_ONLY namespace. Never delete or reuse earlier test fixtures.
// The claim handle stays open until the consolidated script finishes.
bool MDRegressionRunSuffix(string &suffix,int &claim,string &why) {
 suffix="";claim=INVALID_HANDLE;
 string seed=IntegerToString((long)TimeLocal())+"_"+IntegerToString((long)GetMicrosecondCount());
 for(int i=0;i<32;i++) {
  string candidate="MQL5_REGRESSION_"+seed+"_"+IntegerToString(i);
  string marker="ModeloD_TEST_ONLY_RUN_"+candidate+".claim";
  if(FileIsExist(marker,FILE_COMMON))continue;
  int h=FileOpen(marker,FILE_READ|FILE_WRITE|FILE_BIN|FILE_ANSI|FILE_COMMON);
  if(h==INVALID_HANDLE)continue;
  if(FileSize(h)>0){FileClose(h);continue;}
  ResetLastError();uint written=FileWriteString(h,candidate);FileFlush(h);int error=GetLastError();
  if(written!=(uint)StringLen(candidate)||error!=0){FileClose(h);why="TEST_RUN_CLAIM_WRITE_FAILED";return false;}
  suffix=candidate;claim=h;why="TEST_RUN_ISOLATED";return true;
 }
 why="TEST_RUN_CLAIM_UNAVAILABLE";return false;
}
#endif
