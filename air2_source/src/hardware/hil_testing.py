"""
Hardware in the Loop (HIL) Testing for AirOne Professional v4.0
Active fault injection system that modifies system states for stress testing.
"""
import logging
import time
import threading
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class HILTestingEngine:
    def __init__(self, feature_manager: Optional[Any] = None):
        self.logger = logging.getLogger(f"{__name__}.HILTestingEngine")
        self.feature_manager = feature_manager
        self.active_faults = []
        self.is_running = False
        self.test_scenarios = {
            "sensor_critical_failure": self._fault_sensor_critical,
            "thermal_overload": self._fault_thermal_overload,
            "link_saturation": self._fault_link_saturation,
            "swarm_desync": self._fault_swarm_desync
        }
        self.logger.info("Integrated HIL Fault Injection Engine Initialized.")

    def run_scenario(self, name: str, duration: int = 15):
        if name not in self.test_scenarios:
            self.logger.error(f"Invalid HIL scenario: {name}")
            return False
            
        self.is_running = True
        self.logger.info(f"Injecting Fault Sequence: {name} ({duration}s)")
        
        t = threading.Thread(target=self._executor, args=(name, duration))
        t.daemon = True
        t.start()
        return True

    def _executor(self, name: str, duration: int):
        fault_func = self.test_scenarios[name]
        start = time.time()
        while self.is_running and (time.time() - start < duration):
            fault_func()
            time.sleep(1)
        self.logger.info(f"Fault Sequence {name} CLEARED.")
        self.is_running = False

    def _fault_sensor_critical(self):
        """Actively corrupts the TelemetryProcessor buffer."""
        if self.feature_manager:
            tp = self.feature_manager.get_feature('telemetry_processor')
            if tp:
                # Direct manipulation: corrupt the last sequence to force 'lost packet' logic
                tp.last_sequence = (tp.last_sequence - 10) % 65536
                self.logger.warning("HIL: Sequence Gap Injected into Telemetry Processor.")

    def _fault_thermal_overload(self):
        """Forces the thermal system into a throttled state."""
        if self.feature_manager:
            tm = self.feature_manager.get_feature('thermal_management')
            if tm:
                # Trigger throttling logic by spoofing high temp sensor input
                tm.update_sensors(cpu_temp=95.0, battery_temp=50.0, ambient_temp=30.0)
                self.logger.warning("HIL: Thermal Overload Spoofed.")

    def _fault_link_saturation(self):
        """Forces the link analyzer into a critical risk state."""
        if self.feature_manager:
            la = self.feature_manager.get_feature('predictive_link')
            if la:
                la.update(altitude=100, distance_from_station=10000, rssi=-114.0)
                self.logger.warning("HIL: Link Saturation/Fade Injected.")

    def _fault_swarm_desync(self):
        """Injects a collision threat into the swarm coordinator."""
        if self.feature_manager:
            sc = self.feature_manager.get_feature('swarm_coordinator')
            if sc:
                # Inject a static ghost node within the safety radius
                sc.update_telemetry("GHOST_TARGET", 1.0, 1.0, 100.0)
                self.logger.warning("HIL: Swarm Ghost Collision Injected.")
