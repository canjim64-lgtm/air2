#!/usr/bin/env python3
"""
AirOne Professional v4.0 - Main Entry Point
"""

import sys
import os

# Get base directory (parent of air2_source)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR.endswith('air2_source'):
    BASE_DIR = os.path.dirname(SCRIPT_DIR)
else:
    BASE_DIR = SCRIPT_DIR

def run_mode(choice):
    """Run selected mode"""
    
    src_dir = os.path.join(BASE_DIR, 'air2_source', 'src')
    
    desc_map = {
        '1': ('GUI', 'gui/main_gui.py'),
        '2': ('CLI', 'cli/cli_dashboard.py'),
        '3': ('Web', 'web/web_dashboard.py'),
        '4': ('API', 'api/api_server.py'),
        '5': ('Desktop', 'desktop_gui/main.py'),
        '6': ('System', 'system/system_info.py'),
        '7': ('Telemetry', 'telemetry/telemetry_dashboard.py'),
        '8': ('Ground Station', 'communications/ground_station.py'),
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
    print(f"File: {full_path}")
    
    if os.path.exists(full_path):
        sys.path.insert(0, os.path.dirname(full_path))
        try:
            with open(full_path) as f:
                code = compile(f.read(), full_path, 'exec')
            exec(code, {'__name__': '__main__', '__file__': full_path})
        except Exception as e:
            print(f"Error: {type(e).__name__}: {e}")
    else:
        print("Module not found at expected path")
    
    return 0

def main():
    if len(sys.argv) < 2:
        print("""
================================================================================
                    AirOne Professional v4.0
                    = ULTIMATE UNIFIED EDITION =
================================================================================
    13 Modes: GUI | CLI | Web | API | Desktop | System | Telemetry
             Ground Station | AI | Security | Quantum | Cosmic | Pipeline
================================================================================
 [1] GUI    [2] CLI    [3] Web    [4] API    [5] Desktop
 [6] System [7] Telemetry [8] Ground [9] AI    [10] Security
 [11] Quantum [12] Cosmic [13] Pipeline

Install: pip install numpy psutil requests torch flask
Choice: """, end="")
        choice = input().strip()
    else:
        choice = sys.argv[1]
    
    return run_mode(choice)

if __name__ == "__main__":
    sys.exit(main())