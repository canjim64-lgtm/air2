"""
GPS and Location Module
GPS and location services
"""

import numpy as np
from typing import Dict, Tuple


class GPSReceiver:
    """GPS receiver interface"""
    
    def __init__(self):
        self.latitude = 0.0
        self.longitude = 0.0
        self.altitude = 0.0
        self.satellites = 0
    
    def get_position(self) -> Tuple[float, float, float]:
        """Get position"""
        return (self.latitude, self.longitude, self.altitude)
    
    def update(self, data: Dict):
        """Update position"""
        self.latitude = data.get('lat', 0)
        self.longitude = data.get('lon', 0)
        self.altitude = data.get('alt', 0)
        self.satellites = data.get('sat', 0)


class GeofenceMonitor:
    """Monitor geofences"""
    
    def __init__(self):
        self.fences = {}
    
    def add_fence(self, name: str, center: Tuple[float, float], radius: float):
        """Add geofence"""
        self.fences[name] = {'center': center, 'radius': radius}
    
    def check(self, lat: float, lon: float) -> Dict:
        """Check position"""
        results = {}
        for name, fence in self.fences.items():
            dist = self._distance(lat, lon, *fence['center'])
            results[name] = dist < fence['radius']
        return results
    
    def _distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance"""
        return np.sqrt((lat1-lat2)**2 + (lon1-lon2)**2) * 111  # Rough km


# Example
if __name__ == "__main__":
    gps = GPSReceiver()
    print(f"Position: {gps.get_position()}")