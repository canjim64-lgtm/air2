@echo off
title AirOne Professional v4.0 - System Health Monitor
color 0A
echo ========================================================================
echo    AirOne Professional v4.0 - System Health Monitor
echo ========================================================================
echo.
echo Checking system health...
echo.
python src\system_health.py
echo.
echo For continuous monitoring, use:
echo   python -c "from src.system_health import SystemHealthMonitor; m = SystemHealthMonitor(); m.start_monitoring(); import time; [time.sleep(1) for _ in iter(int, 1)]"
echo.
pause
