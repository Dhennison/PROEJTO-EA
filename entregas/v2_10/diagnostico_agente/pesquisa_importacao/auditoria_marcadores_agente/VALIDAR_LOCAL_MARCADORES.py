from pathlib import Path
import importlib.util,tempfile,zipfile,shutil,sys
sys.dont_write_bytecode=True
b=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('host_dia',b/'controle_dia/VALIDAR_LOCAL_DIA.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
with tempfile.TemporaryDirectory(prefix='md_marker_host_') as tmp:
 folder=Path(tmp);csv=folder/'day.csv'
 with zipfile.ZipFile(b/'coleta_dia_20261103/WINZ26_20261030_DIA_COMPLETO.zip') as z:
  with z.open('WINZ26_20261030_DIA_COMPLETO.csv') as f,csv.open('wb') as o:shutil.copyfileobj(f,o)
 prelude=h.EXPERT_PRELUDE.replace('bool SymbolInfoTick(string,MqlTick &v){v=fixture.back();','long callback_index=-1;bool SymbolInfoTick(string,MqlTick &v){v=callback_index>=0?fixture[callback_index]:fixture.back();')
 main=h.EXPERT_MAIN.replace(' reset();tester=false;',''' reset();check(OnInit()==INIT_SUCCEEDED,"callback init failed");
 for(size_t i=0;i<fixture.size();i++){callback_index=(long)i;OnTick();}callback_index=-1;
 check(md_replay_valid==4319271&&md_replay_trades==3190938&&md_replay_all==MD_EXPECT_HASH_ALL&&md_replay_trade==MD_EXPECT_HASH_TRADE&&md_replay_bad==0&&md_replay_volume_bad==0,"callback sequence differs");
 OnTester();OnDeinit(0);check(complete(),"observational replay changed verdict");
 reset();tester=false;''')
 h.build_run(folder,'markers',prelude+h.translate(Path(__file__).resolve().parent/'MQL5/Experts/ModeloD_Diagnostico_Pesquisa/Diagnostico_Marcadores_Dia_WINZ26.mq5')+main,(csv,b/'m1_atual_20261103/WINZ26_M1_20261030_SECUNDARIO_ATUAL.csv'))
