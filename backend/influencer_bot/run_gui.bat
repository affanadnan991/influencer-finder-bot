@echo off
title Influencer Finder Dashboard Launcher
echo ====================================================
echo 🎯 Starting Influencer Finder Bot Web Server...
echo ====================================================

REM Auto-detect virtual environment Python
if exist "venv\bin\python.exe" (
    set PYTHON_BIN=venv\bin\python.exe
) else if exist "venv\bin\python" (
    set PYTHON_BIN=venv\bin\python
) else if exist "venv\Scripts\python.exe" (
    set PYTHON_BIN=venv\Scripts\python.exe
) else (
    echo ❌ Virtual environment Python interpreter not found!
    echo Please run setup.py or run.py to configure the environment first.
    pause
    exit /b 1
)

echo 🔑 Checking dashboard server launch...
echo 🚀 Opening dashboard in your default browser...
start http://localhost:5000

echo.
echo Dashboard is running. Close this command prompt window to stop the server.
echo.
%PYTHON_BIN% gui_server.py
pause
