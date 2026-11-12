#property strict
#property version "1.11"
#property description "Coleta historica em lote; sem ordens; nao substitui o EA da XP."
#include "ModeloD_Core.mqh"
input string InpReferencias="MD_Agosto_2026_Referencias.csv";
input string InpSHA256="7135eca392acfc9ab3ecd5b6ddbfe99b11fef94385680463cf9771dc219222f0";
input string InpM1Work="MD_Agosto_2026_M1_Work.csv";
input string InpM1SHA256="bae9afc7de51461fde8e7aedebdba306a8a76063ded2d571787742e05aea3413";
input int InpMinutosPorBloco=10;
input int InpMaxTentativas=10;
struct Ref { string date,symbol; datetime first,cut,end; MDInputs values; };
struct Minute { long n,first,last; double o,h,l,c,quantity; ulong volume,hash; };
Ref refs[]; MDDay model;
MqlTick before[],now[];
double thresholds[60];
int batch_day_index=0,attempt=0,logfile=INVALID_HANDLE,statusfile=INVALID_HANDLE,events=INVALID_HANDLE,minutes=INVALID_HANDLE;
long ordinal=0,previous_msc=-1,last_minute=-1; int last_bucket=-1,run_count=0;
datetime from_time=0,to_time=0; bool have=false,done=false,io_failed=false;
int pending=0,blocks=0,pending_days=0; string folder="",reference_hash="";

input int InpMaxTentativasContrato=10;
MqlRates source_m1[],rate_before[],rate_now[];
bool resolving=true,rate_have=false,mapping_error=false,current_day_pending=false;
int candidate_index=0,rate_attempt=0,matching_count=0,contractfile=INVALID_HANDLE,resolvedfile=INVALID_HANDLE;
long candidate_start=0,candidate_expiry=0;bool outside_life=false;
string candidates[],chosen="";
int select_error=0;bool select_ok=false;
int probe_index=0,probe_attempt=0;bool probe_have=false;MqlRates probe_before[],probe_now[];

