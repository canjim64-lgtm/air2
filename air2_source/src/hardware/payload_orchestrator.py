"""
Payload Orchestrator for AirOne Professional v4.0
Coordinates multiple scientific payloads and dynamically allocates power/data bandwidth.
"""
import logging
import time
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class PayloadOrchestrator:
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.PayloadOrchestrator")
        self.payloads = {}
        self.total_power_budget = 100.0 # Watts
        self.logger.info("Payload Orchestrator Initialized.")

    def register_payload(self, name: str, priority: int, max_power: float):
        self.payloads[name] = {
            "priority": priority,
            "max_power": max_power,
            "status": "idle",
            "allocated_power": 0.0
        }
        self.logger.info(f"Registered payload: {name} (Priority {priority}, Max Power {max_power}W)")

    def optimize_power(self, available_power: float) -> Dict[str, float]:
        """Dynamically allocate power based on payload priority."""
        self.total_power_budget = available_power
        
        # Sort payloads by priority (highest first)
        sorted_payloads = sorted(self.payloads.items(), key=lambda x: x[1]['priority'], reverse=True)
        
        remaining_power = available_power
        allocation = {}
        
        for name, config in sorted_payloads:
            if remaining_power >= config['max_power']:
                allocated = config['max_power']
                config['status'] = "active"
            else:
                allocated = remaining_power
                config['status'] = "degraded" if remaining_power > 0 else "disabled"
                
            config['allocated_power'] = allocated
            allocation[name] = allocated
            remaining_power -= allocated
            
        self.logger.debug(f"Power allocation updated: {allocation}")
        return allocation

    def get_status(self) -> Dict[str, Any]:
        return {name: config['status'] for name, config in self.payloads.items()}

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    orch = PayloadOrchestrator()
    orch.register_payload("MainCamera", priority=10, max_power=15.0)
    orch.register_payload("Spectrometer", priority=5, max_power=25.0)
    orch.register_payload("EnvironmentalSensor", priority=20, max_power=2.0)
    
    print(orch.optimize_power(30.0))
