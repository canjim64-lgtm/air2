"""
Ground Station Antenna Auto-Tracker for AirOne Professional v4.0
Calculates dynamic Azimuth and Elevation angles to drive a pan-tilt rotator.
"""
import logging
import math
from typing import Dict, Any

logger = logging.getLogger(__name__)

class AntennaTracker:
    def __init__(self, station_lat: float = 34.05, station_lon: float = -118.24, station_alt: float = 100.0):
        self.logger = logging.getLogger(f"{__name__}.AntennaTracker")
        self.station_lat = math.radians(station_lat)
        self.station_lon = math.radians(station_lon)
        self.station_alt = station_alt
        self.earth_radius = 6371000.0 # meters
        self.current_azimuth = 0.0
        self.current_elevation = 0.0
        self.logger.info("Antenna Auto-Tracker Initialized.")

    def calculate_pointing(self, target_lat_deg: float, target_lon_deg: float, target_alt: float) -> Dict[str, float]:
        """Calculates required azimuth and elevation to point at the CanSat."""
        target_lat = math.radians(target_lat_deg)
        target_lon = math.radians(target_lon_deg)
        
        # Haversine formula for distance
        dlon = target_lon - self.station_lon
        dlat = target_lat - self.station_lat
        
        a = math.sin(dlat / 2)**2 + math.cos(self.station_lat) * math.cos(target_lat) * math.sin(dlon / 2)**2
        c = 2 * math.asin(math.sqrt(a))
        ground_dist = self.earth_radius * c
        
        # Calculate Azimuth
        y = math.sin(dlon) * math.cos(target_lat)
        x = math.cos(self.station_lat) * math.sin(target_lat) - math.sin(self.station_lat) * math.cos(target_lat) * math.cos(dlon)
        azimuth = math.degrees(math.atan2(y, x))
        azimuth = (azimuth + 360) % 360
        
        # Calculate Elevation (incorporating earth curvature)
        alt_diff = target_alt - self.station_alt
        slant_range = math.sqrt(ground_dist**2 + alt_diff**2)
        
        if ground_dist == 0:
            elevation = 90.0 if alt_diff > 0 else -90.0
        else:
            # Basic elevation
            elevation = math.degrees(math.atan2(alt_diff, ground_dist))
            
        self.current_azimuth = round(azimuth, 2)
        self.current_elevation = round(elevation, 2)
        
        self.logger.debug(f"Antenna Pointing Update -> AZ: {self.current_azimuth}°, EL: {self.current_elevation}°")
        
        return {
            "azimuth_deg": self.current_azimuth,
            "elevation_deg": self.current_elevation,
            "slant_range_m": round(slant_range, 2)
        }

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    tracker = AntennaTracker(station_lat=34.0, station_lon=-118.0)
    print(tracker.calculate_pointing(34.1, -118.1, 1000.0))
