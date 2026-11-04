#ifndef MODELOD_CHART_MQH
#define MODELOD_CHART_MQH
#include "ModeloD_Visual.mqh"
#include "ModeloD_VisibleCenter.mqh"
// Nomes reservados exclusivos da instancia no grafico. Sem exclusao global.
// Uma instancia por grafico; nao compartilhar Instancia entre EAs concorrentes.
string MDVisualPrefix(const uint instance) { return "DRP_MD615_VIS_"+IntegerToString(instance)+"_"; }
bool MDVisualDelete(const long chart,const string name)
{
   if(ObjectFind(chart,name)<0) return true;
   if(!ObjectDelete(chart,name)) return false;
   return ObjectFind(chart,name)<0; // confirma processamento da fila
}
bool MDVisualClear(const long chart,const uint instance)
{
   string keys[10]={"R200","S200","R236","R382","R50","R618","S236","S382","S50","S618"};
   bool ok=true;
   for(int i=0;i<10;i++)
   {
      if(!MDVisualDelete(chart,MDVisualPrefix(instance)+keys[i]+"_LINE")) ok=false;
      if(!MDVisualDelete(chart,MDVisualPrefix(instance)+keys[i]+"_TEXT")) ok=false;
   }
   ChartRedraw(chart);return ok;
}
bool MDVisualDrawLine(const long chart,const string prefix,const MDVisualLine &l,
                      const datetime begin,const datetime end,const datetime label_time)
{
   string line=prefix+l.key+"_LINE",label=prefix+l.key+"_TEXT";
   if(!l.visible)
   {
      bool a=MDVisualDelete(chart,line),b=MDVisualDelete(chart,label);return a && b;
   }
   if(ObjectFind(chart,line)>=0 && ObjectGetInteger(chart,line,OBJPROP_TYPE)!=OBJ_TREND)
      if(!MDVisualDelete(chart,line)) return false;
   if(ObjectFind(chart,label)>=0 && ObjectGetInteger(chart,label,OBJPROP_TYPE)!=OBJ_TEXT)
      if(!MDVisualDelete(chart,label)) return false;
   if(ObjectFind(chart,line)<0 && !ObjectCreate(chart,line,OBJ_TREND,0,begin,l.price,end,l.price)) return false;
   if(!ObjectMove(chart,line,0,begin,l.price) || !ObjectMove(chart,line,1,end,l.price)) return false;
   color ink=l.support ? clrLimeGreen : clrRed;
   if(!ObjectSetInteger(chart,line,OBJPROP_RAY_LEFT,false) ||
      !ObjectSetInteger(chart,line,OBJPROP_RAY_RIGHT,false) ||
      !ObjectSetInteger(chart,line,OBJPROP_COLOR,ink) ||
      !ObjectSetInteger(chart,line,OBJPROP_WIDTH,l.reference ? 2 : 1) ||
      !ObjectSetInteger(chart,line,OBJPROP_STYLE,l.reference ? STYLE_SOLID : STYLE_DASH) ||
      !ObjectSetInteger(chart,line,OBJPROP_SELECTABLE,false)) return false;
   if(label_time==0)return MDVisualDelete(chart,label);
   // Ancora acima/abaixo do MESMO preco, nunca desloca o nivel para legibilidade.
   // Centro horizontal visivel comum; suporte abaixo e resistencia acima.
   datetime at=label_time;
   if(ObjectFind(chart,label)<0 && !ObjectCreate(chart,label,OBJ_TEXT,0,at,l.price)) return false;
   if(!ObjectMove(chart,label,0,at,l.price) ||
      !ObjectSetInteger(chart,label,OBJPROP_ANCHOR,l.support ? ANCHOR_UPPER : ANCHOR_LOWER) ||
      !ObjectSetInteger(chart,label,OBJPROP_COLOR,ink) ||
      !ObjectSetInteger(chart,label,OBJPROP_FONTSIZE,9) ||
      !ObjectSetInteger(chart,label,OBJPROP_SELECTABLE,false) ||
      !ObjectSetString(chart,label,OBJPROP_TEXT,l.label+"  "+DoubleToString(l.price,0))) return false;
   return ObjectFind(chart,line)>=0 && ObjectFind(chart,label)>=0 &&
      ObjectGetDouble(chart,line,OBJPROP_PRICE,0)==l.price &&
      ObjectGetDouble(chart,line,OBJPROP_PRICE,1)==l.price &&
      ObjectGetInteger(chart,line,OBJPROP_TIME,0)==begin &&
      ObjectGetInteger(chart,line,OBJPROP_TIME,1)==end &&
      ObjectGetDouble(chart,label,OBJPROP_PRICE,0)==l.price;
}
bool MDVisualSync(const long chart,const uint instance,const MDDay &day,
                  const datetime begin,const datetime end,const bool validated_session)
{
   // O controlador deve validar sessao/contrato/OHLC/Ajuste e converter horarios
   // para timestamps do grafico. Este parametro nao faz essas validacoes sozinho.
   if(!validated_session || begin<=0 || end<=begin) return MDVisualClear(chart,instance);
   // Centro apenas da parte VISIVEL do segmento desta sessao.
   long width=0,height=0;
   if(!ChartGetInteger(chart,CHART_WIDTH_IN_PIXELS,0,width) ||
      !ChartGetInteger(chart,CHART_HEIGHT_IN_PIXELS,0,height) || width<2 || height<2) return false;
   int subwindow=-1;datetime probe=0,label_time=0;double probe_price=0;
   if(!ChartXYToTimePrice(chart,(int)(width/2),(int)(height/2),subwindow,probe,probe_price) || subwindow!=0)return false;
   int begin_x=0,end_x=0,unused_y=0;
   if(!ChartTimePriceToXY(chart,0,begin,probe_price,begin_x,unused_y) ||
      !ChartTimePriceToXY(chart,0,end,probe_price,end_x,unused_y))return false;
   int center=MDVisibleCenter615((int)width,begin_x,end_x);
   if(center>=0)
   {
      if(!ChartXYToTimePrice(chart,center,(int)(height/2),subwindow,label_time,probe_price) || subwindow!=0)return false;
      // Conversao quantizada por barras nunca coloca o texto fora da sessao.
      if(label_time<begin)label_time=begin;
      if(label_time>end)label_time=end;
   }
   // Se o segmento nao aparece na tela, apaga apenas seus rotulos.
   MDVisualPlan plan;MDVisualBuild(day,plan);
   for(int i=0;i<10;i++)
   {
      if(!MDPositive(plan.lines[i].price) ||
         !MDVisualDrawLine(chart,MDVisualPrefix(instance),plan.lines[i],begin,end,label_time))
      {
         Print("FALHA_VISUAL_MODELO_D: ",plan.lines[i].key,"; erro=",GetLastError());
         if(!MDVisualClear(chart,instance)) Print("FALHA_LIMPEZA_VISUAL_MODELO_D");
         return false;
      }
   }
   ChartRedraw(chart);return true;
}
#endif
