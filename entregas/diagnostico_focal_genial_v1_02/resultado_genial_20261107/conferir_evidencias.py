"""Reproduz análise dos snapshots e confronta barras Genial com o Work original."""
import csv
import hashlib
import io
import json
import re
import sys
import tempfile
import zipfile
from datetime import datetime
from decimal import Decimal as D
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from analisar_focal import analyze,read,stamp


def run():
    native=HERE/'originais/RETORNO_FOCAL_GENIAL_20261107.zip'
    work=HERE.parents[1]/'historico_work_modelo_d_20261105/replay_setembro_20261106/originais/Candles_Originais_Modelo_D_2023_2026.zip'
    out=HERE/'analise';out.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as temporary:
        folder=Path(temporary)
        with zipfile.ZipFile(native) as z:
            for item in z.infolist():
                if item.is_dir():continue
                name=Path(item.filename).name
                if not (name in {'META.txt','TENTATIVAS.csv'} or re.fullmatch(r'JANELA[12]_(?:ALL|TRADE|M1|MINUTOS|RELATORIO|LEITURA\d+_MINUTOS)\.(?:csv|txt)',name)):
                    raise ValueError('Arquivo inesperado no retorno: '+name)
                if (folder/name).exists():raise ValueError('Nome repetido no retorno')
                (folder/name).write_bytes(z.read(item))
        primary=analyze(folder,out)
        assert primary['lote_tem_marcador_END']
        assert primary['metadados']['Servidor']=='GenialInvestimentos-PRD'
        assert primary['metadados']['SymbolCustom']=='0' and primary['metadados']['ModoGrafico']=='1'
        assert all(w['validade_declarada']==w['estabilidade_declarada']=='SIM' for w in primary['janelas'])
        with zipfile.ZipFile(work) as z:
            raw=z.read('WINFUT_F_0_1min_01-01-2026_22-09-2026.csv')
            original={datetime.strptime(r['Data']+' '+r['Hora'],'%d/%m/%Y %H:%M:%S').strftime('%Y.%m.%d %H:%M:%S'):r
                      for r in csv.DictReader(io.StringIO(raw.decode('cp1252')),delimiter=';')}
        references=[];channels=[];differences=[]
        business_fields=['time','time_msc','bid','ask','last','volume','volume_real','flags']
        recalculated=read(out/'OHLC_RECALCULADO.csv')
        for j in (1,2):
            a=read(folder/f'JANELA{j}_ALL.csv');t=read(folder/f'JANELA{j}_TRADE.csv');rates=read(folder/f'JANELA{j}_M1.csv')
            selected=[r for r in a if int(r['flags']) & 120]
            equal=[[r[k] for k in business_fields] for r in selected]==[[r[k] for k in business_fields] for r in t]
            assert equal
            channels.append({'janela':j,'ALL_n':len(a),'ALL_negocios':len(selected),'TRADE_n':len(t),'igualdade_exata_ALL_filtrado_e_TRADE':equal})
            first=read(folder/f'JANELA{j}_LEITURA1_MINUTOS.csv');second=read(folder/f'JANELA{j}_LEITURA2_MINUTOS.csv')
            assert len(first)==len(second)==5
            compare=lambda r:{k:v for k,v in r.items() if k!='snapshot_estavel'}
            assert [compare(r) for r in first]==[compare(r) for r in second]
            for rate in rates:
                ref=original[rate['horario_servidor']]
                num=lambda s:D(s.replace('.','').replace(',','.'))
                matches=all(D(rate[x])==num(ref[y]) for x,y in [('open','Abertura'),('high','Máximo'),('low','Mínimo'),('close','Fechamento')])
                volume_matches=D(rate['real_volume'])==num(ref['Quantidade'])
                assert matches and volume_matches
                references.append({'Janela':j,'MinutoServidor':rate['horario_servidor'],'OHLC_Genial_Work':'IGUAL','RealVolume_QuantidadeWork':'IGUAL'})
                calc=next(r for r in recalculated if int(r['Janela'])==j and r['MinutoServidor']==rate['horario_servidor'].replace('.','-').replace(' ','T'))
                if calc['Campos_ALL_Diferentes_M1']=='IGUAL':continue
                lo=stamp(rate['horario_servidor']);sub=[r for r in a if lo<=int(r['time_msc'])<lo+60000]
                business=[r for r in sub if int(r['flags']) & 120]
                target=D(rate['high'])
                hits={field:sum(D(r[field])==target for r in sub) for field in ['last','bid','ask']}
                assert hits['last']==0
                differences.append({'janela':j,'minuto':rate['horario_servidor'],'campos':calc['Campos_ALL_Diferentes_M1'],
                                    'ticks_ohlc':{field:calc[f'ALL_{field}'] for field in 'OHLC'},
                                    'm1_ohlc':{field:calc[f'M1_{field}'] for field in 'OHLC'},
                                    'deltas_ticks_menos_m1':{field:calc[f'Delta_ALL_{field}'] for field in 'OHLC'},
                                    'raw_ALL_no_minuto':len(sub),'negocios_no_minuto':len(business),
                                    'preco_maxima_M1_encontrado_em_raw_ALL':hits,
                                    'primeiro_tick_msc':sub[0]['time_msc'],'ultimo_tick_msc':sub[-1]['time_msc'],
                                    'soma_volume_real_registros_negocio':str(sum((D(r['volume_real']) for r in business),D(0))),
                                    'volume_real_barra_m1':rate['real_volume'],
                                    'ressalva_volume':'Soma de registros não prova quantidade exata de contratos/negócios ausentes sem identidade de negócio.'})
        assert len(references)==10 and len(differences)==2
        with (out/'CONFRONTO_10_BARRAS_COM_WORK.csv').open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=references[0].keys(),delimiter=';',lineterminator='\n');w.writeheader();w.writerows(references)
        result={'ambiente':'TERMINAL_GENIAL','SymbolCustom':0,'ModoGrafico':'LAST','barras_conferidas':10,'barras_ticks_m1_iguais':8,'barras_divergentes':2,
                'barras_m1_genial_iguais_ao_work':10,'canais_ALL_TRADE':channels,'ohlc_por_minuto_igual_nas_duas_releituras':True,'divergencias':differences,
                'conclusao':'Inconsistência reproduzida entre barras e ticks recuperados; filtro de flags não explica a ausência dos preços máximos nas duas amostras.',
                'limites':['Não foi comprovado se a causa é origem/servidor, cache/sincronização, timestamp de borda ou convenção de formação de barra.',
                           'Não foi executado teste no Strategy Tester por esta coleta.',
                           'Não foram consultados ticks fora das duas janelas; possíveis eventos de borda permanecem sem prova.',
                           'Concordância entre Work e M1 não substitui fita independente da bolsa.',
                           'Não flexibilizar filtros nem fabricar Last para reproduzir preços ausentes.'],
                'hash_zip_recebido':hashlib.sha256(native.read_bytes()).hexdigest(),'hash_csv_m1_original_work':hashlib.sha256(raw).hexdigest()}
        (out/'CONFERENCIA_ADICIONAL.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        return result


if __name__=='__main__':print(json.dumps(run(),ensure_ascii=False,indent=2))
