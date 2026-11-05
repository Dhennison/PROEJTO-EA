int main(){
 int status=compat21101();if(status)return status;
 Reset210();UsarConsultaAllFiltradaNoTester=true;md_comparacoes21101=0;
 mock_empty_trade21101=true;
 mock_all_ticks.insert(mock_all_ticks.begin(),MqlTick{Begin210(),210000,2});
 bool durable=true;AcceptOrders210(durable);
 Check210(OnInit()==INIT_SUCCEEDED,"21101 native ALL experiment starts without custom symbol");
 Bootstrap210();
 Check210(opening208.confirmed&&opening208.first_msc==Begin210()+1000,
  "21101 actual EA skips book prefix and confirms opening when TRADE is empty");
 Check210(mock_send_calls210==5&&durable,
  "21101 actual EA prepares five orders durably from ALL evidence");
 bool native=true;for(auto r:mock_requests210)native=native&&r.symbol=="WINZ26";
 Check210(native,"21101 native WINZ26 route preserved for every request");
 int sent=mock_send_calls210;Tick210();Tick210();
 Check210(mock_send_calls210==sent,"21101 repeated timers cannot duplicate accepted orders");
 OnDeinit(1);
 std::cout<<"FOCUSED_21101;Checks="<<checks210<<";Failures="<<failures210<<";API_MOCK_NOT_NATIVE_MQL5\n";
 return failures210?1:0;
}
