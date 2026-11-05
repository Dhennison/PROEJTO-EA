"""Run actual MQL adapter/opening bodies translated only for C++ syntax."""
from pathlib import Path
import re, subprocess, tempfile, os
root = Path(__file__).resolve().parents[1]
expert = root / 'MQL5/Experts/ModeloD_Ensaio_Funcional_21101'
with tempfile.TemporaryDirectory(prefix='md21101_') as tmp:
    build = Path(tmp)
    for name, target in [('ModeloD_ConsultaTicks21101.mqh', 'query_adapted.mqh'),
                         ('ModeloD_OpeningTicks.mqh', 'opening_adapted.mqh')]:
        s = (expert / name).read_text()
        s = re.sub(r'^input ', '', s, flags=re.M)
        s = re.sub(r'MqlTick &(\w+)\[\]', r'std::vector<MqlTick> &\1', s)
        s = re.sub(r'MqlTick (\w+)\[\];', r'std::vector<MqlTick> \1;', s)
        (build / target).write_text(s)
    cmd = ['c++', '-std=c++17', '-Wall', '-Wextra', '-Werror', '-g',
           '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
           '-I', str(build), str(root/'tests/query.cpp'), '-o', str(build/'query')]
    subprocess.run(cmd, check=True)
    env = dict(os.environ, ASAN_OPTIONS='halt_on_error=1', UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
    result = subprocess.run([str(build/'query')], text=True, capture_output=True, env=env)
    (root/'TESTES_CONSULTAS.txt').write_text(result.stdout + result.stderr)
    print(result.stdout, result.stderr)
    result.check_returncode()
