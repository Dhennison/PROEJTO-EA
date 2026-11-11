#property strict
#property version "1.00"
#property description "Coleta historica em lote; sem ordens; nao substitui o EA da XP."
#include "ModeloD_Core.mqh"
input string InpReferencias="MD_Setembro_2026_Referencias.csv";
input string InpSHA256="ff2623cc41ddf7a4a9ef8c476b658bd22e5629ec1160a22ad1fa285476408313";
input int InpMinutosPorBloco=10;
input int InpMaxTentativas=10;
struct Ref { string date,symbol; datetime first,cut,end; MDInputs values; };
struct Minute { long n,first,last; double o,h,l,c,quantity; ulong volume,hash; };
Ref refs[]; MDDay model;
MqlTick before[],now[];
double thresholds[60];
int day=0,attempt=0,logfile=INVALID_HANDLE,statusfile=INVALID_HANDLE,events=INVALID_HANDLE,minutes=INVALID_HANDLE;
long ordinal=0,previous_msc=-1,last_minute=-1; int last_bucket=-1,run_count=0;
datetime from_time=0,to_time=0; bool have=false,done=false,io_failed=false;
int pending=0,blocks=0; string folder="",reference_hash="";
void Say(string s) { Print("MES100;",s); if(logfile!=INVALID_HANDLE && FileWrite(logfile,s)==0)io_failed=true; }
void Mix(ulong &h,ulong v) { h^=v; h*=1099511628211; }
ulong Q(double x) { string s=DoubleToString(x,-16); ulong h=1469598103934665603; for(int i=0;i<StringLen(s);i++)Mix(h,(ulong)StringGetCharacter(s,i)); return h; }
void HashTick(ulong &h,const MqlTick &t) { Mix(h,(ulong)t.time_msc);Mix(h,Q(t.bid));Mix(h,Q(t.ask));Mix(h,Q(t.last));Mix(h,t.volume);Mix(h,Q(t.volume_real));Mix(h,(ulong)t.flags); }
bool Same(const MqlTick &a[],const MqlTick &b[]) {
 if(ArraySize(a)!=ArraySize(b))return false;
 for(int i=0;i<ArraySize(a);i++)if(a[i].time!=b[i].time||a[i].time_msc!=b[i].time_msc||a[i].bid!=b[i].bid||a[i].ask!=b[i].ask||a[i].last!=b[i].last||a[i].volume!=b[i].volume||a[i].volume_real!=b[i].volume_real||a[i].flags!=b[i].flags)return false;
 return true;
}
bool LoadReferences() {
 int h=FileOpen(InpReferencias,FILE_READ|FILE_BIN); if(h==INVALID_HANDLE)return false;
 long size=(long)FileSize(h); if(size<=0||size>100000){FileClose(h);return false;}
 uchar data[],key[],digest[]; ArrayResize(data,(int)size);
 uint got=FileReadArray(h,data,0,(int)size);FileClose(h); if((long)got!=size)return false;
 if(CryptEncode(CRYPT_HASH_SHA256,data,key,digest)!=32)return false;
 reference_hash="";for(int i=0;i<32;i++)reference_hash+=StringFormat("%02x",(int)digest[i]);
 string expected=InpSHA256;StringToLower(expected);StringToLower(reference_hash);
 if(StringLen(expected)!=64||reference_hash!=expected){Print("MES100;HASH_REFERENCIA_DIVERGENTE;",reference_hash);return false;}
 h=FileOpen(InpReferencias,FILE_READ|FILE_CSV|FILE_ANSI,';',CP_UTF8);if(h==INVALID_HANDLE)return false;
 string headers[10]={"date","symbol","first_server","cut_server","open","high_prev","low_prev","close_prev","adjustment","end_server"};
 for(int j=0;j<10;j++)if(FileReadString(h)!=headers[j]){FileClose(h);return false;}
 ArrayResize(refs,0);
 while(!FileIsEnding(h)) {
  string date=FileReadString(h);if(date==""&&FileIsEnding(h))break;
  int i=ArraySize(refs);if(date==""||i>=1000||ArrayResize(refs,i+1)!=i+1){FileClose(h);return false;}
  refs[i].date=date;refs[i].symbol=FileReadString(h);
  refs[i].first=StringToTime(FileReadString(h));refs[i].cut=StringToTime(FileReadString(h));
  refs[i].values.open_today=StringToDouble(FileReadString(h));refs[i].values.high_prev=StringToDouble(FileReadString(h));
  refs[i].values.low_prev=StringToDouble(FileReadString(h));refs[i].values.close_prev=StringToDouble(FileReadString(h));refs[i].values.adjustment=StringToDouble(FileReadString(h));
  refs[i].end=StringToTime(FileReadString(h));datetime begin=StringToTime(refs[i].date+" 09:00:00");
  MDDay check;
  datetime expected_cut=StringToTime(refs[i].date+((begin>=D'2023.03.13'&&begin<D'2023.11.04')?" 17:45:00":" 18:00:00"));
  if(refs[i].symbol==""||begin<=0||begin>=TimeLocal()||refs[i].first<begin||refs[i].first>=refs[i].cut||refs[i].cut!=expected_cut||refs[i].end<=refs[i].cut||refs[i].end>=StringToTime(refs[i].date+" 23:59:00")||((long)refs[i].end%60)!=0||!MDCalculate(refs[i].values,check)||(i>0&&refs[i].first<=refs[i-1].first)){FileClose(h);return false;}
 }
 if(ArraySize(refs)==0){FileClose(h);return false;}
 FileClose(h);
 int dest=FileOpen(folder+"\\REFERENCIAS.csv",FILE_WRITE|FILE_BIN|FILE_COMMON);if(dest==INVALID_HANDLE)return false;
 uint written=FileWriteArray(dest,data,0,(int)size);FileClose(dest);return (long)written==size;
}
int Bucket(double price) {
 int lo=0,hi=60;while(lo<hi){int mid=(lo+hi)/2;if(thresholds[mid]<price)lo=mid+1;else hi=mid;}
 return 2*lo+((lo<60&&thresholds[lo]==price)?1:0);
}
void CloseDay() { if(events!=INVALID_HANDLE){FileFlush(events);FileClose(events);events=INVALID_HANDLE;}if(minutes!=INVALID_HANDLE){FileFlush(minutes);FileClose(minutes);minutes=INVALID_HANDLE;} }
datetime BlockEnd(datetime start) { datetime end=start+InpMinutosPorBloco*60;return end<refs[day].end?end:refs[day].end; }
bool StartDay() {
 if(!SymbolSelect(refs[day].symbol,true)||!MDCalculate(refs[day].values,model))return false;
 int k=0;for(int i=0;i<5;i++){
  double values[6];values[0]=model.levels[i].entry;values[1]=model.levels[i].sl;values[2]=model.levels[i].tp;
  values[3]=model.levels[i].entry_tick;values[4]=model.levels[i].sl_tick;values[5]=model.levels[i].tp_tick;
  for(int j=0;j<6;j++){thresholds[k++]=5.0*MathFloor(values[j]/5.0);thresholds[k++]=5.0*MathCeil(values[j]/5.0);}
 }
 ArraySort(thresholds);
 string tag=refs[day].date;StringReplace(tag,".","");
 events=FileOpen(folder+"\\EVENTOS_"+tag+".csv",FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_COMMON,';',CP_UTF8);
 minutes=FileOpen(folder+"\\MINUTOS_"+tag+".csv",FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_COMMON,';',CP_UTF8);
 if(events==INVALID_HANDLE||minutes==INVALID_HANDLE)return false;
 if(FileWrite(events,"ordinal_ALL","time_msc","last","volume","volume_real","flags","bucket")==0)return false;
 if(FileWrite(minutes,"time","business_n","open","high","low","close","volume","volume_real","first_msc","last_msc","business_hash")==0)return false;
 from_time=StringToTime(refs[day].date+" 09:00:00");to_time=BlockEnd(from_time);
 ordinal=0;previous_msc=-1;last_minute=-1;last_bucket=-1;run_count=0;attempt=0;have=false;ArrayFree(before);
 Say("DIA;"+refs[day].date+";simbolo="+refs[day].symbol+";progresso="+IntegerToString(day+1)+"/"+IntegerToString(ArraySize(refs)));return true;
}
void Finish(string reason) {
 if(done)return;
 done=true;EventKillTimer();CloseDay();
 Say("END;reason="+reason+";days="+IntegerToString(day)+";blocks="+IntegerToString(blocks)+";pending_blocks="+IntegerToString(pending)+";io_failed="+(io_failed?"true":"false")+";pasta=Common\\Files\\"+folder);
 if(statusfile!=INVALID_HANDLE){FileFlush(statusfile);FileClose(statusfile);statusfile=INVALID_HANDLE;}
 if(logfile!=INVALID_HANDLE){FileFlush(logfile);FileClose(logfile);logfile=INVALID_HANDLE;}
 ExpertRemove();
}
bool Commit(int n) {
 Minute m[10];ZeroMemory(m);int count=(int)((to_time-from_time)/60);long business=0;ulong hash=1469598103934665603;
 for(int j=0;j<count;j++)m[j].hash=1469598103934665603;
 for(int i=0;i<n;i++) {
  ordinal++;HashTick(hash,now[i]);
  if((now[i].flags&120)==0)continue;
  int idx=(int)((now[i].time_msc-(long)from_time*1000)/60000);if(idx<0||idx>=count||now[i].time_msc<previous_msc)return false;
  previous_msc=now[i].time_msc;business++;double price=now[i].last;
  if(m[idx].n==0){m[idx].o=price;m[idx].h=price;m[idx].l=price;m[idx].first=now[i].time_msc;}
  m[idx].n++;m[idx].h=MathMax(m[idx].h,price);m[idx].l=MathMin(m[idx].l,price);m[idx].c=price;m[idx].last=now[i].time_msc;
  m[idx].volume+=now[i].volume;m[idx].quantity+=now[i].volume_real;HashTick(m[idx].hash,now[i]);
  int bucket=Bucket(price);long minute=now[i].time_msc/60000;
  bool changed=(bucket!=last_bucket),minute_first=(minute!=last_minute);
  if(changed){last_bucket=bucket;run_count=1;}else if(run_count<3)run_count++;
  // Keep the first TWO records of every price category and each minute opener.
  // This preserves a possible entry then exit on the next business at a gap.
  if(changed||run_count<=2||minute_first||MathAbs(price/5.0-MathRound(price/5.0))>1e-8)
   if(FileWrite(events,ordinal,now[i].time_msc,DoubleToString(price,-16),now[i].volume,DoubleToString(now[i].volume_real,-16),now[i].flags,bucket)==0)return false;
  last_minute=minute;
 }
 for(int j=0;j<count;j++)if(FileWrite(minutes,TimeToString(from_time+j*60,TIME_DATE|TIME_MINUTES),m[j].n,DoubleToString(m[j].o,-16),DoubleToString(m[j].h,-16),DoubleToString(m[j].l,-16),DoubleToString(m[j].c,-16),m[j].volume,DoubleToString(m[j].quantity,-16),m[j].first,m[j].last,m[j].hash)==0)return false;
 if(FileWrite(statusfile,refs[day].date,TimeToString(from_time,TIME_DATE|TIME_MINUTES),TimeToString(to_time,TIME_DATE|TIME_MINUTES),"ESTAVEL",attempt,n,business,hash,0)==0)return false;
 FileFlush(events);FileFlush(minutes);FileFlush(statusfile);return true;
}
int OnInit() {
 if(MQLInfoInteger(MQL_TESTER)||InpMinutosPorBloco<1||InpMinutosPorBloco>10||InpMaxTentativas<2){Print("MES100;RECUSADO;TERMINAL_E_PARAMETROS");return INIT_PARAMETERS_INCORRECT;}
 folder="ModeloD_Fechamento_Setembro\\MES100_"+IntegerToString((long)TimeLocal())+"_"+IntegerToString((long)GetTickCount());
 if(!FolderCreate("ModeloD_Fechamento_Setembro",FILE_COMMON)&&GetLastError()!=0)ResetLastError();
 if(!FolderCreate(folder,FILE_COMMON)){Print("MES100;ERRO_PASTA;",GetLastError());return INIT_FAILED;}
 if(!LoadReferences()){Print("MES100;ERRO_REFERENCIAS;copiar CSV para MQL5\\Files;erro=",GetLastError());return INIT_FAILED;}
 if(!SymbolSelect(refs[0].symbol,true)){Print("MES100;ERRO_SIMBOLO");return INIT_FAILED;}
 logfile=FileOpen(folder+"\\RESULTADO.txt",FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_COMMON,0,CP_UTF8);
 statusfile=FileOpen(folder+"\\BLOCOS.csv",FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_COMMON,';',CP_UTF8);
 if(logfile==INVALID_HANDLE||statusfile==INVALID_HANDLE)return INIT_FAILED;
 if(FileWrite(statusfile,"date","from_inclusive","to_exclusive","state","attempts","ALL_n","business_n","ALL_hash","error")==0)return INIT_FAILED;
 Say("START;versao=1.00;servidor="+AccountInfoString(ACCOUNT_SERVER)+";build="+IntegerToString((long)TerminalInfoInteger(TERMINAL_BUILD))+";reference_sha256="+reference_hash+";somente_leitura;SEM_ORDENS;EVENTOS_REDUZIDOS_NAO_SAO_TODOS_OS_TICKS");
 if(!StartDay()||!EventSetTimer(1))return INIT_FAILED;
 return INIT_SUCCEEDED;
}
void OnTick() {}
void OnTimer() {
 if(done)return;
 if(io_failed){Finish("ERRO_IO");return;}
 attempt++;ResetLastError();int n=CopyTicksRange(refs[day].symbol,now,COPY_TICKS_ALL,(ulong)from_time*1000,(ulong)to_time*1000-1);int error=GetLastError();
 bool valid=(n>=0&&n==ArraySize(now)&&error==0);long previous=-1;
 if(valid)for(int i=0;i<n;i++) {
  if(now[i].time_msc<(long)from_time*1000||now[i].time_msc>=(long)to_time*1000||now[i].time_msc<previous||((now[i].flags&120)!=0&&(!MDPositive(now[i].last)||!MathIsValidNumber(now[i].volume_real)||now[i].volume_real<0))){valid=false;break;}
  previous=now[i].time_msc;
 }
 bool stable=valid&&have&&Same(before,now);
 if(stable) {
  if(!Commit(n)){io_failed=true;Finish("ERRO_GRAVACAO_OU_ORDEM");return;}blocks++;
 } else if(attempt>=InpMaxTentativas) {
  pending++;blocks++;if(FileWrite(statusfile,refs[day].date,TimeToString(from_time,TIME_DATE|TIME_MINUTES),TimeToString(to_time,TIME_DATE|TIME_MINUTES),"PENDENTE",attempt,n,0,0,error)==0){io_failed=true;Finish("ERRO_IO");return;}
  Say("PENDENTE;"+refs[day].date+";"+TimeToString(from_time,TIME_MINUTES)+";erro="+IntegerToString(error));last_bucket=-1;last_minute=-1;run_count=0;
 } else {
  have=false;
  if(valid){if(ArrayResize(before,n)!=n||(n>0&&ArrayCopy(before,now)!=n)){io_failed=true;Finish("ERRO_MEMORIA");return;}have=true;}
  if(attempt==1||!valid)Say("LEITURA;dia="+refs[day].date+";bloco="+TimeToString(from_time,TIME_MINUTES)+";tentativa="+IntegerToString(attempt)+";n="+IntegerToString(n)+";erro="+IntegerToString(error));
  return;
 }
 from_time=to_time;have=false;attempt=0;ArrayFree(before);ArrayFree(now);
 if(from_time>=refs[day].end){Say("DIA_CONCLUIDO;"+refs[day].date);CloseDay();day++;if(day>=ArraySize(refs)){Finish("CONCLUIDO");return;}if(!StartDay()){io_failed=true;Finish("ERRO_INICIO_DIA");return;}}
 else to_time=BlockEnd(from_time);
}
void OnDeinit(const int reason) {
 EventKillTimer();if(!done&&logfile!=INVALID_HANDLE)Say("INTERROMPIDO;resultado_incompleto;reason="+IntegerToString(reason));CloseDay();
 if(statusfile!=INVALID_HANDLE){FileClose(statusfile);statusfile=INVALID_HANDLE;}if(logfile!=INVALID_HANDLE){FileClose(logfile);logfile=INVALID_HANDLE;}
}
