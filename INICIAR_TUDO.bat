@echo off
cd /d "%~dp0"

:: Chama o python direto da venv.
:: Ele já entende que deve usar as bibliotecas instaladas lá.
".\.venv\Scripts\python.exe" launcher.py

pause