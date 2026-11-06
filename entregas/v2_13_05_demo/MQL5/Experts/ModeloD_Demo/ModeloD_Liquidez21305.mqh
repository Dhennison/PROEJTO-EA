#ifndef MD_LIQUIDEZ21305
#define MD_LIQUIDEZ21305
string liquidity_signature21305="";long liquidity_last21305=0;
string MDLiquidityRead21305(string symbol) {
 if(symbol=="")return "contrato=NAO_OBSERVADO;volume_conhecido=0;tick_conhecido=0";
 double volume=0;MqlTick tick;bool selected=MDSymbolSelect213(symbol,true);
 bool volume_known=selected&&MDSymbolInfoDouble213(symbol,SYMBOL_SESSION_VOLUME,volume)&&MathIsValidNumber(volume)&&volume>=0;
 bool tick_known=selected&&MDSymbolInfoTick213(symbol,tick)&&tick.time_msc>0;
 return "contrato="+symbol+";volume_conhecido="+IntegerToString(volume_known?1:0)+
  ";volume_sessao="+(volume_known?DoubleToString(volume,8):"NAO_DISPONIVEL")+
  ";tick_conhecido="+IntegerToString(tick_known?1:0)+";ultimo_msc="+(tick_known?IntegerToString(tick.time_msc):"NAO_DISPONIVEL");
}
void MDLiquidityAudit21305(int date,string description) {
 string candidate,why;if(!MDContractCandidate("WIN$N",description,candidate,why))return;
 string previous="";int latest=0;
 for(int k=0;k<operational.nlevels;k++)if(operational.levels[k].date<=date&&operational.levels[k].date>=latest&&
   operational.levels[k].symbol!=candidate){latest=operational.levels[k].date;previous=operational.levels[k].symbol;}
 if(previous==""&&obs615.frozen&&obs615.data.contract!=candidate)previous=obs615.data.contract;
 string signature=IntegerToString(date)+"_"+previous+"_"+candidate;
 if(signature==liquidity_signature21305&&(previous==""||opclock.utc-liquidity_last21305<60000))return;
 liquidity_signature21305=signature;liquidity_last21305=opclock.utc;
 Report615("LIQUIDEZ21305;data="+IntegerToString(date)+";ANTIGO;"+MDLiquidityRead21305(previous)+
  ";CANDIDATO;"+MDLiquidityRead21305(candidate)+";SOMENTE_AUDITORIA;NAO_ESCOLHE_CONTRATO;SEM_FILTRO_ESTRATEGICO");
}
#endif
