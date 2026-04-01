"""
Telemetry Dashboard Module
Real-time telemetry visualization and monitoring
"""

import time
import numpy as np
from typing import Dict, List


class TelemetryDashboard:
    """Real-time dashboard for CanSat telemetry"""
    
    def __init__(self):
        self.data_history = {
            'altitude': [],
            'temperature': [],
            'pressure': [],
            'voc': [],
            'radiation': [],
            'battery': [],
            'rssi': []
        }
        self.alerts = []
        self.events = []
    
    def update(self, telemetry: Dict):
        """Update dashboard with new data"""
        timestamp = time.time()
        
        for key in self.data_history:
            if key in telemetry:
                self.data_history[key].append({
                    'time': timestamp,
                    'value': telemetry[key]
                })
        
        # Trim to last 1000 points
        for key in self.data_history:
            if len(self.data_history[key]) > 1000:
                self.data_history[key] = self.data_history[key][-1000:]
    
    def get_plot_data(self, key: str) -> List[Dict]:
        """Get plot data for a sensor"""
        return self.data_history.get(key, [])
    
    def get_statistics(self, key: str) -> Dict:
        """Get statistics for a sensor"""
        values = [d['value'] for d in self.data_history.get(key, [])]
        
        if not values:
            return {}
        
        return {
            'current': values[-1],
            'min': min(values),
            'max': max(values),
            'mean': np.mean(values),
            'std': np.std(values)
        }
    
    def add_alert(self, level: str, message: str):
        """Add alert"""
        self.alerts.append({
            'time': time.time(),
            'level': level,
            'message': message
        })
    
    def get_alerts(self, level: str = None) -> List[Dict]:
        """Get alerts"""
        if level:
            return [a for a in self.alerts if a['level'] == level]
        return self.alerts


class MissionTimer:
    """Mission timing and phase tracking"""
    
    def __init__(self):
        self.start_time = None
        self.phases = []
        self.current_phase = None
    
    def start_mission(self):
        """Start mission timer"""
        self.start_time = time.time()
        self.add_phase("LAUNCH", time.time())
    
    def add_phase(self, name: str, timestamp: float = None):
        """Add mission phase"""
        if timestamp is None:
            timestamp = time.time()
        
        self.phases.append({
            'name': name,
            'timestamp': timestamp,
            'elapsed': timestamp - self.start_time if self.start_time else 0
        })
        self.current_phase = name
    
    def get_elapsed(self) -> float:
        """Get mission elapsed time"""
        if self.start_time:
            return time.time() - self.start_time
        return 0
    
    def get_current_phase(self) -> str:
        """Get current phase"""
        return self.current_phase


class LiveMap:
    """Live GPS mapping visualization"""
    
    def __init__(self):
        self.track = []
        self.waypoints = []
        self.predicted_path = []
        self.landing_ellipse = None
    
    def add_position(self, lat: float, lon: float, alt: float):
        """Add GPS position"""
        self.track.append({
            'lat': lat,
            'lon': lon,
            'alt': alt,
            'time': time.time()
        })
    
    def add_waypoint(self, lat: float, lon: float, name: str = ""):
        """Add waypoint"""
        self.waypoints.append({
            'lat': lat,
            'lon': lon,
            'name': name
        })
    
    def set_predicted_path(self, path: List[Dict]):
        """Set predicted landing path"""
        self.predicted_path = path
    
    def set_landing_ellipse(self, center: Dict, radius: float):
        """Set landing ellipse"""
        self.landing_ellipse = {
            'center': center,
            'radius': radius
        }
    
    def get_track(self) -> List[Dict]:
        """Get GPS track"""
        return self.track


class DataLogger:
    """Dual-path data persistence"""
    
    def __init__(self, binary_file: str = "raw.bin", csv_file: "telemetry.csv"):
        self.binary_file = binary_file
        self.csv_file = csv_file
        self.buffer = []
    
    def log_raw(self, packet: bytes):
        """Log raw hex packet to binary"""
        with open(self.binary_file, 'ab') as f:
            f.write(packet)
    
    def log_parsed(self, data: Dict):
        """Log parsed data to CSV buffer"""
        self.buffer.append(data)
        
        # Flush every 10 records
        if len(self.buffer) >= 10:
            self.flush_csv()
    
    def flush_csv(self):
        """Flush CSV buffer to file"""
        if not self.buffer:
            return
        
        import csv
        
        with open(self.csv_file, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.buffer[0].keys())
            
            if f.tell() == 0:
                writer.writeheader()
            
            writer.writerows(self.buffer)
        
        self.buffer = []


class AudioVario:
    """Ground proximity audio beeper"""
    
    def __init__(self):
        self.last_beep_time = 0
        self.beep_interval = 0.5
        self.max_distance = 4.0  # meters
    
    def update(self, distance: float) -> bool:
        """Update and return if beep should play"""
        
        if distance > self.max_distance:
            return False
        
        # Closer = faster beeps
        ratio = 1 - (distance / self.max_distance)
        self.beep_interval = 0.1 + (0.4 * ratio)
        
        current_time = time.time()
        
        if current_time - self.last_beep_time >= self.beep_interval:
            self.last_beep_time = current_time
            return True
        
        return False


# Example
if __name__ == "__main__":
    dashboard = TelemetryDashboard()
    dashboard.update({'altitude': 100, 'temperature': 20})
    stats = dashboard.get_statistics('altitude')
    print(f"Stats: {stats}")