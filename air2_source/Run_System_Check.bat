@echo off
title AirOne Professional v4.0 - System Check
color 0E

echo ================================================================================
echo                     AirOne Professional v4.0 - SYSTEM CHECK
echo                         Diagnostics & Information
echo ================================================================================
echo.
echo [1/3] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://www.python.org/
    pause
    exit /b 1
)
python --version
echo.

echo [2/3] Running system diagnostics...
echo.
echo ================================================================================
echo.

cd /d "%~dp0"
python src\system\system_info.py

if errorlevel 1 (
    echo.
    echo WARNING: System check encountered an error
    echo Check logs/airone.log for details
    echo.
)

echo.
echo ================================================================================
echo.
echo [3/3] System check complete.
echo.
pause
