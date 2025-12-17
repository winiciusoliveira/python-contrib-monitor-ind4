@echo off
title Sistema de Monitoramento Industrial v2.0
color 0A

echo ========================================
echo   Sistema de Monitoramento Industrial
echo   Versao 2.0 - Clean Architecture
echo ========================================
echo.

REM Ativa ambiente virtual
if exist .venv\Scripts\activate.bat (
    echo [*] Ativando ambiente virtual...
    call .venv\Scripts\activate.bat
) else (
    echo [!] Ambiente virtual nao encontrado!
    echo [*] Continuando com Python global...
)

echo.
echo ========================================
echo   Iniciando Servicos
echo ========================================
echo.

REM Inicia o servico de monitoramento em uma nova janela
echo [1/2] Iniciando servico de monitoramento...
start "Servico de Monitoramento v2.0" cmd /k "python service_monitor.py"

REM Aguarda 3 segundos
timeout /t 3 /nobreak >nul

REM Inicia o dashboard em uma nova janela
echo [2/2] Iniciando dashboard...
start "Dashboard v2.0" cmd /k "streamlit run dashboard.py"

echo.
echo ========================================
echo   Sistema Iniciado com Sucesso!
echo ========================================
echo.
echo [*] Servico de Monitoramento: Rodando
echo [*] Dashboard: Abrindo navegador...
echo.
echo [i] Para parar o sistema:
echo     - Feche as janelas dos servicos
echo     - Ou pressione Ctrl+C em cada janela
echo.
echo [i] Acesse o dashboard em:
echo     http://localhost:8501
echo.
echo [i] Arquivos antigos foram movidos para: backup_v1/
echo.

pause
