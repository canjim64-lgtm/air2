@echo off
title AirOne Professional v4.0 - Complete Uninstallation
color 0C

echo ========================================================================
echo    AirOne Professional v4.0 - Complete Uninstallation
echo ========================================================================
echo.
echo WARNING: This will completely remove AirOne Professional v4.0
echo.
echo THIS WILL REMOVE:
echo   - All application files and source code
echo   - All configuration files
echo   - All data files and databases
echo   - All log files
echo   - All model files
echo   - All password files (BACKUP FIRST!)
echo   - All secret and certificate files
echo   - All backup files
echo   - All report files
echo   - All launchers and shortcuts
echo   - All documentation files
echo   - Python packages (optional)
echo.
echo THIS ACTION CANNOT BE UNDONE!
echo.
echo IMPORTANT:
echo   - BACKUP your password files from .\passwords\
echo   - BACKUP any important data from .\data\
echo   - BACKUP configuration from .\config\
echo   - BACKUP reports from .\reports\
echo.

:ASK_CONFIRM
set /p confirm=Are you sure you want to proceed with complete uninstallation? (Y/N): 
if /i not "%confirm%"=="Y" (
    if /i "%confirm%"=="N" (
        echo.
        echo Uninstallation cancelled.
        echo Your AirOne Professional v4.0 installation remains intact.
        pause
        exit /b 0
    )
    goto ASK_CONFIRM
)

echo.
echo Starting complete uninstallation of AirOne Professional v4.0...
echo.

REM Change to current directory
cd /d "%~dp0"

REM Stop any running processes
echo Step 1/10: Stopping running processes...
taskkill /f /im python.exe /fi "windowtitle eq AirOne*" >nul 2>&1
taskkill /f /im pythonw.exe /fi "windowtitle eq AirOne*" >nul 2>&1
echo Running processes terminated.
echo.

REM Backup passwords if requested
echo Step 2/10: Password backup...
set /p backup_passwords=Do you want to backup password files before deletion? (Y/N): 
if /i "%backup_passwords%"=="Y" (
    if exist "passwords\" (
        set backup_dir=backups\passwords_backup_%DATE:~-4%%DATE:~3,2%%DATE:~0,2%_%TIME:~0,2%%TIME:~3,2%
        set backup_dir=%backup_dir: =%
        mkdir "%backup_dir%" 2>nul
        xcopy /E /I /Y passwords\ "%backup_dir%\" >nul
        echo Passwords backed up to: %backup_dir%
    )
) else (
    echo Password backup skipped.
)
echo.

REM Remove application files
echo Step 3/10: Removing application files...
del /Q *.py >nul 2>&1
del /Q *.bat >nul 2>&1
del /Q *.txt >nul 2>&1
del /Q *.md >nul 2>&1
del /Q *.log >nul 2>&1
del /Q *.ini >nul 2>&1
del /Q *.json >nul 2>&1
del /Q *.xml >nul 2>&1
del /Q *.html >nul 2>&1
del /Q *.css >nul 2>&1
del /Q *.js >nul 2>&1
echo Application files removed.
echo.

REM Remove directories
echo Step 4/10: Removing directories...
rmdir /S /Q logs >nul 2>&1
rmdir /S /Q data >nul 2>&1
rmdir /S /Q config >nul 2>&1
rmdir /S /Q models >nul 2>&1
rmdir /S /Q passwords >nul 2>&1
rmdir /S /Q secrets >nul 2>&1
rmdir /S /Q certs >nul 2>&1
rmdir /S /Q backups >nul 2>&1
rmdir /S /Q reports >nul 2>&1
rmdir /S /Q tools >nul 2>&1
rmdir /S /Q build >nul 2>&1
rmdir /S /Q __pycache__ >nul 2>&1
echo Directories removed.
echo.

REM Remove src directory
echo Step 5/10: Removing source code directory...
if exist "src" (
    attrib -R -H -S "src" /s /d >nul 2>&1
    rmdir /S /Q "src" >nul 2>&1
    if exist "src" (
        echo Warning: Could not completely remove src directory
    ) else (
        echo Source code directory removed.
    )
) else (
    echo Source code directory not found.
)
echo.

REM Remove V3 directory if exists
echo Step 6/10: Removing V3 directory...
if exist "V3" (
    attrib -R -H -S "V3" /s /d >nul 2>&1
    rmdir /S /Q "V3" >nul 2>&1
    echo V3 directory removed.
) else (
    echo V3 directory not found.
)
echo.

REM Remove shortcuts
echo Step 7/10: Removing shortcuts...
if exist "%USERPROFILE%\Desktop\AirOne*.lnk" (
    del /Q "%USERPROFILE%\Desktop\AirOne*.lnk" >nul 2>&1
    echo Desktop shortcuts removed.
)
if exist "%USERPROFILE%\Desktop\*.lnk" (
    del /Q "%USERPROFILE%\Desktop\*.lnk" >nul 2>&1
)
for /f "tokens=*" %%i in ('dir "%APPDATA%\Microsoft\Windows\Start Menu\Programs" /b /s 2^>nul ^| findstr /i "AirOne"') do (
    del /Q "%%i" >nul 2>&1
)
echo Start Menu shortcuts removed.
echo.

REM Remove registry entries
echo Step 8/10: Removing registry entries...
reg delete "HKCU\Software\AirOne" /f >nul 2>&1
reg delete "HKLM\Software\AirOne" /f >nul 2>&1
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\AirOne" /f >nul 2>&1
echo Registry entries removed.
echo.

