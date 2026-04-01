"""
Power Management Module
Battery monitoring, power health, and switching
"""

import time


class PowerMonitor:
    """Monitor power system health"""
    
    def __init__(self):
        self.voltage_history = []
        self.current_draw = 0
        self.battery_esr = 0.1
    
    def update(self, voltage: float, current: float = 0):
        """Update power readings"""
        self.voltage_history.append({
            'time': time.time(),
            'voltage': voltage,
            'current': current
        })
        
        if len(self.voltage_history) > 100:
            self.voltage_history = self.voltage_history[-100:]
        
        self.current_draw = current
    
    def calculate_esr(self) -> float:
        """Calculate battery ESR"""
        if len(self.voltage_history) < 2:
            return self.battery_esr
        
        v_drop = abs(self.voltage_history[-1]['voltage'] - self.voltage_history[-2]['voltage'])
        i_draw = abs(self.current_draw)
        
        if i_draw > 0.1:
            esr = v_drop / i_draw
            self.battery_esr = 0.9 * self.battery_esr + 0.1 * esr
        
        return self.battery_esr
    
    def get_health(self) -> str:
        """Get battery health status"""
        if not self.voltage_history:
            return "UNKNOWN"
        
        current_v = self.voltage_history[-1]['voltage']
        
        if current_v > 8.0:
            return "EXCELLENT"
        elif current_v > 7.4:
            return "GOOD"
        elif current_v > 7.0:
            return "FAIR"
        else:
            return "LOW"


class MasterSwitch:
    """Master power switch control"""
    
    def __init__(self):
        self.state = False
    
    def on(self):
        self.state = True
        return "POWER_ON"
    
    def off(self):
        self.state = False
        return "POWER_OFF"
    
    def get_state(self) -> bool:
        return self.state


class PowerBudget:
    """Calculate power budget"""
    
    COMPONENTS = {
        'ESP32': 0.2,
        'HC-12': 0.1,
        'Sensors': 0.05,
        'GPS': 0.05,
        'SD Card': 0.02
    }
    
    def __init__(self):
        self.battery_capacity = 8.5 * 7.4
    
    def calculate_runtime(self, active_time: float = 3600) -> Dict:
        total_current = sum(self.COMPONENTS.values())
        capacity_used = total_current * active_time / 3600
        remaining = self.battery_capacity - capacity_used
        
        return {
            'total_draw_w': total_current,
            'capacity_wh': self.battery_capacity,
            'runtime_hours': remaining / total_current if total_current > 0 else 0,
            'percentage_remaining': (remaining / self.battery_capacity) * 100
        }


if __name__ == "__main__":
    pm = PowerMonitor()
    pm.update(7.8, 0.3)
    print(f"Health: {pm.get_health()}")