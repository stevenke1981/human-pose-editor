@echo off
title Human Pose Editor - Environment Setup
color 0B
cd /d "%~dp0"

echo =====================================================================
echo    __  __                                 _____                 
echo   ^|  ^/  ^|                                ^|  __ \                
echo   ^| \_/ ^|  _   _  _ __ ___    __ _  _ __   ^| ^|__) ^|___   ___   ___ 
echo   ^|  _  ^| ^| ^| ^| ^|^| '_ ` _ \  ^/ _` ^|^| '_ \  ^|  ___^// _ \ ^/ __^| ^/ _ \
echo   ^| ^| ^| ^| ^| ^|_^| ^|^| ^| ^| ^| ^| ^|^| (_^| ^|^| ^| ^| ^| ^| ^|   ^| (_) ^|\__ \^|  __/
echo   ^|_^| ^|_^|  \__,_^|^|_^| ^|_^| ^|_^| \__,_^|^|_^| ^|_^| ^|_^|    \___^/ ^|___^/ \___^|
echo =====================================================================
echo           Setting up the Python Dependency Environment...
echo =====================================================================
echo.

:: 1. Check Python installation
echo [+] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    color 0C
    echo [ERROR] Python was not found in your system PATH!
    echo Please install Python 3.9 or higher and make sure to check 
    echo the box "Add Python to environment variables (PATH)" during setup.
    echo.
    echo Website: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)
python --version

:: 2. Check if uv is installed
echo.
echo [+] Checking if 'uv' packet manager is available...
uv --version >nul 2>&1
if errorlevel 1 (
    echo [*] 'uv' is not installed globally. 
    echo [+] Attempting to install 'uv' via pip for faster dependency resolution...
    python -m pip install uv >nul 2>&1
)

:: Re-verify 'uv' after attempting pip install
uv --version >nul 2>&1
if errorlevel 0 (
    echo [+] 'uv' is active. Starting setup using 'uv'...
    echo.
    echo [+] Creating virtual environment (.venv)...
    uv venv
    if errorlevel 1 (
        echo [WARNING] 'uv venv' failed. Falling back to native python venv...
        python -m venv .venv
    )
    echo.
    echo [+] Installing dependencies (PySide6, Pillow)...
    .venv\Scripts\uv pip install PySide6>=6.5.0 Pillow>=10.0.0
    if errorlevel 1 (
        echo [WARNING] 'uv pip install' failed. Falling back to standard pip...
        .venv\Scripts\python -m pip install PySide6>=6.5.0 Pillow>=10.0.0
    )
) else (
    echo [-] 'uv' is not available. Falling back to standard Python 'venv' and 'pip'...
    echo.
    echo [+] Creating virtual environment (.venv)...
    python -m venv .venv
    if errorlevel 1 (
        color 0C
        echo [ERROR] Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo.
    echo [+] Upgrading pip inside virtual environment...
    .venv\Scripts\python -m pip install --upgrade pip
    echo.
    echo [+] Installing dependencies (PySide6, Pillow)...
    .venv\Scripts\python -m pip install PySide6>=6.5.0 Pillow>=10.0.0
)

if errorlevel 1 (
    color 0C
    echo.
    echo =====================================================================
    echo [ERROR] Dependency installation failed! 
    echo Please check your internet connection and try running this script again.
    echo =====================================================================
    pause
    exit /b 1
)

echo.
color 0A
echo =====================================================================
echo [+] ENVIRONMENT SETUP COMPLETED SUCCESSFULLY!
echo =====================================================================
echo.
echo You can now launch the application by:
echo   1. Double-clicking "run.bat"
echo   2. Or running ".venv\Scripts\python main.py" in terminal.
echo.
echo Have fun creating awesome poses for Gemini and AI art!
echo =====================================================================
echo.
pause
exit /b 0
