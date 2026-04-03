@echo off
title AirOne Professional v4.0 - Uninstaller
color 0c
echo ================================================================================
echo              AirOne Professional v4.0 - UNINSTALLER
echo ================================================================================
echo.
set /p CONFIRM="Are you sure? (Y/N): "
if /i not "%CONFIRM%"=="Y" exit

echo Removing AirOne...
del /q "%~dp0reports" 2>nul
del /q "%~dp0logs" 2>nul
del /q "%~dp0config" 2>nul

echo.
echo ================================================================================
echo                   Uninstall Complete
echo ================================================================================
pause