"""Run isolated cutoff EA bodies with simulated APIs; never native MetaTrader."""
from pathlib import Path
import argparse, os, re, subprocess, tempfile, datetime
p=argparse.ArgumentParser();p.add_argument('--preparation',action='store_true');p.add_argument('--sanitize',action='store_true');p.add_argument('--report-dir',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[1];base=root.parent/'v2_11_funcional';a.report_dir.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory(prefix='modelod212_') as name:
 build=Path(name)
 def adapt(s):
  s=re.sub(r'^#property.*$','',s,flags=re.M);s=re.sub(r'^input ','',s,flags=re.M)
  s=re.sub(r'\b(MqlTick|MqlRates) (\w+)\[\];',r'std::vector<\1> \2;',s)
  s=re.sub(r'(MqlTick|MqlRates) &(\w+)\[\]',r'std::vector<\1> &\2',s)
  def date_literal(m):
   d=datetime.datetime.strptime(m.group(1),'%Y.%m.%d %H:%M:%S').replace(tzinfo=datetime.timezone.utc)
   return "((datetime)"+str(int(d.timestamp()))+")"
  s=re.sub(r"D'([^']+)'",date_literal,s)
  return s.replace('"../../Include/ModeloD_Corte212/Cenario.mqh"','"Cenario.mqh"')
 for src in (root/'MQL5/Experts/ModeloD_Ensaio_Corte').iterdir():
  if src.suffix in ('.mq5','.mqh'):(build/src.name).write_text(adapt(src.read_text()))
 (build/'Cenario.mqh').write_text(adapt((root/'MQL5/Include/ModeloD_Corte212/Cenario.mqh').read_text()))
 host=(base/'tests/host.cpp').read_text().replace('#include "../MQL5/',f'#include "{base}/MQL5/')
 host=host.replace('uint FileWriteString(int h,string s,int n=-1){','bool fail_write210=false,flip_guard210=false,delay_write210=false;extern bool mock_tester210;extern long mock_mono;\nuint FileWriteString(int h,string s,int n=-1){if(s.find("TESTER_PREPARE_BEFORE_SEND")!=string::npos){if(flip_guard210){flip_guard210=false;mock_tester210=false;}if(delay_write210){delay_write210=false;mock_mono+=4001;}}if(fail_write210&&handles.at(h)->path.find(".next")!=string::npos){fail_write210=false;lastError=8;return 0;}')
 host=host.replace('long GetMicrosecondCount(){return 615001;}','long GetMicrosecondCount(){static long micro=615001;return micro++;}')
 (build/'host.cpp').write_text(host)
 mock=(base/'tests/runtime_mock.cpp').read_text().replace('#include "host.cpp"',f'#include "{build}/host.cpp"')
 mock=mock.replace('#include "../MQL5/Scripts/',f'#include "{base}/MQL5/Scripts/').replace('#include "../MQL5/Experts/ModeloD_Ensaio_Funcional/',f'#include "{root}/MQL5/Experts/ModeloD_Ensaio_Corte/')
 mock=mock.replace('UsarFonteImportadaNoTester','UsarCenarioSinteticoNoTester').replace('MD_PESQ_WINZ26_DIA1030','MD_SINT_CORTE_WINZ26')
 mock=mock.replace('EA_ADAPTED_PATH',str(build/'EA_ModeloD_Ensaio_Corte.mq5')).replace('int main(){','int inherited_main212(){',1)
 mock=mock.replace('bool IsStopped(){return false;}','bool IsStopped(){return mock_stopped210;}').replace('bool EventSetTimer(int)','bool mock_stopped210=false,mock_partial210=false;\nbool EventSetTimer(int)')
 mock=mock.replace('double bid=209995,ask=210000;','double bid=209995,ask=210000;long time=0;ulong volume=1;double volume_real=1;')
 mock=mock.replace('struct MqlDateTime{','const uint TICK_FLAG_BID=2,TICK_FLAG_ASK=4;\nstruct MqlDateTime{')
 mock=mock.replace('else if(prop==SYMBOL_ASK)v=210000;','else if(prop==SYMBOL_ASK)v=mock_ticks.empty()?170910:mock_ticks.back().ask;').replace('else if(prop==SYMBOL_BID)v=209995;','else if(prop==SYMBOL_BID)v=mock_ticks.empty()?170905:mock_ticks.back().bid;')
 # Sorted ranges keep full-session simulation bounded without changing returned records.
 mock=mock.replace('for(auto v:source)if(v.time_msc>=(long)from&&v.time_msc<=(long)until)out.push_back(v);','for(auto it=std::lower_bound(source.begin(),source.end(),(long)from,[](const MqlTick &q,long t){return q.time_msc<t;});it!=source.end()&&it->time_msc<=(long)until;++it)out.push_back(*it);')
 mock=mock.replace('long tick_volume=100,real_volume=100;', 'long tick_volume=100,real_volume=100;int spread=5;')
 if a.preparation:
  marker='MDOpSnapshot mock_book;std::vector<MqlTick> mock_ticks,mock_all_ticks;std::vector<MqlRates> mock_rates;'
  mock=mock.replace(marker,marker+'\nbool prep_mode212=false;std::vector<MqlRates> prep_prior212,prep_rates212;std::vector<MqlTick> prep_ticks212;')
  mock=mock.replace('auto &source=flags==COPY_TICKS_ALL?mock_all_ticks:mock_ticks;','auto &source=prep_mode212&&symbol=="MD_SINT_CORTE_WINZ26"?prep_ticks212:(flags==COPY_TICKS_ALL?mock_all_ticks:mock_ticks);')
  signature='int CopyRates(string symbol,int period,datetime from,std::time_t until,std::vector<MqlRates> &out){'
  mock=mock.replace(signature,signature+'if(prep_mode212){out.clear();auto &source=symbol=="WINZ26"?prep_prior212:prep_rates212;for(auto q:source)if(q.time>=from&&q.time<=until)out.push_back(q);return out.size();}')
 mock='#include <algorithm>\n'+mock
 case=(root/'tests/cutoff.cpp').read_text()
 if a.preparation:
  helper=case.split('int main(){')[0]
  script=adapt((root/'MQL5/Scripts/ModeloD_Corte212/Preparar_Cenario_Corte_WINZ26.mq5').read_text())
  # Scenario header is already included by the adapted EA.
  script=script.replace('#include "Cenario.mqh"','')
  case=helper+(root/'tests/preparation_mock.cpp').read_text().replace('PREPARATION_SCRIPT_BODY',script)
 (build/'case.cpp').write_text(mock+'\n'+case)
 flags=['-std=c++17','-O0','-g','-Wall','-Wextra','-Wno-unused-parameter']
 if a.sanitize:flags+=['-fsanitize=address,undefined','-fno-omit-frame-pointer']
 result=subprocess.run(['c++',*flags,str(build/'case.cpp'),'-o',str(build/'case')],capture_output=True,text=True)
 (a.report_dir/'COMPILACAO_LOCAL.txt').write_text(result.stdout+result.stderr+f'\nEXIT_STATUS={result.returncode}\n')
 if result.returncode:print(result.stderr[-6000:]);raise SystemExit(result.returncode)
 env=os.environ.copy()
 if a.sanitize:env['ASAN_OPTIONS']='halt_on_error=1';env['UBSAN_OPTIONS']='halt_on_error=1:print_stacktrace=1'
 with (a.report_dir/'TESTES_LOCAIS.txt').open('w') as report:
  result=subprocess.run([str(build/'case')],stdout=report,stderr=subprocess.STDOUT,env=env)
  report.write(f'\nEXIT_STATUS={result.returncode}\n')
 text=(a.report_dir/'TESTES_LOCAIS.txt').read_text();print('\n'.join(x for x in text.splitlines() if x.startswith(('PASS_210','FAIL_210','FOCUSED_212','PREPARATION_212'))))
 if result.returncode:print(text[-3000:])
 raise SystemExit(result.returncode)
