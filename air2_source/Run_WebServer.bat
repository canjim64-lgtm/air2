@echo off
title AirOne Professional v4.0 - Web Server Mode
color 0B

echo ================================================================================
echo                     AirOne Professional v4.0 - WEB SERVER MODE
echo                         Real-time Dashboard & REST API
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

echo [2/3] Checking web server dependencies...
pip show flask >nul 2>&1
if errorlevel 1 (
    echo WARNING: Flask may not be installed
    echo Run INSTALL.bat first to install all dependencies
    echo.
)

echo [3/3] Starting Web Server...
echo.
echo ================================================================================
echo.
echo Starting Flask web server...
echo.
echo Access the dashboard at: http://127.0.0.1:5000
echo Access the REST API at:  http://127.0.0.1:5001
echo.
echo Press Ctrl+C to stop the server
echo.
echo ================================================================================
echo.

cd /d "%~dp0"
python -c "from src.modes.web_mode import WebMode; wm = WebMode(); wm.start()"

if errorlevel 1 (
    echo.
    echo ERROR: Web server exited with an error
    echo Check logs/airone.log for details
    pause
)
