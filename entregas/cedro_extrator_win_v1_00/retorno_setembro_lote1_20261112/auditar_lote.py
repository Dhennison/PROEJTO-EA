"""Auditoria setembro lote1. Contrato por data conforme auditoria anterior, sem escolha por resultado. Sem replay/filtro de condicoes."""
from pathlib import Path
import collections, csv, hashlib, io, json, shutil, zipfile
BASE = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
STORE = Path('/workspace/retorno_cedro_20261112/ticks')
STORE.mkdir(parents=True, exist_ok=True)
MANIFEST = list(csv.DictReader((BASE/'entregas/cedro_extrator_win_v1_00/retorno_geral_20261112/ARQUIVOS.csv').open(),delimiter=';'))
# BASE corresponde ao repositorio; conferir antes de executar.
EXPECTED = {a['arquivo']: a for a in MANIFEST if a['tipo']=='WIN_ZIP'}
INV = list(csv.DictReader((BASE/'entregas/cedro_extrator_win_v1_00/retorno_geral_20261112/CONTRATOS.csv').open(),delimiter=';'))
WORK = list(csv.DictReader((HERE/'M1_WORK_SETEMBRO.csv').open(),delimiter=';'))
all_results=[]; diffs=[]; coverage=[]; part_report=[]
with zipfile.ZipFile('/workspace/retorno_cedro_20261112/GERAL_CEDRO_WIN.zip') as general:
    for day in ['20260901','20260902','20260903','20260904','20260908','20260909','20260910','20260911']:
        reference_symbol = 'WINV26'
        print('START',day,flush=True)
        files=[]
        for name, expected in sorted(EXPECTED.items()):
            if not name.startswith('WIN_'+day+'_'): continue
            matches=list(Path('/workspace/attachments').glob('*/'+name))
            assert len(matches)==1,(name,len(matches))
            src=matches[0]; digest=hashlib.sha256(src.read_bytes()).hexdigest()
            assert digest==expected['sha256'] and src.stat().st_size==int(expected['bytes']), name
            dst=STORE/name
            if not dst.exists():shutil.copyfile(src,dst)
            else:assert hashlib.sha256(dst.read_bytes()).hexdigest()==digest
            files.append(dst)
            part_report.append({'arquivo':name,'sha256':digest,'bytes':src.stat().st_size,'hash_OK':True})
        assert len(files)==2
        symbols={}; minutes={}; previous_ordinal=0; rows=0; selected=0
        for part in files:
            with zipfile.ZipFile(part) as z:
                assert len(z.namelist())==1
                with z.open(z.namelist()[0]) as raw, io.TextIOWrapper(raw,encoding='utf-8-sig') as stream:
                    assert next(stream).strip()=='linha_original|ativo|data_hora|campo3|campo4|campo5|campo6|campo7|campo8'
                    for line in stream:
                        fields=line.rstrip('\r\n').split('|')
                        assert len(fields)==9,(part.name,rows,fields)
                        ordinal=int(fields[0]);assert ordinal>previous_ordinal,(part.name,ordinal,previous_ordinal)
                        previous_ordinal=ordinal;rows+=1
                        _,sym,stamp,price,quantity,c5,c6,c7,c8=fields
                        assert stamp[:10].replace('-','')==day
                        p=float(price);q=float(quantity)
                        assert p>0 and q>0,(ordinal,price,quantity)
                        assert p%5==0,(ordinal,price)
                        stats=symbols.setdefault(sym,{'registros':0,'regressoes':0,'empates':0,'anterior':'','primeiro':stamp,'ultimo':stamp,'condicoes':collections.Counter(),'campo7':collections.Counter(),'soma_campo4':0.0,'open':p,'high':p,'low':p,'close':p})
                        if stats['anterior']:
                            stats['regressoes']+=stamp<stats['anterior'];stats['empates']+=stamp==stats['anterior']
                        stats['anterior']=stamp;stats['ultimo']=stamp;stats['registros']+=1
                        stats['condicoes'][c8]+=1;stats['campo7'][c7]+=1;stats['soma_campo4']+=q
                        stats['high']=max(stats['high'],p);stats['low']=min(stats['low'],p);stats['close']=p
                        if sym!=reference_symbol:continue
                        selected+=1;minute=stamp[:16].replace('-','.')
                        if minute not in minutes:minutes[minute]=[p,p,p,p,q,1]
                        else:
                            bar=minutes[minute];bar[1]=max(bar[1],p);bar[2]=min(bar[2],p);bar[3]=p;bar[4]+=q;bar[5]+=1
        assert rows==sum(int(x['registros']) for x in INV if x['dia']==day)
        for sym,stats in symbols.items():
            control=next(x for x in INV if x['dia']==day and x['ativo']==sym)
            assert stats['registros']==int(control['registros'])
            assert stats['primeiro']==control['primeiro_timestamp_na_ordem']
            assert stats['ultimo']==control['ultimo_timestamp_na_ordem']
            assert stats['regressoes']==int(control['regressoes_timestamp'])
            assert stats['empates']==int(control['empates_consecutivos'])
            stats.pop('anterior')
        work=[x for x in WORK if x['time'].replace('.','').startswith(day)]
        price_diffs=volume_diffs=missing=0
        for w in work:
            key=w['time'];got=minutes.get(key)
            if got is None:missing+=1;diffs.append({'dia':day,'minuto':key,'tipo':'WORK_SEM_TICK_REFERENCIA','campo':'','Work':'','Cedro':''});continue
            for i,k in enumerate(['open','high','low','close','volume_real']):
                if float(w[k])!=got[i]:
                    diffs.append({'dia':day,'minuto':key,'tipo':'PRECO' if i<4 else 'QUANTIDADE','campo':k,'Work':w[k],'Cedro':got[i]})
            price_diffs+=any(float(w[k])!=got[i] for i,k in enumerate(['open','high','low','close']))
            volume_diffs+=float(w['volume_real'])!=got[4]
        eodname=next(n for n in general.namelist() if n.endswith(day+'_bmf.log'))
        eod=next(x for x in csv.DictReader(io.StringIO(general.read(eodname).decode('utf-8-sig'))) if x['papel'].upper()==reference_symbol)
        qstats=symbols[reference_symbol];eod_match={k:qstats[k]==float(eod[e]) for k,e in [('open','open'),('high','high'),('low','low'),('close','last_trade'),('registros','quantitytrades'),('soma_campo4','volume_amount')]}
        coverage.append({'dia':day,'barras_Work':len(work),'Work_sem_tick_referencia':missing,'M1_com_preco_diferente':price_diffs,'M1_com_quantidade_diferente':volume_diffs,'M1_Cedro_referencia_total':len(minutes)})
        all_results.append({'dia':day,'registros_total':rows,'contratos':symbols,'contrato_referencia':reference_symbol,'EOD_CONTRATO_comparacao':eod_match,'ultimo_ordinal':previous_ordinal})
        with (HERE/('M1_'+reference_symbol+'_'+day+'.csv')).open('w') as f:
            writer=csv.writer(f,delimiter=';');writer.writerow(['time','open','high','low','close','soma_campo4','registros'])
            for key,bar in sorted(minutes.items()):writer.writerow([key]+bar)
        print('END',day,rows,'registros;',price_diffs,'minutos OHLC divergentes;',volume_diffs,'quantidade divergente',flush=True)
for name,data in [('DIFERENCAS_M1.csv',diffs),('COBERTURA.csv',coverage),('PARTES_RECEBIDAS.csv',part_report)]:
    with (HERE/name).open('w') as f:
        if data:
            writer=csv.DictWriter(f,fieldnames=list(data[0]),delimiter=';');writer.writeheader();writer.writerows(data)
(HERE/'AUDITORIA.json').write_text(json.dumps(all_results,ensure_ascii=False,indent=2)+'\n')
print('LOTE COMPLETO. Sem resultado novo ModeloD.',flush=True)
