#ifndef MD_SPARSE_M1_615N
#define MD_SPARSE_M1_615N
#include "ModeloD_Stream.mqh"
// Politica exclusivamente observacional. Ausencia conjunta nao prova integridade.
bool MDSparseStamp615N(long stamp,long from,long end,long previous)
{return stamp>=from&&stamp<=end&&stamp%60000==0&&stamp>previous;}
bool MDSparseMinute615N(const MDMinuteAudit &m,int bars,double o,double h,double l,double c,bool observation_only)
{
 if(bars<0||bars>1||m.count<0)return false;
 if(m.count==0)return observation_only&&bars==0;
 if(bars!=1)return false;
 return MDAuditMinuteMatches(m,o,h,l,c);
}
bool MDSparseFinish615N(MDStream615 &s,bool observation_only)
{
 if(s.audit.count>0)return MDStreamFinish615(s,true);
 // So avanca um bloco inteiramente vazio anterior ao primeiro tick diario conhecido.
 // Nenhum tick/preco/toque e criado, nem checkpoint elegivel sem abertura observada.
 if(!observation_only||!s.ready||!s.audit.valid||s.block_end<0||s.data.open_msc<=s.block_end)return false;
 s.cursor=s.block_end+1;s.block_end=-1;s.blocks++;return true;
}
#endif