void Say(string s) { Print("MES111;",s); if(logfile!=INVALID_HANDLE && FileWrite(logfile,s)==0)io_failed=true; }
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
 if(StringLen(expected)!=64||reference_hash!=expected){Print("MES111;HASH_REFERENCIA_DIVERGENTE;",reference_hash);return false;}
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
datetime BlockEnd(datetime start) { datetime end=start+InpMinutosPorBloco*60;return end<refs[batch_day_index].end?end:refs[batch_day_index].end; }
bool StartDay() {
 // Reading a proven matching history must not depend on Market Watch selection.
 SymbolSelect(refs[batch_day_index].symbol,true);ResetLastError();
 if(!MDCalculate(refs[batch_day_index].values,model))return false;
 int k=0;for(int i=0;i<5;i++){
  double values[6];values[0]=model.levels[i].entry;values[1]=model.levels[i].sl;values[2]=model.levels[i].tp;
  values[3]=model.levels[i].entry_tick;values[4]=model.levels[i].sl_tick;values[5]=model.levels[i].tp_tick;
  for(int j=0;j<6;j++){thresholds[k++]=5.0*MathFloor(values[j]/5.0);thresholds[k++]=5.0*MathCeil(values[j]/5.0);}
 }
 ArraySort(thresholds);
 string tag=refs[batch_day_index].date;StringReplace(tag,".","");
 events=FileOpen(folder+"\\EVENTOS_"+tag+".csv",FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_COMMON,';',CP_UTF8);
 minutes=FileOpen(folder+"\\MINUTOS_"+tag+".csv",FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_COMMON,';',CP_UTF8);
 if(events==INVALID_HANDLE||minutes==INVALID_HANDLE)return false;
 if(FileWrite(events,"ordinal_ALL","time_msc","last","volume","volume_real","flags","bucket")==0)return false;
 if(FileWrite(minutes,"time","business_n","open","high","low","close","volume","volume_real","first_msc","last_msc","business_hash")==0)return false;
 from_time=StringToTime(refs[batch_day_index].date+" 09:00:00");to_time=BlockEnd(from_time);
 current_day_pending=false;ordinal=0;previous_msc=-1;last_minute=-1;last_bucket=-1;run_count=0;attempt=0;have=false;ArrayFree(before);
 Say("DIA;"+refs[batch_day_index].date+";simbolo="+refs[batch_day_index].symbol+";progresso="+IntegerToString(batch_day_index+1)+"/"+IntegerToString(ArraySize(refs)));return true;
}
void Finish(string reason) {
 if(done)return;
 done=true;EventKillTimer();CloseDay();CloseMapping();
 Say("END;reason="+reason+";days="+IntegerToString(batch_day_index)+";blocks="+IntegerToString(blocks)+";pending_blocks="+IntegerToString(pending)+";pending_days="+IntegerToString(pending_days)+";io_failed="+(io_failed?"true":"false")+";pasta=Common\\Files\\"+folder);
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
 if(FileWrite(statusfile,refs[batch_day_index].date,TimeToString(from_time,TIME_DATE|TIME_MINUTES),TimeToString(to_time,TIME_DATE|TIME_MINUTES),"ESTAVEL",attempt,n,business,hash,0)==0)return false;
 FileFlush(events);FileFlush(minutes);FileFlush(statusfile);return true;
}
bool LoadAnchor() {
 int h=FileOpen(InpM1Work,FILE_READ|FILE_BIN);if(h==INVALID_HANDLE)return false;
 long size=(long)FileSize(h);if(size<=0||size>4000000){FileClose(h);return false;}
 uchar data[],key[],digest[];ArrayResize(data,(int)size);uint got=FileReadArray(h,data,0,(int)size);FileClose(h);
 if((long)got!=size||CryptEncode(CRYPT_HASH_SHA256,data,key,digest)!=32)return false;
 string hash="";for(int i=0;i<32;i++)hash+=StringFormat("%02x",(int)digest[i]);
 string expected=InpM1SHA256;StringToLower(expected);StringToLower(hash);if(hash!=expected||StringLen(expected)!=64)return false;
 h=FileOpen(InpM1Work,FILE_READ|FILE_CSV|FILE_ANSI,';',CP_UTF8);if(h==INVALID_HANDLE)return false;
 string heads[6]={"time","open","high","low","close","volume_real"};
 for(int i=0;i<6;i++)if(FileReadString(h)!=heads[i]){FileClose(h);return false;}
 ArrayResize(source_m1,0);
 while(!FileIsEnding(h)) {
  string stamp=FileReadString(h);if(stamp==""&&FileIsEnding(h))break;
  int i=ArraySize(source_m1);if(ArrayResize(source_m1,i+1)!=i+1){FileClose(h);return false;}
  source_m1[i].time=StringToTime(stamp+":00");source_m1[i].open=StringToDouble(FileReadString(h));source_m1[i].high=StringToDouble(FileReadString(h));
  source_m1[i].low=StringToDouble(FileReadString(h));source_m1[i].close=StringToDouble(FileReadString(h));double quantity=StringToDouble(FileReadString(h));
  if(source_m1[i].time<=0||(i>0&&source_m1[i].time<=source_m1[i-1].time)||!MDPositive(source_m1[i].open)||!MDPositive(source_m1[i].close)||!MDPositive(source_m1[i].low)||source_m1[i].high<MathMax(source_m1[i].open,source_m1[i].close)||source_m1[i].low>MathMin(source_m1[i].open,source_m1[i].close)||!MathIsValidNumber(quantity)||quantity<0){FileClose(h);return false;}
 }
 FileClose(h);if(ArraySize(source_m1)==0)return false;
 for(int i=0;i<ArraySize(refs);i++) {
  int count=0;datetime begin=StringToTime(refs[i].date+" 09:00:00");
  for(int j=0;j<ArraySize(source_m1);j++)if(source_m1[j].time>=begin&&source_m1[j].time<refs[i].end) {
   if(count==0&&(source_m1[j].time!=refs[i].first||source_m1[j].open!=refs[i].values.open_today))return false;
   count++;
  }
  if(count==0)return false;
 }
 int dest=FileOpen(folder+"\\M1_WORK.csv",FILE_WRITE|FILE_BIN|FILE_COMMON);if(dest==INVALID_HANDLE)return false;
 uint written=FileWriteArray(dest,data,0,(int)size);FileClose(dest);return (long)written==size;
}
void CloseMapping() {
 if(contractfile!=INVALID_HANDLE){FileFlush(contractfile);FileClose(contractfile);contractfile=INVALID_HANDLE;}
 if(resolvedfile!=INVALID_HANDLE){FileFlush(resolvedfile);FileClose(resolvedfile);resolvedfile=INVALID_HANDLE;}
}
bool OpenMappingFiles() {
 contractfile=FileOpen(folder+"\\CONTRATOS.csv",FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_COMMON,';',CP_UTF8);
 resolvedfile=FileOpen(folder+"\\REFERENCIAS_RESOLVIDAS.csv",FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_COMMON,';',CP_UTF8);
 if(contractfile==INVALID_HANDLE||resolvedfile==INVALID_HANDLE)return false;
 if(FileWrite(contractfile,"date","candidate","state","attempts","bars_n","source_bars_before_cut","candidate_bars_before_cut","OHLC_differences_before_cut","exact_before_cut","error","start_time","expiration_time","select_ok","select_error")==0)return false;
 return FileWrite(resolvedfile,"date","symbol","first_server","cut_server","open","high_prev","low_prev","close_prev","adjustment","end_server")>0;
}
bool BeginResolution() {
 resolving=true;candidate_index=0;rate_attempt=0;matching_count=0;mapping_error=false;rate_have=false;chosen="";
 ArrayFree(rate_before);ArrayFree(rate_now);
 if(refs[batch_day_index].symbol!="WINQ26|WINV26")return false;
 Say("CONTRATO_INICIO;"+refs[batch_day_index].date+";comparacao_M1_Work_antes_do_corte;SEM_ESCOLHA_POR_RESULTADO");return true;
}
void AdvanceDay() {
 CloseDay();batch_day_index++;
 if(batch_day_index>=ArraySize(refs)){Finish(pending_days>0||pending>0?"CONCLUIDO_COM_PENDENCIAS":"CONCLUIDO");return;}
 if(!BeginResolution()){io_failed=true;Finish("ERRO_RESOLUCAO");}
}
bool RatesSame(const MqlRates &a[],const MqlRates &b[]) {
 if(ArraySize(a)!=ArraySize(b))return false;
 for(int i=0;i<ArraySize(a);i++)if(a[i].time!=b[i].time||a[i].open!=b[i].open||a[i].high!=b[i].high||a[i].low!=b[i].low||a[i].close!=b[i].close||a[i].tick_volume!=b[i].tick_volume||a[i].spread!=b[i].spread||a[i].real_volume!=b[i].real_volume)return false;
 return true;
}
bool ExportRates() {
 string tag=refs[batch_day_index].date;StringReplace(tag,".","");
 int h=FileOpen(folder+"\\M1_CONTRATO_"+tag+"_"+candidates[candidate_index]+".csv",FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_COMMON,';',CP_UTF8);
 if(h==INVALID_HANDLE)return false;
 bool ok=FileWrite(h,"time","open","high","low","close","real_volume","tick_volume","spread")>0;
 for(int i=0;i<ArraySize(rate_now)&&ok;i++)ok=FileWrite(h,TimeToString(rate_now[i].time,TIME_DATE|TIME_MINUTES),DoubleToString(rate_now[i].open,-16),DoubleToString(rate_now[i].high,-16),DoubleToString(rate_now[i].low,-16),DoubleToString(rate_now[i].close,-16),rate_now[i].real_volume,rate_now[i].tick_volume,rate_now[i].spread)>0;
 FileClose(h);return ok;
}
void CompareRates(int &source_count,int &candidate_count,int &differences) {
 source_count=0;candidate_count=0;differences=0;datetime begin=StringToTime(refs[batch_day_index].date+" 09:00:00"),cut=refs[batch_day_index].cut;
 int a=0,b=0;
 while(a<ArraySize(source_m1)&&source_m1[a].time<begin)a++;
 while(b<ArraySize(rate_now)&&rate_now[b].time<begin)b++;
 for(int i=a;i<ArraySize(source_m1)&&source_m1[i].time<cut;i++)source_count++;
 for(int i=b;i<ArraySize(rate_now)&&rate_now[i].time<cut;i++)candidate_count++;
 while((a<ArraySize(source_m1)&&source_m1[a].time<cut)||(b<ArraySize(rate_now)&&rate_now[b].time<cut)) {
  if(a>=ArraySize(source_m1)||source_m1[a].time>=cut){differences++;b++;continue;}
  if(b>=ArraySize(rate_now)||rate_now[b].time>=cut){differences++;a++;continue;}
  if(source_m1[a].time<rate_now[b].time){differences++;a++;continue;}
  if(rate_now[b].time<source_m1[a].time){differences++;b++;continue;}
  if(source_m1[a].open!=rate_now[b].open||source_m1[a].high!=rate_now[b].high||source_m1[a].low!=rate_now[b].low||source_m1[a].close!=rate_now[b].close)differences++;
  a++;b++;
 }
}
void CompleteCandidate(bool valid,int n,int error) {
 int source_count=0,candidate_count=0,differences=-1;bool exact=false;
 if(valid){CompareRates(source_count,candidate_count,differences);exact=source_count>0&&differences==0&&source_count==candidate_count;if(!ExportRates()){io_failed=true;Finish("ERRO_EXPORTAR_CONTRATO");return;}}
 else if(!outside_life)mapping_error=true;
 if(exact){matching_count++;chosen=candidates[candidate_index];}
 if(FileWrite(contractfile,refs[batch_day_index].date,candidates[candidate_index],valid?"ESTAVEL":outside_life?"FORA_VIGENCIA":"PENDENTE",rate_attempt,n,source_count,candidate_count,differences,exact?1:0,error,candidate_start,candidate_expiry,select_ok?1:0,select_error)==0){io_failed=true;Finish("ERRO_CONTRATOS_IO");return;}
 FileFlush(contractfile);
 Say("CONTRATO;"+refs[batch_day_index].date+";simbolo="+candidates[candidate_index]+";estavel="+(valid?"sim":"nao")+";igual_Work="+(exact?"sim":"nao")+";diferencas="+IntegerToString(differences)+";erro="+IntegerToString(error));
 candidate_index++;rate_attempt=0;rate_have=false;ArrayFree(rate_before);ArrayFree(rate_now);
 if(candidate_index<ArraySize(candidates))return;
 if(matching_count!=1){pending_days++;Say("DIA_PENDENTE_CONTRATO;"+refs[batch_day_index].date+";matches="+IntegerToString(matching_count)+";erro_candidato="+(mapping_error?"sim":"nao"));AdvanceDay();return;}
 if(mapping_error)Say("CONTRATO_COMPATIVEL_COM_RESSALVA;"+refs[batch_day_index].date+";escolhido="+chosen+";OUTRO_CANDIDATO_NAO_VERIFICADO_NAO_E_PROVA_DE_UNICIDADE");
 refs[batch_day_index].symbol=chosen;
 if(FileWrite(resolvedfile,refs[batch_day_index].date,chosen,TimeToString(refs[batch_day_index].first,TIME_DATE|TIME_SECONDS),TimeToString(refs[batch_day_index].cut,TIME_DATE|TIME_SECONDS),DoubleToString(refs[batch_day_index].values.open_today,-16),DoubleToString(refs[batch_day_index].values.high_prev,-16),DoubleToString(refs[batch_day_index].values.low_prev,-16),DoubleToString(refs[batch_day_index].values.close_prev,-16),DoubleToString(refs[batch_day_index].values.adjustment,-16),TimeToString(refs[batch_day_index].end,TIME_DATE|TIME_SECONDS))==0){io_failed=true;Finish("ERRO_REFERENCIA_RESOLVIDA");return;}
 FileFlush(resolvedfile);resolving=false;
 if(!StartDay()){io_failed=true;Finish("ERRO_INICIO_DIA");}
}
void ResolveTimer() {
 rate_attempt++;ResetLastError();int n=-1;datetime begin=StringToTime(refs[batch_day_index].date+" 09:00:00");
 outside_life=false;candidate_start=0;candidate_expiry=0;
 ResetLastError();select_ok=SymbolSelect(candidates[candidate_index],true);select_error=GetLastError();
 // SymbolSelect can fail for archived contracts. Still ask CopyRates directly.
 ResetLastError();candidate_start=SymbolInfoInteger(candidates[candidate_index],SYMBOL_START_TIME);candidate_expiry=SymbolInfoInteger(candidates[candidate_index],SYMBOL_EXPIRATION_TIME);
 int metadata_error=GetLastError();
 outside_life=metadata_error==0&&((candidate_expiry>0&&(long)begin>candidate_expiry)||(candidate_start>0&&(long)refs[batch_day_index].end<=candidate_start));
 if(outside_life){ArrayFree(rate_now);CompleteCandidate(false,0,0);return;}
 ResetLastError();n=CopyRates(candidates[candidate_index],PERIOD_M1,begin,refs[batch_day_index].end-1,rate_now);
 int error=GetLastError();bool valid=n>=0&&n==ArraySize(rate_now)&&error==0;
 if(valid)for(int i=0;i<n;i++)if(rate_now[i].time<begin||rate_now[i].time>=refs[batch_day_index].end||(long)rate_now[i].time%60!=0||(i>0&&rate_now[i].time<=rate_now[i-1].time)||!MDPositive(rate_now[i].open)||!MDPositive(rate_now[i].close)||!MDPositive(rate_now[i].low)||!MathIsValidNumber(rate_now[i].high)||rate_now[i].high<MathMax(rate_now[i].open,rate_now[i].close)||rate_now[i].low>MathMin(rate_now[i].open,rate_now[i].close)){valid=false;break;}
 if(valid&&rate_have&&RatesSame(rate_before,rate_now)){CompleteCandidate(true,n,0);return;}
 if(rate_attempt>=InpMaxTentativasContrato){CompleteCandidate(false,n,error);return;}
 rate_have=false;
 if(valid){if(ArrayResize(rate_before,n)!=n||(n>0&&ArrayCopy(rate_before,rate_now)!=n)){io_failed=true;Finish("ERRO_MEMORIA_CONTRATO");return;}rate_have=true;}
 Say("CONTRATO_LEITURA;"+refs[batch_day_index].date+";simbolo="+candidates[candidate_index]+";tentativa="+IntegerToString(rate_attempt)+";n="+IntegerToString(n)+";erro="+IntegerToString(error)+";select_ok="+(select_ok?"sim":"nao")+";select_error="+IntegerToString(select_error));
}
bool HasBusiness() {
 for(int i=0;i<ArraySize(now);i++)if((now[i].flags&120)!=0)return true;
 return false;
}

