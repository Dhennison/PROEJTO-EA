from pathlib import Path
import importlib.util,tempfile,zipfile,shutil,sys
sys.dont_write_bytecode=True
b=Path(__file__).resolve().parent.parent
p=b/'controle_dia/VALIDAR_LOCAL_DIA.py'
spec=importlib.util.spec_from_file_location('host_dia',p);h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
pre=h.EXPERT_PRELUDE.replace('int CopyTicksRange(', 'bool SymbolSelect(string,bool){return is_custom;}\nextern long MD_MARKERS[14];\nint CopyTicksRange(')
pre=pre.replace(' if(fault=="reorder")', ''' if(fault=="zeros"&&mode==COPY_TICKS_ALL){for(auto m:MD_MARKERS){MqlTick t;t.time_msc=m;t.time=m/1000;a.push_back(t);}std::stable_sort(a.begin(),a.end(),[](const auto&a,const auto&b){return a.time_msc<b.time_msc;});}
 if(fault=="reorder")''')
load='int main('+h.EXPERT_MAIN.split('int main(',1)[1].split(' reset();tester=false;',1)[0]
main=r'''
 reset();tester=true;OnStart();check(queries==0,"tester accepted");
 reset();is_custom=false;OnStart();check(queries==0,"wrong symbol accepted");
 reset();collision=true;OnStart();check(queries==0,"collision accepted");
 reset();file_ok=false;OnStart();check(queries==0,"report failure accepted");
 reset();OnStart();check(queries==2&&opened==closed,"queries/file invalid");
 check(output.find("RESULT;canonical_all_match=1;canonical_trade_match=1;m1_matches_terminal_all_trades=1")!=string::npos,"canonical terminal fixture failed");
 reset();fault="zeros";OnStart();check(output.find("flags_zero=14")!=string::npos&&output.find("MARKER;mode=ALL")!=string::npos&&output.find("RESULT;canonical_all_match=1")!=string::npos,"zero marker logging changed canonical events");
 for(string f:{"reorder","quote_missing","volume_field","api_timeout","outside","published_m1"}){
  reset();fault=f;OnStart();check(queries==2&&opened==closed,"fault file leaked");
  check(output.find("RESULT;canonical_all_match=1;canonical_trade_match=1;m1_matches_terminal_all_trades=1")==string::npos,"fault accepted: "+f);
 }
 std::cout<<"HOST_TERMINAL;Checks="<<checks<<";Failures=0;SOURCE_ROWS="<<source_rows<<";CPP_SIMULADO;NAO_E_COMPILACAO_MQL5\n";return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 1;}}
'''
reset='''void reset(){tester=false;optimization=false;is_custom=true;collision=false;file_ok=true;simulated=1793736000LL;fault.clear();output.clear();api_error=queries=opened=closed=0;md_file=INVALID_HANDLE;for(int i=0;i<1440;i++)ZeroMemory(md_minutes[i]);}\n'''
with tempfile.TemporaryDirectory(prefix='md_terminal_host_') as tmp:
 folder=Path(tmp);csv=folder/'day.csv'
 with zipfile.ZipFile(b/'coleta_dia_20261103/WINZ26_20261030_DIA_COMPLETO.zip') as z:
  with z.open('WINZ26_20261030_DIA_COMPLETO.csv') as f,csv.open('wb') as o:shutil.copyfileobj(f,o)
 h.build_run(folder,'terminal',pre+h.translate(b/'auditoria_terminal/MQL5/Scripts/ModeloD_Pesquisa_Dados/Auditar_Consultas_Dia_WINZ26.mq5')+reset+h.EXPERT_MAIN[h.EXPERT_MAIN.index('std::vector<string> split'):h.EXPERT_MAIN.index('int main(')]+load+main,(csv,b/'m1_atual_20261103/WINZ26_M1_20261030_SECUNDARIO_ATUAL.csv'))
