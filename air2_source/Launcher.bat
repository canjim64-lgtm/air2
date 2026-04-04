@echo off
cd /d "%~dp0"

if "%1"=="" (
    python launcher.py
) else (
    python launcher.py %1
)
pause
