@echo off
title AirOne Professional v4.0 - GUI Mode
color 0A
echo Launching AirOne Professional GUI...
echo.
python main_unified.py --gui --theme modern_dark
if errorlevel 1 (
    echo.
    echo ERROR: GUI failed to start
    pause
)
