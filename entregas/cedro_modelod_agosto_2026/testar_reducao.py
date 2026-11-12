"""Controles sinteticos de ordem/empates/corte e equivalencia com motor anterior."""
import importlib.util, random, subprocess, tempfile
from pathlib import Path
from decimal import Decimal as D
spec=importlib.util.spec_from_file_location('calcular',Path(__file__).with_name('calcular.py'));c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
rng=random.Random(12112026);checked=0
with tempfile.TemporaryDirectory() as temp:
 root=Path(temp);date='2026.08.03';base=c.motor.epoch(date+' 00:00:00');cut=base+32400000+20000
 levels=[]
 for i in range(5):
  en=D('100.3')+5*i;buy=i<3;levels.append({'name':str(i),'eligible':i!=2,'buy':buy,'entry':en,'sl':en-10 if buy else en+10,'tp':en+10 if buy else en-10,'entry5':c.motor.round5(en),'sl5':c.motor.round5(en-10 if buy else en+10),'tp5':c.motor.round5(en+10 if buy else en-10)})
 cases=[[120,110,100,90],[100,100,110,90],[90,110,90],[110,100,110],[]]+[[rng.randrange(14,29)*5 for i in range(100)] for _ in range(15)]
 for k,prices in enumerate(cases):
  cfg=root/'config';dest=root/'direct';red=root/'reduced';c.config(cfg,'WINV26',date,levels,cut)
  raw='linha_original|ativo|data_hora|campo3|campo4|campo5|campo6|campo7|campo8\n';events=[]
  for i,p in enumerate(prices):
   ms=base+32400000+(i//3)*1000;stamp=c.motor.calendar(ms).replace('.','-',2)
   ordinal=2*i+1;raw+=f'{ordinal}|WINV26|{stamp}|{p}|1|2|3|I|5\n';events.append({'ord':ordinal,'msc':ms,'p':D(p)})
   if i==8:raw+='linha_original|ativo|data_hora|campo3|campo4|campo5|campo6|campo7|campo8\n'
  with red.open('wb') as f:
   proc=subprocess.run(['/tmp/cedro-reduzir',str(cfg),str(dest)],input=raw.encode(),stdout=f,stderr=subprocess.PIPE)
  assert proc.returncode==0,proc.stderr
  reduced=c.events(red)
  for grid in (False,True):
   for strict in (False,True):
    a=c.motor.replay(events,levels,cut,grid,strict);b=c.motor.replay(reduced,levels,cut,grid,strict)
    assert c.motor.summary(a)==c.motor.summary(b),(k,grid,strict);checked+=5
  c.direct_check(levels,c.motor.replay(events,levels,cut,True,False),dest)
 # entrada exatamente no corte recusada; alvo no registro do corte usa preco do corte.
 cfg=root/'config';dest=root/'direct';red=root/'reduced';c.config(cfg,'WINV26',date,levels,cut)
 raw='1|WINV26|2026-08-03 09:00:19.999|100|1|2|3|I|5\n2|WINV26|2026-08-03 09:00:20.000|115|1|2|3|I|5\n'
 with red.open('wb') as f:proc=subprocess.run(['/tmp/cedro-reduzir',str(cfg),str(dest)],input=raw.encode(),stdout=f,stderr=subprocess.PIPE)
 assert proc.returncode==0
 c.direct_check(levels,c.motor.replay(c.events(red),levels,cut,True,False),dest)
 print('PASS',checked,'estados sinteticos: fluxos integral/reduzido, 4 variantes, empates, cabecalho entre partes, sem entrada, corte.')
