@echo off
title AirOne Professional v4.0 - Safe Mode
color 04
echo ========================================================================
echo    AirOne Professional v4.0 - SAFE MODE
echo ========================================================================
echo.
echo Starting in SAFE MODE (minimal functionality)
echo.
echo This mode is for:
echo   - System recovery
echo   - Troubleshooting
echo   - Minimal resource usage
echo.
python main_unified.py --safe --quiet
if errorlevel 1 (
    echo.
    echo ERROR: Safe mode failed to start
    pause
)
