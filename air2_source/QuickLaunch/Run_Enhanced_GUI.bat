@echo off
title AirOne Professional v4.0 - Enhanced Tabbed GUI
color 0A
echo ========================================================================
echo    AirOne Professional v4.0 - Enhanced Tabbed GUI
echo ========================================================================
echo.
echo Starting Enhanced GUI with Advanced Tabs...
echo.
echo Tabs Include:
echo   [1] Dashboard - Real-time metrics and gauges
echo   [2] Telemetry - Data tables and export
echo   [3] Mission Control - State machine and commands
echo   [4] AI Analysis - Chat assistant and recommendations
echo   [5] System Health - Resource monitoring
echo   [6] API Gateway - API endpoints and status
echo   [7] Settings - Theme and configuration
echo.
python src\gui\enhanced_tabbed_gui.py
if errorlevel 1 (
    echo.
    echo ERROR: GUI failed to start
    echo Make sure PyQt5 is installed: pip install PyQt5
    pause
)
