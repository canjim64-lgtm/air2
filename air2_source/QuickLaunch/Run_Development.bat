@echo off
title AirOne Professional v4.0 - Development Mode
color 0F
echo ========================================================================
echo    AirOne Professional v4.0 - DEVELOPMENT MODE
echo ========================================================================
echo.
echo WARNING: Authentication is DISABLED
echo DEBUG logging is ENABLED
echo.
echo This mode is for DEVELOPMENT and TESTING ONLY
echo DO NOT use in production!
echo.
timeout /t 3 /nobreak >nul
echo.
echo Starting Development Mode...
python main_unified.py --cli --no-auth --debug --verbose
if errorlevel 1 (
    echo.
    echo ERROR: Development mode failed to start
    pause
)
