#ifndef MD_VISIBLE_CENTER615
#define MD_VISIBLE_CENTER615
// Centro da intersecao entre segmento da sessao e janela visivel.
int MDVisibleCenter615(int width,int begin_x,int end_x)
{
 if(width<2||end_x<begin_x)return -1;
 int left=begin_x>0?begin_x:0;
 int right=end_x<width-1?end_x:width-1;
 if(right<=left)return -1;
 return left+(right-left)/2;
}
#endif
