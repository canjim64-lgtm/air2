#!/usr/bin/env python3
"""
AirOne Professional v4.0 - All-in-One Launcher
Install | Launch | Uninstall
"""

import sys
import os
import subprocess
import shutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def do_install():
    """Install dependencies"""
    print("""
================================================================================
                    AirOne - INSTALLING
================================================================================
""")
    packages = ['numpy', 'psutil', 'requests', 'flask', 'pyjwt', 'cryptography', 'pillow']
    for pkg in packages:
        try:
            print(f"  Installing {pkg}...", end=" ")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q', pkg], 
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("OK")
        except:
            print("FAILED")
    
    # Create shortcuts
    with open(os.path.join(SCRIPT_DIR, 'Launcher.bat'), 'w') as f:
        f.write("""@echo off
cd /d "%~dp0"
python main.py
pause
""")
    print("\n✓ Installation complete!")
    print("Run: python main.py")
    return 0

def do_uninstall():
    """Uninstall and clean up"""
    print("""
================================================================================
                    AirOne - UNINSTALL
================================================================================
WARNING: This will remove AirOne files and shortcuts.
""")
    confirm = input("Type 'yes' to confirm: ").strip().lower()
    if confirm != 'yes':
        print("Cancelled.")
        return 0
    
    # Remove shortcuts
    for f in ['Launcher.bat', 'launcher.py']:
        path = os.path.join(SCRIPT_DIR, f)
        if os.path.exists(path):
            os.remove(path)
            print(f"  Removed {f}")
    
    # Remove reports
    reports = os.path.join(SCRIPT_DIR, 'reports')
    if os.path.exists(reports):
        shutil.rmtree(reports)
        print("  Removed reports/")
    
    print("\n✓ Uninstall complete!")
    return 0

def run_mode(choice):
    """Run selected mode"""
    src_dir = os.path.join(SCRIPT_DIR, 'src')
    
    desc_map = {
        '1': ('GUI', 'gui/main_gui.py'),
        '2': ('CLI', 'modes/headless_cli_mode.py'),
        '3': ('Web', 'web/web_dashboard.py'),
        '4': ('API', 'api_server/rest_api.py'),
        '5': ('Desktop', 'modes/desktop_gui_mode.py'),
        '6': ('System', 'system/system_info.py'),
        '7': ('Telemetry', 'telemetry/advanced_telemetry_features.py'),
        '8': ('Ground Station', 'ground_station/ground_station.py'),
        '9': ('AI', 'ai/ai_chat_assistant.py'),
        '10': ('Security', 'security/enhanced_security_module.py'),
        '11': ('Quantum', 'quantum/quantum_computing.py'),
        '12': ('Cosmic', 'cosmic/cosmic_ai.py'),
        '13': ('Pipeline', 'pipeline/data_pipeline.py'),
    }
    
    if choice not in desc_map:
        print("Invalid choice")
        return 1
    
    desc, rel_path = desc_map[choice]
    full_path = os.path.join(src_dir, rel_path)
    
    print(f"\nStarting {desc}...")
    
    if not os.path.exists(full_path):
        print(f"Module not found: {rel_path}")
        return 1
    
    try:
        with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
            code = compile(f.read(), full_path, 'exec')
        ns = {'__name__': '__main__', '__file__': full_path}
        exec(code, ns)
        if 'main' in ns:
            ns['main']()
    except Exception as e:
        print(f"Error: {type(e).__name__}")
    
    return 0

def main():
    # Print menu
    print("""
================================================================================
                    AirOne Professional v4.0
================================================================================
    [I] Install    [U] Uninstall    [Q] Quit
================================================================================
    13 Modes: GUI | CLI | Web | API | Desktop | System | Telemetry
             Ground Station | AI | Security | Quantum | Cosmic | Pipeline
================================================================================
 [1] GUI    [2] CLI    [3] Web    [4] API    [5] Desktop
 [6] System [7] Telemetry [8] Ground [9] AI    [10] Security
 [11] Quantum [12] Cosmic [13] Pipeline
================================================================================
""")
    
    # Get choice from args or stdin
    choice = ""
    if len(sys.argv) > 1:
        choice = sys.argv[1].lower()
    elif not sys.stdin.isatty():
        choice = input().strip().lower()
    else:
        choice = input("Choice: ").strip().lower()
    
    # Handle choice
    if choice in ['i', 'install', '1']:
        return do_install()
    if choice in ['u', 'uninstall']:
        return do_uninstall()
    if choice in ['q', 'quit', 'exit']:
        print("Goodbye!")
        return 0
    
    # Try as mode number
    if choice.isdigit() and 1 <= int(choice) <= 13:
        return run_mode(choice)
    
    print(f"Invalid: {choice}")
    return 1

if __name__ == "__main__":
    sys.exit(main())