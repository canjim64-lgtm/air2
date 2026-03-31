"""
Chemical Plume Tracker (CPT) for AirOne Professional v4.0
Implements Gaussian Plume Dispersion modeling to predict gas concentration spread.
"""
import logging
import math
import numpy as np
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class ChemicalPlumeTracker:
    def __init__(self, source_pos: tuple = (0, 0, 0), emission_rate: float = 100.0):
        self.logger = logging.getLogger(f"{__name__}.CPT")
        self.source_x, self.source_y, self.source_z = source_pos
        self.q = emission_rate # g/s
        self.logger.info(f"Chemical Plume Tracker Initialized. Source: {source_pos}")

    def predict_concentration(self, x: float, y: float, z: float, wind_speed: float, stability_class: str = 'C') -> Dict[str, Any]:
        """
        Calculates gas concentration at a point (x, y, z) using the Gaussian Plume Equation.
        x: downwind distance, y: crosswind distance, z: height.
        """
        # Dispersion coefficients (simplified Briggs/Pasquill-Gifford for rural 'C' stability)
        # These change based on stability class in a real system
        dist_km = max(0.001, x / 1000.0)
        sig_y = 104 * (dist_km**0.894)
        sig_z = 61 * (dist_km**0.911)
        
        if wind_speed <= 0.1: wind_speed = 0.1
        
        # Gaussian Plume Equation
        term1 = self.q / (2 * math.pi * wind_speed * sig_y * sig_z)
        term2 = math.exp(-(y**2) / (2 * sig_y**2))
        term3 = math.exp(-((z - self.source_z)**2) / (2 * sig_z**2)) + math.exp(-((z + self.source_z)**2) / (2 * sig_z**2)) # Reflection term
                
        concentration = term1 * term2 * term3
        
        status = "NOMINAL"
        if concentration > 50.0: status = "HAZARDOUS_LEVELS"
        elif concentration > 10.0: status = "WARNING_THRESHOLD"

        return {
            "status": status,
            "concentration_mg_m3": round(concentration, 4),
            "dispersion_sigma_y": round(sig_y, 2),
            "dispersion_sigma_z": round(sig_z, 2),
            "downwind_dist_m": round(x, 1)
        }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    cpt = ChemicalPlumeTracker(source_pos=(0, 0, 50))
    print(cpt.predict_concentration(x=500, y=10, z=2, wind_speed=3.5))
