@echo off
title AirOne Professional v4.0 - Launcher
color 0a
echo ================================================================================
echo                 AirOne Professional v4.0 - LAUNCHER
echo                    Complete System Integration
echo ================================================================================
echo.

cd /d "%~dp0air2_source"

python main_launch.py %*

echo.
echo Press any key to exit...
pause >nul