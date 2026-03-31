@echo off
title AirOne Professional v4.0 - Generate User Password
color 0B
echo ========================================================================
echo    AirOne Professional v4.0 - Ultra-Secure Password Generator
echo ========================================================================
echo.
set /p username="Enter username to generate password for: "

if "%username%"=="" (
    echo ERROR: Username cannot be empty!
    pause
    exit /b 1
)

echo.
echo Generating ultra-secure password for: %username%
echo Password length: 512 characters (maximum security)
echo.

python -c "from src.security.advanced_password_generator import generate_and_save_password; p = generate_and_save_password('%username%'); print('Password generated successfully!'); print(f'Length: {len(p)} characters'); print('Saved to: passwords\\latest_password_%username%.txt')"

echo.
echo ========================================================================
echo    Password Generated!
echo ========================================================================
echo.
echo Location: passwords\latest_password_%username%.txt
echo.
echo IMPORTANT:
echo   - Password is 512 characters - use COPY/PASTE only!
echo   - Password will be DIFFERENT next time you generate!
echo   - Save this password file securely!
echo.
pause
