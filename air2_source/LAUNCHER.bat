@echo off
title AirOne Professional v4.0 - Advanced Launcher
color 0A
setlocal enabledelayedexpansion

REM Enable UTF-8 encoding for Python
set PYTHONIOENCODING=utf-8

REM Set console size
mode con: cols=100 lines=40

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://www.python.org/
    pause
    exit /b 1
)

:MAIN_MENU
cls
echo ================================================================================
echo                      AirOne Professional v4.0 - Advanced Launcher
echo                           Ultimate Unified Edition
echo ================================================================================
echo.
echo                         Select Launch Mode:
echo                         ====================
echo.
echo    [1] Desktop GUI Mode           - Full graphical interface
echo    [2] Headless CLI Mode          - Command-line interface
echo    [3] Web Server Mode            - Web-based dashboard
echo    [4] Simulation Mode            - Pure simulation environment
echo    [5] Receiver Mode              - CanSat data receiver
echo    [6] Replay/Forensic Mode       - Historical data analysis
echo    [7] Safe Mode                  - Minimal secure operation
echo    [8] Offline Mode               - Air-gapped operation
echo    [9] Digital Twin Mode          - Advanced digital twin
echo.
echo   [A] Powerful Mode Pack          - All modes with AI enhancement
echo   [B] Powerful Security Mode      - Advanced security suite
echo   [C] Ultimate Enhanced Mode      - Most advanced operational mode
echo   [D] Cosmic Fusion Mode          - Quantum AI fusion + multiverse
echo   [E] CanSat Mission Mode         - AI-orchestrated mission
echo.
echo   [F] Quick Launch Options        - Pre-configured scenarios
echo   [G] Configuration Settings      - Customize launch parameters
echo   [H] System Diagnostics          - Full system check
echo   [I] System Tools                - Diagnostics and utilities
echo.
echo   [0] Exit
echo.
echo ================================================================================
echo.

set /p choice="Enter your choice (0-9, A-I): "

if /i "%choice%"=="1" goto LAUNCH_GUI
if /i "%choice%"=="2" goto LAUNCH_CLI
if /i "%choice%"=="3" goto LAUNCH_WEB
if /i "%choice%"=="4" goto LAUNCH_SIM
if /i "%choice%"=="5" goto LAUNCH_RX
if /i "%choice%"=="6" goto LAUNCH_REPLAY
if /i "%choice%"=="7" goto LAUNCH_SAFE
if /i "%choice%"=="8" goto LAUNCH_OFFLINE
if /i "%choice%"=="9" goto LAUNCH_DIGITAL_TWIN
if /i "%choice%"=="A" goto LAUNCH_POWERFUL
if /i "%choice%"=="B" goto LAUNCH_SECURITY
if /i "%choice%"=="C" goto LAUNCH_ULTIMATE
if /i "%choice%"=="D" goto LAUNCH_COSMIC
if /i "%choice%"=="E" goto LAUNCH_MISSION
if /i "%choice%"=="F" goto QUICK_LAUNCH
if /i "%choice%"=="G" goto CONFIG_SETTINGS
if /i "%choice%"=="H" goto SYSTEM_DIAGNOSTICS
if /i "%choice%"=="I" goto SYSTEM_TOOLS
if /i "%choice%"=="0" goto EXIT

echo Invalid choice! Please try again.
timeout /t 2 /nobreak >nul
goto MAIN_MENU

:LAUNCH_GUI
cls
echo Launching Desktop GUI Mode...
python main_unified.py --gui
if errorlevel 1 (
    echo.
    echo ERROR: GUI mode exited with an error
    echo Check logs/airone.log for details
    pause
)
goto MAIN_MENU

:LAUNCH_CLI
cls
echo Launching Headless CLI Mode...
python main_unified.py --cli
if errorlevel 1 (
    echo.
    echo ERROR: CLI mode exited with an error
    pause
)
goto MAIN_MENU

:LAUNCH_WEB
cls
echo ================================================================================
echo    Web Server Configuration
echo ================================================================================
echo.
set /p web_host="Enter host (default: 127.0.0.1): "
set /p web_port="Enter port (default: 5000): "

if "%web_host%"=="" set web_host=127.0.0.1
if "%web_port%"=="" set web_port=5000

echo.
echo Starting Web Server on http://%web_host%:%web_port%
echo Press Ctrl+C to stop
echo.
python main_unified.py --web --host %web_host% --port %web_port%
goto MAIN_MENU

:LAUNCH_SIM
cls
echo ================================================================================
echo    Simulation Configuration
echo ================================================================================
echo.
echo Simulation Options:
echo   [1] Normal Speed
echo   [2] Fast Forward (2x)
echo   [3] Maximum Speed (5x)
echo   [4] Custom Duration
echo.
set /p sim_speed="Select speed (1-4, default: 1): "

