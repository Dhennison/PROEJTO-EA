"""Execute actual Experts adapter bodies with MT5 API mocks, never native MQL5."""
from pathlib import Path
import argparse, os, re, subprocess, tempfile

p = argparse.ArgumentParser()
p.add_argument('--sanitize', action='store_true')
p.add_argument('--report-dir', type=Path, required=True)
a = p.parse_args()
root = Path(__file__).resolve().parents[1]
a.report_dir.mkdir(parents=True, exist_ok=True)
with tempfile.TemporaryDirectory(prefix='modelod210_') as temp:
    build = Path(temp)
    for source in (root / 'MQL5/Experts/ModeloD_Integrado_Sem_Transporte').iterdir():
        if source.suffix not in ('.mq5', '.mqh'):
            continue
        s = re.sub(r'^#property.*$', '', source.read_text(), flags=re.M)
        s = re.sub(r'^input ', '', s, flags=re.M)
        s = re.sub(r'\b(MqlTick|MqlRates) (\w+)\[\];', r'std::vector<\1> \2;', s)
        (build / source.name).write_text(s)
    host = (root / 'tests/host.cpp').read_text()
    host = host.replace('#include "../MQL5/', f'#include "{root}/MQL5/')
    host = host.replace('uint FileWriteString(int h,string s,int n=-1){',
        'bool fail_write210=false,flip_guard210=false,delay_write210=false;extern bool mock_tester210;extern long mock_mono;\nuint FileWriteString(int h,string s,int n=-1){'
        'if(s.find("TESTER_PREPARE_BEFORE_SEND")!=string::npos){if(flip_guard210){flip_guard210=false;mock_tester210=false;}if(delay_write210){delay_write210=false;mock_mono+=4001;}}'
        'if(fail_write210&&handles.at(h)->path.find(".next")!=string::npos){'
        'fail_write210=false;lastError=8;return 0;}')
    host = host.replace('long GetMicrosecondCount(){return 615001;}',
        'long GetMicrosecondCount(){static long micro=615001;return micro++;}')
    (build / 'host.cpp').write_text(host)
    mock = (root / 'tests/runtime_mock.cpp').read_text()
    mock = mock.replace('#include "host.cpp"', f'#include "{build}/host.cpp"')
    mock = mock.replace('#include "../MQL5/', f'#include "{root}/MQL5/')
    mock = mock.replace('EA_ADAPTED_PATH', str(build / 'EA_ModeloD_Fluxo_Sem_Ordens.mq5'))
    mock = mock.replace('int main(){', 'int inherited_runtime_main210(){', 1)
    mock = mock.replace('bool IsStopped(){return false;}', 'bool IsStopped(){return mock_stopped210;}')
    mock = mock.replace('bool EventSetTimer(int)',
        'bool mock_stopped210=false,mock_partial210=false;\nbool EventSetTimer(int)')
    mock = mock.replace('return out.size();\n}',
        'if(mock_partial210){lastError=4403;}return out.size();\n}', 1)
    (build / 'focused.cpp').write_text(mock + '\n' + (root / 'tests/tester210.cpp').read_text())
    flags = ['-std=c++17', '-O0', '-g', '-Wall', '-Wextra', '-Wno-unused-parameter']
    if a.sanitize:
        flags += ['-fsanitize=address,undefined', '-fno-omit-frame-pointer']
    result = subprocess.run(['c++', *flags, str(build / 'focused.cpp'), '-o', str(build / 'focused')], text=True, capture_output=True)
    (a.report_dir / 'COMPILACAO_LOCAL_v210.txt').write_text(result.stdout + result.stderr + f'\nEXIT_STATUS={result.returncode}\n')
    if result.returncode:
        print(result.stderr[-10000:])
        raise SystemExit(result.returncode)
    env = os.environ.copy()
    if a.sanitize:
        env['ASAN_OPTIONS'] = 'halt_on_error=1'
        env['UBSAN_OPTIONS'] = 'halt_on_error=1:print_stacktrace=1'
    result = subprocess.run([str(build / 'focused')], text=True, capture_output=True, env=env)
    (a.report_dir / 'TESTES_LOCAIS_v210.txt').write_text(result.stdout + result.stderr + f'\nEXIT_STATUS={result.returncode}\n')
    print('\n'.join(x for x in result.stdout.splitlines() if x.startswith(('PASS_210', 'FAIL_210', 'FOCUSED_210'))))
    if result.stderr:
        print(result.stderr[-6000:])
    raise SystemExit(result.returncode)
