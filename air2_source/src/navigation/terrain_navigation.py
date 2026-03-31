"""
Terrain Relative Navigation (TRN) for AirOne Professional v4.0
Cross-references radar altimeter readings with a Digital Elevation Model (DEM) matrix to correct lateral drift.
"""
import logging
import numpy as np
from typing import Dict, Any

logger = logging.getLogger(__name__)

class TerrainNavigator:
    def __init__(self, dem_resolution_m: float = 10.0):
        self.logger = logging.getLogger(f"{__name__}.TerrainNavigator")
        self.resolution = dem_resolution_m
        # Generate a synthetic procedural terrain (mock DEM) using sin/cos waves
        x = np.linspace(-500, 500, 100)
        y = np.linspace(-500, 500, 100)
        X, Y = np.meshgrid(x, y)
        self.dem_map = 50 * np.sin(X/100) + 50 * np.cos(Y/100) + 100 # Base elevation 100m, varied by +/-100m
        self.logger.info("Terrain Relative Navigation (TRN) Engine Initialized.")

    def update_position(self, estimated_x: float, estimated_y: float, baro_alt: float, radar_alt: float) -> Dict[str, Any]:
        """Correlates actual terrain height with DEM to estimate position error."""
        # Calculate actual terrain height directly beneath the craft
        actual_terrain_height = baro_alt - radar_alt
        
        # Map estimated x/y to array indices
        idx_x = int(np.clip((estimated_x + 500) / 10, 0, 99))
        idx_y = int(np.clip((estimated_y + 500) / 10, 0, 99))
        
        expected_terrain_height = self.dem_map[idx_y, idx_x]
        
        elevation_error = actual_terrain_height - expected_terrain_height
        
        # In a real TRN (like MADNAV), we'd compute the gradient of the DEM and shift x/y
        # using a particle filter to minimize elevation_error.
        # Simplified gradient descent correction:
        grad_x = (self.dem_map[idx_y, min(99, idx_x+1)] - self.dem_map[idx_y, max(0, idx_x-1)]) / 20.0
        grad_y = (self.dem_map[min(99, idx_y+1), idx_x] - self.dem_map[max(0, idx_y-1), idx_x]) / 20.0
        
        # Gradient descent step
        learning_rate = 0.5
        correction_x = -elevation_error * grad_x * learning_rate
        correction_y = -elevation_error * grad_y * learning_rate
        
        confidence = max(0.0, 1.0 - (abs(elevation_error) / 50.0))

        return {
            "status": "TRN_LOCKED" if confidence > 0.5 else "TRN_DEGRADED",
            "elevation_error_m": round(float(elevation_error), 2),
            "suggested_correction_x": round(float(correction_x), 2),
            "suggested_correction_y": round(float(correction_y), 2),
            "trn_confidence": round(float(confidence), 3)
        }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    trn = TerrainNavigator()
    # At (0,0), DEM height should be around 150m.
    print(trn.update_position(0.0, 0.0, 1000.0, 850.0)) # Exact match
    print(trn.update_position(0.0, 0.0, 1000.0, 830.0)) # 20m error
