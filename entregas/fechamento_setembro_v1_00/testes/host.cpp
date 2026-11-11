#include <bits/stdc++.h>
#include <openssl/sha.h>
using string=std::string;using datetime=long;using uchar=unsigned char;using ushort=unsigned short;using uint=unsigned int;
enum {INVALID_HANDLE=-1,FILE_READ=1,FILE_WRITE=2,FILE_BIN=4,FILE_CSV=8,FILE_TXT=16,FILE_ANSI=32,FILE_COMMON=64,CP_UTF8=65001,TIME_DATE=1,TIME_MINUTES=2,TIME_SECONDS=4,MQL_TESTER=100,TERMINAL_BUILD=101,ACCOUNT_SERVER=102,CRYPT_HASH_SHA256=103,COPY_TICKS_ALL=104,INIT_SUCCEEDED=0,INIT_FAILED=-1,INIT_PARAMETERS_INCORRECT=-2};
struct MqlTick {long time=0;double bid=0,ask=0,last=0;ulong volume=0;long time_msc=0;uint flags=0;double volume_real=0;};
struct File {string name,data;size_t cursor=0;bool write=false;};std::map<int,File> files;std::map<string,string> saved;int nextid=1,error=0,copy_error=0;bool env_tester=false,write_ok=true,removed=false;std::vector<MqlTick> fixture;
template<class T>void ZeroMemory(T&x){x=T{};}template<class T,size_t N>void ZeroMemory(T(&x)[N]){std::fill(x,x+N,T{});}
template<class T>int ArraySize(const std::vector<T>&x){return (int)x.size();}template<class T>int ArrayResize(std::vector<T>&x,int n){x.resize(n);return n;}template<class T>void ArrayFree(std::vector<T>&x){x.clear();}template<class T>int ArrayCopy(std::vector<T>&to,const std::vector<T>&from){to=from;return from.size();}template<class T,size_t N>void ArraySort(T(&x)[N]){std::sort(x,x+N);}
string IntegerToString(long x){return std::to_string(x);}string DoubleToString(double x,int n){std::ostringstream o;if(n<0)o<<std::scientific<<std::setprecision(-n);else o<<std::fixed<<std::setprecision(n);o<<x;return o.str();}
bool MathIsValidNumber(double x){return std::isfinite(x);}double MathAbs(double x){return std::abs(x);}double MathFloor(double x){return std::floor(x);}double MathCeil(double x){return std::ceil(x);}double MathRound(double x){return std::round(x);}double MathMax(double x,double y){return std::max(x,y);}double MathMin(double x,double y){return std::min(x,y);}
int StringLen(string x){return x.size();}ushort StringGetCharacter(string x,int i){return x.at(i);}void StringToLower(string&x){std::transform(x.begin(),x.end(),x.begin(),[](uchar c){return std::tolower(c);});}void StringReplace(string&x,string a,string b){for(size_t p=0;(p=x.find(a,p))!=string::npos;p+=b.size())x.replace(p,a.size(),b);}double StringToDouble(string x){return std::stod(x);}string StringFormat(const char*fmt,int x){char b[64];std::snprintf(b,sizeof b,fmt,x);return b;}
long StringToTime(string s){std::tm t{};std::istringstream in(s);in>>std::get_time(&t,s.size()==10?"%Y.%m.%d":"%Y.%m.%d %H:%M:%S");if(in.fail())return 0;return timegm(&t);}long TimeLocal(){return StringToTime("2026.11.11 13:00:00");}long GetTickCount(){return 777;}
string TimeToString(long value,int flags){std::time_t v=value;std::tm t=*std::gmtime(&v);std::ostringstream o;if(flags&TIME_DATE)o<<std::put_time(&t,"%Y.%m.%d");if((flags&TIME_DATE)&&(flags&(TIME_MINUTES|TIME_SECONDS)))o<<" ";if(flags&TIME_SECONDS)o<<std::put_time(&t,"%H:%M:%S");else if(flags&TIME_MINUTES)o<<std::put_time(&t,"%H:%M");return o.str();}
void ResetLastError(){error=0;}int GetLastError(){return error;}template<class...T>void Print(T...){ }long MQLInfoInteger(int){return env_tester;}long TerminalInfoInteger(int){return 6231;}string AccountInfoString(int){return "GenialInvestimentos-PRD";}bool FolderCreate(string,int){return true;}bool SymbolSelect(string,bool){return true;}bool EventSetTimer(int){return true;}void EventKillTimer(){}void ExpertRemove(){removed=true;}
int FileOpen(string name,int flags,int=0,int=0){if(flags&FILE_READ){auto it=saved.find(name);if(it==saved.end())return -1;int h=nextid++;files[h]={name,it->second,0,false};return h;}int h=nextid++;files[h]={name,"",0,true};return h;}
void FileFlush(int h){if(files.count(h)&&files[h].write)saved[files[h].name]=files[h].data;}void FileClose(int h){FileFlush(h);}long FileSize(int h){return files[h].data.size();}bool FileIsEnding(int h){return files[h].cursor>=files[h].data.size();}
string FileReadString(int h){auto &f=files[h];while(f.cursor<f.data.size()&&(f.data[f.cursor]=='\n'||f.data[f.cursor]=='\r'))f.cursor++;size_t s=f.cursor;while(f.cursor<f.data.size()&&f.data[f.cursor]!=';'&&f.data[f.cursor]!='\n'&&f.data[f.cursor]!='\r')f.cursor++;string r=f.data.substr(s,f.cursor-s);if(f.cursor<f.data.size())f.cursor++;return r;}
uint FileReadArray(int h,std::vector<uchar>&v,int start,int n){auto &f=files[h];n=std::min(n,(int)(f.data.size()-f.cursor));if(v.size()<(size_t)(start+n))v.resize(start+n);for(int i=0;i<n;i++)v[start+i]=(uchar)f.data[f.cursor++];return n;}
uint FileWriteArray(int h,const std::vector<uchar>&v,int start,int n){if(!write_ok)return 0;files[h].data.append((const char*)v.data()+start,n);return n;}
template<class...T>uint FileWrite(int h,T...x){if(!write_ok)return 0;std::ostringstream o;bool first=true;auto add=[&](const auto &v){if(!first)o<<';';first=false;o<<v;};(add(x),...);o<<'\n';auto s=o.str();files[h].data+=s;return s.size();}
int CryptEncode(int,const std::vector<uchar>&v,const std::vector<uchar>&,std::vector<uchar>&out){out.resize(32);SHA256(v.data(),v.size(),out.data());return 32;}
int CopyTicksRange(string,std::vector<MqlTick>&out,int,ulong a,ulong b){error=copy_error;if(error){out.clear();return -1;}out.clear();for(auto &t:fixture)if((ulong)t.time_msc>=a&&(ulong)t.time_msc<=b)out.push_back(t);return out.size();}
#include "Coletar_Setembro_Sem_Ordens.mq5"
int checks=0;void require(bool ok,const char*label){checks++;if(!ok)throw std::runtime_error(label);}
void reset(){files.clear();nextid=1;saved.clear();fixture.clear();day=attempt=pending=blocks=0;logfile=statusfile=events=minutes=INVALID_HANDLE;ordinal=0;previous_msc=last_minute=-1;last_bucket=-1;run_count=0;from_time=to_time=0;have=done=io_failed=false;env_tester=false;write_ok=true;removed=false;copy_error=error=0;before.clear();now.clear();}
string readall(string p){std::ifstream f(p);return string(std::istreambuf_iterator<char>(f),{});}
MqlTick tick(long ms,double price){MqlTick t;t.time=ms/1000;t.time_msc=ms;t.last=price;t.bid=price;t.ask=price+5;t.flags=56;t.volume=1;t.volume_real=1;return t;}
int main(int argc,char**argv){
 if(argc!=4)return 2;
 string reference=readall(argv[1]);
 reset();env_tester=true;require(OnInit()==INIT_PARAMETERS_INCORRECT,"Tester refused");
 reset();saved[InpReferencias]=reference+"x";require(OnInit()==INIT_FAILED,"Changed reference hash refused");
 reset();saved[InpReferencias]=reference;require(OnInit()==0,"References validated through SHA256 and 14 rows");require(reference_hash==InpSHA256,"Hash exact");
 long ms=(long)from_time*1000;fixture={tick(ms+1,179390),tick(ms+1,179390),tick(ms+1,179390)};
 OnTimer();require(have&&blocks==0,"First read not committed");fixture[1].volume++;OnTimer();require(blocks==0,"Field mutation not stable");OnTimer();require(blocks==1,"Second identical read commits");
 require(ordinal==3,"No raw duplicate millisecond deduplication");require(saved[folder+"\\EVENTOS_20260901.csv"].find("2;")!=string::npos,"Second record of equal category retained");
 reset();saved[InpReferencias]=reference;OnInit();copy_error=4401;for(int i=0;i<10;i++)OnTimer();require(pending==1&&blocks==1,"Error4401 remains pending after retries");
 reset();saved[InpReferencias]=reference;OnInit();fixture={tick((long)from_time*1000+1,-1)};for(int i=0;i<10;i++)OnTimer();require(pending==1,"Invalid business Last never committed");
 reset();saved[InpReferencias]=reference;OnInit();write_ok=false;OnTimer();OnTimer();require(done&&io_failed,"Write error cannot appear as success");
 reset();saved[InpReferencias]=reference;OnInit();
 // Synthetic 4-point path from original M1. API transport test only, not historical ticks.
 std::ifstream in(argv[2]);string line;std::getline(in,line);
 while(std::getline(in,line)){std::vector<string> fields;std::stringstream s(line);string x;while(std::getline(s,x,';'))fields.push_back(x);if(fields.size()<6)continue;
  string stamp=fields[0];StringReplace(stamp,"-",".");long t=StringToTime(stamp.size()==16?stamp+":00":stamp);
  if(!t)throw std::runtime_error("time fixture");
  double q=std::stod(fields[5]);
  for(int i=0;i<4;i++){auto tickvalue=tick(t*1000+i*100,std::stod(fields[i+1]));tickvalue.volume_real=i==3?q-3*std::floor(q/4):std::floor(q/4);tickvalue.volume=(ulong)tickvalue.volume_real;fixture.push_back(tickvalue);}
 }
 int watchdog=0;while(!done&&watchdog++<3000)OnTimer();require(done&&day==14&&pending==0&&!io_failed,"14-day complete transport");require(blocks==798,"798 contiguous 10-minute blocks");
 std::filesystem::create_directories(argv[3]);for(auto &[name,data]:saved){auto slash=name.find_last_of('\\');if(slash!=string::npos){std::ofstream f(std::filesystem::path(argv[3])/name.substr(slash+1));f<<data;}}
 std::cout<<"PASS checks="<<checks<<"; actual collector adapted to C++ with API mocks and OpenSSL SHA256; synthetic 4-point transport; NOT native MT5 compile/execution\n";
}
