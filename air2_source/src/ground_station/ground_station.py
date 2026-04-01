"""
Ground Station Module - Full Implementation
Complete ground station control and monitoring
"""

import socket
import threading
import time
import numpy as np
from typing import Dict, List, Tuple, Callable
from collections import deque


class UDPTelemetryReceiver:
    """Receive telemetry via UDP"""
    
    def __init__(self, port: int = 5000):
        self.port = port
        self.socket = None
        self.running = False
        self.callbacks = []
        self.data_buffer = deque(maxlen=1000)
    
    def start(self):
        """Start receiving"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(('', self.port))
        self.running = True
        
        self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.receive_thread.start()
    
    def _receive_loop(self):
        """Receive loop"""
        while self.running:
            try:
                data, addr = self.socket.recvfrom(4096)
                self.data_buffer.append({
                    'data': data,
                    'address': addr,
                    'timestamp': time.time()
                })
                for callback in self.callbacks:
                    callback(data, addr)
            except:
                pass
    
    def on_receive(self, callback: Callable):
        """Register callback"""
        self.callbacks.append(callback)
    
    def stop(self):
        """Stop receiving"""
        self.running = False
        if self.socket:
            self.socket.close()
    
    def get_stats(self) -> Dict:
        return {'port': self.port, 'buffer_size': len(self.data_buffer), 'running': self.running}


class CommandSender:
    """Send commands to CanSat"""
    
    def __init__(self, target_ip: str = "192.168.1.100", port: int = 5001):
        self.target_ip = target_ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sequence = 0
    
    def send_command(self, command: str, params: Dict = None) -> bool:
        self.sequence += 1
        cmd_packet = {'seq': self.sequence, 'command': command, 'params': params or {}, 'timestamp': time.time()}
        try:
            self.socket.sendto(str(cmd_packet).encode(), (self.target_ip, self.port))
            return True
        except:
            return False
    
    def send_mode(self, mode: str) -> bool:
        return self.send_command('MODE', {'mode': mode})
    
    def send_reboot(self) -> bool:
        return self.send_command('REBOOT')


class SignalAnalyzer:
    """Analyze RF signal quality"""
    
    def __init__(self):
        self.history = deque(maxlen=100)
    
    def analyze_packet(self, rssi: int, snr: float, latency: float) -> Dict:
        rssi_score = 1.0 if rssi > -50 else 0.8 if rssi > -70 else 0.6 if rssi > -85 else 0.3 if rssi > -100 else 0.0
        snr_score = min(1.0, max(0.0, (snr + 10) / 30))
        latency_score = 1.0 if latency < 50 else 0.8 if latency < 100 else 0.5 if latency < 200 else 0.3
        overall_score = rssi_score * 0.4 + snr_score * 0.4 + latency_score * 0.2
        quality = "EXCELLENT" if overall_score > 0.8 else "GOOD" if overall_score > 0.6 else "FAIR" if overall_score > 0.4 else "POOR"
        self.history.append({'rssi': rssi, 'score': overall_score})
        return {'rssi': rssi, 'snr': snr, 'latency': latency, 'score': overall_score, 'quality': quality}


class AntennaTracker:
    """Track antenna toward CanSat"""
    
    def __init__(self):
        self.azimuth = 0
        self.elevation = 0
    
    def calculate(self, my_lat: float, my_lon: float, target_lat: float, target_lon: float, target_alt: float) -> Tuple[float, float]:
        dlon = target_lon - my_lon
        azimuth = (np.degrees(np.arctan2(dlon, target_lat - my_lat)) + 360) % 360
        distance = 1000
        elevation = np.degrees(np.arctan2(target_alt, distance))
        self.azimuth, self.elevation = azimuth, elevation
        return azimuth, elevation


class MissionPlanner:
    """Plan mission phases"""
    
    def __init__(self):
        self.phases = []
        self.current_phase = 0
    
    def add_phase(self, name: str, start_alt: float, end_alt: float, actions: List[str]):
        self.phases.append({'name': name, 'start_alt': start_alt, 'end_alt': end_alt, 'actions': actions})
    
    def update(self, altitude: float, elapsed: float) -> Dict:
        for i, p in enumerate(self.phases):
            if p['start_alt'] >= altitude >= p['end_alt']:
                self.current_phase = i
                return {'phase': p['name'], 'index': i, 'actions': p['actions'], 'elapsed': elapsed}
        return {'phase': 'COMPLETE'}


class RecoveryCoordinator:
    """Coordinate recovery"""
    
    def __init__(self):
        self.predicted = None
        self.ellipse = 0
    
    def update_prediction(self, lat: float, lon: float, radius: float):
        self.predicted = {'lat': lat, 'lon': lon}
        self.ellipse = radius
    
    def calculate_route(self, team_lat: float, team_lon: float) -> Dict:
        if not self.predicted:
            return {'distance': 0, 'bearing': 0}
        dlat = self.predicted['lat'] - team_lat
        dlon = self.predicted['lon'] - team_lon
        distance = np.sqrt(dlat**2 + dlon**2) * 111000
        bearing = np.degrees(np.arctan2(dlon, dlat))
        return {'distance_m': distance, 'bearing_deg': bearing, 'time_min': distance / 80}


class GroundStationGUI:
    """GUI state manager"""
    
    def __init__(self):
        self.telemetry = {}
        self.alerts = []
        self.markers = []
        self.status = 'IDLE'
    
    def update_telemetry(self, data: Dict):
        self.telemetry.update(data)
    
    def add_alert(self, level: str, message: str):
        self.alerts.append({'time': time.time(), 'level': level, 'message': message})
        if len(self.alerts) > 20:
            self.alerts = self.alerts[-20:]
    
    def add_marker(self, lat: float, lon: float, mtype: str, label: str):
        self.markers.append({'lat': lat, 'lon': lon, 'type': mtype, 'label': label})
    
    def set_status(self, status: str):
        self.status = status
    
    def get_state(self) -> Dict:
        return {'telemetry': self.telemetry, 'alerts': self.alerts[-5:], 'markers': self.markers[-20:], 'status': self.status}


if __name__ == "__main__":
    gs = GroundStationGUI()
    gs.set_status('FLYING')
    gs.add_alert('INFO', 'Apogee detected')
    print(gs.get_state())