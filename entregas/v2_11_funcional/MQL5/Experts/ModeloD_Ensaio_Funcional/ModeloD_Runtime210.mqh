#ifndef MD_RUNTIME210
#define MD_RUNTIME210
// Explicit opt-in applies ONLY to the Strategy Tester. Never to a connected account.
input bool ExecutarNoTester=false;
input int DataTester=20261030;
input string ContratoTester="WINZ26";
input int FusoServidorTester=-10800;
bool MDIsTester210(){return (bool)MQLInfoInteger(MQL_TESTER);}
bool MDConnected210(){return MDIsTester210()||TerminalInfoInteger(TERMINAL_CONNECTED);}
// Virtual replay identity: independent of a broker login (which can be zero in an agent).
long MDAccount210(){return MDIsTester210()?1:AccountInfoInteger(ACCOUNT_LOGIN);}
string MDServer210(){return MDIsTester210()?"STRATEGY_TESTER":AccountInfoString(ACCOUNT_SERVER);}
// Retry schedules follow simulated time; API durations still use GetTickCount64.
long MDLogicalMillis210(){return MDIsTester210()?(long)TimeCurrent()*1000:(long)GetTickCount64();}
string tester_prefix210="";
bool MDTesterGate210()
{return MDIsTester210()&&ExecutarNoTester&&!MQLInfoInteger(MQL_OPTIMIZATION)&&tester_prefix210!="";}
#endif
