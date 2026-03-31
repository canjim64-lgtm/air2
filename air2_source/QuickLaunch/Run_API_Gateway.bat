@echo off
title AirOne Professional v4.0 - API Gateway Server
color 0B
echo ========================================================================
echo    AirOne Professional v4.0 - API Gateway Server
echo ========================================================================
echo.
echo Starting RESTful API Gateway...
echo.
echo Endpoints:
echo   GET  /api/health          - Health check
echo   GET  /api/status          - System status
echo   GET  /api/telemetry       - Get telemetry
echo   POST /api/telemetry       - Post telemetry
echo   GET  /api/users           - Get users (admin)
echo   GET  /api/logs            - Get logs (admin)
echo   GET  /api/config          - Get configuration
echo   POST /api/commands        - Execute command
echo   POST /api/export          - Export data
echo.
echo Authentication:
echo   Header: X-API-Key: ^<your-api-key^>
echo.
echo Default API Keys:
echo   Admin:    admin_api_key_2026
echo   Operator: operator_api_key_2026
echo   Viewer:   viewer_api_key_2026
echo.
echo Press Ctrl+C to stop
echo.
python src\api_gateway.py --host 0.0.0.0 --port 8080
if errorlevel 1 (
    echo.
    echo ERROR: API Gateway failed to start
    pause
)
