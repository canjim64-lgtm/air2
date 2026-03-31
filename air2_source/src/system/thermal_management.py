"""
Advanced Thermal Management System (ATMS) for AirOne Professional v4.0
Monitors heat dissipation and triggers hardware-level performance throttling.
"""
import logging
import time
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ThermalManagementSystem:
    def __init__(self, feature_manager: Optional[Any] = None, critical_temp: float = 85.0):
        self.logger = logging.getLogger(f"{__name__}.ThermalManagementSystem")
        self.feature_manager = feature_manager
        self.critical_temp = critical_temp
        self.throttled = False
        self.cooling_active = False
        self.logger.info(f"Thermal Management Initialized. Limit: {critical_temp}C.")

    def update_sensors(self, cpu_temp: float, battery_temp: float, ambient_temp: float) -> Dict[str, Any]:
        current_max = max(cpu_temp, battery_temp)
        
        # Cooling Control (e.g. GPIO fan)
        if current_max >= (self.critical_temp - 15):
            self.cooling_active = True
        elif current_max < (self.critical_temp - 25):
            self.cooling_active = False
            
        # Throttling Logic
        if current_max >= (self.critical_temp - 5):
            if not self.throttled:
                self._apply_throttling(True)
        elif current_max < (self.critical_temp - 15):
            if self.throttled:
                self._apply_throttling(False)

        # Emergency Shutdown Trigger
        if current_max >= self.critical_temp:
            self.logger.critical(f"OVERHEATING ({current_max}C): Emergency system shutdown imminent.")

        return {
            "status": "CRITICAL" if self.throttled else "WARNING" if self.cooling_active else "NOMINAL",
            "max_temp_c": round(current_max, 2),
            "throttled": self.throttled,
            "cooling_active": self.cooling_active
        }

    def _apply_throttling(self, enable: bool):
        """Reduces the duty cycle or sampling rate of other modules to save power/heat."""
        self.throttled = enable
        state = "ENABLED" if enable else "DISABLED"
        self.logger.warning(f"THERMAL THROTTLING {state} - Reducing system load.")
        
        if self.feature_manager:
            # Example: Decrease AI processing frequency
            ai = self.feature_manager.get_feature('unified_ai_service')
            if ai:
                ai.set_performance_mode('THROTTLED' if enable else 'PERFORMANCE')

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    atms = ThermalManagementSystem()
    print(atms.update_sensors(82, 40, 25))
