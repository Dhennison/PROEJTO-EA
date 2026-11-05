"""Extract unchanged v1.20 function bodies and test with simulated MT5 APIs.
This is not native MetaEditor compilation or an MT5 run.
"""
from pathlib import Path
import hashlib, re, subprocess, os, json
root = Path(__file__).resolve().parent
source = root.parent/'DiagTicksAB.mq5'
raw = source.read_bytes()
s = raw.decode('utf-8-sig')
def body(signature):
    begin = s.index(signature)
    brace = s.index('{', begin)
    depth = 1; end = brace + 1
    while depth:
        if s[end] == '{': depth += 1
        elif s[end] == '}': depth -= 1
        end += 1
    return s[begin:end]
struct = s[s.index('struct Res'):s.index('\nRes      g_a')]
functions = '\n'.join(body(x) for x in ['void Mix(', 'ulong Q(', 'bool SameTicks(', 'bool StoreTicks(', 'void Collect(', 'bool SameRes(', 'bool DumpCsv(', 'int OnInit(', 'void OnTimer('])
functions = re.sub(r'MqlTick (\w+)\[\];', r'std::vector<MqlTick> \1;', functions)
functions = re.sub(r'const MqlTick &(\w+)\[\]', r'const std::vector<MqlTick> &\1', functions)
functions = re.sub(r'MqlTick &(\w+)\[\]', r'std::vector<MqlTick> &\1', functions)
(root/'extracted.hpp').write_text(struct+'\nRes g_a{},g_tr{},g_in{},g_pa{},g_ptr{},g_pin{};\n'+functions)
flags = ['-std=c++17','-O0','-g','-Wall','-Wextra','-Werror',
         '-fsanitize=address,undefined,float-cast-overflow','-fno-omit-frame-pointer']
c = subprocess.run(['c++',*flags,str(root/'harness.cpp'),'-o',str(root/'tests')],text=True,capture_output=True)
(root/'compilation.txt').write_text(c.stdout+c.stderr)
c.check_returncode()
env = dict(os.environ, ASAN_OPTIONS='halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
results={}
for case in ['normal','nan']:
    r=subprocess.run([str(root/'tests'),case],text=True,capture_output=True,env=env)
    (root/f'{case}.txt').write_text(r.stdout+r.stderr+f'\nEXIT_STATUS={r.returncode}\n')
    results[case]={'exit_status':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
    print(case,'exit',r.returncode)
    print(r.stdout)
    if r.stderr: print(r.stderr[:2000])
(root/'results.json').write_text(json.dumps({'source_sha256':hashlib.sha256(raw).hexdigest(),
    'scope':'actual Collect/SameRes/Mix/Q bodies, C++ syntax adaptation, simulated MT5 APIs',
    'runs':results},indent=2))
