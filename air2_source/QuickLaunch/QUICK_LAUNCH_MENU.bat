@echo off
title AirOne Professional v4.0 - Quick Launch Menu
color 0A
setlocal enabledelayedexpansion

:MENU
cls
echo ================================================================================
echo                 AirOne Professional v4.0 - Quick Launch Menu
echo                      Ultimate Unified Edition
echo ================================================================================
echo.
echo                    Select a quick launch scenario:
echo                    ================================
echo.
echo    [1] Run GUI Mode              - Full graphical interface
echo    [2] Run CLI Mode              - Command-line interface
echo    [3] Run Web Server            - Web dashboard (all interfaces)
echo    [4] Run Simulation            - Automated simulation
echo.
echo    [5] Run Development Mode      - Debug + No Auth (DEV ONLY)
echo    [6] Run Demo Mode             - 60-second automated demo
echo    [7] Run Safe Mode             - Minimal recovery mode
echo.
echo    [8] Run Ultimate Mode         - All features enhanced
echo    [9] Run Cosmic Mode           - Quantum AI fusion
echo    [A] Run Mission Mode          - CanSat mission control
echo.
echo    [B] System Check              - Full diagnostics
echo    [C] Performance Profile       - Test with profiling
echo.
echo    [0] Back to Main Launcher
echo.
echo ================================================================================
echo.

set /p choice="Enter your choice (0-9, A-C): "

if /i "%choice%"=="1" goto RUN_GUI
if /i "%choice%"=="2" goto RUN_CLI
if /i "%choice%"=="3" goto RUN_WEB
if /i "%choice%"=="4" goto RUN_SIM
if /i "%choice%"=="5" goto RUN_DEV
if /i "%choice%"=="6" goto RUN_DEMO
if /i "%choice%"=="7" goto RUN_SAFE
if /i "%choice%"=="8" goto RUN_ULTIMATE
if /i "%choice%"=="9" goto RUN_COSMIC
if /i "%choice%"=="A" goto RUN_MISSION
if /i "%choice%"=="B" goto RUN_CHECK
if /i "%choice%"=="C" goto RUN_PROFILE
if /i "%choice%"=="0" goto EXIT

echo Invalid choice! Please try again.
timeout /t 2 /nobreak >nul
goto MENU

:RUN_GUI
cls
echo Starting GUI Mode...
python main_unified.py --gui --theme modern_dark
goto MENU

:RUN_CLI
cls
echo Starting CLI Mode...
python main_unified.py --cli --verbose
goto MENU

:RUN_WEB
cls
echo Starting Web Server on http://0.0.0.0:5000
echo Press Ctrl+C to stop
python main_unified.py --web --host 0.0.0.0 --port 5000
goto MENU

:RUN_SIM
cls
echo Starting Simulation...
python main_unified.py --sim --auto-run --speed 1.0
goto MENU

:RUN_DEV
cls
echo WARNING: Development Mode (No Auth + Debug)
timeout /t 2 /nobreak >nul
python main_unified.py --cli --no-auth --debug --verbose
goto MENU

:RUN_DEMO
cls
echo Starting 60-second Demo...
python main_unified.py --sim --auto-run --duration 60
goto MENU

:RUN_SAFE
cls
echo Starting Safe Mode...
python main_unified.py --safe --quiet
goto MENU

:RUN_ULTIMATE
cls
echo Starting Ultimate Enhanced Mode...
python main_unified.py --mode ultimate
goto MENU

:RUN_COSMIC
cls
echo Starting Cosmic Fusion Mode...
python main_unified.py --mode cosmic
goto MENU

:RUN_MISSION
cls
echo Starting CanSat Mission Mode...
python main_unified.py --mode mission
goto MENU

:RUN_CHECK
cls
echo Running System Check...
python src\system\system_info.py
echo.
pause
goto MENU

:RUN_PROFILE
cls
echo Running with Performance Profiling...
python main_unified.py --gui --profile
goto MENU

:EXIT
cls
echo.
echo Returning to main launcher...
timeout /t 2 /nobreak >nul
exit
