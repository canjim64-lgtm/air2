@echo off
title AirOne Professional v4.0 - Batch Processor
color 0E
echo ========================================================================
echo    AirOne Professional v4.0 - Batch Processing Utility
echo ========================================================================
echo.
echo This tool processes multiple files in batch.
echo.
echo Place files in the 'data' folder before running.
echo.
pause

echo.
echo Starting batch processor...
python src\batch_processor.py
echo.
pause
