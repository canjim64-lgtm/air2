@echo off
title AirOne Professional v4.0 - Profile & Test
color 0F
echo ========================================================================
echo    AirOne Professional v4.0 - Performance Profiling
echo ========================================================================
echo.
echo Running with performance profiling enabled...
echo.
echo This will:
echo   - Track all function calls
echo   - Measure execution times
echo   - Generate performance report
echo.
echo Note: This will run slower than normal
echo.
timeout /t 2 /nobreak >nul
echo.
python main_unified.py --gui --profile
if errorlevel 1 (
    echo.
    echo ERROR: Profiling failed
    pause
)
