"""
Star Tracker Navigation Engine for AirOne Professional v4.0
Simulates attitude determination by matching a field-of-view against a celestial catalog.
"""
import logging
import math
import numpy as np
from typing import Dict, Any, List, Tuple

logger = logging.getLogger(__name__)

class StarTracker:
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.StarTracker")
        # Simulated small catalog of stars (Right Ascension, Declination, Magnitude)
        self.catalog = [
            {"name": "Sirius", "ra": 101.287, "dec": -16.716, "mag": -1.46},
            {"name": "Canopus", "ra": 95.987, "dec": -52.695, "mag": -0.74},
            {"name": "Rigel", "ra": 78.634, "dec": -8.201, "mag": 0.13},
            {"name": "Arcturus", "ra": 95.089, "dec": -52.695, "mag": -0.05},
            {"name": "Vega", "ra": 213.915, "dec": 19.182, "mag": 0.03}
        ]
        self.logger.info("Star Tracker Navigation Engine Initialized.")

    def _ra_dec_to_vector(self, ra: float, dec: float) -> np.ndarray:
        """Converts Right Ascension and Declination to a 3D unit vector."""
        ra_rad = math.radians(ra)
        dec_rad = math.radians(dec)
        x = math.cos(dec_rad) * math.cos(ra_rad)
        y = math.cos(dec_rad) * math.sin(ra_rad)
        z = math.sin(dec_rad)
        return np.array([x, y, z])

    def solve_attitude(self, obs_vectors: List[np.ndarray], ref_vectors: List[np.ndarray]) -> Dict[str, Any]:
        """
        Solves Wahba's problem using the TRIAD algorithm.
        Takes observed vectors (body frame) and reference vectors (inertial frame).
        """
        if len(obs_vectors) < 2 or len(ref_vectors) < 2:
            return {"status": "FAILED", "reason": "Need at least 2 vector pairs"}
            
        # TRIAD Algorithm
        # 1. Compute orthonormal bases for body frame
        b1 = obs_vectors[0] / np.linalg.norm(obs_vectors[0])
        b2 = np.cross(obs_vectors[0], obs_vectors[1])
        b2 = b2 / np.linalg.norm(b2)
        b3 = np.cross(b1, b2)
        M_body = np.column_stack((b1, b2, b3))
        
        # 2. Compute orthonormal bases for inertial frame
        r1 = ref_vectors[0] / np.linalg.norm(ref_vectors[0])
        r2 = np.cross(ref_vectors[0], ref_vectors[1])
        r2 = r2 / np.linalg.norm(r2)
        r3 = np.cross(r1, r2)
        M_inertial = np.column_stack((r1, r2, r3))
        
        # 3. Compute rotation matrix R (Inertial to Body)
        R = M_body @ M_inertial.T
        
        # Convert Rotation Matrix to Quaternion
        tr = np.trace(R)
        if tr > 0:
            S = math.sqrt(tr + 1.0) * 2
            qw = 0.25 * S
            qx = (R[2,1] - R[1,2]) / S
            qy = (R[0,2] - R[2,0]) / S
            qz = (R[1,0] - R[0,1]) / S
        else:
            # Handle other cases for robustness
            if (R[0,0] > R[1,1]) and (R[0,0] > R[2,2]):
                S = math.sqrt(1.0 + R[0,0] - R[1,1] - R[2,2]) * 2
                qw = (R[2,1] - R[1,2]) / S
                qx = 0.25 * S
                qy = (R[0,1] + R[1,0]) / S
                qz = (R[0,2] + R[2,0]) / S
            elif R[1,1] > R[2,2]:
                S = math.sqrt(1.0 + R[1,1] - R[0,0] - R[2,2]) * 2
                qw = (R[0,2] - R[2,0]) / S
                qx = (R[0,1] + R[1,0]) / S
                qy = 0.25 * S
                qz = (R[1,2] + R[2,1]) / S
            else:
                S = math.sqrt(1.0 + R[2,2] - R[0,0] - R[1,1]) * 2
                qw = (R[1,0] - R[0,1]) / S
                qx = (R[0,2] + R[2,0]) / S
                qy = (R[1,2] + R[2,1]) / S
                qz = 0.25 * S

        # Calculate Euler angles
        roll = math.degrees(math.atan2(2*(qw*qx + qy*qz), 1 - 2*(qx*qx + qy*qy)))
        pitch = math.degrees(math.asin(2*(qw*qy - qz*qx)))
        yaw = math.degrees(math.atan2(2*(qw*qz + qx*qy), 1 - 2*(qy*qy + qz*qz)))

        return {
            "status": "ATTITUDE_LOCKED",
            "quaternion": [round(qw, 4), round(qx, 4), round(qy, 4), round(qz, 4)],
            "euler_angles_deg": {"roll": round(roll, 2), "pitch": round(pitch, 2), "yaw": round(yaw, 2)},
            "method": "TRIAD"
        }

if __name__ == "__main__":
    import random
    logging.basicConfig(level=logging.INFO)
    st = StarTracker()
    # Mocking two observed star vectors (Body Frame)
    obs = [
        np.array([1.0, 0.0, 0.0]),
        np.array([0.0, 1.0, 0.0])
    ]
    # Reference vectors (Inertial Frame)
    ref = [
        np.array([1.0, 0.0, 0.0]),
        np.array([0.0, 1.0, 0.0])
    ]
    print(st.solve_attitude(obs, ref))
