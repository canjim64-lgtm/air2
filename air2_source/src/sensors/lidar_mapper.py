"""
LiDAR Point Cloud Mapping Engine for AirOne Professional v4.0
Processes raw LiDAR distance arrays into an obstacle map.
"""
import logging
import math
import numpy as np
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class LidarMappingEngine:
    def __init__(self, fov_degrees: float = 360.0, resolution_degrees: float = 1.0):
        self.logger = logging.getLogger(f"{__name__}.LidarMappingEngine")
        self.fov = fov_degrees
        self.resolution = resolution_degrees
        self.point_cloud = []
        self.logger.info(f"LiDAR Mapping Engine Initialized (FOV: {self.fov}°, Res: {self.resolution}°)")

    def process_scan(self, distances_m: List[float], altitude: float, pitch: float, roll: float, yaw: float) -> Dict[str, Any]:
        """Translates 1D array of distances into 3D spatial points considering CanSat orientation."""
        if not distances_m:
            return {"status": "no_data"}
            
        current_cloud = []
        num_points = len(distances_m)
        angle_step = self.fov / max(1, num_points)
        
        # Pre-calculate rotation matrices (Tait-Bryan angles)
        cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
        cr, sr = math.cos(math.radians(roll)), math.sin(math.radians(roll))
        cy, sy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        
        # Combined rotation matrix R = R_z(yaw) * R_y(pitch) * R_x(roll)
        R = np.array([
            [cy*cp, cy*sp*sr - sy*cr, cy*sp*cr + sy*sr],
            [sy*cp, sy*sp*sr + cy*cr, sy*sp*cr - cy*sr],
            [-sp,   cp*sr,            cp*cr]
        ])

        for i, dist in enumerate(distances_m):
            if dist <= 0.0 or dist > 100.0:  # Ignore invalid or out-of-range points
                continue
                
            angle_deg = i * angle_step
            angle_rad = math.radians(angle_deg)
            
            # Local sensor coordinates (assuming scanning in XY plane)
            local_x = dist * math.cos(angle_rad)
            local_y = dist * math.sin(angle_rad)
            local_z = 0.0
            
            local_vec = np.array([local_x, local_y, local_z])
            
            # Rotate to global coordinates
            global_vec = R.dot(local_vec)
            
            # Translate to altitude
            point = {
                "x": round(global_vec[0], 2),
                "y": round(global_vec[1], 2),
                "z": round(altitude + global_vec[2], 2)
            }
            current_cloud.append(point)
            
        self.point_cloud.extend(current_cloud)
        
        # Keep cloud bounded for memory safety
        if len(self.point_cloud) > 10000:
            self.point_cloud = self.point_cloud[-10000:]
            
        return {
            "status": "processed",
            "new_points": len(current_cloud),
            "total_points": len(self.point_cloud)
        }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    mapper = LidarMappingEngine()
    # Mocking a 360 degree scan of 10 meters distance
    scan_data = [10.0] * 360
    print(mapper.process_scan(scan_data, altitude=50.0, pitch=0, roll=0, yaw=45))
