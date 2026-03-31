@echo off
title AirOne Professional v4.0 - Simulation Mode
color 0E
echo Starting AirOne Simulation...
echo.
python main_unified.py --sim --auto-run --speed 1.0
if errorlevel 1 (
    echo.
    echo ERROR: Simulation failed to start
    pause
)
