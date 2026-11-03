#include <iostream>
#include <string>
#include <cmath>
#include <sstream>
#include <iomanip>

double MathRound(double x){return std::round(x);}
double MathFloor(double x){return std::floor(x);}
bool MathIsValidNumber(double x){return std::isfinite(x);}
double MathAbs(double x){return std::abs(x);}
using string=std::string;
int StringLen(const string &s){return (int)s.size();}
int StringGetCharacter(const string &s,int i){return (unsigned char)s.at(i);}
int StringFind(const string &s,const string &what,int start=0){auto p=s.find(what,start);return p==string::npos?-1:(int)p;}
string StringSubstr(const string &s,int start,int n=-1){return s.substr(start,n<0?string::npos:n);}
string IntegerToString(long x){return std::to_string(x);}
long StringToInteger(const string &s){return std::stol(s);}
double StringToDouble(const string &s){return std::stod(s);}
void StringTrimLeft(string &s){s.erase(0,s.find_first_not_of(" \t\r\n"));}
void StringTrimRight(string &s){auto i=s.find_last_not_of(" \t\r\n");if(i==string::npos)s.clear();else s.erase(i+1);}
template<class... T>void Print(T... v){(std::cout<<...<<v)<<'\n';}

string DoubleToString(double x,int precision){std::ostringstream o;o<<std::fixed<<std::setprecision(precision)<<x;return o.str();}

#include <fstream>
#include <filesystem>
#include <map>
#include <memory>
using uint=unsigned int;
const int INVALID_HANDLE=-1,FILE_READ=1,FILE_WRITE=2,FILE_BIN=4,FILE_ANSI=8,FILE_COMMON=16,FILE_REWRITE=32,FILE_TXT=64,CP_UTF8=65001,TERMINAL_COMMONDATA_PATH=0;
struct FH {std::fstream f;string path;};
std::map<int,std::unique_ptr<FH>> handles;int serial=1,lastError=0;
string full(string p){return "/tmp/md615k_host/"+p;}
void ResetLastError(){lastError=0;}int GetLastError(){return lastError;}
int FileOpen(string p,int flags,int delimiter=0,int codepage=0){
 (void)delimiter;(void)codepage;
 for(auto &kv:handles)if(kv.second->path==p)return INVALID_HANDLE;
 auto h=std::make_unique<FH>();h->path=p;
 std::ios::openmode m=std::ios::binary;
 if(flags&FILE_READ)m|=std::ios::in;
 if(flags&FILE_WRITE)m|=std::ios::out;
 if((flags&FILE_WRITE)&&!(flags&FILE_READ))m|=std::ios::trunc;
 if((flags&FILE_WRITE)&&!std::filesystem::exists(full(p))){std::ofstream create(full(p));}
 h->f.open(full(p),m);if(!h->f)return INVALID_HANDLE;
 int id=serial++;handles[id]=std::move(h);return id;
}
unsigned long FileSize(int h){return std::filesystem::file_size(full(handles.at(h)->path));}
void FileClose(int h){handles.erase(h);}
bool FileSeek(int h,long offset,int origin){auto &f=handles.at(h)->f;f.clear();std::ios::seekdir direction=origin==SEEK_SET?std::ios::beg:std::ios::cur;f.seekg(offset,direction);f.seekp(offset,direction);if(!f){lastError=1;return false;}return true;}
string FileReadString(int h,int n){string s(n,' ');auto &f=handles.at(h)->f;f.read(s.data(),n);s.resize(f.gcount());return s;}
uint FileWriteString(int h,string s,int n=-1){if(n<0)n=s.size();auto &f=handles.at(h)->f;f.write(s.data(),n);if(!f){lastError=1;return 0;}return n;}
void FileFlush(int h){auto &f=handles.at(h)->f;f.flush();if(!f)lastError=1;}
bool FileIsExist(string p,int){return std::filesystem::exists(full(p));}
bool FileMove(string a,int,string b,int){std::error_code e;std::filesystem::rename(full(a),full(b),e);return !e;}
long TimeLocal(){return 1792605000;}long GetMicrosecondCount(){return 615001;}
string TerminalInfoString(int){return "/tmp/md615k_host";}






#include "../MQL5/Scripts/ModeloD_Integrado_Sem_Transporte/ModeloD_PreviewIntegradoCases.mqh"
int main(){std::filesystem::remove_all("/tmp/md615k_host");std::filesystem::create_directory("/tmp/md615k_host");RunPreviewIntegrado("host");std::cout<<logPreview;Print("TESTE_PREVIA_INTEGRADA;Checks=",checksPreview,";Failures=",failuresPreview);return failuresPreview?1:0;}
