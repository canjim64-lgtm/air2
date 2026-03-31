@echo off
title AirOne Professional v4.0 - Mission Control
color 0A
echo ========================================================================
echo    AirOne Professional v4.0 - Mission Control Center
echo ========================================================================
echo.
echo Starting Mission Control Center...
echo.
echo Features:
echo   - Real-time mission monitoring
echo   - State machine (IDLE, LAUNCH, ASCENT, APOGEE, DESCENT, LANDING)
echo   - Telemetry tracking
echo   - Event logging
echo   - Threshold alerts
echo   - Data export
echo.
echo Testing mission control...
echo.
python src\mission_control.py
echo.
pause
