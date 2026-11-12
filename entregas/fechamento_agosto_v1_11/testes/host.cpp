#include <bits/stdc++.h>
#include <openssl/sha.h>
using string=std::string;using datetime=long;using ENUM_TIMEFRAMES=int;using uchar=unsigned char;using ushort=unsigned short;using uint=unsigned int;
enum {INVALID_HANDLE=-1,FILE_READ=1,FILE_WRITE=2,FILE_BIN=4,FILE_CSV=8,FILE_TXT=16,FILE_ANSI=32,FILE_COMMON=64,CP_UTF8=65001,TIME_DATE=1,TIME_MINUTES=2,TIME_SECONDS=4,MQL_TESTER=100,TERMINAL_BUILD=101,ACCOUNT_SERVER=102,CRYPT_HASH_SHA256=103,COPY_TICKS_ALL=104,PERIOD_M1=105,PERIOD_D1=108,SYMBOL_START_TIME=106,SYMBOL_EXPIRATION_TIME=107,INIT_SUCCEEDED=0,INIT_FAILED=-1,INIT_PARAMETERS_INCORRECT=-2};
struct MqlRates {long time=0;double open=0,high=0,low=0,close=0;long tick_volume=0;int spread=0;long real_volume=0;};
struct MqlTick {long time=0;double bid=0,ask=0,last=0;ulong volume=0;long time_msc=0;uint flags=0;double volume_real=0;};
struct File {string name,data;size_t cursor=0;bool write=false;};std::map<int,File> files;std::map<string,string> saved;int nextid=1,error=0,copy_error=0;bool env_tester=false,write_ok=true,removed=false;std::vector<MqlTick> fixture;
template<class T>void ZeroMemory(T&x){x=T{};}template<class T,size_t N>void ZeroMemory(T(&x)[N]){std::fill(x,x+N,T{});}
template<class T>int ArraySize(const std::vector<T>&x){return (int)x.size();}template<class T>int ArrayResize(std::vector<T>&x,int n){x.resize(n);return n;}template<class T>void ArrayFree(std::vector<T>&x){x.clear();}template<class T>int ArrayCopy(std::vector<T>&to,const std::vector<T>&from){to=from;return from.size();}template<class T,size_t N>void ArraySort(T(&x)[N]){std::sort(x,x+N);}
string IntegerToString(long x){return std::to_string(x);}string DoubleToString(double x,int n){std::ostringstream o;if(n<0)o<<std::scientific<<std::setprecision(-n);else o<<std::fixed<<std::setprecision(n);o<<x;return o.str();}
bool MathIsValidNumber(double x){return std::isfinite(x);}double MathAbs(double x){return std::abs(x);}double MathFloor(double x){return std::floor(x);}double MathCeil(double x){return std::ceil(x);}double MathRound(double x){return std::round(x);}double MathMax(double x,double y){return std::max(x,y);}double MathMin(double x,double y){return std::min(x,y);}
int StringLen(string x){return x.size();}ushort StringGetCharacter(string x,int i){return x.at(i);}void StringToLower(string&x){std::transform(x.begin(),x.end(),x.begin(),[](uchar c){return std::tolower(c);});}void StringReplace(string&x,string a,string b){for(size_t p=0;(p=x.find(a,p))!=string::npos;p+=b.size())x.replace(p,a.size(),b);}double StringToDouble(string x){return std::stod(x);}string StringFormat(const char*fmt,int x){char b[64];std::snprintf(b,sizeof b,fmt,x);return b;}
long StringToTime(string s){std::tm t{};std::istringstream in(s);in>>std::get_time(&t,s.size()==10?"%Y.%m.%d":"%Y.%m.%d %H:%M:%S");if(in.fail())return 0;return timegm(&t);}long TimeLocal(){return StringToTime("2026.11.11 13:00:00");}long GetTickCount(){return 777;}
string TimeToString(long value,int flags){std::time_t v=value;std::tm t=*std::gmtime(&v);std::ostringstream o;if(flags&TIME_DATE)o<<std::put_time(&t,"%Y.%m.%d");if((flags&TIME_DATE)&&(flags&(TIME_MINUTES|TIME_SECONDS)))o<<" ";if(flags&TIME_SECONDS)o<<std::put_time(&t,"%H:%M:%S");else if(flags&TIME_MINUTES)o<<std::put_time(&t,"%H:%M");return o.str();}
void ResetLastError(){error=0;}int GetLastError(){return error;}template<class...T>void Print(T...){ }long MQLInfoInteger(int){return env_tester;}long TerminalInfoInteger(int){return 6231;}string AccountInfoString(int){return "GenialInvestimentos-PRD";}bool FolderCreate(string,int){return true;}int fail_select=0,fail_q_read=0,alias_mode=0;int StringFind(string a,string b){auto n=a.find(b);return n==string::npos?-1:(int)n;}
bool SymbolSelect(string name,bool){if(fail_select&&name.find("WINQ26")==0){error=4305;return false;}return true;}
int SymbolsTotal(bool){return alias_mode?3:2;}string SymbolName(int i,bool){if(i==0)return "WINQ26";if(i==1)return "WINV26";return "WINQ26.H";}bool SymbolExist(string,bool&custom){custom=false;return true;}bool EventSetTimer(int){return true;}void EventKillTimer(){}void ExpertRemove(){removed=true;}
int FileOpen(string name,int flags,int=0,int=0){if(flags&FILE_READ){auto it=saved.find(name);if(it==saved.end())return -1;int h=nextid++;files[h]={name,it->second,0,false};return h;}int h=nextid++;files[h]={name,"",0,true};return h;}
void FileFlush(int h){if(files.count(h)&&files[h].write)saved[files[h].name]=files[h].data;}void FileClose(int h){FileFlush(h);}long FileSize(int h){return files[h].data.size();}bool FileIsEnding(int h){return files[h].cursor>=files[h].data.size();}
string FileReadString(int h){auto &f=files[h];while(f.cursor<f.data.size()&&(f.data[f.cursor]=='\n'||f.data[f.cursor]=='\r'))f.cursor++;size_t s=f.cursor;while(f.cursor<f.data.size()&&f.data[f.cursor]!=';'&&f.data[f.cursor]!='\n'&&f.data[f.cursor]!='\r')f.cursor++;string r=f.data.substr(s,f.cursor-s);if(f.cursor<f.data.size())f.cursor++;return r;}
uint FileReadArray(int h,std::vector<uchar>&v,int start,int n){auto &f=files[h];n=std::min(n,(int)(f.data.size()-f.cursor));if(v.size()<(size_t)(start+n))v.resize(start+n);for(int i=0;i<n;i++)v[start+i]=(uchar)f.data[f.cursor++];return n;}
uint FileWriteArray(int h,const std::vector<uchar>&v,int start,int n){if(!write_ok)return 0;files[h].data.append((const char*)v.data()+start,n);return n;}
template<class...T>uint FileWrite(int h,T...x){if(!write_ok)return 0;std::ostringstream o;bool first=true;auto add=[&](const auto &v){if(!first)o<<';';first=false;o<<v;};(add(x),...);o<<'\n';auto s=o.str();files[h].data+=s;return s.size();}
int CryptEncode(int,const std::vector<uchar>&v,const std::vector<uchar>&,std::vector<uchar>&out){out.resize(32);SHA256(v.data(),v.size(),out.data());return 32;}
int CopyTicksRange(string,std::vector<MqlTick>&out,int,ulong a,ulong b){error=copy_error;if(error){out.clear();return -1;}out.clear();for(auto &t:fixture)if((ulong)t.time_msc>=a&&(ulong)t.time_msc<=b)out.push_back(t);return out.size();}

