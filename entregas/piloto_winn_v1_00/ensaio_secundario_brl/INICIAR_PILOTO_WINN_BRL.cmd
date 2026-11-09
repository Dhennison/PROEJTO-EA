@echo off
setlocal
if not exist "%~dp0terminal64.exe" (
 echo Coloque este CMD e o INI na RAIZ da instalacao SECUNDARIA da Genial, junto de terminal64.exe.
 pause
 exit /b 1
)
if not exist "%~dp0ModeloD_Piloto_WINN_BRL.ini" (
 echo Falta ModeloD_Piloto_WINN_BRL.ini nesta mesma pasta.
 pause
 exit /b 1
)
if not exist "%~dp0MQL5\Experts\ModeloD_PilotoWINN\EA_ModeloD_Piloto_WINN.ex5" (
 echo Instale e compile EA_ModeloD_Piloto_WINN.mq5 nesta instalacao secundaria antes de continuar.
 pause
 exit /b 1
)
echo PILOTO SIMULADO WIN$N - 21/09/2026 - 1 contrato por nivel.
echo O INI solicita deposito em BRL sem usar a lista de moedas da interface.
echo Confirme antes que esta copia secundaria esta no servidor GenialInvestimentos-PRD.
echo Feche APENAS o MT5 secundario e seu MetaEditor antes de continuar.
echo O MT5 principal pode permanecer aberto.
pause
start "" "%~dp0terminal64.exe" /portable /config:"%~dp0ModeloD_Piloto_WINN_BRL.ini"
