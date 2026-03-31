@echo off
:: ================================================
:: AirOne Professional v4.0 - Unified Installer
:: Complete installation with all dependencies
:: ================================================

echo ================================================
echo AirOne Professional v4.0 - Unified Installer
echo ================================================
echo.

:: Check Python availability
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://www.python.org/
    pause
    exit /b 1
)

echo [OK] Python found

:: Create virtual environment
echo.
echo [*] Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment
    pause
    exit /b 1
)

:: Activate virtual environment
echo [*] Activating virtual environment...
call venv\Scripts\activate.bat

:: Upgrade pip
echo [*] Upgrading pip...
python -m pip install --upgrade pip

:: Install core dependencies
echo [*] Installing core dependencies...
pip install numpy cryptography bcrypt argon2-cffi psutil requests

:: Install AI/ML dependencies
echo [*] Installing AI/ML dependencies...
pip install scikit-learn scipy pandas matplotlib opencv-python

:: Install Flask and web dependencies
echo [*] Installing web dependencies...
pip install flask flask-socketio flask-cors

:: Install GUI dependencies
echo [*] Installing GUI dependencies...
pip install PyQt5 PyQtWebEngine

:: Install JWT/Security
echo [*] Installing security dependencies...
pip install PyJWT

:: Install DeepSeek and transformers (optional)
echo [*] Installing DeepSeek and AI models...
pip install torch transformers huggingface-hub accelerate

:: Install additional utilities
echo [*] Installing additional utilities...
pip install pillow plotly scikit-image

echo.
echo ================================================
echo Installation Complete!
echo ================================================
echo.
echo AirOne Professional v4.0 has been installed successfully.
echo.
echo To run the application:
echo   1. Activate the virtual environment:
echo      call venv\Scripts\activate.bat
echo   2. Run the launcher:
echo      python main_unified.py
echo.
echo Or use the provided LAUNCHER.bat
echo.

:: Create activation script for convenience
echo @echo off > run_airone.bat
echo call venv\Scripts\activate.bat >> run_airone.bat
echo python main_unified.py %%* >> run_airone.bat

echo Created run_airone.bat for easy startup
pause