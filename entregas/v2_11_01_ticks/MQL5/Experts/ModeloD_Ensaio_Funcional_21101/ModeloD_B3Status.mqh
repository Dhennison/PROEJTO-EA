#ifndef MD_B3_STATUS
#define MD_B3_STATUS
// Usa helpers do parser B3. Estado ERRO jamais fornece precos operacionais.
bool MDB3Timestamp(const string s)
{
 if(StringLen(s)!=19||!MDB3Date(StringSubstr(s,0,10))||StringSubstr(s,10,1)!=" "||
 StringSubstr(s,13,1)!=":"||StringSubstr(s,16,1)!=":"||
 !MDB3Digits(StringSubstr(s,11,2))||!MDB3Digits(StringSubstr(s,14,2))||!MDB3Digits(StringSubstr(s,17,2)))return false;
 return StringToInteger(StringSubstr(s,11,2))<24&&StringToInteger(StringSubstr(s,14,2))<60&&StringToInteger(StringSubstr(s,17,2))<60;
}
// 0 formato nao ERRO;1 envelope ERRO valido;2 envelope ERRO malformado.
int MDB3ErrorStatus(const string text,string &reason)
{
 bool error=false;int pos=0;
 while(pos<StringLen(text))
 {
  int end=StringFind(text,"\n",pos);if(end<0)end=StringLen(text);
  string line=MDB3Trim(StringSubstr(text,pos,end-pos));pos=end+1;int eq=StringFind(line,"=");
  if(eq>0&&MDB3Trim(StringSubstr(line,0,eq))=="Status"&&MDB3Trim(StringSubstr(line,eq+1))=="ERRO")error=true;
 }
 if(!error)return 0;
 reason="ARQUIVO_B3_ERRO_MALFORMADO";string keys[6];int count=0;pos=0;
 string execution="",next="",motive="",detail="",bytes="",status="";
 while(pos<StringLen(text))
 {
  int end=StringFind(text,"\n",pos);if(end<0)end=StringLen(text);
  string line=MDB3Trim(StringSubstr(text,pos,end-pos));pos=end+1;if(line=="")continue;
  int eq=StringFind(line,"=");if(eq<1||count>=6)return 2;
  string key=MDB3Trim(StringSubstr(line,0,eq)),value=MDB3Trim(StringSubstr(line,eq+1));
  for(int i=0;i<count;i++)if(keys[i]==key)return 2;
  keys[count++]=key;
  if(key=="DataExecucao")execution=value;
  else if(key=="ProximaTentativa")next=value;
  else if(key=="Motivo")motive=value;
  else if(key=="Detalhe")detail=value;
  else if(key=="BytesRecebidos")bytes=value;
  else if(key=="Status")status=value;
  else return 2;
 }
 if(count!=6||status!="ERRO"||!MDB3Timestamp(execution)||!MDB3Timestamp(next)||next<execution||
 motive==""||detail==""||StringLen(motive)>200||StringLen(detail)>500||
 (bytes!="NAO_DISPONIVEL"&&!MDB3Digits(bytes)))return 2;
 reason="FONTE_B3_STATUS_ERRO;motivo_fonte="+motive+";detalhe_fonte="+detail+";proxima_tentativa="+next;
 return 1;
}
#endif