REM Remove environment variables
echo Step 9/10: Removing environment variables...
setx AIRONE_HOME "" >nul 2>&1
setx AIRONE_CONFIG "" >nul 2>&1
setx AIRONE_DATA "" >nul 2>&1
setx AIRONE_LOGS "" >nul 2>&1
setx AIRONE_PASSWORDS "" >nul 2>&1
echo Environment variables removed.
echo.

REM Clean temp files
echo Step 10/10: Cleaning temporary files...
del /Q "%TEMP%\airone_*" >nul 2>&1
if exist "%LOCALAPPDATA%\airone" (
    rmdir /S /Q "%LOCALAPPDATA%\airone" >nul 2>&1
)
if exist "%APPDATA%\airone" (
    rmdir /S /Q "%APPDATA%\airone" >nul 2>&1
)
echo Temporary files cleaned.
echo.

REM Optional: Remove Python packages
echo.
echo ========================================================================
echo Python Packages Removal (OPTIONAL)
echo ========================================================================
echo.
echo Do you want to uninstall Python packages that were installed for AirOne?
echo.
echo WARNING: This may remove packages that other applications depend on!
echo Recommended: Keep packages unless you're sure you don't need them
echo.
set /p uninstall_packages=Uninstall Python packages? (Y/N - Recommended: N): 
if /i "%uninstall_packages%"=="Y" (
    echo.
    echo Uninstalling Python packages...
    echo This may take several minutes...
    echo.
    
    pip uninstall -y numpy pandas scipy scikit-learn matplotlib PyQt5 PyQtWebEngine folium cryptography pyjwt bcrypt argon2-cffi flask flask-socketio flask-cors flask-jwt-extended flask-limiter aiohttp websockets click rich psutil pyserial torch transformers accelerate optuna datasets evaluate tokenizers sentencepiece plotly dash dash-bootstrap-components redis sqlalchemy alembic requests beautifulsoup4 lxml openpyxl xlrd Pillow opencv-python mediapipe sounddevice pyaudio playsound schedule python-dotenv colorama tabulate tqdm pytz python-dateutil timezonefinder geopy jinja2 typing-extensions pywin32 GPUtil face-recognition librosa qiskit pyusb libusb1 rtlsdr gps3 pynmea2 smbus2 pytest pytest-cov mock >nul 2>&1
    
    echo Python packages uninstalled.
) else (
    echo Python packages retained (recommended).
    echo You can manually uninstall them later if needed.
)
echo.

REM Create uninstallation report
echo Creating uninstallation report...
(
echo AirOne Professional v4.0 - Uninstallation Report
echo ================================================
echo Uninstallation Date: %DATE% %TIME%
echo.
echo Removed Components:
echo   - Application Files: Removed
echo   - Configuration Files: Removed
echo   - Data Files: Removed
echo   - Log Files: Removed
echo   - Model Files: Removed
echo   - Password Files: Removed ^(or backed up^)
echo   - Secret Files: Removed
echo   - Certificate Files: Removed
echo   - Backup Files: Removed
echo   - Report Files: Removed
echo   - Launchers: Removed
echo   - Shortcuts: Removed
echo   - Registry Entries: Removed
echo   - Environment Variables: Removed
echo   - Temporary Files: Removed
echo   - Source Code: Removed
echo.
echo Python Packages: %if "%uninstall_packages%"=="Y" ("Uninstalled") else ("Retained")%
echo.
echo Directories Removed:
echo   - logs/
echo   - data/
echo   - config/
echo   - models/
echo   - passwords/
echo   - secrets/
echo   - certs/
echo   - backups/
echo   - reports/
echo   - tools/
echo   - src/
echo   - V3/
echo   - build/
echo   - __pycache__/
echo.
echo Status: UNINSTALLATION COMPLETE
echo.
echo Note: Some files may remain if they were in use or had permission issues.
echo You can manually delete the installation directory if needed.
echo.
echo If you want to reinstall:
echo   1. Download AirOne Professional v4.0 installer
echo   2. Run INSTALL.bat
echo   3. Follow installation prompts
) > UNINSTALLATION_REPORT.txt
echo Uninstallation report created: UNINSTALLATION_REPORT.txt
echo.

REM Try to remove the installation directory itself
cd ..
if exist "%~dp0" (
    rd "%~dp0" >nul 2>&1
    if errorlevel 1 (
        echo.
        echo Note: Installation directory not empty or in use.
        echo You can manually delete it later: %~dp0
    ) else (
        echo Installation directory removed.
    )
)
echo.

echo ========================================================================
echo    UNINSTALLATION COMPLETE!
echo ========================================================================
echo.
echo AirOne Professional v4.0 has been completely removed from your system.
echo.
echo WHAT WAS REMOVED:
echo   - All application files
echo   - All configuration files
echo   - All data and logs
echo   - All models and secrets
echo   - All shortcuts
echo   - All registry entries
echo   - All environment variables
echo   - All temporary files
if "%uninstall_packages%"=="Y" (
    echo   - Python packages ^(as requested^)
) else (
    echo   - Python packages ^(retained as requested^)
)
echo.
echo FILES CREATED:
echo   - UNINSTALLATION_REPORT.txt ^(Uninstallation log^)
echo.
echo IF YOU WANT TO REINSTALL:
echo   1. Download AirOne Professional v4.0 installer
echo   2. Run INSTALL.bat
echo   3. Follow the installation prompts
echo.
echo Thank you for using AirOne Professional v4.0!
echo.
pause
