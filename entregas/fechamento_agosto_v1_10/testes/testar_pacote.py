"""Compile actual MQL source adapted to C++; API mocks, not native MT5."""
import re,subprocess,tempfile,os,sys,json,csv
from pathlib import Path
from datetime import datetime,timezone
root=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='mes110_') as temp:
 d=Path(temp);source=root/'MQL5/Experts/ModeloD_Fechamento_Agosto'
 for p in source.iterdir():
  if p.suffix not in ('.mqh','.mq5'):continue
  s=p.read_text(encoding='utf-8-sig');s=re.sub(r'^#property.*$','',s,flags=re.M).replace('input ','')
  s=s.replace('Ref refs[];','std::vector<Ref> refs;').replace('MqlTick before[],now[];','std::vector<MqlTick> before,now;').replace('MqlRates source_m1[],rate_before[],rate_now[];','std::vector<MqlRates> source_m1,rate_before,rate_now;')
  s=re.sub(r'const (MqlTick|MqlRates) &(\w+)\[\]',r'const std::vector<\1> &\2',s)
  s=s.replace('uchar data[],key[],digest[];','std::vector<uchar> data,key,digest;')
  s=re.sub(r"D'([^']+)'",lambda m:str(int(datetime.strptime(m[1],'%Y.%m.%d %H:%M:%S' if len(m[1])>10 else '%Y.%m.%d').replace(tzinfo=timezone.utc).timestamp())),s)
  (d/p.name).write_text(s)
 (d/'host.cpp').write_text((root/'testes/host.cpp').read_text())
 binary=d/'collector'
 compile=subprocess.run(['c++','-std=c++17','-O1','-g','-Wall','-Wextra','-Wno-unused-parameter','-Wno-sign-compare','-fsanitize=address,undefined','-fno-omit-frame-pointer',str(d/'host.cpp'),'-lcrypto','-o',str(binary)],capture_output=True,text=True)
 (root/'testes/COMPILACAO_CPP.txt').write_text(compile.stdout+compile.stderr+'\nEXIT_STATUS='+str(compile.returncode)+'\n')
 assert compile.returncode==0,compile.stderr
 env=os.environ.copy();env['ASAN_OPTIONS']='detect_leaks=0:halt_on_error=1';env['UBSAN_OPTIONS']='halt_on_error=1'
 out=d/'coleta';run=subprocess.run([str(binary),str(root/'MQL5/Files/MD_Agosto_2026_Referencias.csv'),str(root/'MQL5/Files/MD_Agosto_2026_M1_Work.csv'),str(out)],capture_output=True,text=True,env=env)
 (root/'testes/RESULTADO_CPP.txt').write_text(run.stdout+run.stderr+'\nEXIT_STATUS='+str(run.returncode)+'\n');print(run.stdout+run.stderr);assert run.returncode==0
 sys.path.insert(0,str(root/'analise'));from analisar_mes import run as analyze,read
 result=analyze(out,d/'audit');assert result['complete'] and result['days_analyzed']==20 and result['price_differences']==0 and result['quantity_differences']==0
 from validar_independente import validate
 independent=validate(out,d/'audit');assert independent['states_checked']==400
 main=read(d/'audit/DIARIO_PRINCIPAL.csv');assert len(main)==20
 rows=read(d/'audit/POR_OPERACAO.csv');cuts=[r for r in rows if r['cenario']=='GRADE5_TOQUE' and r['motivo']=='CORTE_LAST'];assert cuts,'Pipeline must exercise real cutoff logic, not just cutoff presence'
 contracts=read(d/'audit/CONTRATOS_CONFERIDOS.csv');assert len(contracts)==40
 # A valid pending batch must not publish a complete monthly total.
 status=out/'BLOCOS.csv';original_status=status.read_text();status.write_text(original_status.replace(';ESTAVEL;',';PENDENTE;',1))
 log=out/'RESULTADO.txt';original_log=log.read_text();log.write_text(original_log.replace('pending_blocks=0','pending_blocks=1').replace('reason=CONCLUIDO;','reason=CONCLUIDO_COM_PENDENCIAS;'))
 pending=analyze(out,d/'pending');assert not pending['complete'] and pending['principal_points'] is None
 status.write_text(original_status);log.write_text(original_log)
 # Changing the declared chosen symbol cannot pass independent reconstruction.
 resolved=out/'REFERENCIAS_RESOLVIDAS.csv';original_resolved=resolved.read_text();resolved.write_text(original_resolved.replace(';WINQ26;',';WINV26;',1))
 try:analyze(out,d/'bad_contract')
 except AssertionError:pass
 else:raise AssertionError('Forged contract accepted')
 resolved.write_text(original_resolved)
 # Altering a candidate OHLC while retaining the exact-match flag is rejected.
 contract=out/'M1_CONTRATO_20260804_WINQ26.csv';original_contract=contract.read_text();lines=original_contract.splitlines();row=lines[1].split(';');row[2]=str(float(row[2])+5);lines[1]=';'.join(row);contract.write_text('\n'.join(lines)+'\n')
 try:analyze(out,d/'bad_bar')
 except AssertionError:pass
 else:raise AssertionError('Forged match accepted')
 contract.write_text(original_contract)
 # Expiry exclusion must really put the WHOLE session outside the contract life.
 meta=out/'CONTRATOS.csv';original_meta=meta.read_text();lines=original_meta.splitlines()
 for index in range(1,len(lines)):
  fields=lines[index].split(';')
  if fields[2]=='FORA_VIGENCIA':fields[-1]='1999999999';lines[index]=';'.join(fields);break
 meta.write_text('\n'.join(lines)+'\n')
 try:analyze(out,d/'bad_expiry')
 except AssertionError:pass
 else:raise AssertionError('Forged expiry accepted')
 meta.write_text(original_meta)
 # Reference and source hashes are mandatory also on consumption.
 source_m1=out/'M1_WORK.csv';original_source=source_m1.read_bytes();source_m1.write_bytes(original_source+b'x')
 try:analyze(out,d/'bad_source')
 except AssertionError:pass
 else:raise AssertionError('Changed source accepted')
 source_m1.write_bytes(original_source)
 proof=dict(scope='SYNTHETIC FOUR-POINT PATH; API and consumer only; NOT historical ticks or performance',days=20,blocks=1140,contract_candidates_audited=40,stable_m1_snapshots=sum(r['estado']=='ESTAVEL' for r in contracts),candidates_outside_life=sum(r['estado']=='FORA_VIGENCIA' for r in contracts),states_all_variants=len(read(d/'audit/TODOS_NIVEIS_QUATRO_CENARIOS.csv')),price_differences=0,quantity_differences=0,cutoff_cases_exercised=len(cuts),pending_refuses_total=True,forged_contract_refused=True,forged_candidate_bar_refused=True,changed_source_refused=True,forged_expiry_refused=True,independent_states_checked=independent['states_checked'],native_MT5_compile_or_execution=False)
 (root/'testes/RESULTADO_PIPELINE.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n');print(json.dumps(proof,indent=2))
