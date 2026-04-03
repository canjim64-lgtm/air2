#!/usr/bin/env python3
"""
AirOne Professional v4.0 - Main Entry Point
Single launcher for all operations
"""

import sys
import os
import importlib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, 'src')

def get_mode_module(choice):
    """Get mode module and main function"""
    
    modes = {
        '1': ('gui', 'gui_mode'),
        '2': ('cli', 'cli_mode'),
        '3': ('web', 'web_dashboard'),
        '4': ('api', 'api_server'),
        '5': ('desktop_gui', 'desktop_gui_mode'),
        '6': ('system', 'system_info'),
        '7': ('telemetry', 'telemetry_dashboard'),
        '8': ('communications', 'ground_station'),
        '9': ('ai', 'ai_assistant'),
        '10': ('security', None),  # Special case - handled below
        '11': ('quantum', 'quantum_computing'),
        '12': ('cosmic', 'cosmic_ai'),
        '13': ('pipeline', 'data_pipeline'),
    }
    
    if choice not in modes:
        return None, None, None
    
    pkg, mod_name = modes[choice]
    desc = {
        '1': 'GUI Mode', '2': 'CLI Mode', '3': 'Web Dashboard', '4': 'API Server',
        '5': 'Desktop GUI', '6': 'System Check', '7': 'Telemetry', '8': 'Ground Station',
        '9': 'AI Assistant', '10': 'Security', '11': 'Quantum', '12': 'Cosmic', '13': 'Pipeline'
    }.get(choice, 'Unknown')
    
    return pkg, mod_name, desc

def run_mode(choice):
    """Run selected mode"""
    
    pkg, mod_name, desc = get_mode_module(choice)
    if not pkg:
        print("Invalid choice")
        return 1
    
    print(f"\nStarting {desc}...")
    
    try:
        sys.path.insert(0, SRC_DIR)
        
        # Special case for security
        if choice == '10':
            from security import main as security_main
            security_main.main()
            return 0
        
        # Try to import module
        try:
            if mod_name:
                mod = importlib.import_module(pkg)
                if hasattr(mod, 'main'):
                    mod.main()
                    return 0
        except ImportError:
            pass
        
        # Try src.package.module pattern
        try:
            mod = importlib.import_module(f"{pkg}.{mod_name}")
            if hasattr(mod, 'main'):
                mod.main()
                return 0
        except ImportError:
            pass
        
        print(f"Module not available. Run: Installer.bat")
        
    except Exception as e:
        print(f"Error: {e}")
    
    return 1

def main():
    if len(sys.argv) < 2:
        print("""
================================================================================
            AirOne Professional v4.0 - ULTIMATE UNIFIED EDITION
                Complete Integration of ALL Features
================================================================================
    13 Operational Modes | DeepSeek R1 8B AI | Quantum Computing
    Cosmic & Multiverse Computing | Advanced Pipelines | Full Security
================================================================================
Select Mode:
  [1] GUI Mode         [2] CLI Mode        [3] Web Dashboard
  [4] API Server      [5] Desktop GUI     [6] System Check
  [7] Telemetry      [8] Ground Station [9] AI Assistant
  [10] Security      [11] Quantum       [12] Cosmic
  [13] Pipeline
Choice: """, end="")
        choice = input().strip()
    else:
        choice = sys.argv[1]
    
    return run_mode(choice)

if __name__ == "__main__":
    sys.exit(main())