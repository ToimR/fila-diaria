@echo off
cd /d C:\filadiaria202604

echo ======================================================
echo           INICIANDO SERVIDOR FILA DIARIA
echo ======================================================
echo.

::Aguarda antes de entrar com o endereço
timeout /t 2
:: Abre o navegador padrão no endereço do servidor
:: O comando 'start' seguido de uma URL faz o Windows usar o navegador padrão
start http://192.168.1.13:5000

echo Aguardando inicializacao...
echo.

:: Minimiza a janela do terminal para não atrapalhar
powershell -windowstyle minimized -command ""

:: Executa o servidor Python
C:\filadiaria202604\.venv\Scripts\python.exe -m waitress --threads=6 --host=192.168.1.13 --port=5000 filadiaria:app

pause
