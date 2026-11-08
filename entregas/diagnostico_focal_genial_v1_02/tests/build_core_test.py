"""Extrai núcleo e serialização reais do MQL para teste C++ com tipos simulados."""
import re
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'MQL5/Experts/ModeloD_Diagnostico_Focal'
build=ROOT/'tests/build';build.mkdir(exist_ok=True)
def convert(s):return re.sub(r'const (MqlTick|MqlRates) &(\w+)\[\]',r'const std::vector<\1> &\2',s)
(build/'hc_generated.hpp').write_text(convert((SOURCE/'HC_Core.mqh').read_text()))
(build/'focal_generated.hpp').write_text(convert((SOURCE/'Focal_Core.mqh').read_text()).replace('#include "HC_Core.mqh"','#include "hc_generated.hpp"'))
main=(SOURCE/'Diagnostico_Focal_Ticks_M1.mq5').read_text()
def function(name):
    match=re.search(r'(?:string|bool) '+name+r'\(',main);start=main.index('{',match.start());depth=1;end=start+1
    while depth:
        if main[end]=='{':depth+=1
        elif main[end]=='}':depth-=1
        end+=1
    return main[match.start():end]
(build/'format_generated.hpp').write_text(function('FMinuteCells')+'\n'+function('FSaveMinutes')+'\n')
subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-omit-frame-pointer','-I',str(build),str(ROOT/'tests/core_harness.cpp'),'-o',str(build/'core_test')],check=True)
print(build/'core_test')
