@echo off
title AirOne Professional v4.0 - Web Dashboard
color 0B
echo ========================================================================
echo    AirOne Professional v4.0 - Web Dashboard
echo ========================================================================
echo.
echo Starting Web Dashboard...
echo.
echo Dashboard will be available at:
echo   Local:   http://127.0.0.1:5001
echo   Network: http://0.0.0.0:5001
echo.
echo Features:
echo   - Real-time telemetry monitoring
echo   - System resources display
echo   - Interactive charts
echo   - Mission status tracking
echo   - Alert notifications
echo.
echo Press Ctrl+C to stop the dashboard
echo.
python src\web_dashboard.py --host 0.0.0.0 --port 5001
if errorlevel 1 (
    echo.
    echo ERROR: Web dashboard failed to start
    pause
)
