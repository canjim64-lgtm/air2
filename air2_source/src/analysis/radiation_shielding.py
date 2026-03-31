"""
Space Radiation Shielding Simulator (SRSS) for AirOne Professional v4.0
Models particle energy deposition (Bragg Peak) and shielding effectiveness using LET physics.
"""
import logging
import math
import numpy as np
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class RadiationShieldingSimulator:
    def __init__(self, materials: Dict[str, float] = {"Aluminium": 2.7, "Polyethylene": 0.94}):
        self.logger = logging.getLogger(f"{__name__}.SRSS")
        self.materials = materials # Density in g/cm^3
        self.logger.info(f"Radiation Shielding Simulator Initialized. Materials: {list(materials.keys())}")

    def simulate_penetration(self, particle_energy_mev: float, shield_material: str, thickness_cm: float) -> Dict[str, Any]:
        """
        Calculates residual energy and dose reduction.
        Uses a simplified Bethe-Bloch approximation for energy loss (dE/dx).
        """
        if shield_material not in self.materials:
            return {"status": "ERROR", "message": "Unknown material"}

        density = self.materials[shield_material]
        
        # dE/dx approx: Stopping power constant * density / sqrt(E)
        # This is a highly simplified heuristic of the Bethe-Bloch curve
        k_stopping = 0.5 
        current_energy = particle_energy_mev
        depth_step = 0.01 # 0.1mm steps
        depths = np.arange(0, thickness_cm, depth_step)
        
        energy_profile = []
        for d in depths:
            if current_energy <= 0.1: # Particle stopped
                current_energy = 0
                break
            
            # Energy loss in this step
            de = (k_stopping * density / math.sqrt(current_energy)) * depth_step
            current_energy -= de
            energy_profile.append(current_energy)

        # Bragg Peak detection (highest dE/dx occurs just before stopping)
        stopped_at_cm = len(energy_profile) * depth_step
        shielding_factor = 1.0 - (current_energy / particle_energy_mev)

        return {
            "status": "SIMULATED",
            "incident_energy_mev": particle_energy_mev,
            "residual_energy_mev": round(current_energy, 3),
            "shielding_effectiveness_pct": round(shielding_factor * 100, 2),
            "particle_stopped": current_energy == 0,
            "penetration_depth_cm": round(stopped_at_cm, 3)
        }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    rss = RadiationShieldingSimulator()
    print(rss.simulate_penetration(100.0, "Aluminium", 5.0))
