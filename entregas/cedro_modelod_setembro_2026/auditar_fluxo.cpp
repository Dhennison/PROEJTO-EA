// Agrega a fita sem ordenar/deduplicar. Resultado comparado ao auditor Python anterior.
#include <algorithm>
#include <array>
#include <fstream>
#include <iostream>
#include <map>
#include <stdexcept>
#include <string>
#include <string_view>
#include <cstdlib>
using I=long long;
I integer(std::string_view v){std::string s(v);char *e=nullptr;I x=std::strtoll(s.c_str(),&e,10);if(e==s.c_str())throw std::runtime_error("numero invalido");if(*e=='.'){++e;while(*e=='0')++e;}if(*e)throw std::runtime_error("valor nao inteiro");return x;}
struct Bar{I n=0,o=0,h=0,l=0,c=0,q=0;void add(I p,I qty){if(!n){o=h=l=p;}h=std::max(h,p);l=std::min(l,p);c=p;q+=qty;n++;}};
struct Stats{Bar bar;I regress=0,ties=0;std::string first,last,previous_line;std::map<std::string,I> conditions,aggressors;};
int main(int argc,char**argv){try{
 if(argc!=4)throw std::runtime_error("data simbolo prefixo");
 std::string date=argv[1],symbol=argv[2],prefix=argv[3];
 std::ios::sync_with_stdio(false);std::cin.tie(nullptr);std::map<std::string,Stats> all;std::map<std::string,Bar> minutes;
 std::ofstream anomalies(prefix+"_REGRESSOES.csv");anomalies<<"ativo;linha_anterior;linha_atual\n";
 I previous=0;std::string line;
 while(std::getline(std::cin,line)){
  if(!line.empty()&&line.back()=='\r')line.pop_back();
  if(line.rfind("linha_original|",0)==0)continue;
  std::array<std::string_view,9> f;size_t from=0;
  for(int k=0;k<9;k++){size_t end=line.find('|',from);if((k<8&&end==std::string::npos)||(k==8&&end!=std::string::npos))throw std::runtime_error("campos invalidos");f[k]=std::string_view(line).substr(from,end==std::string::npos?line.size()-from:end-from);from=end+1;}
  I ordinal=integer(f[0]);if(ordinal<=previous)throw std::runtime_error("ordinal nao crescente");previous=ordinal;
  if(f[2].size()!=23||f[2].substr(0,10)!=date)throw std::runtime_error("data invalida");
  I p=integer(f[3]),q=integer(f[4]);if(p<=0||p%5||q<=0)throw std::runtime_error("preco/quantidade invalidos");
  std::string sym(f[1]),stamp(f[2]);auto &s=all[sym];
  if(!s.bar.n)s.first=stamp;
  else{if(stamp<s.last){s.regress++;anomalies<<sym<<';'<<s.previous_line<<';'<<line<<'\n';}if(stamp==s.last)s.ties++;}
  s.last=stamp;s.previous_line=line;s.bar.add(p,q);s.conditions[std::string(f[8])]++;s.aggressors[std::string(f[7])]++;
  if(sym==symbol)minutes[stamp.substr(0,16)].add(p,q);
 }
 if(!std::cin.eof())throw std::runtime_error("falha leitura");
 std::ofstream stats(prefix+"_CONTRATOS.csv");stats<<"ativo;registros;regressoes;empates;primeiro;ultimo;open;high;low;close;quantidade\n";
 std::ofstream codes(prefix+"_CODIGOS.csv");codes<<"ativo;campo;codigo;registros\n";
 for(auto &pair:all){auto&s=pair.second;auto&b=s.bar;stats<<pair.first<<';'<<b.n<<';'<<s.regress<<';'<<s.ties<<';'<<s.first<<';'<<s.last<<';'<<b.o<<';'<<b.h<<';'<<b.l<<';'<<b.c<<';'<<b.q<<'\n';for(auto&x:s.conditions)codes<<pair.first<<";8;"<<x.first<<';'<<x.second<<'\n';for(auto&x:s.aggressors)codes<<pair.first<<";7;"<<x.first<<';'<<x.second<<'\n';}
 std::ofstream bars(prefix+"_M1.csv");bars<<"time;open;high;low;close;volume_real;registros\n";
 for(auto&pair:minutes){auto&b=pair.second;bars<<pair.first<<';'<<b.o<<';'<<b.h<<';'<<b.l<<';'<<b.c<<';'<<b.q<<';'<<b.n<<'\n';}
 if(!stats||!codes||!bars||!anomalies)throw std::runtime_error("falha saida");
 std::cerr<<"ordinal_final="<<previous<<'\n';return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
