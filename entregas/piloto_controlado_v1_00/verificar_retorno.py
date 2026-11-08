"""Confronta snapshots do piloto com o CSV original. Não envia nem altera dados.
Exemplo: python verificar_retorno.py --fonte original.csv --importado IMPORT_READBACK.csv
  --historico TESTER_COPYTICKS.csv --eventos ONTICK.csv --saida conferencia.json
Só --fonte é obrigatório; pode analisar o importador antes de executar o Tester.
"""
import argparse,csv,hashlib,json,math
from collections import Counter
from pathlib import Path
EXPECTED_SHA='a3acba0e6d6e8f10ab1f6c24143c63d46fa8ce9767c2f87b87220fd3c2e0ed0b'
FIELDS=('time','time_msc','bid','ask','last','volume','volume_real','flags')
LO=1793264400000;HI=1793265000000

def read(path):
    with path.open(encoding='utf-8-sig',newline='') as f:
        rd=csv.DictReader(f,delimiter=';')
        expected={'time_msc','bid','ask','last','volume','volume_real','flags'}
        if set(rd.fieldnames or []) not in (expected,expected|{'time'}):raise ValueError('Cabeçalho inválido: '+str(path))
        rows=[]
        for index,r in enumerate(rd):
            if None in r or any(v is None for v in r.values()):raise ValueError('Colunas incompletas/extras')
            t=int(r['time_msc']);sec=int(r['time']) if 'time' in r else t//1000
            item=(sec,t,float(r['bid']),float(r['ask']),float(r['last']),int(r['volume']),float(r['volume_real']),int(r['flags']))
            if not all(math.isfinite(v) for v in item):raise ValueError('Número não finito')
            rows.append(item)
        return rows

def summary(rows):
    return {'n':len(rows),'business':sum(bool(r[7]&120) and r[4]>0 for r in rows),
        'flags':dict(Counter(r[7] for r in rows)),
        'time_ordered':all(a[1]<=b[1] for a,b in zip(rows,rows[1:])),
        'inside_window':all(LO<=r[1]<HI for r in rows),
        'seconds_consistent':all(r[0]==r[1]//1000 for r in rows),
        'bid_gt_ask':sum(r[2]>r[3] for r in rows),'zero_quotes':sum(r[2]==0 or r[3]==0 for r in rows)}

def compare(source,seen):
    cursor=0;sub=True
    for event in seen:
        while cursor<len(source) and source[cursor]!=event:cursor+=1
        if cursor==len(source):sub=False;break
        cursor+=1
    return {'exact':source==seen,'source_n':len(source),'seen_n':len(seen),
        'ordered_subsequence':sub,
        'positional_differences_common_prefix':{k:sum(a[i]!=b[i] for a,b in zip(source,seen)) for i,k in enumerate(FIELDS)},
        'note':'Subsequência não significa perda de importação nem associação única a negócios; examinar coalescência e Diário.'}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--fonte',type=Path,required=True);p.add_argument('--importado',type=Path)
    p.add_argument('--historico',type=Path);p.add_argument('--eventos',type=Path)
    p.add_argument('--saida',type=Path,required=True);a=p.parse_args()
    raw=a.fonte.read_bytes();sha=hashlib.sha256(raw).hexdigest()
    if sha!=EXPECTED_SHA:raise ValueError('Fonte não é o CSV A original preservado de 29/10.')
    source=read(a.fonte)
    if len(source)!=204027 or summary(source)['business']!=128669:raise ValueError('Fonte divergente')
    result={'source':summary(source),'source_sha256':sha,'layers':{}}
    for name,path in [('import',a.importado),('tester_history',a.historico),('ontick',a.eventos)]:
        if path is not None:
            rows=read(path)
            result['layers'][name]={'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                'summary':summary(rows),'comparison':compare(source,rows)}
    result['overall']='PENDENTE_DIARIO_DO_TESTER_E_REVISAO_DAS_CAMADAS'
    a.saida.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
