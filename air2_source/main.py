#!/usr/bin/env python3
"""
AirOne Professional v4.0 - All-in-One Launcher
Install | Launch | Uninstall | Menu Loop
"""
import sys
import os
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def do_install():
    print("\n" + "="*80)
    print("                    AirOne - INSTALLING")
    print("="*80)
    packages = ['numpy', 'psutil', 'requests', 'flask', 'pyjwt', 'cryptography', 'pillow', 'pandas', 'PyQt5', 'PyQtWebEngine']
    for pkg in packages:
        try:
            print(f"  Installing {pkg}...", end=" ", flush=True)
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q', pkg],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("OK")
        except:
            print("FAILED")
    print("\n[+] Installation complete!")
    return 0

def do_uninstall():
    print("\n" + "="*80)
    print("                    AirOne - UNINSTALL")
    print("="*80)
    confirm = input("Type 'yes' to confirm: ").strip().lower()
    if confirm != 'yes':
        print("Cancelled.")
        return 0
    for f in ['Launcher.bat', 'launcher.py']:
        path = os.path.join(SCRIPT_DIR, f)
        if os.path.exists(path):
            os.remove(path)
    print("\n[+] Uninstall complete!")
    return 0

# Mode definitions
MODES = [
    ('1', 'GUI', 'src/gui/main_gui.py', 'Graphical User Interface'),
    ('2', 'CLI', 'src/modes/headless_cli_mode.py', 'Headless CLI'),
    ('3', 'Web', 'src/web/web_dashboard.py', 'Web Dashboard'),
    ('4', 'API', 'src/api_server/rest_api.py', 'REST API Server'),
    ('5', 'Desktop', 'src/modes/desktop_gui_mode.py', 'Desktop GUI'),
    ('6', 'System', 'src/system/system_info.py', 'System Info'),
    ('7', 'Telemetry', 'src/telemetry/advanced_telemetry_features.py', 'Telemetry'),
    ('8', 'Ground', 'src/ground_station/ground_station.py', 'Ground Station'),
    ('9', 'AI', 'src/ai/ai_chat_assistant.py', 'AI Assistant'),
    ('10', 'Security', 'src/security/enhanced_security_module.py', 'Security'),
    ('11', 'Quantum', 'src/quantum/quantum_computing.py', 'Quantum'),
    ('12', 'Cosmic', 'src/cosmic/cosmic_ai.py', 'Cosmic AI'),
    ('13', 'Pipeline', 'src/pipeline/data_pipeline.py', 'Data Pipeline'),
    ('14', 'CanSat', 'src/modes/cansat_comms.py', 'CanSat Comms'),
]

def run_mode(choice):
    choice = str(choice).strip()
    name_to_num = {'gui': '1', 'cli': '2', 'web': '3', 'api': '4',
                   'desktop': '5', 'system': '6', 'telemetry': '7',
                   'ground': '8', 'ai': '9', 'security': '10',
                   'quantum': '11', 'cosmic': '12', 'pipeline': '13'}
    if choice.lower() in name_to_num:
        choice = name_to_num[choice.lower()]
    
    for num, name, path, desc in MODES:
        if num == choice:
            print(f"\nStarting {name}...\n")
            full_path = os.path.join(SCRIPT_DIR, path)
            if not os.path.exists(full_path):
                print(f"Module not found: {path}")
                return 1
            subprocess.run([sys.executable, full_path], cwd=SCRIPT_DIR)
            return 0
    print(f"Unknown mode: {choice}")
    return 1

def main():
    while True:
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
        choice = input("Choice: ").strip().lower()
        
        if choice in ['i', 'install']:
            do_install()
            input("\nPress Enter to continue...")
            continue
        if choice in ['u', 'uninstall']:
            do_uninstall()
            input("\nPress Enter to continue...")
            continue
        if choice in ['q', 'quit', 'exit', 'q']:
            print("Goodbye!")
            break
        
        name_to_num = {'gui': '1', 'cli': '2', 'web': '3', 'api': '4',
                       'desktop': '5', 'system': '6', 'telemetry': '7',
                       'ground': '8', 'ai': '9', 'security': '10',
                       'quantum': '11', 'cosmic': '12', 'pipeline': '13'}
        if choice in name_to_num:
            choice = name_to_num[choice]
        
        if choice.isdigit() and 1 <= int(choice) <= 13:
            run_mode(choice)
            input("\nPress Enter to return to menu...")
            continue
        
        print(f"Invalid: {choice}")
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg == 'install':
            do_install()
        elif arg == 'uninstall':
            do_uninstall()
        elif arg in ['1','2','3','4','5','6','7','8','9','10','11','12','13']:
            run_mode(arg)
        elif arg in ['gui','cli','web','api','desktop','system','telemetry','ground','ai','security','quantum','cosmic','pipeline']:
            run_mode(arg)
    else:
        main()