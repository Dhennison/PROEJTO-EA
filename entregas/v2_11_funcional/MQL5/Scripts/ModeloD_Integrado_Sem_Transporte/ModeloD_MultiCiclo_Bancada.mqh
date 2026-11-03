#ifndef MODELOD_MULTI_CICLO_BANCADA
#define MODELOD_MULTI_CICLO_BANCADA
#include "ModeloD_MultiPersist_Bancada.mqh"
// Somente bancada: nao produz permissoes de envio e nao e ligado ao EA.
// Nao aceita troca de ticket quando existir acao externa pendente ou em voo.
bool MDMultiBeginDurableBench(MDMultiStoreBench &store,long expected,long now,const MDChainInput68 &chain_input,bool fresh,bool external_pending,long identifier,long ticket,string &reason)
{
 reason="BLOQUEADO";MDMultiBench before;long revision;
 if(!store.Load(expected,now,before,revision)||revision!=expected)return false;
 MDMultiBench candidate=before;
 if(!MDMultiReconcileBench(candidate,chain_input,fresh,external_pending,reason))return false;
 int at=MDIndexBench(candidate,identifier);if(at<0||candidate.slots[at].control.ticket!=ticket)return false;
 if(!MDManagementBegin615L(candidate.slots[at].control,now,ticket,true))return false;
 if(!store.Commit(before,revision,candidate,now)){reason="FALHA_GRAVACAO";return false;}
 reason="RESERVADO_NA_BANCADA";return true;
}
bool MDMultiCompleteDurableBench(MDMultiStoreBench &store,long expected,long now,long identifier,long ticket,long started,bool verified)
{
 if(!verified)return false;
 MDMultiBench before;long revision;
 if(!store.Load(expected,now,before,revision)||revision!=expected)return false;
 int at=MDIndexBench(before,identifier);
 if(at<0||before.slots[at].control.ticket!=ticket||before.slots[at].control.protection.last_started_ms!=started)return false;
 MDMultiBench candidate=before;
 if(!MDManagementComplete615L(candidate.slots[at].control,now,ticket))return false;
 return store.Commit(before,revision,candidate,now);
}
#endif
