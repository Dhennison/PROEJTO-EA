#ifndef MD_RUNTIME_DEMO213
#define MD_RUNTIME_DEMO213
input bool ExecutarNaDemo=false;
long demo_bound_account213=0;
string demo_bound_server213="",demo_prefix213="MDD213_DEMO_";
bool MDIsTester210(){return (bool)MQLInfoInteger(MQL_TESTER);}
bool MDConnected213(){return (bool)TerminalInfoInteger(TERMINAL_CONNECTED);}
long MDAccount213(){return AccountInfoInteger(ACCOUNT_LOGIN);}
string MDServer213(){return AccountInfoString(ACCOUNT_SERVER);}
long MDLogicalMillis213(){return (long)GetTickCount64();}
bool MDDemoAccount213(string &why)
{
 if(MDIsTester210()){why="EXECUTAR_NA_CONTA_DEMO_FORA_DO_TESTER";return false;}
 ResetLastError();long mode=AccountInfoInteger(ACCOUNT_TRADE_MODE);int error=GetLastError();
 if(error!=0){why="TIPO_CONTA_INDISPONIVEL";return false;}
 if(mode!=ACCOUNT_TRADE_MODE_DEMO){why="CONTA_REAL_OU_CONTEST_BLOQUEADA;EXIGE_ACCOUNT_TRADE_MODE_DEMO";return false;}
 if(MDAccount213()<=0||MDServer213()==""){why="IDENTIDADE_CONTA_DEMO_INDISPONIVEL";return false;}
 if(AccountInfoInteger(ACCOUNT_MARGIN_MODE)!=ACCOUNT_MARGIN_MODE_RETAIL_HEDGING){why="CONTA_DEMO_PRECISA_SER_HEDGE";return false;}
 if(AccountInfoString(ACCOUNT_CURRENCY)!="BRL"){why="CONTA_DEMO_B3_REQUER_BRL";return false;}
 why="DEMO_HEDGE_BRL_CONFIRMADA";return true;
}
bool MDDemoIdentity213()
{
 string why;
 return demo_bound_account213>0&&demo_bound_server213!=""&&MDDemoAccount213(why)&&
        MDAccount213()==demo_bound_account213&&MDServer213()==demo_bound_server213;
}
bool MDDemoGate213()
{
 return ExecutarNaDemo&&MDDemoIdentity213()&&MDConnected213()&&
  TerminalInfoInteger(TERMINAL_TRADE_ALLOWED)&&MQLInfoInteger(MQL_TRADE_ALLOWED)&&
  AccountInfoInteger(ACCOUNT_TRADE_ALLOWED)&&AccountInfoInteger(ACCOUNT_TRADE_EXPERT);
}
string MDDemoPermission213()
{
 if(!MDDemoIdentity213())return "IDENTIDADE_OU_TIPO_CONTA_INVALIDO";
 if(!ExecutarNaDemo)return "OBSERVACAO;ExecutarNaDemo=false";
 if(!MDConnected213())return "SEM_CONEXAO";
 if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED))return "AUTOTRADING_DO_TERMINAL_DESLIGADO";
 if(!MQLInfoInteger(MQL_TRADE_ALLOWED))return "NEGOCIACAO_ALGORITMICA_DO_EA_DESLIGADA";
 if(!AccountInfoInteger(ACCOUNT_TRADE_ALLOWED)||!AccountInfoInteger(ACCOUNT_TRADE_EXPERT))return "SERVIDOR_NAO_PERMITE_EA_OU_NEGOCIACAO";
 return "TRANSPORTE_DEMO_HABILITADO;AINDA_EXIGE_DADOS_E_CONCILIACAO";
}
#endif
