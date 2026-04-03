#!/usr/bin/env python3
"""
AirOne Professional v4.0 - Main Entry Point
"""

import sys, os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def run_mode(choice):
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
    if len(sys.argv) < 2:
        print("""
================================================================================
                    AirOne Professional v4.0
================================================================================
    13 Modes: GUI | CLI | Web | API | Desktop | System | Telemetry
             Ground Station | AI | Security | Quantum | Cosmic | Pipeline
================================================================================
 [1] GUI    [2] CLI    [3] Web    [4] API    [5] Desktop
 [6] System [7] Telemetry [8] Ground [9] AI    [10] Security
 [11] Quantum [12] Cosmic [13] Pipeline

Install: pip install numpy psutil requests flask torch pyjwt cryptography
Choice: """, end="")
        choice = input().strip()
    else:
        choice = sys.argv[1]
    
    return run_mode(choice)

if __name__ == "__main__":
    sys.exit(main())