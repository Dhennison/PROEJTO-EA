"""Compila as funções do núcleo MQL em C++ com tipos simulados; não é MetaEditor."""
import re
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'MQL5/Experts/ModeloD_Historico_Diagnostico/HC_Core.mqh').read_text()
source=re.sub(r'const (MqlTick|MqlRates) &(\w+)\[\]',r'const std::vector<\1> &\2',source)
build=ROOT/'tests/build';build.mkdir(exist_ok=True)
(build/'core_generated.hpp').write_text(source)
subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-omit-frame-pointer','-I',str(build),str(ROOT/'tests/core_harness.cpp'),'-o',str(build/'core_test')],check=True)
print(build/'core_test')
