"""Execute current-day demo adapter with API mocks. Never a native broker login."""
from pathlib import Path
import argparse,json,os,re,subprocess,tempfile,resource
p=argparse.ArgumentParser();p.add_argument('--sanitize',action='store_true');p.add_argument('--report-dir',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[1];base=root.parent/'v2_11_funcional';a.report_dir.mkdir(parents=True,exist_ok=True)
from check_mql_keywords import check_tree
keyword_errors=check_tree(root/'MQL5')
(a.report_dir/'MQL_KEYWORDS.txt').write_text('CHECK=input_global_modifier_only;NOT_NATIVE_MQL_COMPILER\n'+('FAIL\n'+str(keyword_errors) if keyword_errors else 'PASS;all_sources_scanned;no_input_identifier\n'))
if keyword_errors:raise SystemExit('MQL reserved keyword misuse: '+str(keyword_errors))
replacements=json.loads((root/'REPLACEMENTS.json').read_text())
with tempfile.TemporaryDirectory(prefix='modelod213_') as name:
 build=Path(name)
 for src in (root/'MQL5/Experts/ModeloD_Demo').iterdir():
  if src.suffix not in ['.mq5','.mqh']:continue
  s=re.sub(r'^#property.*$','',src.read_text(),flags=re.M);s=re.sub(r'^input ','',s,flags=re.M)
  s=re.sub(r'\b(MqlTick|MqlRates) (\w+)\[\];',r'std::vector<\1> \2;',s)
  s=re.sub(r'(MqlTick|MqlRates) &(\w+)\[\]',r'std::vector<\1> &\2',s)
  (build/src.name).write_text(s)
 host=(base/'tests/host.cpp').read_text().replace('#include "../MQL5/',f'#include "{base}/MQL5/')
 host=host[:host.index('#include \"'+str(base)+'/MQL5/Scripts/ModeloD_Integrado_Sem_Transporte/ModeloD_PreviewIntegradoCases.mqh\"')]
 host=host.replace('uint FileWriteString(int h,string s,int n=-1){','bool fail_write210=false,flip_guard210=false,delay_write210=false;extern long mock_mode213;extern long mock_mono;\nuint FileWriteString(int h,string s,int n=-1){if(s.find("DEMO_PREPARE_BEFORE_SEND")!=string::npos){if(flip_guard210){flip_guard210=false;mock_mode213=2;}if(delay_write210){delay_write210=false;mock_mono+=4001;}}if(fail_write210&&handles.at(h)->path.find(".next")!=string::npos){fail_write210=false;lastError=8;return 0;}')
 host=host.replace('long GetMicrosecondCount(){return 615001;}','long GetMicrosecondCount(){static long micro=615001;return micro++;}')
 (build/'host.cpp').write_text(host)
 mock=(base/'tests/runtime_mock.cpp').read_text().replace('#include "host.cpp"',f'#include "{build}/host.cpp"')
 mock=mock.replace('#include "../MQL5/Scripts/',f'#include "{base}/MQL5/Scripts/')
 # The inherited fixture helpers must include THIS version's ledger/core,
 # not the old script directory's copies (their include guards would hide it).
 cases=base/'MQL5/Scripts/ModeloD_Integrado_Sem_Transporte/ModeloD_OperationalCases.mqh'
 (build/'ModeloD_OperationalCases.mqh').write_text(cases.read_text())
 mock=mock.replace(str(cases),str(build/'ModeloD_OperationalCases.mqh'))
 mock=re.sub(r'^#include "\.\./MQL5/Experts/[^\n]+\n','',mock,flags=re.M)
 mock=mock.replace('#define MD_DAILY_TERMINAL614\n','')
 mock=re.sub(r'^int MDDateValue614\(long stamp\).*\n','',mock,flags=re.M)
 mock=re.sub(r'^bool MDCollectDaily614\(int,.*\n','',mock,flags=re.M)
 mock=mock.replace('struct MqlDateTime{int year,mon,day;};','struct MqlDateTime{int year,mon,day,day_of_week;};')
 mock=mock.replace('out.day=g->tm_mday;return true;','out.day=g->tm_mday;out.day_of_week=g->tm_wday;return true;')
 marker='long mock_login210=1;'
 extra='''const int ACCOUNT_TRADE_MODE=200,ACCOUNT_TRADE_MODE_DEMO=0,ACCOUNT_TRADE_MODE_CONTEST=1,ACCOUNT_TRADE_MODE_REAL=2,
 TERMINAL_TRADE_ALLOWED=201,MQL_TRADE_ALLOWED=202,ACCOUNT_TRADE_ALLOWED=203,ACCOUNT_TRADE_EXPERT=204,SYMBOL_DESCRIPTION=205;
long mock_mode213=ACCOUNT_TRADE_MODE_DEMO;long mock_freeze21305=0,mock_terminal_state21305=-1;
bool mock_terminal_algo213=true,mock_ea_algo213=true,mock_account_trade213=true,mock_account_ea213=true,mock_custom213=false,mock_description_failure213=false;
bool mock_flip_on_symbol213=false;
string mock_description213="IBOVESPA MINI(WINZ26)";
long mock_session_begin213=32400,mock_session_end213=68100;bool mock_session_available213=true;
bool SymbolInfoSessionTrade(string,int,uint index,datetime &from,datetime &to){if(!mock_session_available213||index>0)return false;from=mock_session_begin213;to=mock_session_end213;return true;}
'''
 mock=mock.replace(marker,extra+marker)
 mock=mock.replace('return p==MQL_TESTER?mock_tester210:mock_optimization210;','return p==MQL_TESTER?mock_tester210:(p==MQL_TRADE_ALLOWED?mock_ea_algo213:mock_optimization210);')
 mock=mock.replace('bool TerminalInfoInteger(int){return mock_connected;}','long TerminalInfoInteger(int p){return p==TERMINAL_TRADE_ALLOWED?mock_terminal_algo213:mock_connected;}')
 old='long AccountInfoInteger(int p){return p==ACCOUNT_MARGIN_MODE?(mock_hedge210?ACCOUNT_MARGIN_MODE_RETAIL_HEDGING:0):mock_login210;}'
 new='long AccountInfoInteger(int p){if(p==ACCOUNT_TRADE_MODE)return mock_mode213;if(p==ACCOUNT_TRADE_ALLOWED)return mock_account_trade213;if(p==ACCOUNT_TRADE_EXPERT)return mock_account_ea213;return p==ACCOUNT_MARGIN_MODE?(mock_hedge210?ACCOUNT_MARGIN_MODE_RETAIL_HEDGING:0):mock_login210;}'
 assert old in mock;mock=mock.replace(old,new)
 mock=mock.replace('bool SymbolInfoInteger(string symbol,int prop,long &v){','long MDCivilMidnight2026(int date);\nbool SymbolInfoInteger(string symbol,int prop,long &v){')
 mock=mock.replace('using ENUM_TIMEFRAMES=int;','using ENUM_DAY_OF_WEEK=int;using ENUM_TIMEFRAMES=int;')
 mock=mock.replace('if(prop==114){v=symbol=="MD_PESQ_WINZ26_DIA1030"?1:0;return true;}','if(prop==114){v=mock_custom213?1:0;if(mock_flip_on_symbol213){mock_flip_on_symbol213=false;mock_mode213=2;}return true;}')
 mock=mock.replace('v="BRL";return true;}','if(mock_description_failure213)return false;v=mock_description213;return true;}')
 mock=mock.replace('string MDLogico211(string s);','string MDLogico211(string s){return s;}')
 mock=mock.replace('const int ACCOUNT_TRADE_MODE=200,','const int ORDER_STATE=300,ORDER_STATE_CANCELED=4,ORDER_STATE_EXPIRED=6,DEAL_REASON=301,SYMBOL_SESSION_VOLUME=302,DEAL_REASON_SL=4,DEAL_REASON_TP=5;\nconst int ACCOUNT_TRADE_MODE=200,')
 mock=mock.replace('bool HI69(ulong id,int prop,long &v){selected_order=id;return OI69(prop,v);}',
  'bool HI69(ulong id,int prop,long &v){selected_order=id;if(prop==ORDER_STATE){int i=order_index(id);if(i<0)return false;v=mock_book.book.o[i].order.state==1?ORDER_STATE_CANCELED:0;return true;}return OI69(prop,v);}')
 mock=mock.replace('bool DD69(ulong id,int prop,double &v){','std::map<long,long> mock_reason21305;std::map<long,double> mock_profit21305;bool mock_cost_error21305=false;\nbool DI69(ulong id,int,long &v){auto it=mock_reason21305.find(id);if(it==mock_reason21305.end())return false;v=it->second;return true;}\nbool DD69(ulong id,int prop,double &v){')
 mock=mock.replace('if(prop==SYMBOL_EXPIRATION_MODE){','if(prop==SYMBOL_TRADE_FREEZE_LEVEL){v=mock_freeze21305;return true;}if(prop==SYMBOL_EXPIRATION_MODE){')
 mock=mock.replace('v=mock_book.book.o[i].order.state==1?ORDER_STATE_CANCELED:0;', 'v=mock_terminal_state21305>=0?mock_terminal_state21305:(mock_book.book.o[i].order.state==1?ORDER_STATE_CANCELED:0);')
 mock=mock.replace('if(prop!=DEAL_PRICE){v=0;return true;}', 'if(prop!=DEAL_PRICE){if(mock_cost_error21305)return false;v=prop==DEAL_PROFIT&&mock_profit21305.count(id)?mock_profit21305[id]:0;return true;}')
 mock=mock.replace('EA_ADAPTED_PATH',str(build/'EA_ModeloD_Demo.mq5'))
 mock=mock.replace('int main(){','int inherited_runtime_main213(){',1)
 mock=mock.replace('bool IsStopped(){return false;}','bool IsStopped(){return mock_stopped210;}').replace('bool EventSetTimer(int)','bool mock_stopped210=false,mock_partial210=false;\nbool EventSetTimer(int)')
 mock=mock.replace('return out.size();\n}','if(mock_partial210){lastError=4403;}return out.size();\n}',1)
 for old,new in replacements.items():mock=mock.replace(old,new)
 (build/'case.cpp').write_text(mock+'\n'+(root/'tests/demo.cpp').read_text())
 flags=['-std=c++17','-O0','-g','-Wall','-Wextra','-Wno-unused-parameter']
 if a.sanitize:flags+=['-fsanitize=address,undefined','-fno-omit-frame-pointer']
 result=subprocess.run(['c++',*flags,str(build/'case.cpp'),'-o',str(build/'case')],capture_output=True,text=True)
 (a.report_dir/'COMPILACAO_LOCAL.txt').write_text(result.stdout+result.stderr+f'\nEXIT_STATUS={result.returncode}\n')
 if result.returncode:print(result.stderr[-8500:]);raise SystemExit(result.returncode)
 env=os.environ.copy()
 if a.sanitize:env['ASAN_OPTIONS']='halt_on_error=1';env['UBSAN_OPTIONS']='halt_on_error=1:print_stacktrace=1'
 # Large fixed-capacity MQL structs and nested regression fixtures need a larger host stack.
 resource.setrlimit(resource.RLIMIT_STACK,(64*1024*1024,resource.getrlimit(resource.RLIMIT_STACK)[1]))
 with (a.report_dir/'TESTES_LOCAIS.txt').open('w') as report:
  result=subprocess.run([str(build/'case')],stdout=report,stderr=subprocess.STDOUT,env=env);report.write(f'\nEXIT_STATUS={result.returncode}\n')
 s=(a.report_dir/'TESTES_LOCAIS.txt').read_text();print('\n'.join(x for x in s.splitlines() if x.startswith(('PASS_213','FAIL_213','DEMO_213'))))
 if result.returncode:print(s[-3500:])
 raise SystemExit(result.returncode)
