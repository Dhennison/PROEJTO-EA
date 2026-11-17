from pathlib import Path
import ast
p=Path(__file__).parent
source=(p/'testar_cenarios.py').read_text();t=ast.parse(source);names={'evaluate','tick_choices','dist'}
ns={'collections':__import__('collections'),'math':__import__('math'),'replay':{},'known_noquote':set()}
for f in t.body:
 if isinstance(f,ast.FunctionDef) and f.name in names:exec(compile(ast.Module(body=[f],type_ignores=[]),str(p/'testar_cenarios.py'),'exec'),ns)
o=dict(date='2099-01-01',buy=True,entry=100,tp=115,sl=90,entry_minute='09:00')
ns['bars']={o['date']:[(540,110,120,95,99),(541,95,100,85,90),(1080,100,100,100,100)]}
a,b,_=ns['evaluate'](o,15,10);assert (a,b)==(-10,15)
ns['replay']={(o['date'],'09:00'):[('09:00:00.001',110,1),('09:00:01.001',120,1),('09:00:59.999',95,1)]}
a,b,_=ns['evaluate'](o,15,10);assert (a,b)==(-10,-10),'Pre-entry high cannot be taken as post-entry target'
ns['replay']={};ns['bars'][o['date']]=[(540,100,110,99,105),(1080,104,104,104,104)]
a,b,_=ns['evaluate'](o,50,30);assert a==b==4
ns['bars'][o['date']]=[(540,100,110,99,105),(542,105,110,101,107),(1080,104,104,104,104)]
a,b,_=ns['evaluate'](o,50,30);assert (a,b)==(-30,50),'Unexplained gap must keep unknown exits'
ns['bars']['2026-08-03']=[(540,100,200,50,120),(1080,104,104,104,104)]
a,b,_=ns['evaluate'](o|{'date':'2026-08-03'},50,30);assert (a,b)==(-30,50)
print('Motor: pre-entry high, Replay chronology, daily cut, unknown gap, absent CedroAugust source: OK')
