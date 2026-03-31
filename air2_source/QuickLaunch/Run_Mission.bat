@echo off
title AirOne Professional v4.0 - Mission Control
color 0A
echo ========================================================================
echo    AirOne Professional v4.0 - CanSat MISSION MODE
echo ========================================================================
echo.
echo Launching CanSat Mission Control
echo.
echo Features:
echo   - AI-orchestrated mission
echo   - Real-time telemetry analysis
echo   - Autonomous decision making
echo   - Full mission lifecycle management
echo.
timeout /t 2 /nobreak >nul
echo.
python main_unified.py --mode mission
if errorlevel 1 (
    echo.
    echo ERROR: Mission mode failed to start
    pause
)
