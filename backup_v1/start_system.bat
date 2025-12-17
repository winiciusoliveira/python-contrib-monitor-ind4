@echo off
TITLE Orquestrador Industrial

echo [1/2] Iniciando o Motor de Monitoramento (Backend)...
start "Service Monitor" cmd /k python service_monitor.py

echo Aguardando inicializacao do banco de dados...
timeout /t 3

echo [2/2] Iniciando o Dashboard (Frontend)...
start "Dashboard Streamlit" cmd /k streamlit run dashboard.py

echo.
echo =================================================
echo SISTEMA INICIADO COM SUCESSO.
echo Nao feche as janelas pretas.
echo =================================================
pause