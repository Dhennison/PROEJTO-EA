
bool prep_created212=false,prep_real_name212=false,prep_source_missing212=false;
int prep_writes212=0,prep_foreign_writes212=0;
bool SymbolExist(string name,bool &custom){
 if(name=="WINZ26"){custom=false;return !prep_source_missing212;}
 if(name=="MD_SINT_CORTE_WINZ26"){custom=!prep_real_name212;return prep_created212||prep_real_name212;}
 custom=false;return false;
}
bool CustomSymbolCreate(string name,string folder,string origin){
 if(name!="MD_SINT_CORTE_WINZ26"||origin!="WINZ26"||prep_created212){prep_foreign_writes212++;return false;}
 prep_created212=true;return true;
}
int CustomRatesReplace(string name,datetime,datetime,const std::vector<MqlRates> &rows){
 if(name!="MD_SINT_CORTE_WINZ26"){prep_foreign_writes212++;return -1;}
 prep_writes212++;prep_rates212=rows;return rows.size();
}
int CustomTicksReplace(string name,ulong,ulong,const std::vector<MqlTick> &ticks){
 if(name!="MD_SINT_CORTE_WINZ26"){prep_foreign_writes212++;return -1;}
 prep_writes212++;prep_ticks212=ticks;std::map<long,MqlRates> bars;
 for(auto q:ticks){long minute=q.time_msc/60000*60;
  if(!bars.count(minute))bars[minute]={minute,q.last,q.last,q.last,q.last,0,0};
  auto &bar=bars[minute];bar.high=std::max(bar.high,q.last);bar.low=std::min(bar.low,q.last);bar.close=q.last;bar.tick_volume++;bar.real_volume++;
 }
 for(auto &item:bars)prep_rates212.push_back(item.second);
 return ticks.size();
}
PREPARATION_SCRIPT_BODY
int main(){
 std::cout.setf(std::ios::unitbuf);
 std::filesystem::remove_all("/tmp/md615k_host");std::filesystem::create_directories("/tmp/md615k_host");
 ResetCase212();mock_tester210=false;prep_mode212=true;
 for(int k=0;k<565;k++)prep_prior212.push_back({MDCivilMidnight2026(20261029)/1000+9*3600+k*60,170000,170005,169995,170000,10,10});
 OnStart();
 Check210(prep_created212&&prep_writes212==2&&prep_ticks212.size()==32957,"actual preparation script creates only new synthetic symbol and complete tick recipe");
 Check210(CutCheck(prep_prior212),"actual script verifies copied prior bars, all ticks and all 551 synthetic M1 bars");
 if(prep_ticks212.size()<101){Print("PREPARATION_212;EARLY_FAILURE;incomplete fixture");return 1;}
 int before=prep_writes212;OnStart();Check210(prep_writes212==before,"identical existing scenario is reused read-only");
 prep_ticks212[100].bid-=5;OnStart();Check210(prep_writes212==before&&!CutCheck(prep_prior212),"existing divergent scenario is refused without overwriting");
 prep_real_name212=true;OnStart();Check210(prep_writes212==before,"existing non-custom name cannot be overwritten");prep_real_name212=false;
 prep_created212=false;prep_source_missing212=true;OnStart();Check210(!prep_created212&&prep_writes212==before,"missing original symbol blocks preparation before creation");prep_source_missing212=false;
 prep_prior212.resize(1);OnStart();Check210(!prep_created212&&prep_writes212==before,"insufficient prior history cannot create a partial scenario");
 mock_tester210=true;OnStart();Check210(!prep_created212&&prep_writes212==before,"preparation script refuses execution inside Tester");
 Check210(prep_foreign_writes212==0&&mock_send_calls210==0,"preparation never writes WINZ26 or any historical research symbol and never sends orders");
 Print("PREPARATION_212;Checks=",checks210,";Failures=",failures210,";API_MOCK_NOT_NATIVE_MQL5");return failures210?1:0;
}
