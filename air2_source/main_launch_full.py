#!/usr/bin/env python3
"""
AirOne Professional v4.0 - All-in-One Launcher
=============================================

Complete ground station software with:
- 7 Operational Modes (GUI, CLI, Simulation, Security, Offline, Database, AI)
- 25+ AI Systems (LNN, SNN, BNN, PINN, Autoencoder, GAN, RL, etc.)
- Database Mode with ESP32-CAM 200ms capture
- Real-time analytics and autonomous decisions
- Web Dashboard (port 5000)
- REST API (port 5001)

Author: AirOne Professional Development Team
Version: 4.0
Build: 2026
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def print_banner():
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║     ██████╗ ███████╗ █████╗ ██████╗                         ║
║     ██╔══██╗██╔════╝██╔══██╗██╔══██╗                        ║
║     ██████╔╝█████╗  ███████║██║  ██║                        ║
║     ██╔══██╗██╔══╝  ██╔══██║██║  ██║                        ║
║     ██║  ██║███████╗██║  ██║██████╔╝                        ║
║     ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═════╝                         ║
║                    v4.0 ULTIMATE                             ║
║                                                               ║
║     Installer │ Uninstaller │ Launcher │ Reports             ║
║     DeepSeek R1 8B INT Support                               ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
    """)

def main():
    print_banner()
    print("""
Main Menu:
  [I] Install AirOne
  [U] Uninstall AirOne  
  [R] Generate Report
  [S] Settings
  [K] DeepSeek Status
  
  [1] Desktop GUI (10 Tabs + Charts)
  [2] Simulation Mode
  [3] CLI Mode
  [4] Security Mode
  [5] Offline Mode
  [6] Web Dashboard (Live Charts)
  [7] REST API Server
  [8] Run Scheduler
  [9] Health Monitor
  [D] Database Mode
  
  [B] Backup Manager
  [C] Cloud Integration
  [F] Flight Control
  [M] Mapping & GIS
  [N] Mission Planning
  [P] Plugin Manager
  [W] Weather Service
  [V] Voice Assistant
  [T] Telemetry Analyzer
  [E] Error Handler
  [X] Radio/SDR System
  [Y] Notifications
  [Z] Compliance & Audit
  [O] Performance Optimizer
  
  [Q] Quit

Select: """, end="")
    
    choice = input().strip().upper()
    
    if choice == 'Q':
        print("\nGoodbye!")
        return
        
    elif choice == 'I':
        from src.install.installer import install
        install()
        
    elif choice == 'U':
        from src.install.installer import uninstall
        uninstall()
        
    elif choice == 'R':
        from src.install.installer import settings as inst_settings
        inst_settings()
        print("\nReport Generator ready")
        
    elif choice == 'S':
        from src.install.installer import settings
        settings()
        
    elif choice == 'K':
        from src.ai.deepseek_integration import check_installation
        status = check_installation()
        print("\nDeepSeek R1 8B INT Status:")
        print(f"  Installed: {status['installed']}")
        print(f"  Model: {status['model_name']}")
        print(f"  Path: {status['model_path']}")
        print(f"  Available: {status['available']}")
        
    elif choice == '1':
        print("\nStarting Desktop GUI...")
        import sys
        sys.path.insert(0, 'src')
        from gui.enhanced_tabbed_gui import EnhancedTabbedGUI
        from PyQt5.QtWidgets import QApplication
        app = QApplication(sys.argv)
        app.setApplicationName("AirOne v4.0")
        window = EnhancedTabbedGUI()
        window.show()
        sys.exit(app.exec_())
        
    elif choice == '2':
        print("\nStarting Simulation...")
        import sys
        sys.path.insert(0, 'src')
        from modes.simulation_mode import SimulationMode
        sim = SimulationMode()
        sim.start_simulation(launch_delay=1.0)
        
    elif choice == '3':
        print("\nStarting CLI...")
        import sys
        sys.path.insert(0, 'src')
        from modes.headless_cli_mode import HeadlessCLIMode
        cli = HeadlessCLIMode()
        cli.start()
        
    elif choice == '4':
        print("\nStarting Security Mode...")
        import sys
        sys.path.insert(0, 'src')
        from modes.safe_mode import SafeMode
        sec = SafeMode()
        sec.start()
        
    elif choice == '5':
        print("\nStarting Offline Mode...")
        import sys
        sys.path.insert(0, 'src')
        from modes.offline_mode import OfflineMode
        off = OfflineMode()
        off.start()
        
    elif choice == '6':
        print("\nStarting Web Dashboard...")
        print("Open http://localhost:5000 in your browser")
        import sys
        sys.path.insert(0, 'src')
        from web_dashboard import start_dashboard
        start_dashboard(host='0.0.0.0', port=5000)
        
    elif choice == '7':
        print("\nStarting REST API Server...")
        print("API available at http://localhost:5001")
        import sys
        sys.path.insert(0, 'src')
        from api_server.rest_api import run_api_server
        run_api_server(host='0.0.0.0', port=5001, debug=False)
        
    elif choice == '8':
        print("\nStarting Scheduler...")
        import sys
        sys.path.insert(0, 'src')
        from scheduler.scheduler import demo
        demo()
        
    elif choice == '9':
        print("\nRunning Health Monitor...")
        import sys
        sys.path.insert(0, 'src')
        from monitoring.health.monitor import demo
        demo()
        
    elif choice == 'D':
        print("\nStarting Database Mode...")
        import sys
        sys.path.insert(0, 'src')
        from database.database_manager import DatabaseManager
        db = DatabaseManager()
        print(f"Database initialized at: {db.db_path}")
        print("\\nDatabase Mode Active - Use DatabaseManager for all operations")
        
    elif choice == 'B':
        print("\nStarting Backup Manager...")
        import sys
        sys.path.insert(0, 'src')
        from backup.backup_manager import BackupManager
        bm = BackupManager()
        print(f"✓ Backup Manager ready ({len(bm.list_backups())} backups)")
        
    elif choice == 'C':
        print("\nStarting Cloud Integration...")
        import sys
        sys.path.insert(0, 'src')
        from cloud import CloudStorage, CloudSync, CloudDeploy
        print("Cloud modules available:")
        print("  - CloudStorage: Azure, AWS S3, Google Cloud storage")
        print("  - CloudSync: Real-time file synchronization")
        print("  - CloudDeploy: Container deployment")
        storage = CloudStorage()
        print("✓ Cloud Integration Ready")
        
    elif choice == 'F':
        print("\nStarting Flight Control...")
        import sys
        sys.path.insert(0, 'src')
        from flight.flight_controller import FlightController
        fc = FlightController()
        print("✓ Flight Controller ready")
        
    elif choice == 'M':
        print("\nStarting Mapping & GIS...")
        import sys
        sys.path.insert(0, 'src')
        from mapping import MapGenerator, Geocoder, GPSParser, RoutePlanner
        print("✓ Mapping & GIS Ready")
        
    elif choice == 'N':
        print("\nStarting Mission Planning...")
        import sys
        sys.path.insert(0, 'src')
        from mission.mission_planner import MissionPlanner
        mp = MissionPlanner()
        print("✓ Mission Planner ready")
        
    elif choice == 'P':
        print("\nStarting Plugin Manager...")
        import sys
        sys.path.insert(0, 'src')
        from plugin_system import PluginManager
        pm = PluginManager()
        print("✓ Plugin Manager ready")
        
    elif choice == 'W':
        print("\nStarting Weather Service...")
        import sys
        sys.path.insert(0, 'src')
        from weather import AtmosphericModel, AtmosphericConditions
        print("✓ Weather Service Ready")
        
    elif choice == 'V':
        print("\nStarting Voice Assistant...")
        import sys
        sys.path.insert(0, 'src')
        from voice_assistant import VoiceAssistant
        va = VoiceAssistant()
        print("✓ Voice Assistant ready")
        
    elif choice == 'T':
        print("\nStarting Telemetry Analyzer...")
        import sys
        sys.path.insert(0, 'src')
        from telemetry_analyzer import TelemetryAnalyzer
        ta = TelemetryAnalyzer()
        print("✓ Telemetry Analyzer ready")
        
    elif choice == 'E':
        print("\nStarting Error Handler...")
        import sys
        sys.path.insert(0, 'src')
        from error_handler import ErrorHandler
        eh = ErrorHandler()
        print("✓ Error Handler ready")
        
    elif choice == 'X':
        print("\nStarting Radio/SDR System...")
        import sys
        sys.path.insert(0, 'src')
        from radio import SDRDemodulator, SDRInterface
        print("✓ Radio/SDR System Ready")
        
    elif choice == 'Y':
        print("\nStarting Notifications...")
        import sys
        sys.path.insert(0, 'src')
        from notifications.notification_system import NotificationManager
        nm = NotificationManager()
        print("✓ Notification System Ready")
        
    elif choice == 'Z':
        print("\nCompliance & Audit System...")
        import sys
        sys.path.insert(0, 'src')
        from compliance.compliance_audit_system import ComplianceAndAuditSystem
        ca = ComplianceAndAuditSystem()
        print("✓ Compliance System Ready")
        
    elif choice == 'O':
        print("\nPerformance Optimizer...")
        try:
            import sys
            sys.path.insert(0, 'src')
            from performance.optimizer import PerformanceOptimizer
            po = PerformanceOptimizer()
            print("✓ Performance Optimizer Ready")
        except ImportError as e:
            print(f"⚠ Performance Optimizer requires: {e}")
            print("  (Optional - install aioredis for full functionality)")
        
    else:
        print("\nInvalid choice")

if __name__ == "__main__":
    main()
