"""Freeze the original trade sequence per minute; never rewrite imported MT5 data."""
from pathlib import Path
import csv, hashlib, io, json, zipfile, datetime
root=Path(__file__).resolve().parents[1]
source=root.parent/'v2_10/diagnostico_agente/pesquisa_importacao/coleta_dia_20261103/WINZ26_20261030_DIA_COMPLETO.zip'
rows={}; prime1=1000000007;prime2=1000000009
with zipfile.ZipFile(source) as z:
 raw=z.read(z.namelist()[0]);assert hashlib.sha256(raw).hexdigest()=='8035268c0d8ac2e0fdc99a5c42e748c0f13b5d684563c820d56a1634693d861a'
 for row in csv.DictReader(io.StringIO(raw.decode('utf-8-sig')),delimiter='\t'):
  flag=int(row['<FLAGS>']);text=row['<LAST>']
  if not flag&120 or not text:continue
  price=int(text);dt=datetime.datetime.strptime(row['<DATE>']+' '+row['<TIME>'],'%Y.%m.%d %H:%M:%S.%f').replace(tzinfo=datetime.timezone.utc)
  stamp=(int(dt.replace(microsecond=0).timestamp())*1000+dt.microsecond//1000);minute=stamp//60000*60000
  if minute not in rows:rows[minute]=[minute,0,price,price,price,price,0,0]
  r=rows[minute];r[1]+=1;r[3]=max(r[3],price);r[4]=min(r[4],price);r[5]=price
  for i,p in [(6,prime1),(7,prime2)]:
   for value in [stamp%p,price,flag&120]:r[i]=(r[i]*131+value)%p
assert len(rows)==566
# Independent exported terminal M1 must agree with every frozen OHLC/count.
m1=root.parent/'v2_10/diagnostico_agente/pesquisa_importacao/controle_dia/teste_20261103/MD_PESQ_WINZ26_DIA1030_M1.csv'
b=m1.read_bytes();text=b.decode('utf-16') if b.startswith(b'\xff\xfe') else b.decode('utf-8-sig')
for line in list(csv.reader(io.StringIO(text),delimiter='\t'))[1:]:
 if not line:continue
 dt=datetime.datetime.strptime(line[0]+' '+line[1],'%Y.%m.%d %H:%M:%S').replace(tzinfo=datetime.timezone.utc)
 stamp=int(dt.timestamp())*1000;r=rows[stamp]
 assert [int(float(x)) for x in line[2:6]]==[r[2],r[3],r[4],r[5]],(line,r)
 assert int(line[6])==r[1],(line,r)
header='''#ifndef MD_REFERENCE211_HEADER
#define MD_REFERENCE211_HEADER
// Original CSV SHA256: 8035268c0d8ac2e0fdc99a5c42e748c0f13b5d684563c820d56a1634693d861a
// Independently compared with the original terminal M1 export (566 minutes).
// Columns: minute, count, O,H,L,C, ordered hashes of (time_msc,Last,trade flags).
const long MD_REFERENCE211[566][8]={
'''+',\n'.join(' {'+','.join(map(str,r))+'}' for r in rows.values())+'''\n};
long md_reference_hits211=0,md_reference_minute211=0;
bool MDReferenceMinute211(long minute,const MqlTick &ticks[],int size)
{
 if(!MDFonteAtiva211()||minute%60000!=0||minute+60000>(long)TimeCurrent()*1000)return false;
 int row=-1;
 for(int k=0;k<566;k++)if(MD_REFERENCE211[k][0]==minute){row=k;break;}
 if(row<0)return false;
 long count=0,h1=0,h2=0,previous=-1;double o=0,h=0,l=0,c=0;
 for(int i=0;i<size;i++){
  long stamp=ticks[i].time_msc;if(stamp<minute||stamp>=minute+60000)continue;
  long flag=(long)(ticks[i].flags&120);if(flag==0)continue;
  double price=ticks[i].last;long integer=(long)MathRound(price);
  if(price<=0||price!=(double)integer||stamp<previous)return false;
  if(count==0){o=price;h=price;l=price;}
  else{if(price>h)h=price;if(price<l)l=price;}
  c=price;count++;previous=stamp;
  h1=(h1*131+stamp%1000000007)%1000000007;h1=(h1*131+integer)%1000000007;h1=(h1*131+flag)%1000000007;
  h2=(h2*131+stamp%1000000009)%1000000009;h2=(h2*131+integer)%1000000009;h2=(h2*131+flag)%1000000009;
 }
 bool valid=count==MD_REFERENCE211[row][1]&&o==MD_REFERENCE211[row][2]&&h==MD_REFERENCE211[row][3]&&
        l==MD_REFERENCE211[row][4]&&c==MD_REFERENCE211[row][5]&&h1==MD_REFERENCE211[row][6]&&h2==MD_REFERENCE211[row][7];
 if(valid){md_reference_hits211++;md_reference_minute211=minute;}
 return valid;
}
#endif
'''
(root/'MQL5/Experts/ModeloD_Ensaio_Funcional/ModeloD_ReferenciaOriginal211.mqh').write_text(header)
(root/'REFERENCIA_ORIGINAL.json').write_text(json.dumps({'csv_sha256':hashlib.sha256(raw).hexdigest(),'minutes':len(rows),'independent_m1_sha256':hashlib.sha256(b).hexdigest(),'minute_0901':rows[1793350860000]},indent=2)+'\n')
fixture=root/'tests/fixtures/09_01_original.txt';fixture.parent.mkdir(exist_ok=True)
with fixture.open('w') as f:
 for row in csv.DictReader(io.StringIO(raw.decode('utf-8-sig')),delimiter='\t'):
  if row['<TIME>'].startswith('09:01:') and row['<LAST>'] and int(row['<FLAGS>'])&120:
   dt=datetime.datetime.strptime(row['<DATE>']+' '+row['<TIME>'],'%Y.%m.%d %H:%M:%S.%f').replace(tzinfo=datetime.timezone.utc)
   f.write(f"{(int(dt.replace(microsecond=0).timestamp())*1000+dt.microsecond//1000)} {int(row['<LAST>'])} {int(row['<FLAGS>'])}\n")
print('566 raw-CSV minutes agree with independent M1 export; reference generated.')
