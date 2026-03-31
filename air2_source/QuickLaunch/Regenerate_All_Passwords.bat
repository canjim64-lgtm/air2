@echo off
title AirOne Professional v4.0 - Regenerate All Passwords
color 0C
echo ========================================================================
echo    AirOne Professional v4.0 - ULTRA-SECURE PASSWORD REGENERATOR
echo ========================================================================
echo.
echo WARNING: This will generate NEW passwords for ALL users!
echo.
echo IMPORTANT:
echo   - All previous passwords will become INVALID
echo   - New passwords are 512 characters of maximum complexity
echo   - Passwords include Unicode symbols and special characters
echo   - Each password is UNIQUE and changes EVERY generation
echo   - You MUST copy/paste - passwords CANNOT be typed manually
echo.
echo ========================================================================
echo.

set /p confirm="Are you sure you want to regenerate ALL passwords? (YES/NO): "

if /i not "%confirm%"=="YES" (
    echo.
    echo Operation cancelled.
    pause
    exit /b 1
)

echo.
echo Regenerating passwords for all users...
echo.

python src\security\advanced_password_generator.py

echo.
echo ========================================================================
echo    Password Regeneration Complete!
echo ========================================================================
echo.
echo NEW passwords have been saved to: passwords\ folder
echo.
echo NEXT STEPS:
echo   1. Go to passwords\ folder
echo   2. Copy the latest password files (latest_password_*.txt)
echo   3. Save passwords securely
echo   4. Delete this notification file
echo   5. NEVER share your passwords!
echo.
echo SECURITY REMINDERS:
echo   - Passwords are 512 characters (copy/paste ONLY)
echo   - Passwords change EVERY time they are generated
echo   - Save password files after EACH login
echo   - Use a password manager for security
echo.
pause
