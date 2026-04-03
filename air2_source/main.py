#!/usr/bin/env python3
"""
AirOne Professional v4.0 - Main Entry Point
Single launcher for all operations
"""

import sys
import os
import subprocess

# Get the directory where main.py is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, 'src')

def run_mode(choice):
    """Run selected mode"""
    
    scripts = {
        '1': ('gui', 'GUI Mode'),
        '2': ('cli', 'CLI Mode'),
        '3': ('web_dashboard', 'Web Dashboard'),
        '4': ('api_server', 'API Server'),
        '5': ('desktop_gui', 'Desktop GUI'),
        '6': ('system_info', 'System Check'),
        '7': ('telemetry_dashboard', 'Telemetry'),
        '8': ('ground_station', 'Ground Station'),
        '9': ('ai_assistant', 'AI Assistant'),
        '10': ('security', 'Security'),
        '11': ('quantum', 'Quantum'),
        '12': ('cosmic', 'Cosmic'),
        '13': ('pipeline', 'Pipeline'),
    }
    
    if choice not in scripts:
        print("Invalid choice")
        return 1
    
    module, desc = scripts[choice]
    print(f"\nStarting {desc}...")
    
    # Try to run as module
    try:
        # Import from src directory
        sys.path.insert(0, SRC_DIR)
        
        if choice == '1':
            from gui import gui_mode
            gui_mode.main()
        elif choice == '2':
            from cli import cli_mode
            cli_mode.main()
        elif choice == '3':
            from web import web_dashboard
            web_dashboard.main()
        elif choice == '4':
            from api import api_server
            api_server.main()
        elif choice == '5':
            from desktop_gui import desktop_gui_mode
            desktop_gui_mode.main()
        elif choice == '6':
            from system import system_info
            system_info.main()
        elif choice == '7':
            from telemetry import telemetry_dashboard
            telemetry_dashboard.main()
        elif choice == '8':
            from communications import ground_station
            ground_station.main()
        elif choice == '9':
            from ai import ai_assistant
            ai_assistant.main()
        elif choice == '10':
            from security import security_manager
            security_manager.main()
        elif choice == '11':
            from quantum import quantum_computing
            quantum_computing.main()
        elif choice == '12':
            from cosmic import cosmic_ai
            cosmic_ai.main()
        elif choice == '13':
            from pipeline import data_pipeline
            data_pipeline.main()
            
    except ImportError as e:
        print(f"Module not available: {e}")
        print("Run: Installer.bat to install required packages")
    except Exception as e:
        print(f"Error: {e}")
    
    return 0

def main():
    if len(sys.argv) < 2:
        print("""
================================================================================
            AirOne Professional v4.0 - ULTIMATE UNIFIED EDITION
                Complete Integration of ALL Features
================================================================================

    13 Operational Modes | DeepSeek R1 8B AI | Quantum Computing
    Cosmic & Multiverse Computing | Advanced Pipelines | Full Security

Select Mode:
  [1] GUI Mode          - Graphical User Interface
  [2] CLI Mode          - Command Line Interface
  [3] Web Dashboard     - Browser-based Dashboard
  [4] API Server       - REST API Server
  [5] Desktop GUI      - PyQt Desktop Interface
  [6] System Check    - Diagnostics & Health
  [7] Telemetry       - Telemetry Dashboard
  [8] Ground Station  - Ground Station Control
  [9] AI Assistant    - DeepSeek R1 8B AI
  [10] Security      - Security Management
  [11] Quantum       - Quantum Computing
  [12] Cosmic        - Cosmic AI Fusion
  [13] Pipeline      - Data Pipeline

Choice: """, end="")
        choice = input().strip()
    else:
        choice = sys.argv[1]
    
    return run_mode(choice)

if __name__ == "__main__":
    sys.exit(main())