void AddContract(string name) {
 bool custom=false;if(SymbolExist(name,custom)&&custom)return;
 for(int k=0;k<StringLen(name);k++){ushort c=StringGetCharacter(name,k);if(!((c>='A'&&c<='Z')||(c>='a'&&c<='z')||(c>='0'&&c<='9')||c=='_'||c=='#'||c=='.'||c=='-'))return;}
 for(int i=0;i<ArraySize(candidates);i++)if(candidates[i]==name)return;
 if(ArraySize(candidates)>=32){io_failed=true;return;}
 int n=ArraySize(candidates);if(ArrayResize(candidates,n+1)!=n+1){io_failed=true;return;}candidates[n]=name;
}
bool DiscoverContracts() {
 ArrayResize(candidates,0);AddContract("WINQ26");AddContract("WINV26");
 int total=SymbolsTotal(false);
 for(int i=0;i<total;i++) {
  string name=SymbolName(i,false);
  if(StringFind(name,"WINQ26")!=0&&StringFind(name,"WINV26")!=0)continue;
  bool custom=false;if(!SymbolExist(name,custom)||custom)continue;
  AddContract(name);
 }
 if(io_failed||ArraySize(candidates)==0)return false;
 int h=FileOpen(folder+"\\SIMBOLOS.csv",FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_COMMON,';',CP_UTF8);if(h==INVALID_HANDLE)return false;
 bool ok=FileWrite(h,"symbol","exists","custom","select_ok","select_error","start_time","expiration_time","metadata_error")>0;
 for(int i=0;i<ArraySize(candidates)&&ok;i++) {
  bool custom=false;bool exists=SymbolExist(candidates[i],custom);ResetLastError();bool selected=SymbolSelect(candidates[i],true);int selection_error=GetLastError();
  ResetLastError();long begin=SymbolInfoInteger(candidates[i],SYMBOL_START_TIME),end=SymbolInfoInteger(candidates[i],SYMBOL_EXPIRATION_TIME);int metadata_error=GetLastError();
  ok=FileWrite(h,candidates[i],exists?1:0,custom?1:0,selected?1:0,selection_error,begin,end,metadata_error)>0;
 }
 FileClose(h);Say("SIMBOLOS;total_servidor="+IntegerToString(total)+";candidatos="+IntegerToString(ArraySize(candidates))+";TENTAR_HISTORICO_MESMO_COM_SELECT_FALHO");return ok;
}
void ProbeContext() {
 probe_attempt++;ResetLastError();int frame=probe_index==0?PERIOD_M1:PERIOD_D1;string tf=probe_index==0?"M1":"D1";
 int n=CopyRates("WIN$N",(ENUM_TIMEFRAMES)frame,D'2026.07.31 00:00:00',D'2026.07.31 23:59:59',probe_now);int error=GetLastError();
 bool valid=n>=0&&n==ArraySize(probe_now)&&error==0;
 if(valid)for(int i=0;i<n;i++)if(probe_now[i].time<D'2026.07.31'||probe_now[i].time>D'2026.07.31 23:59:59'||(i>0&&probe_now[i].time<=probe_now[i-1].time)||!MDPositive(probe_now[i].open)||!MDPositive(probe_now[i].high)||!MDPositive(probe_now[i].low)||!MDPositive(probe_now[i].close)||probe_now[i].high<MathMax(probe_now[i].open,probe_now[i].close)||probe_now[i].low>MathMin(probe_now[i].open,probe_now[i].close)) {valid=false;break;}
 if(!(valid&&probe_have&&RatesSame(probe_before,probe_now))&&probe_attempt<InpMaxTentativasContrato) {
  probe_have=false;if(valid){if(ArrayResize(probe_before,n)!=n||(n>0&&ArrayCopy(probe_before,probe_now)!=n)){io_failed=true;Finish("ERRO_MEMORIA_CONTEXTO");return;}probe_have=true;}
  Say("CONTEXTO_31JUL_LEITURA;frame="+tf+";tentativa="+IntegerToString(probe_attempt)+";n="+IntegerToString(n)+";erro="+IntegerToString(error));return;
 }
 bool stable=valid&&probe_have&&RatesSame(probe_before,probe_now);
 int h=FileOpen(folder+"\\CONTEXTO_20260731_"+tf+".csv",FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_COMMON,';',CP_UTF8);
 if(h==INVALID_HANDLE){io_failed=true;Finish("ERRO_IO_CONTEXTO");return;}
 bool ok=FileWrite(h,"state","time","open","high","low","close","real_volume","tick_volume","spread","error")>0;
 if(stable)for(int i=0;i<n&&ok;i++)ok=FileWrite(h,"ESTAVEL",TimeToString(probe_now[i].time,TIME_DATE|TIME_MINUTES),DoubleToString(probe_now[i].open,-16),DoubleToString(probe_now[i].high,-16),DoubleToString(probe_now[i].low,-16),DoubleToString(probe_now[i].close,-16),probe_now[i].real_volume,probe_now[i].tick_volume,probe_now[i].spread,0)>0;
 if(!stable||n==0)ok=FileWrite(h,stable?"VAZIO_ESTAVEL":"PENDENTE","","","","","","","","",error)>0&&ok;
 FileClose(h);if(!ok){io_failed=true;Finish("ERRO_IO_CONTEXTO");return;}
 Say("CONTEXTO_31JUL;frame="+tf+";estavel="+(stable?"sim":"nao")+";n="+IntegerToString(n)+";erro="+IntegerToString(error)+";CONFERENCIA_ADICIONAL_NAO_ALTERA_REFERENCIAS_CONGELADAS");
 probe_index++;probe_attempt=0;probe_have=false;ArrayFree(probe_before);ArrayFree(probe_now);
}

