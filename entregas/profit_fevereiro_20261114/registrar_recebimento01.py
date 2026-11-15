"""Preserve partial February receipt, publish two resolutions and exact remaining prefix.
Does not close February or modify frozen daily series/PDFs.
"""
from pathlib import Path
import json,csv,hashlib,shutil,zipfile,sys
P=Path(__file__).parent;ROOT=P.parents[1]
s=json.loads((P/'REPLAY_TODAS_ABAS_RESULTADO.json').read_text())
assert s['records']==152719 and s['resolved_original_pending']==2 and s['pending_operation_count']==1
assert s['test_points'] is None and s['difference'] is None
assert s['unresolved_operations']==[['2026-02-27','S38.2']]
rr=s['results'];assert all(r['tie_invariant'] and not r['mixed_exit_barrier_ms'] for r in rr)
assert [(r['date'],r['primary']['reason'],r['primary']['points']) for r in rr[:2]]==[('2026-02-11','SL','-450'),('2026-02-24','SL','-375')]
assert all(r['entry_minute_check']['ohlc_match'] and r['entry_minute_check']['quantity_match'] for r in rr[:2])
pending=rr[2];assert pending['missing_quantity']==1798 and pending['observed_start']=='09:01:00.286'
source=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/workspace/dados_brutos_modelo_d/replay_profit/Fevereiro_2026_Recebimento01.xlsx')
dest=Path('/workspace/dados_brutos_modelo_d/replay_profit/Fevereiro_2026_Recebimento01.xlsx');dest.parent.mkdir(parents=True,exist_ok=True)
if source.resolve()!=dest.resolve():shutil.copy2(source,dest)
assert hashlib.sha256(dest.read_bytes()).hexdigest()==s['workbook_sha256']
(P/'PRESERVACAO_BRUTO_RECEBIMENTO01.json').write_text(json.dumps(dict(source=str(source),preserved=str(dest),sha256=s['workbook_sha256'],size_bytes=dest.stat().st_size,raw_published=False),ensure_ascii=False,indent=2)+'\n')
progress=dict(status='FEVEREIRO_PARCIAL_FALTA_INICIO_27FEV',operations=39,determined_M1=36,resolved_Replay=2,pending=1,principal=None,work_points=s['work_points'],difference=None,missing=dict(date='2026-02-27',contract='WINJ26',level='S38.2',interval_start_inclusive='09:01:00.000',first_observed='09:01:00.286',same_millisecond_prefix_may_also_be_partial=True,quantity_observed=131722,quantity_reference=133520,quantity_shortfall=1798,requested_capture_start='09:00:58.000',requested_capture_end_exclusive='09:01:01.000',purpose='Repair beginning and full boundary timestamp group, verify overlap against existing copy without deduplication.'),do_not_repeat=['11/02 R61.8','24/02 R38.2','27/02 after09:01:01'],DD_expansion='WAIT_UNTIL_FEBRUARY_CLOSED',previous_months='UNCHANGED',raw_sha256=s['workbook_sha256'])
(P/'PROGRESSO_RESOLUCAO.json').write_text(json.dumps(progress,ensure_ascii=False,indent=2)+'\n')
with (P/'COLETA_COMPLEMENTAR_PENDENTE.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=['data','contrato','inicio','fim_exclusivo','nivel','motivo'],delimiter=';',lineterminator='\n');w.writeheader();w.writerow(dict(data='2026-02-27',contrato='WINJ26',inicio='09:00:58.000',fim_exclusivo='09:01:01.000',nivel='S38.2',motivo='Falta inicio09:01:00 e possivel grupo parcial09:01:00.286;repor prefixo com sobreposicao,sem deduplicar'))
text='''FEVEREIRO/2026 — RECEBIMENTO01 PARCIAL — FALTA INÍCIO DE27/02
Nosso resultado principal: PENDENTE. Não existe fechamento mensal nem DD do
teste para fevereiro. Não somar subtotal de operações determinadas.
Work original -664,311665 preservado.

Arquivo Mês de Fevereiro.xlsx: três abas, 152719 negócios preservados sem
remover duplicatas. Sem limite200001 por aba. Cópia original e réplica
SHA256 idêntica preservadas; manifesto PRESERVACAO_BRUTO_RECEBIMENTO01.json.

RESOLVIDOS — NÃO REPETIR COLETA
11/02 WING26 R61.8: SL -450. Entrada09:02:31.309; saída no minuto09:04 peloM1.
Confirma STOP Work. Minuto09:02 completo, OHLC/quantidade iguais aoM1.
24/02 WINJ26 R38.2: SL -375. Entrada09:06:11.210; saída no minuto09:11 peloM1.
ALVO Work passa aSTOP. Minuto09:06 completo, OHLC/quantidade iguais aoM1.
Controles matemáticos dãoSL nos dois casos. Dois desempates de milissegundo
mantêm motivo/pontos; sem barreiras opostas no mesmo ms. Regressões contra
reprocessar máxima pré-entrada e aceitar barra de entrada incompleta passaram.
Saídas CANDLE indicam apenas minuto, não instante exato de negócio.
Estado:36resultados determinadosM1 +2resolvidosReplay +1pendente.

ÚNICA PENDÊNCIA
27/02 WINJ26 S38.2. A aba começa09:01:00.286, a194015; a abertura do
candle09:01 é193930. Quantidade observada131722 versus referência133520;
diferença1798. Máxima194055/mínima193200/fechamento193265 conferem.
Essas igualdades não reconstituem a trajetória nem excluem entrada/saída
no prefixo ausente. O primeiro grupo09:01:00.286 também pode estar cortado.
O trecho observado, isoladamente, sugereSL, mas esse cálculo éCONDICIONAL
e não foi incorporado a resultado/fechamento. Primary noJSON está explicitamente
marcado resolved=false/conditional_only=true para essa operação.

ENVIAR APENAS COMPLEMENTO CURTO
27/02/2026 WINJ26:09:00:58.000 até09:01:01.000 (fimexclusivo), sem saltar,
filtrar ou deduplicar negócios; preservar milissegundos e ordem original.
É necessário o começo de09:01 e a sobreposição até o segundo01 para conferir
a emenda. Não repetir11/02,24/02 nem o minuto inteiro de27/02.
Ao receber, comparar a sobreposição registro por registro, inclusive negócios
idênticos, e substituir o prefixo por um corte temporal explícito. Não unir
arquivos por deduplicação. Só classificar depois de recompor e conferir
OHLC/quantidade133520 do minuto09:01 e desempates de milissegundo.

PRESERVAÇÃO
Março+350/Abril+5720/Maio-780/Junho+3405/Julho+1100 eCedroAgo-2375/Set+2855/
Out+3830 intactos. Curvas deDD/PDFs fechados não regravados. Fevereiro não
entrou noDD. Após resolver, ampliar DD cronológico por série, sem reinício
mensal, e preparar os dois PDFs finais com diárioWork versus nosso teste.
M1+Replay pontual não é mês inteiro por negócios nem prova de fills reais.
Parâmetros originais/grade5/toque/1contrato/corte18h preservados.
Controle10/07 dispensado permanece encerrado. Plano vigente sem mudança.
'''
(P/'LEIA_RESULTADO_PARCIAL.txt').write_text(text)
with zipfile.ZipFile(P/'Fevereiro_Modelo_D_Recebimento01_Parcial.zip','w',zipfile.ZIP_DEFLATED) as z:
 for name in ['LEIA_RESULTADO_PARCIAL.txt','PROGRESSO_RESOLUCAO.json','COLETA_COMPLEMENTAR_PENDENTE.csv','REPLAY_TODAS_ABAS_RESULTADO.json','REPLAY_OPERACOES_RESOLVIDAS.csv','REPLAY_TODAS_ABAS_AUDITORIA.csv','REPLAY_TODAS_ABAS_M1.csv','DIARIO_APOS_JANELAS.csv','PRESERVACAO_BRUTO_RECEBIMENTO01.json','conferir_todas_janelas.py','registrar_recebimento01.py']:z.write(P/name,name)
print(json.dumps(progress,ensure_ascii=False,indent=2))
