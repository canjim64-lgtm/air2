@echo off
title AirOne Professional v4.0 - Installer
color 0a
echo ================================================================================
echo              AirOne Professional v4.0 - INSTALLER
echo ================================================================================
echo.

echo Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.8+
    pause
    exit /b 1
)

echo.
echo Running Python installer...
python install.py

echo.
echo ================================================================================
echo                    INSTALLATION COMPLETE
echo ================================================================================
echo Run: python launcher.py
echo.
pause