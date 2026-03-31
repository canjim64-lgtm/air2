"""
Safe Mode for AirOne v3.0
Implements the safe operational mode
"""

import logging
import time
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
import json
import os # For simulating file operations
import platform # To check OS

# Import external system components for diagnostics (if available)
try:
    from system.diagnostics_service import DiagnosticsService
    DIAGNOSTICS_SERVICE_AVAILABLE = True
except ImportError:
    DIAGNOSTICS_SERVICE_AVAILABLE = False
    # print("Warning: DiagnosticsService not found. SafeMode diagnostics will be simulated.")


class SafeMode:
    """Safe operational mode"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.name = "Secure SAFE Mode"
        self.description = "Minimal functionality for emergency recovery"
        self.logger = logging.getLogger(__name__)
        self.running = False
        self.config = config or {}
        self.diagnostics_service = DiagnosticsService() if DIAGNOSTICS_SERVICE_AVAILABLE else None

        if not DIAGNOSTICS_SERVICE_AVAILABLE:
            self.logger.warning("DiagnosticsService not found. SafeMode diagnostics will be simulated.")

    def start(self):
        """Start the safe mode"""
        self.logger.info(f"Starting {self.name}...")
        self.logger.info(self.description)
        
        self.running = True
        self.logger.info("Running in secure safe mode. Minimal functionality enabled.")
        
        self._display_safe_mode_menu()
        
        return True

    def stop(self):
        """Stop the safe mode"""
        self.logger.info("Stopping Secure SAFE Mode...")
        self.running = False
        self.logger.info("Safe Mode stopped.")

    def _display_safe_mode_menu(self):
        """Displays the interactive menu for safe mode operations."""
        print("\n" + "="*40)
        print("    --- SECURE SAFE MODE ---")
        print("="*40)
        print("1. Run system diagnostics")
        print("2. Check system logs")
        print("3. Reset configuration (simulated)")
        print("4. Verify file integrity (simulated)")
        print("5. Exit SAFE mode")
        print("="*40)

        while self.running:
            try:
                choice = input("Select an option (1-5): ").strip()
                
                if choice == '1':
                    self._run_diagnostics()
                elif choice == '2':
                    self._check_logs()
                elif choice == '3':
                    self._reset_config()
                elif choice == '4':
                    self._verify_integrity()
                elif choice == '5':
                    self.logger.info("Exiting SAFE mode per user request.")
                    self.stop()
                else:
                    print("Invalid option. Please enter a number between 1 and 5.")
                
                if self.running: # Only redisplay if still running
                    print("\n" + "="*40)
                    print("    --- SECURE SAFE MODE ---")
                    print("="*40)
                    print("1. Run system diagnostics")
                    print("2. Check system logs")
                    print("3. Reset configuration (simulated)")
                    print("4. Verify file integrity (simulated)")
                    print("5. Exit SAFE mode")
                    print("="*40)

            except KeyboardInterrupt:
                self.logger.info("Keyboard interrupt received. Exiting SAFE mode.")
                self.stop()
            except Exception as e:
                self.logger.error(f"Error in SAFE mode menu: {e}")
                print(f"An error occurred: {e}")

    def _run_diagnostics(self):
        """Runs system diagnostics, leveraging DiagnosticsService if available."""
        self.logger.info("Running system diagnostics...")
        if self.diagnostics_service:
            report = self.diagnostics_service.run_full_diagnostics()
            print("\n--- Diagnostic Report ---")
            for key, value in report.items():
                print(f"  {key}: {value}")
            print("-------------------------\n")
        else:
            print("\n--- Simulated Diagnostic Report ---")
            print(f"  OS: {platform.system()} {platform.release()}")
            print(f"  Python Version: {sys.version.split(' ')[0]}")
            print("  CPU Usage: 10% (Normal)")
            print("  Memory Usage: 20% (Normal)")
            print("  Disk Health: OK")
            print("  Network Connectivity: Limited (SAFE Mode)")
            print("  Critical Services: Running")
            print("-----------------------------------\n")

    def _check_logs(self):
        """Checks system logs, simulating log access."""
        self.logger.info("Checking system logs...")
        log_dir = Path("./logs") # Assuming logs directory at project root
        if log_dir.exists():
            log_files = list(log_dir.glob("*.log"))
            if log_files:
                print("\n--- Recent Log Entries (Simulated) ---")
                # Simulate reading a few lines from the latest log file
                latest_log = max(log_files, key=os.path.getmtime)
                with open(latest_log, 'r') as f:
                    lines = f.readlines()
                    for line in lines[-5:]: # Show last 5 lines
                        print(f"  {line.strip()}")
                print("--------------------------------------\n")
            else:
                print("No log files found in ./logs directory.")
        else:
            print("Log directory (./logs) not found. Cannot check logs.")

    def _reset_config(self):
        """Simulates resetting configuration to default settings."""
        self.logger.warning("Simulating configuration reset...")
        confirm = input("Are you sure you want to reset configuration? Type 'yes' to confirm: ").strip().lower()
        if confirm == 'yes':
            print("Configuration reset initiated (simulated).")
            # In a real system, this would call a ConfigManager.reset_to_defaults()
            time.sleep(1)
            print("Configuration reset complete (simulated).")
            self.logger.info("Configuration reset simulated successfully.")
        else:
            print("Configuration reset cancelled.")
            self.logger.info("Configuration reset cancelled by user.")

    def _verify_integrity(self):
        """Simulates verifying core system file integrity."""
        self.logger.info("Simulating file integrity verification...")
        print("Verifying core system files...")
        # Simulate checks
        time.sleep(1)
        print("Critical files: OK")
        print("Checksums: Matching")
        print("No tampering detected (simulated).")
        self.logger.info("File integrity verification simulated successfully.")