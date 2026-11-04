@echo off
setlocal
if not exist "%~dp0terminal64.exe" (
 echo Coloque este arquivo e ModeloD_Funcional_BRL.ini na raiz do MT5 secundario.
 pause
 exit /b 1
)
if not exist "%~dp0ModeloD_Funcional_BRL.ini" (
 echo Arquivo ModeloD_Funcional_BRL.ini nao encontrado nesta pasta.
 pause
 exit /b 1
)
echo Compile primeiro EA_ModeloD_Ensaio_Funcional.mq5 com F7.
echo Feche o MT5 secundario antes de continuar. Nao precisa fechar o principal.
echo Este comando iniciara automaticamente um teste SIMULADO em BRL.
pause
start "" "%~dp0terminal64.exe" /portable /config:"%~dp0ModeloD_Funcional_BRL.ini"
