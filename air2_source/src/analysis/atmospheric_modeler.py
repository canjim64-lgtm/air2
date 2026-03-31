"""
Atmospheric Profile Modeler for AirOne Professional v4.0
Predicts air density, pressure, and O2 concentration based on altitude using the ISA model.
"""
import logging
import math
from typing import Dict, Any

logger = logging.getLogger(__name__)

class AtmosphericModeler:
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.AtmosphericModeler")
        # Constants for International Standard Atmosphere (ISA)
        self.P0 = 101325.0 # Pa (Sea level pressure)
        self.T0 = 288.15   # K (Sea level temperature)
        self.L = 0.0065    # K/m (Temperature lapse rate)
        self.R = 8.31447   # J/(mol·K) (Gas constant)
        self.M = 0.0289644 # kg/mol (Molar mass of air)
        self.g = 9.80665   # m/s^2 (Gravity)
        self.logger.info("Atmospheric Profile Modeler Initialized.")

    def get_profile_at_altitude(self, altitude_m: float) -> Dict[str, Any]:
        """Calculates theoretical atmospheric parameters using the Barometric Formula."""
        altitude_m = max(0, altitude_m)
        
        # Temperature at altitude
        temp_k = self.T0 - self.L * altitude_m
        temp_c = temp_k - 273.15
        
        # Pressure at altitude (Troposphere model < 11km)
        if altitude_m < 11000:
            pressure_pa = self.P0 * (1 - (self.L * altitude_m) / self.T0) ** ((self.g * self.M) / (self.R * self.L))
        else:
            # Stratosphere model (simplified)
            p_11 = 22632.1
            t_11 = 216.65
            pressure_pa = p_11 * math.exp(-self.g * self.M * (altitude_m - 11000) / (self.R * t_11))
            
        # Density (Ideal Gas Law: rho = PM / RT)
        density = (pressure_pa * self.M) / (self.R * temp_k)
        
        # Estimated Oxygen Concentration (approx 20.95% by volume, stays fairly constant in lower atmosphere)
        # But partial pressure changes
        o2_partial_pressure = pressure_pa * 0.2095

        return {
            "altitude_m": altitude_m,
            "theoretical_pressure_pa": round(pressure_pa, 2),
            "theoretical_temp_c": round(temp_c, 2),
            "air_density_kg_m3": round(density, 4),
            "o2_partial_pressure_pa": round(o2_partial_pressure, 2),
            "speed_of_sound_m_s": round(math.sqrt(1.4 * (self.R / self.M) * temp_k), 2)
        }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    atm = AtmosphericModeler()
    print(atm.get_profile_at_altitude(5000))
