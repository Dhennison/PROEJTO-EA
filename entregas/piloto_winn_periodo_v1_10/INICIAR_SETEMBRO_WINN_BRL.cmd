@echo off
setlocal
if not exist "%~dp0terminal64.exe" (
 echo Coloque este CMD e o INI na RAIZ do MT5 SECUNDARIO, junto de terminal64.exe.
 pause
 exit /b 1
)
if not exist "%~dp0ModeloD_WINN_Setembro_BRL.ini" (
 echo Falta ModeloD_WINN_Setembro_BRL.ini na mesma pasta deste CMD.
 pause
 exit /b 1
)
if not exist "%~dp0MQL5\Experts\ModeloD_PilotoWINN_Periodo\EA_ModeloD_WINN_Periodo.ex5" (
 echo Compile primeiro EA_ModeloD_WINN_Periodo.mq5 no MetaEditor DESTE secundario.
 pause
 exit /b 1
)
echo SIMULACAO - WIN$N - 01 A 21/09/2026 - BRL - UM CONTRATO POR NIVEL.
echo TICKS REAIS SE DISPONIVEIS; CONFERIR NO DIARIO SE HOUVE GERACAO SUBSTITUTA.
echo Confira que esta copia secundaria esta em GenialInvestimentos-PRD.
echo Feche APENAS o MT5 secundario e o MetaEditor dele antes de continuar.
echo O principal e o MT5 da XP podem permanecer abertos.
pause
start "" "%~dp0terminal64.exe" /portable /config:"%~dp0ModeloD_WINN_Setembro_BRL.ini"
