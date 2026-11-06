#include <vector>
#include <string>
#include <cmath>
#include <limits>
#include <iostream>
using string=std::string;
struct MqlTick {long time=60000,time_msc=60000001;double bid=100,ask=105,last=100;unsigned long volume=1;double volume_real=1;unsigned int flags=56;};
struct MqlRates {long time=60000;double open=100,high=110,low=100,close=110;long tick_volume=2;};
template<class T>int ArraySize(const std::vector<T>& value){return static_cast<int>(value.size());}
bool MathIsValidNumber(double value){return std::isfinite(value);}
#include "core_generated.hpp"
int checks=0,failures=0;
void check(bool value,const char*name){checks++;if(!value)failures++;std::cout<<(value?"PASS ":"FAIL ")<<name<<'\n';}
int main(){
 const long lo=60000000,hi=60120000;int trades=0;string why;
 MqlTick one,two;two.last=110;two.time_msc=60000002;
 std::vector<MqlTick> tape{one,two};
 check(HCValidate(tape,2,0,lo,hi,trades,why)&&trades==2,"flagged positive Last accepted");
 check(!HCValidate(tape,2,4403,lo,hi,trades,why),"API partial timeout rejected");
 check(!HCValidate(tape,-1,0,lo,hi,trades,why),"negative return rejected");
 check(!HCValidate(tape,1,0,lo,hi,trades,why),"array/count mismatch rejected");
 check(HCValidate({},0,0,lo,hi,trades,why)&&trades==0,"empty response not confused with trades");
 auto bad=tape;bad[0].last=std::numeric_limits<double>::quiet_NaN();
 check(!HCValidate(bad,2,0,lo,hi,trades,why),"NaN rejected before statistics");
 bad=tape;bad[0].volume_real=std::numeric_limits<double>::infinity();
 check(!HCValidate(bad,2,0,lo,hi,trades,why),"nonfinite volume rejected");
 bad=tape;bad[0].last=0;
 check(!HCValidate(bad,2,0,lo,hi,trades,why),"flagged zero Last rejected");
 bad=tape;bad[0].time_msc=hi;
 check(!HCValidate(bad,2,0,lo,hi,trades,why),"exclusive end preserved");
 bad=tape;bad[0].time_msc=lo-1;
 check(!HCValidate(bad,2,0,lo,hi,trades,why),"tick before window rejected");
 bad=tape;bad[0].time_msc=two.time_msc+1;
 check(!HCValidate(bad,2,0,lo,hi,trades,why),"reverse time rejected");
 bad=tape;bad[1].time_msc=bad[0].time_msc;
 check(HCValidate(bad,2,0,lo,hi,trades,why)&&trades==2,"same millisecond records preserved");
 bad={one};bad[0].flags=6;bad[0].last=0;
 check(HCValidate(bad,1,0,lo,hi,trades,why)&&trades==0,"bid ask only valid but not business");
 bad[0].last=100;
 check(HCValidate(bad,1,0,lo,hi,trades,why)&&trades==0,"carried Last not classified as business");
 bad={one};bad[0].flags=1336;
 check(HCValidate(bad,1,0,lo,hi,trades,why)&&trades==1,"additional flag bits preserved");
 check(HCSame(tape,tape),"exact snapshot comparison");
 bad=tape;bad[0].bid+=0.000000001;
 check(!HCSame(tape,bad),"no loss of double precision in stability");
 check(!HCSame(tape,{one}),"shorter array cannot retain stale buffer");
 int mt,mb,diff;MqlRates rate;
 check(HCM1(tape,{rate},lo,hi,mt,mb,diff,why),"minute OHLC agreement");
 rate.low=99;
 check(!HCM1(tape,{rate},lo,hi,mt,mb,diff,why)&&diff==1,"one price divergence detected");
 check(!HCM1(tape,{},lo,hi,mt,mb,diff,why)&&mb==1,"trades without minute bars detected");
 rate=MqlRates{};
 check(!HCM1({}, {rate},lo,hi,mt,mb,diff,why)&&mt==1,"minute bars without trades detected");
 check(HCM1({}, {},lo,hi,mt,mb,diff,why),"joint absence remains structurally valid not certified coverage");
 check(!HCM1(tape,{rate,rate},lo,hi,mt,mb,diff,why),"duplicate M1 rejected");
 rate.time=60060;
 check(!HCM1(tape,{rate},lo,hi,mt,mb,diff,why)&&mt==1&&mb==1,"different minute cannot be treated as whole block OHLC");
 rate.time=60000;rate.open=500;
 check(!HCM1(tape,{rate},lo,hi,mt,mb,diff,why),"malformed OHLC rejected");
 check(!HCM1(tape,{},lo,lo+16*60000,mt,mb,diff,why),"bounded minute workspace checked");
 std::cout<<"checks="<<checks<<" failures="<<failures<<'\n';return failures?1:0;
}
