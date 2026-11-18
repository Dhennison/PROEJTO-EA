import csv,json
from pathlib import Path
E=Path(__file__).resolve().parents[1];BASE=E/'estudo_saidas_niveis_20261117';pool={};stops={'R38.2':375,'R61.8':450,'S38.2':375,'S50':375,'S61.8':650}
def read(p):return list(csv.DictReader(p.open(encoding='utf-8-sig'),delimiter=';'))
def canon(l,stopmode,stop,tpMode,tp):
 if stopmode=='fixed' and stop==stops[l] and tpMode=='factor' and tp==1:return ('ORIGINAL',)
 return (stopmode,float(stop),tpMode,float(tp))
def broad(l,c):
 mode=c['mode'];sf=float(c['stop_parameter']);tf=float(c['tp_multiplier'])
 if mode=='ORIGINAL':return ('ORIGINAL',)
 if mode=='STOP_MULT_ORIGINAL':return canon(l,'fixed',max(5,int(stops[l]*sf/5+.5)*5),'factor',tf)
 if mode=='STOP_FIXED_POINTS':return canon(l,'fixed',sf,'factor',tf)
 if mode=='STOP_PROPORTIONAL_NEW_TARGET':return canon(l,'ratio',sf,'factor',tf)
 return canon(l,'fixed',sf,'fixed',tf)
def add(id,recipe,lo,hi,ddlo,ddhi,ylo,yhi,pending,source,priority):
 key=tuple(sorted(recipe.items()));r=dict(id=id,recipe=recipe,lo=float(lo),hi=float(hi),ddlo=float(ddlo),ddhi=float(ddhi),years=list(map(float,ylo)),yearshi=list(map(float,yhi)),pending=int(float(pending)),source=source,priority=priority)
 if key not in pool or priority>pool[key]['priority']:pool[key]=r
params={r['id']:r for r in read(BASE/'PARAMETROS_VARIANTES.csv')}
updated={r['id']:r for r in read(E/'fechamento_variante_r61_750_150_20261117/CENARIOS_RELACIONADOS_ATUALIZADOS.csv')}
for rr in read(BASE/'CENARIOS_SAIDAS_E_MISTOS.csv'):
 r=updated.get(rr['id'],rr)
 if r['family']=='SAME_RULE_ALL_LEVELS':recipe={l:broad(l,params[r['id']]) for l in stops}
 else:recipe={l:broad(l,params[v]) for l,v in (x.split(':') for x in r['rule'].split('|')) if v!='OFF'}
 add(r['id'],recipe,r['points_lower'],r['points_upper'],r['DD_lower'],r['DD_upper'],[r[k] for k in ['year2024_lower','year2025_lower','year2026_JanOct_lower']],[r[k] for k in ['year2024_upper','year2025_upper','year2026_JanOct_upper']],r['uncertain_trades'],'ESTUDO_AMPLO',1)
for r in read(BASE/'EXCLUSOES_31_COMBINACOES_EXATAS.csv'):
 recipe={l:('ORIGINAL',) for l in r['levels'].split('|')}
 add(r['id'],recipe,r['points_lower'],r['points_upper'],r['DD_lower'],r['DD_upper'],[r[k] for k in ['year2024_lower','year2025_lower','year2026_JanOct_lower']],[r[k] for k in ['year2024_upper','year2025_upper','year2026_JanOct_upper']],0,'EXCLUSOES',2)
for r in read(E/'fechamento_variante_r61_750_150_20261117/COMBINACOES_16_R61_NOVO_OUTROS_ORIGINAIS.csv'):
 recipe={l:('ORIGINAL',) for l in r['levels'].split('|') if l and l!='R61.8_NOVO'};recipe['R61.8']=canon('R61.8','fixed',150,'fixed',750)
 add(r['id'],recipe,r['points'],r['points'],r['DD_continuous'],r['DD_continuous'],[r[k] for k in ['year2024','year2025','year2026']],[r[k] for k in ['year2024','year2025','year2026']],0,'CEDRO_RECUPERADO',3)
ps={r['id']:r for r in read(E/'estudo_s61_saidas_20261117/PARAMETROS_CENARIOS.csv')}
for r in read(E/'estudo_s61_saidas_20261117/COMBINACOES_COM_R61.csv'):
 c=ps[r['variant']];sm={'FIXED_POINTS':'fixed','PROPORTIONAL_NEW_TARGET':'ratio','PROPORTIONAL_NEW_TARGET_CAP650':'ratio_cap650'}[c['stop_mode']]
 recipe={'S61.8':canon('S61.8',sm,float(c['stop_value']),'factor',float(c['target_multiplier']))}
 if r['combination']=='COM_R61_ORIGINAL':recipe['R61.8']=('ORIGINAL',)
 if r['combination']=='COM_R61_750_150':recipe['R61.8']=canon('R61.8','fixed',150,'fixed',750)
 add(r['variant']+'_'+r['combination'],recipe,r['lower'],r['upper'],r['DD_lower'],r['DD_upper'],[r[f'year{y}_lower'] for y in [2024,2025,2026]],[r[f'year{y}_upper'] for y in [2024,2025,2026]],r['unresolved'],'ESTUDO_S61_CORRIGIDO',4)
closed=[r for r in pool.values() if r['pending']==0 and r['lo']==r['hi'] and r['lo']>0]
for r in closed:
 r['npos']=sum(v>0 for v in r['years']);r['ratio']=r['lo']/max(1,r['ddhi'])
Path(__file__).with_name('UNIVERSO_CONSOLIDADO.json').write_text(json.dumps(list(pool.values()),ensure_ascii=False,indent=2)+'\n')
print('UNIVERSO',len(pool),'FECHADAS_POSITIVAS',len(closed))
