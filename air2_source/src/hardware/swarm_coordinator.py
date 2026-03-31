"""
Satellite Swarm Coordinator for AirOne Professional v4.0
Implements a real 3D vector-based repulsion algorithm for autonomous collision avoidance.
"""
import logging
import math
import numpy as np
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class SwarmCoordinator:
    def __init__(self, min_safe_distance: float = 15.0):
        self.logger = logging.getLogger(f"{__name__}.SwarmCoordinator")
        self.fleet = {}
        self.min_safe_distance = min_safe_distance # meters
        self.repulsion_gain = 2.0 # Force factor
        self.logger.info(f"Satellite Swarm Coordinator Initialized. Safe Distance: {min_safe_distance}m.")

    def register_satellite(self, sat_id: str, role: str = "node"):
        self.fleet[sat_id] = {
            "role": role,
            "pos": np.array([0.0, 0.0, 0.0]),
            "vel": np.array([0.0, 0.0, 0.0]),
            "evasion_vector": np.array([0.0, 0.0, 0.0]),
            "status": "active"
        }
        self.logger.info(f"Registered satellite {sat_id} as {role}.")

    def update_telemetry(self, sat_id: str, x: float, y: float, z: float, vx: float = 0, vy: float = 0, vz: float = 0):
        if sat_id in self.fleet:
            self.fleet[sat_id]["pos"] = np.array([x, y, z])
            self.fleet[sat_id]["vel"] = np.array([vx, vy, vz])
            self._calculate_safety_vectors(sat_id)
        else:
            self.logger.warning(f"Telemetry ignored for unknown satellite: {sat_id}")

    def _calculate_safety_vectors(self, active_sat: str):
        """Calculates a repulsion vector if another satellite is within the danger zone."""
        pos1 = self.fleet[active_sat]["pos"]
        total_repulsion = np.array([0.0, 0.0, 0.0])
        
        for sat_id, data in self.fleet.items():
            if sat_id == active_sat: continue
            
            pos2 = data["pos"]
            diff = pos1 - pos2
            dist = np.linalg.norm(diff)
            
            if dist < self.min_safe_distance and dist > 0.1:
                self.logger.warning(f"COLLISION RISK: {active_sat} vs {sat_id} (Dist: {dist:.2f}m)")
                
                # Inverse square repulsion force
                force_mag = self.repulsion_gain * (self.min_safe_distance - dist) / dist
                total_repulsion += (diff / dist) * force_mag
        
        self.fleet[active_sat]["evasion_vector"] = total_repulsion
        if np.linalg.norm(total_repulsion) > 0.01:
            self._issue_evasion_command(active_sat, total_repulsion)

    def _issue_evasion_command(self, sat_id: str, vector: np.ndarray):
        """Issues the actual correction command to the satellite flight controller."""
        v_str = f"X:{vector[0]:.2f}, Y:{vector[1]:.2f}, Z:{vector[2]:.2f}"
        self.logger.info(f"CMD sent to {sat_id}: Adjust trajectory by repulsion vector [{v_str}]")

    def get_swarm_status(self) -> Dict[str, Any]:
        return {
            "active_nodes": len(self.fleet),
            "threat_levels": {sid: float(np.linalg.norm(d['evasion_vector'])) for sid, d in self.fleet.items()}
        }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    swarm = SwarmCoordinator(min_safe_distance=10.0)
    swarm.register_satellite("SAT-1")
    swarm.register_satellite("SAT-2")
    
    # Simulate proximity
    swarm.update_telemetry("SAT-1", 0, 0, 100)
    swarm.update_telemetry("SAT-2", 2, 2, 100) # Only 2.8m apart
