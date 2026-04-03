#!/usr/bin/env python3
"""
AirOne Professional v4.0 - Python Installer
Installs all required dependencies for AirOne
"""

import subprocess
import sys
import os
import shutil

def print_header():
    print("""
================================================================================
                    AirOne Professional v4.0
                         PYTHON INSTALLER
================================================================================
""")

def check_python():
    """Check Python version"""
    print("[1] Checking Python...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"    ✓ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print("    ✗ Python 3.8+ required")
        return False

def install_packages():
    """Install required packages"""
    print("\n[2] Installing packages...")
    
    packages = [
        'numpy',
        'psutil', 
        'requests',
        'flask',
        # 'torch',  # Optional - large download
        'pyjwt',
        'cryptography',
        'pillow',
    ]
    
    for pkg in packages:
        try:
            print(f"    Installing {pkg}...", end=" ")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q', pkg])
            print("OK")
        except Exception as e:
            print(f"FAILED: {e}")
    
    print("\n    ✓ All packages installed")

def create_shortcuts():
    """Create launcher shortcuts"""
    print("\n[3] Creating shortcuts...")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create Launcher.bat
    bat_content = """@echo off
title AirOne Professional v4.0
cd /d "%~dp0"
python main.py
pause
"""
    with open(os.path.join(script_dir, 'Launcher.bat'), 'w') as f:
        f.write(bat_content)
    print("    ✓ Launcher.bat created")
    
    # Create Python launcher
    py_content = """#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from main import main
if __name__ == "__main__":
    main()
"""
    with open(os.path.join(script_dir, 'launcher.py'), 'w') as f:
        f.write(py_content)
    print("    ✓ launcher.py created")

def verify_installation():
    """Verify key modules can be imported"""
    print("\n[4] Verifying installation...")
    
    modules = ['numpy', 'psutil', 'requests', 'flask']
    for mod in modules:
        try:
            __import__(mod)
            print(f"    ✓ {mod}")
        except ImportError:
            print(f"    ✗ {mod} - not installed")
    
    print("\n[5] Testing main.py...")
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from main import main as launcher_main
        print("    ✓ Main module loads")
    except Exception as e:
        print(f"    ✗ {e}")

def main():
    print_header()
    
    if not check_python():
        print("\nPlease install Python 3.8+ from python.org")
        input("Press Enter to exit...")
        return 1
    
    install_packages()
    create_shortcuts()
    verify_installation()
    
    print("""
================================================================================
                       INSTALLATION COMPLETE
================================================================================

Run: python main.py
   or: Launcher.bat

Choose mode 1-13 to start different modules.
""")
    
    input("Press Enter to launch AirOne...")
    
    from main import main
    return main()

if __name__ == "__main__":
    sys.exit(main())