@echo off
title NOVA AI Assistant (Windows)
cd /d "%~dp0"
echo =======================================================
echo          KHOI DONG TRO LY AO NOVA (WINDOWS)
echo =======================================================
echo [Info] Kich hoat moi truong ao Python...
call .\venv\Scripts\activate.bat

echo [Info] Khoi chay he thong NOVA AI...
python app.py

pause
