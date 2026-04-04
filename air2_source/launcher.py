#!/usr/bin/env python3
"""
AirOne Professional v4.0 - Python Launcher
Menu-driven interface to launch all AirOne modes
"""
import os
import sys
import subprocess

# Colors
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
CYAN = '\033[96m'
BOLD = '\033[1m'
END = '\033[0m'

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

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

def print_banner():
    """Print the launcher banner"""
    print(f"""
{CYAN}{BOLD}
╔═══════════════════════════════════════════════════════════════════════════╗
║                   AirOne Professional v4.0                               ║
║                         LAUNCHER                                         ║
╚═══════════════════════════════════════════════════════════════════════════╝
{END}
   {YELLOW}Ground Station GUI - Login Required{END}
            Ground Station | AI | Security | Quantum | Cosmic | Pipeline
""")

def print_menu():
    """Print the mode selection menu"""
    print(f"""
{GREEN}================================================================================{END}
    [I] Install    [U] Uninstall    [Q] Quit
{GREEN}================================================================================{END}
 [1] GUI    [2] CLI    [3] Web    [4] API    [5] Desktop
 [6] System [7] Telemetry [8] Ground [9] AI    [10] Security
 [11] Quantum [12] Cosmic [13] Pipeline [14] CanSat
{GREEN}================================================================================{END}
""")

def run_mode(choice):
    """Run the selected mode"""
    choice = str(choice).strip()
    name_to_num = {
        'gui': '1', 'cli': '2', 'web': '3', 'api': '4',
        'desktop': '5', 'system': '6', 'telemetry': '7',
        'ground': '8', 'ai': '9', 'security': '10',
        'quantum': '11', 'cosmic': '12', 'pipeline': '13', 'cansat': '14'
    }
    
    if choice.lower() in name_to_num:
        choice = name_to_num[choice.lower()]
    
    for num, name, path, desc in MODES:
        if num == choice:
            print(f"\n{GREEN}▶ Starting {name}...{END}\n")
            full_path = os.path.join(SCRIPT_DIR, path)
            
            if not os.path.exists(full_path):
                print(f"{RED}✗ Module not found: {path}{END}")
                return False
            
            try:
                subprocess.run([sys.executable, full_path], cwd=SCRIPT_DIR)
                return True
            except KeyboardInterrupt:
                print(f"\n{YELLOW}▸ Interrupted{END}")
                return True
            except Exception as e:
                print(f"{RED}✗ Error: {e}{END}")
                return False
    
    print(f"{RED}✗ Unknown mode: {choice}{END}")
    return False

def do_install():
    """Run the installer"""
    print(f"\n{BLUE}▶ Running installer...{END}\n")
    install_path = os.path.join(SCRIPT_DIR, 'install.py')
    
    if os.path.exists(install_path):
        try:
            subprocess.run([sys.executable, install_path], cwd=SCRIPT_DIR)
        except KeyboardInterrupt:
            print(f"\n{YELLOW}▸ Installation interrupted{END}")
    else:
        print(f"{RED}✗ install.py not found{END}")
    
    input(f"\n{YELLOW}Press Enter to continue...{END}")

def do_uninstall():
    """Run uninstaller"""
    print(f"\n{YELLOW}▸ Uninstall not fully implemented{END}")
    print(f"  To uninstall, simply remove the air2_source directory")
    input(f"\n{YELLOW}Press Enter to continue...{END}")

def main():
    """Main launcher loop"""
    # Create required directories
    for dirname in ['logs', 'reports', 'data', 'config', 'models']:
        path = os.path.join(SCRIPT_DIR, dirname)
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
    
    while True:
        print_banner()
        print_menu()
        
        choice = input(f"{CYAN}Choice:{END} ").strip().lower()
        
        if choice in ['i', 'install']:
            do_install()
            continue
        
        if choice in ['u', 'uninstall']:
            do_uninstall()
            continue
        
        if choice in ['q', 'quit', 'exit']:
            print(f"\n{GREEN}Goodbye! 👋{END}\n")
            break
        
        # Handle name-based input
        name_to_num = {
            'gui': '1', 'cli': '2', 'web': '3', 'api': '4',
            'desktop': '5', 'system': '6', 'telemetry': '7',
            'ground': '8', 'ai': '9', 'security': '10',
            'quantum': '11', 'cosmic': '12', 'pipeline': '13', 'cansat': '14'
        }
        
        if choice in name_to_num:
            choice = name_to_num[choice]
        
        if choice.isdigit() and 1 <= int(choice) <= 14:
            run_mode(choice)
            input(f"\n{YELLOW}Press Enter to return to menu...{END}")
        else:
            print(f"{RED}Invalid choice: {choice}{END}")
            input(f"\n{YELLOW}Press Enter to continue...{END}")

if __name__ == "__main__":
    main()