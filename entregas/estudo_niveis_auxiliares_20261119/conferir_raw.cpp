#include <algorithm>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <string_view>
#include <vector>
#include <array>
#include <stdexcept>
using I=long long;
struct E{I ord,ms,p;};
struct S{int eligible,buy;I en,sl,tp;bool active=false,closed=false,mixed=false;I em=0,xm=0,eo=0,xo=0,pts=0;int reason=0;};
void step(S&s,E e,I cut){if(!s.eligible||s.closed)return;if(e.ms>=cut){if(s.active){s.closed=true;s.xm=e.ms;s.xo=e.ord;s.pts=s.buy?e.p-s.en:s.en-e.p;s.reason=3;}return;}if(!s.active){if(s.buy?e.p<=s.en:e.p>=s.en){s.active=true;s.em=e.ms;s.eo=e.ord;}return;}if(s.buy?e.p<=s.sl:e.p>=s.sl){s.closed=true;s.reason=1;s.pts=s.buy?s.sl-s.en:s.en-s.sl;}else if(s.buy?e.p>=s.tp:e.p<=s.tp){s.closed=true;s.reason=2;s.pts=s.buy?s.tp-s.en:s.en-s.tp;}if(s.closed){s.xm=e.ms;s.xo=e.ord;}}
I num(std::string_view v){std::string s(v);size_t pos;I r=std::stoll(s,&pos);if(pos<s.size()&&s[pos]=='.'){pos++;while(pos<s.size()&&s[pos]=='0')pos++;}if(pos!=s.size())throw std::runtime_error("number");return r;}
int main(int argc,char**argv){try{std::ifstream cfg(argv[1]);std::string contract,date;I cut;int n;cfg>>contract>>date>>cut>>n;std::vector<S>a(n),b(n);for(auto&s:a)cfg>>s.eligible>>s.buy>>s.en>>s.sl>>s.tp;if(!cfg)throw std::runtime_error("config");b=a;std::ios::sync_with_stdio(false);std::cin.tie(nullptr);I records=0,prev=0,prevms=-1;std::vector<E>group;
auto flush=[&](){if(group.empty())return;I low=group[0].p,high=low;for(E e:group){low=std::min(low,e.p);high=std::max(high,e.p);}for(int i=0;i<n;i++){bool consider= !a[i].closed;for(E e:group)step(a[i],e,cut);for(auto j=group.rbegin();j!=group.rend();j++)step(b[i],*j,cut);if(consider&&(a[i].active||b[i].active)&&((low<=std::min(a[i].sl,a[i].tp)&&high>=std::max(a[i].sl,a[i].tp))||(a[i].em==group[0].ms&&(a[i].buy?high>=a[i].tp:low<=a[i].tp)))){a[i].mixed=true;b[i].mixed=true;}}group.clear();};
std::string line;while(std::getline(std::cin,line)){if(line.rfind("linha_original|",0)==0)continue;if(!line.empty()&&line.back()=='\r')line.pop_back();std::array<std::string_view,9>f;size_t from=0;for(int k=0;k<9;k++){size_t end=line.find('|',from);if(k<8&&end==std::string::npos)throw std::runtime_error("fields");f[k]=std::string_view(line).substr(from,end==std::string::npos?line.size()-from:end-from);from=end+1;}I ord=num(f[0]);if(ord<=prev)throw std::runtime_error("ordinal");prev=ord;if(f[1]!=contract)continue;auto t=f[2];if(t.size()!=23||t.substr(0,10)!=date)throw std::runtime_error("date");I ms=std::stoi(std::string(t.substr(11,2)))*3600000LL+std::stoi(std::string(t.substr(14,2)))*60000LL+std::stoi(std::string(t.substr(17,2)))*1000LL+std::stoi(std::string(t.substr(20,3)));if(ms<prevms)throw std::runtime_error("time");I p=num(f[3]);if(p<=0||p%5)throw std::runtime_error("price");if(ms!=prevms)flush();prevms=ms;group.push_back({ord,ms,p});records++;}flush();std::cout<<"index;entered;closed;reason;points;entry_ms;exit_ms;resolved\n";for(int i=0;i<n;i++){auto s=a[i],t=b[i];bool ok=s.active==t.active&&s.closed==t.closed&&s.reason==t.reason&&s.pts==t.pts&&!s.mixed&&!t.mixed;std::cout<<i<<';'<<s.active<<';'<<s.closed<<';'<<s.reason<<';'<<s.pts<<';'<<s.em<<';'<<s.xm<<';'<<ok<<'\n';}std::cerr<<records<<'\n';}catch(std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
