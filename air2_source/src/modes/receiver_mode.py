"""
Receiver Mode for AirOne v3.0
Implements the receiver operational mode
"""

import logging
import time
import threading
from typing import Dict, Any, Optional, List
from datetime import datetime
import numpy as np # Needed for mock data

# Import communication manager (assuming it's in communication/enhanced_communications.py)
try:
    from communication.enhanced_communications import CommunicationManager
    COMMUNICATION_MANAGER_AVAILABLE = True
except ImportError:
    COMMUNICATION_MANAGER_AVAILABLE = False
    # No print here, use logger later
    


class ReceiverMode:
    """Receiver operational mode"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.name = "CanSat Data Receiver Mode"
        self.description = "Real hardware interface for telemetry reception"
        self.logger = logging.getLogger(__name__)
        self.running = False
        self.config = config or {
            'port': 'COM1',  # Default serial port
            'baud_rate': 115200,
            'protocol': 'cansat_v2_enhanced'
        }
        self.comm_manager = None
        self.receive_thread = None
        self.latest_telemetry = {} # To store the latest received telemetry

        if not COMMUNICATION_MANAGER_AVAILABLE:
            self.logger.warning("CommunicationManager not found. ReceiverMode will operate in mock mode.")

    def start(self):
        """Start the receiver mode"""
        self.logger.info(f"Starting {self.name}...")
        self.logger.info(self.description)
        
        if not COMMUNICATION_MANAGER_AVAILABLE:
            self.logger.error("CommunicationManager is not available. Cannot start in real mode.")
            self.logger.info("Starting in mock receiver mode.")
            return self._start_mock_receiver()

        try:
            self.comm_manager = CommunicationManager(self.config)
            if not self.comm_manager.connect():
                self.logger.error("Failed to connect communication manager.")
                return False
            self.logger.info("Communication manager connected.")

            self.running = True
            self.receive_thread = threading.Thread(target=self._receive_data_loop, daemon=True)
            self.receive_thread.start()
            
            self.logger.info("Receiver mode started. Waiting for data...")
            return True
        except Exception as e:
            self.logger.error(f"Failed to start Receiver Mode: {e}")
            return False

    def stop(self):
        """Stop the receiver mode"""
        self.logger.info("Stopping Receiver Mode...")
        self.running = False
        
        if self.receive_thread and self.receive_thread.is_alive():
            self.logger.info("Joining receive data thread...")
            self.receive_thread.join(timeout=5)
            if self.receive_thread.is_alive():
                self.logger.warning("Receive data thread did not terminate in time.")
            else:
                self.logger.info("Receive data thread terminated.")
        
        if self.comm_manager:
            self.comm_manager.disconnect()
            self.logger.info("Communication manager disconnected.")
        
        self.logger.info("Receiver Mode stopped.")

    def _receive_data_loop(self):
        """Loop to continuously receive data from the communication manager."""
        while self.running:
            try:
                raw_data = self.comm_manager.receive_telemetry()
                if raw_data:
                    # Assuming raw_data is a dictionary, or can be parsed into one
                    # For now, just store and log.
                    self.latest_telemetry = raw_data
                    self.logger.debug(f"Received telemetry: {self.latest_telemetry.get('altitude', 'N/A')}m, {self.latest_telemetry.get('temperature', 'N/A')}C")
                else:
                    self.logger.debug("No data received, waiting...")
                time.sleep(0.1) # Small delay to prevent busy-waiting
            except Exception as e:
                self.logger.error(f"Error in receive data loop: {e}")
                time.sleep(1) # Wait longer on error

    def _start_mock_receiver(self):
        """Starts a mock receiver when CommunicationManager is not available."""
        self.logger.warning("Starting mock receiver mode. No actual hardware communication.")
        self.running = True
        self.receive_thread = threading.Thread(target=self._mock_receive_data_loop, daemon=True)
        self.receive_thread.start()
        self.logger.info("Mock Receiver mode started.")
        return True

    def _mock_receive_data_loop(self):
        """Mock loop to simulate receiving data."""
        packet_count = 0
        while self.running:
            packet_count += 1
            mock_telemetry = {
                'timestamp': datetime.now().isoformat(),
                'altitude': np.random.uniform(500, 1500),
                'velocity': np.random.uniform(10, 50),
                'temperature': np.random.uniform(20, 30),
                'pressure': np.random.uniform(950, 1050),
                'battery_level': np.random.uniform(80, 100),
                'packet_id': f"MOCK-{packet_count}"
            }
            self.latest_telemetry = mock_telemetry
            self.logger.debug(f"MOCK Telemetry: Altitude={mock_telemetry['altitude']:.2f}m")
            time.sleep(np.random.uniform(0.5, 1.5)) # Simulate variable receive rate
        self.logger.info("Mock receive data loop terminated.")

    def get_latest_telemetry(self) -> Dict[str, Any]:
        """Returns the latest received telemetry data."""
        return self.latest_telemetry.copy()
    
    def get_receiver_status(self) -> Dict[str, Any]:
        """Returns the current status of the receiver mode."""
        return {
            "mode_name": self.name,
            "description": self.description,
            "running": self.running,
            "comm_manager_connected": self.comm_manager is not None and self.comm_manager.is_connected(),
            "latest_telemetry_timestamp": self.latest_telemetry.get('timestamp'),
            "config": self.config
        }