int OnInit() {
 if(MQLInfoInteger(MQL_TESTER)||InpMinutosPorBloco<1||InpMinutosPorBloco>10||InpMaxTentativas<2||InpMaxTentativasContrato<2){Print("MES111;RECUSADO;TERMINAL_E_PARAMETROS");return INIT_PARAMETERS_INCORRECT;}
 folder="ModeloD_Fechamento_Agosto\\MES111_"+IntegerToString((long)TimeLocal())+"_"+IntegerToString((long)GetTickCount());
 if(!FolderCreate("ModeloD_Fechamento_Agosto",FILE_COMMON)&&GetLastError()!=0)ResetLastError();
 if(!FolderCreate(folder,FILE_COMMON)){Print("MES111;ERRO_PASTA;",GetLastError());return INIT_FAILED;}
 if(!LoadReferences()){Print("MES111;ERRO_REFERENCIAS;copiar CSV para MQL5\\Files;erro=",GetLastError());return INIT_FAILED;}
 if(!LoadAnchor()){Print("MES111;ERRO_M1_WORK_OU_HASH");return INIT_FAILED;}
 logfile=FileOpen(folder+"\\RESULTADO.txt",FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_COMMON,0,CP_UTF8);
 statusfile=FileOpen(folder+"\\BLOCOS.csv",FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_COMMON,';',CP_UTF8);
 if(logfile==INVALID_HANDLE||statusfile==INVALID_HANDLE)return INIT_FAILED;
 if(FileWrite(statusfile,"date","from_inclusive","to_exclusive","state","attempts","ALL_n","business_n","ALL_hash","error")==0)return INIT_FAILED;
 Say("START;versao=1.11;servidor="+AccountInfoString(ACCOUNT_SERVER)+";build="+IntegerToString((long)TerminalInfoInteger(TERMINAL_BUILD))+";reference_sha256="+reference_hash+";m1_work_sha256="+InpM1SHA256+";somente_leitura;SEM_ORDENS;EVENTOS_REDUZIDOS_NAO_SAO_TODOS_OS_TICKS");
 if(!DiscoverContracts()||!OpenMappingFiles()||!BeginResolution()||!EventSetTimer(1))return INIT_FAILED;
 return INIT_SUCCEEDED;
}
void OnTick() {}
void OnTimer() {
 if(done)return;
 if(io_failed){Finish("ERRO_IO");return;}
 if(probe_index<2){ProbeContext();return;}
 if(resolving){ResolveTimer();return;}
 attempt++;ResetLastError();int n=CopyTicksRange(refs[batch_day_index].symbol,now,COPY_TICKS_ALL,(ulong)from_time*1000,(ulong)to_time*1000-1);int error=GetLastError();
 bool valid=(n>=0&&n==ArraySize(now)&&error==0);long previous=-1;
 if(valid)for(int i=0;i<n;i++) {
  if(now[i].time_msc<(long)from_time*1000||now[i].time_msc>=(long)to_time*1000||now[i].time_msc<previous||((now[i].flags&120)!=0&&(!MDPositive(now[i].last)||!MathIsValidNumber(now[i].volume_real)||now[i].volume_real<0))){valid=false;break;}
  previous=now[i].time_msc;
 }
 bool stable=valid&&have&&Same(before,now);
 if(stable) {
  if(from_time<=refs[batch_day_index].first && to_time>refs[batch_day_index].first && !HasBusiness()){
   pending++;blocks++;if(!current_day_pending){pending_days++;current_day_pending=true;}Say("DIA_PENDENTE_SEM_NEGOCIOS_ABERTURA;"+refs[batch_day_index].date+";duas_leituras_estaveis_nao_provam_ausencia_no_servidor");
   if(FileWrite(statusfile,refs[batch_day_index].date,TimeToString(from_time,TIME_DATE|TIME_MINUTES),TimeToString(to_time,TIME_DATE|TIME_MINUTES),"SEM_NEGOCIOS_ABERTURA",attempt,n,0,0,0)==0)io_failed=true;
   AdvanceDay();return;
  }
  if(!Commit(n)){io_failed=true;Finish("ERRO_GRAVACAO_OU_ORDEM");return;}blocks++;
 } else if(attempt>=InpMaxTentativas) {
  pending++;blocks++;if(FileWrite(statusfile,refs[batch_day_index].date,TimeToString(from_time,TIME_DATE|TIME_MINUTES),TimeToString(to_time,TIME_DATE|TIME_MINUTES),"PENDENTE",attempt,n,0,0,error)==0){io_failed=true;Finish("ERRO_IO");return;}
  if(!current_day_pending){pending_days++;current_day_pending=true;}
  Say("PENDENTE;"+refs[batch_day_index].date+";"+TimeToString(from_time,TIME_MINUTES)+";erro="+IntegerToString(error));last_bucket=-1;last_minute=-1;run_count=0;
  if(from_time<=refs[batch_day_index].first&&to_time>refs[batch_day_index].first){Say("DIA_PENDENTE_ABERTURA_NAO_RECUPERADA;"+refs[batch_day_index].date);AdvanceDay();return;}
 } else {
  have=false;
  if(valid){if(ArrayResize(before,n)!=n||(n>0&&ArrayCopy(before,now)!=n)){io_failed=true;Finish("ERRO_MEMORIA");return;}have=true;}
  if(attempt==1||!valid)Say("LEITURA;dia="+refs[batch_day_index].date+";bloco="+TimeToString(from_time,TIME_MINUTES)+";tentativa="+IntegerToString(attempt)+";n="+IntegerToString(n)+";erro="+IntegerToString(error));
  return;
 }
 from_time=to_time;have=false;attempt=0;ArrayFree(before);ArrayFree(now);
 if(from_time>=refs[batch_day_index].end){Say("DIA_CONCLUIDO;"+refs[batch_day_index].date);CloseDay();AdvanceDay();return;}
 else to_time=BlockEnd(from_time);
}
void OnDeinit(const int reason) {
 EventKillTimer();CloseMapping();if(!done&&logfile!=INVALID_HANDLE)Say("INTERROMPIDO;resultado_incompleto;reason="+IntegerToString(reason));CloseDay();
 if(statusfile!=INVALID_HANDLE){FileClose(statusfile);statusfile=INVALID_HANDLE;}if(logfile!=INVALID_HANDLE){FileClose(logfile);logfile=INVALID_HANDLE;}
}
