@echo off
title AirOne Professional v4.0 - Ultimate Unified Edition
color 0A

echo ================================================================================
echo                     AirOne Professional v4.0 - ULTIMATE UNIFIED EDITION
echo                         Complete Integration of ALL Features
echo ================================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://www.python.org/
    pause
    exit /b 1
)

REM Run the new unified launcher
python airone.py %*

if errorlevel 1 (
    echo.
    echo ERROR: AirOne exited with an error
    echo Check logs/airone.log for details
    pause
)
