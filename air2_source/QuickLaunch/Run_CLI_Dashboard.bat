@echo off
title AirOne Professional v4.0 - CLI Dashboard
color 0A
echo ========================================================================
echo    AirOne Professional v4.0 - CLI Dashboard
echo ========================================================================
echo.
echo Starting terminal-based real-time dashboard...
echo.
echo Features:
echo   - Live telemetry monitoring
echo   - System resources display
echo   - Mission status tracking
echo   - Rich terminal UI
echo.
echo Press Ctrl+C to exit
echo.
python src\cli_dashboard.py --refresh 1.0
if errorlevel 1 (
    echo.
    echo ERROR: Dashboard failed to start
    pause
)
