@echo off
title AirOne Professional v4.0 - Installer
color 0a
echo ================================================================================
echo              AirOne Professional v4.0 - INSTALLER
echo                 Complete System Installation
echo ================================================================================
echo.
echo Checking Python...

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

echo Installing packages...
pip install numpy psutil requests -q

echo.
echo ================================================================================
echo                    Installation Complete
echo ================================================================================
echo Installed: AirOne Professional v4.0
echo Location: %~dp0
echo.
echo Run: Launcher.bat
echo.
pause