if "%sim_speed%"=="2" set speed_arg=2.0
if "%sim_speed%"=="3" set speed_arg=5.0
if "%sim_speed%"=="4" (
    set /p duration="Enter duration in seconds: "
    python main_unified.py --sim --auto-run --speed 1.0 --duration %duration%
    goto MAIN_MENU
)
if "%sim_speed%"=="" set speed_arg=1.0

python main_unified.py --sim --auto-run --speed %speed_arg%
goto MAIN_MENU

:LAUNCH_RX
cls
echo Launching Receiver Mode...
python main_unified.py --rx
goto MAIN_MENU

:LAUNCH_REPLAY
cls
echo ================================================================================
echo    Replay Mode Configuration
echo ================================================================================
echo.
set /p input_file="Enter input data file (or press Enter to skip): "

if "%input_file%"=="" (
    python main_unified.py --replay
) else (
    python main_unified.py --replay --input "%input_file%"
)
goto MAIN_MENU

:LAUNCH_SAFE
cls
echo Launching Safe Mode...
python main_unified.py --safe
goto MAIN_MENU

:LAUNCH_OFFLINE
cls
echo Launching Offline Mode...
python main_unified.py --offline
goto MAIN_MENU

:LAUNCH_DIGITAL_TWIN
cls
echo Launching Digital Twin Mode...
python main_unified.py --digital-twin
goto MAIN_MENU

:LAUNCH_POWERFUL
cls
echo Launching Powerful Mode Pack...
python main_unified.py --mode powerful
goto MAIN_MENU

:LAUNCH_SECURITY
cls
echo Launching Powerful Security Mode...
python main_unified.py --mode security
goto MAIN_MENU

:LAUNCH_ULTIMATE
cls
echo Launching Ultimate Enhanced Mode...
python main_unified.py --mode ultimate
goto MAIN_MENU

:LAUNCH_COSMIC
cls
echo Launching Cosmic Fusion Mode...
python main_unified.py --mode cosmic
goto MAIN_MENU

:LAUNCH_MISSION
cls
echo Launching CanSat Mission Mode...
python main_unified.py --mode mission
goto MAIN_MENU

:QUICK_LAUNCH
cls
echo ================================================================================
echo    Quick Launch Scenarios
echo ================================================================================
echo.
echo   [1] Development Mode (No Auth + Debug)
echo   [2] Demo Mode (Auto-run Simulation)
echo   [3] Production Web Server (All Interfaces)
echo   [4] Data Analysis (Replay with Output)
echo   [5] Full System Test (Profile + Verbose)
echo   [6] Minimal/Safe Mode (Quiet)
echo   [7] GUI with Custom Theme
echo   [8] Back to Main Menu
echo.
set /p quick_choice="Select scenario (1-8): "

if "%quick_choice%"=="1" (
    echo Launching Development Mode...
    python main_unified.py --cli --no-auth --debug --verbose
    goto MAIN_MENU
)
if "%quick_choice%"=="2" (
    echo Launching Demo Mode...
    python main_unified.py --sim --auto-run --duration 60
    goto MAIN_MENU
)
if "%quick_choice%"=="3" (
    echo Launching Production Web Server...
    echo Access at: http://localhost:5000
    python main_unified.py --web --host 0.0.0.0 --port 5000
    goto MAIN_MENU
)
if "%quick_choice%"=="4" (
    set /p replay_file="Enter data file to analyze: "
    set /p output_dir="Enter output directory: "
    python main_unified.py --replay --input "%replay_file%" --output "%output_dir%"
    goto MAIN_MENU
)
if "%quick_choice%"=="5" (
    echo Running Full System Test...
    python main_unified.py --profile --verbose
    goto MAIN_MENU
)
if "%quick_choice%"=="6" (
    echo Launching Minimal Mode...
    python main_unified.py --safe --quiet
    goto MAIN_MENU
)
if "%quick_choice%"=="7" (
    echo.
    echo Select Theme:
    echo   [1] Dark (Default)
    echo   [2] Light
    echo   [3] Blue
    echo   [4] Green
    echo   [5] High Contrast
    echo.
    set /p theme_choice="Select theme (1-5): "
    
    if "%theme_choice%"=="2" set theme=light
    if "%theme_choice%"=="3" set theme=blue
    if "%theme_choice%"=="4" set theme=green
    if "%theme_choice%"=="5" set theme=high-contrast
    if "%theme_choice%"=="" set theme=dark
    
    python main_unified.py --gui --theme %theme%
    goto MAIN_MENU
)
if "%quick_choice%"=="8" goto MAIN_MENU

echo Invalid choice!
timeout /t 2 /nobreak >nul
goto QUICK_LAUNCH

:CONFIG_SETTINGS
cls
echo ================================================================================
echo    Configuration Settings
echo ================================================================================
echo.
echo   [1] Edit Main Configuration
echo   [2] Edit Security Configuration
echo   [3] View System Information
echo   [4] Check Requirements
echo   [5] Back to Main Menu
echo.
set /p config_choice="Select option (1-5): "

