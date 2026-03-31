@echo off
title AirOne Professional v4.0 - Web Server
color 0C
echo Starting AirOne Professional Web Server...
echo.
echo Server will be available at:
echo   Local:   http://127.0.0.1:5000
echo   Network: http://0.0.0.0:5000
echo.
echo Press Ctrl+C to stop the server
echo.
python main_unified.py --web --host 0.0.0.0 --port 5000
if errorlevel 1 (
    echo.
    echo ERROR: Web server failed to start
    pause
)
