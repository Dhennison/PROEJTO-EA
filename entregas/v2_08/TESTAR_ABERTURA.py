from pathlib import Path
import subprocess
import sys
art=Path(__file__).resolve().parent
experts=Path(sys.argv[1])
(art/'opening_adapted.mqh').write_text((experts/'ModeloD_OpeningTicks.mqh').read_text().replace('MqlTick ticks[];','std::vector<MqlTick> ticks;'))
subprocess.run(['c++','-std=c++17','-Wall','-Wextra','-fsanitize=address,undefined','-g',str(art/'opening_ticks.cpp'),'-o','/tmp/opening208'],check=True)
subprocess.run(['/tmp/opening208'],check=True)
