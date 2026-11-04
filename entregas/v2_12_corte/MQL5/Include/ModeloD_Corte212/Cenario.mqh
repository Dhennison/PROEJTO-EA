#ifndef MD_CORTE212_CENARIO
#define MD_CORTE212_CENARIO
// Fita inteiramente SINTETICA. Horarios civis do servidor/BRT, nao UTC real.
const long MD_CORTE212_BEGIN=1793350844000,MD_CORTE212_FILL=1793351100000,MD_CORTE212_END=1793383800000;
const int MD_CORTE212_COUNT=32957;
double MDCortePrice212(long stamp)
{if(stamp<MD_CORTE212_FILL)return 170910;if(stamp==MD_CORTE212_FILL)return 169800;return 169900;}
void MDCorteTick212(int index,MqlTick &tick)
{
 ZeroMemory(tick);tick.time_msc=MD_CORTE212_BEGIN+(long)index*1000;tick.time=(datetime)(tick.time_msc/1000);
 tick.last=MDCortePrice212(tick.time_msc);tick.bid=tick.last-5;tick.ask=tick.last;
 tick.volume=1;tick.volume_real=1;tick.flags=TICK_FLAG_BID|TICK_FLAG_ASK|TICK_FLAG_LAST|TICK_FLAG_VOLUME|TICK_FLAG_BUY;
}
bool MDCorteTickSame212(const MqlTick &tick,int index)
{
 MqlTick expected;MDCorteTick212(index,expected);
 return tick.time_msc==expected.time_msc&&tick.last==expected.last&&tick.bid==expected.bid&&tick.ask==expected.ask&&
        tick.volume==1&&tick.volume_real==1&&(tick.flags&120)==56;
}
#endif
