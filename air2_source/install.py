#!/usr/bin/env python3
"""
AirOne Professional v4.0 - Python Installer
Installs all required dependencies and sets up the environment
"""
import os
import sys
import subprocess
import time

# Simple color codes
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
CYAN = '\033[96m'
BOLD = '\033[1m'
END = '\033[0m'

def banner():
    print(f"""
{CYAN}{BOLD}
================================================================================
                    AirOne Professional v4.0
                        INSTALLER
================================================================================
{END}
""")

def check_python():
    print(f"{YELLOW}Checking Python version...{END}", end=" ")
    if sys.version_info >= (3, 8):
        print(f"{GREEN}OK ({sys.version_info.major}.{sys.version_info.minor}){END}")
        return True
    print(f"{RED}FAILED - Python 3.8+ required{END}")
    return False

def check_pip():
    print(f"{YELLOW}Checking pip...{END}", end=" ")
    try:
        subprocess.run([sys.executable, '-m', 'pip', '--version'], 
                      capture_output=True, check=True)
        print(f"{GREEN}OK{END}")
        return True
    except:
        print(f"{RED}FAILED{END}")
        return False

# Package list: (pip_name, import_name, description)
PACKAGES = [
    ('numpy', 'numpy', 'Numerical computing'),
    ('psutil', 'psutil', 'System monitoring'),
    ('requests', 'requests', 'HTTP requests'),
    ('flask', 'flask', 'Web framework'),
    ('pyjwt', 'jwt', 'JSON Web Tokens'),
    ('cryptography', 'cryptography', 'Encryption'),
    ('pillow', 'PIL', 'Image processing'),
    ('pandas', 'pandas', 'Data analysis'),
    ('PyQt5', 'PyQt5', 'GUI framework'),
    ('PyQtWebEngine', 'PyQtWebEngine', 'Web view'),
    ('pyserial', 'serial', 'Serial communication'),
    ('matplotlib', 'matplotlib', 'Plotting'),
    ('pyqtgraph', 'pyqtgraph', 'Fast plotting'),
]

def check_installed(pip_name, import_name):
    """Check if a package is installed"""
    try:
        __import__(import_name)
        return True
    except ImportError:
        return False

def install_one(pip_name, import_name, description, num, total):
    """Install a single package one by one"""
    # First check if already installed
    if check_installed(pip_name, import_name):
        print(f"[{num}/{total}] {pip_name:20s} {GREEN}already installed{END}")
        return True, False  # success, newly_installed
    
    print(f"[{num}/{total}] {pip_name:20s} {YELLOW}installing...{END}", end=" ", flush=True)
    
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '--upgrade', pip_name],
            capture_output=True,
            text=True,
            timeout=180
        )
        
        if result.returncode == 0:
            # Verify it installed correctly
            if check_installed(pip_name, import_name):
                print(f"{GREEN}INSTALLED{END}")
                return True, True
            else:
                print(f"{YELLOW}installed but not verified{END}")
                return False, True
        else:
            error = result.stderr.split('\n')[-2] if result.stderr else "unknown error"
            print(f"{RED}FAILED{END}")
            print(f"       {error[:50]}")
            return False, True
            
    except subprocess.TimeoutExpired:
        print(f"{RED}TIMEOUT{END}")
        return False, True
    except Exception as e:
        print(f"{RED}ERROR: {str(e)[:30]}{END}")
        return False, True

def create_dirs():
    """Create required directories"""
    print(f"\n{YELLOW}Creating directories...{END}")
    dirs = ['logs', 'reports', 'data', 'config', 'models']
    for d in dirs:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), d)
        os.makedirs(path, exist_ok=True)
        print(f"  {GREEN}created:{END} {d}/")

def main():
    banner()
    
    if not check_python():
        sys.exit(1)
    if not check_pip():
        print(f"{RED}pip not available{END}")
        sys.exit(1)
    
    create_dirs()
    
    print(f"\n{BLUE}{BOLD}Installing 13 packages one by one...{END}\n")
    
    installed = 0
    already = 0
    failed = 0
    
    for i, (pip_name, import_name, desc) in enumerate(PACKAGES, 1):
        success, new = install_one(pip_name, import_name, desc, i, len(PACKAGES))
        if success:
            if new:
                installed += 1
            else:
                already += 1
        else:
            failed += 1
        time.sleep(0.3)
    
    print(f"""
================================================================================
                       INSTALLATION SUMMARY
================================================================================
  {GREEN}Newly installed:{END}   {installed}
  {YELLOW}Already installed:{END} {already}
  {RED}Failed:{END}             {failed}

Run: python3 launcher.py
================================================================================
""")

if __name__ == "__main__":
    main()