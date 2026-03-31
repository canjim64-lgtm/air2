@echo off
title AirOne Professional v4.0 - Export Data
color 0E
echo ========================================================================
echo    AirOne Professional v4.0 - Data Export Utility
echo ========================================================================
echo.
echo This utility exports telemetry and system data in multiple formats.
echo.
echo Supported formats:
echo   - JSON (structured data)
echo   - CSV (spreadsheet compatible)
echo   - TXT (human readable)
echo   - HTML (web report)
echo   - XML (structured markup)
echo.
set /p format="Enter export format (json/csv/txt/html/xml, default: json): "
set /p filename="Enter filename (or press Enter for auto-generated): "

if "%format%"=="" set format=json

echo.
echo Exporting data...
python -c "from data_export import DataExporter; de = DataExporter(); print('Export completed:', de.export({'test': 'data', 'timestamp': '__import__(\"datetime\").datetime.now().isoformat()'}, '%format%', '%filename%' if '%filename%' else None))"
echo.
echo Check the 'exports' folder for exported files.
echo.
pause
