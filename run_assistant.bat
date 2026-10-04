@echo off
title Hey Google Assistant (Windows)
cd /d "%~dp0"
echo =======================================================
echo          KHOI DONG TRO LY AO HEY GOOGLE (PC)
echo =======================================================
echo [Info] Kich hoat moi truong ao Python...
call .\venv\Scripts\activate.bat

echo [Info] Khoi chay tro ly ao...
python app.py

pause
