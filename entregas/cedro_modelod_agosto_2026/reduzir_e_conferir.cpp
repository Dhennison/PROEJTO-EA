// Leitura em fluxo. Preserva primeiras duas ocorrencias de cada categoria de preco.
// Confere em paralelo o resultado grade5 em TODOS os registros, sem reducao.
#include <algorithm>
#include <array>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>
#include <cstdlib>
using I=long long;
struct Level{bool eligible,buy;I en,sl,tp;bool entered=false,closed=false;I eo=0,em=0,ep=0,xo=0,xm=0,xp=0,exit=0;int reason=0;};
I integer(std::string_view v){std::string s(v);char *e=nullptr;I x=std::strtoll(s.c_str(),&e,10);if(e==s.c_str())throw std::runtime_error("numero invalido");if(*e=='.'){++e;while(*e=='0')++e;}if(*e)throw std::runtime_error("preco nao inteiro");return x;}
int digits(std::string_view s,int a,int n){int v=0;for(int i=a;i<a+n;i++){if(s[i]<'0'||s[i]>'9')throw std::runtime_error("data invalida");v=v*10+s[i]-'0';}return v;}
int main(int argc,char**argv){try{
 if(argc!=3)throw std::runtime_error("config e saida direta exigidas");
 std::ifstream cfg(argv[1]);std::string contract,date;I base,cut;int n;cfg>>contract>>date>>base>>cut>>n;
 std::vector<I> bounds(n);for(I&b:bounds)cfg>>b;
 std::array<Level,5> levels;
 for(auto&l:levels)cfg>>l.eligible>>l.buy>>l.en>>l.sl>>l.tp;
 if(!cfg)throw std::runtime_error("config invalida");
 std::ios::sync_with_stdio(false);std::cin.tie(nullptr);
 std::cout<<"ordinal_ALL;time_msc;last\n";
 I previous=0,previous_ms=-1,last_minute=-1,records=0,emitted=0;int last_bucket=-1,run=0;
 std::string line;while(std::getline(std::cin,line)){
  if(!line.empty()&&line.back()=='\r')line.pop_back();
  if(line.rfind("linha_original|",0)==0)continue;
  std::array<std::string_view,9> f;size_t from=0;
  for(int k=0;k<9;k++){size_t end=line.find('|',from);if((k<8&&end==std::string::npos)||(k==8&&end!=std::string::npos))throw std::runtime_error("campos invalidos");f[k]=std::string_view(line).substr(from,end==std::string::npos?line.size()-from:end-from);from=end+1;}
  I ord=integer(f[0]);if(ord<=previous)throw std::runtime_error("ordinal nao crescente");previous=ord;
  if(f[1]!=contract)continue;
  auto stamp=f[2];if(stamp.size()!=23||stamp.substr(0,10)!=date)throw std::runtime_error("timestamp invalido");
  I ms=base+digits(stamp,11,2)*3600000LL+digits(stamp,14,2)*60000LL+digits(stamp,17,2)*1000LL+digits(stamp,20,3);
  I p=integer(f[3]);if(p<=0||p%5)throw std::runtime_error("preco fora da grade");if(ms<previous_ms)throw std::runtime_error("regressao temporal");previous_ms=ms;records++;
  for(auto&l:levels){
   if(!l.eligible||l.closed)continue;
   if(ms>=cut){if(l.entered){l.closed=true;l.xo=ord;l.xm=ms;l.xp=p;l.exit=p;l.reason=3;}continue;}
   if(!l.entered){if(l.buy?p<=l.en:p>=l.en){l.entered=true;l.eo=ord;l.em=ms;l.ep=p;}continue;}
   bool stop=l.buy?p<=l.sl:p>=l.sl;bool tp=l.buy?p>=l.tp:p<=l.tp;
   if(stop||tp){l.closed=true;l.xo=ord;l.xm=ms;l.xp=p;l.exit=stop?l.sl:l.tp;l.reason=stop?1:2;}
  }
  auto it=std::lower_bound(bounds.begin(),bounds.end(),p);int idx=int(it-bounds.begin());int bucket=2*idx+(it!=bounds.end()&&*it==p);
  I minute=ms/60000;bool changed=bucket!=last_bucket;run=changed?1:std::min(3,run+1);
  if(changed||run<=2||minute!=last_minute){std::cout<<ord<<';'<<ms<<';'<<p<<'\n';emitted++;}
  last_bucket=bucket;last_minute=minute;
 }
 if(!std::cin.eof())throw std::runtime_error("falha leitura");
 std::ofstream out(argv[2]);out<<"nivel;eligible;entered;closed;entry_ord;entry_ms;entry_price;exit_ord;exit_ms;exit_price;theory_exit;reason;points\n";
 for(int k=0;k<5;k++){auto &l=levels[k];out<<k<<';'<<l.eligible<<';'<<l.entered<<';'<<l.closed<<';'<<l.eo<<';'<<l.em<<';'<<l.ep<<';'<<l.xo<<';'<<l.xm<<';'<<l.xp<<';'<<l.exit<<';'<<l.reason<<';'<<(l.closed?(l.buy?l.exit-l.en:l.en-l.exit):0)<<'\n';}
 if(!out)throw std::runtime_error("falha saida direta");
 std::cerr<<"records="<<records<<";reduced="<<emitted<<'\n';return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
