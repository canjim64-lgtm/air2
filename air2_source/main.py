#!/usr/bin/env python3
"""
AirOne Professional v4.0 - Main Entry Point
Single launcher for all operations
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

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
  [9] AI Assistant   - DeepSeek R1 8B AI
  [10] Security     - Security Management
  [11] Quantum     - Quantum Computing
  [12] Cosmic      - Cosmic AI Fusion
  [13] Pipeline   - Data Pipeline
  [14] Uninstall  - Uninstall AirOne

Choice: """, end="")
        choice = input().strip()
    else:
        choice = sys.argv[1]

    modes = {
        '1': ('gui_mode', 'GUI Mode'),
        '2': ('cli_mode', 'CLI Mode'),
        '3': ('web_dashboard_mode', 'Web Dashboard'),
        '4': ('api_server_mode', 'API Server'),
        '5': ('desktop_gui_mode', 'Desktop GUI'),
        '6': ('system_check_mode', 'System Check'),
        '7': ('telemetry_dashboard_mode', 'Telemetry'),
        '8': ('ground_station_mode', 'Ground Station'),
        '9': ('ai_assistant_mode', 'AI Assistant'),
        '10': ('security_mode', 'Security'),
        '11': ('quantum_mode', 'Quantum'),
        '12': ('cosmic_mode', 'Cosmic'),
        '13': ('pipeline_mode', 'Pipeline'),
        '14': ('uninstall', 'Uninstall'),
    }

    if choice not in modes:
        print("Invalid choice")
        return 1

    mode_name, mode_desc = modes[choice]

    if mode_name == 'uninstall':
        os.system('Uninstaller.bat')
        return 0

    print(f"\nStarting {mode_desc}...")

    # Import and run the mode
    try:
        if choice == '1':
            from modes import gui_mode
            gui_mode.main()
        elif choice == '2':
            from modes import cli_mode
            cli_mode.main()
        elif choice == '3':
            from web import web_dashboard
            web_dashboard.main()
        elif choice == '4':
            from web import api_server
            api_server.main()
        elif choice == '5':
            from desktop import desktop_gui
            desktop_gui.main()
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
    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())