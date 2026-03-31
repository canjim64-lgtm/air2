"""
Power Monitoring System
Monitors voltage, current, and temperature to detect power anomalies.
"""

from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
import time
import numpy as np

class PowerMonitor:
    def __init__(self):
        self.running = False
        self.start_time: Optional[datetime] = None
        self.voltage_history: List[Tuple[float, float]] = []
        self.current_history: List[Tuple[float, float]] = []
        self.temperature_history: List[Tuple[float, float]] = []
        self.power_warnings: List[Dict[str, Any]] = []
        self.max_history_length = 1000

    def start(self):
        """Start power monitoring"""
        self.running = True
        self.start_time = datetime.now()

    def stop(self):
        """Stop power monitoring"""
        self.running = False

    def update(self, voltage: float, current: float, temperature: float):
        """Update power metrics"""
        if not self.running:
            return
        
        timestamp = time.time()
        
        self.voltage_history.append((timestamp, voltage))
        self.current_history.append((timestamp, current))
        self.temperature_history.append((timestamp, temperature))
        
        # Check for warnings
        if voltage < 10.0:
            self.power_warnings.append({
                "type": "low_voltage",
                "value": voltage,
                "timestamp": timestamp,
                "message": "Voltage below 10V"
            })
        elif current > 5.0:
            self.power_warnings.append({
                "type": "high_current",
                "value": current,
                "timestamp": timestamp,
                "message": "Current above 5A"
            })
        
        if temperature > 60:
            self.power_warnings.append({
                "type": "high_temperature",
                "value": temperature,
                "timestamp": timestamp,
                "message": "Temperature above 60°C"
            })
        
        # Keep history limited
        self.voltage_history = self.voltage_history[-self.max_history_length:]
        self.current_history = self.current_history[-self.max_history_length:]
        self.temperature_history = self.temperature_history[-self.max_history_length:]
        self.power_warnings = self.power_warnings[-100:] # Keep last 100 warnings

    def get_status(self) -> Dict[str, Any]:
        """Get current power status"""
        status = {
            "running": self.running,
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
            "metrics": {}
        }
        
        if self.voltage_history:
            voltages = [v for _, v in self.voltage_history]
            status["metrics"]["voltage"] = {
                "current": voltages[-1] if voltages else 0,
                "average": float(np.mean(voltages)),
                "min": float(np.min(voltages)),
                "max": float(np.max(voltages))
            }
        
        if self.current_history:
            currents = [c for _, c in self.current_history]
            status["metrics"]["current"] = {
                "current": currents[-1] if currents else 0,
                "average": float(np.mean(currents)),
                "min": float(np.min(currents)),
                "max": float(np.max(currents))
            }
        
        if self.temperature_history:
            temps = [t for _, t in self.temperature_history]
            status["metrics"]["temperature"] = {
                "current": temps[-1] if temps else 0,
                "average": float(np.mean(temps)),
                "min": float(np.min(temps)),
                "max": float(np.max(temps))
            }
        
        status["warnings"] = self.power_warnings
        
        return status
