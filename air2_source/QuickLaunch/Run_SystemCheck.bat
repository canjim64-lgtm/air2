@echo off
title AirOne Professional v4.0 - System Check
color 0B
echo ========================================================================
echo    AirOne Professional v4.0 - System Diagnostics
echo ========================================================================
echo.
echo Running comprehensive system check...
echo.
python src\system\system_info.py
echo.
echo ========================================================================
echo    Startup Manager
echo ========================================================================
echo.
python src\system\startup_manager.py
echo.
echo ========================================================================
echo    Hardware Check
echo ========================================================================
echo.
python -c "from src.hardware.drivers import HardwareDrivers; drivers = HardwareDrivers(); results = drivers.scan_for_hardware(); import json; print(json.dumps(results, indent=2, default=str))"
echo.
pause