std::vector<MqlRates> rate_fixture;
int rate_mode=0,rate_error=0,tick_calls=0;
int CopyRates(string symbol,int frame,long a,long b,std::vector<MqlRates>&out){
 error=rate_error;out.clear();if(error)return -1;
 if(symbol=="WIN$N") {MqlRates r;r.time=StringToTime("2026.07.31 12:34:00");r.open=177470;r.high=179495;r.low=176985;r.close=178725;if(frame==PERIOD_D1){r.time=StringToTime("2026.07.31");r.open=176000;r.high=180000;r.low=175000;}out.push_back(r);return 1;}
 if((fail_q_read&&symbol=="WINQ26")||(alias_mode&&symbol=="WINQ26")){error=4302;return -1;}
 bool correct=(a<StringToTime("2026.08.19")?symbol.find("WINQ26")==0:symbol=="WINV26");
 for(auto row:rate_fixture)if(row.time>=a&&row.time<=b){
  if(rate_mode==2||(!correct&&rate_mode==0)){row.open+=1000;row.high+=1000;row.low+=1000;row.close+=1000;}
  out.push_back(row);
 }
 return out.size();
}
long SymbolInfoInteger(string symbol,int field){if(field==SYMBOL_START_TIME)return StringToTime("2026.01.01");return symbol=="WINQ26"?StringToTime("2026.08.19 18:25:00"):StringToTime("2026.10.14 18:25:00");}
void CloseMapping();void AdvanceDay();
#include "Coletar_Agosto_Sem_Ordens.mq5"
int checks=0;void require(bool ok,const char*label){checks++;if(!ok)throw std::runtime_error(label);}
void reset(){files.clear();nextid=1;saved.clear();fixture.clear();rate_fixture.clear();batch_day_index=attempt=pending=blocks=pending_days=0;logfile=statusfile=events=minutes=contractfile=resolvedfile=INVALID_HANDLE;ordinal=0;previous_msc=last_minute=-1;last_bucket=-1;run_count=0;from_time=to_time=0;have=done=io_failed=false;env_tester=false;write_ok=true;removed=false;fail_select=fail_q_read=alias_mode=0;probe_index=0;probe_attempt=0;probe_have=false;copy_error=error=rate_error=rate_mode=0;before.clear();now.clear();source_m1.clear();rate_before.clear();rate_now.clear();rate_have=mapping_error=false;resolving=true;matching_count=candidate_index=rate_attempt=0;chosen="";}
string readall(string p){std::ifstream f(p);return string(std::istreambuf_iterator<char>(f),{});}
MqlTick tick(long ms,double price){MqlTick t;t.time=ms/1000;t.time_msc=ms;t.last=price;t.bid=price;t.ask=price+5;t.flags=56;t.volume=1;t.volume_real=1;return t;}
std::vector<string> split(string line){std::vector<string> v;std::stringstream s(line);string x;while(std::getline(s,x,';'))v.push_back(x);return v;}
void init_fixture(string refs_text,string m1_text){
 saved[InpReferencias]=refs_text;saved[InpM1Work]=m1_text;require(OnInit()==0,"Init hashes and references valid");probe_index=2;
 std::stringstream stream(m1_text);string line;std::getline(stream,line);
 while(std::getline(stream,line)){
  auto f=split(line);if(f.size()!=6)continue;
  MqlRates row;row.time=StringToTime(f[0]+":00");row.open=std::stod(f[1]);row.high=std::stod(f[2]);row.low=std::stod(f[3]);row.close=std::stod(f[4]);row.real_volume=(long)std::stod(f[5]);row.tick_volume=4;row.spread=5;rate_fixture.push_back(row);
  double px[4]={row.open,row.high,row.low,row.close};
  for(int i=0;i<4;i++){auto t=tick(row.time*1000+i*100,px[i]);t.volume_real=i==3?row.real_volume-3*std::floor(row.real_volume/4.0):std::floor(row.real_volume/4.0);t.volume=(ulong)t.volume_real;fixture.push_back(t);}
 }
}
void resolve_first(){for(int i=0;i<4;i++)OnTimer();}
int main(int argc,char**argv){
 if(argc!=4)return 2;
 string reference=readall(argv[1]),m1=readall(argv[2]);
 reset();env_tester=true;require(OnInit()==INIT_PARAMETERS_INCORRECT,"Tester refused");
 reset();saved[InpReferencias]=reference+"x";require(OnInit()==INIT_FAILED,"Reference hash mutation refused");
 reset();saved[InpReferencias]=reference;saved[InpM1Work]=m1+"x";require(OnInit()==INIT_FAILED,"M1 hash mutation refused");
 reset();init_fixture(reference,m1);resolve_first();require(!resolving&&refs[0].symbol=="WINQ26","Unique contract selected by source M1");
 fixture={tick(from_time*1000+1,refs[0].values.open_today),tick(from_time*1000+1,refs[0].values.open_today),tick(from_time*1000+1,refs[0].values.open_today)};
 OnTimer();require(have&&blocks==0,"First tick read not committed");fixture[1].volume++;OnTimer();require(blocks==0,"Tick mutation not stable");OnTimer();require(blocks==1&&ordinal==3,"Second equal read commits and preserves duplicate ms");
 reset();init_fixture(reference,m1);rate_mode=1;resolve_first();require(batch_day_index==1&&pending_days==1&&resolving,"Both contracts equal refuses arbitrary selection");
 reset();init_fixture(reference,m1);rate_mode=2;resolve_first();require(batch_day_index==1&&pending_days==1,"Neither contract equal remains pending");
 reset();init_fixture(reference,m1);rate_error=4401;for(int i=0;i<20;i++)OnTimer();require(batch_day_index==1&&pending_days==1,"Contract error4401 retries then pending");
 reset();init_fixture(reference,m1);OnTimer();rate_fixture[0].real_volume++;OnTimer();require(candidate_index==0,"Whole M1 field mutation resets stable read");OnTimer();require(candidate_index==1,"M1 restabilizes on second equal snapshot");
 reset();init_fixture(reference,m1);resolve_first();fixture.clear();OnTimer();OnTimer();require(batch_day_index==1&&pending_days==1&&pending==1,"Stable empty opening never becomes zero PnL");
 reset();init_fixture(reference,m1);resolve_first();copy_error=4401;for(int i=0;i<10;i++)OnTimer();require(pending==1&&blocks==1,"Tick4401 retry exhaustion marked pending");
 reset();init_fixture(reference,m1);resolve_first();write_ok=false;OnTimer();OnTimer();require(done&&io_failed,"Write failure stops collection");
 reset();fail_select=1;init_fixture(reference,m1);resolve_first();require(!resolving&&refs[0].symbol=="WINQ26","Select4305 does not prevent a successful direct history read");OnTimer();OnTimer();require(blocks==1,"Selected matching Q history can collect ticks despite select failure");
 reset();alias_mode=1;init_fixture(reference,m1);int alias_guard=0;while(resolving&&alias_guard++<30)OnTimer();require(!resolving&&refs[0].symbol=="WINQ26.H","Native suffix discovered and selected by exact OHLC");
 reset();fail_q_read=1;rate_mode=1;init_fixture(reference,m1);int missing_guard=0;while(resolving&&missing_guard++<30)OnTimer();require(!resolving&&refs[0].symbol=="WINV26"&&mapping_error,"Verified V match continues with explicit unverified-Q caveat");
 reset();init_fixture(reference,m1);probe_index=0;for(int i=0;i<4;i++)OnTimer();require(probe_index==2,"M1 and D1 July31 probed through stable readings");require(saved[folder+"\\CONTEXTO_20260731_M1.csv"].find("12:34")!=string::npos,"Partial M1 context retained");require(saved[folder+"\\CONTEXTO_20260731_D1.csv"].find("00:00")!=string::npos,"D1 context retained separately, without adding Aug3");
 reset();init_fixture(reference,m1);int watchdog=0;while(!done&&watchdog++<5000)OnTimer();
 require(done&&batch_day_index==21&&pending==0&&pending_days==0&&!io_failed,"All21days synthetic pipeline complete");require(blocks==1197,"1197 contiguous blocks");
 string result=saved[folder+"\\REFERENCIAS_RESOLVIDAS.csv"];require(result.find("2026.08.18;WINQ26")!=string::npos&&result.find("2026.08.19;WINV26")!=string::npos,"Rollover by match, not a fixed date in collector");
 require(saved[folder+"\\RESULTADO.txt"].find("END;reason=CONCLUIDO;days=21;blocks=1197;pending_blocks=0;pending_days=0;io_failed=false")!=string::npos,"Native summary format");
 std::filesystem::create_directories(argv[3]);for(auto &[name,data]:saved){auto slash=name.find_last_of('\\');if(slash!=string::npos){std::ofstream f(std::filesystem::path(argv[3])/name.substr(slash+1));f<<data;}}
 std::cout<<"PASS checks="<<checks<<"; actual collector adapted to C++ API mocks; synthetic four-point path; NOT native MetaEditor compilation/execution or historical PnL\n";
}
