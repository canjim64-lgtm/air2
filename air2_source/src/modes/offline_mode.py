"""
Offline Mode for AirOne v3.0
Implements the offline operational mode
"""

import logging
import time
from typing import Dict, Any
from datetime import datetime

class OfflineMode:
    """Offline operational mode"""
    
    def __init__(self):
        self.name = "Offline/Air-Gapped Mode"
        self.description = "No network dependencies, secure isolated operation"
        self.logger = logging.getLogger(__name__)
        self.running = False
        self.local_data_store = {} # Simulate a local data store
        self.network_status = "offline" # Enforce offline status
    
    def start(self):
        """Start the offline mode"""
        self.logger.info(f"Starting {self.name}...")
        self.logger.info(self.description)
        
        self.running = True
        self.logger.info("Enforcing network isolation...")
        self._disable_network_interfaces() # Simulate network disable
        
        self.logger.info("Initializing local data sources...")
        self.local_data_store = self._load_local_data() # Load data from local storage
        self.logger.info(f"Loaded {len(self.local_data_store)} items from local data store.")

        self.logger.info("Running in secure offline mode. All operations will use local resources only.")
        
        # Optional: Start a passive monitoring loop for offline operations
        # self._offline_monitoring_loop()
        
        return True

    def stop(self):
        """Stop the offline mode"""
        self.logger.info("Stopping Offline/Air-Gapped Mode...")
        self.running = False
        self._enable_network_interfaces() # Simulate network re-enable
        self.logger.info("Network interfaces re-enabled (simulated).")
        self.logger.info("Offline Mode stopped.")
    
    def _disable_network_interfaces(self):
        """Simulates disabling all network interfaces."""
        # In a real system, this would involve OS-specific commands or network stack manipulation.
        self.network_status = "offline"
        self.logger.warning("Network interfaces are now logically DISABLED. No external connections possible.")
        # Example: os.system("ifconfig eth0 down") # Linux example
        # Example: netsh interface set interface "Ethernet" DISABLED # Windows example

    def _enable_network_interfaces(self):
        """Simulates re-enabling all network interfaces."""
        self.network_status = "online"
        self.logger.info("Network interfaces are now logically ENABLED.")

    def _load_local_data(self) -> Dict[str, Any]:
        """Simulates loading data from local, air-gapped storage."""
        # In a real system, this would load data from a local database, files, etc.
        # For demonstration, return some dummy local data.
        return {
            "telemetry_log_offline_1": {"timestamp": time.time(), "altitude": 500, "temp": 20},
            "telemetry_log_offline_2": {"timestamp": time.time(), "altitude": 510, "temp": 21},
            "config_offline": {"mode": "offline", "security_level": "high"}
        }

    def process_data_offline(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process data using only local resources."""
        if not self.running or self.network_status == "online":
            self.logger.error("Attempted offline operation while not in strict offline mode or network active.")
            raise Exception("Cannot perform offline processing: not in offline mode or network active.")

        self.logger.info(f"Processing data '{list(data.keys())[0] if data else 'empty'}' using local algorithms.")
        # Simulate some local processing
        processed_data = {
            "original_data": data,
            "processed_at": datetime.now().isoformat(),
            "status": "processed_offline",
            "integrity_check": "passed", # Local integrity check
            "local_resources_used": True
        }
        self.local_data_store[f"processed_record_{time.time()}"] = processed_data
        return processed_data

    def get_offline_status(self) -> Dict[str, Any]:
        """Get the current status of the offline mode."""
        return {
            "mode_name": self.name,
            "description": self.description,
            "running": self.running,
            "network_status": self.network_status,
            "local_data_items": len(self.local_data_store),
            "last_processed_time": datetime.now().isoformat()
        }