"""
3D Visualization Module
Voxel mapping, 3D rendering, and digital twin display
"""

import numpy as np
from typing import Dict, List, Tuple


class VoxelMapper:
    """3D voxel atmospheric mapping"""
    
    def __init__(self, resolution: int = 10):
        self.resolution = resolution
        self.voxels = {}
    
    def add_measurement(self, lat: float, lon: float, alt: float, value: float):
        """Add measurement to voxel grid"""
        key = self._coord_to_key(lat, lon, alt)
        self.voxels[key] = value
    
    def _coord_to_key(self, lat: float, lon: float, alt: float) -> Tuple[int, int, int]:
        """Convert coordinates to voxel key"""
        lat_idx = int(lat * self.resolution)
        lon_idx = int(lon * self.resolution)
        alt_idx = int(alt / 10)
        return (lat_idx, lon_idx, alt_idx)
    
    def get_voxel_grid(self) -> np.ndarray:
        """Get 3D voxel grid"""
        if not self.voxels:
            return np.zeros((10, 10, 10))
        
        max_key = max(self.voxels.keys())
        shape = (max_key[0] + 1, max_key[1] + 1, max_key[2] + 1)
        
        grid = np.zeros(shape)
        for key, value in self.voxels.items():
            grid[key] = value
        
        return grid
    
    def get_color_map(self) -> List[Dict]:
        """Get color-mapped voxels for visualization"""
        colors = []
        for key, value in self.voxels.items():
            colors.append({
                'position': key,
                'value': value,
                'color': self._value_to_color(value)
            })
        return colors
    
    def _value_to_color(self, value: float) -> str:
        """Map value to color (0-1)"""
        if value < 0.3:
            return "GREEN"
        elif value < 0.6:
            return "YELLOW"
        else:
            return "RED"


class PlumeMapper:
    """Gas/chemical plume mapping"""
    
    def __init__(self):
        self.sources = []
        self.plume_points = []
    
    def add_plume_point(self, lat: float, lon: float, alt: float, concentration: float):
        """Add plume measurement"""
        self.plume_points.append({
            'lat': lat, 'lon': lon, 'alt': alt, 'concentration': concentration
        })
    
    def calculate_source_probability(self) -> Dict:
        """Calculate most likely source location"""
        if not self.plume_points:
            return {'lat': 0, 'lon': 0, 'probability': 0}
        
        # Simple centroid calculation weighted by concentration
        total_weight = sum(p['concentration'] for p in self.plume_points)
        
        if total_weight == 0:
            return {'lat': 0, 'lon': 0, 'probability': 0}
        
        lat = sum(p['lat'] * p['concentration'] for p in self.plume_points) / total_weight
        lon = sum(p['lon'] * p['concentration'] for p in self.plume_points) / total_weight
        
        return {'lat': lat, 'lon': lon, 'probability': 0.8}


class DigitalTwin:
    """3D digital twin of CanSat"""
    
    def __init__(self):
        self.position = {'lat': 0, 'lon': 0, 'alt': 0}
        self.velocity = {'x': 0, 'y': 0, 'z': 0}
        self.attitude = {'pitch': 0, 'roll': 0, 'yaw': 0}
        self.forces = {'lift': 0, 'drag': 0, 'gravity': 0}
    
    def update(self, telemetry: Dict):
        """Update digital twin from telemetry"""
        self.position = {
            'lat': telemetry.get('latitude', 0),
            'lon': telemetry.get('longitude', 0),
            'alt': telemetry.get('altitude', 0)
        }
        self.velocity = {
            'x': telemetry.get('vx', 0),
            'y': telemetry.get('vy', 0),
            'z': telemetry.get('vertical_speed', 0)
        }
        self.attitude = {
            'pitch': telemetry.get('pitch', 0),
            'roll': telemetry.get('roll', 0),
            'yaw': telemetry.get('heading', 0)
        }
        # Physics calculations would go here
        self.forces = {'lift': 0, 'drag': 0, 'gravity': 9.8}
    
    def get_state(self) -> Dict:
        """Get current state"""
        return {
            'position': self.position,
            'velocity': self.velocity,
            'attitude': self.attitude,
            'forces': self.forces
        }


class LandingZonePredictor:
    """Predict and visualize landing zone"""
    
    def __init__(self):
        self.predictions = []
    
    def predict(self, current_pos: Dict, wind: Dict, descent_rate: float) -> Dict:
        """Predict landing zone"""
        
        time_to_land = current_pos.get('alt', 0) / abs(descent_rate) if descent_rate < 0 else 999
        
        # Horizontal drift
        wind_speed = wind.get('speed', 0)
        wind_dir = wind.get('direction', 0)
        
        drift_x = wind_speed * time_to_land * np.cos(np.radians(wind_dir))
        drift_y = wind_speed * time_to_land * np.sin(np.radians(wind_dir))
        
        landing = {
            'lat': current_pos.get('lat', 0) + drift_x / 111000,
            'lon': current_pos.get('lon', 0) + drift_y / 111000,
            'time_to_land': time_to_land,
            'ellipse_radius': max(2, wind_speed * time_to_land * 0.3)
        }
        
        self.predictions.append(landing)
        return landing
    
    def get_heatmap(self) -> List[Dict]:
        """Get Monte Carlo landing heatmap"""
        if not self.predictions:
            return []
        
        return [{
            'lat': p['lat'],
            'lon': p['lon'],
            'weight': 1.0 / len(self.predictions)
        } for p in self.predictions]


class HazardMap:
    """Terrain hazard mapping"""
    
    def __init__(self):
        self.hazards = []
    
    def add_terrain(self, classification: str, bounds: Dict):
        """Add terrain classification"""
        self.hazards.append({
            'type': classification,
            'bounds': bounds,
            'risk': self._get_risk(classification)
        })
    
    def _get_risk(self, terrain_type: str) -> str:
        risks = {
            'grass': 'LOW',
            'forest': 'MEDIUM',
            'water': 'HIGH',
            'buildings': 'HIGH',
            'road': 'MEDIUM'
        }
        return risks.get(terrain_type, 'UNKNOWN')
    
    def get_safe_zones(self) -> List[Dict]:
        """Get safe landing zones"""
        return [h for h in self.hazards if h['risk'] == 'LOW']


# Example
if __name__ == "__main__":
    twin = DigitalTwin()
    twin.update({'latitude': 51.5, 'longitude': -0.1, 'altitude': 100})
    print(f"State: {twin.get_state()}")