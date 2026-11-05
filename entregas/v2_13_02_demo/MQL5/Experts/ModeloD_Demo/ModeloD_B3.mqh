#ifndef MODELOD_B3_MQH
#define MODELOD_B3_MQH
// Parser puro do formato operacional observado em 15/10/2026.
// Validade estrutural NAO comprova calendario, contrato vigente ou autorizacao.
struct MDB3Record { string symbol; double adjustment, previous; bool has_adjustment, has_previous; };
struct MDB3File
{
   bool validated;
   string source_date, operational_date, source, status;
   int count;
   MDB3Record records[128];
};
string MDB3Trim(string s) { StringTrimLeft(s); StringTrimRight(s); return s; }
bool MDB3Digits(const string s)
{
   if(StringLen(s)==0) return false;
   for(int i=0;i<StringLen(s);i++)
      if(StringGetCharacter(s,i)<48 || StringGetCharacter(s,i)>57) return false;
   return true;
}
bool MDB3Symbol(const string s)
{
   return StringLen(s)==6 && StringSubstr(s,0,3)=="WIN" &&
      StringFind("FGHJKMNQUVXZ",StringSubstr(s,3,1))>=0 && MDB3Digits(StringSubstr(s,4,2));
}
bool MDB3Date(const string s)
{
   if(StringLen(s)!=10 || StringSubstr(s,4,1)!="-" || StringSubstr(s,7,1)!="-" ||
      !MDB3Digits(StringSubstr(s,0,4)) || !MDB3Digits(StringSubstr(s,5,2)) || !MDB3Digits(StringSubstr(s,8,2))) return false;
   int y=(int)StringToInteger(StringSubstr(s,0,4)),m=(int)StringToInteger(StringSubstr(s,5,2)),d=(int)StringToInteger(StringSubstr(s,8,2));
   if(y<2000 || m<1 || m>12 || d<1) return false;
   int days=31;
   if(m==4 || m==6 || m==9 || m==11) days=30;
   if(m==2) days=(y%4==0 && (y%100!=0 || y%400==0)) ? 29 : 28;
   return d<=days;
}
bool MDB3Number(const string s,double &v)
{
   int dots=0;
   if(StringLen(s)==0) return false;
   for(int i=0;i<StringLen(s);i++)
   {
      int c=StringGetCharacter(s,i);
      if(c==46) { if(++dots>1 || i==0 || i==StringLen(s)-1) return false; }
      else if(c<48 || c>57) return false;
   }
   v=StringToDouble(s); return MathIsValidNumber(v) && v>0;
}
bool MDB3Fail(string &reason,const string message) { reason=message; return false; }
#include "ModeloD_B3Status.mqh"
bool MDB3Parse(const string text,MDB3File &out,string &reason)
{
   out.validated=false;
   out.source_date=""; out.operational_date=""; out.source=""; out.status=""; out.count=0;
   reason="";
   string keys[512]; int key_count=0,declared=-1,pos=0,lines=0;
   if(StringLen(text)==0 || StringLen(text)>131072) return MDB3Fail(reason,"TAMANHO_INVALIDO");
   if(MDB3ErrorStatus(text,reason)!=0)return false;
   while(pos<StringLen(text))
   {
      if(++lines>2000) return MDB3Fail(reason,"LIMITE_LINHAS");
      int end=StringFind(text,"\n",pos); if(end<0) end=StringLen(text);
      string line=MDB3Trim(StringSubstr(text,pos,end-pos)); pos=end+1;
      if(line=="") continue;
      // BOM UTF-8 e removido pelo adaptador antes de chamar este parser.
      int eq=StringFind(line,"=");
      if(eq<1) return MDB3Fail(reason,"LINHA_INVALIDA");
      string key=MDB3Trim(StringSubstr(line,0,eq)),value=MDB3Trim(StringSubstr(line,eq+1));
      for(int k=0;k<key_count;k++) if(keys[k]==key) return MDB3Fail(reason,"CHAVE_DUPLICADA: "+key);
      if(key_count>=512) return MDB3Fail(reason,"LIMITE_CHAVES");
      keys[key_count++]=key;
      if(key=="DataExecucao") { if(!MDB3Timestamp(value)) return MDB3Fail(reason,"DATA_EXECUCAO_INVALIDA"); }
      else if(key=="DataFonte") out.source_date=value;
      else if(key=="DataOperacional") out.operational_date=value;
      else if(key=="Fonte") out.source=value;
      else if(key=="Status") out.status=value;
      else if(key=="Modo") { if(value!="OPERACIONAL") return MDB3Fail(reason,"MODO_NAO_OPERACIONAL"); }
      else if(key=="QuantidadeContratos")
      {
         if(!MDB3Digits(value) || StringLen(value)>3) return MDB3Fail(reason,"CONTAGEM_INVALIDA");
         declared=(int)StringToInteger(value);
         if(declared<1 || declared>128) return MDB3Fail(reason,"CONTAGEM_INVALIDA");
      }
      else if(StringSubstr(key,0,9)=="Contrato.")
      {
         if(StringLen(key)<17 || StringSubstr(key,15,1)!=".") return MDB3Fail(reason,"CAMPO_CONTRATO_INVALIDO");
         string symbol=StringSubstr(key,9,6),field=StringSubstr(key,16);
         if(!MDB3Symbol(symbol)) return MDB3Fail(reason,"TICKER_INVALIDO");
         if(field!="Ajuste" && field!="AjusteAnterior") return MDB3Fail(reason,"CAMPO_DESCONHECIDO");
         double number=0; if(!MDB3Number(value,number)) return MDB3Fail(reason,"NUMERO_INVALIDO");
         int idx=-1;
         for(int k=0;k<out.count;k++) if(out.records[k].symbol==symbol) { idx=k; break; }
         if(idx<0)
         {
            if(out.count>=128) return MDB3Fail(reason,"LIMITE_CONTRATOS");
            idx=out.count++; out.records[idx].symbol=symbol;
            out.records[idx].adjustment=0; out.records[idx].previous=0;
            out.records[idx].has_adjustment=false; out.records[idx].has_previous=false;
         }
         if(field=="Ajuste") { out.records[idx].adjustment=number; out.records[idx].has_adjustment=true; }
         else { out.records[idx].previous=number; out.records[idx].has_previous=true; }
      }
      else return MDB3Fail(reason,"CHAVE_DESCONHECIDA: "+key);
   }
   if(out.status!="OK") return MDB3Fail(reason,"STATUS_NAO_OK");
   if(out.source!="BVBG.187.01") return MDB3Fail(reason,"FONTE_INVALIDA");
   if(!MDB3Date(out.source_date) || !MDB3Date(out.operational_date) || out.source_date>=out.operational_date)
      return MDB3Fail(reason,"DATAS_INVALIDAS");
   if(out.count!=declared) return MDB3Fail(reason,"CONTAGEM_DIVERGENTE");
   for(int i=0;i<out.count;i++) if(!out.records[i].has_adjustment || !out.records[i].has_previous)
      return MDB3Fail(reason,"PAR_INCOMPLETO: "+out.records[i].symbol);
   out.validated=true; return true;
}
bool MDB3Select(const MDB3File &data,const string session_date,const string real_symbol,
               double &adjustment,double &previous,string &reason)
{
   // Chamador deve usar somente objeto retornado por Parse=true.
   adjustment=0; previous=0; reason="";
   if(!data.validated) return MDB3Fail(reason,"ARQUIVO_NAO_VALIDADO");
   if(!MDB3Date(session_date) || data.operational_date!=session_date) return MDB3Fail(reason,"SESSAO_DIVERGENTE");
   if(!MDB3Symbol(real_symbol)) return MDB3Fail(reason,"CONTRATO_INVALIDO");
   for(int i=0;i<data.count;i++) if(data.records[i].symbol==real_symbol)
   {
      adjustment=data.records[i].adjustment; previous=data.records[i].previous; return true;
   }
   return MDB3Fail(reason,"CONTRATO_AUSENTE");
}
#endif
