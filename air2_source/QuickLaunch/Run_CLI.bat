@echo off
title AirOne Professional v4.0 - CLI Mode
color 0B
echo Launching AirOne Professional CLI...
echo.
python main_unified.py --cli --verbose
if errorlevel 1 (
    echo.
    echo ERROR: CLI failed to start
    pause
)
