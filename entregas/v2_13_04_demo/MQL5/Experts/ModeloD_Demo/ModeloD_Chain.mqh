#ifndef MD_CHAIN68
#define MD_CHAIN68
#include "ModeloD_Recovery.mqh"
// Snapshot limitado de UMA ordem original e suas posicoes HEDGE. Sem API MT5.
// Admissao exige origem registrada e confirmada, nao apenas Magic coincidente.
struct MDOrigin68
{
   bool verified,buy;
   string symbol;
   int instance,level,date;
   long order_ticket,magic,accepted_msc;
   double initial_volume;
};
struct MDOrder68
{
   long ticket,magic;
   string symbol;
   bool buy;
   int state; // 0=ativa,1=cancelada/expirada,2=preenchida,3=rejeitada
   double initial_volume,remaining;
};
struct MDDeal68
{
   long ticket,order,position,magic,msc;
   string symbol;
   bool buy;
   int entry; // 0=IN,1=OUT,3=OUT_BY;2=INOUT nao suportado HEDGE
   double volume;
};
struct MDPosition68
{long ticket,identifier,magic;string symbol;bool buy;double volume;};
struct MDChainInput68
{
   MDOrigin68 origin;
   MDOrder68 order;
   bool snapshot_complete;
   long snapshot_msc;
   int deal_count,position_count;
   MDDeal68 deals[128];
   MDPosition68 positions[16];
};
struct MDChainPosition68
{long identifier,current_ticket,first_entry_msc;double entered,exited,open_volume;};
struct MDChainResult68
{
   bool valid,consumed,pending,terminal_without_fill;
   string reason;
   int unique_deals,duplicates,position_count,open_positions;
   double entered,exited,open_volume,remaining;
   MDChainPosition68 positions[16];
};
bool MDVolume68(const double x){return MathIsValidNumber(x)&&x>=0;}
bool MDEqual68(const double a,const double b){return MathAbs(a-b)<0.00000001;}
bool MDFail68(MDChainResult68 &r,const string why){r.valid=false;r.reason=why;return false;}
bool MDDealSame68(const MDDeal68 &a,const MDDeal68 &b)
{return a.ticket==b.ticket&&a.order==b.order&&a.position==b.position&&a.magic==b.magic&&a.msc==b.msc&&a.symbol==b.symbol&&a.buy==b.buy&&a.entry==b.entry&&a.volume==b.volume;}
int MDPosIndex68(const MDChainResult68 &r,const long identifier)
{for(int i=0;i<r.position_count;i++)if(r.positions[i].identifier==identifier)return i;return -1;}
bool MDReconcileChain68(const MDChainInput68 &s,MDChainResult68 &r)
{
   r.valid=false;r.consumed=false;r.pending=false;r.terminal_without_fill=false;r.reason="NAO_CONCILIADO";
   r.unique_deals=0;r.duplicates=0;r.position_count=0;r.open_positions=0;
   r.entered=0;r.exited=0;r.open_volume=0;r.remaining=0;
   if(!s.snapshot_complete)return MDFail68(r,"SNAPSHOT_INCOMPLETO");
   if(s.deal_count<0||s.deal_count>128||s.position_count<0||s.position_count>16)return MDFail68(r,"CAPACIDADE_EXCEDIDA");
   if(!s.origin.verified || !MDDateValid67(s.origin.date) || s.origin.symbol=="" ||
      s.origin.order_ticket<=0 || s.origin.magic!=MDMagic67(s.origin.instance,s.origin.level) || s.origin.magic<0 ||
      s.origin.accepted_msc<0 || s.snapshot_msc<s.origin.accepted_msc || !MDVolume68(s.origin.initial_volume)||s.origin.initial_volume==0)
      return MDFail68(r,"ORIGEM_NAO_COMPROVADA");
   if(s.order.ticket!=s.origin.order_ticket||s.order.magic!=s.origin.magic||s.order.symbol!=s.origin.symbol||s.order.buy!=s.origin.buy||
      s.order.state<0||s.order.state>3 || !MDVolume68(s.order.initial_volume) || !MDVolume68(s.order.remaining)||
      !MDEqual68(s.order.initial_volume,s.origin.initial_volume)||s.order.remaining>s.order.initial_volume)
      return MDFail68(r,"ORDEM_DIVERGENTE");
   bool duplicate[128];
   for(int i=0;i<s.deal_count;i++)
   {
      duplicate[i]=false;
      for(int j=0;j<i;j++)if(s.deals[i].ticket==s.deals[j].ticket)
      {
         if(!MDDealSame68(s.deals[i],s.deals[j]))return MDFail68(r,"DEAL_DUPLICADO_DIVERGENTE");
         duplicate[i]=true;break;
      }
      if(duplicate[i]){r.duplicates++;continue;}
      if(s.deals[i].order!=s.origin.order_ticket)continue;
      MDDeal68 d=s.deals[i];
      if(d.entry!=0||d.magic!=s.origin.magic||d.symbol!=s.origin.symbol||d.buy!=s.origin.buy||d.ticket<=0||d.position<=0||
         !MDVolume68(d.volume)||d.volume==0||d.msc<s.origin.accepted_msc||d.msc>s.snapshot_msc)
         return MDFail68(r,"ENTRADA_DIVERGENTE");
      int k=MDPosIndex68(r,d.position);
      if(k<0)
      {
         if(r.position_count>=16)return MDFail68(r,"CAPACIDADE_POSICOES");
         k=r.position_count++;r.positions[k].identifier=d.position;r.positions[k].current_ticket=0;
         r.positions[k].first_entry_msc=d.msc;r.positions[k].entered=0;r.positions[k].exited=0;r.positions[k].open_volume=0;
      }
      if(d.msc<r.positions[k].first_entry_msc)r.positions[k].first_entry_msc=d.msc;
   }
   // Agrega todos os deals das posicoes identificadas. Saida manual pode ter Magic0.
   for(int i=0;i<s.deal_count;i++)
   {
      if(duplicate[i])continue;
      MDDeal68 d=s.deals[i];int k=MDPosIndex68(r,d.position);
      if(k<0)
      {
         if(d.magic==s.origin.magic&&d.symbol==s.origin.symbol)return MDFail68(r,"OUTRA_CADEIA_OU_ENTRADA_AUSENTE");
         continue;
      }
      if(d.ticket<=0||d.order<=0||d.symbol!=s.origin.symbol||!MDVolume68(d.volume)||d.volume==0||d.msc>s.snapshot_msc)
         return MDFail68(r,"DEAL_VINCULADO_INVALIDO");
      if(d.entry==0)
      {
         if(d.order!=s.origin.order_ticket||d.magic!=s.origin.magic||d.buy!=s.origin.buy)
            return MDFail68(r,"ENTRADA_DE_OUTRA_ORDEM");
         r.positions[k].entered+=d.volume;r.entered+=d.volume;
      }
      else if(d.entry==1||d.entry==3)
      {
         if(d.buy==s.origin.buy||d.msc<r.positions[k].first_entry_msc)return MDFail68(r,"SAIDA_DIRECAO_OU_TEMPO_INVALIDO");
         r.positions[k].exited+=d.volume;r.exited+=d.volume;
      }
      else return MDFail68(r,"REVERSAO_OU_TIPO_NAO_SUPORTADO");
      r.unique_deals++;
   }
   // Volume acumulado por instante: mesmo ms tratado como grupo, sem inventar
   // ordem de execucao pelo ticket. Valida saldo de grupo, nao fila intrams.
   for(int i=0;i<s.deal_count;i++)
   {
      if(duplicate[i])continue;
      int k=MDPosIndex68(r,s.deals[i].position);if(k<0)continue;
      double net=0;
      for(int j=0;j<s.deal_count;j++)if(!duplicate[j]&&s.deals[j].position==s.deals[i].position&&s.deals[j].msc<=s.deals[i].msc)
         net+=(s.deals[j].entry==0?1.0:-1.0)*s.deals[j].volume;
      if(net< -0.00000001)return MDFail68(r,"SAIDA_MAIOR_QUE_ENTRADAS_NO_INSTANTE");
   }
   for(int i=0;i<s.position_count;i++)
   {
      MDPosition68 p=s.positions[i];int k=MDPosIndex68(r,p.identifier);
      if(k<0)
      {if(p.magic==s.origin.magic&&p.symbol==s.origin.symbol)return MDFail68(r,"POSICAO_SEM_ENTRADA_COMPROVADA");continue;}
      if(p.ticket<=0||p.symbol!=s.origin.symbol||p.magic!=s.origin.magic||p.buy!=s.origin.buy||!MDVolume68(p.volume)||p.volume==0)
         return MDFail68(r,"POSICAO_DIVERGENTE");
      if(r.positions[k].current_ticket!=0)return MDFail68(r,"POSICAO_DUPLICADA");
      for(int j=0;j<i;j++)if(s.positions[j].ticket==p.ticket)return MDFail68(r,"TICKET_POSICAO_DUPLICADO");
      r.positions[k].current_ticket=p.ticket;r.positions[k].open_volume=p.volume;r.open_volume+=p.volume;r.open_positions++;
   }
   for(int i=0;i<r.position_count;i++)if(!MDEqual68(r.positions[i].entered-r.positions[i].exited,r.positions[i].open_volume))
      return MDFail68(r,"SALDO_DEALS_DIFERE_POSICAO");
   if(r.entered>s.origin.initial_volume+0.00000001)return MDFail68(r,"EXECUCAO_ACIMA_VOLUME_ORIGINAL");
   r.pending=s.order.state==0;
   if(r.pending)
   {
      if(s.order.remaining<=0||!MDEqual68(r.entered+s.order.remaining,s.origin.initial_volume))return MDFail68(r,"SALDO_PENDENTE_DIVERGENTE");
      r.remaining=s.order.remaining;
   }
   if(s.order.state==2 && (!MDEqual68(r.entered,s.origin.initial_volume)||s.order.remaining!=0))return MDFail68(r,"ORDEM_PREENCHIDA_SEM_DEALS_COMPLETOS");
   if(s.order.state==3 && r.entered>0)return MDFail68(r,"ORDEM_REJEITADA_COM_EXECUCAO");
   r.consumed=r.entered>0;r.terminal_without_fill=s.order.state!=0&&!r.consumed;r.valid=true;r.reason="CADEIA_CONCILIADA_NO_SNAPSHOT";return true;
}
// Ponte para o modelo de recuperacao6.7. Qualidade do Last e cronologia de
// fronteiras continuam evidencias separadas. Nao inferir essas flags de volumes.
bool MDChainEvidence68(const MDChainResult68 &chain,MDRecoveryEvidence67 &e)
{
   if(!chain.valid){e.server_complete=false;e.ownership_resolved=false;return false;}
   e.server_complete=true;e.ownership_resolved=true;e.request_resolved=!chain.terminal_without_fill;
   e.had_entry=chain.consumed;e.pending_count=chain.pending?1:0;e.position_count=chain.open_positions;
   return true;
}
#endif
