"""Demonstra separacao entre ordem de chegada e timestamp, sem escolher pelo resultado."""
from pathlib import Path
from decimal import Decimal as D
import importlib.util,subprocess,tempfile,csv,io
p=Path(__file__).resolve();spec=importlib.util.spec_from_file_location('calc',p.with_name('calcular.py'));c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
with tempfile.TemporaryDirectory() as tmp:
 root=Path(tmp);date='2026.09.22';base=c.motor.epoch(date+' 00:00:00');cut=base+18*3600000
 ls=[{'name':str(i),'eligible':True,'buy':True,'entry':D(100),'sl':D(90),'tp':D(110),'entry5':D(100),'sl5':D(90),'tp5':D(110)} for i in range(5)]
 c.config(root/'cfg','WINV26',date,ls,cut)
 stamps=['09:00:01.000','09:00:02.000','09:00:03.000','09:00:04.000','09:00:02.500','09:00:05.000'];prices=[120,110,115,105,95,90]
 lines=[f'{i}|WINV26|2026-09-22 {t}|{price}|1|2|3|I|0' for i,(t,price) in enumerate(zip(stamps,prices),1)]
 for mode,sequence,reason,points in [('file',lines,1,-10),('time',sorted(lines,key=lambda x:(x.split('|')[2],int(x.split('|')[0]))),2,10)]:
  red=root/(mode+'.csv');direct=root/(mode+'_direto.csv')
  with red.open('wb') as f:proc=subprocess.run(['/tmp/cedro-reduzir-setembro',str(root/'cfg'),str(direct),mode],input=('\n'.join(sequence)+'\n').encode(),stdout=f,stderr=subprocess.PIPE)
  assert proc.returncode==0,proc.stderr
  assert b'records=6;' in proc.stderr
  for r in c.read(direct):assert int(r['reason'])==reason and int(r['points'])==points
  c.direct_check(ls,c.motor.replay(c.events(red),ls,cut,True,False),direct)
 # Strict bloqueia timestamp regressivo; nao houve aceitacao silenciosa.
 proc=subprocess.run(['/tmp/cedro-reduzir-setembro',str(root/'cfg'),str(root/'strict.csv')],input=('\n'.join(lines)+'\n').encode(),stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
 assert proc.returncode!=0 and b'regressao temporal' in proc.stderr
 print('PASS: 6registros preservados;ordemarquivo SL,cronologica TP;strict recusa regressao. Mesma regra em ambos.')
