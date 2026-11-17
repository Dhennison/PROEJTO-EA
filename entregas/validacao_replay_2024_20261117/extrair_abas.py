"""Stream XLSX raw Replay rows to local cache without dropping duplicates or sorting source.
Cache is intermediate only;original release asset is preserved with verifiedSHA256.
"""
from pathlib import Path
from decimal import Decimal as D
import zipfile,lxml.etree as E,json,pickle,re,hashlib,sys
P=Path(__file__).parent
SOURCE=Path('/workspace/dados_brutos_modelo_d/replay_profit/Janeiro_a_Dezembro_2024_Release.xlsx')
CACHE=Path('/workspace/work/lote2024/cache');CACHE.mkdir(parents=True,exist_ok=True)
assert SOURCE.stat().st_size==38318901
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()=='7124866bdfc2a605ba5fd5d1a2edfba99761188e620997df81b84a595eea38b2'
ns={'x':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'};tag='{'+ns['x']+'}'
with zipfile.ZipFile(SOURCE) as z:
 strings=[]
 with z.open('xl/sharedStrings.xml') as f:
  for _,si in E.iterparse(f,events=('end',),tag=tag+'si'):
   strings.append(''.join(si.itertext()));si.clear()
   while si.getprevious() is not None:del si.getparent()[0]
 sheets=E.fromstring(z.read('xl/workbook.xml')).findall('x:sheets/x:sheet',ns)
 rels={x.get('Id'):x.get('Target') for x in E.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
 inventory=[]
 for idx,sh in enumerate(sheets,1):
  name=sh.get('name');rid=sh.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id');target=rels[rid];target=target.lstrip('/') if target.startswith('/') else 'xl/'+target
  date=re.search(r'(\d{2})-(\d{2})-(\d{2})',name);assert date,name
  day=f'20{date[3]}-{date[2]}-{date[1]}'
  rows=[];ignored=0
  with z.open(target) as f:
   for _,row in E.iterparse(f,events=('end',),tag=tag+'row'):
    ordinal=int(row.get('r'));cells={}
    for c in row:
     col=re.sub(r'\d','',c.get('r',''))
     if col not in ('A','C','D'):continue
     v=c.find(tag+'v')
     if v is None:continue
     raw=v.text;value=strings[int(raw)] if c.get('t')=='s' else raw;cells[col]=(value,c.get('t')=='s')
    if ordinal>1 and 'A' in cells:
     tm=cells['A'][0];assert re.fullmatch(r'\d\d:\d\d:\d\d\.\d\d\d',tm),(name,ordinal,tm)
     vals=[]
     for col in ['C','D']:
      value,txt=cells[col];d=D(value.replace('.','').replace(',','.') if txt else value);assert d>0 and d==d.to_integral_value(),(name,ordinal,col,value);vals.append(int(d))
     rows.append((tm,*vals,ordinal))
    else:ignored+=1
    row.clear()
    while row.getprevious() is not None:del row.getparent()[0]
  assert rows and all(a[0]>=b[0] for a,b in zip(rows,rows[1:])),name
  path=CACHE/f'{idx:02d}.pickle';path.write_bytes(pickle.dumps(rows,protocol=4))
  inv=dict(index=idx,sheet=name,date=day,records=len(rows),start=rows[-1][0],end=rows[0][0],at_limit_200001=len(rows)>=200001,cache=str(path),ignored_header_or_blank=ignored)
  inventory.append(inv);print(json.dumps(inv,ensure_ascii=False),flush=True)
(P/'INVENTARIO_ABAS.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n')
