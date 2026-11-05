#ifndef MODELOD_VISUAL_MQH
#define MODELOD_VISUAL_MQH
#include "ModeloD_Core.mqh"
// Plano puro: precos sempre matematicos. Nenhum objeto de Ajuste pertence ao EA.
struct MDVisualLine
{
   string key,label;
   double price;
   bool visible,support,reference;
};
struct MDVisualPlan { MDVisualLine lines[10]; };
void MDVisualSet(MDVisualLine &l,const string key,const string label,const double price,
                 const bool visible,const bool support,const bool reference)
{
   l.key=key;l.label=label;l.price=price;l.visible=visible;l.support=support;l.reference=reference;
}
void MDVisualBuild(const MDDay &d,MDVisualPlan &p)
{
   MDVisualSet(p.lines[0],"R200","R200",d.r200,true,false,true);
   MDVisualSet(p.lines[1],"S200","S200",d.s200,true,true,true);
   MDVisualSet(p.lines[2],"R236","R23,6",d.r236,false,false,false);
   MDVisualSet(p.lines[3],"R382","R38,2",d.r382,!d.block_sell,false,false);
   MDVisualSet(p.lines[4],"R50","R50",d.r50,false,false,false);
   MDVisualSet(p.lines[5],"R618","R61,8",d.r618,!d.block_sell,false,false);
   MDVisualSet(p.lines[6],"S236","S23,6",d.s236,false,true,false);
   MDVisualSet(p.lines[7],"S382","S38,2",d.s382,!d.block_buy,true,false);
   MDVisualSet(p.lines[8],"S50","S50",d.s50,!d.block_buy,true,false);
   MDVisualSet(p.lines[9],"S618","S61,8",d.s618,!d.block_buy,true,false);
}
#endif
