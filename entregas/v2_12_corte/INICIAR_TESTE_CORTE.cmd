@echo off
setlocal
if not exist "%~dp0terminal64.exe" (
 echo Coloque este arquivo e ModeloD_Corte_1800_BRL.ini na raiz do MT5 secundario.
 pause
 exit /b 1
)
if not exist "%~dp0ModeloD_Corte_1800_BRL.ini" (
 echo Arquivo ModeloD_Corte_1800_BRL.ini nao encontrado nesta pasta.
 pause
 exit /b 1
)
if not exist "%~dp0MQL5\Experts\ModeloD_Ensaio_Corte\EA_ModeloD_Ensaio_Corte.ex5" (
 echo Compile primeiro o EA_ModeloD_Ensaio_Corte.mq5 no MetaEditor secundario.
 pause
 exit /b 1
)
echo Execute primeiro o script Preparar_Cenario_Corte_WINZ26 e confira READY.
echo Compile primeiro EA_ModeloD_Ensaio_Corte.mq5 com F7.
echo Feche o MT5 secundario antes de continuar. Nao precisa fechar o principal.
echo Este comando iniciara automaticamente o teste SINTETICO DO CORTE em BRL.
pause
start "" "%~dp0terminal64.exe" /portable /config:"%~dp0ModeloD_Corte_1800_BRL.ini"
