#property strict
#property version "1.00"
#property description "Leitura da grade WINZ26 da corretora. Nao envia ordens nem altera dados."
#property script_show_inputs
input string Contrato="WINZ26";
void OnStart()
{
 Print("SESSAO_XP;START;SOMENTE_LEITURA;servidor=",AccountInfoString(ACCOUNT_SERVER),
       ";contrato=",Contrato,";build=",TerminalInfoInteger(TERMINAL_BUILD));
 datetime server=TimeTradeServer();MqlDateTime dt;
 if(!TimeToStruct(server,dt)){Print("SESSAO_XP;FALHA_TIME_TO_STRUCT;erro=",GetLastError());return;}
 Print("SESSAO_XP;RELOGIO;servidor=",TimeToString(server,TIME_DATE|TIME_SECONDS),
       ";ultima_cotacao=",TimeToString(TimeCurrent(),TIME_DATE|TIME_SECONDS),";dia_semana=",dt.day_of_week);
 ResetLastError();
 if(!SymbolSelect(Contrato,true)){Print("SESSAO_XP;SIMBOLO_INDISPONIVEL;erro=",GetLastError());return;}
 long custom=-1;ResetLastError();bool info=SymbolInfoInteger(Contrato,SYMBOL_CUSTOM,custom);
 Print("SESSAO_XP;SIMBOLO;descricao=",SymbolInfoString(Contrato,SYMBOL_DESCRIPTION),
       ";custom_lido=",info,";custom=",custom);
 int total=0;
 for(uint i=0;i<32;i++)
 {
  datetime from=0,to=0;ResetLastError();
  bool ok=SymbolInfoSessionTrade(Contrato,(ENUM_DAY_OF_WEEK)dt.day_of_week,i,from,to);
  int error=GetLastError();
  if(!ok){Print("SESSAO_XP;FIM_CONSULTA;indice=",i,";erro=",error);break;}
  total++;
  long begin=(long)from%86400,end=(long)to%86400;
  Print("SESSAO_XP;TRADE;indice=",i,";inicio=",TimeToString(from,TIME_SECONDS),
        ";fim=",TimeToString(to,TIME_SECONDS),";from_raw=",(long)from,";to_raw=",(long)to,
        ";begin_s=",begin,";end_s=",end,
        ";passa_filtro_horario_v213=",(begin==32400&&end>=64800&&end<86400));
 }
 Print("SESSAO_XP;END;total_sessoes=",total,";SEM_ORDENS;SEM_ALTERAR_EA");
}
