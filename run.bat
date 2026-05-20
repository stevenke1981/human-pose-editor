@echo off
title Human Pose Editor Launcher
cd /d "%~dp0"

:: Check if virtual environment and pythonw exists
if not exist ".venv\Scripts\pythonw.exe" (
    echo ==========================================================
    echo [ERROR] Virtual environment or pythonw.exe not found!
    echo Please make sure you have run the setup commands:
    echo   uv venv
    echo   uv pip install -r pyproject.toml
    echo ==========================================================
    pause
    exit /b
)

echo Launching Human Pose Editor...
:: Start using pythonw.exe to run GUI without showing CMD console window
start "" ".venv\Scripts\pythonw.exe" main.py
exit
