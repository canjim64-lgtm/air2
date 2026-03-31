@echo off
title AirOne Professional v4.0 - Tools and Utilities
color 0B

:MENU
cls
echo ========================================================================
echo    AirOne Professional v4.0 - Tools and Utilities
echo ========================================================================
echo.
echo Select a tool to run:
echo.
echo 1. Run System Check (Diagnostics & Information)
echo 2. Run Startup Manager (System Initialization)
echo 3. View System Information
echo 4. Check Hardware Drivers
echo 5. Generate System Report
echo 6. View Password Files
echo 7. Backup Configuration
echo 8. Restore Configuration
echo 9. Clear Logs and Cache
echo 0. Exit
echo.
echo ========================================================================
echo.

set /p choice="Enter your choice (0-9): "

if "%choice%"=="1" goto SYSTEM_CHECK
if "%choice%"=="2" goto STARTUP_MANAGER
if "%choice%"=="3" goto SYSTEM_INFO
if "%choice%"=="4" goto HARDWARE_CHECK
if "%choice%"=="5" goto GENERATE_REPORT
if "%choice%"=="6" goto VIEW_PASSWORDS
if "%choice%"=="7" goto BACKUP_CONFIG
if "%choice%"=="8" goto RESTORE_CONFIG
if "%choice%"=="9" goto CLEAR_LOGS
if "%choice%"=="0" goto EXIT

echo Invalid choice! Please try again.
timeout /t 2 /nobreak >nul
goto MENU

:SYSTEM_CHECK
cls
echo ========================================================================
echo    Running System Check...
echo ========================================================================
echo.
python src\system\system_info.py
echo.
pause
goto MENU

:STARTUP_MANAGER
cls
echo ========================================================================
echo    Running Startup Manager...
echo ========================================================================
echo.
python src\system\startup_manager.py
echo.
pause
goto MENU

:SYSTEM_INFO
cls
echo ========================================================================
echo    System Information
echo ========================================================================
echo.
python -c "from src.system.system_info import SystemInfo; import json; info = SystemInfo().get_all_info(); print(json.dumps(info, indent=2, default=str))"
echo.
pause
goto MENU

:HARDWARE_CHECK
cls
echo ========================================================================
echo    Hardware Driver Check
echo ========================================================================
echo.
python -c "from src.hardware.drivers import HardwareDrivers; drivers = HardwareDrivers(); results = drivers.scan_for_hardware(); import json; print(json.dumps(results, indent=2, default=str))"
echo.
pause
goto MENU

:GENERATE_REPORT
cls
echo ========================================================================
echo    Generating System Report...
echo ========================================================================
echo.
python -c "from src.system.system_info import ReportGenerator; rg = ReportGenerator(); report = rg.generate_system_report(); print(f'Report saved to: {report}')"
echo.
pause
goto MENU

:VIEW_PASSWORDS
cls
echo ========================================================================
echo    Password Files
echo ========================================================================
echo.
if exist "passwords\" (
    echo Password files found:
    echo.
    dir /b passwords\*.txt
    echo.
    set /p view="Enter password file to view (or press Enter to cancel): "
    if not "%view%"=="" (
        if exist "passwords\%view%" (
            type "passwords\%view%"
        ) else (
            echo File not found!
        )
    )
) else (
    echo No password files found.
)
echo.
pause
goto MENU

:BACKUP_CONFIG
cls
echo ========================================================================
echo    Backup Configuration
echo ========================================================================
echo.
set backup_dir=backups\config_backup_%date:~-4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%
set backup_dir=%backup_dir: =%
mkdir "%backup_dir%" 2>nul
if exist "config\" (
    xcopy /E /I /Y config\ "%backup_dir%\config\"
    echo Configuration backed up to: %backup_dir%
) else (
    echo No configuration to backup!
)
echo.
pause
goto MENU

:RESTORE_CONFIG
cls
echo ========================================================================
echo    Restore Configuration
echo ========================================================================
echo.
if exist "backups\" (
    echo Available backups:
    echo.
    dir /b /ad backups\
    echo.
    set /p backup="Enter backup folder name to restore (or press Enter to cancel): "
    if not "%backup%"=="" (
        if exist "backups\%backup%\config\" (
            xcopy /E /I /Y "backups\%backup%\config\" config\
            echo Configuration restored from: backups\%backup%
        ) else (
            echo No configuration found in backup!
        )
    )
) else (
    echo No backups found!
)
echo.
pause
goto MENU

:CLEAR_LOGS
cls
echo ========================================================================
echo    Clear Logs and Cache
echo ========================================================================
echo.
set /p confirm="Are you sure you want to clear logs and cache? (Y/N): "
if /i not "%confirm%"=="Y" goto MENU

if exist "logs\" (
    del /Q logs\*.log
    echo Logs cleared.
)

if exist "__pycache__\" (
    rmdir /S /Q __pycache__
    echo Cache cleared.
)

echo.
echo Cleanup complete!
echo.
pause
goto MENU

:EXIT
cls
echo.
echo Thank you for using AirOne Professional v4.0 Tools!
echo.
timeout /t 2 /nobreak >nul
exit
