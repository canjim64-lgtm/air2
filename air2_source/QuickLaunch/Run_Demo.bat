@echo off
title AirOne Professional v4.0 - Demo Mode
color 0A
echo ========================================================================
echo    AirOne Professional v4.0 - DEMO MODE
echo ========================================================================
echo.
echo Starting automated demo simulation...
echo Duration: 60 seconds
echo.
python main_unified.py --sim --auto-run --duration 60 --speed 1.0
if errorlevel 1 (
    echo.
    echo ERROR: Demo mode failed to start
    pause
)
