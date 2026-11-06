#ifndef MD_BROKER_BOUNDARY21305
#define MD_BROKER_BOUNDARY21305
// Explicit SL/TP exit receipts are sufficient to cancel the SAME order's
// remaining volume, even while the independent Last replay is still catching up.
bool MDBrokerExitBoundary21305(const MDOpState &s,const MDOpSnapshot &b,int k) {
 if(k<0||k>=s.nlevels||!b.book.complete||!b.book.connected||
    MDContext612(b.book.account_key,b.book.server_key,s.instance)!=s.scope)return false;
 for(int p=0;p<s.npositions;p++)if(s.positions[p].owner==k){
  MDOpPosition v=s.positions[p];
  for(int d=0;d<b.book.deals;d++){
   MDDeal68 deal=b.book.d[d];if(deal.position!=v.identifier||deal.symbol!=s.levels[k].symbol||
    (deal.entry!=1&&deal.entry!=3)||deal.msc<v.first_server||deal.msc>b.server_msc)continue;
   long reason=0;
   if(DI69((ulong)deal.ticket,DEAL_REASON,reason)&&(reason==DEAL_REASON_SL||reason==DEAL_REASON_TP))return true;
  }
 }
 return false;
}
#endif
