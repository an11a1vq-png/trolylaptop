@echo off
title NOVA AI Assistant (Windows)
cd /d "%~dp0"
echo =======================================================
echo          KHOI DONG TRO LY AO NOVA (WINDOWS)
echo =======================================================

:: Kiem tra va khoi dong Ollama neu chua chay
set "OLLAMA_EXE=%LOCALAPPDATA%\Programs\Ollama\ollama.exe"
if exist "%OLLAMA_EXE%" (
    curl -s http://127.0.0.1:11434 >nul 2>&1
    if errorlevel 1 (
        echo [Info] Khoi dong dich vu AI Ollama cuc bo...
        start "" /B "%OLLAMA_EXE%" serve >nul 2>&1
        timeout /t 2 /nobreak >nul
    )
)

echo [Info] Kich hoat moi truong ao Python...
call .\venv\Scripts\activate.bat

echo [Info] Khoi chay he thong NOVA AI...
python app.py

:: Giai phong RAM bang cach dong Ollama khi thoat tro ly
echo [Info] Dang giai phong tai nguyen he thong...
taskkill /F /IM ollama.exe >nul 2>&1

pause
