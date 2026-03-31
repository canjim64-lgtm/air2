"""
Radiation Environment Monitor (REM) for AirOne Professional v4.0
Calculates ionizing radiation dose rates and exposure risk using physics-based Linear Energy Transfer (LET) modeling.
"""
import logging
import math
import time
from typing import Dict, Any

logger = logging.getLogger(__name__)

class RadiationMonitor:
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.RadiationMonitor")
        self.accumulated_dose_uSv = 0.0
        self.last_update = time.time()
        self.solar_activity_index = 1.0 # 1.0 = Nominal
        self.logger.info("Radiation Environment Monitor (REM) Initialized.")

    def update_exposure(self, altitude_m: float, latitude: float) -> Dict[str, Any]:
        """Models radiation flux based on altitude and geomagnetic shielding."""
        now = time.time()
        dt_sec = now - self.last_update
        self.last_update = now
        
        # Physics Model: Cosmic ray flux increases exponentially with altitude
        # Flux(h) = Flux_0 * exp(h / scale_height)
        # Note: This is a simplified atmospheric shielding model
        flux_base = 0.01 # uSv/hr at sea level
        scale_height = 7000.0 # meters
        
        # Geomagnetic shielding factor (stronger at equator, weaker at poles)
        # L-shell approx: cos(lat)^4
        shielding = math.cos(math.radians(latitude))**4
        geomagnetic_factor = 1.0 + (5.0 * (1.0 - shielding)) # Up to 6x increase at poles
        
        instant_dose_rate = flux_base * math.exp(altitude_m / scale_height) * geomagnetic_factor * self.solar_activity_index
        
        # Accumulate dose (uSv)
        dose_increment = (instant_dose_rate / 3600.0) * dt_sec
        self.accumulated_dose_uSv += dose_increment
        
        status = "SAFE"
        if instant_dose_rate > 50.0: status = "EXTREME_EXPOSURE"
        elif instant_dose_rate > 10.0: status = "HIGH_EXPOSURE"
        elif instant_dose_rate > 2.0: status = "MODERATE_EXPOSURE"

        return {
            "status": status,
            "dose_rate_uSv_hr": round(instant_dose_rate, 3),
            "total_accumulated_dose_uSv": round(self.accumulated_dose_uSv, 4),
            "geomagnetic_factor": round(geomagnetic_factor, 2),
            "altitude_m": altitude_m
        }

    def reset_dosimeter(self):
        self.accumulated_dose_uSv = 0.0
        self.logger.info("Dosimeter reset to zero.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    rem = RadiationMonitor()
    print(rem.update_exposure(altitude_m=35000, latitude=60.0)) # High altitude near pole
