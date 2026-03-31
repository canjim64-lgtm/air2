"""
Simulation Environment Module
Physics-based simulation environment
"""

import numpy as np
from typing import Dict


class Environment:
    """Physics simulation environment"""
    
    def __init__(self):
        self.gravity = 9.81
        self.air_density = 1.225
    
    def get_gravity(self, altitude: float) -> float:
        """Get gravity at altitude"""
        R = 6371000
        return self.gravity * (R / (R + altitude))**2
    
    def get_air_density(self, altitude: float) -> float:
        """Get air density at altitude"""
        return self.air_density * np.exp(-altitude / 8500)


class AtmosphericModel:
    """Atmospheric model"""
    
    def __init__(self):
        pass
    
    def temperature(self, altitude: float) -> float:
        """Temperature at altitude"""
        if altitude < 11000:
            return 15.04 - 0.00649 * altitude
        return -56.46
    
    def pressure(self, altitude: float) -> float:
        """Pressure at altitude"""
        return 101325 * np.exp(-altitude / 8500)


# Example
if __name__ == "__main__":
    env = Environment()
    print(f"Gravity: {env.get_gravity(1000)}")