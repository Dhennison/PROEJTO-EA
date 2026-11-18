from pathlib import Path
import ast,collections
P=Path(__file__).parent;tree=ast.parse((P/'testar_50_250.py').read_text());old=ast.parse((P.parents[1]/'entregas/estudo_saidas_niveis_20261117/testar_cenarios.py').read_text());helpers={'collections':collections}
for f in old.body:
 if isinstance(f,ast.FunctionDef) and f.name=='tick_choices':exec(compile(ast.Module(body=[f],type_ignores=[]),'tick','exec'),helpers)
day='2099-01-01';o=dict(date=day,level='S61.8',buy=True,entry=1000,tp=1500,sl=350,entry_minute='09:00',original=500)
ns=dict(reason={(day,'S61.8'):'TP'},bars={day:[(540,1100,1300,980,990),(541,990,1000,940,950),(542,1000,1600,1000,1500),(1080,1050,1050,1050,1050)]},replay={},known_noquote=set(),ns=helpers)
for f in tree.body:
 if isinstance(f,ast.FunctionDef) and f.name=='evaluate':exec(compile(ast.Module(body=[f],type_ignores=[]),'fixed_engine','exec'),ns)
ends,_,_=ns['evaluate'](o);assert ends=={('TP',250),('SL',-50)}
ns['replay']={(day,'09:00'):[('09:00:00.001',1100,1),('09:00:01.001',1300,1),('09:00:59.999',980,1)]}
ends,_,_=ns['evaluate'](o);assert ends=={('SL',-50)},'High before entry is not a post-entry target'
ns['replay']={};ns['reason'][(day,'S61.8')]='SL';ns['bars'][day]=[(540,1000,1300,980,1260),(541,1200,1300,350,400),(1080,400,400,400,400)]
ends,_,_=ns['evaluate'](o|{'original':-650});assert ends=={('TP',250)},'Closer target may be hit even when original later stopped'
ns['bars'][day]=[(540,1000,1100,980,990),(541,990,1000,350,400),(1080,400,400,400,400)]
ends,_,basis=ns['evaluate'](o|{'tp':1200,'original':-650});assert ends=={('SL',-50)} and basis.startswith('PROVEN')
ns['reason'][(day,'S61.8')]='CORTE';ns['bars'][day]=[(540,1000,1100,990,1050),(1080,1010,1010,1010,1010)]
ends,_,_=ns['evaluate'](o|{'original':10});assert ends=={('CORTE',10)}
ns['bars'][day]=[(540,1000,1100,990,1050),(1080,930,930,930,930)]
ends,_,_=ns['evaluate'](o|{'original':-70});assert ends=={('CORTE',-70)},'No artificial50point clamp on a gap at cutoff'
print('Motor: pre-entry high;completeReplay;closertargetafteroriginalSL;monotonicproof;cut;no artificial daily-loss clamp: OK')