if "%config_choice%"=="1" (
    if exist "airone_security_config.ini" (
        notepad airone_security_config.ini
    ) else (
        echo Configuration file not found!
        timeout /t 2 /nobreak >nul
    )
    goto CONFIG_SETTINGS
)
if "%config_choice%"=="2" (
    if exist "config\system_config.json" (
        notepad config\system_config.json
    ) else (
        echo Configuration file not found!
        timeout /t 2 /nobreak >nul
    )
    goto CONFIG_SETTINGS
)
if "%config_choice%"=="3" (
    python -c "from src.system.system_info import SystemInfo; import json; info = SystemInfo().get_all_info(); print(json.dumps(info, indent=2, default=str))"
    pause
    goto CONFIG_SETTINGS
)
if "%config_choice%"=="4" (
    echo Checking installed packages...
    pip list
    pause
    goto CONFIG_SETTINGS
)
if "%config_choice%"=="5" goto MAIN_MENU

echo Invalid choice!
timeout /t 2 /nobreak >nul
goto CONFIG_SETTINGS

:SYSTEM_DIAGNOSTICS
cls
echo ================================================================================
echo    AirOne Professional v4.0 - System Diagnostics
echo ================================================================================
echo.
echo Running comprehensive system check...
echo.
python src\startup_diagnostics.py
echo.
pause
goto MAIN_MENU

:SYSTEM_TOOLS
cls
echo ================================================================================
echo    System Tools and Utilities
echo ================================================================================
echo.
echo   [1] Run System Check
echo   [2] Run Startup Manager
echo   [3] View Logs
echo   [4] Clear Logs and Cache
echo   [5] Backup Configuration
echo   [6] Restore Configuration
echo   [7] Check Hardware Drivers
echo   [8] Generate System Report
echo   [9] Back to Main Menu
echo.
set /p tool_choice="Select tool (1-9): "

if "%tool_choice%"=="1" (
    cls
    echo Running System Check...
    python src\system\system_info.py
    pause
    goto SYSTEM_TOOLS
)
if "%tool_choice%"=="2" (
    cls
    echo Running Startup Manager...
    python src\system\startup_manager.py
    pause
    goto SYSTEM_TOOLS
)
if "%tool_choice%"=="3" (
    cls
    if exist "logs\airone.log" (
        type logs\airone.log | more
    ) else (
        echo No logs found!
        timeout /t 2 /nobreak >nul
    )
    goto SYSTEM_TOOLS
)
if "%tool_choice%"=="4" (
    cls
    echo Clearing logs and cache...
    if exist "logs\" (
        del /Q logs\*.log
        echo Logs cleared.
    )
    if exist "__pycache__\" (
        rmdir /S /Q __pycache__
        echo Cache cleared.
    )
    echo Cleanup complete!
    timeout /t 2 /nobreak >nul
    goto SYSTEM_TOOLS
)
if "%tool_choice%"=="5" (
    cls
    echo Backing up configuration...
    set backup_dir=backups\config_backup_%date:~-4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%
    set backup_dir=%backup_dir: =%
    mkdir "%backup_dir%" 2>nul
    if exist "config\" (
        xcopy /E /I /Y config\ "%backup_dir%\config\"
        echo Configuration backed up to: %backup_dir%
    ) else (
        echo No configuration to backup!
    )
    pause
    goto SYSTEM_TOOLS
)
if "%tool_choice%"=="6" (
    cls
    if exist "backups\" (
        echo Available backups:
        dir /b /ad backups\
        echo.
        set /p backup="Enter backup folder name: "
        if not "%backup%"=="" (
            if exist "backups\%backup%\config\" (
                xcopy /E /I /Y "backups\%backup%\config\" config\
                echo Configuration restored!
            ) else (
                echo No configuration in backup!
            )
        )
    ) else (
        echo No backups found!
    )
    pause
    goto SYSTEM_TOOLS
)
if "%tool_choice%"=="7" (
    cls
    echo Checking Hardware Drivers...
    python -c "from src.hardware.drivers import HardwareDrivers; drivers = HardwareDrivers(); results = drivers.scan_for_hardware(); import json; print(json.dumps(results, indent=2, default=str))"
    pause
    goto SYSTEM_TOOLS
)
if "%tool_choice%"=="8" (
    cls
    echo Generating System Report...
    python -c "from src.system.system_info import ReportGenerator; rg = ReportGenerator(); report = rg.generate_system_report(); print(f'Report saved to: {report}')"
    pause
    goto SYSTEM_TOOLS
)
if "%tool_choice%"=="9" goto MAIN_MENU

echo Invalid choice!
timeout /t 2 /nobreak >nul
goto SYSTEM_TOOLS

:EXIT
cls
echo.
echo ================================================================================
echo    Thank you for using AirOne Professional v4.0!
echo ================================================================================
echo.
timeout /t 2 /nobreak >nul
exit
