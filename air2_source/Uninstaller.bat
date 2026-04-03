@echo off
title AirOne Professional v4.0 - Uninstaller
color 0c
echo ================================================================================
echo              AirOne Professional v4.0 - UNINSTALLER
echo ================================================================================
echo.
set /p CONFIRM="Are you sure? (Y/N): "
if /i not "%CONFIRM%"=="Y" exit

echo Uninstalling AirOne...
pip uninstall numpy psutil requests flask pyjwt cryptography pillow -y 2>nul

echo Removing shortcuts...
del /q "%~dp0Launcher.bat" 2>nul

echo Removing reports...
rmdir /s /q "%~dp0reports" 2>nul

echo.
echo ================================================================================
echo                   Uninstall Complete
echo ================================================================================
pause