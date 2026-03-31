"""
Solar Position & Panel Aligner for AirOne Professional v4.0
Calculates celestial solar coordinates based on GPS/Time to optimize energy harvest.
"""
import logging
import math
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class SolarAligner:
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.SolarAligner")
        self.logger.info("Solar Position & Aligner Initialized.")

    def calculate_sun_position(self, lat: float, lon: float, alt: float, timestamp: Optional[float] = None) -> Dict[str, Any]:
        """
        Calculates Solar Azimuth and Elevation using a simplified PSA (PSA Algorithm).
        """
        dt = datetime.fromtimestamp(timestamp) if timestamp else datetime.utcnow()
        
        # Calculate Day of Year and Decimal Hour
        day_of_year = dt.timetuple().tm_yday
        hour = dt.hour + dt.minute / 60.0 + dt.second / 3600.0
        
        # Fractional year in radians
        gamma = (2 * math.pi / 365) * (day_of_year - 1 + (hour - 12) / 24)
        
        # Equation of time and declination
        eq_time = 229.18 * (0.000075 + 0.001868 * math.cos(gamma) - 0.032077 * math.sin(gamma) - 0.014615 * math.cos(2 * gamma) - 0.040849 * math.sin(2 * gamma))
        
        declination = 0.006918 - 0.399912 * math.cos(gamma) + 0.070257 * math.sin(gamma) - 0.006758 * math.cos(2 * gamma) + 0.000907 * math.sin(2 * gamma) - 0.002697 * math.cos(3 * gamma) + 0.00148 * math.sin(3 * gamma)
        
        # Hour angle
        time_offset = eq_time + 4 * lon - 60 * 0 # Assuming UTC 0 for standard
        t_solar = hour * 60 + time_offset
        hour_angle = math.radians((t_solar / 4) - 180)
        
        # Convert lat to radians
        lat_rad = math.radians(lat)
        
        # Zenith angle
        cos_zenith = (math.sin(lat_rad) * math.sin(declination) + math.cos(lat_rad) * math.cos(declination) * math.cos(hour_angle))
        zenith = math.acos(max(-1, min(1, cos_zenith)))
        elevation = 90 - math.degrees(zenith)
        
        # Azimuth
        cos_azimuth = ((math.sin(declination) - math.sin(lat_rad) * cos_zenith) / (math.cos(lat_rad) * math.sin(zenith)))
        azimuth = 180 - math.degrees(math.acos(max(-1, min(1, cos_azimuth))))
        if hour_angle > 0:
            azimuth = 360 - azimuth

        return {
            "solar_azimuth": round(azimuth, 2),
            "solar_elevation": round(elevation, 2),
            "is_daylight": elevation > -0.83,
            "optimal_panel_pitch": round(max(0, 90 - elevation), 2)
        }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    aligner = SolarAligner()
    print(aligner.calculate_sun_position(34.05, -118.24, 100))
