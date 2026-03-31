@echo off
title AirOne Professional v4.0 - Analyze Telemetry
color 0B
echo ========================================================================
echo    AirOne Professional v4.0 - Telemetry Analyzer
echo ========================================================================
echo.
echo This tool analyzes telemetry data from files.
echo.
set /p input_file="Enter telemetry file path (or press Enter for test): "

if "%input_file%"=="" (
    echo.
    echo Running test analysis...
    python src\telemetry_analyzer.py
) else (
    echo.
    echo Analyzing: %input_file%
    python -c "from telemetry_analyzer import TelemetryAnalyzer; a = TelemetryAnalyzer(); a.load_data('%input_file%'); a.calculate_statistics(); a.detect_anomalies(); print(a.generate_report('txt'))"
)
echo.
pause
