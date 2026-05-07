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
start http://10.66.24.105:8502

echo Aguardando inicializacao...
echo.

:: Minimiza a janela do terminal para não atrapalhar
powershell -windowstyle minimized -command ""

:: Executa o servidor Python
"C:\FILA-DIARIA\.venv\Scripts\python.exe" -m waitress --threads=6 --host=10.66.24.105 --port=8502 filadiaria:app

pause
