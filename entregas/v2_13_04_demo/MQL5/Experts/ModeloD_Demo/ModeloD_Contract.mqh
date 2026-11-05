#ifndef MODELOD_CONTRACT_MQH
#define MODELOD_CONTRACT_MQH
#include "ModeloD_B3.mqh"
// Mesma origem usada pelo indicador B3: ticker entre parenteses na descricao.
// Nao escolhe por calendario, volume, data atual ou presenca no arquivo B3.
bool MDContractCandidate(const string chart_symbol,const string description,
                         string &candidate,string &reason)
{
   candidate="";reason="";
   if(chart_symbol!="WIN$N") return MDB3Fail(reason,"GRAFICO_NAO_WIN_N");
   int pos=0;
   while(true)
   {
      int a=StringFind(description,"(",pos);if(a<0)break;
      int b=StringFind(description,")",a+1);
      if(b<0) { candidate="";return MDB3Fail(reason,"DESCRICAO_MALFORMADA"); }
      string token=MDB3Trim(StringSubstr(description,a+1,b-a-1));
      if(MDB3Symbol(token))
      {
         if(candidate!="" && candidate!=token)
         { candidate="";return MDB3Fail(reason,"CONTRATO_AMBIGUO"); }
         candidate=token;
      }
      else if(StringSubstr(token,0,3)=="WIN")
      { candidate="";return MDB3Fail(reason,"TICKER_MALFORMADO_NA_DESCRICAO"); }
      pos=b+1;
   }
   if(candidate=="")return MDB3Fail(reason,"CONTRATO_NAO_IDENTIFICADO");
   return true; // Candidato; calendario B3 e demais validacoes continuam obrigatorios.
}
#endif
